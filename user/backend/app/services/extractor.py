"""Document text extraction engine supporting PDF (PyMuPDF) and DOCX (python-docx)."""

from collections.abc import Iterator
from dataclasses import dataclass, field
import io
import logging
import re
import threading
import docx
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
import pymupdf

logger = logging.getLogger("app.extractor")

# Thread lock to serialize PyMuPDF C-library calls across worker threads
_pdf_extraction_lock = threading.Lock()


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
    Serialized across worker threads for C-library isolation.
    """
    with _pdf_extraction_lock:
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
            raw_digital_chars = 0

            for idx, page in enumerate(doc, start=1):
                page_text = page.get_text("text").strip()
                image_list = page.get_images()
                total_images += len(image_list)
                # Measure actual digital character count before synthetic page markers are attached
                raw_digital_chars += len(re.sub(r"\s", "", page_text))

                if page_text:
                    if page_count > 1:
                        extracted_pages.append(f"--- Page {idx} ---\n{page_text}")
                    else:
                        extracted_pages.append(page_text)

            full_text = "\n\n".join(extracted_pages)
            normalized = normalize_extracted_text(full_text)

            # Scanned PDF detection: image(s) present with minimal or no text measured from source
            if raw_digital_chars < 50 and total_images > 0:
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


def _iter_block_elements(parent_elem: object, doc: docx.Document) -> Iterator[str]:
    """Yield extracted text blocks from XML container elements in document order.

    Handles paragraphs, tables, and block-level structured document tags (w:sdt).
    """
    if not hasattr(parent_elem, "iterchildren"):
        return

    for child in parent_elem.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            text = p.text.strip()
            if text:
                if p.style and p.style.name and p.style.name.startswith("Heading"):
                    yield f"## {text}"
                else:
                    yield text
        elif tag == "tbl":
            tbl = Table(child, doc)
            t_rows = _extract_table_rows(tbl, doc)
            if t_rows:
                yield "\n".join(t_rows)
        elif tag == "sdt":
            for subchild in child.iterchildren():
                if subchild.tag.split("}")[-1] == "sdtContent":
                    yield from _iter_block_elements(subchild, doc)


def _extract_cell_content(cell: _Cell, doc: docx.Document) -> str:
    """Extract cell content in document order across paragraphs, nested tables, and SDTs."""
    parts: list[str] = []

    def _extract_from(container: object) -> None:
        if not hasattr(container, "iterchildren"):
            return
        for child in container.iterchildren():
            tag = child.tag.split("}")[-1]
            if tag == "p":
                p = Paragraph(child, cell)
                t = p.text.strip().replace("\n", " ")
                if t:
                    parts.append(t)
            elif tag == "tbl":
                tbl = Table(child, doc)
                nested_rows = _extract_table_rows(tbl, doc)
                if nested_rows:
                    nested_str = " | ".join(nested_rows)
                    parts.append(f"[{nested_str}]")
            elif tag == "sdt":
                for subchild in child.iterchildren():
                    if subchild.tag.split("}")[-1] == "sdtContent":
                        _extract_from(subchild)

    _extract_from(cell._tc)
    return " ".join(parts).strip()


def _extract_table_rows(table: Table, doc: docx.Document) -> list[str]:
    """Extract rows from a DOCX table, traversing cells in document order and comparing cell XML identity."""
    table_rows: list[str] = []
    for row in table.rows:
        seen_tcs: set[object] = set()
        cleaned_cells: list[str] = []
        for cell in row.cells:
            # Compare underlying XML cell identity to correctly preserve distinct cells with identical text
            if cell._tc in seen_tcs:
                continue
            seen_tcs.add(cell._tc)

            cell_text = _extract_cell_content(cell, doc)
            cleaned_cells.append(cell_text)

        if any(cleaned_cells):
            table_rows.append(" | ".join(cleaned_cells))
    return table_rows


def extract_docx_text(content: bytes) -> ExtractionResult:
    """Extract text from DOCX bytes in document order using python-docx.

    Traverses headers, body paragraphs, tables, block content controls (w:sdt), and footers.
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
        seen_hdrftr_parts: set[object] = set()

        # 1. Section Headers (deduplicating linked and shared header parts)
        for section in doc.sections:
            headers_to_check = (
                section.header,
                getattr(section, "first_page_header", None),
                getattr(section, "even_page_header", None),
            )
            for hdr in headers_to_check:
                if hdr is not None and not getattr(hdr, "is_linked_to_previous", False):
                    hdr_part = getattr(hdr, "part", None)
                    if hdr_part is not None:
                        if hdr_part in seen_hdrftr_parts:
                            continue
                        seen_hdrftr_parts.add(hdr_part)
                    sections_text.extend(_iter_block_elements(hdr._element, doc))

        # 2. Document Body Elements (document order: paragraphs, tables, block content controls)
        sections_text.extend(_iter_block_elements(doc.element.body, doc))

        # 3. Section Footers (deduplicating linked and shared footer parts)
        for section in doc.sections:
            footers_to_check = (
                section.footer,
                getattr(section, "first_page_footer", None),
                getattr(section, "even_page_footer", None),
            )
            for ftr in footers_to_check:
                if ftr is not None and not getattr(ftr, "is_linked_to_previous", False):
                    ftr_part = getattr(ftr, "part", None)
                    if ftr_part is not None:
                        if ftr_part in seen_hdrftr_parts:
                            continue
                        seen_hdrftr_parts.add(ftr_part)
                    sections_text.extend(_iter_block_elements(ftr._element, doc))

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
