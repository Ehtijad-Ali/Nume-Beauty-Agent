"""
Generic repository base.

Implements common CRUD operations so each specific repository only has to
override or add what's unique to its model.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic CRUD repository."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def get(self, id_: uuid.UUID | str) -> ModelT | None:
        """Fetch a single record by primary key."""
        return self.db.get(self.model, id_)

    def get_by_id(self, id_: uuid.UUID | str) -> ModelT:
        """Fetch by id or raise ValueError."""
        obj = self.get(id_)
        if obj is None:
            raise ValueError(f"{self.model.__name__} {id_} not found")
        return obj

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[ModelT], int]:
        """
        Return a paginated, filtered, sorted list.

        Returns a ``(items, total)`` tuple.
        """
        stmt = select(self.model)

        # Equality filters
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        # Free-text search across provided columns (ILIKE)
        if search and search_fields:
            from sqlalchemy import or_

            clauses = []
            for field_name in search_fields:
                column = getattr(self.model, field_name, None)
                if column is not None:
                    clauses.append(column.ilike(f"%{search}%"))
            if clauses:
                stmt = stmt.where(or_(*clauses))

        # Count first — wrap the filtered statement in a subquery
        from sqlalchemy import func

        count_query = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_query).scalar_one()

        # Sort
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                stmt = stmt.order_by(column.desc() if order_dir.lower() == "desc" else column.asc())
        else:
            # Default: newest first
            if hasattr(self.model, "created_at"):
                stmt = stmt.order_by(self.model.created_at.desc())

        stmt = stmt.offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create(self, data: dict[str, Any]) -> ModelT:
        """Create a new record from a dict."""
        obj = self.model(**data)  # type: ignore[call-arg]
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelT, data: dict[str, Any]) -> ModelT:
        """Update an existing record with a dict of partial changes."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        """Delete a record."""
        self.db.delete(obj)
        self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()
