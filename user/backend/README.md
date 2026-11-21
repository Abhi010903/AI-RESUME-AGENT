# AI Resume Agent — User Backend

Core backend for the User application of the **AI Resume Agent** platform.

## Architecture & Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13+)
- **Configuration**: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (environment-driven)
- **Database Layer**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite by default for local development, forward-compatible with PostgreSQL)
- **Document Processing**: [PyMuPDF](https://pymupdf.readthedocs.io/) (PDF) & [python-docx](https://python-docx.readthedocs.io/) (DOCX)
- **Testing**: [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

## Directory Structure

```text
user/backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py          # /health (liveness) & /ready (readiness)
│   │   └── resumes.py         # Resume ingestion, extraction, and document management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extractor.py       # PyMuPDF & python-docx extraction engine with OCR detection
│   │   ├── file_validator.py  # Magic bytes verification, sanitization, and hashing
│   │   └── storage.py         # Private file storage management
│   ├── __init__.py
│   ├── config.py              # Centralized environment settings
│   ├── database.py            # SQLAlchemy engine, session factory, connection checks
│   ├── errors.py              # Consistent API error envelope & exception handlers
│   ├── logging.py             # Structured logging (JSON/Text) with request_id context
│   ├── models.py              # SQLAlchemy Document model
│   ├── schemas.py             # Pydantic request/response schemas
│   └── main.py                # FastAPI factory, security headers, middleware
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Test fixtures and in-memory DB configuration
│   ├── test_config.py         # Settings & validator tests
│   ├── test_database.py       # Session lifecycle, rollback, and URL masking tests
│   ├── test_errors.py         # Error envelope & exception handler tests
│   ├── test_health.py         # Health and readiness probe tests
│   ├── test_resumes.py        # Ingestion, validation, extraction, deduplication tests
│   └── test_security_headers.py # HTTP security headers & Request-ID tests
├── .env.example               # Template environment configuration
├── .gitignore                 # Backend-specific ignore rules
├── pytest.ini                 # Pytest configuration
├── README.md                  # Project documentation
└── requirements.txt           # Minimal pinned dependencies
```

## API Endpoints

### System & Health Probes
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness probe returning process status and app metadata |
| `GET` | `/ready` | Readiness probe actively testing database connectivity |

### Resume Ingestion & Processing (Phase 2)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/resumes/upload` | Ingests 1 to 10 resume documents (PDF or DOCX), validates signatures, stores raw files, and extracts structured text |
| `GET` | `/api/v1/resumes` | Lists uploaded resumes with metadata and processing status (`skip`, `limit` pagination) |
| `GET` | `/api/v1/resumes/{document_id}` | Retrieves full document metadata, extraction status, warnings, and text |
| `GET` | `/api/v1/resumes/{document_id}/text` | Retrieves only the extracted plain text and warnings for downstream processing |
| `DELETE` | `/api/v1/resumes/{document_id}` | Deletes the document record and removes the stored file from disk |

## Ingestion & Security Features

- **Binary Signature Verification**: Validates magic bytes (`%PDF-` for PDF, OpenXML ZIP archive for DOCX); never trusts client-supplied MIME types or extensions.
- **Path Traversal Defense**: Client-supplied filenames are sanitized (`safe_name = sanitize_filename(raw)`). Stored files are written to server-controlled UUID filenames (`{doc_id}.{format}`) inside private storage.
- **Deduplication**: Computes SHA-256 content hashes. Uploads with identical hashes reuse existing completed extraction records, avoiding duplicate disk usage and reprocessing.
- **Scanned PDF Detection**: Inspects pages for image elements combined with sparse/absent digital text. Emits explicit warnings that OCR is not yet supported.
- **Batch Enforcement**: Enforces 1 to 10 files per batch and rejects oversized files (> 10MB default).
- **Sensitive Data Protection**: Resumes and extracted text are stored outside public web directories and excluded from git via `.gitignore`. Resume contents are never logged.

## Running Tests

```bash
pytest -v
```

## License

Provisional recommendation: **MIT License**. Final license decision pending owner confirmation.
