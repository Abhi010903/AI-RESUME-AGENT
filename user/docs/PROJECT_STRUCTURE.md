# Project Structure — AI Resume Agent

## 1. Monorepo Organization
The codebase uses a Turborepo + pnpm workspaces structure organized into applications, shared packages, tooling, and database migrations.

```
AI-RESUME-AGENT/
├── apps/
│   ├── web/               # React 19 / Vite+ web application
│   ├── server/            # Hono backend HTTP / RPC / MCP server
│   └── mobile/            # React Native / Expo mobile application
├── packages/
│   ├── ai/                # LLM client abstractions & providers
│   ├── api/               # Business logic, services, oRPC feature routers
│   ├── auth/              # Better Auth config, plugins, and session management
│   ├── config/            # Shared tsconfig, lint, and tool configs
│   ├── db/                # Drizzle ORM database client & schema definitions
│   ├── docx/              # Microsoft Word (.docx) document exporter
│   ├── email/             # React Email templates & transport
│   ├── env/               # Zod-validated environment configurations
│   ├── fonts/             # Font assets, Computer Modern, and Google mirrors
│   ├── import/            # Parsers for JSON Resume, LinkedIn, and RR formats
│   ├── mcp/               # Model Context Protocol tools & discovery
│   ├── odt/               # OpenDocument (.odt) exporter
│   ├── pdf/               # Multi-page PDF rendering via @formepdf
│   ├── resume/            # Pure resume domain logic & JSON Patch transforms
│   ├── schema/            # Zod domain schemas for resumes & applications
│   ├── tooling/           # Monorepo development & localization utilities
│   ├── ui/                # Shared UI primitives and Tailwind styles
│   ├── utils/             # Core utility functions
│   └── dsh-plugin/        # External deep-seek integration plugin
├── migrations/            # Drizzle ORM SQL migrations & snapshots
├── tooling/               # Dev scripts, Playwright runner, test DB orchestrator
├── tests/                 # Playwright end-to-end test suites & fixtures
└── docs/                  # Architecture, setup, and usage documentation
```

## 2. Package Boundaries
Turborepo boundaries are enforced via `pnpm exec turbo boundaries`:
- `apps/web` and `apps/server` must never depend on each other directly; communication occurs strictly over HTTP/oRPC.
- Shared domain logic belongs in `packages/` and is consumed via package import maps (e.g. `@reactive-resume/schema`).
- Platform-specific code sits behind explicit export subpaths (e.g. `@reactive-resume/env/server`).
