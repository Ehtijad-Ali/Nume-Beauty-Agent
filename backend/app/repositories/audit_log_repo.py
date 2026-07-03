"""AuditLog repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for :class:`AuditLog`."""

    model = AuditLog

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def record(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an audit-log entry (without committing)."""
        return self.create(
            {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "status_code": status_code,
                "details": details,
            }
        )

    def list_for_user(self, user_id: uuid.UUID, *, limit: int = 50) -> list[AuditLog]:
        """Return recent audit entries for a user."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
