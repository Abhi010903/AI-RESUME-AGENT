"""Unit and API tests for Stage 7 — Authentication, Password Security & JWT.

Covers:
- Registration (POST /api/v1/auth/register)
- Duplicate email prevention (409 Conflict)
- Password length and email format validation (422)
- PBKDF2-HMAC-SHA256 password hashing (600,000 iterations, random salt)
- Constant-time password verification
- Login (POST /api/v1/auth/login)
- Invalid credentials rejection (401 Unauthorized)
- HS256 JWT creation, decoding, and tamper detection
- Expired token rejection
- Authenticated user endpoint (GET /api/v1/auth/me)
"""

from datetime import timedelta
import time
from fastapi import status
from fastapi.testclient import TestClient
from app.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    """Test PBKDF2-HMAC-SHA256 hashing and constant-time verification."""
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2:sha256:600000$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "invalid$format") is False


def test_jwt_creation_verification_and_tampering() -> None:
    """Test HS256 JWT token creation, signature validation, and tamper detection."""
    user_id = "test-user-uuid"
    email = "candidate@example.com"
    token = create_access_token(user_id=user_id, email=email)

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["exp"] > time.time()

    # Tampered token (change payload)
    parts = token.split(".")
    tampered_payload = parts[1][:-2] + "AA"
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
    try:
        decode_access_token(tampered_token)
        assert False, "Should have raised ValueError on signature mismatch"
    except ValueError as exc:
        assert "signature" in str(exc).lower()

    # Expired token
    expired_token = create_access_token(user_id=user_id, email=email, expires_delta=timedelta(seconds=-10))
    try:
        decode_access_token(expired_token)
        assert False, "Should have raised ValueError on expired token"
    except ValueError as exc:
        assert "expired" in str(exc).lower()


def test_candidate_registration_and_login_flow(client: TestClient) -> None:
    """Test end-to-end registration, login, and current user retrieval."""
    reg_payload = {
        "email": "sarah.connor@cyberdyne.org",
        "password": "ResistancePassword2026!",
        "full_name": "Sarah Connor",
    }

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_201_CREATED
    reg_data = reg_res.json()
    assert reg_data["access_token"] is not None
    assert reg_data["token_type"] == "bearer"
    assert reg_data["user"]["email"] == "sarah.connor@cyberdyne.org"
    assert reg_data["user"]["full_name"] == "Sarah Connor"

    # 2. Duplicate registration rejected
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == status.HTTP_409_CONFLICT

    # 3. Login with correct credentials
    login_res = client.post("/api/v1/auth/login", json={
        "email": "sarah.connor@cyberdyne.org",
        "password": "ResistancePassword2026!",
    })
    assert login_res.status_code == status.HTTP_200_OK
    token = login_res.json()["access_token"]

    # 4. Login with wrong password
    bad_login = client.post("/api/v1/auth/login", json={
        "email": "sarah.connor@cyberdyne.org",
        "password": "WrongPassword!",
    })
    assert bad_login.status_code == status.HTTP_401_UNAUTHORIZED

    # 5. Access /api/v1/auth/me with Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["email"] == "sarah.connor@cyberdyne.org"

    # 6. Access /api/v1/auth/me without token
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED


def test_registration_validation_rules(client: TestClient) -> None:
    """Test password length and invalid email validation."""
    # Short password
    r1 = client.post("/api/v1/auth/register", json={
        "email": "valid@example.com",
        "password": "short",
        "full_name": "Valid Name",
    })
    assert r1.status_code == 422

    # Invalid email
    r2 = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "full_name": "Valid Name",
    })
    assert r2.status_code == 422
