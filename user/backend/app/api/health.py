"""Health and readiness check endpoints for monitoring and orchestration."""

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from app.config import Settings, get_settings
from app.database import check_db_health

router = APIRouter(tags=["Monitoring"])


class HealthResponse(BaseModel):
    """Liveness probe response payload."""

    status: str
    app: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    """Readiness probe response payload."""

    status: str
    database: str
    details: str | None = None


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness Probe",
    description="Returns HTTP 200 if the service process is up and running.",
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Check service liveness."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={
        status.HTTP_200_OK: {"description": "Service is ready to handle traffic"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database or dependency unavailable"},
    },
    summary="Readiness Probe",
    description="Verifies database connectivity and operational dependencies.",
)
async def readiness_check(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadyResponse:
    """Verify backend and database readiness."""
    db_ok, error_message = check_db_health()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(
            status="unhealthy",
            database="disconnected",
            details=error_message if settings.debug else "Database connection check failed",
        )

    return ReadyResponse(
        status="ready",
        database="connected",
        details=None,
    )
