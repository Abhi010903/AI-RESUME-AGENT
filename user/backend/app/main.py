"""FastAPI application entrypoint with security middleware and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import re
import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.api.applications import router as applications_router
from app.api.ats import router as ats_router
from app.api.auth import router as auth_router
from app.api.generation import router as generation_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.matches import router as matches_router
from app.api.profiles import router as profiles_router
from app.api.resumes import router as resumes_router
from app.api.workflow import router as workflow_router
from app.config import Settings, get_settings
from app.database import close_db_engine, get_engine, init_db
from app.errors import (
    AppException,
    app_exception_handler,
    starlette_http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.logging import request_id_ctx, setup_logging

# Pattern for safe Request-IDs (alphanumeric, hyphens, underscores; max 64 chars)
SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds essential HTTP security headers to all outgoing responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Allow Swagger UI and ReDoc to load assets on docs paths in non-production; strict none elsewhere
        if request.url.path in ("/docs", "/redoc", "/openapi.json"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "frame-ancestors 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches a validated Request-ID to incoming requests and records execution duration.

    Guards against log injection and HTTP response splitting by validating incoming X-Request-ID.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw_request_id = request.headers.get("X-Request-ID")
        # Validate format: discard untrusted, malformed, or injected values
        if raw_request_id and SAFE_REQUEST_ID_REGEX.match(raw_request_id):
            request_id = raw_request_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        process_time = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and graceful shutdown."""
    settings = getattr(app.state, "settings", None) or get_settings()
    setup_logging(settings)
    engine = get_engine(settings)
    init_db(engine)
    try:
        yield
    finally:
        close_db_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    cfg = settings or get_settings()

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        docs_url="/docs" if not cfg.is_production else None,
        redoc_url="/redoc" if not cfg.is_production else None,
        lifespan=lifespan,
    )
    app.state.settings = cfg

    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: settings

    # Middleware registration (executed in reverse order of addition)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Custom exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register routers (specific static paths before parameterized wildcards)
    app.include_router(health_router)
    app.include_router(workflow_router)
    app.include_router(auth_router)
    app.include_router(applications_router)
    app.include_router(generation_router)
    app.include_router(resumes_router)
    app.include_router(profiles_router)
    app.include_router(jobs_router)
    app.include_router(matches_router)
    app.include_router(ats_router)

    return app


app = create_app()
