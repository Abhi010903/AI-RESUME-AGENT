# Candidate Platform — Manual Testing & Evaluation Guide
## AI Resume Intelligence Platform

This guide provides end-to-end instructions for launching, navigating, and evaluating the Candidate Platform locally.

---

## 1. Prerequisites & Environment Setup

Ensure the following runtimes are installed on your workstation:
- **Python**: Version 3.11+ (Python 3.13+ verified) accessible on system `PATH` (`python --version`)
- **Node.js**: Version 18+ (Node.js 20+ or 24+ verified) accessible on system `PATH` (`node -v`)
- **NPM**: Version 9+ accessible on system `PATH` (`npm -v`)
- **OS**: Windows (PowerShell), macOS, or Linux

---

## 2. Launching the Services

Open **two separate PowerShell / Terminal windows** in the project root: `C:\Coding\Projects\AI-RESUME-AGENT`.

### Terminal 1: Candidate Backend (FastAPI)

```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Specification**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Terminal 2: Candidate Frontend (Vite + React)

```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
npm run dev
```

- **Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 3. End-to-End Candidate Evaluation Checklist

Follow this sequence to test all platform features and cross-module workflows:

### Step 1: Candidate Registration & Authentication
1. Navigate to [http://localhost:5173](http://localhost:5173). You will automatically be routed to `/login`.
2. Click **"Create candidate account"** to open `/register`.
3. Fill in:
   - **Full Name**: `Jane Candidate`
   - **Email**: `jane@example.com`
   - **Password**: `SecurePass123!`
4. Click **Create Account**.
5. You will immediately be authenticated and redirected to the **Dashboard** (`/`).
6. Notice the candidate avatar, legal name, and green **API Connected** live status indicator in the top navigation bar.

### Step 2: Dashboard & 12-Stage Lifecycle Progress Tracker
1. Observe the **12-Stage Lifecycle Progress Stepper**:
   - Stage 1 (Account & Authentication) displays a green `Completed` badge.
   - Stage 2 (Upload Resumes) displays an active action button: **"Upload Resume"**.
2. Notice the **Recommended Next Action** card:
   - Prominently advises: *"Upload your existing PDF or DOCX resumes to extract career facts."*
   - Features a high-priority action button routing directly to `/resumes`.
3. Notice the live **Activity Stream** at the bottom displaying your recent account registration event.

### Step 3: Multi-Resume Ingestion & Extraction
1. Click **"Resumes & Ingestion"** (`/resumes`) in the sidebar.
2. In the upload card:
   - Drag and drop or browse to upload 1 or 2 sample PDF or DOCX resumes.
3. Observe the live table populating:
   - Filename, format badge (`PDF` / `DOCX`), file size, extraction status (`completed`), and page count.
4. Test document preview:
   - Click the **Eye icon** on a resume row to open the **Extracted Text Preview Modal**.
   - Verify the **Extracted Text** tab displays clean parsed text.
   - Verify the **Extraction Warnings** tab displays parsing observations.
5. Click the **Download icon** to verify the original file downloads cleanly.
6. Click the **Refresh icon** to test the on-demand extraction reprocessing pipeline.
7. Select the checkbox next to your uploaded resume(s). A blue button labeled **"Consolidate N Resume(s) into Profile"** appears at the top right.
8. Click **Consolidate**. You will be redirected to `/profile`.

### Step 4: Candidate Profile Intelligence & Conflict Resolution
1. On the **Candidate Profile** page (`/profile`):
   - Notice the candidate header card displaying the consolidated Name, Headline, Contact Info, Completeness Gauge, and Verification Status (`Draft`).
2. Test entity management across tabs:
   - **Work Experience tab**: Click **"Add Experience"** to create a role with job title, company, dates, and skills used. Test deleting or updating entries.
   - **Academic Qualifications tab**: View extracted degrees or click **"Add Education"** to record an academic credential.
   - **Technical Skills tab**: View skills categorized by domain. Click **"Add Skill"** to add a technical skill.
   - **Certifications tab**: Add or view professional certifications.
   - **Portfolio Projects tab**: Add portfolio projects with technology tags.
3. **Conflicts & Audit tab**:
   - Inspect any detected cross-document discrepancies.
   - Click **"Resolve"** on a conflict, enter a resolution note, and click **"Save Resolution"**.
4. In the profile header, click **"Approve Profile"**:
   - Notice the verification badge updates to **Approved** with a checkmark.
   - The profile is now locked in as the authoritative master source of truth.

### Step 5: Target Job Intelligence
1. Click **"Target Jobs"** (`/jobs`) in the sidebar.
2. Click **"Add Target Job"**.
3. Choose either:
   - **Option A (Paste JD Text)**: Paste an unstructured job posting (e.g. Senior AI Engineer role).
   - **Option B (Upload Document)**: Upload a `.pdf`, `.docx`, `.txt`, or `.md` file containing a job description.
4. Click **"Analyze & Extract"**.
5. The job card appears showing:
   - Role Title, Seniority badge, Company, Location, Summary, and counts of Mandatory & Preferred requirements.
6. Click **"Inspect Requirements"** to view extracted mandatory skills, preferred skills, core responsibilities, and eligibility constraints.

### Step 6: Evidence-Based Skill Matching Engine
1. Click **"Skill Match Engine"** (`/matching`) in the sidebar.
2. Select your **Candidate Profile** and **Target Job** from the dropdowns.
3. Click **"Compute Evidence Match"**.
4. Review the matching output:
   - **Overall Match Gauge**: Percentage fit based on candidate profile evidence.
   - **6 Dimension Breakdown**: Mandatory Skills, Preferred Skills, Experience Alignment, Education Alignment, Domain Fit, and Certifications.
   - **Requirements & Evidence Table**: Every requirement shows matched status and exact evidence citations extracted from your profile.
   - **Identified Competency Gaps**: Lists missing skills with honest, actionable advice (no fabrication).
5. Click **"Tailor Resume with this Match"** to transition directly to the Resume Builder.

### Step 7: Reactive Stale Match Invalidation Test
1. Return to **Candidate Profile** (`/profile`).
2. In the **Technical Skills** tab, click **"Add Skill"** and add a new skill (e.g. `Kubernetes`).
3. Return to **Skill Match Engine** (`/matching`).
4. **Verify Reactive Invalidation**:
   - An amber alert banner appears reading:
     > **"Match Outdated"**: Candidate profile updated. Please recompute match to reflect latest changes.
5. Click **"Recompute Match"**:
   - The match engine recalculates scores and the amber banner clears.

### Step 8: Tailored Single-Page A4 Resume Builder
1. Navigate to **Resume Builder** (`/generation`).
2. Enter an optional title (e.g. `Senior AI Engineer - TechCorp`).
3. Click **"Generate Single-Page Resume"**.
4. In the generated preview:
   - Inspect the clean typography and section hierarchy.
   - Note the calculated **ATS Score** and version number (`v1`).
5. **Download Verification**:
   - Click **"Download PDF"**: Open the PDF and verify it is **strictly 1 page**, standard A4 dimensions ($595.28 \times 841.89\text{ pt}$).
   - Click **"DOCX"**: Open the DOCX in Word or LibreOffice and verify formatting.
6. **Provenance Inspector**:
   - Click **"Provenance"** tab: verify that every bullet point links directly to source document claims (Zero-Hallucination verification).

### Step 9: Transparent 7-Dimension ATS Evaluation & Feedback Loop
1. Click **"ATS Evaluation"** (`/ats`) in the sidebar.
2. Select your newly generated resume and target job.
3. Click **"Run ATS Audit"**.
4. Review the 7-dimension score breakdown:
   - Mandatory Skills, Preferred Skills, Experience Alignment, Education Alignment, Keyword Relevance, Structure & Formatting, Readability.
5. Check the **Keyword Coverage** checklist and **Anti-Stuffing Indicator**.
6. **Closed-Loop Improvement Test**:
   - Click the green button: **"Improve Resume in Builder"**.
   - You are routed directly back to `/generation` with the target job and resume preloaded to tailor a version 2!

### Step 10: 8-Stage Kanban Application Tracker
1. Click **"Application Tracker"** (`/applications`) in the sidebar.
2. Click **"Track New Application"**.
3. Select your target job and linked tailored resume version. Fill in company, role, salary range, and applied date.
4. Click **"Save Application"**.
5. Observe the card appear in the Kanban board across the 8 stages:
   `INTERESTED` → `PREPARING` → `APPLIED` → `ASSESSMENT` → `INTERVIEW` → `OFFER` → `REJECTED` → `WITHDRAWN`.
6. Click the resume download button directly on the application card to confirm file access.
7. Click the card to open the **Interview Tracker** modal and log interview rounds.

### Step 11: Data Portability & Account Settings
1. Click **"Settings"** (`/settings`) in the sidebar.
2. Update your full legal name and click **"Save Name"**.
3. Under **Data Governance & Portability**:
   - Click **"Export Data (JSON)"**.
   - Verify that your complete career knowledge base downloads as a JSON archive.
4. Test logging out via the user footer in the sidebar to verify session invalidation.

---

## 4. Automated Test Commands

To verify automated test health from the terminal:

```powershell
# From C:\Coding\Projects\AI-RESUME-AGENT\user\backend
python -m pytest tests -q
```
**Expected Outcome**: **104 passed, 0 failed in ~17 seconds**.

To verify the frontend build:

```powershell
# From C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
npm run build
```
**Expected Outcome**: **Clean Vite production build with 0 errors in ~1.4 seconds**.
