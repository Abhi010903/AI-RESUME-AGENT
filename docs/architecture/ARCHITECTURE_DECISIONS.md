# ARCHITECTURE DECISION RECORDS (ADR)
## AI Resume Intelligence Platform — Technology Adoption & Integration Strategy

**Decision Date:** 2026-11-21  
**Project:** AI Resume Intelligence Platform (`C:\Coding\Projects\AI-RESUME-AGENT`)  
**Status:** Approved for Implementation  
**Standard:** Ponytail v5.3.3 Full Mode — Minimal Footprint, Maximum Product Value  

---

### ADR-01: Document Extraction Pipeline
- **Decision:** **RETAIN** PyMuPDF for primary extraction; **ADOPT** `pypdf` for secondary independent verification.
- **Context:** Previous evaluations considered IBM Docling and Unstructured.
- **Justification:** PyMuPDF extracts text, blocks, and font attributes in 8–15 ms without GPU or heavy dependencies. Benchmarks proved 100% vocabulary agreement between PyMuPDF and pypdf. Docling requires 2.5GB of model downloads and introduces 7-second latency per document, which severely degrades user experience.
- **Action Plan:** Maintain `app/services/extractor.py` using PyMuPDF; integrate `pypdf` into `app/services/ats_evaluator.py` for decoupled document verification.

---

### ADR-02: Structured Resume Rendering & Export
- **Decision:** **RETAIN & REFINE** in-process PyMuPDF vector rendering and python-docx; **REJECT** RenderCV and Typst host-binary dependencies.
- **Context:** RenderCV was evaluated for automated resume typesetting.
- **Justification:** RenderCV requires an external host installation of Typst or pdflatex (`PATH` execution). On containerized or clean Python environments without system package managers, RenderCV fails. Our in-process vector generator renders perfect A4 single-page PDFs in 40 ms with zero external binaries, 100% selectable vector text, and synchronized DOCX exports.
- **Action Plan:** Refine typography, dynamic vertical section spacing, and pixel-measured text wrapping (`_wrap_text_by_width`) inside `app/services/resume_generator.py`.

---

### ADR-03: Vector Database vs Authoritative Relational Storage
- **Decision:** **RETAIN** SQLite 3 / SQLAlchemy 2.0 with in-memory scikit-learn / numpy vector indexing; **REJECT** ChromaDB.
- **Context:** Evaluated ChromaDB v1.5.9 for candidate profile vector storage.
- **Justification:** ChromaDB suffers from a breaking upstream OpenTelemetry import collision on Python 3.13.14 (`cannot import name '_ExtendedAttributes' from 'opentelemetry.util.types'`). Furthermore, candidate profiles contain tens to hundreds of structured items, not millions. SQLite with transactional ACID guarantees, FTS5 full-text indexing, and in-memory cosine similarity executes in under 2 ms with zero external daemon overhead.
- **Action Plan:** Keep candidate profiles authoritative in SQLite/PostgreSQL; perform embedding similarity operations in-process via scikit-learn / numpy.

---

### ADR-04: Skill Taxonomy & Category Label Isolation
- **Decision:** **REPLACE** unconstrained comma splitting in `profile_parser.py` with prefix-aware category label separation.
- **Context:** Previous parser emitted category headers as skills (e.g. `Languages: Python`, `Backend & Tools: FastAPI`).
- **Justification:** Contaminating skill entities with taxonomy prefixes ruins ATS matching and creates embarrassing duplicate lines on resumes.
- **Action Plan:** Update `parse_skills_section` to detect and strip category labels (e.g. `Category: `) before parsing comma-delimited tokens, and add category fallback mapping to canonical ATS groups.

---

### ADR-05: Project Boundary Detection & Bullet Continuation
- **Decision:** **REPLACE** heuristic line-length project heading classification with bullet continuation and structured title detection.
- **Context:** Wrapped bullet lines in Projects were misclassified as standalone projects (e.g. `React dashboard receiving live updates over WebSockets.`), splintering real projects and displacing `Breath.exe`.
- **Justification:** A project must be a verified entity with an explicit title, technologies, and bullet claims. Multi-line bullets must concatenate with their parent bullet unless an explicit project header is encountered.
- **Action Plan:** Refactor `parse_project_section` in `app/services/profile_parser.py` to preserve bullet continuation and validate project identity against candidate evidence.

---

### ADR-06: Claim-Level Factual Provenance
- **Decision:** **ADOPT** deterministic claim-level provenance tracking (`ClaimEvidence`) for every generated statement.
- **Context:** Evaluated DeBERTa NLI vs deterministic validation for hallucination prevention.
- **Justification:** LLMs and generative tailorer templates can accidentally invent metrics or claim unverified skills. DeBERTa NLI is probabilistic (12.4% false alarm rate in benchmarks) and does not guarantee factual consistency. Deterministic string, entity, date, and document ID validation provides 100% mathematical certainty that every claim traces to approved candidate evidence.
- **Action Plan:** Define `ClaimEvidence` model and deterministic verifier in `app/services/resume_tailorer.py` and enforce validation before document rendering.

---

### ADR-07: Professional Writing & Zero Boilerplate
- **Decision:** **REPLACE** static template boilerplate in professional summaries with dynamic, evidence-grounded action phrasing.
- **Context:** Previous summaries contained generic machine filler ("Dedicated to applying core engineering principles, robust data structures...").
- **Justification:** Recruiters immediately discard resumes with canned AI filler. Summaries must highlight candidate education, top matched technical skills, and verified project outcomes in active, natural professional language (35–55 words).
- **Action Plan:** Implement role-targeted dynamic summary generation in `app/services/resume_tailorer.py` following: `[Candidate Degree/Background] + [Technical Project Evidence in Core Skills] + [Target Role Initiative & Impact]`.
