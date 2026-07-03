"""
Shared pytest fixtures.

Uses an in-memory SQLite database for speed (no PostgreSQL required for the
unit tests). Note that JSONB columns fall back to JSON on SQLite via
SQLAlchemy's dialect-aware typing, but our tests don't heavily exercise JSON
columns.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator

# Make sure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Override settings BEFORE importing app modules — force SQLite + tiny secret
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-test-secret-test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "true"

from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402, F401  (register models)
from app.database import session as session_module  # noqa: E402
from app.config.settings import get_settings  # noqa: E402

# Reset cached settings so env overrides take effect
get_settings.cache_clear()
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory SQLite engine per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Iterator[Session]:
    """Yield a session bound to the in-memory engine."""
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session, monkeypatch) -> Iterator[TestClient]:
    """FastAPI test client with the DB dependency overridden."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app = create_app()
    # Override the get_db dependency
    from app.dependencies.database import get_db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_roles(db_session):
    """Seed the four default roles and return them as a dict."""
    from app.models.role import Role

    roles = {}
    for name in ["admin", "manager", "editor", "viewer"]:
        r = Role(name=name, description=f"{name} role", is_system=True)
        db_session.add(r)
        roles[name] = r
    db_session.commit()
    return roles
