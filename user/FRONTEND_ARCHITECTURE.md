# Candidate Platform — Frontend Architecture
## AI Resume Intelligence Platform

---

## 1. Technology Stack & Key Libraries

- **Framework**: React 19 (TypeScript)
- **Tooling & Bundler**: Vite 6+ (Pure ESM build configuration)
- **Styling**: Tailwind CSS v3.4 + PostCSS + Autoprefixer
- **Icons**: Lucide React
- **Routing**: React Router DOM v7 (Data Router ready, client-side route guards)
- **Utility Classes**: `clsx` + `tailwind-merge` (via `cn()` helper)

---

## 2. Directory Structure & Component Tree

```
user/frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppLayout.tsx       # Sidebar navigation, live API status badge, user avatar, outlet
│   │   └── ui/                     # Design System Reusable Primitives
│   │       ├── Badge.tsx           # Status indicators (neutral, success, warning, error, brand)
│   │       ├── Button.tsx          # 5 variants (primary, secondary, outline, danger, ghost), loading spinners
│   │       ├── Card.tsx            # Structural card containers with headers and footers
│   │       ├── Input.tsx           # Form inputs with labels, helper text, and validation states
│   │       └── Modal.tsx           # Accessible modal dialog with backdrop blur & Escape key listener
│   │
│   ├── context/
│   │   └── AuthContext.tsx         # JWT token management, user profile state, session persistence
│   │
│   ├── lib/
│   │   └── utils.ts                # Class merging utility `cn()`
│   │
│   ├── pages/                      # Feature Workspaces
│   │   ├── Dashboard.tsx           # 12-stage stepper, dynamic recommendation, KPI metrics, activity stream
│   │   ├── Resumes.tsx             # Dropzone, search, status filters, dual-panel preview & warning viewer
│   │   ├── Profile.tsx             # Master career tabs, conflict resolver, approval header, entity CRUD
│   │   ├── Jobs.tsx                # Paste text / file upload (.pdf, .docx, .txt, .md), requirement inspection
│   │   ├── Matching.tsx            # 6-dimension fit radar, evidence citations, stale invalidation banner
│   │   ├── Generation.tsx          # Single-page A4 layout wizard, provenance inspector, version diffs
│   │   ├── AtsEvaluation.tsx       # 7 transparent gauges, anti-stuffing detector, "Improve in Builder" loop
│   │   ├── Applications.tsx        # 8-stage Kanban board, resume linking, multi-round interview tracker
│   │   ├── Settings.tsx            # Name edit, password change, JSON career data export, account deletion
│   │   ├── Login.tsx               # Candidate login with sliding-window rate limit defense
│   │   ├── Register.tsx            # Candidate registration with instant JWT session initialization
│   │   └── ForgotPassword.tsx      # Multi-step token password reset workflow
│   │
│   ├── services/
│   │   └── api.ts                  # Centralized typed API service with Bearer token injection
│   │
│   ├── App.tsx                     # Route tree configuration & ProtectedRoute authorization guard
│   └── main.tsx                    # React DOM entrypoint
```

---

## 3. Core Architectural Patterns

### 3.1 Centralized Typed API Client (`src/services/api.ts`)
All interactions with the backend are encapsulated within the singleton `api` service:
- **Bearer Token Injection**: Automatically pulls the current `auth_token` from `localStorage` and appends `Authorization: Bearer <token>` to request headers.
- **Unified Error Handling**: Unpacks FastAPI standard error details (`{ detail: string }`) and throws descriptive JavaScript `Error` instances.
- **Resource Namespaces**:
  - `api.auth.*`: login, register, me, updateName, changePassword, logout, deleteAccount, exportData.
  - `api.workflow.*`: status, activity.
  - `api.resumes.*`: upload, list, get, getText, download, reprocess, delete.
  - `api.profiles.*`: list, get, consolidate, update, approve, resolveConflict, entity CRUD.
  - `api.jobs.*`: analyze, upload, create, list, get, update, delete.
  - `api.matches.*`: compute, list, get.
  - `api.generation.*`: generate, list, get, downloadUrl, versions, delete.
  - `api.ats.*`: evaluate, reports, getReport.
  - `api.applications.*`: create, list, get, update, delete.

### 3.2 Dynamic Workflow & Action Recommendation Engine (`Dashboard.tsx`)
Rather than relying on static placeholders, the Dashboard queries `api.workflow.status()` on mount:
- **12-Stage Visual Stepper**: Displays each lifecycle stage with real-time status badges (`completed` in emerald, `in_progress` in blue, `needs_attention` in amber, `not_started` in slate, `blocked` in red).
- **Interactive Action Links**: Each stage features a direct action button routing the candidate directly to the corresponding workspace.
- **Dynamic Recommended Next Action Card**: Prominently highlights the highest-priority action calculated by the backend (e.g., "Approve Master Profile" or "Run ATS Evaluation") with explanatory rationale.
- **Real Activity Stream**: Live feed displaying immutable candidate audit events (`api.workflow.activity()`).

### 3.3 Reactive Stale Match Handling (`Matching.tsx`)
- When `matchResult.is_stale === true`, `Matching.tsx` renders an amber alert banner informing the candidate that upstream profile or job data has changed (`matchResult.stale_reason`).
- Provides a one-click **"Recompute Match"** button that immediately calls `api.matches.compute()`, refreshing scores and clearing the stale flag.

### 3.4 Closed-Loop ATS Optimization (`AtsEvaluation.tsx`)
- After running a 7-dimension ATS audit, candidates can click **"Improve Resume in Builder"**.
- This navigates the candidate directly to `/generation?job_id=...&resume_id=...&from_ats=true`, preloading the target job and candidate profile so the candidate can immediately apply ATS recommendations to produce an improved version.

### 3.5 8-Stage Kanban Application Tracker (`Applications.tsx`)
- Tracks candidates across all 8 pipeline stages: `INTERESTED`, `PREPARING`, `APPLIED`, `ASSESSMENT`, `INTERVIEW`, `OFFER`, `REJECTED`, `WITHDRAWN`.
- Allows linking target jobs and tailored resume versions directly on application cards.
- Provides a direct resume download button right on the Kanban card.

---

## 4. Design System Tokens & Accessibility

- **Color Palette**:
  - Brand Primary: Sky/Slate Blue (`#0284c7`, `#0369a1`)
  - Dark Slate Neutral: `#0f172a`, `#1e293b`, `#334155`, `#64748b`
  - Canvas Backgrounds: `#f8fafc`, `#ffffff`
  - Semantics: Emerald (`#10b981`), Amber (`#f59e0b`), Rose/Red (`#ef4444`)
- **Typography**: Clean system sans-serif hierarchy (`system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`).
- **Accessibility & Focus States**:
  - Form fields include explicit `label` elements, visible `:focus-visible` rings with brand offset, and ARIA attributes.
  - Modals trap focus and listen for `Escape` keypress events to close safely.
- **Responsive Layout**: Fluid CSS Grid and Flexbox structures adapt seamlessly across mobile (single-column stack) and desktop (persistent sidebar and multi-column workspaces).
