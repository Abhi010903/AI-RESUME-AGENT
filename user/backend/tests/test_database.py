"""Tests for database session lifecycle, cleanup, and masked logging."""

from unittest.mock import MagicMock
import pytest
from sqlalchemy.engine import make_url
from app.config import Settings
from app.database import close_db_engine, get_db, get_engine


def test_get_db_session_lifecycle() -> None:
    """Verify get_db dependency yields active session and closes it cleanly."""
    gen = get_db()
    db = next(gen)
    assert db.is_active
    with pytest.raises(StopIteration):
        next(gen)


def test_get_db_rollback_on_error() -> None:
    """Verify get_db rolls back the session if an unhandled exception occurs."""
    gen = get_db()
    db = next(gen)
    mock_rollback = MagicMock()
    db.rollback = mock_rollback

    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("Simulated endpoint crash"))

    assert mock_rollback.called


def test_masked_url_hides_password() -> None:
    """Verify engine URL string masks credentials when rendered for logging."""
    url = make_url("postgresql+psycopg2://testuser:super_secret_pw@db.example.com:5432/resumedb")
    rendered = url.render_as_string(hide_password=True)
    assert "super_secret_pw" not in rendered
    assert "***" in rendered


def test_close_db_engine_idempotent() -> None:
    """Verify close_db_engine can be called repeatedly without errors."""
    close_db_engine()
    close_db_engine()
