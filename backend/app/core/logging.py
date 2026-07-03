"""
Logging configuration.

Configures stdlib logging with a JSON formatter when running in production
and a human-readable formatter in development. A rotating file handler writes
to ``logs/app.log``.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from app.config.settings import get_settings

_CONFIGURED = False


def setup_logging() -> None:
    """Configure root logging once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter: logging.Formatter
    if settings.is_production:
        from pythonjsonlogger import jsonlogger

        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "time", "levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    root = logging.getLogger()
    root.setLevel(level)
    # Remove any pre-existing handlers so re-init is safe.
    for h in list(root.handlers):
        root.removeHandler(h)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Rotating file handler
    try:
        log_path: Path = settings.log_directory / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # Filesystem might not be writable in some environments; don't crash.
        pass

    # Tame noisy libs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.app_debug else logging.WARNING
    )

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Ensures logging is configured."""
    setup_logging()
    return logging.getLogger(name)
