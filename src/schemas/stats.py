from pydantic import BaseModel


class SpotifyStats(BaseModel):
    total_minutes: int = 0
    unique_artists: int = 0
    unique_tracks: int = 0
    top_artist: str | None = None
    top_track: str | None = None


class GithubStats(BaseModel):
    total_commits: int = 0
    total_prs: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    top_repo: str | None = None


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
    spotify: SpotifyStats = SpotifyStats()
    github: GithubStats = GithubStats()
    hardcover: HardcoverStats = HardcoverStats()
    trakt: TraktStats = TraktStats()
