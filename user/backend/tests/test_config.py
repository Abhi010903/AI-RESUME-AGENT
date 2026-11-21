"""Tests for application settings and configuration parsing."""

from pydantic import ValidationError
import pytest
from app.config import Settings


def test_settings_defaults() -> None:
    """Verify default configuration values."""
    settings = Settings()
    assert settings.app_name == "AI Resume Agent - User API"
    assert settings.is_sqlite is True
    assert settings.is_production is False
    assert "http://localhost:3000" in settings.cors_origins


def test_cors_origins_parsing() -> None:
    """Verify string-to-list parsing for CORS origins."""
    settings = Settings(cors_origins="https://app.example.com, https://portal.example.com")
    assert settings.cors_origins == ["https://app.example.com", "https://portal.example.com"]

    json_settings = Settings(cors_origins='["https://user.example.com"]')
    assert json_settings.cors_origins == ["https://user.example.com"]


def test_database_url_postgresql() -> None:
    """Verify is_sqlite flag with non-SQLite database URLs."""
    pg_settings = Settings(database_url="postgresql+psycopg2://user:pass@localhost:5432/resume_db")
    assert pg_settings.is_sqlite is False


def test_legacy_postgres_url_normalized() -> None:
    """Verify postgres:// is safely normalized to postgresql:// for SQLAlchemy 2.0+."""
    settings = Settings(database_url="postgres://user:secret@db.host.com:5432/resumedb")
    assert settings.database_url == "postgresql://user:secret@db.host.com:5432/resumedb"


def test_invalid_port_validation() -> None:
    """Verify port boundaries (1 to 65535)."""
    with pytest.raises(ValidationError):
        Settings(port=0)

    with pytest.raises(ValidationError):
        Settings(port=70000)

    valid = Settings(port=8080)
    assert valid.port == 8080


def test_empty_database_url_validation() -> None:
    """Verify empty database_url is rejected."""
    with pytest.raises(ValidationError):
        Settings(database_url="   ")
