"""Document text extraction engine supporting PDF (PyMuPDF) and DOCX (python-docx)."""

from dataclasses import dataclass, field
import io
import logging
import re
import docx
import pymupdf

logger = logging.getLogger("app.extractor")


@dataclass
class ExtractionResult:
    """Structured text extraction outcome."""

    text: str = ""
    page_count: int | None = None
    status: str = "completed"
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None


def normalize_extracted_text(text: str) -> str:
    """Clean and normalize extracted text, removing null bytes and excessive whitespace."""
    if not text:
        return ""
    # Remove null bytes and control chars (except standard newlines/tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize excessive empty lines (more than 2 consecutive newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_pdf_text(content: bytes) -> ExtractionResult:
    """Extract text and metadata from PDF bytes using PyMuPDF.

    Detects encryption, scanned/image-only pages, and preserves page boundaries.
    """
    warnings: list[str] = []
    doc = None
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:
        logger.warning("Failed to parse PDF document: %s", exc)
        return ExtractionResult(
            status="failed",
            warnings=["Malformed or corrupted PDF document"],
            error_message=f"PDF parsing error: {exc}",
        )

    try:
        if doc.is_encrypted:
            # Attempt to authenticate with blank password
            auth_success = doc.authenticate("")
            if not auth_success:
                return ExtractionResult(
                    status="failed",
                    warnings=["PDF is password-protected"],
                    error_message="Document is encrypted and password-protected",
                )

        page_count = len(doc)
        if page_count == 0:
            return ExtractionResult(
                page_count=0,
                status="completed",
                warnings=["PDF contains 0 pages"],
                text="",
            )

        extracted_pages: list[str] = []
        total_images = 0

        for idx, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            image_list = page.get_images()
            total_images += len(image_list)

            if page_text:
                if page_count > 1:
                    extracted_pages.append(f"--- Page {idx} ---\n{page_text}")
                else:
                    extracted_pages.append(page_text)

        full_text = "\n\n".join(extracted_pages)
        normalized = normalize_extracted_text(full_text)

        # Scanned PDF detection: image(s) present with minimal or no text
        raw_char_count = len(re.sub(r"\s", "", normalized))
        if raw_char_count < 50 and total_images > 0:
            warnings.append(
                "Scanned PDF detected. Document contains minimal or no extractable digital text. OCR is not yet supported."
            )
        elif not normalized:
            warnings.append("Document contains no readable text.")

        return ExtractionResult(
            text=normalized,
            page_count=page_count,
            status="completed",
            warnings=warnings,
        )
    except Exception as exc:
        logger.error("Unexpected error during PDF extraction: %s", exc, exc_info=True)
        return ExtractionResult(
            status="failed",
            warnings=["Unexpected error during text extraction"],
            error_message=str(exc),
        )
    finally:
        if doc is not None:
            doc.close()


def extract_docx_text(content: bytes) -> ExtractionResult:
    """Extract text from DOCX bytes using python-docx.

    Preserves headings, paragraphs, and tables.
    """
    warnings: list[str] = []
    try:
        doc = docx.Document(io.BytesIO(content))
    except Exception as exc:
        logger.warning("Failed to open DOCX document: %s", exc)
        return ExtractionResult(
            status="failed",
            warnings=["Malformed or corrupted DOCX document"],
            error_message=f"DOCX parsing error: {exc}",
        )

    try:
        sections_text: list[str] = []

        # Extract text from paragraphs
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            # Preserve headings format
            if paragraph.style and paragraph.style.name and paragraph.style.name.startswith("Heading"):
                sections_text.append(f"## {text}")
            else:
                sections_text.append(text)

        # Extract text from tables
        for table in doc.tables:
            table_rows: list[str] = []
            for row in table.rows:
                row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                # Filter duplicate adjacent cells from merged table cells
                cleaned_cells: list[str] = []
                for cell in row_cells:
                    if not cleaned_cells or cell != cleaned_cells[-1]:
                        cleaned_cells.append(cell)
                if any(cleaned_cells):
                    table_rows.append(" | ".join(cleaned_cells))
            if table_rows:
                sections_text.append("\n".join(table_rows))

        full_text = "\n\n".join(sections_text)
        normalized = normalize_extracted_text(full_text)

        if not normalized:
            warnings.append("Document contains no readable text.")

        return ExtractionResult(
            text=normalized,
            page_count=None,
            status="completed",
            warnings=warnings,
        )
    except Exception as exc:
        logger.error("Unexpected error during DOCX extraction: %s", exc, exc_info=True)
        return ExtractionResult(
            status="failed",
            warnings=["Unexpected error during text extraction"],
            error_message=str(exc),
        )


def extract_document_text(content: bytes, file_format: str) -> ExtractionResult:
    """Dispatcher to extract text based on validated document format."""
    fmt = file_format.lower().lstrip(".")
    if fmt == "pdf":
        return extract_pdf_text(content)
    if fmt == "docx":
        return extract_docx_text(content)
    return ExtractionResult(
        status="failed",
        warnings=[f"Unsupported format '{file_format}'"],
        error_message=f"Extraction not supported for {file_format}",
    )
