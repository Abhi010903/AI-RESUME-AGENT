"""Tests for security headers and request-id tracing."""

from starlette import status
from starlette.testclient import TestClient


def test_security_headers_present(client: TestClient) -> None:
    """Verify essential security headers are applied to HTTP responses."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'none'" in headers.get("Content-Security-Policy", "")


def test_request_id_generation_and_propagation(client: TestClient) -> None:
    """Ensure X-Request-ID is generated and preserved if provided."""
    # Generated if omitted
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers

    # Preserved if client supplies a valid, safe ID
    custom_id = "test-request-id-12345"
    response_custom = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response_custom.headers.get("X-Request-ID") == custom_id


def test_malformed_request_id_rejected_and_replaced(client: TestClient) -> None:
    """Ensure malformed or log-injection Request-IDs (with CRLF, spaces, or symbols) are discarded."""
    injected_id = "evil-id\r\nInjected-Header: malicious"
    response = client.get("/health", headers={"X-Request-ID": injected_id})
    assigned_id = response.headers.get("X-Request-ID")
    assert assigned_id is not None
    assert "\r" not in assigned_id
    assert "\n" not in assigned_id
    assert "evil-id" not in assigned_id


def test_csp_allows_docs_assets_in_dev(client: TestClient) -> None:
    """Verify that /docs route allows Swagger UI assets while retaining clickjacking protection."""
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
    csp = response.headers.get("Content-Security-Policy", "")
    assert "cdn.jsdelivr.net" in csp
    assert "frame-ancestors 'none'" in csp


def test_security_headers_present_on_error(client: TestClient) -> None:
    """Verify that error responses also receive essential security headers."""
    response = client.get("/non-existent-path")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Request-ID") is not None
