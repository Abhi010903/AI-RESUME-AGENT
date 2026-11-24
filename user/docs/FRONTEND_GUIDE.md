# Frontend Guide — AI Resume Agent

## 1. Overview
The frontend application lives in `apps/web`. It is a single-page application built with React 19, TypeScript, and Vite+ (built on Rolldown).

## 2. Key Directories
- `apps/web/src/routes/`: File-based routing powered by TanStack Router.
  - `_auth/`: Sign-in, sign-up, password reset, and guest entry pages.
  - `builder.$id.tsx`: The primary resume editor interface.
  - `dashboard/`: User dashboard displaying resumes, settings, and job applications.
  - `ats-checker/`: Interactive ATS scoring and match analyzer.
  - `routeTree.gen.ts`: Auto-generated router tree (never edit manually).
- `apps/web/src/features/`: Feature-scoped components and hooks.
  - `resume/`: Section editors, live preview canvas, template selectors, and export menus.
  - `auth/`: Authentication forms, session management providers, and protected route wrappers.
  - `ats-checker/`: ATS parsing, score cards, and keyword suggestions.
  - `dashboard/`: Management grids for resumes and application pipelines.

## 3. Development Server & Proxy
- Port: `3000` (configurable via `PORT`).
- Proxy: In development, [`apps/web/vite.config.ts`](../apps/web/vite.config.ts) proxies `/api/*` requests to the Hono backend server on `http://localhost:3001` (`SERVER_PORT`).

## 4. State Management & Data Fetching
- **Server State**: Managed via `@tanstack/react-query` and `@orpc/client`.
- **Client State**: Fine-grained local state using React hooks and TanStack Store.
- **Internationalization**: Lingui macros (`t`, `Trans`, `<Trans>`) with message extraction via `pnpm lingui:extract`.
