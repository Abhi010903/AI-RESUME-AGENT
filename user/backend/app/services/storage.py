"""Secure file storage operations."""

import logging
from pathlib import Path

logger = logging.getLogger("app.storage")


def save_upload_file(content: bytes, document_id: str, file_format: str, upload_dir: Path) -> str:
    """Save raw file bytes to disk using server-generated identifier.

    Returns the relative storage filename.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = file_format.lower().lstrip(".")
    storage_filename = f"{document_id}.{ext}"
    dest_path = (upload_dir / storage_filename).resolve()

    # Path traversal safety check
    if not dest_path.is_relative_to(upload_dir.resolve()):
        raise ValueError("Invalid storage destination path")

    dest_path.write_bytes(content)
    logger.info("Saved uploaded file", extra={"document_id": document_id, "size": len(content)})
    return storage_filename


def delete_upload_file(storage_filename: str, upload_dir: Path) -> bool:
    """Delete stored file from disk if it exists."""
    target_path = (upload_dir / storage_filename).resolve()

    # Safety check: prevent deleting files outside upload_dir
    if not target_path.is_relative_to(upload_dir.resolve()):
        logger.warning("Attempted path traversal deletion: %s", storage_filename)
        return False

    if target_path.exists() and target_path.is_file():
        try:
            target_path.unlink()
            logger.info("Deleted file from storage: %s", storage_filename)
            return True
        except Exception as exc:
            logger.error("Failed to delete file %s: %s", storage_filename, exc)
            return False
    return False
