"""Tests for consistent API error formatting and exception handlers."""

from fastapi import APIRouter
from pydantic import BaseModel
import pytest
from starlette import status
from starlette.testclient import TestClient
from app.errors import AppException, ConflictError, NotFoundError

dummy_router = APIRouter()


class SampleModel(BaseModel):
    name: str
    age: int


@dummy_router.get("/test/not-found")
def raise_not_found():
    raise NotFoundError("Candidate profile not found")


@dummy_router.get("/test/conflict")
def raise_conflict():
    raise ConflictError("Email already registered")


@dummy_router.post("/test/validate")
def validate_body(payload: SampleModel):
    return {"message": "ok"}


@dummy_router.get("/test/unhandled")
def raise_unhandled():
    raise RuntimeError("Unexpected failure")


def test_404_route_not_found(client: TestClient) -> None:
    """Non-existent route should return structured 404 response."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "NOT_FOUND"


def test_custom_app_exceptions(client: TestClient) -> None:
    """AppException should map to configured HTTP status and structured error."""
    client.app.include_router(dummy_router)

    res_nf = client.get("/test/not-found")
    assert res_nf.status_code == status.HTTP_404_NOT_FOUND
    nf_data = res_nf.json()
    assert nf_data["status"] == "error"
    assert nf_data["error"]["code"] == "NOT_FOUND"
    assert "Candidate profile not found" in nf_data["error"]["message"]

    res_conflict = client.get("/test/conflict")
    assert res_conflict.status_code == status.HTTP_409_CONFLICT
    conflict_data = res_conflict.json()
    assert conflict_data["status"] == "error"
    assert conflict_data["error"]["code"] == "CONFLICT"


def test_validation_error_envelope(client: TestClient) -> None:
    """Request validation errors should return 422 with structured field details."""
    client.app.include_router(dummy_router)

    response = client.post("/test/validate", json={"name": "Alice", "age": "not-an-integer"})
    assert response.status_code == getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0


def test_unhandled_exception_envelope(client: TestClient) -> None:
    """Unhandled internal errors should return 500 without leaking stack traces."""
    client.app.include_router(dummy_router)

    response = client.get("/test/unhandled")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "Unexpected failure" not in data["error"]["message"]
