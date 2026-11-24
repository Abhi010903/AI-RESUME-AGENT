# Backend Guide — AI Resume Agent

## 1. Overview
The backend application lives in `apps/server`. It runs a Hono application on Node.js using `@hono/node-server`.

## 2. Startup Sequence
The server startup sequence is orchestrated in [apps/server/src/index.ts](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/apps/server/src/index.ts):
1. **Startup Checks** ([apps/server/src/startup/checks.ts](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/apps/server/src/startup/checks.ts)):
   - Connects to PostgreSQL using advisory locks (`SELECT pg_advisory_lock(721830451)`).
   - Executes pending Drizzle migrations from `migrations/`.
   - Verifies schema integrity.
   - Validates storage directory permissions (`data/` when using local storage).
2. **App Creation** ([apps/server/src/http/app.ts](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/apps/server/src/http/app.ts)):
   - Registers route handlers:
     - `/api/auth/*`: Better Auth handler ([apps/server/src/http/auth.ts](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/apps/server/src/http/auth.ts)).
     - `/api/rpc/*`: oRPC handler ([apps/server/src/rpc/handler.ts](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/apps/server/src/rpc/handler.ts)).
     - `/api/health`: Healthcheck endpoint reporting DB, storage, and redis status.
     - `/mcp`: Model Context Protocol streamable HTTP handler.
3. **Schedulers**:
   - `startCareerScheduler`: Synchronizes job application updates.
   - `startStorageCleanupScheduler`: Cleans orphaned temporary upload files.
4. **Listener**: Listens on `http://localhost:3001` (`SERVER_PORT`).
