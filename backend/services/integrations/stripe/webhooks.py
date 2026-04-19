from datetime import UTC, datetime

import stripe
import structlog

from core.config import settings

from .client import StripeNotConfiguredError, _ensure_configured
from .schemas import WebhookEvent

logger = structlog.get_logger(__name__)


def construct_event(payload: bytes, sig_header: str) -> WebhookEvent:
    _ensure_configured()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise StripeNotConfiguredError("STRIPE_WEBHOOK_SECRET must be set to verify webhook signatures")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning("stripe.webhook.invalid_signature", error=str(exc))
        raise ValueError("Invalid Stripe webhook payload/signature") from exc

    webhook_event = WebhookEvent(
        id=event["id"],
        type=event["type"],
        data=dict(event["data"]),
        created=datetime.fromtimestamp(event["created"], tz=UTC),
    )
    logger.info("stripe.webhook.constructed", event_id=webhook_event.id, event_type=webhook_event.type)
    return webhook_event


async def handle_webhook(event: WebhookEvent) -> dict:
    logger.info("stripe.webhook.received", event_id=event.id, event_type=event.type)

    if event.type == "payment_intent.succeeded":
        logger.info("stripe.webhook.payment_succeeded", event_id=event.id)
        # Add your business logic here.
        return {"status": "handled", "event_type": event.type}

    if event.type == "payment_intent.payment_failed":
        logger.info("stripe.webhook.payment_failed", event_id=event.id)
        # Add your business logic here.
        return {"status": "handled", "event_type": event.type}

    if event.type == "account.updated":
        logger.info("stripe.webhook.account_updated", event_id=event.id)
        # Add your business logic here.
        return {"status": "handled", "event_type": event.type}

    logger.info("stripe.webhook.unhandled", event_id=event.id, event_type=event.type)
    return {"status": "ignored", "event_type": event.type}
