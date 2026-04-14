"""Shared pytest fixtures.

Uses an in-memory SQLite engine to isolate tests from a real PostgreSQL
database. Overrides DATABASE_URL and the FastAPI DB/Redis dependencies.
"""

import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# ---------------------------------------------------------------------------
# Engine — SQLite in-memory for fast, isolated tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per test session."""
    import models.token  # noqa: F401 — ensure metadata registered
    import models.user  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
def mock_redis() -> AsyncMock:
    """Return a mock Redis client that satisfies the get_redis dependency."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = True
    redis.delete.return_value = 1
    return redis


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """Return an httpx AsyncClient wired to the test DB and mock Redis."""
    from main import app
    from api.deps import get_db, get_redis

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create and return a test user in the test database."""
    from core.security import hash_password
    from models.user import User

    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
