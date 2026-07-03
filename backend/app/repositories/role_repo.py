"""Role repository."""

from __future__ import annotations

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository for :class:`Role`."""

    model = Role

    def get_by_name(self, name: str) -> Role | None:
        """Return a role by its unique name."""
        return self.db.query(Role).filter(Role.name == name).first()
