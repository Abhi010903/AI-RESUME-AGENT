# Authentication Guide — AI Resume Agent

## 1. Authentication Engine
Authentication is provided by [Better Auth](https://www.better-auth.com/) in [`packages/auth`](../packages/auth).

## 2. Supported Flows
1. **Email / Password**:
   - Sign-up: `POST /api/auth/sign-up/email`
   - Sign-in: `POST /api/auth/sign-in/email`
   - Sign-out: `POST /api/auth/sign-out`
   - Passwords hashed using `bcryptjs`.
2. **Anonymous / Guest Login**:
   - Sign-in: `POST /api/auth/sign-in/anonymous`
   - Issues a temporary guest account (`temp-*@resume-agent.local`) with `is_anonymous = true`.
   - Allows users to build resumes immediately without upfront registration.
   - When the user signs up or logs in, `moveGuestWork` automatically transfers resumes, profiles, and applications to the registered account.
3. **Session Management**:
   - Session tokens are stored in the database `session` table and transmitted via `better-auth.session_token` HTTP-only cookie.
   - Session retrieval: `GET /api/auth/get-session`.

## 3. Security & Origin Verification
- Better Auth enforces origin checking. In development, `http://localhost:3000` and `http://127.0.0.1:3000` are configured as trusted origins in [`packages/auth/src/trusted-origins.ts`](../packages/auth/src/trusted-origins.ts).
- Requests lacking an approved `Origin` header are rejected with HTTP 403 `MISSING_OR_NULL_ORIGIN`.
