from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger

from backend.api import router as api_router
from backend.config import ALLOWED_ORIGINS
from backend.db.database import close_db, init_db
from backend.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting backend")
    await init_db()
    yield
    logger.info("Stopping backend")
    await close_db()


app = FastAPI(
    title="In a Year",
    description="Show your year in stats from connected services",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - start) * 1000
        logger.exception(
            "Request failed: {} {} ({:.2f} ms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - start) * 1000
    logger.info(
        "{} {} -> {} ({:.2f} ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy"}


@app.get("/")
async def root():
    # redirect to API docs
    return RedirectResponse(url="/docs")
