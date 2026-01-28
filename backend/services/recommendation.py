
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import ML_MODEL_PATH, TMDB_API_KEY, TMDB_API_URL, TRAKT_API_URL, TRAKT_CLIENT_ID
from backend.db.models.trakt import WatchHistory
from ml.model import get_recommender


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.recommender = get_recommender(ML_MODEL_PATH)

    def _get_trakt_headers(self, access_token: str | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": TRAKT_CLIENT_ID,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def fetch_trending_movies_trakt(self, limit: int = 20) -> list[dict]:
        """Fetch trending movies from Trakt API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TRAKT_API_URL}/movies/trending",
                params={"limit": limit, "extended": "full"},
                headers=self._get_trakt_headers(),
            )
            response.raise_for_status()
            data = response.json()

            movies = []
            for item in data:
                movie = item.get("movie", {})
                movies.append({
                    "id": movie.get("ids", {}).get("tmdb"),
                    "trakt_id": movie.get("ids", {}).get("trakt"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "runtime": movie.get("runtime"),
                    "genres": movie.get("genres", []),
                    "vote_average": movie.get("rating"),
                    "watchers": item.get("watchers", 0),
                })
            return movies

    async def fetch_latest_movies_tmdb(self, limit: int = 20) -> list[dict]:
        """Fetch latest/now playing movies from TMDB API."""
        if not TMDB_API_KEY:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_API_URL}/movie/now_playing",
                params={"api_key": TMDB_API_KEY, "page": 1},
            )
            response.raise_for_status()
            data = response.json()

            movies = []
            for movie in data.get("results", [])[:limit]:
                movies.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "year": (
                        int(movie["release_date"][:4]) if movie.get("release_date") else None
                    ),
                    "genres": movie.get("genre_ids", []),
                    "vote_average": movie.get("vote_average"),
                    "popularity": movie.get("popularity"),
                    "poster_path": movie.get("poster_path"),
                })
            return movies

    async def fetch_popular_movies_tmdb(self, pages: int = 3) -> list[dict]:
        """Fetch popular movies from TMDB API."""
        if not TMDB_API_KEY:
            return []

        movies = []
        async with httpx.AsyncClient() as client:
            for page in range(1, pages + 1):
                response = await client.get(
                    f"{TMDB_API_URL}/movie/popular",
                    params={"api_key": TMDB_API_KEY, "page": page},
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                for movie in data.get("results", []):
                    movies.append({
                        "id": movie["id"],
                        "title": movie["title"],
                        "year": (
                        int(movie["release_date"][:4]) if movie.get("release_date") else None
                    ),
                        "genres": movie.get("genre_ids", []),
                        "vote_average": movie.get("vote_average"),
                        "popularity": movie.get("popularity"),
                        "poster_path": movie.get("poster_path"),
                    })
        return movies

    async def get_user_watch_history(self, user_id: str, media_type: str = "movie") -> list[dict]:
        """Get user's watch history from database."""
        stmt = select(WatchHistory).where(
            WatchHistory.user_id == user_id,
            WatchHistory.media_type == media_type,
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        return [
            {
                "id": e.trakt_id,
                "trakt_id": e.trakt_id,
                "title": e.title,
                "year": e.year,
                "runtime": e.runtime_minutes,
                "watched_at": e.watched_at,
            }
            for e in entries
        ]

    async def get_recommendations(
        self,
        user_id: str,
        n: int = 10,
        include_trending: bool = True,
        include_latest: bool = True,
    ) -> dict:
        """
        Get personalized movie recommendations for a user.

        Combines user's watch history with trending/latest movies to generate recommendations.
        """
        watched_movies = await self.get_user_watch_history(user_id)

        candidate_movies = []
        if include_trending:
            trending = await self.fetch_trending_movies_trakt(limit=50)
            candidate_movies.extend(trending)
        if include_latest:
            latest = await self.fetch_latest_movies_tmdb(limit=30)
            candidate_movies.extend(latest)

        if not candidate_movies:
            candidate_movies = await self.fetch_popular_movies_tmdb(pages=3)

        seen_ids = set()
        unique_candidates = []
        for m in candidate_movies:
            if m["id"] and m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_candidates.append(m)

        if watched_movies and self.recommender.movie_features is not None:
            recommendations = self.recommender.recommend(
                watched_movies=watched_movies,
                candidate_movies=unique_candidates,
                n=n,
            )
        else:
            recommendations = sorted(
                unique_candidates,
                key=lambda x: (x.get("popularity") or 0),
                reverse=True,
            )[:n]
            for r in recommendations:
                r["score"] = 0.0

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "watched_count": len(watched_movies),
            "model_trained": self.recommender.movie_features is not None,
        }

    async def retrain_model(self) -> dict:
        """Retrain the recommendation model with fresh data."""
        movies = await self.fetch_popular_movies_tmdb(pages=50)
        trending = await self.fetch_trending_movies_trakt(limit=100)
        movies.extend(trending)

        seen_ids = set()
        unique_movies = []
        for m in movies:
            if m["id"] and m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_movies.append(m)

        self.recommender.train(unique_movies)
        self.recommender.save()

        return {
            "status": "success",
            "movies_trained": len(unique_movies),
        }
