from sqlalchemy.ext.asyncio import AsyncSession


class HardcoverService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_upload(self, data: dict) -> int:
        """Process uploaded Hardcover data and store in database."""
        raise NotImplementedError

    async def get_year_stats(self, year: int) -> dict:
        """Get reading statistics for a specific year."""
        raise NotImplementedError
