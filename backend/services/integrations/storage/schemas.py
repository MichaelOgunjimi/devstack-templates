from datetime import datetime

from pydantic import BaseModel


class StorageFile(BaseModel):
    bucket: str
    key: str
    size: int
    content_type: str | None = None
    last_modified: datetime | None = None
    url: str | None = None


class UploadResult(BaseModel):
    bucket: str
    key: str
    size: int
    url: str
