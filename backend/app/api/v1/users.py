"""Users CRUD endpoints."""

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
from app.schemas.user import UserCreate, UserList, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserList],
    summary="List users",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def list_users(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    is_active: bool | None = Query(default=None),
    role_id: uuid.UUID | None = Query(default=None),
) -> dict:
    """List users with pagination, search and filters."""
    service = UserService(db)
    items, total = service.list_users(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        is_active=is_active,
        role_id=role_id,
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
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def get_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return a single user by ID."""
    return UserService(db).get(user_id)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    dependencies=[Depends(require_roles("admin"))],
)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Create a new user (admin only)."""
    return UserService(db).create(payload, actor_id=actor.id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user",
    dependencies=[Depends(require_roles("admin", "manager"))],
)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Update an existing user."""
    return UserService(db).update(user_id, payload)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    dependencies=[Depends(require_roles("admin"))],
)
def delete_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Delete a user (admin only). Cannot delete self or superusers."""
    UserService(db).delete(user_id, actor_id=actor.id)
    return {"message": "User deleted"}
