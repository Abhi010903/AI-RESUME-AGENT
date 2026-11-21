"""Consistent API error handling and custom exception classes."""

from collections.abc import Mapping
import logging
from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")


class AppException(Exception):
    """Base application exception with structured error representation."""

    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message=message, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND, details=details)


class ConflictError(AppException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Resource conflict", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message=message, code="CONFLICT", status_code=status.HTTP_409_CONFLICT, details=details)


class DatabaseUnavailableError(AppException):
    """Database connectivity failure."""

    def __init__(self, message: str = "Database service unavailable") -> None:
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Helper to build consistent error envelope response."""
    return JSONResponse(
        status_code=status_code,
        headers=dict(headers) if headers else None,
        content={
            "status": "error",
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            },
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle domain-specific AppException instances."""
    logger.warning("Application exception [%s]: %s (path: %s)", exc.code, exc.message, request.url.path)
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI / Pydantic request validation errors."""
    details = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "issue": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]
    logger.info("Validation error on %s: %d issues", request.url.path, len(details))
    return create_error_response(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette / FastAPI standard HTTP exceptions, preserving headers."""
    code_map = {
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        403: "FORBIDDEN",
        401: "UNAUTHORIZED",
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    return create_error_response(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
        headers=getattr(exc, "headers", None),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to prevent unhandled 500 exceptions from leaking internals."""
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred",
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )
