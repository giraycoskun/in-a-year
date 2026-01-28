from sqlalchemy.ext.asyncio import AsyncSession


class GithubService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_upload(self, data: dict) -> int:
        """Process uploaded GitHub data and store in database."""
        raise NotImplementedError

    async def get_year_stats(self, year: int) -> dict:
        """Get contribution statistics for a specific year."""
        raise NotImplementedError
