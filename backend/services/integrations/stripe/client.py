import stripe
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)


class StripeNotConfiguredError(Exception):
    """Raised when Stripe credentials are not configured."""


_configured = False


def configure() -> None:
    """Configure the Stripe SDK from settings."""
    global _configured

    if not settings.STRIPE_SECRET_KEY:
        raise StripeNotConfiguredError("STRIPE_SECRET_KEY must be set to use Stripe integration")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.max_network_retries = 2
    _configured = True
    logger.info("stripe.configured")


def _ensure_configured() -> None:
    """Ensure Stripe SDK is configured before making API calls."""
    if not _configured or stripe.api_key != settings.STRIPE_SECRET_KEY:
        configure()


def get_publishable_key() -> str:
    """Return the publishable key for frontend Stripe initialization."""
    if not settings.STRIPE_PUBLISHABLE_KEY:
        raise StripeNotConfiguredError(
            "STRIPE_PUBLISHABLE_KEY must be set to use Stripe frontend flows"
        )
    return settings.STRIPE_PUBLISHABLE_KEY


def get_connect_client_id() -> str | None:
    """Return Stripe Connect client ID when OAuth-based Connect is enabled."""
    return settings.STRIPE_CONNECT_CLIENT_ID or None
