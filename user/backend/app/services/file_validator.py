"""File validation, signature verification, and sanitization service."""

import hashlib
import io
from pathlib import Path
import re
import zipfile
from app.errors import AppException


class FileValidationError(AppException):
    """File upload validation error."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="FILE_VALIDATION_ERROR", status_code=400)


def sanitize_filename(raw_filename: str | None) -> str:
    """Sanitize uploaded filename to prevent path traversal and shell injection."""
    if not raw_filename or not raw_filename.strip():
        return "unnamed_document"

    # Strip directory components (both Unix and Windows slashes) and null bytes
    cleaned = raw_filename.replace("\x00", "").strip()
    name = Path(cleaned).name

    # Replace special characters with underscores, allowing only alphanumerics, dots, hyphens, and underscores
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    safe_name = re.sub(r"_+", "_", safe_name).strip("._")

    if not safe_name:
        return "unnamed_document"

    # Enforce reasonable maximum filename length while preserving extension
    ext = Path(safe_name).suffix.lower()
    stem = Path(safe_name).stem
    if len(stem) > 80:
        stem = stem[:80]
    return f"{stem}{ext}" if ext else stem


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for integrity and deduplication."""
    return hashlib.sha256(content).hexdigest()


def validate_file_signature(content: bytes, filename: str) -> tuple[str, list[str]]:
    """Validate file size, extension, and binary magic bytes.

    Returns tuple of (detected_format, warnings).
    Raises FileValidationError if the file is invalid, empty, or spoofed.
    """
    if not content:
        raise FileValidationError(f"File '{filename}' is empty (0 bytes)")

    ext = Path(filename).suffix.lower()
    if ext not in (".pdf", ".docx"):
        raise FileValidationError(f"Unsupported file format '{ext}'. Only .pdf and .docx are supported")

    # Verify PDF signature
    if ext == ".pdf":
        # PDF spec: %PDF- appears in the first 1024 bytes
        header = content[:1024]
        if b"%PDF-" not in header:
            raise FileValidationError(f"File '{filename}' is not a valid PDF document (invalid signature)")
        return "pdf", []

    # Verify DOCX signature (OpenXML ZIP archive)
    if ext == ".docx":
        if len(content) < 4 or content[:4] != b"PK\x03\x04":
            raise FileValidationError(f"File '{filename}' is not a valid DOCX document (missing ZIP header)")

        # Validate that the archive contains Microsoft Word document parts
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                namelist = zf.namelist()
                has_content_types = "[Content_Types].xml" in namelist
                has_word_doc = any(name.startswith("word/") for name in namelist)

                if not (has_content_types and has_word_doc):
                    raise FileValidationError(
                        f"File '{filename}' is a ZIP archive but does not contain a valid Word document structure"
                    )

                # Defense against decompression bomb / excessive memory allocation
                total_uncompressed_size = sum(info.file_size for info in zf.infolist())
                max_uncompressed_limit = 50 * 1024 * 1024  # 50 MB safety cap
                if total_uncompressed_size > max_uncompressed_limit:
                    raise FileValidationError(
                        f"File '{filename}' exceeds safe decompressed size limit ({total_uncompressed_size // (1024 * 1024)}MB)"
                    )
        except zipfile.BadZipFile:
            raise FileValidationError(f"File '{filename}' is corrupted or not a valid DOCX file")

        return "docx", []

    raise FileValidationError(f"Unsupported file format: {ext}")
