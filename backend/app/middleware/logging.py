"""
Request/response logging middleware.

Generates a per-request ``X-Request-ID``, logs the request method/path, the
authenticated subject (when present in the JWT), the response status and the
total duration. Useful for debugging and audit trails.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("nume.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request/response with a request ID and timing."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Skip noisy endpoints
        path = request.url.path
        if path in {"/health", "/healthz", "/metrics"} or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        start = time.perf_counter()

        # Tag request state so handlers can read it
        request.state.request_id = request_id
        request.state.start_time = start

        # Extract user subject from JWT if present
        auth_header = request.headers.get("Authorization", "")
        subject = None
        if auth_header.lower().startswith("bearer "):
            try:
                from app.core.security import decode_token

                payload = decode_token(auth_header[7:].strip())
                subject = payload.get("sub")
            except Exception:  # noqa: BLE001
                subject = None

        logger.info(
            "request.start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "query": str(request.url.query) if request.url.query else None,
                "user_id": subject,
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request.error",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"

        logger.info(
            "request.end",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "method": request.method,
                "path": path,
                "user_id": subject,
            },
        )
        return response
