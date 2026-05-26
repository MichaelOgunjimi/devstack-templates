from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from core.config import settings

logger = structlog.get_logger(__name__)

# Engine created once at module load.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables defined by SQLModel metadata.

    Called once at application startup. In production, prefer Alembic migrations
    over calling this directly; this is kept for convenience in development.
    """
    async with engine.begin() as conn:
        # Import models so their metadata is registered before create_all.
        import models.token  # noqa: F401
        import models.user  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("database.init_db.complete")
