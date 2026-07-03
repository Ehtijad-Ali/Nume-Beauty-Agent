"""
Application settings.

Reads configuration from environment variables (and `.env` file when present)
using pydantic-settings v2. A single shared :class:`Settings` instance is
exposed through :func:`get_settings` so it can be injected via FastAPI's
``Depends`` and cached for the lifetime of the process.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env" if os.environ.get("APP_ENV") != "test" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "NUMÉ AI Marketing Assistant"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_version: str = "1.1.0"

    # --- Frontend URL (CORS) ---
    frontend_url: str = "http://localhost:5173"

    # --- Database ---
    database_url: str = "postgresql+psycopg2://nume:nume_secret@localhost:5432/nume"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- JWT ---
    jwt_secret: str = Field(
        default="change-me-to-a-long-random-string-in-production-please",
        description="Secret used to sign JWT tokens. MUST be overridden in production.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # --- Security ---
    bcrypt_rounds: int = 12

    # --- Uploads ---
    upload_path: str = "./uploads"
    max_upload_size_mb: int = 50

    # --- AI provider keys (stored but NOT used in Phase 1.1) ---
    openai_api_key: str = ""
    claude_api_key: str = ""
    gemini_api_key: str = ""

    # --- Logging ---
    log_level: str = "INFO"
    log_dir: str = "./logs"

    # --- Computed helpers ---------------------------------------------------
    @computed_field  # type: ignore[misc]
    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size expressed in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def upload_dir(self) -> Path:
        """Resolved upload directory as a :class:`Path`."""
        path = Path(self.upload_path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_directory(self) -> Path:
        """Resolved log directory as a :class:`Path`."""
        path = Path(self.log_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_production(self) -> bool:
        """Whether the app is running in production mode."""
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
