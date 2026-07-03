"""Session repository — refresh-token session management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.session import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for :class:`Session`."""

    model = Session

    def get_by_jti(self, jti: str) -> Session | None:
        """Return a session by its refresh-token JTI."""
        return self.db.query(Session).filter(Session.refresh_token_jti == jti).first()

    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        jti: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> Session:
        """Persist a new session."""
        return self.create(
            {
                "user_id": user_id,
                "refresh_token_jti": jti,
                "expires_at": expires_at,
                "user_agent": user_agent,
                "ip_address": ip_address,
            }
        )

    def revoke(self, jti: str) -> bool:
        """Revoke a session by JTI. Returns ``True`` if revoked."""
        session = self.get_by_jti(jti)
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            self.db.flush()
            return True
        return False

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke every active session for a user. Returns count."""
        sessions = (
            self.db.query(Session)
            .filter(Session.user_id == user_id, Session.revoked_at.is_(None))
            .all()
        )
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.revoked_at = now
        self.db.flush()
        return len(sessions)
