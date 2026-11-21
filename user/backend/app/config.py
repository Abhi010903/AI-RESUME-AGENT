"""Centralized application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Resume Agent - User API"
    app_version: str = "0.1.0"
    env: Literal["development", "production", "testing"] = "development"
    debug: bool = False

    # Server configuration
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    # Logging configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = False

    # Database configuration (SQLite default, PostgreSQL compatible)
    database_url: str = "sqlite:///./resume_agent.db"

    # CORS configuration
    cors_origins: list[str] | str = ["http://localhost:3000", "http://localhost:5173"]

    # Resume Ingestion & Storage Settings
    upload_dir: str = "storage/uploads"
    generated_resumes_dir: str = "storage/generated_resumes"
    max_upload_file_size: int = 10 * 1024 * 1024  # 10 MB per file
    max_upload_files: int = 10
    min_upload_files: int = 1
    allowed_extensions: list[str] = [".pdf", ".docx"]

    # Authentication & Security (Stage 7)
    secret_key: str = "dev-secret-key-change-in-production-at-least-32-bytes-long"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> str:
        if isinstance(value, str):
            val = value.strip()
            if not val:
                raise ValueError("database_url cannot be empty")
            # Normalize legacy postgres:// prefix to modern postgresql:// required by SQLAlchemy 2.0+
            if val.startswith("postgres://"):
                return val.replace("postgres://", "postgresql://", 1)
            return val
        return str(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value]
        return ["http://localhost:3000", "http://localhost:5173"]

    @model_validator(mode="after")
    def validate_production_secret_key(self) -> "Settings":
        """Ensure production environment uses a dedicated, secure secret key."""
        if self.env == "production":
            disallowed_shipped_keys = {
                "dev-secret-key-change-in-production-at-least-32-bytes-long",
                "change-me-to-a-cryptographically-random-32-byte-secret-key",
            }
            if self.secret_key in disallowed_shipped_keys or len(self.secret_key) < 32:
                raise ValueError(
                    "In production, SECRET_KEY must be explicitly configured with a secure key containing at least 32 characters"
                )
        return self

    @property
    def is_sqlite(self) -> bool:
        """Check if the configured database is SQLite."""
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.env == "production"

    @property
    def resolved_upload_dir(self) -> Path:
        """Return absolute path to upload directory, creating it if necessary."""
        path = Path(self.upload_dir)
        if not path.is_absolute():
            # Relative to user/backend directory
            base_dir = Path(__file__).resolve().parent.parent
            path = base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_generated_resumes_dir(self) -> Path:
        """Return absolute path to generated resumes directory, creating it if necessary."""
        path = Path(self.generated_resumes_dir)
        if not path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent
            path = base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
