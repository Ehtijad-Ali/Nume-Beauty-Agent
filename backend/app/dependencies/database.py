"""Database dependency re-exported for ergonomic imports."""

from __future__ import annotations

from app.database.session import get_db

__all__ = ["get_db"]
