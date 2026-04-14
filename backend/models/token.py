import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    # jti (JWT ID) is the unique identifier embedded in the refresh token payload.
    jti: str = Field(unique=True, index=True, max_length=36)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)

    user: Optional["User"] = Relationship(back_populates="refresh_tokens")
