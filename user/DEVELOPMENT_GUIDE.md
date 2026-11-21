# Candidate Platform — Development & Operations Guide
## AI Resume Intelligence Platform

---

## 1. Prerequisites & Tooling

Before running the application locally, ensure your development environment meets the following requirements:

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version 3.11+ (Python 3.13.14 verified) accessible via system `PATH`.
- **Node.js**: Version 18+ (Node.js 20+ or 24+ verified) accessible via system `PATH`.
- **Package Managers**: `pip` (Python) and `npm` (Node).

---

## 2. Local Environment Setup

### 2.1 Backend Setup (`user/backend`)

1. Open PowerShell / Terminal and navigate to the backend directory:
   ```powershell
   cd C:\Coding\Projects\AI-RESUME-AGENT\user\backend
   ```
2. Verify Python version:
   ```powershell
   python --version
   ```
3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```
4. Verify directory layout:
   The backend will automatically initialize storage directories (`storage/uploads`, `storage/jobs`, `storage/generated_resumes`) and the SQLite database (`resume_agent.db`) on first startup.
5. Start the FastAPI development server with auto-reload:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
6. **Verify Backend Health**:
   - Health endpoint: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
   - Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 2.2 Frontend Setup (`user/frontend`)

1. Open a second PowerShell / Terminal window and navigate to the frontend directory:
   ```powershell
   cd C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
   ```
2. Verify Node.js and npm versions:
   ```powershell
   node -v
   npm -v
   ```
3. Install frontend dependencies:
   ```powershell
   npm install
   ```
4. Start the Vite development server:
   ```powershell
   npm run dev
   ```
5. **Access Application**:
   Open your browser to [http://localhost:5173](http://localhost:5173). The Vite dev server proxies or communicates directly with the FastAPI backend at `http://127.0.0.1:8000`.

---

## 3. Configuration & Environment Variables

Default configuration values are defined in `app/core/config.py` and can be overridden via environment variables or a `.env` file in `user/backend/`:

| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `AI Resume Intelligence Platform` | Name of the platform |
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `production`, `test`) |
| `DEBUG` | `True` | Enable debug mode and detailed logs |
| `SECRET_KEY` | *(auto-generated or configured string)* | Secret key for JWT signing (HMAC-SHA256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | JWT session lifetime |
| `DATABASE_URL` | `sqlite:///./resume_agent.db` | SQLAlchemy database connection URI |
| `UPLOAD_DIR` | `./storage/uploads` | Directory for raw resume uploads |
| `JOBS_DIR` | `./storage/jobs` | Directory for job description files |
| `GENERATED_RESUMES_DIR` | `./storage/generated_resumes`| Directory for generated PDF/DOCX files |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum allowed file upload size |

> [!NOTE]
> To use PostgreSQL instead of SQLite, set `DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/resume_agent`.

---

## 4. Running Automated Tests

### 4.1 Backend Test Suite (Pytest)

All tests are located in `user/backend/tests/`.

To run the complete test suite:
```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\backend
python -m pytest tests -q
```
*(Expected: 104 passed in ~17 seconds)*

To run specific test categories:
```powershell
# Candidate End-to-End Journey
python -m pytest tests/test_candidate_e2e_journey.py -v

# Dynamic Workflow & Stale State Management
python -m pytest tests/test_workflow.py -v

# Resume Generation & Single-Page A4 Quality
python -m pytest tests/test_resume_quality.py -v

# Application Tracker & Kanban Pipeline
python -m pytest tests/test_applications.py -v

# Security & Tenant Isolation
python -m pytest tests/test_security_isolation.py tests/test_security_headers.py -v
```

> [!IMPORTANT]
> On Windows machines running inside restricted sandbox environments, run pytest commands with sandboxing bypassed (`BypassSandbox: true`) to avoid Windows AppContainer file locking or socket handle hangs.

### 4.2 Frontend Typechecking & Production Build

To verify TypeScript typing and build the static production distribution:
```powershell
cd C:\Coding\Projects\AI-RESUME-AGENT\user\frontend
npm run build
```
*(Expected: Clean compilation with 0 errors in ~1.4 seconds)*

---

## 5. Development Conventions & Guidelines

1. **Ponytail v5.3.3 Full Mode**:
   Write the minimum necessary code to fully solve each task. Avoid speculative abstractions, unnecessary dependency layers, or duplicated logic.
2. **Strict Zero-Hallucination Invariant**:
   Never generate or synthesize candidate credentials that do not exist in the candidate's approved profile.
3. **Database Integrity & Foreign Keys**:
   Always declare foreign keys with appropriate cascade options (`CASCADE` or `SET NULL`). Always verify multi-tenant isolation by filtering queries with `user_id == current_user.id`.
4. **Physical File Discipline**:
   Whenever a database record representing a file is deleted (`ResumeDocument`, `GeneratedResume`), explicitly unlink the underlying physical file from disk.
5. **No Direct Git Operations**:
   Per project policy, do not execute git commands.
