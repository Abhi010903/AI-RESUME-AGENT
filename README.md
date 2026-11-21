# AI Resume Agent — Intelligent Career Platform

> **AI Resume Agent** is an enterprise-grade career and resume intelligence platform designed for precision resume architecture, ATS readability optimization, candidate profile management, and career tracking.

---

## 1. Target Architecture

```text
AI-RESUME-AGENT/
├── user/                    # AI Resume Agent Candidate Platform (Reactive Resume v6.1.1 engine)
│   ├── apps/
│   │   ├── web/             # React 19, Vite+, TanStack Router/Query, Tailwind CSS v4, Lingui
│   │   ├── server/          # Node.js Hono, oRPC, Better Auth, Drizzle ORM, MCP, PDF export
│   │   └── mobile/          # Expo 58 / React Native mobile application
│   ├── packages/            # 17 shared workspace packages (ai, schema, db, ui, pdf, docx, etc.)
│   ├── tooling/             # Monorepo build, locale, and test automation
│   ├── compose.dev.yml      # Local dev stack (PostgreSQL, Redis, SeaweedFS S3)
│   ├── package.json         # Root workspace manifest (pnpm + Turborepo)
│   └── LICENSE              # Original MIT License notice (Amruth Pillai)
│
├── company/                 # Reserved for future recruiter platform (Untouched)
│   └── README.md
│
├── docs/                    # Master platform architecture & development documentation
│
└── README.md                # Project master documentation
```

---

## 2. Technology Stack

* **Frontend (`user/apps/web`)**: React 19, Vite+, TanStack Router, TanStack Query, Tailwind CSS v4 (with OKLCH design tokens), Lingui i18n, Tiptap rich text editor, CodeMirror, Framer Motion.
* **Backend (`user/apps/server`)**: Node.js Hono HTTP/oRPC engine, `@orpc/server`, Better Auth (Drizzle adapter), Model Context Protocol (MCP) server.
* **Database & Cache**: PostgreSQL (via Drizzle ORM) & Redis (coordination, queues, agent streaming).
* **Document Generation**: Vector PDF rendering via `@formepdf/core` and `@resvg/resvg-wasm`; DOCX export via `docx`.
* **Mobile (`user/apps/mobile`)**: Expo 58 and React Native 0.88.
* **Monorepo Tooling**: pnpm workspaces (`pnpm@12.18.0`) and Turborepo (`turbo ^2.11.11`).

---

## 3. Brand Identity & Design System

The application features the **AI Resume Agent** design system:
* **Primary Palette**: Executive Navy/Indigo (`#0F172A`, `--ink`), Enterprise Slate (`#475569`, `--ink-2`), Crisp Canvas (`#F8FAFC`, `--bg`), Pure White Surfaces (`#FFFFFF`, `--surface`).
* **Accent**: Electric Sapphire (`#2563EB`, `--accent`) with interactive hover (`#1D4ED8`, `--accent-hover`) and soft selection tint (`#EFF6FF`, `--accent-soft`).
* **Typography**: Instrument Serif for editorial display headers; Figtree Variable for crisp, accessible UI typography.
* **WCAG Compliance**: High-contrast ratios (> 4.8:1) across all text, controls, badges, and focus rings.

---

## 4. Local Development Quickstart

### Prerequisites
* Node.js 24+ (Node 26 recommended)
* `pnpm@12.18.0` (`npm install -g pnpm@12.18.0` or `corepack enable`)
* Docker Desktop (for PostgreSQL, Redis, SeaweedFS)

### Startup Sequence
```bash
# 1. Navigate to user workspace
cd user

# 2. Launch supporting local services
docker compose -f compose.dev.yml up -d

# 3. Setup environment configuration
cp .env.example .env.local

# 4. Install dependencies
pnpm install

# 5. Run database migrations
pnpm db:migrate

# 6. Compile PDF translation catalogs
pnpm pdf:translations

# 7. Start development servers
pnpm dev
```

* **Web UI**: `http://localhost:3000`
* **API Server**: `http://localhost:3001`

---

## 5. Licensing & Legal Attribution

AI Resume Agent candidate application is a derivative project built upon **Reactive Resume** by Amruth Pillai.
In compliance with the **MIT License**, the original copyright notice is preserved in `user/LICENSE` and source package manifests:

```text
MIT License
Copyright (c) 2026 Amruth Pillai
```
All original attribution, license notices, and third-party dependency disclosures are strictly maintained.
