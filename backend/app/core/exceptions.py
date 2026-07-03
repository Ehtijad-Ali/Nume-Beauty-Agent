"""
Custom exception hierarchy and HTTP error payloads.

All application errors inherit from :class:`AppException`. The exception
handler middleware converts them into a consistent JSON envelope.
"""

from __future__ import annotations


class AppException(Exception):
    """Base application exception."""

    status_code: int = 400
    error_code: str = "app_error"

    def __init__(self, message: str, *, error_code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict"


class UnauthorizedError(AppException):
    status_code = 401
    error_code = "unauthorized"


class ForbiddenError(AppException):
    status_code = 403
    error_code = "forbidden"


class ValidationError(AppException):
    status_code = 422
    error_code = "validation_error"


class BadRequestError(AppException):
    status_code = 400
    error_code = "bad_request"


class RateLimitError(AppException):
    status_code = 429
    error_code = "rate_limited"
