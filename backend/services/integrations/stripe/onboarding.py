import asyncio
from datetime import UTC, datetime
from typing import Any

import stripe
import structlog

from core.config import settings

from .client import _ensure_configured
from .schemas import ConnectAccountCreate, OnboardingLink

logger = structlog.get_logger(__name__)


async def _run_in_executor(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def _default_refresh_url() -> str:
    return f"{settings.BACKEND_URL.rstrip('/')}/api/v1/integrations/stripe/connect/refresh"


def _default_return_url() -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/settings/payments/connect"


async def create_connect_account(data: ConnectAccountCreate) -> str:
    _ensure_configured()
    logger.info(
        "stripe.connect.account.create.attempt",
        email=data.email,
        country=data.country,
        has_connect_client_id=bool(settings.STRIPE_CONNECT_CLIENT_ID),
    )

    account = await _run_in_executor(
        stripe.Account.create,
        email=data.email,
        country=data.country,
        business_type=data.business_type,
        controller={
            "fees": {"payer": "application"},
            "losses": {"payments": "application"},
            "stripe_dashboard": {"type": "express"},
        },
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
    )

    account_id = account["id"]
    logger.info("stripe.connect.account.create.success", account_id=account_id)
    return account_id


async def get_onboarding_link(
    account_id: str, *, refresh_url: str | None = None, return_url: str | None = None
) -> OnboardingLink:
    _ensure_configured()

    resolved_refresh_url = refresh_url or _default_refresh_url()
    resolved_return_url = return_url or _default_return_url()
    logger.info("stripe.connect.onboarding_link.create.attempt", account_id=account_id)

    account_link = await _run_in_executor(
        stripe.AccountLink.create,
        account=account_id,
        refresh_url=resolved_refresh_url,
        return_url=resolved_return_url,
        type="account_onboarding",
    )
    link = OnboardingLink(
        url=account_link["url"],
        expires_at=datetime.fromtimestamp(account_link["expires_at"], tz=UTC),
    )
    logger.info("stripe.connect.onboarding_link.create.success", account_id=account_id)
    return link


async def get_dashboard_link(account_id: str) -> str:
    _ensure_configured()
    logger.info("stripe.connect.dashboard_link.create.attempt", account_id=account_id)

    login_link = await _run_in_executor(stripe.Account.create_login_link, account_id)
    url = login_link["url"]
    logger.info("stripe.connect.dashboard_link.create.success", account_id=account_id)
    return url
