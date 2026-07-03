"""
Database initialisation helper.

Runs idempotent seed operations after migrations:
  * Ensures the four default roles exist (admin, manager, editor, viewer).
  * Ensures a default admin user exists (configurable via env).

Run via:  ``python -m app.database.init_db``
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_ROLES = ["admin", "manager", "editor", "viewer"]


def _seed_roles(db: Session) -> None:
    """Create the four default roles if missing."""
    for name in DEFAULT_ROLES:
        existing = db.query(Role).filter(Role.name == name).first()
        if not existing:
            db.add(Role(name=name, description=f"{name.capitalize()} role"))
            logger.info("Created role: %s", name)


def _seed_admin(db: Session) -> None:
    """Create a default admin user if none exists."""
    if db.query(User).filter(User.is_superuser.is_(True)).first():
        return

    settings = get_settings()
    admin_email = "admin@nume.ai"
    admin_password = "Admin@12345"  # demo only — change immediately

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    user = User(
        email=admin_email,
        full_name="NUMÉ Admin",
        hashed_password=hash_password(admin_password),
        is_active=True,
        is_superuser=True,
        role_id=admin_role.id if admin_role else None,
    )
    db.add(user)
    logger.info("Created superuser: %s (password: %s)", admin_email, admin_password)


def init_db() -> None:
    """Seed default roles and admin user."""
    db = SessionLocal()
    try:
        _seed_roles(db)
        db.commit()
        _seed_admin(db)
        db.commit()
        logger.info("Database initialisation complete.")
    except Exception:
        db.rollback()
        logger.exception("Database initialisation failed.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
