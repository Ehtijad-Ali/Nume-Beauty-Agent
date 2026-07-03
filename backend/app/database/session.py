"""
Database engine and session factory.

Uses synchronous SQLAlchemy 2.0 with psycopg2 — reliable, well-supported by
Alembic and trivially pool-able for production workloads.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

_settings = get_settings()

# Pool options only apply to connection-pooling dialects (Postgres, MySQL).
# SQLite (used in tests) uses SingletonThreadPool which doesn't accept them.
_engine_kwargs: dict = {
    "pool_pre_ping": True,
    "echo": _settings.app_debug and _settings.app_env == "development",
    "future": True,
}
if not _settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
    )

engine = create_engine(_settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency that yields a scoped database session.

    The session is automatically closed when the request finishes, even if an
    exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Convenient reusable type alias for dependency injection.
DBSession = Annotated[Session, "depends_on=get_db"]
