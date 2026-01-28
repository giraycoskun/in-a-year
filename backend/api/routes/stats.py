from fastapi import APIRouter

router = APIRouter()


@router.get("/{year}")
async def get_yearly_stats(year: int):
    """Get combined stats from all services for a specific year."""
    return {
        "year": year,
        "hardcover": {},
        "trakt": {},
    }
