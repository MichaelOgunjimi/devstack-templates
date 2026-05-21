import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from utils.datetime import utc_now

if TYPE_CHECKING:
    from models.user import User


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"  # type: ignore[assignment]
    __table_args__ = ({"extend_existing": True},)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    # jti (JWT ID) is the unique identifier embedded in the refresh token payload.
    jti: str = Field(unique=True, index=True, max_length=36)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)

    user: Optional["User"] = Relationship(back_populates="refresh_tokens")
