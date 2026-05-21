import uuid

import structlog
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from core.config import settings
from core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_verification_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.token import RefreshToken
from models.user import OAuthAccount, User
from schemas.auth import (
    ChangePasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from schemas.user import UserUpdate
from utils.datetime import utc_now

logger = structlog.get_logger(__name__)

# Redis key prefix for refresh tokens: refresh:{jti} -> user_id
_REDIS_PREFIX = "refresh"


def _redis_key(jti: str) -> str:
    return f"{_REDIS_PREFIX}:{jti}"


def _parse_user_id(user_id: str | None) -> uuid.UUID:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub'",
        )
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        ) from exc


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    result = await db.execute(select(User).where(col(User.email) == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if user.hashed_password is None or not verify_password(password, user.hashed_password):
        return None
    return user


async def register_user(body: RegisterRequest, db: AsyncSession) -> User:
    """Create a new user account, raising 409 if the email is already used."""
    result = await db.execute(select(User).where(col(User.email) == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.register.success", user_id=str(user.id))
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


async def refresh_access_token(
    refresh_token_str: str,
    db: AsyncSession,
    redis: Redis,
) -> TokenResponse:
    """Validate a refresh token and issue a new access token."""
    payload = decode_token(refresh_token_str)

    jti: str | None = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    redis_key = _redis_key(jti)
    user_id = await redis.get(redis_key)

    if not user_id:
        result = await db.execute(select(RefreshToken).where(col(RefreshToken.jti) == jti))
        db_token = result.scalar_one_or_none()
        if not db_token or db_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        if db_token.expires_at < utc_now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )
        user_id = str(db_token.user_id)
        remaining_ttl = int((db_token.expires_at - utc_now()).total_seconds())
        if remaining_ttl > 0:
            await redis.setex(redis_key, remaining_ttl, user_id)

    parsed_user_id = _parse_user_id(user_id)
    user_result = await db.execute(select(User).where(col(User.id) == parsed_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return TokenResponse(
        access_token=create_access_token({"sub": user_id}),
        refresh_token=refresh_token_str,
    )


async def update_user(user: User, body: UserUpdate, db: AsyncSession) -> User:
    """Apply partial current-user updates."""
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    user.updated_at = utc_now()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.me.updated", user_id=str(user.id))
    return user


async def verify_user_email(token: str, db: AsyncSession) -> tuple[User, bool]:
    """Decode an email verification token and mark the user as verified."""
    payload = decode_token(token)
    if payload.get("type") != "verify_email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user_id = _parse_user_id(payload.get("sub"))
    result = await db.execute(select(User).where(col(User.id) == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return user, False

    user.is_verified = True
    user.updated_at = utc_now()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.verify_email.success", user_id=str(user.id))
    return user, True


async def initiate_password_reset(email: str, db: AsyncSession) -> User | None:
    """Return the password-backed user for a reset request, if one exists."""
    result = await db.execute(select(User).where(col(User.email) == email))
    user = result.scalar_one_or_none()
    if user and user.hashed_password:
        logger.info("auth.forgot_password.requested", user_id=str(user.id))
        return user
    logger.info("auth.forgot_password.generic_response", email=email)
    return None


async def reset_user_password(body: ResetPasswordRequest, db: AsyncSession) -> User:
    """Decode a reset token and update the user's password."""
    payload = decode_token(body.token)
    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user_id = _parse_user_id(payload.get("sub"))
    result = await db.execute(select(User).where(col(User.id) == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    user.updated_at = utc_now()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.reset_password.success", user_id=str(user.id))
    return user


async def change_user_password(user: User, body: ChangePasswordRequest, db: AsyncSession) -> None:
    """Verify the current password and replace it with a new one."""
    if not user.hashed_password or not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = hash_password(body.new_password)
    user.updated_at = utc_now()
    db.add(user)
    await db.commit()
    logger.info("auth.change_password.success", user_id=str(user.id))


async def send_verify_email(*, email: str, name: str, user_id: str) -> None:
    token = create_verification_token(user_id)
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    logger.info("auth.email.verify", email=email, name=name, link=link)


async def send_reset_email(*, email: str, name: str, user_id: str) -> None:
    token = create_password_reset_token(user_id)
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    logger.info("auth.email.password_reset", email=email, name=name, link=link)


async def send_password_changed_email(*, email: str, name: str, user_id: str) -> None:
    logger.info("auth.email.password_changed", email=email, name=name, user_id=user_id)


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
    user_result = await db.execute(select(User).where(col(User.email) == email))
    user = user_result.scalar_one_or_none()

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
