import asyncio
from datetime import timedelta
from typing import Any, BinaryIO

import structlog
from minio import Minio
from minio.error import S3Error

from core.config import settings
from core.exceptions import StorageNotConfiguredError

logger = structlog.get_logger(__name__)


def _get_client() -> Minio:
    if not all([settings.MINIO_ENDPOINT, settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY]):
        raise StorageNotConfiguredError(
            "MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY must be set",
        )

    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
    )


async def put_object(
    bucket: str,
    name: str,
    data: BinaryIO,
    length: int,
    content_type: str,
) -> Any:
    logger.info("storage.client.put_object.attempt", bucket=bucket, key=name, size=length)
    client = _get_client()
    loop = asyncio.get_running_loop()

    def _put() -> Any:
        data.seek(0)
        return client.put_object(
            bucket_name=bucket,
            object_name=name,
            data=data,
            length=length,
            content_type=content_type,
        )

    try:
        result = await loop.run_in_executor(None, _put)
    except Exception:
        logger.exception("storage.client.put_object.failed", bucket=bucket, key=name)
        raise

    logger.info("storage.client.put_object.success", bucket=bucket, key=name, size=length)
    return result


async def remove_object(bucket: str, name: str) -> None:
    logger.info("storage.client.remove_object.attempt", bucket=bucket, key=name)
    client = _get_client()
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, lambda: client.remove_object(bucket, name))
    except Exception:
        logger.exception("storage.client.remove_object.failed", bucket=bucket, key=name)
        raise
    logger.info("storage.client.remove_object.success", bucket=bucket, key=name)


async def list_objects(bucket: str, prefix: str) -> list[Any]:
    logger.info("storage.client.list_objects.attempt", bucket=bucket, prefix=prefix)
    client = _get_client()
    loop = asyncio.get_running_loop()
    try:
        objects = await loop.run_in_executor(
            None,
            lambda: list(client.list_objects(bucket, prefix=prefix, recursive=True)),
        )
    except Exception:
        logger.exception("storage.client.list_objects.failed", bucket=bucket, prefix=prefix)
        raise
    logger.info("storage.client.list_objects.success", bucket=bucket, count=len(objects))
    return objects


async def presigned_get(bucket: str, name: str, expires_hours: int = 1) -> str:
    logger.info(
        "storage.client.presigned_get.attempt",
        bucket=bucket,
        key=name,
        expires_hours=expires_hours,
    )
    client = _get_client()
    loop = asyncio.get_running_loop()
    try:
        url = await loop.run_in_executor(
            None,
            lambda: client.presigned_get_object(
                bucket_name=bucket,
                object_name=name,
                expires=timedelta(hours=expires_hours),
            ),
        )
    except Exception:
        logger.exception("storage.client.presigned_get.failed", bucket=bucket, key=name)
        raise
    logger.info("storage.client.presigned_get.success", bucket=bucket, key=name)
    return url


async def stat_object(bucket: str, name: str) -> bool:
    logger.info("storage.client.stat_object.attempt", bucket=bucket, key=name)
    client = _get_client()
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, lambda: client.stat_object(bucket, name))
        logger.info("storage.client.stat_object.exists", bucket=bucket, key=name)
        return True
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject"}:
            logger.info("storage.client.stat_object.missing", bucket=bucket, key=name)
            return False
        logger.exception("storage.client.stat_object.failed", bucket=bucket, key=name)
        raise


async def ensure_bucket(bucket: str) -> None:
    logger.info("storage.client.ensure_bucket.attempt", bucket=bucket)
    client = _get_client()
    loop = asyncio.get_running_loop()

    def _ensure() -> None:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

    try:
        await loop.run_in_executor(None, _ensure)
    except Exception:
        logger.exception("storage.client.ensure_bucket.failed", bucket=bucket)
        raise
    logger.info("storage.client.ensure_bucket.success", bucket=bucket)
