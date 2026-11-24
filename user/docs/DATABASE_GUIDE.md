# Database Guide — AI Resume Agent

## 1. Database Architecture
AI Resume Agent uses PostgreSQL managed with Drizzle ORM in [packages/db](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/packages/db).

## 2. Schema Structure ([packages/db/src/schema](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/packages/db/src/schema))
- `auth.ts`: Users, sessions, accounts, verification tokens, passkeys, and two-factor credentials (managed in tandem with Better Auth).
- `resume.ts`: Resumes, sections, revisions, locks, and public share settings.
- `application.ts`: Job applications, stages, application lanes, and notes.
- `storage.ts`: Metadata records for uploaded attachments and user files.
- `oauth.ts`: OAuth clients, dynamic registrations, consent grants, and tokens.

## 3. Credentials & Environment
- Environment variable: `DATABASE_URL`
- Default development connection:
  `postgresql://resume_agent:resume_agent_secret@127.0.0.1:5432/resume_agent`

## 4. Migrations
- Migration files are located in `migrations/` (`0000_...sql` to `0019_...sql`).
- Migrations run automatically when the backend server boots.
- Manual commands:
  - Generate new migrations from schema changes: `pnpm db:generate`
  - Run migrations manually: `pnpm db:migrate`
  - Open Drizzle Studio UI: `pnpm db:studio`
