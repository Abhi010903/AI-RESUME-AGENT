# Candidate-Facing AI Resume Intelligence Platform

A self-hostable, evidence-based AI resume intelligence and tailoring platform designed for candidates.

The platform enables candidates to:
1. **Ingest & Parse Multiple Resumes**: Upload multiple resume versions (PDF & DOCX) with C-level parsing using PyMuPDF and python-docx, preserving document structure and page boundaries.
2. **Consolidate Candidate Evidence**: Merge fragmented resumes into a single verified candidate profile with automated cross-document deduplication and conflict detection.
3. **Analyze Target Job Descriptions**: Extract structured competencies (mandatory technical skills, preferred skills, responsibilities, qualifications, and eligibility warnings) from text or uploaded documents (`.pdf`, `.docx`, `.txt`, `.md`).
4. **Evidence-Based Skill Matching**: Run deterministic 6-dimension skill matching with confidence scoring, evidence source citations, and actionable gap analysis.
5. **Reactive Stale Invalidation**: Automatically flag downstream match results as stale whenever candidate profile facts or target job requirements are updated.
6. **Tailored Single-Page Resume Generation**: Generate strictly single-page, A4 standard-compliant (210 x 297 mm / 595.28 x 841.89 pt) resumes in both DOCX and vector PDF formats with claim-level provenance mapping (guaranteeing zero hallucinations).
7. **Transparent 7-Dimension ATS Evaluation**: Audit generated resumes against enterprise ATS parsing criteria with keyword density scoring, keyword stuffing detection, format parsability, and a closed-loop "Improve Resume in Builder" action.
8. **8-Stage Job Application Pipeline**: Manage active applications, interview stages, and notes in an interactive Kanban pipeline with direct resume version linking.
9. **Dynamic Workflow & Audit Logger**: Real-time 12-stage lifecycle progress tracking, state-based primary next action recommendation, and an immutable activity audit stream.
10. **Security & Data Portability**: Argon2id / PBKDF2 password security, sliding-window rate limiting on login, multi-tenant IDOR protection, and 1-click JSON career knowledge base export.

---

## Comprehensive Platform Documentation

The platform includes 12 exhaustive technical and user-facing specifications in `user/`:

1. [PRODUCT_SPECIFICATION.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/PRODUCT_SPECIFICATION.md) — Product vision, personas, 12-step lifecycle, 9 core modules, and non-functional specifications.
2. [BUSINESS_LOGIC.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/BUSINESS_LOGIC.md) — Architectural tenets, master source of truth, cross-module stale invalidations, scoring algorithms, and workflow engine rules.
3. [USER_WORKFLOW_GUIDE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/USER_WORKFLOW_GUIDE.md) — Detailed non-technical candidate walkthrough covering all 12 stages, buttons, inputs, and FAQs.
4. [SYSTEM_ARCHITECTURE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/SYSTEM_ARCHITECTURE.md) — High-level architecture, module decomposition, middleware pipeline, service boundaries, and storage layout.
5. [DATABASE_ARCHITECTURE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/DATABASE_ARCHITECTURE.md) — Complete ERD, 15 database tables, column types, foreign key cascades, and SQLite WAL mode.
6. [API_REFERENCE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/API_REFERENCE.md) — Complete REST API reference across all 9 routers including request/response schemas and status codes.
7. [FRONTEND_ARCHITECTURE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/FRONTEND_ARCHITECTURE.md) — React 19 + TypeScript component hierarchy, service client, design system tokens, and state patterns.
8. [DEVELOPMENT_GUIDE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/DEVELOPMENT_GUIDE.md) — Local development setup, environment variables, test runners, and build procedures.
9. [SECURITY_AUDIT.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/SECURITY_AUDIT.md) — Threat model, password hashing, JWT blacklisting, multi-tenant IDOR defense, and magic byte validation.
10. [TESTING_STRATEGY.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/TESTING_STRATEGY.md) — Test pyramid, automated test matrix, E2E journey validation, and regression suites.
11. [PRODUCTION_READINESS_REPORT.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/PRODUCTION_READINESS_REPORT.md) — Production audit report verifying compliance with all requirements and test results (104 passing tests).
12. [MANUAL_TESTING_GUIDE.md](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/MANUAL_TESTING_GUIDE.md) — Step-by-step evaluator instructions for launching services and verifying all features locally.

---

## Architecture Overview

```
user/
├── backend/                  # FastAPI Application (Python 3.13)
│   ├── app/
│   │   ├── api/              # API Routers (auth, resumes, profiles, jobs, matches, generation, ats, applications, workflow)
│   │   ├── core/             # Security, config, logging, rate limiting
│   │   ├── models.py         # SQLAlchemy 2.0 ORM Models
│   │   ├── schemas.py        # Pydantic v2 Request/Response Schemas
│   │   ├── database.py       # Engine & Connection Pool Management
│   │   └── services/         # Domain Business Logic & AI Services
│   ├── storage/              # Local disk storage (uploads, jobs, generated_resumes)
│   └── tests/                # 18 Pytest Test Modules (104 Passing Tests)
│
├── frontend/                 # React 19 + TypeScript + Vite Application
│   ├── src/
│   │   ├── components/       # Design System UI Primitives (Button, Modal, Input, Badge, Card) & Layout
│   │   ├── pages/            # Feature Workspaces (Dashboard, Resumes, Profile, Jobs, Matching, Generation, ATS, Applications, Settings, Auth)
│   │   ├── context/          # Auth Context & JWT Session Management
│   │   └── services/         # Centralized API Client (api.ts)
│   └── vite.config.ts        # ESM-native Vite bundler configuration
```

---

## Quick Start

### 1. Start the Candidate Backend

```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base: `http://127.0.0.1:8000/api/v1`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/v1/health`

### 2. Start the Candidate Frontend

```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
npm run dev
```

- Web App: `http://localhost:5173`

---

## Automated Verification

- **Backend Test Suite**:
  ```powershell
  cd C:\Coding\Projects\AI-RESUME-AGENT\user\backend
  python -m pytest tests -q
  ```
  *(104 passed, 0 failed in ~17s)*

- **Frontend Production Build**:
  ```powershell
  cd C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
  npm run build
  ```
  *(Built successfully in ~1.4s with 0 TypeScript errors)*
