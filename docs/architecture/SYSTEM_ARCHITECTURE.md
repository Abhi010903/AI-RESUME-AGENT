# AI Resume Intelligence Platform — Architecture Specification

## 1. Executive Summary

The AI Resume Intelligence Platform is an open-source, dual-domain system engineered to provide transparent, evidence-based resume intelligence for job seekers (`user/`) and recruiters (`company/`).

---

## 2. System Architecture

```text
ai-resume-builder/
├── user/                          # Candidate Application Domain
│   └── backend/                   # FastAPI Core Application (Phases 1 & 2 Complete)
│       ├── app/
│       │   ├── api/               # API Routers (Health, Ingestion)
│       │   ├── services/          # Document Extractor, File Validator, Storage
│       │   ├── config.py          # Pydantic v2 Settings
│       │   ├── database.py        # SQLAlchemy 2.0 Engine & Session
│       │   ├── errors.py          # Unified Error Envelope
│       │   ├── logging.py         # Structured JSON Logging
│       │   ├── models.py          # Document ORM Models
│       │   └── schemas.py         # Request/Response Schemas
│       └── tests/                 # Regression Test Suite
├── legacy/                        # Archived Hackathon Implementation (Preserved Reference)
├── company/                       # Recruiter Domain (Reserved)
├── docs/                          # Architecture & Planning Documentation
├── .gitignore                     # Repository Exclusions
└── README.md                      # Platform Master Documentation
```

---

## 3. Core Architectural Principles

1. **Deterministic Processing First**: High-risk tasks (parsing, validation, hashing, dates, contact details) use deterministic Python parsers (`pymupdf`, `python-docx`) rather than non-deterministic LLM calls.
2. **Ground Truth Candidate Profile**: The candidate's verified profile is the single source of truth. LLMs are never permitted to hallucinate qualifications, dates, companies, or skills.
3. **Traceability**: All extracted facts and skills link back to source document evidence.
4. **Security by Design**: Private storage for resumes, strict binary signature validation, request ID tracing, CSP security headers, and zero PII logging.
