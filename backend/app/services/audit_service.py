"""Audit service — thin wrapper around the audit-log repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.audit_log_repo import AuditLogRepository


class AuditService:
    """Audit-trail helper exposed to other services and middleware."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditLogRepository(db)

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
        commit: bool = False,
    ) -> None:
        """Record an audit-log entry."""
        self.repo.record(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            details=details,
        )
        if commit:
            self.db.commit()
