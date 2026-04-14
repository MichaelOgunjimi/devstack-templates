import uuid
from datetime import datetime, timezone

import structlog
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

logger = structlog.get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Create a signed JWT access token with an expiry embedded in the payload."""
    expire = datetime.now(timezone.utc) + settings.access_token_expire
    payload = {**data, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> tuple[str, str]:
    """Create a signed JWT refresh token.

    Returns (token, jti) where jti is the unique identifier stored in Redis/DB
    so the token can be revoked without decoding it on every request.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + settings.refresh_token_expire
    payload = {**data, "exp": expire, "jti": jti, "type": "refresh"}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """Decode and verify a JWT.

    Raises HTTP 401 if the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning("security.decode_token.invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
