"""File storage abstraction. Local backend for V1, S3-ready interface for V2."""
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import settings


class StorageBackend(Protocol):
    def save(self, file_obj: BinaryIO, filename: str) -> str: ...
    def url(self, key: str) -> str: ...


class LocalStorage:
    """Stores files on the local filesystem (V1)."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_obj: BinaryIO, filename: str) -> str:
        ext = os.path.splitext(filename)[1]
        key = f"{uuid.uuid4().hex}{ext}"
        dest = self.base_dir / key
        with dest.open("wb") as out:
            shutil.copyfileobj(file_obj, out)
        return key

    def url(self, key: str) -> str:
        return f"/static/uploads/{key}"


def get_storage() -> StorageBackend:
    # V2: branch on settings.STORAGE_BACKEND == "s3" -> S3Storage(...)
    return LocalStorage(settings.STORAGE_LOCAL_DIR)


storage = get_storage()
