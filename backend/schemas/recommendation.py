from pydantic import BaseModel


class MovieRecommendation(BaseModel):
    id: int
    title: str
    year: int | None = None
    genres: list[str | int] = []
    score: float
    vote_average: float | None = None
    poster_path: str | None = None


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[MovieRecommendation]
    watched_count: int
    model_trained: bool


class TrendingMovie(BaseModel):
    id: int | None
    trakt_id: int | None = None
    title: str
    year: int | None = None
    runtime: int | None = None
    genres: list[str] = []
    vote_average: float | None = None
    watchers: int = 0


class LatestMovie(BaseModel):
    id: int
    title: str
    year: int | None = None
    genres: list[int] = []
    vote_average: float | None = None
    popularity: float | None = None
    poster_path: str | None = None


class RetrainResponse(BaseModel):
    status: str
    movies_trained: int
