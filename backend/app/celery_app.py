from celery import Celery
from backend.app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "trafficguard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "collect-system-metrics": {
        "task": "backend.app.tasks.collect_system_metrics",
        "schedule": 60.0,
    },
    "check-model-drift": {
        "task": "backend.app.tasks.check_model_drift",
        "schedule": 3600.0,
    },
}
