import structlog
import httpx

from core.config import settings
from core.exceptions import NotificationServiceError, NotificationServiceNotConfiguredError

logger = structlog.get_logger(__name__)


async def send(
    event: str,
    recipient_email: str,
    data: dict,
    channels: list[str] | None = None,
) -> None:
    """Send a notification via the configured Notification Service.

    Raises NotificationServiceNotConfiguredError if NOTIFY_URL or NOTIFY_API_KEY
    are not set. Raises NotificationServiceError if the HTTP call fails. Never
    silently swallows errors — callers must handle or propagate them.
    """
    if channels is None:
        channels = ["email"]

    if not settings.NOTIFY_URL or not settings.NOTIFY_API_KEY:
        raise NotificationServiceNotConfiguredError(
            "NOTIFY_URL and NOTIFY_API_KEY must be set to send notifications"
        )

    payload = {
        "event": event,
        "recipient_email": recipient_email,
        "data": data,
        "channels": channels,
    }

    logger.info(
        "notify.send.attempt",
        event=event,
        recipient_email=recipient_email,
        channels=channels,
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.NOTIFY_URL.rstrip('/')}/send",
                json=payload,
                headers={"X-API-Key": settings.NOTIFY_API_KEY},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "notify.send.http_error",
                status_code=exc.response.status_code,
                body=exc.response.text,
            )
            raise NotificationServiceError(
                message=f"Notification Service returned {exc.response.status_code}: {exc.response.text}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("notify.send.request_error", error=str(exc))
            raise NotificationServiceError(
                message=f"Notification Service request failed: {exc}",
                status_code=503,
            ) from exc

    logger.info("notify.send.success", event=event, recipient_email=recipient_email)
