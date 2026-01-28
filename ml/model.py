from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


class MovieRecommender:
    """
    Content-based movie recommender using TF-IDF on genres and metadata.
    Learns user preferences from watch history and recommends similar movies.
    """

    def __init__(self, model_path: str = "ml/models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)

        self.vectorizer: TfidfVectorizer | None = None
        self.scaler: MinMaxScaler | None = None
        self.movie_features: np.ndarray | None = None
        self.movie_ids: list[int] = []
        self.movie_metadata: dict[int, dict] = {}

    def _create_feature_text(self, movie: dict) -> str:
        """Create a text representation of movie features for TF-IDF."""
        parts = []

        if genres := movie.get("genres"):
            if isinstance(genres, list):
                parts.extend([g.get("name", g) if isinstance(g, dict) else g for g in genres])

        if year := movie.get("year"):
            decade = (year // 10) * 10
            parts.append(f"decade_{decade}s")

        if runtime := movie.get("runtime"):
            if runtime < 90:
                parts.append("short_movie")
            elif runtime < 150:
                parts.append("medium_movie")
            else:
                parts.append("long_movie")

        if vote_avg := movie.get("vote_average"):
            if vote_avg >= 7.5:
                parts.append("highly_rated")
            elif vote_avg >= 6.0:
                parts.append("well_rated")

        return " ".join(parts) if parts else "unknown"

    def train(self, movies: list[dict]) -> None:
        """
        Train the model on a list of movies.

        Args:
            movies: List of movie dicts with keys: id, title, genres, year, runtime, vote_average
        """
        if not movies:
            return

        self.movie_ids = [m["id"] for m in movies]
        self.movie_metadata = {m["id"]: m for m in movies}

        feature_texts = [self._create_feature_text(m) for m in movies]

        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
        self.movie_features = self.vectorizer.fit_transform(feature_texts).toarray()

        numeric_features = []
        for m in movies:
            numeric_features.append([
                m.get("year", 2000) / 2030,
                (m.get("runtime") or 100) / 300,
                (m.get("vote_average") or 5.0) / 10,
                (m.get("popularity") or 10) / 1000,
            ])

        self.scaler = MinMaxScaler()
        scaled_numeric = self.scaler.fit_transform(numeric_features)

        self.movie_features = np.hstack([self.movie_features, scaled_numeric])

    def save(self) -> None:
        """Save the trained model to disk."""
        if self.vectorizer is None:
            raise ValueError("Model not trained yet")

        joblib.dump(self.vectorizer, self.model_path / "vectorizer.joblib")
        joblib.dump(self.scaler, self.model_path / "scaler.joblib")
        np.save(self.model_path / "movie_features.npy", self.movie_features)
        joblib.dump(self.movie_ids, self.model_path / "movie_ids.joblib")
        joblib.dump(self.movie_metadata, self.model_path / "movie_metadata.joblib")

    def load(self) -> bool:
        """Load a trained model from disk. Returns True if successful."""
        try:
            self.vectorizer = joblib.load(self.model_path / "vectorizer.joblib")
            self.scaler = joblib.load(self.model_path / "scaler.joblib")
            self.movie_features = np.load(self.model_path / "movie_features.npy")
            self.movie_ids = joblib.load(self.model_path / "movie_ids.joblib")
            self.movie_metadata = joblib.load(self.model_path / "movie_metadata.joblib")
            return True
        except FileNotFoundError:
            return False

    def _get_user_profile(self, watched_movies: list[dict]) -> np.ndarray | None:
        """Create a user preference profile from watched movies."""
        if not watched_movies or self.vectorizer is None:
            return None

        watched_ids = set(m.get("trakt_id") or m.get("id") for m in watched_movies)
        indices = [i for i, mid in enumerate(self.movie_ids) if mid in watched_ids]

        if not indices:
            feature_texts = [self._create_feature_text(m) for m in watched_movies]
            watched_features = self.vectorizer.transform(feature_texts).toarray()

            numeric_features = []
            for m in watched_movies:
                numeric_features.append([
                    m.get("year", 2000) / 2030,
                    (m.get("runtime") or 100) / 300,
                    (m.get("vote_average") or 5.0) / 10,
                    (m.get("popularity") or 10) / 1000,
                ])
            if self.scaler:
                scaled_numeric = self.scaler.transform(numeric_features)
            else:
                scaled_numeric = np.array(numeric_features)
            watched_features = np.hstack([watched_features, scaled_numeric])
        else:
            watched_features = self.movie_features[indices]

        return np.mean(watched_features, axis=0).reshape(1, -1)

    def recommend(
        self,
        watched_movies: list[dict],
        candidate_movies: list[dict] | None = None,
        n: int = 10,
    ) -> list[dict]:
        """
        Recommend movies based on user's watch history.

        Args:
            watched_movies: User's watched movies
            candidate_movies: Movies to recommend from (defaults to all known movies)
            n: Number of recommendations

        Returns:
            List of recommended movies with scores
        """
        if self.movie_features is None:
            return []

        user_profile = self._get_user_profile(watched_movies)
        if user_profile is None:
            return []

        watched_ids = set(m.get("trakt_id") or m.get("id") for m in watched_movies)

        if candidate_movies:
            candidate_ids = [m["id"] for m in candidate_movies if m["id"] not in watched_ids]
            candidate_indices = [i for i, mid in enumerate(self.movie_ids) if mid in candidate_ids]

            if not candidate_indices:
                unwatched = [m for m in candidate_movies if m["id"] not in watched_ids]
                feature_texts = [self._create_feature_text(m) for m in unwatched]
                if not feature_texts:
                    return []
                candidate_features = self.vectorizer.transform(feature_texts).toarray()
                numeric_features = []
                for m in unwatched:
                    numeric_features.append([
                        m.get("year", 2000) / 2030,
                        (m.get("runtime") or 100) / 300,
                        (m.get("vote_average") or 5.0) / 10,
                        (m.get("popularity") or 10) / 1000,
                    ])
                if self.scaler:
                    scaled_numeric = self.scaler.transform(numeric_features)
                else:
                    scaled_numeric = np.array(numeric_features)
                candidate_features = np.hstack([candidate_features, scaled_numeric])
                candidate_metadata = {m["id"]: m for m in unwatched}
                candidate_movie_ids = [m["id"] for m in unwatched]
            else:
                candidate_features = self.movie_features[candidate_indices]
                candidate_movie_ids = [self.movie_ids[i] for i in candidate_indices]
                candidate_metadata = {mid: self.movie_metadata[mid] for mid in candidate_movie_ids}
        else:
            unwatched_indices = [
                i for i, mid in enumerate(self.movie_ids) if mid not in watched_ids
            ]
            if not unwatched_indices:
                return []
            candidate_features = self.movie_features[unwatched_indices]
            candidate_movie_ids = [self.movie_ids[i] for i in unwatched_indices]
            candidate_metadata = {mid: self.movie_metadata[mid] for mid in candidate_movie_ids}

        similarities = cosine_similarity(user_profile, candidate_features)[0]
        top_indices = np.argsort(similarities)[::-1][:n]

        recommendations = []
        for idx in top_indices:
            movie_id = candidate_movie_ids[idx]
            movie = candidate_metadata.get(movie_id, {})
            recommendations.append({
                "id": movie_id,
                "title": movie.get("title", "Unknown"),
                "year": movie.get("year"),
                "genres": movie.get("genres", []),
                "score": float(similarities[idx]),
                "vote_average": movie.get("vote_average"),
                "poster_path": movie.get("poster_path"),
            })

        return recommendations


def get_recommender(model_path: str = "ml/models") -> MovieRecommender:
    """Get a MovieRecommender instance, loading from disk if available."""
    recommender = MovieRecommender(model_path)
    recommender.load()
    return recommender
