from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from core.config import settings
from core.database import get_session
from core.security import decode_token
from models.user import User

logger = structlog.get_logger(__name__)

_bearer_scheme = HTTPBearer()

# ---------------------------------------------------------------------------
# Redis dependency
# ---------------------------------------------------------------------------

_redis_client: Redis | None = None


def _get_redis_client() -> Redis:
    """Return the module-level Redis client, initialising it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Yield a Redis client for use as a FastAPI dependency."""
    yield _get_redis_client()


# ---------------------------------------------------------------------------
# Database dependency (re-exported from core for convenience)
# ---------------------------------------------------------------------------

get_db = get_session


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate the Bearer token and return the corresponding User.

    Raises HTTP 401 if the token is missing, invalid, or the user does not exist.
    """
    payload = decode_token(credentials.credentials)

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.exec(select(User).where(User.id == user_id))
    user = result.first()

    if not user:
        logger.warning("deps.get_current_user.not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Wrap get_current_user and raise 403 if the account is deactivated."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return user
