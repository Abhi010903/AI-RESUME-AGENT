# Docker Guide — AI Resume Agent

## 1. Compose Configurations
The repository contains two Docker Compose files:

1. **[compose.dev.yml](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/compose.dev.yml) (Local Development Infrastructure)**:
   - Starts auxiliary backend infrastructure containers without containerizing the app itself:
     - `postgres`: PostgreSQL container on `127.0.0.1:5432`.
     - `redis`: Redis cache container on `127.0.0.1:6379`.
     - `seaweedfs`: SeaweedFS S3 object store on `127.0.0.1:8333`.
     - `seaweedfs_create_bucket`: Automatically provisions the `reactive-resume` bucket.
   - Command to start:
     ```sh
     docker compose -f compose.dev.yml up -d
     ```
   - Command to stop:
     ```sh
     docker compose -f compose.dev.yml down
     ```
2. **[compose.yml](file:///C:/Coding/Projects/AI-RESUME-AGENT/user/compose.yml) (Full Production Containerized Stack)**:
   - Builds and runs the full containerized application (`reactive_resume` service) alongside internal database and storage networks.

## 2. Container Health & Credentials
- PostgreSQL container initializes role `resume_agent` with password `resume_agent_secret` and database `resume_agent`.
- Dual healthcheck allows backward compatibility with both `resume_agent` and default `postgres` superuser roles.
- Persistent volumes: `postgres_data`, `redis_data`, `seaweedfs_data`.
