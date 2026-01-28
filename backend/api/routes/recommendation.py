from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.schemas.recommendation import (
    LatestMovie,
    RecommendationResponse,
    RetrainResponse,
    TrendingMovie,
)
from backend.services.recommendation import RecommendationService

router = APIRouter()


@router.get("/movies", response_model=RecommendationResponse)
async def get_movie_recommendations(
    user_id: str,
    n: int = Query(10, ge=1, le=50),
    include_trending: bool = Query(True),
    include_latest: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized movie recommendations for a user.

    Uses the user's watch history to recommend movies from trending and latest releases.
    If the ML model is trained, recommendations are based on content similarity.
    Otherwise, returns popular movies sorted by popularity.
    """
    service = RecommendationService(db)
    try:
        return await service.get_recommendations(
            user_id=user_id,
            n=n,
            include_trending=include_trending,
            include_latest=include_latest,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=list[TrendingMovie])
async def get_trending_movies(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get currently trending movies from Trakt."""
    service = RecommendationService(db)
    try:
        return await service.fetch_trending_movies_trakt(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=list[LatestMovie])
async def get_latest_movies(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get latest/now playing movies from TMDB."""
    service = RecommendationService(db)
    try:
        movies = await service.fetch_latest_movies_tmdb(limit=limit)
        if not movies:
            raise HTTPException(status_code=503, detail="TMDB API key not configured")
        return movies
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain", response_model=RetrainResponse)
async def retrain_model(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrain the recommendation model with fresh data from TMDB and Trakt.
    This fetches popular and trending movies and rebuilds the content-based model.
    """
    service = RecommendationService(db)
    try:
        return await service.retrain_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
