"""SQLAlchemy database models for AI Resume Agent."""

from datetime import datetime, timezone
import json
from typing import Any
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Document(Base):
    """Uploaded candidate resume document and extraction metadata."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Document ownership boundary (ready for Phase 7 authentication / multi-tenancy)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def warnings_list(self) -> list[str]:
        """Deserialize stored JSON warnings."""
        if not self.warnings:
            return []
        try:
            parsed = json.loads(self.warnings)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            return [self.warnings]

    def set_warnings(self, warnings: list[str]) -> None:
        """Serialize warnings list to JSON string."""
        self.warnings = json.dumps(warnings) if warnings else None
