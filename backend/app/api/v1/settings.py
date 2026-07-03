"""Settings CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user, require_roles
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate
from app.services.setting_service import SettingService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SettingRead],
    summary="List settings",
)
def list_settings(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    category: str | None = Query(default=None),
) -> dict:
    """List settings with optional category filter."""
    service = SettingService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        category=category,
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    # Mask sensitive values via SettingRead.from_model
    masked = [SettingRead.from_model(item) for item in items]
    return {
        "items": masked,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.get(
    "/{setting_id}",
    response_model=SettingRead,
    summary="Get a setting",
)
def get_setting(
    setting_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> SettingRead:
    """Return a setting by ID."""
    return SettingRead.from_model(SettingService(db).get(setting_id))


@router.get(
    "/by-key/{key}",
    response_model=SettingRead,
    summary="Get a setting by key",
)
def get_setting_by_key(
    key: str,
    db: Annotated[Session, Depends(get_db)],
) -> SettingRead:
    """Return a setting by its unique key."""
    return SettingRead.from_model(SettingService(db).get_by_key(key))


@router.post(
    "",
    response_model=SettingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a setting",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def create_setting(
    payload: SettingCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> SettingRead:
    """Create a new setting."""
    s = SettingService(db).create(payload, actor_id=actor.id)
    return SettingRead.from_model(s)


@router.put(
    "/by-key/{key}",
    response_model=SettingRead,
    summary="Upsert a setting by key",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def upsert_setting(
    key: str,
    payload: SettingUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> SettingRead:
    """Insert or update a setting by key."""
    service = SettingService(db)
    existing = None
    try:
        existing = service.get_by_key(key)
    except Exception:  # noqa: BLE001
        existing = None

    if existing is None:
        from app.schemas.setting import SettingCreate

        create_payload = SettingCreate(
            key=key,
            value=payload.value,
            category=payload.category or "general",
            is_sensitive=payload.is_sensitive or False,
            description=payload.description,
        )
        s = service.create(create_payload, actor_id=actor.id)
    else:
        s = service.update(existing.id, payload, actor_id=actor.id)
    return SettingRead.from_model(s)


@router.patch(
    "/{setting_id}",
    response_model=SettingRead,
    summary="Update a setting",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def update_setting(
    setting_id: uuid.UUID,
    payload: SettingUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> SettingRead:
    """Update an existing setting."""
    s = SettingService(db).update(setting_id, payload, actor_id=actor.id)
    return SettingRead.from_model(s)


@router.delete(
    "/{setting_id}",
    response_model=MessageResponse,
    summary="Delete a setting",
    dependencies=[Depends(require_roles("admin"))],
)
def delete_setting(
    setting_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a setting."""
    SettingService(db).delete(setting_id)
    return {"message": "Setting deleted"}
