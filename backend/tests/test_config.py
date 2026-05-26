from core.config import Settings


def test_sync_database_url_uses_psycopg_for_async_postgres_url() -> None:
    settings = Settings(DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/app")

    assert settings.SYNC_DATABASE_URL == "postgresql+psycopg://user:password@localhost:5432/app"


def test_sync_database_url_uses_psycopg_for_plain_postgres_url() -> None:
    settings = Settings(DATABASE_URL="postgresql://user:password@localhost:5432/app")

    assert settings.SYNC_DATABASE_URL == "postgresql+psycopg://user:password@localhost:5432/app"


def test_sync_database_url_uses_plain_sqlite_for_async_sqlite_url() -> None:
    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")

    assert settings.SYNC_DATABASE_URL == "sqlite:///:memory:"
