"""AuditLog model — track user actions for compliance."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


# JSONB on PostgreSQL, plain JSON on SQLite (for tests).
_details_type = JSONB().with_variant(JSON(), "sqlite")


class AuditLog(Base, UUIDPKMixin, TimestampMixin):
    """An audit-trail entry for a user action."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(_details_type, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="audit_logs", lazy="noload")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog {self.action} {self.resource_type}>"
