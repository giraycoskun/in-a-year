from sqlalchemy.ext.asyncio import AsyncSession


class TraktService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_upload(self, data: dict) -> int:
        """Process uploaded Trakt data and store in database."""
        raise NotImplementedError

    async def get_year_stats(self, year: int) -> dict:
        """Get watching statistics for a specific year."""
        raise NotImplementedError
