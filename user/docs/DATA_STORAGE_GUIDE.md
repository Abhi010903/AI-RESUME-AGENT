# Data Storage Guide — AI Resume Agent

## 1. Storage Architecture

The application abstracts document and asset storage through `@reactive-resume/api/features/storage` and selects the engine based on the `STORAGE_BACKEND` environment variable.

```
                              ┌─────────────────────────────┐
                              │  @reactive-resume/api        │
                              │  Storage Service            │
                              └──────────────┬──────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
        ┌───────────────────────────┐                 ┌───────────────────────────┐
        │  Local Filesystem Driver  │                 │  S3 / SeaweedFS Driver    │
        │  STORAGE_BACKEND="local"  │                 │  STORAGE_BACKEND="s3"     │
        └─────────────┬─────────────┘                 └─────────────┬─────────────┘
                      │                                             │
                      ▼                                             ▼
         user/data/uploads/<userId>/                     http://127.0.0.1:8333
         └── pdfs/<resumeId>/                            (SeaweedFS S3 Bucket)
```

---

## 2. Storage Engines

### A. Local Filesystem (`STORAGE_BACKEND="local"`)
- **Default for local development.**
- Target directory configured by `LOCAL_STORAGE_PATH` (defaults to `./data` resolving to `user/data`).
- Directory structure:
  ```
  user/data/
  └── uploads/
      └── <userId>/
          └── pdfs/
              └── <resumeId>/
                  └── public-<hash>.pdf
  ```
- The backend startup checks verify directory existence and write permissions at boot.

### B. S3 / SeaweedFS (`STORAGE_BACKEND="s3"`)
- **Recommended for multi-instance production.**
- Compatible with SeaweedFS, AWS S3, Cloudflare R2, and MinIO.
- Configured via:
  - `S3_ENDPOINT`: e.g. `http://127.0.0.1:8333`
  - `S3_BUCKET`: e.g. `reactive-resume`
  - `S3_ACCESS_KEY_ID`: S3 access key
  - `S3_SECRET_ACCESS_KEY`: S3 secret key
  - `S3_REGION`: Storage region (e.g. `us-east-1`)
  - `S3_FORCE_PATH_STYLE`: `true` for SeaweedFS/MinIO

---

## 3. Separation of Runtime Data vs Source Code

A strict boundary is maintained between application source code and runtime data:

1. **Pre-Production Clean State**:
   - `user/data/uploads/` is maintained clean with only `.gitkeep`.
   - No user-uploaded documents, resumes, or profile pictures are tracked in Git.
2. **Database Clean State**:
   - PostgreSQL contains zero user accounts, zero sessions, and zero resume records in pre-production.
   - Only system OAuth metadata (`oauth_resource` bootstrap records required by MCP) is maintained.
3. **Redis Cache**:
   - Ephemeral cache flushed of stale sessions.

---

## 4. Original User Resume Assets Protection

Original candidate resumes are protected user assets and must never be committed to Git or deleted as disposable test fixtures.

### Verified Locations of Original Resumes
The original user resumes have been verified intact and safe at:
- `C:\Users\AbhijitKumar\Downloads\Abhijit_Kumar_AIML_Resume.pdf` (127,650 bytes)
- `C:\Users\AbhijitKumar\Downloads\Abhijit_Kumar_DataEngineer_Resume.pdf` (126,887 bytes)
- `C:\Users\AbhijitKumar\Downloads\Abhijit_Kumar_AI_Resume.pdf` (262,360 bytes)
- `C:\Users\AbhijitKumar\Downloads\Abhijit_Kumar_Software_Engineering_Resume.pdf` (155,038 bytes)
- `C:\Users\AbhijitKumar\Downloads\Abhijit_Kumar_Resume.pdf` (4,238,559 bytes)

### Git Ignore Isolation
Root `.gitignore` explicitly isolates local resume fixtures:
```gitignore
# Databases & local storage
data/testing/results/
data/testing/resumes/
```
This ensures personal resume files are never inadvertently tracked, staged, or exposed in repository commits.
