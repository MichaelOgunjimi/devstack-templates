import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from core.config import settings
from core.security import create_access_token, create_refresh_token, verify_password
from models.token import RefreshToken
from models.user import OAuthAccount, User
from schemas.auth import TokenResponse
from utils.datetime import utc_now

logger = structlog.get_logger(__name__)

# Redis key prefix for refresh tokens: refresh:{jti} -> user_id
_REDIS_PREFIX = "refresh"


def _redis_key(jti: str) -> str:
    return f"{_REDIS_PREFIX}:{jti}"


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    result = await db.execute(select(User).where(col(User.email) == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user_tokens(user: User, db: AsyncSession, redis: Redis) -> TokenResponse:
    """Issue a fresh access + refresh token pair for the user.

    Stores the refresh token in both Redis (fast lookup) and PostgreSQL
    (source of truth / audit trail).
    """
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token_str, jti = create_refresh_token(token_data)

    expires_at = utc_now() + settings.refresh_token_expire

    # Persist to DB first so we have the source of truth before Redis.
    db_token = RefreshToken(
        user_id=user.id,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.commit()

    # Cache in Redis; TTL matches the token lifetime in seconds.
    ttl_seconds = int(settings.refresh_token_expire.total_seconds())
    await redis.setex(_redis_key(jti), ttl_seconds, str(user.id))

    logger.info("auth.tokens_created", user_id=str(user.id), jti=jti)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


async def revoke_refresh_token(jti: str, db: AsyncSession, redis: Redis) -> None:
    """Mark a refresh token as revoked in both Redis and DB."""
    # Remove from Redis immediately.
    await redis.delete(_redis_key(jti))

    # Mark revoked in DB for audit purposes.
    result = await db.execute(select(RefreshToken).where(col(RefreshToken.jti) == jti))
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.revoked = True
        db.add(db_token)
        await db.commit()

    logger.info("auth.token_revoked", jti=jti)


async def get_or_create_oauth_user(
    db: AsyncSession,
    provider: str,
    provider_account_id: str,
    email: str,
    full_name: str | None,
    access_token: str,
) -> User:
    """Find or create a User via OAuth.

    Auto-link rule: if a User with the same email already exists, link the
    OAuthAccount to that user instead of creating a duplicate account.
    """
    # Check if this OAuth account is already linked.
    result = await db.execute(
        select(OAuthAccount).where(
            col(OAuthAccount.provider) == provider,
            col(OAuthAccount.provider_account_id) == provider_account_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        # Known OAuth account — fetch the linked user.
        user_result = await db.execute(select(User).where(col(User.id) == oauth_account.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            logger.error(
                "auth.oauth.linked_user_missing",
                provider=provider,
                provider_account_id=provider_account_id,
            )
            raise ValueError("Linked OAuth user record not found")
        # Update access token in case it changed.
        oauth_account.access_token = access_token
        db.add(oauth_account)
        await db.commit()
        logger.info("auth.oauth.existing_account", provider=provider, user_id=str(user.id))
        return user

    # No existing OAuth account — check if email already belongs to a user.
    result = await db.execute(select(User).where(col(User.email) == email))
    user = result.scalar_one_or_none()

    if not user:
        # Brand-new user via OAuth.
        user = User(
            email=email,
            full_name=full_name,
            is_verified=True,  # Email verified by the OAuth provider.
        )
        db.add(user)
        await db.flush()  # Populate user.id before creating OAuthAccount FK.
        logger.info("auth.oauth.new_user_created", provider=provider, user_id=str(user.id))
    else:
        logger.info(
            "auth.oauth.linked_to_existing_user",
            provider=provider,
            user_id=str(user.id),
        )

    new_oauth = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_account_id=provider_account_id,
        access_token=access_token,
    )
    db.add(new_oauth)
    await db.commit()
    await db.refresh(user)
    return user
