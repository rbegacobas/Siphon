from celery import Celery
from app.config import settings

celery_app = Celery(
    "ytdownloader",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=settings.max_concurrent_downloads,
    worker_max_tasks_per_child=50,  # Reciclar workers para evitar memory leaks
    task_soft_time_limit=600,  # 10 min soft limit
    task_time_limit=900,  # 15 min hard limit
    result_expires=3600,  # Resultados expiran en 1h
)

celery_app.autodiscover_tasks(["app.workers"])
