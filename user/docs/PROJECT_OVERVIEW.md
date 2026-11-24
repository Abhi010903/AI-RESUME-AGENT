# Project Overview — AI Resume Agent

## 1. Mission and Identity
**AI Resume Agent** is an intelligent career, resume creation, and document management platform derived from Reactive Resume v6.1.1. It provides an intuitive, real-time web builder, mobile client, automated ATS parsing/matching, AI-assisted content optimization, document export (PDF, Word, OpenDocument), and Model Context Protocol (MCP) tool integration.

## 2. Core Capabilities
- **Resume Authoring**: Modular, section-based resume builder with live reactive rendering across multi-page layouts.
- **Export Formats**: Multi-page PDF generation via `@formepdf/react`, Microsoft Word (.docx), and OpenDocument (.odt).
- **Authentication**: Email/password authentication, guest/anonymous mode with automatic data transfer upon registration, passkey support, and two-factor authentication via Better Auth.
- **ATS Checker**: Structured evaluation of resume content against ATS criteria and job requirements.
- **Career Management**: Automated job application pipeline tracking across customizable workflow stages.
- **AI Integrations**: Provider support for OpenAI, Anthropic, Google Gemini, DeepSeek, and custom OpenAI-compatible endpoints.
- **MCP Integration**: Remote Model Context Protocol transport enabling autonomous agents to read, query, and edit resumes.
- **Internationalization**: Lingui-powered translations supporting dozens of languages across web, mobile, and PDFs.

## 3. Technology Stack Summary
- **Frontend**: React 19, Vite+, Tailwind CSS v4, TanStack Router, TanStack Query, Lingui, Phosphor Icons.
- **Backend**: Hono, Node Server, oRPC, Better Auth, Drizzle ORM, Zod, OpenAPI.
- **Database & Cache**: PostgreSQL (v14/v18/v19 compatibility), Redis.
- **Storage**: Pluggable storage abstraction supporting local filesystem storage (`STORAGE_BACKEND=local`) and S3-compatible object storage (SeaweedFS, AWS S3, Cloudflare R2).
- **Monorepo Management**: Turborepo, pnpm workspaces.
