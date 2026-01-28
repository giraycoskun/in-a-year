from pydantic import BaseModel


class HardcoverStats(BaseModel):
    books_read: int = 0
    pages_read: int = 0
    average_rating: float | None = None


class TraktStats(BaseModel):
    movies_watched: int = 0
    episodes_watched: int = 0
    total_runtime_hours: int = 0


class YearlyStats(BaseModel):
    year: int
    hardcover: HardcoverStats = HardcoverStats()
    trakt: TraktStats = TraktStats()
