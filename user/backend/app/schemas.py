"""Pydantic request and response schemas for Resume Ingestion."""

from datetime import datetime
import json
from pydantic import BaseModel, ConfigDict, field_validator


class DocumentBase(BaseModel):
    """Base document attributes."""

    id: str
    filename: str
    file_format: str
    file_size: int
    file_hash: str
    status: str
    page_count: int | None = None
    warnings: list[str] = []
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("warnings", mode="before")
    @classmethod
    def parse_warnings_field(cls, value: object) -> list[str]:
        """Safely parse warnings whether passed as list or JSON-encoded ORM column string."""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class DocumentListItemResponse(BaseModel):
    """Concise document metadata for list endpoints."""

    id: str
    filename: str
    file_format: str
    file_size: int
    status: str
    page_count: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentBase):
    """Detailed document response including full extraction outcome."""

    extracted_text: str | None = None


class DocumentTextResponse(BaseModel):
    """Focused response for extracted text and warnings."""

    id: str
    filename: str
    file_format: str
    status: str
    extracted_text: str
    page_count: int | None = None
    warnings: list[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("warnings", mode="before")
    @classmethod
    def parse_warnings_field(cls, value: object) -> list[str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class BatchUploadResponse(BaseModel):
    """Summary of batch upload and extraction."""

    total_submitted: int
    successful_count: int
    failed_count: int
    documents: list[DocumentResponse]
