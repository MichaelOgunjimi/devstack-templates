"""Async Redis client pool.

Usage:
    from core.redis import redis_client

    await redis_client.set("key", "value", ex=300)
    value = await redis_client.get("key")

    # Pub/sub
    from core.redis import get_pubsub
    pubsub = get_pubsub()
    await pubsub.subscribe("channel")

Requires REDIS_URL in .env.
"""

import redis.asyncio as aioredis
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)

redis_client: aioredis.Redis = aioredis.from_url(  # type: ignore[assignment]
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


def get_pubsub() -> aioredis.client.PubSub:
    """Create a new pub/sub instance from the shared client."""
    return redis_client.pubsub()


async def close_redis() -> None:
    """Close the Redis connection pool (call on app shutdown)."""
    await redis_client.aclose()
    logger.info("redis.closed")
