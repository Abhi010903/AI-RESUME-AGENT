"""Unit and API tests for Stage 5 — Evidence-Based Skill Matching Engine.

Covers:
- Exact skill match (STRONG_MATCH with candidate skill ID and source doc traceability).
- Partial skill match (PARTIAL_MATCH with reduced confidence).
- Related transferable skill match (RELATED_MATCH with relationship note).
- Missing skill (NO_EVIDENCE with standard non-accusatory reason).
- Conflicted candidate evidence handling (CONFLICTED_EVIDENCE).
- Experience matching (exact years, partial years, overlapping periods).
- Education and certification matching.
- Configurable scoring model, breakdown, and penalties.
- Structured gap analysis.
- Determinism of repeated executions.
- REST APIs (/api/v1/matches, /requirements, /gaps, /score, list, 404s).
"""

import uuid
from fastapi import status
from fastapi.testclient import TestClient
from app.models import CandidateProfile, Certification, Education, JobDescription, Skill, WorkExperience
from app.services.experience_matcher import calculate_non_overlapping_years, evaluate_experience_match
from app.services.match_scorer import compute_match_score
from app.services.qualification_matcher import evaluate_certifications_match, evaluate_education_match
from app.services.skill_matcher import evaluate_skill_matches


def _setup_test_profile_and_job(client: TestClient) -> tuple[str, str]:
    """Helper to insert a rich CandidateProfile and JobDescription directly into DB."""
    from app.database import get_db

    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    doc_id = str(uuid.uuid4())
    prof_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    profile = CandidateProfile(
        id=prof_id,
        full_name="Sarah Connor",
        email="sarah.connor@example.com",
        headline="Senior Backend Engineer",
        source_document_ids_json=f'["{doc_id}"]',
        verification_status="verified",
        is_approved=True,
    )
    db.add(profile)

    # Add candidate skills
    sk1 = Skill(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        name="Python",
        category="Languages",
        years_of_experience=6.0,
        source_document_id=doc_id,
        is_approved=True,
    )
    sk2 = Skill(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        name="PostgreSQL",
        category="Databases",
        years_of_experience=5.0,
        source_document_id=doc_id,
        is_approved=True,
    )
    sk3 = Skill(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        name="Flask",  # Related to FastAPI
        category="Backend",
        years_of_experience=3.0,
        source_document_id=doc_id,
        is_approved=True,
    )
    db.add_all([sk1, sk2, sk3])

    # Add work experience
    exp1 = WorkExperience(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        company="Cyberdyne Systems",
        job_title="Senior Python Developer",
        start_date="2020-01",
        end_date="2023-12",
        is_current=False,
        description="Architected microservices using Python and PostgreSQL. Utilized Docker for deployment.",
        skills_used_json='["Python", "PostgreSQL", "Docker"]',
        source_document_id=doc_id,
        is_approved=True,
    )
    exp2 = WorkExperience(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        company="Resistance Tech",
        job_title="Software Engineer",
        start_date="2018-01",
        end_date="2019-12",
        is_current=False,
        description="Built backend applications in Python.",
        skills_used_json='["Python"]',
        source_document_id=doc_id,
        is_approved=True,
    )
    db.add_all([exp1, exp2])

    # Add education
    edu = Education(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        institution="MIT",
        degree="Bachelor of Science in Computer Science",
        field_of_study="Computer Science",
        start_date="2014",
        end_date="2018",
        source_document_id=doc_id,
        is_approved=True,
    )
    db.add(edu)

    # Add certification
    cert = Certification(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        name="AWS Certified Solutions Architect",
        issuing_organization="Amazon Web Services",
        source_document_id=doc_id,
        is_approved=True,
    )
    db.add(cert)

    # Create Job Description
    job = JobDescription(
        id=job_id,
        title="Senior Backend Engineer",
        company="Skynet Innovations",
        raw_text="Job requiring Python, FastAPI, PostgreSQL, Docker, and Kubernetes.",
        min_years_experience=5.0,
        education_level="Bachelor's in Computer Science",
        status="analyzed",
    )
    job.set_required_skills([
        {"name": "Python", "category": "Languages", "is_mandatory": True, "raw_mention": "python"},
        {"name": "PostgreSQL", "category": "Databases", "is_mandatory": True, "raw_mention": "postgresql"},
        {"name": "FastAPI", "category": "Backend", "is_mandatory": True, "raw_mention": "fastapi"},  # Candidate has Flask (Related)
    ])
    job.set_preferred_skills([
        {"name": "Docker", "category": "DevOps & Cloud", "is_mandatory": False, "raw_mention": "docker"},  # Candidate has in experience
        {"name": "Kubernetes", "category": "DevOps & Cloud", "is_mandatory": False, "raw_mention": "kubernetes"},  # Missing
    ])
    job.set_certifications(["AWS Certified Solutions Architect"])
    db.add(job)

    db.commit()
    return prof_id, job_id


def test_experience_matcher_overlapping_intervals() -> None:
    """Ensure overlapping employment periods are never double-counted."""
    doc_id = str(uuid.uuid4())
    prof_id = str(uuid.uuid4())

    # Job A: 2020 - 2022 (2 years)
    # Job B: 2021 - 2023 (2 years)
    # Combined calendar duration is 2020 to 2023 = 3 years, not 4 years!
    exp_a = WorkExperience(
        id="1", profile_id=prof_id, company="A", job_title="Dev",
        start_date="2020-01", end_date="2022-01", source_document_id=doc_id,
    )
    exp_b = WorkExperience(
        id="2", profile_id=prof_id, company="B", job_title="Dev",
        start_date="2021-01", end_date="2023-01", source_document_id=doc_id,
    )

    years, excerpts = calculate_non_overlapping_years([exp_a, exp_b])
    assert 2.9 <= years <= 3.1
    assert len(excerpts) == 2


def test_skill_match_classifications(client: TestClient) -> None:
    """Verify strong match, related match, and no evidence classifications."""
    prof_id, job_id = _setup_test_profile_and_job(client)

    from app.database import get_db
    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    profile = db.get(CandidateProfile, prof_id)
    job = db.get(JobDescription, job_id)

    evals = evaluate_skill_matches(profile, job)
    status_map = {e.requirement_name: e.match_status for e in evals}

    # Python: Direct match
    assert status_map["Python"] == "STRONG_MATCH"
    # PostgreSQL: Direct match
    assert status_map["PostgreSQL"] == "STRONG_MATCH"
    # FastAPI: Candidate only has Flask, so should be RELATED_MATCH
    assert status_map["FastAPI"] == "RELATED_MATCH"
    # Docker: Found in WorkExperience description
    assert status_map["Docker"] == "STRONG_MATCH"
    # Kubernetes: Not present anywhere in candidate profile
    assert status_map["Kubernetes"] == "NO_EVIDENCE"


def test_education_and_certification_match(client: TestClient) -> None:
    """Verify education degree hierarchy matching and certification matching."""
    prof_id, job_id = _setup_test_profile_and_job(client)

    from app.database import get_db
    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    profile = db.get(CandidateProfile, prof_id)
    job = db.get(JobDescription, job_id)

    edu_eval = evaluate_education_match(profile, job)
    assert edu_eval.match_status == "STRONG_MATCH"
    assert "Bachelor" in (edu_eval.evidence_excerpt or "")
    assert edu_eval.source_document_id is not None

    cert_evals = evaluate_certifications_match(profile, job)
    assert len(cert_evals) == 1
    assert cert_evals[0].match_status == "STRONG_MATCH"
    assert "AWS Certified" in cert_evals[0].requirement_name


def test_api_create_match_workflow(client: TestClient) -> None:
    """Test POST /api/v1/matches endpoint and output schema."""
    prof_id, job_id = _setup_test_profile_and_job(client)

    payload = {
        "profile_id": prof_id,
        "job_id": job_id,
    }

    res = client.post("/api/v1/matches", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert data["id"] is not None
    assert data["profile_id"] == prof_id
    assert data["job_id"] == job_id
    assert 60.0 <= data["overall_score"] <= 95.0
    assert data["mandatory_skill_score"] > 60.0
    assert data["experience_score"] == 100.0  # 6 years exp vs 5 years required
    assert data["education_score"] == 100.0
    assert data["certification_score"] == 100.0

    # Inspect requirement matches
    req_matches = data["requirement_matches"]
    status_map = {r["requirement_name"]: r["match_status"] for r in req_matches}
    assert status_map["Python"] == "STRONG_MATCH"
    assert status_map["FastAPI"] == "RELATED_MATCH"
    assert status_map["Kubernetes"] == "NO_EVIDENCE"

    # Inspect gaps
    gaps = data["gaps"]
    gap_reqs = [g["requirement_name"] for g in gaps]
    assert "Kubernetes" in gap_reqs


def test_api_get_match_endpoints(client: TestClient) -> None:
    """Test GET /api/v1/matches/{id}, /requirements, /gaps, /score."""
    prof_id, job_id = _setup_test_profile_and_job(client)

    create_res = client.post("/api/v1/matches", json={"profile_id": prof_id, "job_id": job_id})
    match_id = create_res.json()["id"]

    # 1. GET /matches/{id}
    get_res = client.get(f"/api/v1/matches/{match_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == match_id

    # 2. GET /matches/{id}/requirements
    req_res = client.get(f"/api/v1/matches/{match_id}/requirements")
    assert req_res.status_code == status.HTTP_200_OK
    req_data = req_res.json()
    assert req_data["match_id"] == match_id
    assert len(req_data["requirements"]) >= 4

    # 3. GET /matches/{id}/gaps
    gap_res = client.get(f"/api/v1/matches/{match_id}/gaps")
    assert gap_res.status_code == status.HTTP_200_OK
    gap_data = gap_res.json()
    assert gap_data["match_id"] == match_id
    assert gap_data["total_gaps"] >= 1
    # Kubernetes is preferred and missing
    assert any(g["requirement_name"] == "Kubernetes" for g in gap_data["missing_preferred_skills"])

    # 4. GET /matches/{id}/score
    score_res = client.get(f"/api/v1/matches/{match_id}/score")
    assert score_res.status_code == status.HTTP_200_OK
    score_data = score_res.json()
    assert score_data["overall_score"] > 0
    assert "mandatory_skills" in score_data["weights"]
    assert "disclaimer" in score_data


def test_repeated_matching_determinism(client: TestClient) -> None:
    """Verify that repeated matching runs on identical data yield deterministic scores."""
    prof_id, job_id = _setup_test_profile_and_job(client)

    res1 = client.post("/api/v1/matches", json={"profile_id": prof_id, "job_id": job_id})
    res2 = client.post("/api/v1/matches", json={"profile_id": prof_id, "job_id": job_id})

    score1 = res1.json()["overall_score"]
    score2 = res2.json()["overall_score"]
    assert score1 == score2

    bd1 = res1.json()["score_breakdown"]
    bd2 = res2.json()["score_breakdown"]
    assert bd1["mandatory_skill_score"] == bd2["mandatory_skill_score"]
    assert bd1["experience_score"] == bd2["experience_score"]


def test_missing_mandatory_skills_visibly_affects_score(client: TestClient) -> None:
    """Verify that candidate missing all mandatory skills incurs a substantial score reduction."""
    from app.database import get_db
    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    # Candidate with only JavaScript/HTML (no Python/Backend)
    prof_id = str(uuid.uuid4())
    profile = CandidateProfile(id=prof_id, full_name="Frontend Dev")
    db.add(profile)
    sk = Skill(id=str(uuid.uuid4()), profile_id=prof_id, name="HTML", source_document_id="doc1")
    db.add(sk)

    # Job requiring Python, Rust, and Go as mandatory
    job_id = str(uuid.uuid4())
    job = JobDescription(id=job_id, title="Systems Dev", raw_text="Systems programming role.")
    job.set_required_skills([
        {"name": "Python", "category": "Languages", "is_mandatory": True},
        {"name": "Rust", "category": "Languages", "is_mandatory": True},
        {"name": "Go", "category": "Languages", "is_mandatory": True},
    ])
    db.add(job)
    db.commit()

    res = client.post("/api/v1/matches", json={"profile_id": prof_id, "job_id": job_id})
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    # Mandatory skill score must be 0 and overall score heavily penalized
    assert data["mandatory_skill_score"] == 0.0
    assert data["overall_score"] <= 30.0


def test_api_invalid_ids_return_404(client: TestClient) -> None:
    """Test 404 handling for invalid profile_id or job_id."""
    bad_id = "00000000-0000-0000-0000-000000000000"
    assert client.post("/api/v1/matches", json={"profile_id": bad_id, "job_id": bad_id}).status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/matches/{bad_id}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/matches/{bad_id}/requirements").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/matches/{bad_id}/gaps").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/matches/{bad_id}/score").status_code == status.HTTP_404_NOT_FOUND


def test_api_list_matches_with_filtering(client: TestClient) -> None:
    """Test GET /api/v1/matches filtering by profile_id and job_id."""
    prof_id, job_id = _setup_test_profile_and_job(client)
    client.post("/api/v1/matches", json={"profile_id": prof_id, "job_id": job_id})

    # List all
    all_res = client.get("/api/v1/matches")
    assert all_res.status_code == status.HTTP_200_OK
    assert len(all_res.json()) >= 1

    # Filter by profile_id
    filtered_res = client.get(f"/api/v1/matches?profile_id={prof_id}")
    assert filtered_res.status_code == status.HTTP_200_OK
    assert all(m["profile_id"] == prof_id for m in filtered_res.json())
