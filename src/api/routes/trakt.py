from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.schemas.trakt import (
    AuthStatusResponse,
    DeviceCodeResponse,
    SyncHistoryRequest,
    SyncHistoryResponse,
    YearStatsResponse,
)
from src.services.trakt import TraktAuthError, TraktService

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
    request: SyncHistoryRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync user's watch history from Trakt.
    Optionally specify start_at and end_at to sync a specific date range.
    """
    service = TraktService(db)
    try:
        start_at = request.start_at if request else None
        end_at = request.end_at if request else None
        count = await service.sync_user_history(user_id, start_at, end_at)
        return SyncHistoryResponse(
            synced_count=count,
            message=f"Successfully synced {count} new watch entries",
        )
    except TraktAuthError as e:
        if str(e) == "not_authenticated":
            raise HTTPException(status_code=401, detail="User not authenticated with Trakt")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    user_id: str,
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    media_type: str | None = Query(None, regex="^(movies|episodes)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch watch history directly from Trakt API.
    Use /sync to persist data to the database.
    """
    service = TraktService(db)
    try:
        history = await service.fetch_history(user_id, start_at, end_at, media_type)
        return {"count": len(history), "history": history}
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
