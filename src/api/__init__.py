from fastapi import APIRouter

from src.api.routes import github, hardcover, spotify, stats, trakt

router = APIRouter()

router.include_router(spotify.router, prefix="/spotify", tags=["spotify"])
router.include_router(github.router, prefix="/github", tags=["github"])
router.include_router(hardcover.router, prefix="/hardcover", tags=["hardcover"])
router.include_router(trakt.router, prefix="/trakt", tags=["trakt"])
router.include_router(stats.router, prefix="/stats", tags=["stats"])
