"""Authentication, password security, and JWT services (Stage 7).

Implements:
- PBKDF2-HMAC-SHA256 password hashing with 600,000 iterations and cryptographic salts
- Constant-time password verification (resilient against timing attacks)
- Pure standard-library HS256 JWT creation, decoding, and signature validation
- User lookup and authentication against database
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import Settings, get_settings
from app.models import User

logger = logging.getLogger("app.services.auth")

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256, random salt, and 600,000 iterations."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        iterations=PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        meta, salt, expected_hash = parts
        _, _, iters_str = meta.split(":")
        iterations = int(iters_str)

        computed = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=plain_password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            iterations=iterations,
        )
        return hmac.compare_digest(computed.hex(), expected_hash)
    except Exception as exc:
        logger.warning("Password verification failed with exception: %s", exc)
        return False


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding '='."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    """Decode URL-safe base64 string with restored '=' padding."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: timedelta | None = None,
    settings: Settings | None = None,
) -> str:
    """Generate cryptographically signed HS256 JWT access token."""
    cfg = settings or get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=cfg.access_token_expire_minutes)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        key=cfg.secret_key.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Validate HS256 signature and expiration, returning token claims."""
    cfg = settings or get_settings()
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    expected_sig = hmac.new(
        key=cfg.secret_key.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()

    try:
        provided_sig = _b64url_decode(sig_b64)
    except Exception as exc:
        raise ValueError("Invalid token signature encoding") from exc

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("JWT signature verification failed")

    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid token payload encoding") from exc

    exp = payload.get("exp")
    if exp is None:
        raise ValueError("Token missing expiration claim")
    if time.time() > exp:
        raise ValueError("Token has expired")

    return payload


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch user by normalized email address."""
    clean_email = email.strip().lower()
    return db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Fetch user by ID."""
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def create_user(db: Session, email: str, password: str, full_name: str) -> User:
    """Create new candidate user account with hashed password."""
    clean_email = email.strip().lower()
    hashed = hash_password(password)
    user = User(
        id=str(uuid.uuid4()),
        email=clean_email,
        hashed_password=hashed,
        full_name=full_name.strip(),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user with email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def update_user_password(db: Session, user: User, new_password: str) -> None:
    """Update candidate password with new secure PBKDF2 hash."""
    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)


def create_password_reset_token(user_id: str, email: str, settings: Settings | None = None) -> str:
    """Generate time-limited signed password reset token (15-minute validity)."""
    cfg = settings or get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=15)

    header = {"alg": "HS256", "typ": "PWD_RESET"}
    payload = {
        "sub": user_id,
        "email": email,
        "purpose": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        key=cfg.secret_key.encode("utf-8"),
        msg=signing_input,
        digestmod=hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_password_reset_token(token: str, settings: Settings | None = None) -> str:
    """Verify reset token and extract user_id."""
    payload = decode_access_token(token, settings=settings)
    if payload.get("purpose") != "password_reset":
        raise ValueError("Invalid token purpose")
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token missing user identifier")
    return user_id


_RATE_LIMIT_STORE: dict[str, list[float]] = {}


def check_rate_limit(key: str, max_attempts: int = 5, window_seconds: int = 60) -> bool:
    """Simple in-memory sliding window rate limiter."""
    now = time.time()
    attempts = _RATE_LIMIT_STORE.get(key, [])
    valid_attempts = [t for t in attempts if now - t < window_seconds]
    if len(valid_attempts) >= max_attempts:
        _RATE_LIMIT_STORE[key] = valid_attempts
        return False
    valid_attempts.append(now)
    _RATE_LIMIT_STORE[key] = valid_attempts
    return True
