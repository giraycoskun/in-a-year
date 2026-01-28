from fastapi import APIRouter

from backend.api.routes import hardcover, recommendation, stats, trakt

router = APIRouter()

router.include_router(hardcover.router, prefix="/hardcover", tags=["hardcover"])
router.include_router(trakt.router, prefix="/trakt", tags=["trakt"])
router.include_router(stats.router, prefix="/stats", tags=["stats"])
router.include_router(recommendation.router, prefix="/recommendations", tags=["recommendations"])
