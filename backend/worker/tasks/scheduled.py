"""Scheduled tasks for periodic maintenance."""

from datetime import datetime, timedelta

import httpx
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.config import SYNC_DATABASE_URL, TRAKT_API_URL, TRAKT_CLIENT_ID, TRAKT_CLIENT_SECRET
from backend.db.models.trakt import TraktToken
from backend.worker.celery_app import celery_app

engine = create_engine(SYNC_DATABASE_URL)


def get_trakt_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
    }


def refresh_trakt_token(db: Session, token: TraktToken) -> bool:
    """Refresh a single Trakt token. Returns True if successful."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{TRAKT_API_URL}/oauth/token",
                json={
                    "refresh_token": token.refresh_token,
                    "client_id": TRAKT_CLIENT_ID,
                    "client_secret": TRAKT_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                },
                headers=get_trakt_headers(),
            )
            response.raise_for_status()
            token_data = response.json()

        expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        token.access_token = token_data["access_token"]
        token.refresh_token = token_data["refresh_token"]
        token.expires_at = expires_at
        db.commit()
        return True
    except Exception as e:
        logger.exception("Failed to refresh token for user {}", token.user_id)
        return False


@celery_app.task
def refresh_expiring_tokens() -> dict:
    """
    Refresh all Trakt tokens that will expire within the next 24 hours.
    This task should run periodically (e.g., every 6 hours).
    """
    threshold = datetime.utcnow() + timedelta(hours=24)

    with Session(engine) as db:
        stmt = select(TraktToken).where(TraktToken.expires_at < threshold)
        result = db.execute(stmt)
        expiring_tokens = result.scalars().all()

        refreshed = 0
        failed = 0

        for token in expiring_tokens:
            if refresh_trakt_token(db, token):
                refreshed += 1
            else:
                failed += 1

    return {
        "status": "completed",
        "tokens_checked": len(expiring_tokens),
        "refreshed": refreshed,
        "failed": failed,
    }


@celery_app.task
def refresh_user_token(user_id: str) -> dict:
    """Manually refresh a specific user's Trakt token."""
    with Session(engine) as db:
        stmt = select(TraktToken).where(TraktToken.user_id == user_id)
        result = db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            return {"status": "error", "message": f"No token found for user {user_id}"}

        if refresh_trakt_token(db, token):
            return {
                "status": "success",
                "user_id": user_id,
                "expires_at": token.expires_at.isoformat(),
            }
        else:
            return {"status": "error", "message": "Failed to refresh token"}
