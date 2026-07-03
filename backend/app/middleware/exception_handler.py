"""
Global exception handlers.

Converts :class:`AppException` subclasses into a consistent JSON envelope
and logs the error with request context.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger("nume.exceptions")


def _error_envelope(
    *,
    code: str,
    message: str,
    status: int,
    details: list | dict | None = None,
    request_id: str | None = None,
) -> dict:
    """Build the standard error envelope."""
    body: dict = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    if request_id:
        body["error"]["request_id"] = request_id
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def _handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(_.state, "request_id", None) if _ else None
        if exc.status_code >= 500:
            logger.exception("Unhandled app exception", extra={"request_id": request_id})
        else:
            logger.warning(
                "App exception: %s (%s)",
                exc.message,
                exc.error_code,
                extra={"request_id": request_id, "status_code": exc.status_code},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_envelope(
                code=exc.error_code,
                message=exc.message,
                status=exc.status_code,
                request_id=request_id,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.info(
            "Validation error",
            extra={"request_id": request_id, "errors": exc.errors()},
        )
        return JSONResponse(
            status_code=422,
            content=_error_envelope(
                code="validation_error",
                message="Request validation failed",
                status=422,
                details=exc.errors(),
                request_id=request_id,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_envelope(
                code="http_error",
                message=str(exc.detail) if exc.detail else "HTTP error",
                status=exc.status_code,
                request_id=request_id,
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _handle_unhandled_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content=_error_envelope(
                code="internal_error",
                message="An unexpected error occurred" if request.app.state.app_debug else "Internal server error",
                status=500,
                request_id=request_id,
            ),
        )
