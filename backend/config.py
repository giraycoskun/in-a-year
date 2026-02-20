import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_NAME = os.getenv("DATABASE_NAME", "inayear")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
POSTGRE_DATABASE_URL = os.getenv("POSTGRE_DATABASE_URL", f"postgresql+asyncpg://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")

logger.info(f"Database URL: {POSTGRE_DATABASE_URL}")

# Trakt API configuration
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID", "")
TRAKT_CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET", "")
TRAKT_API_URL = os.getenv("TRAKT_API_URL", "https://api.trakt.tv")

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Sync database URL for Celery (psycopg2)
SYNC_DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}",
)

ALLOWED_ORIGINS = [
    "http://localhost:3000"
]

# TMDB API configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_API_URL = os.getenv("TMDB_API_URL", "https://api.themoviedb.org/3")

# ML Model paths
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "ml/models")
