# Candidate Platform — API Reference
## AI Resume Intelligence Platform

All candidate API endpoints are served under the base prefix `/api/v1`.

### Global Headers & Conventions
- **Authentication**: `Authorization: Bearer <jwt_access_token>` (for protected endpoints).
- **Tracing**: Every response contains an `X-Request-ID` header containing a unique UUID for distributed tracing.
- **Content-Type**: Requests with JSON bodies must specify `Content-Type: application/json`.
- **Response Format**: Standard JSON responses. Errors follow `{ "detail": "<error_message>" }`.

---

## 1. Authentication & Account (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new candidate account | No |
| `POST` | `/api/v1/auth/login` | Authenticate candidate & obtain JWT (Rate limited) | No |
| `GET` | `/api/v1/auth/me` | Fetch authenticated candidate details | Yes |
| `PATCH` | `/api/v1/auth/me` | Update candidate legal name | Yes |
| `POST` | `/api/v1/auth/password-change` | Change password (requires current password) | Yes |
| `POST` | `/api/v1/auth/password-reset/request` | Request password reset token | No |
| `POST` | `/api/v1/auth/password-reset/confirm` | Confirm password reset with token | No |
| `POST` | `/api/v1/auth/logout` | Revoke session & blacklist JWT token | Yes |
| `DELETE` | `/api/v1/auth/me` | Permanently delete account and all associated data | Yes |
| `GET` | `/api/v1/auth/export-data` | Export complete career knowledge base archive as JSON | Yes |

### Endpoint Details

#### `POST /api/v1/auth/register`
- **Request Body**:
  ```json
  {
    "email": "candidate@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Candidate"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": {
      "id": "c7a82b45-1234-4567-89ab-cdef01234567",
      "email": "candidate@example.com",
      "full_name": "Jane Candidate"
    }
  }
  ```

#### `GET /api/v1/auth/export-data`
- **Response `200 OK`**:
  Returns candidate archive JSON containing user profile, uploaded resumes metadata, approved candidate profiles, experiences, education, skills, target jobs, match results, generated resumes, ATS evaluations, applications, and activity logs.

---

## 2. Workflow & Activity Stream (`/api/v1/workflow`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/workflow/status` | Get 12-stage candidate lifecycle progress & primary action | Yes |
| `GET` | `/api/v1/workflow/activity` | Get chronological audit activity feed (supports `limit`) | Yes |

### Endpoint Details

#### `GET /api/v1/workflow/status`
- **Response `200 OK`**:
  ```json
  {
    "stages": [
      {
        "stage_number": 1,
        "key": "auth",
        "title": "Account & Authentication",
        "status": "completed",
        "action_label": "Manage Account",
        "action_path": "/settings"
      },
      {
        "stage_number": 2,
        "key": "upload_resumes",
        "title": "Upload Resumes",
        "status": "completed",
        "action_label": "Upload Resume",
        "action_path": "/resumes"
      }
    ],
    "primary_action": {
      "key": "approve_profile",
      "stage_number": 6,
      "title": "Approve Master Profile",
      "description": "Lock in your verified credentials as the source of truth for matching.",
      "action_label": "Review & Approve",
      "action_path": "/profile",
      "priority": "high"
    },
    "metrics": {
      "resumes_count": 2,
      "profile_completion": 85.0,
      "profile_approved": false,
      "jobs_count": 3,
      "matches_count": 2,
      "resumes_generated_count": 1,
      "applications_count": 4,
      "workflow_readiness": 50.0
    }
  }
  ```

#### `GET /api/v1/workflow/activity?limit=20`
- **Response `200 OK`**: Array of chronological activity logs with `action`, `title`, `description`, `created_at`.

---

## 3. Resume Ingestion & Processing (`/api/v1/resumes`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/resumes/upload` | Upload 1 to 10 resume files (`multipart/form-data`) | Optional/Yes |
| `GET` | `/api/v1/resumes` | List uploaded resumes with pagination | Optional/Yes |
| `GET` | `/api/v1/resumes/{id}` | Get resume document metadata | Optional/Yes |
| `GET` | `/api/v1/resumes/{id}/text` | Preview raw extracted text and extraction warnings | Optional/Yes |
| `GET` | `/api/v1/resumes/{id}/download` | Download original uploaded file | Optional/Yes |
| `POST` | `/api/v1/resumes/{id}/reprocess` | Re-run text extraction pipeline on stored document | Optional/Yes |
| `DELETE` | `/api/v1/resumes/{id}` | Delete resume record and unlink physical file | Optional/Yes |

---

## 4. Candidate Profile Intelligence (`/api/v1/profiles`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/profiles` | List candidate profiles for authenticated user | Optional/Yes |
| `POST` | `/api/v1/profiles/consolidate` | Consolidate selected resume documents into master profile | Optional/Yes |
| `GET` | `/api/v1/profiles/{id}` | Get full profile with experiences, education, skills, projects | Optional/Yes |
| `PATCH` | `/api/v1/profiles/{id}` | Update personal info, headline, contact (invalidates matches) | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/approve` | Formally approve profile as source of truth | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/conflicts/{conflict_id}/resolve` | Resolve/dismiss detected data conflict | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/experiences` | Add employment experience (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}/experiences/{exp_id}` | Delete employment record (invalidates matches) | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/education` | Add academic degree (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}/education/{edu_id}` | Delete academic record (invalidates matches) | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/skills` | Add technical skill (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}/skills/{skill_id}` | Delete technical skill (invalidates matches) | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/certifications` | Add certification (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}/certifications/{cert_id}` | Delete certification (invalidates matches) | Optional/Yes |
| `POST` | `/api/v1/profiles/{id}/projects` | Add portfolio project (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}/projects/{idx}` | Delete portfolio project (invalidates matches) | Optional/Yes |
| `DELETE` | `/api/v1/profiles/{id}` | Delete candidate profile | Optional/Yes |

---

## 5. Job Description Intelligence (`/api/v1/jobs`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/jobs/analyze` | Parse and analyze raw text job description | Optional/Yes |
| `POST` | `/api/v1/jobs/upload` | Upload job description file (`.pdf`, `.docx`, `.txt`, `.md`) | Optional/Yes |
| `POST` | `/api/v1/jobs` | Create structured job description | Optional/Yes |
| `GET` | `/api/v1/jobs` | List analyzed job postings | Optional/Yes |
| `GET` | `/api/v1/jobs/{job_id}` | Get job details and extracted requirements | Optional/Yes |
| `PATCH` | `/api/v1/jobs/{job_id}` | Update job fields (invalidates downstream matches) | Optional/Yes |
| `GET` | `/api/v1/jobs/{job_id}/requirements` | Get mandatory & preferred requirements breakdown | Optional/Yes |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete target job description | Optional/Yes |

---

## 6. Skill Match Engine (`/api/v1/matches`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/matches` | Compute 6-dimension evidence match (sets `is_stale=False`) | Optional/Yes |
| `GET` | `/api/v1/matches` | List computed matches (supports `profile_id`, `job_id` filters)| Optional/Yes |
| `GET` | `/api/v1/matches/{match_id}` | Get match breakdown, evidence citations, and gap analysis | Optional/Yes |

### Response Model Highlights (`MatchResultResponse`)
```json
{
  "id": "d8f34120-e41c-4b36-a19f-...",
  "candidate_profile_id": "...",
  "job_id": "...",
  "overall_fit_score": 87.5,
  "dimension_scores": {
    "mandatory_skills": 90.0,
    "experience_alignment": 85.0,
    "domain_fit": 80.0,
    "preferred_skills": 85.0,
    "education_alignment": 100.0,
    "certifications": 80.0
  },
  "is_stale": false,
  "stale_reason": null,
  "matched_skills": [ ... ],
  "missing_skills": [ ... ],
  "gap_analysis": { ... }
}
```

---

## 7. Resume Generation (`/api/v1/resumes`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/resumes/generate` | Generate single-page tailored resume (DOCX & PDF) | Optional/Yes |
| `GET` | `/api/v1/resumes/generated` | List generated tailored resumes | Optional/Yes |
| `GET` | `/api/v1/resumes/generated/{id}` | Get generated resume structure and metadata | Optional/Yes |
| `GET` | `/api/v1/resumes/generated/{id}/download` | Download compiled file (`?format=pdf` or `?format=docx`) | Optional/Yes |
| `GET` | `/api/v1/resumes/generated/{id}/versions` | Compare version differences and ATS scores | Optional/Yes |
| `DELETE` | `/api/v1/resumes/generated/{id}` | Delete tailored resume and unlink physical files | Optional/Yes |

---

## 8. ATS Evaluation (`/api/v1/ats`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/ats/evaluate` | Run transparent 7-dimension ATS audit on generated resume | Optional/Yes |
| `GET` | `/api/v1/ats/reports` | List ATS evaluation reports | Optional/Yes |
| `GET` | `/api/v1/ats/reports/{id}` | Get full ATS report, keyword analysis, and recommendations | Optional/Yes |

---

## 9. Application Tracker (`/api/v1/applications`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/applications` | Track new job application (links `job_id` and `resume_id`) | Optional/Yes |
| `GET` | `/api/v1/applications` | List applications with status, search, and ordering filters | Optional/Yes |
| `GET` | `/api/v1/applications/{id}` | Get application details and interview round history | Optional/Yes |
| `PATCH` | `/api/v1/applications/{id}` | Update pipeline stage, notes, or interview rounds | Optional/Yes |
| `DELETE` | `/api/v1/applications/{id}` | Delete tracked application | Optional/Yes |

---

## 10. HTTP Status Codes & Error Handling

- `200 OK`: Request succeeded.
- `201 Created`: Resource created successfully.
- `400 Bad Request`: Validation failure or invalid parameters.
- `401 Unauthorized`: Missing, expired, or revoked Bearer token.
- `404 Not Found`: Resource does not exist or belongs to another tenant.
- `422 Unprocessable Entity`: Request body violates Pydantic schema rules.
- `429 Too Many Requests`: Sliding-window rate limit exceeded on authentication endpoints.
- `500 Internal Server Error`: Unhandled server exception with internal stack trace masked.
