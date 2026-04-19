import asyncio
from typing import Any

import stripe
import structlog

from .client import _ensure_configured
from .schemas import PaymentIntentCreate, PaymentIntentResponse, RefundCreate, RefundResponse

logger = structlog.get_logger(__name__)


async def _run_in_executor(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def _map_payment_intent(payment_intent: Any) -> PaymentIntentResponse:
    return PaymentIntentResponse(
        id=payment_intent["id"],
        amount=payment_intent["amount"],
        currency=payment_intent["currency"],
        status=payment_intent["status"],
        client_secret=payment_intent.get("client_secret"),
        metadata=dict(payment_intent.get("metadata", {})),
    )


async def create_payment_intent(
    data: PaymentIntentCreate, *, idempotency_key: str | None = None
) -> PaymentIntentResponse:
    _ensure_configured()
    logger.info("stripe.payment_intent.create.attempt", amount=data.amount, currency=data.currency)

    payload: dict[str, Any] = {
        "amount": data.amount,
        "currency": data.currency,
        "automatic_payment_methods": {"enabled": True},
    }
    if data.customer_id:
        payload["customer"] = data.customer_id
    if data.metadata:
        payload["metadata"] = data.metadata
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key

    payment_intent = await _run_in_executor(stripe.PaymentIntent.create, **payload)
    result = _map_payment_intent(payment_intent)

    logger.info(
        "stripe.payment_intent.create.success",
        payment_intent_id=result.id,
        status=result.status,
    )
    return result


async def capture_payment(payment_intent_id: str) -> PaymentIntentResponse:
    _ensure_configured()
    logger.info("stripe.payment_intent.capture.attempt", payment_intent_id=payment_intent_id)

    payment_intent = await _run_in_executor(stripe.PaymentIntent.capture, payment_intent_id)
    result = _map_payment_intent(payment_intent)

    logger.info(
        "stripe.payment_intent.capture.success",
        payment_intent_id=result.id,
        status=result.status,
    )
    return result


async def refund_payment(data: RefundCreate) -> RefundResponse:
    _ensure_configured()
    logger.info("stripe.refund.create.attempt", payment_intent_id=data.payment_intent_id)

    payload: dict[str, Any] = {"payment_intent": data.payment_intent_id}
    if data.amount is not None:
        payload["amount"] = data.amount
    if data.reason:
        payload["reason"] = data.reason

    refund = await _run_in_executor(stripe.Refund.create, **payload)
    result = RefundResponse(
        id=refund["id"],
        amount=refund["amount"],
        status=refund["status"],
        payment_intent_id=refund.get("payment_intent") or data.payment_intent_id,
    )
    logger.info("stripe.refund.create.success", refund_id=result.id, status=result.status)
    return result


async def get_payment(payment_intent_id: str) -> PaymentIntentResponse:
    _ensure_configured()
    logger.info("stripe.payment_intent.get.attempt", payment_intent_id=payment_intent_id)

    payment_intent = await _run_in_executor(stripe.PaymentIntent.retrieve, payment_intent_id)
    result = _map_payment_intent(payment_intent)

    logger.info(
        "stripe.payment_intent.get.success",
        payment_intent_id=result.id,
        status=result.status,
    )
    return result
