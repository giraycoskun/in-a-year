from celery import Celery

from backend.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery(
    "in-a-year",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["src.worker.tasks.trakt"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)
