"""Notification Service integration.

Sends notifications via your Notification Service at NOTIFY_URL.

The Notification Service API:
  POST {NOTIFY_URL}/api/v1/events
  Header: X-API-Key: {NOTIFY_API_KEY}

  Body:
  {
    "event_type": "user.welcome",
    "recipients": [
      {
        "user_id": "optional-user-id",
        "channels": ["email"],
        "email": "user@example.com",
        "phone": "+15551234567",    # only if sms channel
        "webhook_url": "https://..."  # only if webhook channel
      }
    ],
    "payload": { "name": "John", ... },
    "priority": "medium"           # low | medium | high | critical
  }

Usage:
  from services.integrations.notify import send

  await send(
      event_type="user.welcome",
      recipient_email="user@example.com",
      payload={"name": user.full_name},
  )
"""

import structlog
import httpx

from core.config import settings
from core.exceptions import NotificationServiceError, NotificationServiceNotConfiguredError

logger = structlog.get_logger(__name__)


async def send(
    event_type: str,
    payload: dict,
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
    recipient_webhook_url: str | None = None,
    recipient_user_id: str | None = None,
    channels: list[str] | None = None,
    priority: str = "medium",
) -> None:
    """Send a notification via the Notification Service.

    Args:
        event_type:            Matches a template in the Notification Service
                               e.g. "user.welcome", "password.reset"
        payload:               Template variables e.g. {"name": "John"}
        recipient_email:       Required if "email" is in channels
        recipient_phone:       Required if "sms" is in channels (E.164 format)
        recipient_webhook_url: Required if "webhook" is in channels
        recipient_user_id:     Optional — links notification to a user record
        channels:              Defaults to ["email"]
        priority:              low | medium | high | critical

    Raises:
        NotificationServiceNotConfiguredError: NOTIFY_URL or NOTIFY_API_KEY not set
        NotificationServiceError:              HTTP call to Notification Service failed
    """
    if not settings.NOTIFY_URL or not settings.NOTIFY_API_KEY:
        raise NotificationServiceNotConfiguredError(
            "NOTIFY_URL and NOTIFY_API_KEY must be set to send notifications"
        )

    if channels is None:
        channels = ["email"]

    recipient: dict = {"channels": channels}
    if recipient_user_id:
        recipient["user_id"] = recipient_user_id
    if recipient_email:
        recipient["email"] = recipient_email
    if recipient_phone:
        recipient["phone"] = recipient_phone
    if recipient_webhook_url:
        recipient["webhook_url"] = recipient_webhook_url

    body = {
        "event_type": event_type,
        "recipients": [recipient],
        "payload": payload,
        "priority": priority,
    }

    logger.info(
        "notify.send.attempt",
        event_type=event_type,
        channels=channels,
        recipient_email=recipient_email,
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.NOTIFY_URL.rstrip('/')}/api/v1/events",
                json=body,
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
                message=f"Could not reach Notification Service: {exc}",
                status_code=503,
            ) from exc

    logger.info("notify.send.success", event_type=event_type)
