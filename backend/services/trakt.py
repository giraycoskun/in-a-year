from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import TRAKT_API_URL, TRAKT_CLIENT_ID, TRAKT_CLIENT_SECRET
from backend.db.models.trakt import TraktToken, WatchHistory


class TraktAuthError(Exception):
    pass


class TraktService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_url = TRAKT_API_URL
        self.client_id = TRAKT_CLIENT_ID
        self.client_secret = TRAKT_CLIENT_SECRET

    def _get_headers(self, access_token: str | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": self.client_id,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def get_device_code(self) -> dict:
        """Generate device code for OAuth2 device flow."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/oauth/device/code",
                json={"client_id": self.client_id},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def poll_for_token(self, device_code: str) -> dict:
        """Poll for access token after user authorizes the device."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/oauth/device/token",
                json={
                    "code": device_code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                raise TraktAuthError("pending")
            elif response.status_code == 404:
                raise TraktAuthError("invalid_device_code")
            elif response.status_code == 409:
                raise TraktAuthError("already_used")
            elif response.status_code == 410:
                raise TraktAuthError("expired")
            elif response.status_code == 418:
                raise TraktAuthError("denied")
            elif response.status_code == 429:
                raise TraktAuthError("slow_down")
            else:
                response.raise_for_status()
            return {}

    async def save_token(self, user_id: str, token_data: dict) -> TraktToken:
        """Save OAuth token to database."""
        expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        stmt = select(TraktToken).where(TraktToken.user_id == user_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.access_token = token_data["access_token"]
            existing.refresh_token = token_data["refresh_token"]
            existing.expires_at = expires_at
            token = existing
        else:
            token = TraktToken(
                user_id=user_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=expires_at,
            )
            self.db.add(token)

        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_token(self, user_id: str) -> TraktToken | None:
        """Get stored token for a user."""
        stmt = select(TraktToken).where(TraktToken.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def refresh_access_token(self, user_id: str) -> TraktToken:
        """Refresh an expired access token."""
        token = await self.get_token(user_id)
        if not token:
            raise TraktAuthError("no_token")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/oauth/token",
                json={
                    "refresh_token": token.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            token_data = response.json()

        return await self.save_token(user_id, token_data)

    async def get_valid_token(self, user_id: str) -> str:
        """Get a valid access token, refreshing if necessary."""
        token = await self.get_token(user_id)
        if not token:
            raise TraktAuthError("not_authenticated")

        if token.expires_at < datetime.utcnow():
            token = await self.refresh_access_token(user_id)

        return token.access_token

    async def fetch_history(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        media_type: str | None = None,
    ) -> list[dict]:
        """Fetch watch history from Trakt API."""
        access_token = await self.get_valid_token(user_id)

        url = f"{self.api_url}/users/me/history"
        if media_type:
            url = f"{url}/{media_type}"

        params: dict[str, str | int] = {"limit": 1000}
        if start_at:
            params["start_at"] = start_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if end_at:
            params["end_at"] = end_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        all_history = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                params["page"] = page
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(access_token),
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

    async def process_and_store_history(
        self,
        user_id: str,
        history_data: list[dict],
    ) -> int:
        """Process Trakt history data and store in database."""
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
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

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
                self.db.add(watch_entry)
                count += 1

        await self.db.commit()
        return count

    async def sync_user_history(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> int:
        """Fetch and store user's watch history."""
        history = await self.fetch_history(user_id, start_at, end_at)
        return await self.process_and_store_history(user_id, history)

    async def get_year_stats(self, user_id: str, year: int) -> dict:
        """Get watching statistics for a specific year."""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        stmt = select(WatchHistory).where(
            WatchHistory.user_id == user_id,
            WatchHistory.watched_at >= start_date,
            WatchHistory.watched_at <= end_date,
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        movies = [e for e in entries if e.media_type == "movie"]
        episodes = [e for e in entries if e.media_type == "episode"]

        total_movie_minutes = sum(m.runtime_minutes or 0 for m in movies)
        total_episode_minutes = sum(e.runtime_minutes or 0 for e in episodes)
        unique_shows = len(set(e.show_title for e in episodes if e.show_title))

        return {
            "year": year,
            "movies": {
                "count": len(movies),
                "total_minutes": total_movie_minutes,
                "total_hours": round(total_movie_minutes / 60, 1),
            },
            "episodes": {
                "count": len(episodes),
                "total_minutes": total_episode_minutes,
                "total_hours": round(total_episode_minutes / 60, 1),
                "unique_shows": unique_shows,
            },
            "total": {
                "count": len(entries),
                "total_minutes": total_movie_minutes + total_episode_minutes,
                "total_hours": round((total_movie_minutes + total_episode_minutes) / 60, 1),
            },
        }
