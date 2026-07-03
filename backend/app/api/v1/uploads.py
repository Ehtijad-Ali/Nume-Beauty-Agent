"""Uploads endpoints — list, get, upload (file), update, delete, download."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.upload import UploadRead
from app.services.upload_service import UploadService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UploadRead],
    summary="List uploads",
)
def list_uploads(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    category: str | None = Query(default=None),
    status: str | None = Query(
        default=None, pattern="^(queued|uploading|completed|failed)$"
    ),
) -> dict:
    """List uploads with filters."""
    service = UploadService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        category=category,
        status=status,
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.get(
    "/{upload_id}",
    response_model=UploadRead,
    summary="Get an upload",
)
def get_upload(
    upload_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return an upload by ID."""
    return UploadService(db).get(upload_id)


@router.post(
    "",
    response_model=UploadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
)
async def upload_file(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(..., description="File to upload"),
    category: str = Form(default="other"),
    description: str | None = Form(default=None),
) -> dict:
    """Upload a file to local storage and create an :class:`Upload` record."""
    service = UploadService(db)
    content = await file.read()
    return service.save_file(
        filename=file.filename or "untitled",
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        category=category,
        description=description,
        actor_id=actor.id,
    )


@router.delete(
    "/{upload_id}",
    response_model=MessageResponse,
    summary="Delete an upload",
)
def delete_upload(
    upload_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete an upload record and remove the underlying file."""
    UploadService(db).delete(upload_id)
    return {"message": "Upload deleted"}


@router.get(
    "/{upload_id}/download",
    summary="Download an upload",
)
def download_upload(
    upload_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    """Stream the file content for an upload."""
    service = UploadService(db)
    upload = service.get(upload_id)
    path = service.get_file_path(upload_id)
    return FileResponse(
        path=path,
        media_type=upload.mime_type,
        filename=upload.original_filename,
    )
