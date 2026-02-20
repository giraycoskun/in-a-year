from datetime import datetime

from pydantic import BaseModel


class DeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_url: str
    expires_in: int
    interval: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
    created_at: int


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user_id: str | None = None
    expires_at: datetime | None = None


class SyncHistoryRequest(BaseModel):
    year: int
    month: int | None = None


class SyncHistoryResponse(BaseModel):
    synced_count: int
    message: str
    last_tracked_sync_at: datetime | None = None


class MovieStats(BaseModel):
    count: int
    total_minutes: int
    total_hours: float


class EpisodeStats(BaseModel):
    count: int
    total_minutes: int
    total_hours: float
    unique_shows: int


class TotalStats(BaseModel):
    count: int
    total_minutes: int
    total_hours: float


class YearStatsResponse(BaseModel):
    year: int
    movies: MovieStats
    episodes: EpisodeStats
    total: TotalStats
