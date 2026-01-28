import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = os.getenv("DATABASE_NAME", "inayear")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
POSTGRE_DATABASE_URL = os.getenv("POSTGRE_DATABASE_URL", f"postgresql+asyncpg://postgres:postgres@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")

# Trakt API configuration
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID", "")
TRAKT_CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET", "")
TRAKT_API_URL = os.getenv("TRAKT_API_URL", "https://api.trakt.tv")
