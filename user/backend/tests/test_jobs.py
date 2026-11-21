"""Unit and integration tests for Stage 4 — Job Description Intelligence.

Covers:
- Job description ingestion and parsing (plain text, pasted, API).
- Structured model representation (title, company, location, experience, etc.).
- Requirement classification (mandatory vs preferred vs responsibilities).
- Skill normalization and taxonomy alias mapping.
- Experience and qualification extraction.
- Quality warnings (missing title, vague description, contradictory requirements, duplicates).
- REST APIs (/api/v1/jobs/analyze, /api/v1/jobs, /requirements, /skills, pagination, updates, error handling).
"""

from fastapi import status
from fastapi.testclient import TestClient
from app.services.job_description_parser import parse_job_description
from app.services.skill_normalizer import (
    are_skills_related,
    extract_known_skills_from_text,
    get_related_skills,
    normalize_skill,
)


def test_skill_normalization_and_aliases() -> None:
    """Verify alias normalization to canonical names and taxonomy categories."""
    assert normalize_skill("js")["canonical_name"] == "JavaScript"
    assert normalize_skill("ts")["canonical_name"] == "TypeScript"
    assert normalize_skill("py")["canonical_name"] == "Python"
    assert normalize_skill("python3")["canonical_name"] == "Python"
    assert normalize_skill("golang")["canonical_name"] == "Go"
    assert normalize_skill("k8s")["canonical_name"] == "Kubernetes"
    assert normalize_skill("postgres")["canonical_name"] == "PostgreSQL"
    assert normalize_skill("Postgre SQL")["canonical_name"] == "PostgreSQL"
    assert normalize_skill("reactjs")["canonical_name"] == "React"
    assert normalize_skill("react.js")["canonical_name"] == "React"
    assert normalize_skill("node")["canonical_name"] == "Node.js"
    assert normalize_skill("nodejs")["canonical_name"] == "Node.js"
    assert normalize_skill("ml")["canonical_name"] == "Machine Learning"
    assert normalize_skill("dl")["canonical_name"] == "Deep Learning"
    assert normalize_skill("tf")["canonical_name"] == "TensorFlow"
    assert normalize_skill("rest api")["canonical_name"] == "REST APIs"
    assert normalize_skill("cicd")["canonical_name"] == "CI/CD"


def test_skill_distinctions_and_relationships() -> None:
    """Ensure distinct skills are never conflated, while related skills are mapped correctly."""
    # Strict distinctions
    is_rel, _, strength = are_skills_related("Java", "JavaScript")
    assert not is_rel
    assert strength == 0.0

    is_rel, _, _ = are_skills_related("React", "Angular")
    assert not is_rel

    is_rel, _, _ = are_skills_related("AWS", "Azure")
    assert not is_rel

    # Transferable / Related skill relationships
    is_rel, note, strength = are_skills_related("FastAPI", "Python")
    assert is_rel
    assert strength >= 0.8
    assert note is not None and "Python" in note

    is_rel, _, strength = are_skills_related("PostgreSQL", "MySQL")
    assert is_rel
    assert strength >= 0.6

    is_rel, _, strength = are_skills_related("Docker", "Kubernetes")
    assert is_rel
    assert strength >= 0.6

    related_fastapi = get_related_skills("FastAPI")
    skills = [r["related_skill"] for r in related_fastapi]
    assert "Python" in skills
    assert "REST APIs" in skills


def test_job_description_parser_structured_extraction() -> None:
    """Verify parsing of title, company, location, experience, and requirements."""
    jd_text = """
    Senior Python Engineer
    Company: CloudScale Solutions
    Location: Remote
    Employment Type: Full-time

    About the Role:
    We are looking for an experienced Senior Python Engineer to lead our API team.

    Key Responsibilities:
    - Architect and maintain high-performance REST APIs using FastAPI.
    - Optimize complex PostgreSQL queries and Redis caching.
    - Collaborate with product and DevOps engineers.

    Requirements:
    - 5+ years of experience in backend software engineering.
    - Must have deep knowledge of Python and FastAPI.
    - Required hands-on experience with PostgreSQL and relational databases.
    - Bachelor's degree in Computer Science or related field.

    Preferred Qualifications:
    - Experience with Docker and Kubernetes is a plus.
    - Knowledge of AWS cloud infrastructure is desirable.
    - Familiarity with CI/CD pipelines.
    """

    parsed = parse_job_description(jd_text)

    assert parsed.title == "Senior Python Engineer"
    assert parsed.company == "CloudScale Solutions"
    assert parsed.location == "Remote"
    assert parsed.seniority_level == "Senior"
    assert parsed.employment_type == "Full-Time"
    assert parsed.min_years_experience == 5.0
    assert "Bachelor" in (parsed.education_level or "")
    assert len(parsed.responsibilities) >= 2

    # Required skills vs preferred skills
    req_names = [s["name"] for s in parsed.required_skills]
    pref_names = [s["name"] for s in parsed.preferred_skills]

    assert "Python" in req_names
    assert "FastAPI" in req_names
    assert "PostgreSQL" in req_names
    assert "Kubernetes" in pref_names
    assert "Docker" in pref_names
    assert "AWS" in pref_names


def test_quality_warnings_for_problematic_job_descriptions() -> None:
    """Test detection of missing title, short text, and contradictory requirements."""
    # Missing title and unusually short text
    vague_text = "Looking for a coder who knows coding and computer stuff."
    parsed = parse_job_description(vague_text)
    assert any("short" in w.lower() for w in parsed.quality_warnings)
    assert any("skills" in w.lower() for w in parsed.quality_warnings)

    # Contradictory experience requirements: Junior role with 8 years experience
    contradictory_text = """
    Junior Software Developer
    Company: TechCorp
    Requirements:
    - 8+ years of hands-on experience in backend engineering.
    - Must know Python and SQL.
    """
    parsed_contra = parse_job_description(contradictory_text)
    assert any("contradictory" in w.lower() for w in parsed_contra.quality_warnings)


def test_api_analyze_job_description(client: TestClient) -> None:
    """Test POST /api/v1/jobs/analyze endpoint."""
    payload = {
        "raw_text": """
        Position: Lead Backend Architect
        Company: NexaCorp
        Location: New York, NY
        Summary:
        Lead our backend engineering teams.
        Responsibilities:
        - Design scalable microservices in Go and Python.
        - Mentor junior and mid-level engineers.
        Requirements:
        - At least 7 years of software development experience.
        - Must have expert knowledge of Go, Python, and PostgreSQL.
        - Master's degree preferred.
        Preferred Qualifications:
        - Kubernetes certification (CKA) is a plus.
        - Experience with Terraform.
        """,
    }

    response = client.post("/api/v1/jobs/analyze", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["id"] is not None
    assert data["title"] == "Lead Backend Architect"
    assert data["company"] == "NexaCorp"
    assert data["location"] == "New York, NY"
    assert data["seniority_level"] == "Lead"
    assert data["min_years_experience"] == 7.0
    assert len(data["responsibilities"]) >= 1

    req_skills = [s["name"] for s in data["required_skills"]]
    assert "Go" in req_skills
    assert "Python" in req_skills
    assert "PostgreSQL" in req_skills


def test_api_create_and_get_job_description(client: TestClient) -> None:
    """Test POST /api/v1/jobs and GET /api/v1/jobs/{job_id}."""
    create_payload = {
        "title": "Full Stack Engineer",
        "company": "StartupX",
        "raw_text": """
        Full Stack Engineer
        We need a Full Stack Engineer to build web apps.
        Responsibilities:
        - Develop React user interfaces.
        - Build FastAPI REST endpoints.
        Requirements:
        - 3+ years of experience with React and Python.
        - Must know TypeScript and PostgreSQL.
        """,
    }

    create_res = client.post("/api/v1/jobs", json=create_payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    job_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == status.HTTP_200_OK
    job_data = get_res.json()
    assert job_data["title"] == "Full Stack Engineer"
    assert job_data["company"] == "StartupX"
    assert job_data["min_years_experience"] == 3.0


def test_api_list_jobs_and_filtering(client: TestClient) -> None:
    """Test GET /api/v1/jobs with pagination and seniority filtering."""
    # Seed 2 jobs
    res1 = client.post(
        "/api/v1/jobs",
        json={"title": "Senior DevOps Engineer", "raw_text": "Senior DevOps Engineer with 6+ years in AWS and Docker."},
    )
    senior_id = res1.json()["id"]

    res2 = client.post(
        "/api/v1/jobs",
        json={"title": "Junior QA Engineer", "raw_text": "Junior QA Engineer with 1+ years in automated testing."},
    )
    junior_id = res2.json()["id"]

    list_res = client.get("/api/v1/jobs?limit=10")
    assert list_res.status_code == status.HTTP_200_OK
    items = list_res.json()
    assert len(items) >= 2

    # Filter by seniority
    filter_res = client.get("/api/v1/jobs?seniority=Senior")
    assert filter_res.status_code == status.HTTP_200_OK
    filtered = filter_res.json()
    filtered_ids = [j["id"] for j in filtered]
    assert senior_id in filtered_ids
    assert junior_id not in filtered_ids


def test_api_patch_job_description(client: TestClient) -> None:
    """Test PATCH /api/v1/jobs/{job_id} updates fields properly."""
    res = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Dev", "raw_text": "Backend Dev with 2+ years of Python experience."},
    )
    job_id = res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/jobs/{job_id}",
        json={"title": "Staff Backend Engineer", "min_years_experience": 8.0},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    updated = patch_res.json()
    assert updated["title"] == "Staff Backend Engineer"
    assert updated["min_years_experience"] == 8.0


def test_api_job_requirements_and_skills_endpoints(client: TestClient) -> None:
    """Test GET /api/v1/jobs/{job_id}/requirements and /skills."""
    jd_text = """
    Site Reliability Engineer
    Responsibilities:
    - Maintain 99.99% uptime for cloud infrastructure.
    Requirements:
    - 4+ years of experience with Linux and Kubernetes.
    - Must have deep knowledge of Docker and CI/CD.
    Preferred:
    - Knowledge of Terraform is a plus.
    """
    res = client.post("/api/v1/jobs", json={"title": "Site Reliability Engineer", "raw_text": jd_text})
    job_id = res.json()["id"]

    # Test requirements endpoint
    req_res = client.get(f"/api/v1/jobs/{job_id}/requirements")
    assert req_res.status_code == status.HTTP_200_OK
    req_data = req_res.json()
    assert req_data["job_id"] == job_id
    assert len(req_data["mandatory_requirements"]) >= 2
    assert len(req_data["preferred_requirements"]) >= 1

    # Test skills endpoint
    skills_res = client.get(f"/api/v1/jobs/{job_id}/skills")
    assert skills_res.status_code == status.HTTP_200_OK
    skills_data = skills_res.json()
    req_names = [s["name"] for s in skills_data["required_skills"]]
    pref_names = [s["name"] for s in skills_data["preferred_skills"]]
    assert "Kubernetes" in req_names
    assert "Docker" in req_names
    assert "Terraform" in pref_names


def test_api_invalid_job_id_returns_404(client: TestClient) -> None:
    """Test 404 behavior for nonexistent job IDs."""
    bad_id = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/jobs/{bad_id}").status_code == status.HTTP_404_NOT_FOUND
    assert client.patch(f"/api/v1/jobs/{bad_id}", json={"title": "New"}).status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/jobs/{bad_id}/requirements").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/jobs/{bad_id}/skills").status_code == status.HTTP_404_NOT_FOUND


def test_api_empty_input_validation(client: TestClient) -> None:
    """Test that empty or too short text fails request validation."""
    response = client.post("/api/v1/jobs/analyze", json={"raw_text": ""})
    assert response.status_code == 422


def test_api_upload_and_delete_job(client: TestClient) -> None:
    """Test uploading a job description file and deleting a job."""
    content = b"Senior ML Engineer at Scale AI. Required: Python, PyTorch. 3+ years experience."
    res = client.post(
        "/api/v1/jobs/upload",
        files={"file": ("job.txt", content, "text/plain")},
        data={"company": "Scale AI", "title": "Senior ML Engineer"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    job_id = res.json()["id"]
    assert res.json()["company"] == "Scale AI"

    # Delete
    del_res = client.delete(f"/api/v1/jobs/{job_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify 404
    assert client.get(f"/api/v1/jobs/{job_id}").status_code == status.HTTP_404_NOT_FOUND

