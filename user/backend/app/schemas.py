"""Pydantic request and response schemas for Resume Ingestion."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


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


class BatchUploadResponse(BaseModel):
    """Summary of batch upload and extraction."""

    total_submitted: int
    successful_count: int
    failed_count: int
    documents: list[DocumentResponse]
