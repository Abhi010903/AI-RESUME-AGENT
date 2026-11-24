# Architecture Guide — AI Resume Agent

## 1. System Architecture Diagram

```
[ Browser / Client ]
        │
        ├── Port 3000 (Development)
        ▼
┌──────────────────────────────────────────────┐
│  Vite Development Server / Static SPA Host   │
│  - React 19 Frontend                         │
│  - TanStack Router & Query                   │
│  - API Proxy (/api/* -> :3001)               │
└──────────────────────┬───────────────────────┘
                       │ HTTP Proxy
                       ▼
┌──────────────────────────────────────────────┐
│  Hono Backend Server (:3001)                 │
│  ├── /api/auth/*     -> Better Auth Engine   │
│  ├── /api/rpc/*      -> oRPC Procedure Router│
│  ├── /api/health     -> Healthcheck Endpoint │
│  ├── /mcp            -> Model Context Protocol│
│  └── Schedulers      -> Storage / Careers    │
└──────────────┬───────────────────────┬───────┘
               │                       │
      Drizzle / TCP           Storage Provider (Local / S3)
               ▼                       ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │  PostgreSQL (:5432)  │   │ Local Filesystem /   │
    │  - Users & Accounts  │   │ SeaweedFS S3 (:8333) │
    │  - Resumes & Profiles│   └──────────────────────┘
    │  - Job Applications  │
    └──────────────────────┘
```

## 2. Communication Protocols
- **Frontend to Backend**:
  - Authentication requests execute over standard HTTP JSON endpoints handled by Better Auth (`/api/auth/*`).
  - Application queries and mutations execute via typed RPC through oRPC (`/api/rpc/*`), providing end-to-end type safety between client and server without code generation.
- **Backend to Database**:
  - Drizzle ORM connects to PostgreSQL via connection pooling with `pg.Pool`.
- **Document Generation Pipeline**:
  - In browser: dynamic client-side rendering uses Web Workers and canvas previews.
  - On server: headless PDF compilation using `@formepdf/core` and `@formepdf/react`.
