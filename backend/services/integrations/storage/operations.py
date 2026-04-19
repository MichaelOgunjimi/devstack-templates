import io
import mimetypes

import structlog

from core.config import settings
from core.exceptions import StorageNotConfiguredError

from .client import ensure_bucket, list_objects, presigned_get, put_object, remove_object, stat_object
from .schemas import StorageFile, UploadResult

logger = structlog.get_logger(__name__)


def _resolve_bucket(bucket: str | None) -> str:
    target_bucket = bucket or settings.MINIO_BUCKET
    if not target_bucket:
        raise StorageNotConfiguredError("MINIO_BUCKET must be set")
    return target_bucket


async def upload_file(
    file_bytes: bytes,
    filename: str,
    *,
    bucket: str | None = None,
    content_type: str = "application/octet-stream",
) -> UploadResult:
    target_bucket = _resolve_bucket(bucket)
    logger.info(
        "storage.upload_file.attempt",
        bucket=target_bucket,
        key=filename,
        size=len(file_bytes),
        content_type=content_type,
    )
    try:
        await ensure_bucket(target_bucket)
        await put_object(
            bucket=target_bucket,
            name=filename,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=content_type,
        )
        url = await presigned_get(target_bucket, filename)
    except Exception:
        logger.exception("storage.upload_file.failed", bucket=target_bucket, key=filename)
        raise

    logger.info("storage.upload_file.success", bucket=target_bucket, key=filename)
    return UploadResult(bucket=target_bucket, key=filename, size=len(file_bytes), url=url)


async def upload_image(
    file_bytes: bytes,
    filename: str,
    *,
    bucket: str | None = None,
) -> UploadResult:
    guessed_type, _ = mimetypes.guess_type(filename)
    logger.info("storage.upload_image.attempt", key=filename, guessed_type=guessed_type)
    if not guessed_type or not guessed_type.startswith("image/"):
        logger.error("storage.upload_image.invalid_content_type", key=filename, guessed_type=guessed_type)
        raise ValueError("upload_image requires an image filename/content type")

    return await upload_file(
        file_bytes=file_bytes,
        filename=filename,
        bucket=bucket,
        content_type=guessed_type,
    )


async def delete_file(filename: str, *, bucket: str | None = None) -> None:
    target_bucket = _resolve_bucket(bucket)
    logger.info("storage.delete_file.attempt", bucket=target_bucket, key=filename)
    try:
        await remove_object(target_bucket, filename)
    except Exception:
        logger.exception("storage.delete_file.failed", bucket=target_bucket, key=filename)
        raise
    logger.info("storage.delete_file.success", bucket=target_bucket, key=filename)


async def list_files(prefix: str = "", *, bucket: str | None = None) -> list[StorageFile]:
    target_bucket = _resolve_bucket(bucket)
    logger.info("storage.list_files.attempt", bucket=target_bucket, prefix=prefix)
    try:
        objects = await list_objects(target_bucket, prefix=prefix)
        files: list[StorageFile] = []
        for obj in objects:
            key = getattr(obj, "object_name", "")
            exists = await stat_object(target_bucket, key)
            if not exists:
                continue
            files.append(
                StorageFile(
                    bucket=target_bucket,
                    key=key,
                    size=int(getattr(obj, "size", 0) or 0),
                    last_modified=getattr(obj, "last_modified", None),
                    url=await presigned_get(target_bucket, key),
                )
            )
    except Exception:
        logger.exception("storage.list_files.failed", bucket=target_bucket, prefix=prefix)
        raise

    logger.info("storage.list_files.success", bucket=target_bucket, count=len(files), prefix=prefix)
    return files


async def get_presigned_url(
    filename: str,
    *,
    bucket: str | None = None,
    expires_hours: int = 1,
) -> str:
    target_bucket = _resolve_bucket(bucket)
    logger.info(
        "storage.get_presigned_url.attempt",
        bucket=target_bucket,
        key=filename,
        expires_hours=expires_hours,
    )
    try:
        url = await presigned_get(target_bucket, filename, expires_hours=expires_hours)
    except Exception:
        logger.exception("storage.get_presigned_url.failed", bucket=target_bucket, key=filename)
        raise
    logger.info("storage.get_presigned_url.success", bucket=target_bucket, key=filename)
    return url
