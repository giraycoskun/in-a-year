from fastapi import APIRouter

from src.api.routes import hardcover, stats, trakt

router = APIRouter()

router.include_router(hardcover.router, prefix="/hardcover", tags=["hardcover"])
router.include_router(trakt.router, prefix="/trakt", tags=["trakt"])
router.include_router(stats.router, prefix="/stats", tags=["stats"])
