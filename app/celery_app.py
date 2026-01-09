from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "testit",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'app.tasks.periodic_cleanup_task',
        'schedule': settings.session_cleanup_interval_minutes * 60.0,  # Run every N minutes
    },
}
