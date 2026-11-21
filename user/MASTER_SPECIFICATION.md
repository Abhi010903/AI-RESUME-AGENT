# MASTER IMPLEMENTATION SPECIFICATION
## AI RESUME INTELLIGENCE PLATFORM
### Complete Candidate Application — Business Logic, Backend, Frontend, Integration, UX and Production Readiness

---

## 1. MISSION & GUIDING PRINCIPLES

- **Business Logic First**: Understand module relationships before modifying them.
- **Approved Candidate Profile as Central Source of Truth**: The approved profile is authoritative for matching, resume generation, and ATS evaluation. Extracted information is not automatically verified until confirmed/approved.
- **Cross-Module Reactive Consequences**: Every operation has consequences across the platform. E.g., changing a skill or resolving a conflict must invalidate outdated match results or mark them as stale.
- **Preserve Historical Records**: Snapshot generated resumes and ATS reports. Changing a profile must never silently rewrite an already-generated resume.
- **User Workflow Drives the UI**: The candidate should always know what they completed, what is in progress, what requires attention, what is blocked, and what to do next.
- **Real Production Criteria Beyond Passing Tests**: Verified E2E candidate journeys, tenant isolation, IDOR defense, file safety, and single-page A4 document aesthetics.
- **Strict Constraints**:
  - STRICT NO-GIT RULE: Absolutely no git commands or indirect git operations.
  - Zero deployment: Local development and manual testing only.
  - Scope: Work exclusively in `user/`. Do not touch `company/` or `legacy/`.
  - Ponytail v5.3.3 Full Mode: Minimum necessary code, clean abstractions, no bloat.

---

## 2. THE 12-STEP CANDIDATE LIFECYCLE

```
1. CREATE ACCOUNT / LOGIN
       ↓
2. UPLOAD RESUMES (PDF / DOCX)
       ↓
3. EXTRACT RESUME INFORMATION (Provenance preserved)
       ↓
4. CONSOLIDATE CANDIDATE PROFILE (Identify conflicts & duplicates)
       ↓
5. REVIEW & RESOLVE CONFLICTS / EDIT (Factual verification)
       ↓
6. APPROVE CANDIDATE PROFILE (Authoritative snapshot state)
       ↓
7. ADD TARGET JOB (Text paste or PDF/DOCX/TXT/MD upload)
       ↓
8. ANALYZE JOB REQUIREMENTS (Mandatory vs Preferred vs Eligibility)
       ↓
9. MATCH CANDIDATE AGAINST JOB (Transparent weights, evidence citations)
       ↓
10. IDENTIFY SKILL & EXPERIENCE GAPS (Actionable advice without hallucination)
       ↓
11. GENERATE TAILORED RESUME (Single-page A4 PDF & DOCX, provenance tags)
       ↓
12. EVALUATE ATS COMPATIBILITY & TRACK APPLICATION (7 dimensions, Kanban pipeline)
```

---

## 3. THE 9 CORE MODULES

### Module 1: Dashboard
- Welcome header with live authenticated user name, headline, current profile status, and primary recommended action.
- Profile summary metrics (completion %, uploaded resumes count, verified skills, projects, experiences, certifications, approval status).
- Workflow Progress Tracker (12 stages with real statuses: Not Started, In Progress, Needs Attention, Completed, Blocked, plus direct action buttons).
- Dynamic Workflow Recommendation Engine (state-based: no resumes -> upload; resumes but no profile -> consolidate; conflicts -> resolve; not approved -> review & approve; approved -> add job; job analyzed -> match; match exists -> generate; resume exists -> ATS evaluate; applied -> track).
- Recent activity stream (real audit events).
- Recent jobs, matches, generated resumes, and active applications with direct deep links.

### Module 2: Resumes & Ingestion
- Searchable/filterable library with status badges (Uploaded, Processing, Extracted, Failed), entity counts, file sizes.
- Drag-and-drop & file picker for PDF & DOCX with magic byte MIME validation, file signature check, path traversal prevention.
- Dual-panel preview modal: left side document viewer / text preview, right side extracted sections and structured entities with provenance tags.
- Reprocess capability (re-runs extraction, preserves original file, marks dependent drafts as stale).
- Delete with confirmation (preserves independently confirmed profile claims while flagging that original source doc is unlinked).

### Module 3: Candidate Profile Intelligence
- Unified career knowledge base: Overview, Personal Information, Education, Experience, Skills, Projects, Certifications, Achievements, Conflicts & Verification, Profile History.
- Consolidation Engine: Multi-document entity merging, normalization, duplicate detection, and source-document conflict detection.
- Detailed CRUD on all entity collections with verification flags (`extracted`, `candidate_confirmed`, `project_evidenced`, `experience_evidenced`).
- Side-by-side Conflict Resolution: Source A vs Source B vs manual override, with audit trail and completeness recalculation.
- Formal Profile Approval: Validates mandatory fields, checks unresolved conflicts, persists approval timestamp and version, invalidates stale downstream matches if re-edited.
- Historical version tracking.

### Module 4: Target Jobs / Job Description Intelligence
- Job library with search, filtering, and analysis status badges.
- Ingestion via raw text paste or multi-format upload (`.pdf`, `.docx`, `.txt`, `.md`).
- Multi-dimensional extraction: Mandatory skills, preferred skills, responsibilities, qualifications, education, experience, eligibility restrictions, compensation, location.
- Job Details page with structured requirements classification and confidence indicators.
- Stale match invalidation when job requirements are updated or reanalyzed.

### Module 5: Skill Match Engine
- Multi-dimensional evaluation: Mandatory skills, preferred skills, technical experience, project relevance, work experience relevance, education eligibility, domain knowledge, evidence strength.
- Requirement status: `MATCHED`, `PARTIALLY_MATCHED`, `MISSING`, `NEEDS_VERIFICATION`, `NOT_APPLICABLE`.
- Explainable score breakdown (internal requirement alignment, NOT a mysterious hiring probability).
- Evidence citations linking each requirement to candidate projects or work history.
- Honest Gap Analysis: Actionable suggestions without advising candidates to fabricate claims.
- Match persistence with algorithm version and profile/job snapshots.

### Module 6: Resume Builder / Generation
- Inputs: Approved profile snapshot + Analyzed job + Match results.
- Custom title, tailoring emphasis, section ordering.
- Strict Zero-Hallucination Policy: Only factually evidenced claims from approved profile; never invent skills, metrics, or employers.
- Dynamic single-page A4 layout optimizer (PyMuPDF & python-docx): 595.28 x 841.89 pt, margins, clean typography, guaranteed single-page fitting without silent data loss.
- Claim-level provenance inspector showing exact source document/project citations for every bullet.
- Version management: PDF & DOCX downloads, side-by-side visual/text diff comparison between versions, delete with physical file cleanup.

### Module 7: ATS Evaluation
- 7 transparent evaluation dimensions: Mandatory skills, preferred skills, keyword density/relevance, experience alignment, education alignment, structure/formatting, readability.
- Anti-stuffing warnings and actionable recommendations.
- "Improve Resume" workflow: Preloads recommendations back into Resume Builder for an iterative improvement loop while preserving previous version reports.

### Module 8: Application Tracker
- 8-stage Kanban board: `INTERESTED`, `PREPARING`, `APPLIED`, `ASSESSMENT`, `INTERVIEW`, `OFFER`, `REJECTED`, `WITHDRAWN`.
- Link job description, generated resume version, external URL, application date, notes, interview timeline.
- Interview stage tracker with dates, interviewers, notes, and outcomes.
- Timeline history tracking status transitions.

### Module 9: Settings & Account
- Personal information (Legal name, contact preferences).
- Security (Password change, password reset confirm, sliding-window rate limit protection).
- Privacy & Data Governance (Download data export, delete generated resumes, account deletion with full cascade).

---

## 4. CROSS-MODULE WORKFLOW ENGINE & STALE INVALIDATION RULES

1. **Profile Edit**: When approved profile is modified, its approval status reverts to `DRAFT` / `NEEDS_REVIEW`, and downstream match results are flagged `stale = True`.
2. **Job Reanalysis**: Downstream match results for this job are flagged `stale = True`.
3. **Resume Regeneration**: Creates a new immutable resume version; previous ATS reports remain tied to previous versions.
4. **Dynamic Next Action Service**: Backend service and frontend state compute the exact next recommended action based on real candidate state.
