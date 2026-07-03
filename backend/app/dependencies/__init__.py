"""FastAPI dependencies (auth, DB, pagination)."""

from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_roles,
    require_superuser,
    RoleChecker,
)
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_roles",
    "require_superuser",
    "RoleChecker",
    "get_db",
    "PaginationDep",
]
