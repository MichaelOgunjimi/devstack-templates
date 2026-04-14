import io

import structlog
from minio import Minio
from minio.error import S3Error

from core.config import settings
from core.exceptions import StorageNotConfiguredError

logger = structlog.get_logger(__name__)


def _get_client() -> Minio:
    """Build a Minio client from environment settings.

    Raises StorageNotConfiguredError if any required env var is missing.
    """
    if not all([settings.MINIO_ENDPOINT, settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY]):
        raise StorageNotConfiguredError(
            "MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY must be set"
        )
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
    )


async def upload_file(file_bytes: bytes, filename: str, bucket: str | None = None) -> str:
    """Upload bytes to MinIO and return the public object URL.

    Raises StorageNotConfiguredError if MinIO env vars are not set.
    Raises minio.error.S3Error on upload failure.
    """
    target_bucket = bucket or settings.MINIO_BUCKET
    client = _get_client()

    logger.info("storage.upload.attempt", filename=filename, bucket=target_bucket)

    # Minio client is sync; run in thread for async compatibility.
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: client.put_object(
            target_bucket,
            filename,
            io.BytesIO(file_bytes),
            length=len(file_bytes),
        ),
    )

    url = f"https://{settings.MINIO_ENDPOINT}/{target_bucket}/{filename}"
    logger.info("storage.upload.success", filename=filename, url=url)
    return url


async def delete_file(filename: str, bucket: str | None = None) -> None:
    """Delete an object from MinIO.

    Raises StorageNotConfiguredError if MinIO env vars are not set.
    Raises minio.error.S3Error if the deletion fails.
    """
    target_bucket = bucket or settings.MINIO_BUCKET
    client = _get_client()

    logger.info("storage.delete.attempt", filename=filename, bucket=target_bucket)

    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: client.remove_object(target_bucket, filename),
    )

    logger.info("storage.delete.success", filename=filename)
