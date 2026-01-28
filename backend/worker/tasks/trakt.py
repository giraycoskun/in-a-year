import calendar
from datetime import datetime, timedelta

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.config import SYNC_DATABASE_URL, TRAKT_API_URL, TRAKT_CLIENT_ID, TRAKT_CLIENT_SECRET
from backend.db.models.trakt import TraktToken, WatchHistory
from backend.worker.celery_app import celery_app


def get_date_range(year: int, month: int | None = None) -> tuple[datetime, datetime]:
    """Get start and end datetime for a year or specific month."""
    if month:
        start_at = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_at = datetime(year, month, last_day, 23, 59, 59)
    else:
        start_at = datetime(year, 1, 1)
        end_at = datetime(year, 12, 31, 23, 59, 59)
    return start_at, end_at

engine = create_engine(SYNC_DATABASE_URL)


def get_headers(access_token: str | None = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def refresh_token_sync(db: Session, token: TraktToken) -> TraktToken:
    """Refresh an expired access token (sync version)."""
    with httpx.Client() as client:
        response = client.post(
            f"{TRAKT_API_URL}/oauth/token",
            json={
                "refresh_token": token.refresh_token,
                "client_id": TRAKT_CLIENT_ID,
                "client_secret": TRAKT_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
            headers=get_headers(),
        )
        response.raise_for_status()
        token_data = response.json()

    expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
    token.access_token = token_data["access_token"]
    token.refresh_token = token_data["refresh_token"]
    token.expires_at = expires_at
    db.commit()
    db.refresh(token)
    return token


def get_valid_token_sync(db: Session, user_id: str) -> str:
    """Get a valid access token, refreshing if necessary (sync version)."""
    stmt = select(TraktToken).where(TraktToken.user_id == user_id)
    token = db.execute(stmt).scalar_one_or_none()

    if not token:
        raise ValueError(f"User {user_id} not authenticated with Trakt")

    if token.expires_at < datetime.utcnow():
        token = refresh_token_sync(db, token)

    return token.access_token


def fetch_history_sync(
    access_token: str,
    year: int,
    month: int | None = None,
    media_type: str | None = None,
) -> list[dict]:
    """Fetch watch history for a specific year or month (sync version)."""
    start_at, end_at = get_date_range(year, month)

    url = f"{TRAKT_API_URL}/users/me/history"
    if media_type:
        url = f"{url}/{media_type}"

    params: dict[str, str | int] = {
        "limit": 1000,
        "start_at": start_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "end_at": end_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }

    all_history = []
    page = 1

    with httpx.Client(timeout=60.0) as client:
        while True:
            params["page"] = page
            response = client.get(
                url,
                params=params,
                headers=get_headers(access_token),
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            all_history.extend(data)

            total_pages = int(response.headers.get("X-Pagination-Page-Count", 1))
            if page >= total_pages:
                break
            page += 1

    return all_history


def process_and_store_history_sync(
    db: Session,
    user_id: str,
    history_data: list[dict],
) -> int:
    """Process Trakt history data and store in database (sync version)."""
    count = 0

    for item in history_data:
        watched_at = datetime.fromisoformat(item["watched_at"].replace("Z", "+00:00"))
        media_type = item["type"]

        if media_type == "movie":
            movie = item["movie"]
            trakt_id = movie["ids"]["trakt"]
            title = movie["title"]
            year = movie.get("year")
            runtime = movie.get("runtime")
            show_title = None
            season = None
            episode_num = None
        elif media_type == "episode":
            episode = item["episode"]
            show = item["show"]
            trakt_id = episode["ids"]["trakt"]
            title = episode["title"]
            year = show.get("year")
            runtime = episode.get("runtime")
            show_title = show["title"]
            season = episode.get("season")
            episode_num = episode.get("number")
        else:
            continue

        stmt = select(WatchHistory).where(
            WatchHistory.user_id == user_id,
            WatchHistory.trakt_id == trakt_id,
            WatchHistory.watched_at == watched_at,
        )
        existing = db.execute(stmt).scalar_one_or_none()

        if not existing:
            watch_entry = WatchHistory(
                user_id=user_id,
                trakt_id=trakt_id,
                title=title,
                media_type=media_type,
                watched_at=watched_at,
                runtime_minutes=runtime,
                year=year,
                season=season,
                episode=episode_num,
                show_title=show_title,
            )
            db.add(watch_entry)
            count += 1

    db.commit()
    return count


@celery_app.task(bind=True, max_retries=3)  # type: ignore[misc]
def sync_trakt_history_for_year(  # type: ignore[no-untyped-def]
    self, user_id: str, year: int, month: int | None = None
) -> dict:
    """
    Celery task to fetch and store Trakt history for a user in a given year or month.

    Args:
        user_id: The user identifier
        year: The year to sync history for
        month: Optional month (1-12) to sync only that month

    Returns:
        dict with sync results
    """
    try:
        with Session(engine) as db:
            access_token = get_valid_token_sync(db, user_id)
            history = fetch_history_sync(access_token, year, month)
            synced_count = process_and_store_history_sync(db, user_id, history)

            period = f"{year}/{month}" if month else str(year)
            return {
                "status": "success",
                "user_id": user_id,
                "period": period,
                "year": year,
                "month": month,
                "total_fetched": len(history),
                "new_entries": synced_count,
            }
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)  # type: ignore[misc]
def sync_trakt_history_full(  # type: ignore[no-untyped-def]
    self, user_id: str, start_year: int, end_year: int
) -> dict:
    """
    Celery task to sync Trakt history across multiple years.

    Args:
        user_id: The user identifier
        start_year: The starting year (inclusive)
        end_year: The ending year (inclusive)

    Returns:
        dict with sync results
    """
    results = []
    total_fetched = 0
    total_new = 0

    try:
        with Session(engine) as db:
            access_token = get_valid_token_sync(db, user_id)

            for year in range(start_year, end_year + 1):
                history = fetch_history_sync(access_token, year)
                synced_count = process_and_store_history_sync(db, user_id, history)

                results.append({
                    "year": year,
                    "fetched": len(history),
                    "new_entries": synced_count,
                })
                total_fetched += len(history)
                total_new += synced_count

        return {
            "status": "success",
            "user_id": user_id,
            "years": results,
            "total_fetched": total_fetched,
            "total_new_entries": total_new,
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
