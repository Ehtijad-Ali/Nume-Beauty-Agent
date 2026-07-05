"""
Database initialisation helper.

Runs idempotent seed operations after migrations:
  * Ensures the four default roles exist (admin, manager, editor, viewer).
  * Ensures a default admin user exists (configurable via env).
  * Ensures the default knowledge base categories exist.

Run via:  ``python -m app.database.init_db``
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.category import Category
from app.models.role import Role
from app.models.user import User
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_ROLES = ["admin", "manager", "editor", "viewer"]

# (name, slug, description, color)
DEFAULT_CATEGORIES = [
    ("Brand Guidelines", "brand-guidelines", "Voice, tone, visual identity and brand rules.", "#8B5CF6"),
    ("Product Information", "product-information", "Product specs, ingredients, catalogues and FAQs.", "#0EA5E9"),
    ("Marketing Material", "marketing-material", "Campaign briefs, ad copy and promotional content.", "#F59E0B"),
    ("Reports & Analytics", "reports-analytics", "Performance reports, research and data exports.", "#10B981"),
    ("Legal & Compliance", "legal-compliance", "Policies, terms, regulatory and compliance documents.", "#EF4444"),
    ("Other", "other", "Anything that does not fit the other categories.", "#6B7280"),
]


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


def _seed_categories(db: Session) -> None:
    """Create the default knowledge base categories if missing."""
    for name, slug, description, color in DEFAULT_CATEGORIES:
        existing = db.query(Category).filter(Category.slug == slug).first()
        if not existing:
            db.add(Category(name=name, slug=slug, description=description, color=color))
            logger.info("Created category: %s", name)


def init_db() -> None:
    """Seed default roles, admin user and knowledge base categories."""
    db = SessionLocal()
    try:
        _seed_roles(db)
        db.commit()
        _seed_admin(db)
        db.commit()
        _seed_categories(db)
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
