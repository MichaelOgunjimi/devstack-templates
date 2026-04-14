import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(unique=True, index=True, max_length=255)
    # Nullable: OAuth-only users never set a password.
    hashed_password: Optional[str] = Field(default=None, nullable=True)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    # String annotations let SQLModel resolve cross-module relationships lazily.
    oauth_accounts: list["OAuthAccount"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


class OAuthAccount(SQLModel, table=True):
    __tablename__ = "oauth_accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    # provider is one of: google, github, facebook
    provider: str = Field(max_length=50)
    provider_account_id: str = Field(max_length=255)
    access_token: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)

    user: Optional[User] = Relationship(back_populates="oauth_accounts")
