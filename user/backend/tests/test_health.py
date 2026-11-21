"""Tests for health and readiness probes."""

from unittest.mock import patch
from starlette import status
from starlette.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Verify that /health endpoint returns 200 with service metadata."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "AI Resume Agent - Test API"
    assert data["version"] == "0.1.0-test"
    assert data["environment"] == "testing"


def test_readiness_check_success(client: TestClient) -> None:
    """Verify that /ready endpoint returns 200 when database is healthy."""
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_readiness_check_database_failure(client: TestClient) -> None:
    """Verify that /ready endpoint returns 503 when database is unreachable."""
    with patch("app.api.health.check_db_health", return_value=(False, "Connection refused")):
        response = client.get("/ready")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
