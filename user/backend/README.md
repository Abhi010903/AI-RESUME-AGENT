# AI Resume Agent — User Backend

Core backend for the User application of the **AI Resume Agent** platform.

## Architecture & Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13+)
- **Configuration**: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (environment-driven)
- **Database Layer**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite by default for local development, forward-compatible with PostgreSQL)
- **Document Processing**: [PyMuPDF](https://pymupdf.readthedocs.io/) (PDF) & [python-docx](https://python-docx.readthedocs.io/) (DOCX)
- **Skill Normalization & Taxonomy**: Deterministic canonical taxonomy, alias mapping, and transferable skill graph
- **Testing**: [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

## Directory Structure

```text
user/backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py            # /health (liveness) & /ready (readiness)
│   │   ├── resumes.py           # Stage 2: Resume ingestion & document management
│   │   ├── profiles.py          # Stage 3: Candidate profile intelligence & conflict review
│   │   ├── jobs.py              # Stage 4: Job description intelligence & requirement extraction
│   │   ├── matches.py           # Stage 5: Evidence-based skill matching engine
│   │   ├── generation.py        # Stage 6: Tailored resume generation & document export
│   │   ├── ats.py               # Stage 6: 7-dimension ATS evaluation engine
│   │   └── auth.py              # Stage 7: Candidate authentication & account endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extractor.py         # PyMuPDF & python-docx extraction engine with OCR detection
│   │   ├── file_validator.py    # Magic bytes verification, sanitization, and hashing
│   │   ├── storage.py           # Private file storage management
│   │   ├── profile_parser.py    # Deterministic resume text parser
│   │   ├── profile_consolidator.py # Multi-resume deduplication and fusion
│   │   ├── conflict_detector.py # Chronology, overlap, and identity conflict detector
│   │   ├── skill_normalizer.py  # Canonical skills taxonomy, aliases, and transferability graph
│   │   ├── job_description_parser.py # Section extraction, requirements classifier, and warnings
│   │   ├── skill_matcher.py     # Evidence-based requirement-to-profile matcher
│   │   ├── experience_matcher.py # Non-overlapping duration calculation and domain relevance
│   │   ├── qualification_matcher.py # Degree hierarchy and professional certification matcher
│   │   ├── match_scorer.py      # Configurable weighted scoring model and penalty engine
│   │   ├── gap_analyzer.py      # Structured missing skill, education, and experience gap analysis
│   │   ├── resume_tailorer.py   # Job-targeted factual tailoring (zero hallucinations)
│   │   ├── resume_generator.py  # DOCX (python-docx) and PDF (PyMuPDF) vector rendering
│   │   ├── ats_evaluator.py     # Transparent 7-dimension ATS evaluation engine
│   │   └── auth.py              # PBKDF2-HMAC-SHA256 & pure standard-library HS256 JWT
│   ├── __init__.py
│   ├── config.py                # Centralized environment settings
│   ├── database.py              # SQLAlchemy engine, session factory, connection checks
│   ├── errors.py                # Consistent API error envelope & exception handlers
│   ├── logging.py               # Structured logging (JSON/Text) with request_id context
│   ├── models.py                # SQLAlchemy models (Document, Profile, Job, Match, GeneratedResume, ATSEvaluation, User)
│   ├── schemas.py               # Pydantic request/response schemas
│   └── main.py                  # FastAPI factory, security headers, middleware
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures and in-memory DB configuration
│   ├── test_config.py           # Settings & validator tests
│   ├── test_database.py         # Session lifecycle, rollback, and URL masking tests
│   ├── test_errors.py           # Error envelope & exception handler tests
│   ├── test_health.py           # Health and readiness probe tests
│   ├── test_resumes.py          # Stage 2: Ingestion, validation, extraction, deduplication tests
│   ├── test_profiles.py         # Stage 3: Consolidation, conflict resolution, approval tests
│   ├── test_jobs.py             # Stage 4: Job description parsing, classification, skills tests
│   ├── test_matches.py          # Stage 5: Matching engine, scoring, and gap analysis tests
│   ├── test_matching_integration.py # Multi-stage end-to-end integration test (Stages 1–5)
│   ├── test_generation.py       # Stage 6: Tailored resume generation, DOCX/PDF export, versioning
│   ├── test_ats.py              # Stage 6: 7-dimension ATS scoring, keyword stuffing checks
│   ├── test_auth.py             # Stage 7: Registration, PBKDF2 hashing, login, JWT validation
│   ├── test_security_isolation.py # Stage 7: Multi-tenant data isolation & IDOR prevention
│   └── test_security_headers.py # HTTP security headers & Request-ID tests
├── .env.example                 # Template environment configuration
├── .gitignore                   # Backend-specific ignore rules
├── pytest.ini                   # Pytest configuration
├── README.md                    # Project documentation
└── requirements.txt             # Minimal pinned dependencies
```

## API Endpoints

### System & Health Probes (Stage 1)
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness probe returning process status and app metadata |
| `GET` | `/ready` | Readiness probe actively testing database connectivity |

### Resume Ingestion & Extraction (Stage 2)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/resumes/upload` | Ingests 1 to 10 resume documents (PDF or DOCX), validates signatures, stores raw files, and extracts structured text |
| `GET` | `/api/v1/resumes` | Lists uploaded resumes with metadata and processing status (`skip`, `limit` pagination) |
| `GET` | `/api/v1/resumes/{document_id}` | Retrieves full document metadata, extraction status, warnings, and text |
| `GET` | `/api/v1/resumes/{document_id}/text` | Retrieves only the extracted plain text and warnings for downstream processing |
| `DELETE` | `/api/v1/resumes/{document_id}` | Deletes the document record and removes the stored file from disk |

### Candidate Profile Intelligence (Stage 3)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/profiles/consolidate` | Fuses 1 to 10 extracted resumes into a unified candidate profile, deduplicates experiences/education/skills, preserves document traceability, and evaluates chronology conflicts |
| `GET` | `/api/v1/profiles/{profile_id}` | Retrieves full candidate profile with experiences, education, skills, certifications, and detected conflicts |
| `PATCH` | `/api/v1/profiles/{profile_id}` | Updates general candidate contact information, headline, and summary |
| `PATCH` | `/api/v1/profiles/{profile_id}/experiences/{exp_id}` | Updates a specific work experience record and sets approval status |
| `PATCH` | `/api/v1/profiles/{profile_id}/education/{edu_id}` | Updates an academic qualification record and sets approval status |
| `PATCH` | `/api/v1/profiles/{profile_id}/skills/{skill_id}` | Updates a skill record (name, category, proficiency, years) |
| `PATCH` | `/api/v1/profiles/{profile_id}/certifications/{cert_id}` | Updates a professional certification record |
| `POST` | `/api/v1/profiles/{profile_id}/conflicts/{conflict_id}` | Resolves or dismisses a detected conflict with candidate notes |
| `POST` | `/api/v1/profiles/{profile_id}/approve` | Approves specific profile entities or the complete profile |

### Job Description Intelligence (Stage 4)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/jobs/analyze` | Ingests plain-text or pasted job description, extracts title, seniority, min/max experience, responsibilities, mandatory vs preferred skills, and persists the structured record |
| `POST` | `/api/v1/jobs` | Creates and persists a job description with automatic requirement extraction |
| `GET` | `/api/v1/jobs` | Lists stored job descriptions with pagination and optional seniority filtering |
| `GET` | `/api/v1/jobs/{job_id}` | Retrieves complete structured job description record |
| `PATCH` | `/api/v1/jobs/{job_id}` | Updates editable job fields (title, company, location, experience range, status) |
| `GET` | `/api/v1/jobs/{job_id}/requirements` | Retrieves itemized mandatory and preferred requirements breakdown |
| `GET` | `/api/v1/jobs/{job_id}/skills` | Retrieves normalized required and preferred skills with canonical taxonomy names |

### Evidence-Based Skill Matching Engine (Stage 5)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/matches` | Executes evidence-based matching between a candidate profile and a structured job description |
| `GET` | `/api/v1/matches/{match_id}` | Retrieves complete match result with sub-scores, requirement breakdown, and gaps |
| `GET` | `/api/v1/matches` | Lists match results with filtering by `profile_id`, `job_id`, and pagination |
| `GET` | `/api/v1/matches/{match_id}/requirements` | Retrieves requirement-level match status, evidence excerpts, and source document IDs |
| `GET` | `/api/v1/matches/{match_id}/gaps` | Retrieves structured gap analysis (missing mandatory, missing preferred, related skills, experience gaps) |
| `GET` | `/api/v1/matches/{match_id}/score` | Retrieves score breakdown with weights, sub-scores, penalties applied, and disclaimers |

### Resume Generation & Versioning (Stage 6)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/resumes/generate` | Generates tailored resume strictly grounded in candidate evidence, renders DOCX & PDF, runs ATS audit |
| `GET` | `/api/v1/resumes/generated` | Lists generated resumes with optional `profile_id` and `job_id` filtering |
| `GET` | `/api/v1/resumes/generated/{id}` | Retrieves tailored resume metadata and full section content |
| `GET` | `/api/v1/resumes/generated/{id}/download` | Downloads generated resume document (`?format=pdf` or `?format=docx`) |
| `GET` | `/api/v1/resumes/generated/{id}/versions` | Compares current resume version against preceding version |

### ATS Evaluation Engine (Stage 6)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/ats/evaluate` | Evaluates a generated resume across 7 transparent dimensions, checks keyword stuffing |
| `GET` | `/api/v1/ats/reports/{id}` | Retrieves detailed ATS evaluation report by ID |
| `GET` | `/api/v1/ats/reports` | Lists ATS evaluation reports with optional filtering |

### Authentication & Account Security (Stage 7)
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Registers candidate account with PBKDF2-HMAC-SHA256 password hashing and returns JWT token |
| `POST` | `/api/v1/auth/login` | Authenticates candidate credentials and returns signed HS256 JWT access token |
| `GET` | `/api/v1/auth/me` | Retrieves profile of currently authenticated candidate |

---

## Stage 4 — Job Description Intelligence Details

### Ingestion & Parsing Workflow
1. **Input**: Plain-text or pasted job descriptions submitted via `POST /api/v1/jobs/analyze` or `POST /api/v1/jobs`.
2. **Metadata Extraction**: Identifies Job Title, Company, Location (Remote/Hybrid/Onsite), Seniority Level (Junior, Senior, Lead, etc.), and Employment Type.
3. **Requirement Classification**:
   - **Mandatory Requirements**: Items under required headings or containing explicit markers (`must have`, `required`, `essential`, `minimum of`).
   - **Preferred Requirements**: Items under preferred headings or containing bonus markers (`nice to have`, `is a plus`, `preferred`, `bonus`).
   - **Responsibilities**: Action-oriented role duties (`What you'll do`, `Responsibilities`).
   - **Experience Limits**: Extracts minimum and maximum required years (e.g., `5+ years`, `3-5 years`).
   - **Education & Certifications**: Identifies degree levels (Bachelor's, Master's, Ph.D.) and recognized certifications (AWS, CKA, PMP, CISSP).
4. **Skill Normalization & Taxonomy**:
   - Resolves aliases to canonical names (`k8s` → `Kubernetes`, `postgres` → `PostgreSQL`, `py` → `Python`, `reactjs` → `React`, `rest api` → `REST APIs`).
   - Preserves strict technological boundaries (Java ≠ JavaScript, React ≠ Angular, AWS ≠ Azure, SQL ≠ PostgreSQL).
5. **Quality Warnings**: Detects missing job titles, unusually short/vague job descriptions (< 40 words), duplicate requirements, and contradictory experience requirements (e.g. Junior role asking for 8+ years).

---

## Stage 5 — Evidence-Based Skill Matching Engine Details

### Matching Methodology
A candidate **never** receives credit for a skill merely because it appears in a job description. Every credit must be grounded in direct evidence from Stage 3 candidate profiles.

### Skill Matching Classifications
- `STRONG_MATCH`: Direct, credible evidence in candidate skills (verified in profile, or explicitly documented in work experience/certifications).
- `PARTIAL_MATCH`: Skill mentioned in work experience descriptions without a standalone skill record or with short duration (< 1 year).
- `RELATED_MATCH`: Candidate possesses a transferable, related skill from our taxonomy graph (e.g. Job requires `FastAPI`; candidate has `Python` and `Flask`). Related matches receive partial credit (0.35x strength) and never satisfy an exact mandatory requirement fully.
- `NO_EVIDENCE`: Skill not demonstrated in the available candidate profile. Reason: *"Not demonstrated in the available profile."* (Does not assert candidate lacks the ability in life).
- `CONFLICTED_EVIDENCE`: Unresolved profile conflicts (e.g. date overlap or contradictory claim) affect the skill assessment; credit is discounted.
- `NOT_ASSESSED`: Requirement cannot be evaluated using available data.

### Experience Matching
- Computes non-overlapping calendar duration from work experience dates, preventing double-counting of concurrent or overlapping positions (e.g., 2020-2022 and 2021-2023 = 3.0 years total, not 4.0 years).
- Evaluates relevant experience against job `min_years_experience`.

### Education & Certification Matching
- Academic degree hierarchy evaluation: Doctorate (4) > Master's (3) > Bachelor's (2) > Associate (1).
- Professional certifications must be directly verified in candidate records; certifications are never inferred merely because a tool was used.

### Scoring Model & Weights
The scoring engine uses configurable weights with defensible defaults:

| Dimension | Default Weight | Description |
| :--- | :---: | :--- |
| **Mandatory Skills** | **40%** | Demonstrated proficiency in non-negotiable job requirements |
| **Relevant Experience** | **20%** | Total non-overlapping relevant calendar experience |
| **Preferred Skills** | **15%** | Desirable skills, bonus qualifications, and transferable skills |
| **Education** | **10%** | Degree level and academic specialization alignment |
| **Domain Alignment** | **10%** | Inferred from mandatory skill coverage and experience relevance |
| **Certifications** | **5%** | Verified professional certifications |
| **Total** | **100%** | |

### Penalty & Conflict Controls
- **Missing Mandatory Skills Penalty**: Missing mandatory skills result in a progressive deduction (up to -25.0%). If a candidate possesses zero mandatory skills, the overall score is strictly capped at 25.0%.
- **Conflict Impact**: Unresolved chronology or credential conflicts incur an immediate 8.0% deduction.
- **Evidence Coverage**: Computes the proportion of job requirements backed by verified profile data.

> [!IMPORTANT]
> **Scoring Disclaimer**:
> The match score is a platform-generated alignment indicator based strictly on documented evidence in the candidate profile. It is **not** a hiring guarantee, hiring probability, or prediction of employment success.

---

## Running Tests

Execute the full regression test suite (70 tests across Stages 1–5):

```bash
pytest -v
```

## License

Provisional recommendation: **MIT License**. Final license decision pending owner confirmation.
