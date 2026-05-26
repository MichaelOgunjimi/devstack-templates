from datetime import timedelta
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    DATABASE_ECHO: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URL(self) -> str:  # noqa: N802
        """Synchronous database URL for sync-only contexts."""
        url = make_url(self.DATABASE_URL)
        if url.drivername == "postgresql+asyncpg":
            url = url.set(drivername="postgresql+psycopg")
        elif url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        elif url.drivername == "sqlite+aiosqlite":
            url = url.set(drivername="sqlite")
        return url.render_as_string(hide_password=False)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery (requires redis)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # JWT
    JWT_SECRET: str = "change-me-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    FACEBOOK_CLIENT_ID: str = ""
    FACEBOOK_CLIENT_SECRET: str = ""

    # Notification Service
    NOTIFY_URL: str = ""
    NOTIFY_API_KEY: str = ""

    # App
    BACKEND_URL: str = "http://localhost:3101"
    FRONTEND_URL: str = "http://localhost:3100"
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str = ""

    # Storage (optional)
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""

    # Stripe (optional)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CONNECT_CLIENT_ID: str = ""

    # Email / SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = ""
    SMTP_USE_TLS: bool = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expire(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

    @property
    def email_verification_token_expire(self) -> timedelta:
        return timedelta(hours=self.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

    @property
    def password_reset_token_expire(self) -> timedelta:
        return timedelta(minutes=self.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
