"""Shared/common schemas — pagination, error envelopes, generic responses."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: str | None = Field(default=None, description="Search query")
    sort_by: str | None = Field(default=None, description="Column to sort by")
    sort_dir: str | None = Field(default="asc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response envelope."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class IDResponse(BaseModel):
    """Response containing only an ID."""

    id: str


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: dict

    model_config = {"from_attributes": True}
