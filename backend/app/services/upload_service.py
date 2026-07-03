"""Upload service."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.config.settings import get_settings
from app.models.upload import Upload
from app.repositories.upload_repo import UploadRepository
from app.schemas.upload import UploadCreate, UploadUpdate


def _compute_checksum(file_bytes: bytes) -> str:
    """Return the SHA-256 checksum of the given bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


class UploadService:
    """Business logic for file uploads."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UploadRepository(db)
        self.settings = get_settings()

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Upload], int]:
        """List uploads with filters."""
        filters: dict[str, Any] = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, upload_id: uuid.UUID) -> Upload:
        """Return an upload by ID or raise."""
        upload = self.repo.get(upload_id)
        if not upload:
            raise NotFoundError("Upload not found")
        return upload

    def save_file(
        self,
        *,
        filename: str,
        content: bytes,
        mime_type: str,
        category: str = "other",
        description: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> Upload:
        """Persist a file to disk and create an :class:`Upload` record."""
        # Enforce size limit
        if len(content) > self.settings.max_upload_size_bytes:
            raise BadRequestError(
                f"File exceeds maximum size of {self.settings.max_upload_size_mb} MB"
            )

        # Save under uploads/<year>/<month>/<uuid>_<filename>
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        rel_dir = Path(str(now.year)) / now.strftime("%m")
        abs_dir = self.settings.upload_dir / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}_{filename}"
        abs_path = abs_dir / safe_name
        rel_path = str(rel_dir / safe_name)

        abs_path.write_bytes(content)
        checksum = _compute_checksum(content)

        payload = UploadCreate(
            filename=safe_name,
            original_filename=filename,
            mime_type=mime_type,
            size=len(content),
            storage_path=rel_path,
            storage_type="local",
            category=category,
            status="completed",
            checksum=checksum,
            description=description,
        )
        data = payload.model_dump()
        if actor_id:
            data["uploaded_by_id"] = actor_id
        upload = self.repo.create(data)
        self.db.commit()
        return upload

    def register_external(
        self,
        payload: UploadCreate,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> Upload:
        """Register an upload that has already been stored elsewhere (e.g. S3)."""
        data = payload.model_dump()
        if actor_id:
            data["uploaded_by_id"] = actor_id
        upload = self.repo.create(data)
        self.db.commit()
        return upload

    def update(self, upload_id: uuid.UUID, payload: UploadUpdate) -> Upload:
        """Update an upload's metadata."""
        upload = self.get(upload_id)
        data = payload.model_dump(exclude_unset=True)
        updated = self.repo.update(upload, data)
        self.db.commit()
        return updated

    def delete(self, upload_id: uuid.UUID) -> None:
        """Delete an upload record and remove the file from disk."""
        upload = self.get(upload_id)
        # Best-effort file removal
        try:
            if upload.storage_type == "local":
                abs_path = self.settings.upload_dir / upload.storage_path
                if abs_path.exists():
                    abs_path.unlink()
        except OSError:
            pass
        self.repo.delete(upload)
        self.db.commit()

    def get_file_path(self, upload_id: uuid.UUID) -> Path:
        """Return the absolute path of an uploaded file (local storage only)."""
        upload = self.get(upload_id)
        if upload.storage_type != "local":
            raise BadRequestError("Upload is not stored locally")
        return self.settings.upload_dir / upload.storage_path
