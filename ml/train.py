"""
Script to train the movie recommender model.
Fetches popular movies from TMDB and trains the content-based model.

Usage:
    uv run python -m ml.train
"""

import asyncio
import os

import httpx
from dotenv import load_dotenv

from ml.model import MovieRecommender

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_API_URL = "https://api.themoviedb.org/3"


async def fetch_popular_movies(pages: int = 50) -> list[dict]:
    """Fetch popular movies from TMDB."""
    movies = []

    async with httpx.AsyncClient() as client:
        for page in range(1, pages + 1):
            response = await client.get(
                f"{TMDB_API_URL}/movie/popular",
                params={"api_key": TMDB_API_KEY, "page": page},
            )
            if response.status_code != 200:
                print(f"Error fetching page {page}: {response.status_code}")
                continue

            data = response.json()
            for movie in data.get("results", []):
                movies.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
                    "genres": movie.get("genre_ids", []),
                    "vote_average": movie.get("vote_average", 0),
                    "popularity": movie.get("popularity", 0),
                    "poster_path": movie.get("poster_path"),
                    "runtime": None,
                })

            print(f"Fetched page {page}/{pages} ({len(movies)} movies)")

    return movies


async def fetch_movie_details(movie_ids: list[int]) -> dict[int, dict]:
    """Fetch detailed info for movies (including runtime and genres)."""
    details = {}

    async with httpx.AsyncClient() as client:
        for i, movie_id in enumerate(movie_ids):
            response = await client.get(
                f"{TMDB_API_URL}/movie/{movie_id}",
                params={"api_key": TMDB_API_KEY},
            )
            if response.status_code == 200:
                data = response.json()
                details[movie_id] = {
                    "runtime": data.get("runtime"),
                    "genres": [g["name"] for g in data.get("genres", [])],
                }

            if (i + 1) % 100 == 0:
                print(f"Fetched details for {i + 1}/{len(movie_ids)} movies")

            await asyncio.sleep(0.05)

    return details


async def main():
    if not TMDB_API_KEY:
        print("Error: TMDB_API_KEY not set")
        return

    print("Fetching popular movies from TMDB...")
    movies = await fetch_popular_movies(pages=50)
    print(f"Fetched {len(movies)} movies")

    print("Fetching movie details...")
    movie_ids = [m["id"] for m in movies]
    details = await fetch_movie_details(movie_ids[:500])

    for movie in movies:
        if movie["id"] in details:
            movie["runtime"] = details[movie["id"]].get("runtime")
            movie["genres"] = details[movie["id"]].get("genres", movie["genres"])

    print("Training model...")
    recommender = MovieRecommender()
    recommender.train(movies)

    print("Saving model...")
    recommender.save()

    print("Done! Model saved to ml/models/")


if __name__ == "__main__":
    asyncio.run(main())
