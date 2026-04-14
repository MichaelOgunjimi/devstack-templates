"""Notification Service API client.

Wraps the notification-system REST API at:
  {NOTIFY_URL}/api/v1

Example:
    await send(
        event_type="user.welcome",
        payload={"name": "John"},
        recipient_email="john@example.com",
    )
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from core.config import settings
from core.exceptions import NotificationServiceError, NotificationServiceNotConfiguredError

logger = structlog.get_logger(__name__)


class NotifyPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotifyChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotifyEventStatus(StrEnum):
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotifyRecipient(BaseModel):
    user_id: str | None = None
    channels: list[NotifyChannel]
    email: str | None = None
    phone: str | None = None
    webhook_url: str | None = None


class NotifyEventCreate(BaseModel):
    event_type: str
    recipients: list[NotifyRecipient]
    payload: dict[str, Any]
    priority: NotifyPriority = NotifyPriority.MEDIUM
    template_id: uuid.UUID | None = None
    idempotency_key: str | None = None


class NotifyEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    priority: NotifyPriority
    status: NotifyEventStatus
    notification_ids: list[uuid.UUID]
    created_at: datetime


class NotifyTemplateCreate(BaseModel):
    name: str
    channel: NotifyChannel
    subject: str | None = None
    body: str
    variables: list[str] = Field(default_factory=list)


class NotifyTemplateUpdate(BaseModel):
    name: str | None = None
    channel: NotifyChannel | None = None
    subject: str | None = None
    body: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class NotifyTemplateResponse(BaseModel):
    id: uuid.UUID
    api_key_id: uuid.UUID
    name: str
    channel: NotifyChannel
    subject: str | None = None
    body: str
    variables: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


def _base_url() -> str:
    if not settings.NOTIFY_URL or not settings.NOTIFY_API_KEY:
        raise NotificationServiceNotConfiguredError(
            "NOTIFY_URL and NOTIFY_API_KEY must be set to use notifications"
        )
    return f"{settings.NOTIFY_URL.rstrip('/')}/api/v1"


def _headers() -> dict[str, str]:
    return {"X-API-Key": settings.NOTIFY_API_KEY}


@asynccontextmanager
async def _client() -> AsyncIterator[httpx.AsyncClient]:
    """Create an API client configured for the Notification Service."""
    async with httpx.AsyncClient(
        base_url=_base_url(),
        headers=_headers(),
        timeout=10.0,
    ) as client:
        yield client


def _raise_service_error(exc: httpx.HTTPStatusError, operation: str) -> None:
    status_code = exc.response.status_code
    response_body = exc.response.text
    logger.error(
        "notify.http_error",
        operation=operation,
        status_code=status_code,
        response_body=response_body,
    )
    raise NotificationServiceError(
        message=f"{operation} failed with {status_code}: {response_body}",
        status_code=status_code,
    ) from exc


def _raise_connection_error(exc: httpx.RequestError, operation: str) -> None:
    logger.error("notify.connection_error", operation=operation, error=str(exc))
    raise NotificationServiceError(
        message=f"{operation} failed: could not reach Notification Service",
        status_code=503,
    ) from exc


async def send(
    event_type: str,
    payload: dict[str, Any],
    recipient_email: str,
    *,
    recipient_user_id: str | None = None,
    priority: NotifyPriority = NotifyPriority.MEDIUM,
    template_id: uuid.UUID | None = None,
    idempotency_key: str | None = None,
) -> NotifyEventResponse:
    """Send a single event to one email recipient."""
    event = NotifyEventCreate(
        event_type=event_type,
        recipients=[
            NotifyRecipient(
                user_id=recipient_user_id,
                channels=[NotifyChannel.EMAIL],
                email=recipient_email,
            )
        ],
        payload=payload,
        priority=priority,
        template_id=template_id,
        idempotency_key=idempotency_key,
    )
    return await _send_event(event)


async def _send_event(data: NotifyEventCreate) -> NotifyEventResponse:
    """Send a single event payload to /events."""
    logger.info(
        "notify.send_event.attempt",
        event_type=data.event_type,
        priority=data.priority.value,
    )
    try:
        async with _client() as client:
            response = await client.post(
                "/events",
                json=data.model_dump(mode="json", exclude_none=True),
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "send_event")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "send_event")

    event = NotifyEventResponse.model_validate(response.json())
    logger.info("notify.send_event.success", event_id=str(event.id), status=event.status.value)
    return event


async def send_batch(events: list[NotifyEventCreate]) -> list[NotifyEventResponse]:
    """Send multiple events to /events/batch."""
    logger.info("notify.send_batch.attempt", event_count=len(events))
    try:
        async with _client() as client:
            response = await client.post(
                "/events/batch",
                json=[event.model_dump(mode="json", exclude_none=True) for event in events],
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "send_batch")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "send_batch")

    data = response.json()
    items = data if isinstance(data, list) else data.get("items", [])
    result = [NotifyEventResponse.model_validate(item) for item in items]
    logger.info("notify.send_batch.success", event_count=len(result))
    return result


async def get_event(event_id: uuid.UUID) -> NotifyEventResponse | None:
    """Fetch event status by ID."""
    logger.info("notify.get_event.attempt", event_id=str(event_id))
    try:
        async with _client() as client:
            response = await client.get(f"/events/{event_id}")
            if response.status_code == 404:
                logger.info("notify.get_event.not_found", event_id=str(event_id))
                return None
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "get_event")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "get_event")

    event = NotifyEventResponse.model_validate(response.json())
    logger.info("notify.get_event.success", event_id=str(event.id), status=event.status.value)
    return event


async def list_templates(
    *,
    page: int = 1,
    per_page: int = 20,
    channel: NotifyChannel | None = None,
) -> list[NotifyTemplateResponse]:
    """List templates with optional pagination and channel filtering."""
    params: dict[str, str | int] = {"page": page, "per_page": per_page}
    if channel is not None:
        params["channel"] = channel.value

    logger.info("notify.list_templates.attempt", page=page, per_page=per_page, channel=channel)
    try:
        async with _client() as client:
            response = await client.get("/templates", params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "list_templates")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "list_templates")

    data = response.json()
    items = data if isinstance(data, list) else data.get("items", [])
    templates = [NotifyTemplateResponse.model_validate(item) for item in items]
    logger.info("notify.list_templates.success", template_count=len(templates))
    return templates


async def get_template(template_id: uuid.UUID) -> NotifyTemplateResponse | None:
    """Fetch a single template by ID."""
    logger.info("notify.get_template.attempt", template_id=str(template_id))
    try:
        async with _client() as client:
            response = await client.get(f"/templates/{template_id}")
            if response.status_code == 404:
                logger.info("notify.get_template.not_found", template_id=str(template_id))
                return None
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "get_template")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "get_template")

    template = NotifyTemplateResponse.model_validate(response.json())
    logger.info("notify.get_template.success", template_id=str(template.id))
    return template


async def create_template(data: NotifyTemplateCreate) -> NotifyTemplateResponse:
    """Create a template."""
    logger.info("notify.create_template.attempt", name=data.name, channel=data.channel.value)
    try:
        async with _client() as client:
            response = await client.post(
                "/templates",
                json=data.model_dump(mode="json", exclude_none=True),
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "create_template")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "create_template")

    template = NotifyTemplateResponse.model_validate(response.json())
    logger.info("notify.create_template.success", template_id=str(template.id))
    return template


async def update_template(
    template_id: uuid.UUID,
    data: NotifyTemplateUpdate,
) -> NotifyTemplateResponse:
    """Update a template."""
    logger.info("notify.update_template.attempt", template_id=str(template_id))
    try:
        async with _client() as client:
            response = await client.put(
                f"/templates/{template_id}",
                json=data.model_dump(mode="json", exclude_none=True),
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "update_template")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "update_template")

    template = NotifyTemplateResponse.model_validate(response.json())
    logger.info("notify.update_template.success", template_id=str(template.id))
    return template


async def delete_template(template_id: uuid.UUID) -> None:
    """Delete a template."""
    logger.info("notify.delete_template.attempt", template_id=str(template_id))
    try:
        async with _client() as client:
            response = await client.delete(f"/templates/{template_id}")
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_service_error(exc, "delete_template")
    except httpx.RequestError as exc:
        _raise_connection_error(exc, "delete_template")

    logger.info("notify.delete_template.success", template_id=str(template_id))
