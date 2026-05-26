import time

import structlog
from fastapi import APIRouter

from core.config import settings

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)


async def _ping_postgres() -> dict:
    """Check PostgreSQL connectivity."""
    from sqlalchemy import text

    from core.database import engine

    start = time.monotonic()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": ms}
    except Exception as exc:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "error", "latency_ms": ms, "error": str(exc)}


async def _ping_redis() -> dict:
    """Check Redis connectivity."""
    import redis.asyncio as aioredis

    start = time.monotonic()
    try:
        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await client.ping()
        await client.aclose()
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": ms}
    except Exception as exc:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "error", "latency_ms": ms, "error": str(exc)}


async def _ping_minio() -> dict:
    """Check MinIO connectivity."""
    from minio import Minio

    if not settings.MINIO_ENDPOINT:
        return {"status": "skipped", "reason": "not configured"}

    start = time.monotonic()
    try:
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        import asyncio

        await asyncio.get_running_loop().run_in_executor(None, client.list_buckets)
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": ms}
    except Exception as exc:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "error", "latency_ms": ms, "error": str(exc)}


async def _ping_elasticsearch() -> dict:
    """Check Elasticsearch connectivity."""
    if not settings.ELASTICSEARCH_URL:
        return {"status": "skipped", "reason": "not configured"}

    start = time.monotonic()
    try:
        from elasticsearch import AsyncElasticsearch

        es = AsyncElasticsearch(settings.ELASTICSEARCH_URL, request_timeout=2)
        await es.ping()
        await es.close()
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": ms}
    except Exception as exc:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "error", "latency_ms": ms, "error": str(exc)}


@router.get("/health")
async def health_check() -> dict:
    """Quick liveness probe."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Deep readiness check — pings all configured services."""
    checks: dict[str, dict] = {}
    checks["postgres"] = await _ping_postgres()
    checks["redis"] = await _ping_redis()
    checks["minio"] = await _ping_minio()
    checks["elasticsearch"] = await _ping_elasticsearch()

    overall = all(c["status"] in ("ok", "skipped") for c in checks.values())
    return {
        "status": "ok" if overall else "degraded",
        "version": "0.1.0",
        "services": checks,
    }
