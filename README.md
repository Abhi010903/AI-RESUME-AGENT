# AI Resume Builder — Resume Intelligence Platform

> **Origin & Identity**: This project originally started as a hackathon project (`hackathon project`) and is being systematically transformed into a production-oriented, open-source AI Resume Intelligence Platform.

---

## 1. Project Overview

**AI Resume Builder** is an intelligent resume analysis, profile consolidation, and evaluation platform designed for two independent application domains:

1. **USER Application** *(In Active Development)*: Enables candidates to upload existing resumes, extract structured information, consolidate verified professional history, detect skill gaps, analyze job descriptions, and generate tailored resumes.
2. **COMPANY Application** *(Reserved for Future Development)*: Enables recruiters to define job requirements, ingest candidate resumes through secure pipelines, detect prompt injection, evaluate evidence-backed skills, and perform transparent candidate shortlisting.

---

## 2. Repository Structure

```text
ai-resume-builder/
├── user/                          # User application domain
│   └── backend/                   # Modern FastAPI backend (Phases 1 & 2 complete)
│       ├── app/
│       │   ├── api/               # Health probes, resume ingestion, extraction API
│       │   ├── services/          # Extraction engine, validator, private storage
│       │   ├── config.py          # Pydantic v2 settings & environment management
│       │   ├── database.py        # SQLAlchemy 2.0 engine & session lifecycle
│       │   ├── errors.py          # Consistent error envelope & exception handlers
│       │   ├── logging.py         # Structured JSON logging & request ID tracking
│       │   ├── models.py          # SQLAlchemy Document data models
│       │   ├── schemas.py         # Pydantic request/response schemas
│       │   └── main.py            # FastAPI factory, security headers, middleware
│       ├── tests/                 # 42-test automated regression suite
│       ├── .env.example           # Environment template
│       ├── .gitignore             # Backend-specific ignore rules
│       ├── pytest.ini             # Pytest configuration
│       ├── README.md              # Backend-specific documentation
│       └── requirements.txt       # Minimal, verified production dependencies
│
├── resume_builder/                # Original Hackathon Project (Preserved Archive)
│   ├── resumes/                   # Django app: forms, models, views, migrations
│   ├── resume_builder/            # Django project configuration (settings, urls, wsgi)
│   ├── templates/                 # HTML templates (create, list, update, delete)
│   ├── manage.py                  # Django administrative script
│   └── db.sqlite3                 # Historical hackathon demonstration database
│
├── company/                       # Company / Recruiter application (Reserved)
├── .gitignore                     # Repository-wide exclusions (secrets, storage, caches)
└── README.md                      # Project master documentation
```

---

## 3. Rebuilt Architecture (Phase 1 & Phase 2)

The rebuilt **User Backend** (`user/backend/`) delivers a modular, production-grade foundation:

- **Phase 1 — Backend Foundation**:
  - FastAPI application factory with dynamic environment management.
  - SQLAlchemy 2.0 database abstraction (SQLite locally, forward-compatible with PostgreSQL).
  - Security hardening: Content Security Policy (CSP), HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy.
  - Request ID tracing propagated across all requests, responses, and structured logs.
  - Comprehensive health (`/health`) and readiness (`/ready`) probes.

- **Phase 2 — Resume Ingestion & Extraction**:
  - Secure multi-document batch uploads (1–10 resumes per operation).
  - Binary file signature verification (`%PDF-` magic bytes, OpenXML ZIP structure) preventing MIME spoofing.
  - Zip bomb decompression thresholds (50MB cap) and path traversal sanitization.
  - PyMuPDF extraction engine with scanned/image-only PDF detection and C-library thread serialization.
  - python-docx extraction engine preserving document order, section headers, footers, nested tables, and Structured Document Tags (`w:sdt`).
  - SHA-256 content deduplication avoiding redundant disk storage and extraction overhead.
  - Transaction rollback cleanup and durably retryable document deletion.

---

## 4. Quickstart — User Backend

### Prerequisites
- Python 3.13+
- Virtual environment tool (`venv`)

### Setup & Execution
```bash
# Navigate to the user backend
cd user/backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the test suite (42 tests)
pytest -v

# Start the development server
uvicorn app.main:create_app --factory --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

---

## 5. Security & Privacy

- **Private Storage**: Raw candidate resumes and extracted plain text are stored in private, server-controlled directories outside web-accessible roots.
- **Exclusion by Default**: `.env`, `.venv`, binary caches, local databases, and `storage/` directories are strictly excluded from source control via `.gitignore`.
- **Zero Log Leakage**: Candidate personally identifiable information (PII) and resume text are never logged.

---

## 6. License & Legacy Notice

The `resume_builder/` directory contains original hackathon implementation work created during the project's inception. It is retained to preserve historical context and feature ideas.

The newly rebuilt platform in `user/` is published as open source under the **MIT License**.
