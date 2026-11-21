"""API endpoints for resume ingestion, extraction, and management."""

import logging
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import Settings, get_settings
from app.database import get_db
from app.errors import AppException, NotFoundError
from app.models import Document
from app.schemas import (
    BatchUploadResponse,
    DocumentListItemResponse,
    DocumentResponse,
    DocumentTextResponse,
)
from app.services.extractor import extract_document_text
from app.services.file_validator import (
    FileValidationError,
    compute_file_hash,
    sanitize_filename,
    validate_file_signature,
)
from app.services.storage import delete_upload_file, save_upload_file

logger = logging.getLogger("app.api.resumes")

router = APIRouter(prefix="/api/v1/resumes", tags=["Resume Ingestion"])


def _model_to_response(doc: Document) -> DocumentResponse:
    """Map SQLAlchemy Document to Pydantic DocumentResponse."""
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_format=doc.file_format,
        file_size=doc.file_size,
        file_hash=doc.file_hash,
        status=doc.status,
        page_count=doc.page_count,
        extracted_text=doc.extracted_text,
        warnings=doc.warnings_list,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post(
    "/upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest Resumes",
    description="Accepts 1 to 10 resume documents (PDF or DOCX), validates signatures, and extracts structured text.",
)
async def upload_resumes(
    files: list[UploadFile] = File(..., description="1 to 10 resume files (PDF or DOCX)"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BatchUploadResponse:
    """Ingest and extract up to 10 candidate resumes."""
    if not files or len(files) < settings.min_upload_files or len(files) > settings.max_upload_files:
        raise AppException(
            message=f"Upload batch must contain between {settings.min_upload_files} and {settings.max_upload_files} files",
            code="INVALID_BATCH_SIZE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    processed_documents: list[DocumentResponse] = []
    successful_count = 0
    failed_count = 0

    for upload in files:
        raw_name = upload.filename or "unnamed_document"
        safe_name = sanitize_filename(raw_name)
        content = await upload.read()
        file_size = len(content)

        # 1. Size check
        if file_size > settings.max_upload_file_size:
            failed_doc = Document(
                id=str(uuid.uuid4()),
                filename=safe_name,
                file_format=safe_name.split(".")[-1].lower() if "." in safe_name else "unknown",
                file_size=file_size,
                file_hash=compute_file_hash(content) if content else "",
                storage_path="",
                status="failed",
                error_message=f"File exceeds maximum allowed size ({settings.max_upload_file_size // (1024 * 1024)}MB)",
            )
            failed_doc.set_warnings(["File size limit exceeded"])
            db.add(failed_doc)
            db.commit()
            db.refresh(failed_doc)
            processed_documents.append(_model_to_response(failed_doc))
            failed_count += 1
            continue

        # 2. Signature and structure validation
        try:
            file_format, validation_warnings = validate_file_signature(content, safe_name)
        except FileValidationError as err:
            failed_doc = Document(
                id=str(uuid.uuid4()),
                filename=safe_name,
                file_format=safe_name.split(".")[-1].lower() if "." in safe_name else "unknown",
                file_size=file_size,
                file_hash=compute_file_hash(content) if content else "",
                storage_path="",
                status="failed",
                error_message=err.message,
            )
            failed_doc.set_warnings([err.message])
            db.add(failed_doc)
            db.commit()
            db.refresh(failed_doc)
            processed_documents.append(_model_to_response(failed_doc))
            failed_count += 1
            continue

        file_hash = compute_file_hash(content)

        # 3. Duplicate detection
        existing_doc = db.scalars(
            select(Document).where(Document.file_hash == file_hash, Document.status == "completed")
        ).first()

        if existing_doc:
            logger.info("Duplicate document detected; reusing existing record: %s", existing_doc.id)
            warnings = existing_doc.warnings_list
            if "Duplicate file detected; existing processed document record reused" not in warnings:
                warnings.append("Duplicate file detected; existing processed document record reused")
                existing_doc.set_warnings(warnings)
                db.commit()
                db.refresh(existing_doc)
            processed_documents.append(_model_to_response(existing_doc))
            successful_count += 1
            continue

        # 4. Storage
        doc_id = str(uuid.uuid4())
        try:
            storage_path = save_upload_file(content, doc_id, file_format, settings.resolved_upload_dir)
        except Exception as exc:
            logger.error("Failed to store file %s: %s", safe_name, exc)
            failed_doc = Document(
                id=doc_id,
                filename=safe_name,
                file_format=file_format,
                file_size=file_size,
                file_hash=file_hash,
                storage_path="",
                status="failed",
                error_message="Storage write failure",
            )
            db.add(failed_doc)
            db.commit()
            db.refresh(failed_doc)
            processed_documents.append(_model_to_response(failed_doc))
            failed_count += 1
            continue

        # 5. Text extraction
        extraction = extract_document_text(content, file_format)
        combined_warnings = list(validation_warnings) + extraction.warnings

        # 6. Database persistence
        doc_record = Document(
            id=doc_id,
            filename=safe_name,
            file_format=file_format,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
            status=extraction.status,
            page_count=extraction.page_count,
            extracted_text=extraction.text,
            error_message=extraction.error_message,
        )
        doc_record.set_warnings(combined_warnings)

        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        if extraction.status == "completed":
            successful_count += 1
        else:
            failed_count += 1

        processed_documents.append(_model_to_response(doc_record))

    return BatchUploadResponse(
        total_submitted=len(files),
        successful_count=successful_count,
        failed_count=failed_count,
        documents=processed_documents,
    )


@router.get(
    "",
    response_model=list[DocumentListItemResponse],
    summary="List Uploaded Resumes",
    description="Returns a paginated list of uploaded resume documents and processing statuses.",
)
def list_resumes(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    db: Session = Depends(get_db),
) -> list[DocumentListItemResponse]:
    """List all ingested resume documents."""
    docs = db.scalars(select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)).all()
    return [DocumentListItemResponse.model_validate(doc) for doc in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get Resume Metadata and Extraction Details",
    description="Fetches processing status, extraction warnings, and full extracted text for a specific document.",
)
def get_resume(document_id: str, db: Session = Depends(get_db)) -> DocumentResponse:
    """Retrieve document metadata and extraction results."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc:
        raise NotFoundError(f"Document '{document_id}' not found")
    return _model_to_response(doc)


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextResponse,
    summary="Get Extracted Text",
    description="Returns the clean extracted plain text and warnings for a document.",
)
def get_resume_text(document_id: str, db: Session = Depends(get_db)) -> DocumentTextResponse:
    """Retrieve only the extracted text for downstream profile processing."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc:
        raise NotFoundError(f"Document '{document_id}' not found")
    if doc.status == "failed":
        raise AppException(
            message=f"Extraction failed for document '{document_id}': {doc.error_message or 'Unknown error'}",
            code="EXTRACTION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return DocumentTextResponse(
        id=doc.id,
        filename=doc.filename,
        file_format=doc.file_format,
        status=doc.status,
        extracted_text=doc.extracted_text or "",
        page_count=doc.page_count,
        warnings=doc.warnings_list,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Ingested Resume",
    description="Deletes a document from the database and permanently removes its stored raw file.",
)
def delete_resume(
    document_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Delete document and stored file."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc:
        raise NotFoundError(f"Document '{document_id}' not found")

    if doc.storage_path:
        delete_upload_file(doc.storage_path, settings.resolved_upload_dir)

    db.delete(doc)
    db.commit()
    logger.info("Deleted document %s", document_id)
    return {"status": "deleted", "document_id": document_id}
