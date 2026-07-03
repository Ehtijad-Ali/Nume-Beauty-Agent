"""CORS middleware configuration."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings


def setup_cors(app: FastAPI) -> None:
    """Register the CORS middleware on the FastAPI app."""
    settings = get_settings()
    origins = [
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
        "http://172.26.192.1:5173",  # Network IP for development
        "http://172.26.192.1:5174",
        "http://172.26.192.1:5175",
        "http://192.168.1.9:5175",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Request-ID"],
    )
