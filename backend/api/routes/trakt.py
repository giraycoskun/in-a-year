from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.schemas.trakt import (
    AuthStatusResponse,
    DeviceCodeResponse,
    SyncHistoryRequest,
    SyncHistoryResponse,
    YearStatsResponse,
)
from backend.services.trakt import TraktAuthError, TraktService
from backend.worker.tasks.trakt import sync_trakt_history_for_year, sync_trakt_history_full

router = APIRouter()


@router.get("/auth/device-code", response_model=DeviceCodeResponse)
async def get_device_code(db: AsyncSession = Depends(get_db)):
    """
    Start OAuth2 device flow.
    Returns a user_code and verification_url for the user to authorize.
    """
    service = TraktService(db)
    try:
        return await service.get_device_code()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/token")
async def exchange_device_code(
    device_code: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange device code for access token after user authorization.
    Poll this endpoint at the interval returned by /auth/device-code.
    """
    service = TraktService(db)
    try:
        token_data = await service.poll_for_token(device_code)
        await service.save_token(user_id, token_data)
        return {"status": "authenticated", "user_id": user_id}
    except TraktAuthError as e:
        error_code = str(e)
        if error_code == "pending":
            raise HTTPException(status_code=202, detail="Authorization pending")
        elif error_code == "expired":
            raise HTTPException(status_code=410, detail="Device code expired")
        elif error_code == "denied":
            raise HTTPException(status_code=403, detail="User denied authorization")
        elif error_code == "slow_down":
            raise HTTPException(status_code=429, detail="Polling too fast")
        else:
            raise HTTPException(status_code=400, detail=error_code)


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check if a user is authenticated with Trakt."""
    service = TraktService(db)
    token = await service.get_token(user_id)
    if token:
        return AuthStatusResponse(
            authenticated=True,
            user_id=user_id,
            expires_at=token.expires_at,
        )
    return AuthStatusResponse(authenticated=False)


@router.post("/sync", response_model=SyncHistoryResponse)
async def sync_history(
    user_id: str,
    request: SyncHistoryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync user's watch history from Trakt for a specific year or month.

    - year: Required. The year to sync (e.g., 2025)
    - month: Optional. If provided, only sync that month (1-12)
    """
    service = TraktService(db)
    try:
        count = await service.sync_user_history(user_id, request.year, request.month)
        period = f"{request.year}/{request.month}" if request.month else str(request.year)
        return SyncHistoryResponse(
            synced_count=count,
            message=f"Successfully synced {count} new watch entries for {period}",
        )
    except TraktAuthError as e:
        if str(e) == "not_authenticated":
            raise HTTPException(status_code=401, detail="User not authenticated with Trakt")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    user_id: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    media_type: str | None = Query(None, pattern="^(movies|episodes)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch watch history directly from Trakt API.

    - year: Required. The year to fetch (e.g., 2025)
    - month: Optional. If provided, only fetch that month (1-12)
    - media_type: Optional. Filter by 'movies' or 'episodes'
    """
    from backend.services.trakt import get_date_range

    service = TraktService(db)
    try:
        start_at, end_at = get_date_range(year, month)
        history = await service.fetch_history(user_id, start_at, end_at, media_type)
        period = f"{year}/{month}" if month else str(year)
        return {"count": len(history), "period": period, "history": history}
    except TraktAuthError as e:
        if str(e) == "not_authenticated":
            raise HTTPException(status_code=401, detail="User not authenticated with Trakt")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/{year}", response_model=YearStatsResponse)
async def get_trakt_stats(
    year: int,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get movies/TV watching stats for a specific year."""
    service = TraktService(db)
    return await service.get_year_stats(user_id, year)


@router.post("/sync/year/{year}")
async def sync_year_history_task(
    year: int,
    user_id: str,
    month: int | None = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a background task to sync Trakt history for a specific year or month.

    - year: The year to sync (e.g., 2025)
    - month: Optional. If provided, only sync that month (1-12)
    """
    service = TraktService(db)
    token = await service.get_token(user_id)
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated with Trakt")

    task = sync_trakt_history_for_year.delay(user_id, year, month)  # type: ignore
    period = f"{year}/{month}" if month else str(year)
    return {"task_id": task.id, "status": "started", "period": period, "year": year, "month": month}


@router.post("/sync/years")
async def sync_multiple_years_task(
    user_id: str,
    start_year: int = Query(..., ge=2000, le=2100),
    end_year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a background task to sync Trakt history for multiple years.
    Returns a task ID to track progress.
    """
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year must be <= end_year")

    service = TraktService(db)
    token = await service.get_token(user_id)
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated with Trakt")

    task = sync_trakt_history_full.delay(user_id, start_year, end_year) # type: ignore
    return {
        "task_id": task.id,
        "status": "started",
        "start_year": start_year,
        "end_year": end_year,
    }


@router.get("/sync/status/{task_id}")
async def get_sync_task_status(task_id: str):
    """Get the status of a sync task."""
    from celery.result import AsyncResult

    from backend.worker.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.ready():
        if result.successful():
            response["result"] = result.get()
        else:
            response["error"] = str(result.result)

    return response
