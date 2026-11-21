"""Comprehensive tests for Resume Ingestion and Extraction (Phase 2)."""

import io
from fastapi.testclient import TestClient
import pymupdf
import docx
import pytest
from starlette import status


def _make_pdf(text: str = "Jane Doe\nSoftware Engineer\nPython, FastAPI", pages: int = 1) -> bytes:
    """Helper to generate a clean PDF in memory."""
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((50, 72), f"{text}\nPage {i + 1}")
    data = doc.tobytes()
    doc.close()
    return data


def _make_scanned_pdf() -> bytes:
    """Helper to generate an image-only PDF without digital text."""
    doc = pymupdf.open()
    page = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 10, 10), 1)
    page.insert_image(pymupdf.Rect(50, 50, 200, 200), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


def _make_encrypted_pdf(password: str = "secret123") -> bytes:
    """Helper to generate an encrypted PDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Confidential resume data")
    data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
    doc.close()
    return data


def _make_docx(heading: str = "Jane Doe", text: str = "Senior Developer with Python experience") -> bytes:
    """Helper to generate a clean DOCX in memory with heading and table."""
    doc = docx.Document()
    doc.add_heading(heading, level=1)
    doc.add_paragraph(text)
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Skill"
    table.rows[0].cells[1].text = "Proficiency"
    table.rows[1].cells[0].text = "Python"
    table.rows[1].cells[1].text = "Expert"
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def test_upload_single_pdf_success(client: TestClient) -> None:
    """Upload a valid PDF and verify metadata and text extraction."""
    pdf_bytes = _make_pdf("John Doe\nData Scientist\nMachine Learning, Python")
    files = [("files", ("resume_john.pdf", pdf_bytes, "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["total_submitted"] == 1
    assert data["successful_count"] == 1
    assert data["failed_count"] == 0

    doc = data["documents"][0]
    assert doc["filename"] == "resume_john.pdf"
    assert doc["file_format"] == "pdf"
    assert doc["status"] == "completed"
    assert doc["page_count"] == 1
    assert "John Doe" in doc["extracted_text"]
    assert "Data Scientist" in doc["extracted_text"]


def test_upload_single_docx_success(client: TestClient) -> None:
    """Upload a valid DOCX and verify heading and table extraction."""
    docx_bytes = _make_docx(heading="Alice Smith", text="Frontend Architect with React and TypeScript")
    files = [("files", ("alice_cv.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["successful_count"] == 1

    doc = data["documents"][0]
    assert doc["filename"] == "alice_cv.docx"
    assert doc["file_format"] == "docx"
    assert doc["status"] == "completed"
    assert "## Alice Smith" in doc["extracted_text"]
    assert "Frontend Architect" in doc["extracted_text"]
    assert "Skill | Proficiency" in doc["extracted_text"]


def test_upload_batch_multiple_documents(client: TestClient) -> None:
    """Upload a batch of multiple mixed documents (1-10 allowed)."""
    files = [
        ("files", ("dev1.pdf", _make_pdf("Developer One"), "application/pdf")),
        ("files", ("dev2.docx", _make_docx("Developer Two", "Python dev"), "application/octet-stream")),
        ("files", ("dev3.pdf", _make_pdf("Developer Three"), "application/pdf")),
    ]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["total_submitted"] == 3
    assert data["successful_count"] == 3
    assert len(data["documents"]) == 3


def test_upload_batch_exceeds_maximum_limit(client: TestClient) -> None:
    """Reject upload if more than 10 files are submitted in one request."""
    files = [
        ("files", (f"dev_{i}.pdf", _make_pdf(f"Candidate {i}"), "application/pdf"))
        for i in range(11)
    ]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "INVALID_BATCH_SIZE"


def test_signature_spoofing_pdf_rejected(client: TestClient) -> None:
    """Reject file with .pdf extension that is actually plain text or non-PDF bytes."""
    fake_pdf = b"Hello, this is just a text file renamed to resume.pdf"
    files = [("files", ("fake.pdf", fake_pdf, "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["failed_count"] == 1
    doc = data["documents"][0]
    assert doc["status"] == "failed"
    assert "invalid signature" in doc["error_message"].lower()


def test_signature_spoofing_docx_rejected(client: TestClient) -> None:
    """Reject file with .docx extension that lacks DOCX OpenXML structure."""
    fake_docx = b"Not a real docx archive"
    files = [("files", ("fake.docx", fake_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["failed_count"] == 1
    doc = data["documents"][0]
    assert doc["status"] == "failed"


def test_empty_file_rejected(client: TestClient) -> None:
    """Reject 0-byte empty files."""
    files = [("files", ("empty.pdf", b"", "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["failed_count"] == 1
    assert "empty" in data["documents"][0]["error_message"].lower()


def test_scanned_pdf_detected_with_ocr_warning(client: TestClient) -> None:
    """Detect image-only / scanned PDF and warn that OCR is not yet supported."""
    scanned_bytes = _make_scanned_pdf()
    files = [("files", ("scanned_resume.pdf", scanned_bytes, "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    doc = data["documents"][0]
    assert doc["status"] == "completed"
    assert any("Scanned PDF detected" in w for w in doc["warnings"])
    assert any("OCR is not yet supported" in w for w in doc["warnings"])


def test_encrypted_pdf_marked_failed(client: TestClient) -> None:
    """Handle password-protected PDF gracefully without crashing."""
    encrypted_bytes = _make_encrypted_pdf(password="secret")
    files = [("files", ("locked.pdf", encrypted_bytes, "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    doc = data["documents"][0]
    assert doc["status"] == "failed"
    assert "password-protected" in doc["error_message"]


def test_duplicate_file_upload_deduplicated(client: TestClient) -> None:
    """Duplicate file upload should reuse the existing processed document."""
    pdf_bytes = _make_pdf("Unique Candidate Record")
    files1 = [("files", ("candidate_v1.pdf", pdf_bytes, "application/pdf"))]
    files2 = [("files", ("candidate_copy.pdf", pdf_bytes, "application/pdf"))]

    # First upload
    res1 = client.post("/api/v1/resumes/upload", files=files1)
    doc1 = res1.json()["documents"][0]

    # Second upload of identical content
    res2 = client.post("/api/v1/resumes/upload", files=files2)
    doc2 = res2.json()["documents"][0]

    assert doc1["id"] == doc2["id"]
    assert any("Duplicate file detected" in w for w in doc2["warnings"])


def test_filename_sanitization_path_traversal(client: TestClient) -> None:
    """Sanitize malicious filenames containing path traversal or illegal characters."""
    pdf_bytes = _make_pdf("Secure Candidate")
    malicious_name = "../../../etc/passwd.pdf"
    files = [("files", (malicious_name, pdf_bytes, "application/pdf"))]

    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    doc = response.json()["documents"][0]
    assert ".." not in doc["filename"]
    assert "/" not in doc["filename"]
    assert "\\" not in doc["filename"]
    assert doc["filename"].endswith(".pdf")


def test_list_resumes_and_pagination(client: TestClient) -> None:
    """Test GET /api/v1/resumes listing and pagination."""
    files = [("files", ("list_test.pdf", _make_pdf("Listing Test"), "application/pdf"))]
    client.post("/api/v1/resumes/upload", files=files)

    response = client.get("/api/v1/resumes?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    assert "extracted_text" not in items[0]  # List view omits full text for payload efficiency


def test_get_resume_by_id_and_not_found(client: TestClient) -> None:
    """Test GET /api/v1/resumes/{id} and 404 for missing IDs."""
    files = [("files", ("detail_test.pdf", _make_pdf("Detail Test Candidate"), "application/pdf"))]
    upload_res = client.post("/api/v1/resumes/upload", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    # Valid ID
    detail_res = client.get(f"/api/v1/resumes/{doc_id}")
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.json()["id"] == doc_id
    assert "Detail Test Candidate" in detail_res.json()["extracted_text"]

    # Non-existent ID
    missing_res = client.get("/api/v1/resumes/00000000-0000-0000-0000-000000000000")
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND
    assert missing_res.json()["status"] == "error"
    assert missing_res.json()["error"]["code"] == "NOT_FOUND"


def test_get_resume_text_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/resumes/{id}/text returns clean text payload."""
    files = [("files", ("text_test.pdf", _make_pdf("Specialized Skillset\nKubernetes, Golang"), "application/pdf"))]
    upload_res = client.post("/api/v1/resumes/upload", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    text_res = client.get(f"/api/v1/resumes/{doc_id}/text")
    assert text_res.status_code == status.HTTP_200_OK
    data = text_res.json()
    assert data["id"] == doc_id
    assert "Specialized Skillset" in data["extracted_text"]


def test_delete_resume_success(client: TestClient) -> None:
    """Test DELETE /api/v1/resumes/{id} removes record and disk file."""
    files = [("files", ("to_delete.pdf", _make_pdf("Disposable Resume"), "application/pdf"))]
    upload_res = client.post("/api/v1/resumes/upload", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    del_res = client.delete(f"/api/v1/resumes/{doc_id}")
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["status"] == "deleted"

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/resumes/{doc_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_unsupported_file_extension_rejected(client: TestClient) -> None:
    """Reject files with unsupported extensions (e.g. .txt, .sh, .exe)."""
    files = [("files", ("notes.txt", b"Plain text resume notes", "text/plain"))]
    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["failed_count"] == 1
    assert "unsupported" in data["documents"][0]["error_message"].lower()


def test_multi_page_pdf_structure_preserved(client: TestClient) -> None:
    """Verify multi-page PDF preserves page count and page headers."""
    multi_page_pdf = _make_pdf("Page Content Here", pages=3)
    files = [("files", ("multipage.pdf", multi_page_pdf, "application/pdf"))]
    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == status.HTTP_201_CREATED
    doc = response.json()["documents"][0]
    assert doc["page_count"] == 3
    assert "--- Page 1 ---" in doc["extracted_text"]
    assert "--- Page 2 ---" in doc["extracted_text"]
    assert "--- Page 3 ---" in doc["extracted_text"]


def test_get_text_for_failed_extraction_returns_400(client: TestClient) -> None:
    """GET /api/v1/resumes/{id}/text should return 400 if the document extraction failed."""
    files = [("files", ("corrupt.pdf", b"corrupted header", "application/pdf"))]
    upload_res = client.post("/api/v1/resumes/upload", files=files)
    doc_id = upload_res.json()["documents"][0]["id"]

    response = client.get(f"/api/v1/resumes/{doc_id}/text")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["status"] == "error"
    assert response.json()["error"]["code"] == "EXTRACTION_FAILED"

