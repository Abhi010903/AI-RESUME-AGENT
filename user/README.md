# AI Resume Agent — Candidate Platform

> **AI Resume Agent** is an intelligent career and resume management platform designed for precision resume architecture, ATS readability optimization, candidate profile management, and career tracking.

---

## Architecture Overview

The candidate platform is located in the `user/` workspace and powered by a modern, high-performance web stack:

- **Frontend (`apps/web`)**: React 19, Vite+, TanStack Router, TanStack Query, Tailwind CSS v4, Lingui i18n, Tiptap rich-text editor, Forme PDF engine.
- **Backend (`apps/server`)**: Node.js Hono HTTP/oRPC engine, Better Auth, Drizzle ORM, Model Context Protocol (MCP) server.
- **Database & Cache**: PostgreSQL (via Drizzle ORM) and Redis.
- **Document Rendering**: High-fidelity vector PDF generation (`@formepdf/core`, `@resvg/resvg-wasm`) and DOCX document export.
- **Shared Packages (`packages/`)**: Modular monorepo architecture with schema validation, design tokens, UI components, document engines, and utilities.

---

## Key Features

### 1. Resume Architecture & Builder
- Real-time inline editing with live page canvas and visual selection.
- 18 professionally styled resume templates with custom layout variants (single-column, two-column, ATS-safe).
- Complete typography, spacing, color palette, and margin controls.
- Real-time autosave with local crash recovery and revision history.

### 2. ATS Readiness & Verification
- Browser-based ATS checker analyzing font encodings, reading flow, and semantic hierarchy.
- Readability scoring and keyword alignment against target job descriptions.
- Export verification ensuring vector PDFs parse accurately into text-based applicant tracking systems.

### 3. Career & Application Intelligence
- Centralized tracking pipeline from saved postings to active interviews and offers.
- Automated cover letter generation linked to customized candidate resumes.
- Knowledge base storing career accomplishments, stories, and application preferences.

### 4. Multiformat Export & Import
- Vector PDF, Microsoft Word (DOCX), Markdown, and JSON data formats.
- High-fidelity import from PDF, LinkedIn archives, JSON Resume, and AI Resume Agent backups.

### 5. Developer & Agent Integration
- Built-in Model Context Protocol (MCP) server for autonomous agent orchestration.
- OpenAPI 3.1 REST API specification and client integration endpoints.

---

## Local Development Quickstart

### Prerequisites
- Node.js 24+ (Node 26 recommended)
- `pnpm@12.18.0` (`npm install -g pnpm@12.18.0` or `corepack enable`)
- PostgreSQL 18+ and Redis

### Getting Started

```bash
# 1. Install dependencies across the workspace
pnpm install

# 2. Configure environment
cp .env.example .env

# 3. Run database migrations
pnpm db:migrate

# 4. Generate PDF translation catalogs
pnpm pdf:translations

# 5. Start development servers
pnpm dev
```

The application runs at:
- **Web Interface**: `http://localhost:3000`
- **Server API & MCP**: `http://localhost:3001`

---

## Open Source Compliance & Legal Attribution

AI Resume Agent candidate application is built upon **Reactive Resume** by Amruth Pillai.
In strict compliance with the **MIT License**, all original copyright notices, license disclosures, and author credits are preserved:

```text
MIT License
Copyright (c) 2026 Amruth Pillai
```

The full license text is maintained in [`./LICENSE`](./LICENSE).
