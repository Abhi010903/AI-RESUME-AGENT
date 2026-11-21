# Candidate Platform — User Workflow Guide
## Complete Non-Technical Candidate Walkthrough

Welcome to the **AI Resume Intelligence Platform**! This guide walks you step-by-step through the entire platform from creating your account to tracking your job applications.

---

## 1. Quick Start Overview

```
Step 1: Register / Login
   ↓
Step 2: Upload Existing Resumes (PDF / Word)
   ↓
Step 3: Review Extracted Information & Warnings
   ↓
Step 4: Consolidate Your Master Career Profile
   ↓
Step 5: Review & Resolve Any Discrepancies
   ↓
Step 6: Formally Approve Your Candidate Profile
   ↓
Step 7: Add a Target Job Description
   ↓
Step 8: Review Extracted Job Requirements
   ↓
Step 9: Run the Skill Match Engine
   ↓
Step 10: Review Match Evidence & Address Gaps
   ↓
Step 11: Generate a Polished Single-Page A4 Resume
   ↓
Step 12: Run ATS Audit & Track Job Application
```

---

## 2. Step-by-Step Workflow Guide

### Step 1: Create Your Account & Log In

1. Open your browser and navigate to `http://localhost:5173`.
2. You will be greeted by the **Login** screen.
3. If this is your first time, click **"Create candidate account"** at the bottom.
4. Enter:
   - **Full Name**: e.g., `Alex Morgan`
   - **Email Address**: e.g., `alex@example.com`
   - **Password**: Enter a secure password (at least 8 characters).
5. Click **"Create Account"**.
6. You will immediately be logged in and taken to your **Dashboard**.
7. In the top navigation bar, notice your avatar, name, and the green **"API Connected"** indicator confirming live communication with the server.

---

### Step 2: Upload Your Existing Resumes

1. Click **"Resumes & Ingestion"** in the left sidebar.
2. In the upload card at the top:
   - Drag and drop one or more of your existing resumes into the upload zone, or click **"Browse Files"**.
   - Supported formats: **PDF (`.pdf`)** and **Microsoft Word (`.docx`)** up to 10 MB.
3. As files are uploaded, you will see them appear in the **Uploaded Resumes** table with:
   - File name and format badge (`PDF` / `DOCX`).
   - File size.
   - Processing status badge (green `completed` when ready).
   - Extracted entity counts (skills, experiences, education).
4. If a file upload fails, check that the file is not password-protected and is a genuine PDF or DOCX document.

---

### Step 3: Review Extracted Information & Raw Text

1. In the **Uploaded Resumes** table, locate your uploaded resume.
2. Click the **Eye icon** (Preview) on that row.
3. A dual-panel modal will open:
   - **Extracted Text Tab**: Displays the clean raw text extracted from your document. Verify that your name, employers, job titles, and dates are present.
   - **Extraction Warnings Tab**: Displays any observations made by the parser (such as image-based pages, multi-column tables, or character encoding notes).
4. Click the **Download icon** if you wish to verify the original file, or the **Refresh icon** if you wish to re-parse the file.
5. Close the modal when satisfied.

---

### Step 4: Consolidate Your Master Career Profile

1. In the **Uploaded Resumes** table, check the box next to the resume(s) you wish to merge into your master profile.
2. When at least one resume is selected, a blue button labeled **"Consolidate N Resume(s) into Profile"** appears in the top right.
3. Click **"Consolidate"**.
4. The platform merges the extracted facts, deduplicates identical employment or education entries, and redirects you directly to your **Candidate Profile** (`/profile`).

---

### Step 5: Review & Resolve Discrepancies

1. On the **Candidate Profile** page, you will see your master career profile organized into tabs:
   - **Personal Info**: Full Name, Professional Headline, Email, Phone, Location, and Bio.
   - **Work Experience**: Past roles, company names, start/end dates, location, and key accomplishments.
   - **Academic Qualifications**: Degrees, institutions, fields of study, and graduation years.
   - **Technical Skills**: Grouped by category (Languages, Frameworks, Cloud, Databases).
   - **Certifications**: Professional licenses and certifications with credential IDs.
   - **Portfolio Projects**: Project titles, descriptions, and technology tags.
   - **Conflicts & Audit**: Discrepancies identified across multiple resumes.
2. Click on the **Conflicts & Audit** tab:
   - If you uploaded multiple resumes with differing dates or titles for the same employer, the system highlights them here.
   - For each conflict, you can inspect the sources, choose which version is correct, or enter a custom resolution note.
   - Click **"Save Resolution"** to resolve the item.
3. Review each tab and make any edits using the **"Add"** or **"Delete"** buttons to ensure your profile is 100% accurate.

---

### Step 6: Formally Approve Your Candidate Profile

1. Look at the top right header of the **Candidate Profile** workspace.
2. You will see your profile status badge (e.g. `Draft` or `Needs Review`) and a profile completeness gauge.
3. Click the green **"Approve Profile"** button.
4. The system validates that all required fields are complete and that no blocking conflicts remain.
5. Once approved:
   - The status badge changes to **"Approved"** with a checkmark.
   - This approved profile snapshot becomes the authoritative source of truth for all matching and resume tailoring.

> [!NOTE]
> If you make changes to your profile later, the status will return to `Draft`, and any existing match results will be marked as outdated until re-approved.

---

### Step 7: Add a Target Job Description

1. In the left sidebar, click **"Target Jobs"** (`/jobs`).
2. Click the **"Add Target Job"** button.
3. You have two convenient options:
   - **Option A (Paste Text)**: Copy the job description text from LinkedIn, Indeed, or a company career page and paste it into the text box.
   - **Option B (Upload File)**: Upload a `.pdf`, `.docx`, `.txt`, or `.md` file containing the job posting.
4. Click **"Analyze & Extract"**.
5. The system parses the job posting, extracting:
   - Role Title, Company, Seniority Level, and Location.
   - Summary and Department.
   - Counts of Mandatory vs. Preferred skills.

---

### Step 8: Review Extracted Job Requirements

1. On the **Target Jobs** page, locate your newly added job card.
2. Click **"Inspect Requirements"**.
3. A detailed drawer or modal displays:
   - **Mandatory Requirements**: Core technical skills and qualifications marked as required.
   - **Preferred Requirements**: Bonus skills and nice-to-have qualifications.
   - **Responsibilities**: Key daily duties and operational expectations.
   - **Eligibility & Restrictions**: Years of experience, location constraints, and clearance prerequisites.
4. If you need to edit or update the job posting, click **"Edit Job"** to refine any requirements.

---

### Step 9: Run the Skill Match Engine

1. In the left sidebar, click **"Skill Match Engine"** (`/matching`).
2. At the top of the page, select your **Candidate Profile** and your **Target Job** from the dropdown menus.
3. Click **"Compute Evidence Match"**.
4. Within moments, the matching engine calculates an alignment score based on real evidence in your profile:
   - **Overall Fit Gauge**: A clear percentage score representing requirement coverage.
   - **6 Dimension Breakdown Cards**:
     - Mandatory Skills Fit
     - Experience Alignment
     - Domain Knowledge
     - Preferred Skills Fit
     - Education Alignment
     - Certifications Match

---

### Step 10: Review Match Evidence & Address Gaps

1. Scroll down on the **Skill Match Engine** page:
2. **Requirements & Evidence Table**:
   - Every requirement from the job posting is listed alongside its status: `MATCHED`, `PARTIALLY_MATCHED`, or `MISSING`.
   - Click any requirement to see the exact evidence citations extracted from your work history and portfolio.
3. **Identified Competency Gaps**:
   - Review any missing mandatory or preferred qualifications.
   - Read the actionable recommendations provided for each gap. Notice that the platform never suggests lying or fabricating claims, but instead advises emphasizing related projects, self-study, or adjacent tools.
4. When ready, click **"Tailor Resume with this Match"** at the top right to transition directly to the Resume Builder.

---

### Step 11: Generate a Polished Single-Page A4 Resume

1. You are now in the **Resume Builder** workspace (`/generation`):
   - Your profile and target job are already pre-selected.
2. Optional Settings:
   - **Resume Title**: Customize the document title (e.g. `Senior AI Platform Engineer - TechCorp`).
   - **Tailoring Emphasis**: Choose whether to emphasize technical skills, project leadership, or architectural scope.
3. Click **"Generate Single-Page Resume"**.
4. The engine compiles your verified profile facts, optimizes the content hierarchy, and fits the document perfectly to standard A4 dimensions.
5. In the generated preview:
   - Review your formatted resume layout.
   - Note the **ATS Compatibility Score** and version badge (`v1`).
6. **Download Options**:
   - Click **"Download PDF"** to receive a vector PDF formatted strictly to 1 page A4 ($595.28 \times 841.89\text{ pt}$).
   - Click **"Download DOCX"** to receive an editable Microsoft Word document.
7. **Provenance Inspector**:
   - Click the **"Provenance"** tab to view the source audit trail proving that every single bullet point originated from your approved profile.

---

### Step 12: Run ATS Audit & Track Job Application

#### Running the ATS Audit
1. In the left sidebar, click **"ATS Evaluation"** (`/ats`).
2. Select your newly generated resume and target job.
3. Click **"Run ATS Audit"**.
4. The system scores your resume across 7 transparent dimensions:
   - Mandatory Skills, Preferred Skills, Experience Alignment, Education Alignment, Keyword Relevance, Structure & Formatting, and Readability.
5. Check the **Keyword Coverage** checklist to see which terms were successfully embedded.
6. Verify the **Anti-Stuffing Indicator** (confirms keywords are used naturally without repetitive stuffing).
7. If you want to make further improvements, click **"Improve Resume in Builder"**. This takes you right back to the Resume Builder with your recommendations in hand!

#### Tracking Your Application
1. In the left sidebar, click **"Application Tracker"** (`/applications`).
2. Click **"Track New Application"**.
3. Fill in the modal:
   - Select your Target Job and tailored Generated Resume.
   - Enter Company Name, Role Title, Job Board URL, and Salary Range.
   - Set Initial Status (e.g. `APPLIED`).
4. Click **"Save Application"**.
5. Your application appears on the **8-Stage Kanban Board**:
   - `INTERESTED` → `PREPARING` → `APPLIED` → `ASSESSMENT` → `INTERVIEW` → `OFFER` → `REJECTED` → `WITHDRAWN`.
6. Drag cards or click stage buttons to move your application forward as you progress.
7. Click any card to open the **Interview Tracker** to record dates, interviewer names, rounds, and personal notes.

---

## 3. Advanced Features & Data Management

### Stale Match Invalidation
If you edit your candidate profile (such as adding a new project or updating a job title) after having matched against a job, you will see an orange banner on the **Skill Match Engine** page reading:
> **"Match Outdated"**: Candidate profile updated. Please recompute match to reflect latest changes.

Click **"Recompute Match"** to update your score with zero fuss.

### Exporting Your Data
You own your career data. At any time:
1. Navigate to **Settings** (`/settings`) in the sidebar.
2. Scroll to the **Data Governance & Portability** card.
3. Click **"Export Data (JSON)"**.
4. A complete `.json` archive containing your user profile, resumes, verified work history, target jobs, match analyses, tailored resumes, and application tracker pipeline will download to your device.

---

## 4. Frequently Asked Questions (FAQ)

**Q: Can the AI resume generator add skills I haven't entered?**  
*A: No. The platform adheres to a strict Zero-Hallucination policy. Every bullet point and skill must be anchored in your approved profile.*

**Q: Why is my generated PDF strictly 1 page?**  
*A: Recruitment research shows that single-page resumes achieve higher review completion rates. The engine uses dynamic vertical spacing clamping to guarantee that content fits onto exactly 1 standard A4 sheet without spilling over.*

**Q: Can I re-use a generated resume for multiple applications?**  
*A: Yes! You can link any previously generated resume to multiple applications in the Application Tracker.*

**Q: What happens if I delete an uploaded resume?**  
*A: Deleting an uploaded resume deletes the source file from disk. Any claims already consolidated and approved in your master profile remain safely preserved.*
