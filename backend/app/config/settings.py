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

    # --- Vector store (Qdrant) — Phase 2.2 ---
    # "embedded" persists to qdrant_path with no server; "remote" connects to
    # qdrant_url; "memory" is for tests. NOTE: embedded mode is single-process
    # only — multi-worker deployments (e.g. docker-compose --workers 2) must
    # use qdrant_mode=remote with a Qdrant server.
    qdrant_mode: Literal["embedded", "remote", "memory"] = "embedded"
    qdrant_path: str = "./qdrant_data"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "nume_knowledge"

    # --- Embeddings — Phase 2.2 ---
    # "fastembed" runs a local ONNX model; "hashing" is a deterministic
    # dependency-free fallback used in tests.
    embedding_provider: Literal["fastembed", "hashing"] = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_batch_size: int = 32
    embedding_max_retries: int = 3
    embedding_retry_backoff: float = 1.0  # seconds; doubles per attempt

    # --- AI provider keys ---
    openai_api_key: str = ""
    claude_api_key: str = ""
    gemini_api_key: str = ""

    # --- LLM completion — Phase 2.3 ---
    # "claude", "openai" and "gemini" call the real APIs (need the matching
    # key above); "mock" is a deterministic, dependency-free provider used in
    # tests/dev.
    llm_provider: Literal["claude", "openai", "gemini", "mock"] = "claude"
    claude_model: str = "claude-opus-4-8"
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-2.5-flash"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.4  # OpenAI only; Claude Opus 4.8 rejects it

    # --- RAG engine — Phase 2.3 ---
    rag_top_k: int = 6
    rag_score_threshold: float = 0.15
    rag_max_context_chars: int = 8000
    rag_max_chunks_per_document: int = 3  # keep retrieval multi-document
    rag_history_messages: int = 6  # conversation-memory turns sent to the LLM
    rag_allow_general_knowledge: bool = False  # answer outside the KB?
    rag_priority_boost: float = 0.08  # rank bonus for priority doc categories

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
