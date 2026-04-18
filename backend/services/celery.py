"""Celery application factory and example tasks.

Usage:
    from services.celery import celery_app

    @celery_app.task
    def my_task(arg: str) -> str:
        return f"processed {arg}"

The Celery worker is started by docker-compose (celery service).
"""

from celery import Celery

from core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


# ---------------------------------------------------------------------------
# Example tasks — replace or extend as needed
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def example_task(self, payload: dict) -> dict:  # type: ignore[type-arg]
    """Example background task with retry logic."""
    import structlog

    logger = structlog.get_logger(__name__)
    logger.info("celery.example_task.start", payload=payload)

    try:
        result = {"status": "done", "input": payload}
        logger.info("celery.example_task.success", result=result)
        return result
    except Exception as exc:
        logger.error("celery.example_task.failed", exc=str(exc))
        raise self.retry(exc=exc)
