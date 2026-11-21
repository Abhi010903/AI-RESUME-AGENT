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

## 3. Rebuilt Architecture (Stages 1 through 5)

The rebuilt **User Backend** (`user/backend/`) delivers a modular, production-grade foundation:

- **Stage 1 — Backend Foundation**:
  - FastAPI application factory with dynamic environment management.
  - SQLAlchemy 2.0 database abstraction (SQLite locally, forward-compatible with PostgreSQL).
  - Security hardening: Content Security Policy (CSP), HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy.
  - Request ID tracing propagated across all requests, responses, and structured logs.
  - Comprehensive health (`/health`) and readiness (`/ready`) probes.

- **Stage 2 — Resume Ingestion & Extraction**:
  - Secure multi-document batch uploads (1–10 resumes per operation).
  - Binary file signature verification (`%PDF-` magic bytes, OpenXML ZIP structure) preventing MIME spoofing.
  - Zip bomb decompression thresholds (50MB cap) and path traversal sanitization.
  - PyMuPDF extraction engine with scanned/image-only PDF detection and C-library thread serialization.
  - python-docx extraction engine preserving document order, section headers, footers, nested tables, and Structured Document Tags (`w:sdt`).
  - SHA-256 content deduplication avoiding redundant disk storage and extraction overhead.
  - Transaction rollback cleanup and durably retryable document deletion.

- **Stage 3 — Candidate Profile Intelligence**:
  - Multi-resume consolidation across 1–10 extracted candidate documents.
  - Entity deduplication and fusion for work experiences, degrees, skills, and certifications.
  - Source document traceability preserved for every extracted entity.
  - Conflict detection engine for overlapping employment dates, chronology anomalies, career gaps, and identity mismatches.
  - Candidate review, manual entity updates, and approval workflows (`/api/v1/profiles/...`).

- **Stage 4 — Job Description Intelligence**:
  - Unstructured plain-text and pasted job description ingestion.
  - Automatic extraction of title, company, location, employment type, and seniority levels.
  - Requirement classification: Mandatory vs. Preferred qualifications, responsibilities, and experience limits.
  - Reusable skill normalization and canonical taxonomy mapping (`k8s` → `Kubernetes`, `py` → `Python`, `postgres` → `PostgreSQL`).
  - Strict skill distinction preservation (Java ≠ JavaScript, React ≠ Angular, AWS ≠ Azure).
  - Quality and completeness warnings (missing titles, vague descriptions, contradictory experience demands).

- **Stage 5 — Evidence-Based Skill Matching Engine**:
  - Strict evidence-based matching: candidates never receive credit without verified profile evidence.
  - Classification categories: `STRONG_MATCH`, `PARTIAL_MATCH`, `RELATED_MATCH`, `NO_EVIDENCE`, `CONFLICTED_EVIDENCE`, `NOT_ASSESSED`.
  - Transferable skill relationship graph (e.g. FastAPI relates to Python/REST APIs; React relates to JavaScript/TypeScript).
  - Experience matching with non-overlapping calendar duration calculation to prevent double-counting.
  - Academic degree hierarchy evaluation and professional certification verification.
  - Configurable weighted scoring model (Mandatory Skills 40%, Experience 20%, Preferred Skills 15%, Education 10%, Domain 10%, Certifications 5%).
  - Missing mandatory skills penalty and conflict impact deductions.
  - Structured gap analysis with actionable evidence development recommendations.
  - Full traceability: every match links back to candidate entities and Stage 2 source documents.

- **Stage 6 — Tailored Resume Generation & ATS Evaluation**:
  - Truthful, evidence-backed tailored resume generation strictly grounded in candidate profile data (zero hallucinations).
  - Clean single-column ATS typography with 0.75" margins, standard headers, and bulleted accomplishments.
  - Dual document export: professional `.docx` via `python-docx` and vector-rendered `.pdf` via `PyMuPDF`.
  - Consecutive version control (`v1`, `v2`, ...) with automated diffing and score progression tracking.
  - Transparent 7-dimension ATS scoring engine: Mandatory Skill Coverage (30%), Preferred Skill Coverage (15%), Experience Alignment (20%), Education Alignment (10%), Keyword Relevance & Natural Frequency (10%), Document Structure & Parsability (10%), Readability & Formatting (5%).
  - Anti-gaming keyword stuffing detection, formatting warnings, and actionable improvement recommendations.

- **Stage 7 — Authentication, Authorization & Production Hardening**:
  - Candidate registration and login with PBKDF2-HMAC-SHA256 password hashing (600,000 iterations, random salt).
  - Cryptographically signed HS256 JWT access tokens with expiration validation (built-in standard library).
  - Multi-tenant data isolation protecting candidate documents, profiles, generated resumes, and ATS evaluations.
  - Insecure Direct Object Reference (IDOR) prevention returning 404 on cross-tenant resource access attempts.
  - Production security headers: CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy.
  - Zero log leakage of candidate PII, passwords, or document text.

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

# Run the test suite (84 automated tests)
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
