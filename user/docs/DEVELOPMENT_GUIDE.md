# Development Guide — AI Resume Agent

## 1. Prerequisites
- **Node.js**: Node 26 (recommended via `.nvmrc`).
- **Package Manager**: pnpm (v12.x or matching root `packageManager`).
- **Docker**: Docker Desktop (WSL2 engine on Windows) for local PostgreSQL, Redis, and SeaweedFS.

---

## 2. Environment Setup

1. The development environment requires `.env` in `user/`. Default development configuration:
   ```env
   PORT="3000"
   SERVER_PORT="3001"
   APP_URL="http://localhost:3000"
   DATABASE_URL="postgresql://resume_agent:resume_agent_secret@127.0.0.1:5432/resume_agent"
   STORAGE_BACKEND="local"
   LOCAL_STORAGE_PATH="./data"
   AUTH_SECRET="a1-resume-agent-auth-secret-key-development-32-chars-min"
   FLAG_ENABLE_GUEST_LOGIN="true"
   ```

2. If custom local overrides are needed, create `.env.local`. Dotenvx automatically loads `.env.local` first and falls back to `.env` (`-f .env.local -f .env`).

---

## 3. Development Startup & Orchestration

### A. The Single-Command Workflow
To start all application services in development:

```sh
# Step 1: Start Docker infrastructure (PostgreSQL, Redis, SeaweedFS)
docker compose -f compose.dev.yml up -d

# Step 2: Start the monorepo dev processes
pnpm dev
```

### B. Service Port Map
| Service | URL | Role |
| :--- | :--- | :--- |
| **Web Application** | `http://localhost:3000` | Vite+ React 19 Frontend |
| **Backend API** | `http://localhost:3001` | Hono Server, oRPC, Better Auth |
| **Health Check** | `http://localhost:3001/api/health` | PostgreSQL, Redis & Storage status |
| **Email Preview** | `http://localhost:3002` | React Email template development |
| **PostgreSQL** | `localhost:5432` | Primary database (`resume_agent`) |
| **Redis** | `localhost:6379` | Session caching & rate limiting |
| **SeaweedFS** | `localhost:8333` | S3-compatible document storage |

---

## 4. Development Stability & Orchestration Diagnosis

### The Issue Previously Encountered
When running `pnpm dev`, developers previously encountered `ECONNREFUSED` and `502 Bad Gateway` errors on frontend requests (e.g., `/api/auth/get-session`, `/api/rpc/flags/get`), while running backend (`pnpm --filter server dev`) and frontend (`pnpm --filter web dev`) in separate terminals appeared to succeed.

### Root Cause Analysis
1. **Asynchronous Startup Racing**:
   - `apps/web` (Vite) initializes and binds to port 3000 in under 500ms.
   - `apps/server` (Node/Hono) executes a sequence of essential startup checks before opening port 3001:
     1. Database connectivity check
     2. Drizzle SQL migration execution (`runDatabaseMigrations()`)
     3. Local storage path validation
     4. Better Auth initialization
   - If PostgreSQL is down, unreachable, or rejects authentication credentials:
     - `apps/server` throws an unhandled connection error and exits immediately (`process.exit(1)`).
     - `apps/web` remains alive on port 3000.
     - Browser requests to `http://localhost:3000` trigger Vite proxy forward to `http://localhost:3001`.
     - Because the backend crashed before opening port 3001, Vite's proxy receives `ECONNREFUSED` and returns `502 Bad Gateway`.

2. **Environment Ingestion**:
   - Root `package.json` previously invoked `dotenvx run -f .env.local`. When `.env.local` was absent, 0 environment variables were injected, causing fallback to unconfigured defaults.
   - Fixed by adding explicit fallback: `-f .env.local -f .env`.

3. **Database Credential Alignment**:
   - The PostgreSQL Docker container was previously created with credentials `postgres:postgres`, whereas `.env` specified `resume_agent:resume_agent_secret`.
   - Fixed by provisioning the `resume_agent` role with `CREATEDB` privileges and updating `compose.dev.yml` to match `.env`.

### Prevention & Recovery Checklist
- Always verify Docker services before running `pnpm dev`:
  ```powershell
  docker compose -f compose.dev.yml ps
  ```
- If the backend fails to start, verify connectivity directly:
  ```powershell
  Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
  ```

---

## 5. Standard Verification Commands

```sh
# Typecheck all 21 packages
pnpm typecheck

# Verify Turbo package boundaries (zero violations required)
pnpm exec turbo boundaries

# Extract translation keys across web and mobile
pnpm lingui:extract

# Apply database migrations
pnpm db:migrate

# Run fast agent lint check
pnpm lint:agent
```
