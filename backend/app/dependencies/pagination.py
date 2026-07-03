"""Pagination dependency."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationDep:
    """Common pagination query params."""

    page: int
    page_size: int
    search: str | None
    sort_by: str | None
    sort_dir: str

    @property
    def offset(self) -> int:
        """SQL OFFSET."""
        return (self.page - 1) * self.page_size


def pagination_dep(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search query"),
    sort_by: str | None = Query(default=None, description="Sort column"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort direction"),
) -> PaginationDep:
    """FastAPI dependency that produces a :class:`PaginationDep`."""
    return PaginationDep(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
