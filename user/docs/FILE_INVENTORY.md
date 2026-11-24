# File Inventory & Classification — AI Resume Agent

This inventory classifies every major directory and root file in the repository, establishing their functional purpose, runtime role, and pre-production status.

---

## 1. Monorepo Directory Classification Table

| Path | Classification | Category | Purpose & Usage |
| :--- | :--- | :--- | :--- |
| **`apps/web/`** | **KEEP** | Source | Candidate-facing web frontend (React 19, Vite+, TanStack Router, Lingui i18n, Tailwind CSS). |
| **`apps/server/`** | **KEEP** | Source | Core backend server application (Hono v4, oRPC, Better Auth, OpenAPI, server-rendered resumes). |
| **`apps/mobile/`** | **KEEP** | Source | Cross-platform mobile application (React Native, Expo SDK 52, Expo Router). |
| **`packages/ai/`** | **KEEP** | Source | AI model providers and LLM interfaces (OpenAI, Anthropic, Gemini, DeepSeek, Groq, Ollama). |
| **`packages/api/`** | **KEEP** | Source | Core business logic, feature services, and oRPC procedure definitions. |
| **`packages/auth/`** | **KEEP** | Source | Better Auth configuration, session management, and guest/anonymous auth handlers. |
| **`packages/config/`** | **KEEP** | Configuration | Shared TypeScript, Vite, Tailwind, and ESLint configs. |
| **`packages/db/`** | **KEEP** | Source / Infra | PostgreSQL Drizzle ORM client, table schemas, and connection pool management. |
| **`packages/docx/`** | **KEEP** | Source | Word document (.docx) resume generator and styler. |
| **`packages/email/`** | **KEEP** | Source | React Email templates and transactional email dispatchers. |
| **`packages/env/`** | **KEEP** | Configuration | Strict runtime environment variable validation schemas using Zod. |
| **`packages/fonts/`** | **KEEP** | Assets | Embedded font definitions and Google Fonts mirror utilities. |
| **`packages/import/`** | **KEEP** | Source | Data parsers for importing resumes from JSON Resume, Reactive Resume, and LinkedIn. |
| **`packages/mcp/`** | **KEEP** | Source | Model Context Protocol (MCP) server endpoints for external AI agent integration. |
| **`packages/odt/`** | **KEEP** | Source | OpenDocument (.odt) resume export generator. |
| **`packages/pdf/`** | **KEEP** | Source | High-fidelity PDF rendering engine built on Forme (`@formepdf`). |
| **`packages/resume/`** | **KEEP** | Source | Pure resume algorithms, section ordering, and RFC 6902 JSON Patch operators. |
| **`packages/schema/`** | **KEEP** | Source | Canonical Zod domain models for profiles, resumes, jobs, and applications. |
| **`packages/tooling/`** | **KEEP** | Tooling | Monorepo internal workspace package (`@reactive-resume/tooling`) for builds and tests. |
| **`packages/ui/`** | **KEEP** | Source | Design system components, dialogs, form primitives, and Tailwind styling. |
| **`packages/utils/`** | **KEEP** | Source | Shared universal utilities, path helpers, and crypto primitives. |
| **`packages/dsh-plugin/`** | **KEEP** | Source | DeepSeek Harness plugin bridge for MCP sessions. |
| **`migrations/`** | **KEEP** | Database Infra | 13 sequential Drizzle SQL migration files (schema history). |
| **`tests/`** | **KEEP** | Testing | Playwright end-to-end integration test suites and fixtures. |
| **`docs/`** | **KEEP** | Documentation | Architectural specifications, deployment runbooks, and developer guides. |
| **`scripts/setup-db-user.mjs`** | **KEEP** | Script | Least-privilege database role bootstrap script (`CREATEDB` role `resume_agent`). |
| **`compose.dev.yml`** | **KEEP** | Infrastructure | Docker Compose definition for local PostgreSQL, Redis, and SeaweedFS services. |
| **`compose.yml`** | **KEEP** | Infrastructure | Base Docker Compose recipe for multi-container deployment. |
| **`Dockerfile`** | **KEEP** | Infrastructure | Production multi-stage Docker build recipe. |
| **`package.json`** | **KEEP** | Configuration | Monorepo root manifest, orchestration scripts, and package manager pin. |
| **`turbo.json`** | **KEEP** | Configuration | Turborepo pipeline caching and environment pass-through configuration. |
| **`pnpm-workspace.yaml`** | **KEEP** | Configuration | Workspace package inclusion boundaries and package patches. |
| **`LICENSE`** | **KEEP** | Legal | Legally required MIT license notice. |
| **`AGENTS.md` / `CODING_STANDARDS.md`** | **KEEP** | Governance | Engineering rules, architectural invariants, and agent instructions. |
| **`scripts/*.json`** | **REMOVED** | Obsolete Artifact | ~14.5 MB of temporary scanner dumps from initial repository audit. |
| **`server.*.log`** | **REMOVED** | Ephemeral Log | Stale development runtime stdout/stderr log files. |

---

## 2. In-Depth Inspection of the Seven Target Directories

### A. `data/` and `user/data/`
- **Purpose**: Local filesystem document storage destination when `STORAGE_BACKEND="local"`.
- **Contents**:
  - `user/data/uploads/`: Empty folder with `.gitkeep`. Live user document uploads (avatars, generated PDFs, and DOCX exports) are stored here at runtime under `user/data/uploads/<userId>/`.
  - Root `data/`: Formerly held `testing/` (test job descriptions and test runner). Cleaned up for pre-production.
- **Application References**:
  - `packages/env/src/server.ts`: Validates `LOCAL_STORAGE_PATH`.
  - `packages/api/src/features/storage/local.ts`: Writes and serves uploaded and generated artifacts.
  - `apps/server/src/startup/checks.ts`: Validates that `LOCAL_STORAGE_PATH` exists and is read/write accessible on boot.
- **Classification**: Runtime Data Destination (Empty Placeholder in Pre-Production).
- **Requirement**: Required in development and self-hosted local storage mode.
- **Recommendation**: **KEEP (EMPTY PLACEHOLDER)**. Preserve directory structure with `.gitkeep`. Ensure live user contents are git-ignored.

### B. `user/pgdata/`
- **Purpose**: Legacy Docker host volume mount directory.
- **Contents**: Contains only a 4-byte `.keep` file (`keep\n`). No PostgreSQL cluster files (`PG_VERSION`, `base/`, `global/`) exist in this directory.
- **Application References**:
  - Neither `compose.dev.yml` nor `compose.yml` mounts `./pgdata`. The active PostgreSQL service uses a managed Docker named volume (`ai_resume_agent_postgres_data:/var/lib/postgresql/data`).
- **Classification**: Infrastructure Placeholder (Legacy).
- **Requirement**: Not required at runtime since Docker uses named volumes.
- **Recommendation**: **KEEP (SAFE PLACEHOLDER)**. Retain `.keep` to avoid breaking external developer scripts or alternate compose overrides, but confirm it contains zero database records.

### C. `user/cloudron/`
- **Purpose**: Cloudron app packaging and deployment definitions.
- **Contents**: `CloudronManifest.json`, `CloudronVersions.json`, `CHANGELOG`, `DESCRIPTION.md`, `POSTINSTALL.md`, `README.md`.
- **Application References**:
  - `apps/server/docker-entrypoint.sh`: References `CLOUDRON=1` to auto-generate secrets and adjust permissions on Cloudron hosts.
- **Classification**: Deployment / Packaging Configuration.
- **Requirement**: Optional at development time; required for publishing to the Cloudron App Store.
- **Recommendation**: **KEEP (ALTERNATIVE DEPLOYMENT TARGET)**.

### D. `user/plugins/` (and `apps/mobile/plugins/`)
- **Purpose**: External AI agent and Claude plugin integration.
- **Contents**:
  - `user/plugins/reactive-resume/`: Contains `plugin.json`, `.claude-plugin/plugin.json`, `mcp.json`, and 32 domain-specific skills (e.g., `resume-builder`, `cover-letter-writer`, `career-change-resume`, `technical-writer-resume`, `interview-prep`).
  - `apps/mobile/plugins/`: Expo config plugins for native mobile build customization.
- **Application References**:
  - `packages/mcp`: Integrates with MCP client tools.
  - `apps/mobile/app.json`: References Expo native build plugins.
- **Classification**: AI Extension / Agent Integration & Build Plugins.
- **Requirement**: Core capability for AI agent ecosystem and mobile native build.
- **Recommendation**: **KEEP (CORE AI CAPABILITY)**.

### E. `user/patches/`
- **Purpose**: pnpm package patch definitions for upstream dependencies.
- **Contents**:
  - `deepmerge@4.3.1.patch`
  - `expo-router@58.0.31.patch`
  - `expo-sharing@58.0.23.patch`
  - `react-native-screens@4.30.1.patch`
- **Application References**:
  - `user/pnpm-workspace.yaml`:
    ```yaml
    patchedDependencies:
      deepmerge@4.3.1: patches/deepmerge@4.3.1.patch
      expo-router@58.0.31: patches/expo-router@58.0.31.patch
      expo-sharing@58.0.23: patches/expo-sharing@58.0.23.patch
      react-native-screens@4.30.1: patches/react-native-screens@4.30.1.patch
    ```
- **Classification**: Package Configuration / Build Patch.
- **Requirement**: Mandatory. Without these patches, `pnpm install` will fail or produce runtime exceptions in Expo routing and native screen transitions.
- **Recommendation**: **KEEP (CRITICAL BUILD CONFIGURATION)**.

### F. `user/tooling/`
- **Purpose**: Internal monorepo developer tooling and build harness package (`@reactive-resume/tooling`).
- **Contents**:
  - `locales/generate.ts`: Generates localized translation catalogs.
  - `icons/phosphor-pdf.ts`: Generates PDF-compatible phosphor icon definitions.
  - `capture/`: Browser capture and packet import utilities.
  - `dev/test-db.mjs`: Test database provisioning for isolated testing.
  - `dependency-security.test.mjs`: Dependency security auditing test suite.
  - `docker-publishing.test.ts`: Docker image validation tests.
- **Application References**:
  - Referenced in root `package.json` scripts: `pdf:translations`, `check:affected`, `locales:diff`, `test:db`.
- **Classification**: Monorepo Tooling Workspace.
- **Requirement**: Mandatory for building, translating, and testing the monorepo.
- **Recommendation**: **KEEP (ESSENTIAL TOOLING)**.

### G. `.turbo/` (and subpackage `.turbo/` directories)
- **Purpose**: Turborepo local build and task output caching.
- **Contents**: Cached outputs of `turbo run build`, `turbo run typecheck`, and task logs.
- **Application References**:
  - Controlled by Turborepo binary (`turbo`) according to `turbo.json`.
  - Listed in root `.gitignore` (`.turbo/`).
- **Classification**: Ephemeral Build Cache.
- **Requirement**: Development and build optimization cache; auto-regenerated on task execution.
- **Recommendation**: **KEEP (LOCAL CACHE, GIT-IGNORED)**. Do not commit to source control.
