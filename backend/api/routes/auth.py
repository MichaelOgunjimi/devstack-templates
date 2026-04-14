from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.deps import get_current_active_user, get_db, get_redis
from core.security import create_access_token, decode_token, hash_password
from models.token import RefreshToken
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from schemas.user import UserRead, UserUpdate
from services.auth import authenticate_user, create_user_tokens, revoke_refresh_token

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenResponse:
    """Create a new user account and return tokens."""
    result = await db.exec(select(User).where(User.email == body.email))
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("auth.register.success", user_id=str(user.id))
    return await create_user_tokens(user, db, redis)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenResponse:
    """Authenticate with email + password and return tokens."""
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("auth.login.success", user_id=str(user.id))
    return await create_user_tokens(user, db, redis)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token.

    Lookup order: Redis first (fast path), then DB (fallback + Redis backfill).
    """
    payload = decode_token(body.refresh_token)

    jti: str | None = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_type: str | None = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    redis_key = f"refresh:{jti}"

    # Fast path: check Redis.
    user_id = await redis.get(redis_key)

    if not user_id:
        # Fallback: check DB and backfill Redis if still valid.
        result = await db.exec(select(RefreshToken).where(RefreshToken.jti == jti))
        db_token = result.first()

        if not db_token or db_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user_id = str(db_token.user_id)
        # Backfill Redis for subsequent requests.
        remaining_ttl = int((db_token.expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining_ttl > 0:
            await redis.setex(redis_key, remaining_ttl, user_id)

    # Issue a new access token only (keep the same refresh token).
    new_access_token = create_access_token({"sub": user_id})
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=body.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> None:
    """Revoke the supplied refresh token."""
    try:
        payload = decode_token(body.refresh_token)
        jti: str | None = payload.get("jti")
        if jti:
            await revoke_refresh_token(jti, db, redis)
    except HTTPException:
        # Token already invalid; treat as successful logout.
        pass


@router.get("/me", response_model=UserRead)
async def get_me(
    user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return user


@router.put("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.me.updated", user_id=str(user.id))
    return user
