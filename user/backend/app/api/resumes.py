"""API endpoints for resume ingestion, extraction, and management."""

import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.config import Settings, get_settings
from app.database import get_db
from app.errors import AppException, NotFoundError
from app.models import Document, User
from app.schemas import (
    BatchUploadResponse,
    DocumentListItemResponse,
    DocumentResponse,
    DocumentTextResponse,
)
from app.services.activity_logger import record_activity
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
def upload_resumes(
    files: list[UploadFile] = File(..., description="1 to 10 resume files (PDF or DOCX)"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User | None = Depends(get_current_user_optional),
) -> BatchUploadResponse:
    """Ingest and extract up to 10 candidate resumes.

    Runs as a standard synchronous endpoint so blocking I/O (disk writes, DB commits,
    and CPU-bound document parsing) runs on FastAPI's threadpool rather than blocking the event loop.
    """
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

        # Bounded read to prevent memory exhaustion from oversized malicious payloads
        content = upload.file.read(settings.max_upload_file_size + 1)
        file_size = len(content)

        # 1. Size check with bounded memory consumption
        if file_size > settings.max_upload_file_size:
            failed_doc = Document(
                id=str(uuid.uuid4()),
                filename=safe_name,
                file_format=safe_name.split(".")[-1].lower() if "." in safe_name else "unknown",
                file_size=file_size,
                file_hash="",
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
            user_id=current_user.id if current_user else None,
        )
        doc_record.set_warnings(combined_warnings)

        db.add(doc_record)
        try:
            db.commit()
            db.refresh(doc_record)
        except Exception:
            db.rollback()
            if storage_path:
                delete_upload_file(storage_path, settings.resolved_upload_dir)
            raise

        if extraction.status == "completed":
            successful_count += 1
            record_activity(
                db=db,
                user_id=current_user.id if current_user else None,
                action="resume_uploaded",
                title=f"Uploaded and parsed {doc_record.filename}",
                description=f"Extracted {len(doc_record.extracted_text or '')} characters with {len(doc_record.warnings_list)} warnings",
                entity_type="document",
                entity_id=doc_record.id,
            )
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
    current_user: User | None = Depends(get_current_user_optional),
) -> list[DocumentListItemResponse]:
    """List all ingested resume documents."""
    query = select(Document)
    if current_user:
        query = query.where(Document.user_id == current_user.id)
    docs = db.scalars(query.order_by(Document.created_at.desc()).offset(skip).limit(limit)).all()
    return [DocumentListItemResponse.model_validate(doc) for doc in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get Resume Metadata and Extraction Details",
    description="Fetches processing status, extraction warnings, and full extracted text for a specific document.",
)
def get_resume(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DocumentResponse:
    """Retrieve document metadata and extraction results."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc or (doc.user_id is not None and (current_user is None or doc.user_id != current_user.id)):
        raise NotFoundError(f"Document '{document_id}' not found")
    return _model_to_response(doc)


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextResponse,
    summary="Get Extracted Text",
    description="Returns the clean extracted plain text and warnings for a document.",
)
def get_resume_text(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DocumentTextResponse:
    """Retrieve only the extracted text for downstream profile processing."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc or (doc.user_id is not None and (current_user is None or doc.user_id != current_user.id)):
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


@router.get(
    "/{document_id}/download",
    summary="Download Original Uploaded Resume File",
)
def download_resume_file(
    document_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User | None = Depends(get_current_user_optional),
) -> FileResponse:
    """Download the raw stored resume document."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc or (doc.user_id is not None and (current_user is None or doc.user_id != current_user.id)):
        raise NotFoundError(f"Document '{document_id}' not found")

    file_path = settings.resolved_upload_dir / doc.storage_path
    if not file_path.exists():
        raise NotFoundError(f"Raw file for document '{document_id}' not found on disk")

    media_type = (
        "application/pdf"
        if doc.file_format == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=doc.filename,
    )


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentResponse,
    summary="Reprocess and Re-extract Document",
)
def reprocess_resume(
    document_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User | None = Depends(get_current_user_optional),
) -> DocumentResponse:
    """Re-run extraction pipeline on an existing uploaded resume."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc or (doc.user_id is not None and (current_user is None or doc.user_id != current_user.id)):
        raise NotFoundError(f"Document '{document_id}' not found")

    file_path = settings.resolved_upload_dir / doc.storage_path
    if not file_path.exists():
        raise NotFoundError(f"Raw file for document '{document_id}' not found on disk")

    content = file_path.read_bytes()
    extraction = extract_document_text(content, doc.file_format)

    doc.status = extraction.status
    doc.extracted_text = extraction.text
    doc.page_count = extraction.page_count
    doc.error_message = extraction.error_message
    doc.set_warnings(extraction.warnings)

    db.commit()
    db.refresh(doc)
    record_activity(
        db=db,
        user_id=current_user.id if current_user else None,
        action="resume_processed",
        title=f"Reprocessed extraction for {doc.filename}",
        description=f"Status: {doc.status}, extracted {len(doc.extracted_text or '')} chars",
        entity_type="document",
        entity_id=doc.id,
    )
    logger.info("Reprocessed document %s with status %s", doc.id, doc.status)
    return _model_to_response(doc)


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
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, str]:
    """Delete document and stored file."""
    doc = db.scalars(select(Document).where(Document.id == document_id)).first()
    if not doc or (doc.user_id is not None and (current_user is None or doc.user_id != current_user.id)):
        raise NotFoundError(f"Document '{document_id}' not found")

    deleted_filename = doc.filename
    storage_path = doc.storage_path
    if storage_path:
        deleted = delete_upload_file(storage_path, settings.resolved_upload_dir)
        raw_file = (settings.resolved_upload_dir / storage_path).resolve()
        if not deleted and raw_file.exists():
            raise AppException(
                message="Failed to delete stored file from disk; deletion aborted for retryability.",
                code="STORAGE_DELETE_FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    db.delete(doc)
    db.commit()
    record_activity(
        db=db,
        user_id=current_user.id if current_user else None,
        action="resume_deleted",
        title=f"Deleted resume {deleted_filename}",
        entity_type="document",
        entity_id=document_id,
    )

    logger.info("Deleted document %s", document_id)
    return {"status": "deleted", "document_id": document_id}
