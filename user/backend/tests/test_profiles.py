"""Tests for Stage 3 — Candidate Profile Intelligence.

Covers:
- Information consolidation across multiple resumes (1-10 resumes).
- Duplicate detection and record merging.
- Conflict detection (chronology, overlaps, gaps, identity, missing contact info).
- Evidence traceability (source document ID and raw text retention).
- Candidate review, updates, conflict resolution, and approval workflow.
- Input validation and failure handling.
"""

from fastapi import status
from fastapi.testclient import TestClient
from app.models import Document


def _create_mock_document(client: TestClient, filename: str, text: str) -> str:
    """Helper to insert a mock completed Document record and return its ID."""
    from app.database import get_db
    import uuid

    app = client.app
    # Obtain a DB session from app dependency
    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        filename=filename,
        file_format="pdf",
        file_size=len(text.encode()),
        file_hash=f"hash_{doc_id[:8]}",
        storage_path=f"storage/{doc_id}.pdf",
        status="completed",
        page_count=1,
        extracted_text=text,
    )
    db.add(doc)
    db.commit()
    return doc_id


def test_consolidate_single_resume_success(client: TestClient) -> None:
    """Test consolidating a single extracted resume into a candidate profile."""
    resume_text = """
    Alice Walker
    alice.walker@example.com | +1 555-0199 | San Francisco, CA
    https://linkedin.com/in/alicewalker | https://github.com/alicewalker

    ## Summary
    Senior Backend Architect with 8+ years building distributed Python services.

    ## Work Experience
    Senior Software Engineer at Stripe | 2021-01 - Present
    - Architected payment routing services with Python, FastAPI, and PostgreSQL.
    - Reduced transaction latency by 35%.

    Backend Developer at Twilio | 2018-05 - 2020-12
    - Developed SMS delivery pipeline with Python and Redis.

    ## Education
    Bachelor of Science in Computer Science | Stanford University | 2014 - 2018

    ## Skills
    Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes

    ## Certifications
    AWS Certified Solutions Architect | Amazon Web Services | 2022
    """
    doc_id = _create_mock_document(client, "alice_resume.pdf", resume_text)

    res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id]})
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert data["full_name"] == "Alice Walker"
    assert data["email"] == "alice.walker@example.com"
    assert data["phone"] == "+1 555-0199"
    assert "linkedin.com/in/alicewalker" in (data["linkedin_url"] or "")
    assert data["source_document_ids"] == [doc_id]
    assert data["verification_status"] == "unverified"
    assert data["is_approved"] is False

    # Experiences check
    assert len(data["experiences"]) == 2
    titles = [e["job_title"] for e in data["experiences"]]
    assert "Senior Software Engineer" in titles
    assert "Backend Developer" in titles
    for exp in data["experiences"]:
        assert exp["source_document_id"] == doc_id
        assert exp["is_approved"] is False

    # Education check
    assert len(data["education"]) == 1
    assert "Stanford" in data["education"][0]["institution"]
    assert data["education"][0]["source_document_id"] == doc_id

    # Skills check
    assert len(data["skills"]) >= 5
    skill_names = [s["name"] for s in data["skills"]]
    assert "Python" in skill_names
    assert "Fastapi" in skill_names

    # Certifications check
    assert len(data["certifications"]) == 1
    assert "AWS Certified Solutions Architect" in data["certifications"][0]["name"]
    assert data["certifications"][0]["source_document_id"] == doc_id


def test_consolidate_multiple_resumes_deduplication(client: TestClient) -> None:
    """Test merging 2 resumes for the same candidate without losing historical details or duplicating entries."""
    resume_1 = """
    Bob Chen
    bob.chen@example.com | 555-123-4567

    ## Work Experience
    Lead Engineer at DataCorp | 2020-01 - Present
    - Implemented real-time ETL engine using Python and Kafka.

    ## Education
    B.S. in Software Engineering | University of Michigan | 2016 - 2020

    ## Skills
    Python, Kafka, SQL
    """

    # Resume 2 contains updated/overlapping details for same job + new skills
    resume_2 = """
    Bob Chen
    bob.chen@example.com | 555-123-4567

    ## Work Experience
    Lead Engineer at DataCorp | 2020-01 - Present
    - Scaled distributed database clusters with PostgreSQL and Docker.

    ## Education
    B.S. in Software Engineering | University of Michigan | 2016 - 2020

    ## Skills
    python, sql, Docker, Kubernetes
    """

    doc_id_1 = _create_mock_document(client, "bob_resume_v1.pdf", resume_1)
    doc_id_2 = _create_mock_document(client, "bob_resume_v2.pdf", resume_2)

    res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id_1, doc_id_2]})
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert set(data["source_document_ids"]) == {doc_id_1, doc_id_2}

    # Verify experience is merged into a single entry with combined descriptions and skills
    assert len(data["experiences"]) == 1
    exp = data["experiences"][0]
    assert exp["company"] == "DataCorp"
    assert exp["job_title"] == "Lead Engineer"
    assert "ETL engine" in exp["description"]
    assert "database clusters" in exp["description"]

    # Verify education is deduplicated
    assert len(data["education"]) == 1
    assert "Michigan" in data["education"][0]["institution"]

    # Verify skills are deduplicated case-insensitively
    skill_names = [s["name"] for s in data["skills"]]
    assert len(skill_names) == len(set(s.lower() for s in skill_names))
    assert "Python" in skill_names
    assert "Docker" in skill_names


def test_conflict_detection_chronology_and_overlap(client: TestClient) -> None:
    """Detect conflicting employment dates and overlapping full-time positions."""
    resume_with_conflicts = """
    Carol Danvers
    carol@example.com | 555-987-6543

    ## Work Experience
    Software Engineer at TechCorp | 2022-05 - 2020-01
    - Reverse date sequence error.

    Full-Time Architect at AlphaCorp | 2021-01 - 2023-01
    - Role A

    Full-Time Developer at BetaCorp | 2022-01 - 2024-01
    - Role B overlapping with Role A
    """
    doc_id = _create_mock_document(client, "carol_conflicts.pdf", resume_with_conflicts)

    res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id]})
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    conflicts = data["conflicts"]
    conflict_types = [c["conflict_type"] for c in conflicts]

    # Verify chronological invalid date conflict detected
    assert "EMPLOYMENT_DATE_INVALID" in conflict_types

    # Verify overlapping positions detected
    assert "EMPLOYMENT_DATE_OVERLAP" in conflict_types


def test_conflict_detection_missing_contact_and_identity_conflict(client: TestClient) -> None:
    """Detect missing email/phone and differing candidate names across submitted documents."""
    resume_anonymous = """
    Developer Profile

    ## Work Experience
    Backend Engineer at StartupX | 2021 - 2023
    - Built microservices.
    """

    resume_differing_name = """
    John Doe
    john.doe@example.com | 555-444-3333

    ## Work Experience
    Senior Engineer at StartupX | 2021 - 2023
    """

    resume_another_name = """
    Jane Smith
    jane.smith@example.com | 555-777-8888

    ## Work Experience
    Staff Engineer at StartupX | 2021 - 2023
    """

    doc_anon = _create_mock_document(client, "anon.pdf", resume_anonymous)
    doc_john = _create_mock_document(client, "john.pdf", resume_differing_name)
    doc_jane = _create_mock_document(client, "jane.pdf", resume_another_name)

    # 1. Missing contact info test
    res_anon = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_anon]})
    conflicts_anon = [c["conflict_type"] for c in res_anon.json()["conflicts"]]
    assert "MISSING_CONTACT_INFO" in conflicts_anon

    # 2. Identity conflict test (John vs Jane)
    res_identity = client.post(
        "/api/v1/profiles/consolidate", json={"document_ids": [doc_john, doc_jane]}
    )
    conflicts_identity = [c["conflict_type"] for c in res_identity.json()["conflicts"]]
    assert "IDENTITY_CONFLICT" in conflicts_identity


def test_candidate_review_and_manual_updates(client: TestClient) -> None:
    """Candidate can review, edit contact info, experiences, education, and skills."""
    resume_text = """
    David Miller
    david@example.com | 555-222-1111

    ## Work Experience
    Engineer at OldCompany | 2019 - 2021
    - Maintained systems.

    ## Education
    B.A. in History | State College | 2015 - 2019

    ## Skills
    Java, C++
    """
    doc_id = _create_mock_document(client, "david.pdf", resume_text)
    init_res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id]})
    profile = init_res.json()
    profile_id = profile["id"]
    exp_id = profile["experiences"][0]["id"]
    edu_id = profile["education"][0]["id"]
    skill_id = profile["skills"][0]["id"]

    # 1. Update Profile General Info
    patch_profile = client.patch(
        f"/api/v1/profiles/{profile_id}",
        json={"headline": "Staff Distributed Systems Engineer", "location": "Austin, TX"},
    )
    assert patch_profile.status_code == status.HTTP_200_OK
    assert patch_profile.json()["headline"] == "Staff Distributed Systems Engineer"
    assert patch_profile.json()["location"] == "Austin, TX"

    # 2. Update Work Experience
    patch_exp = client.patch(
        f"/api/v1/profiles/{profile_id}/experiences/{exp_id}",
        json={"job_title": "Senior Staff Engineer", "skills_used": ["Java", "Spring Boot", "Kafka"]},
    )
    assert patch_exp.status_code == status.HTTP_200_OK
    assert patch_exp.json()["job_title"] == "Senior Staff Engineer"
    assert "Spring Boot" in patch_exp.json()["skills_used"]

    # 3. Update Education
    patch_edu = client.patch(
        f"/api/v1/profiles/{profile_id}/education/{edu_id}",
        json={"degree": "B.S. in Computer Science"},
    )
    assert patch_edu.status_code == status.HTTP_200_OK
    assert patch_edu.json()["degree"] == "B.S. in Computer Science"

    # 4. Update Skill
    patch_sk = client.patch(
        f"/api/v1/profiles/{profile_id}/skills/{skill_id}",
        json={"proficiency": "expert", "years_of_experience": 5.5},
    )
    assert patch_sk.status_code == status.HTTP_200_OK
    assert patch_sk.json()["proficiency"] == "expert"
    assert patch_sk.json()["years_of_experience"] == 5.5


def test_conflict_resolution_and_approval_workflow(client: TestClient) -> None:
    """Test resolving detected conflicts and stepping through verification approval."""
    resume_text = """
    Eva Green
    eva@example.com | 555-999-0000

    ## Work Experience
    Engineer at CompanyA | 2020 - 2022
    Engineer at CompanyB | 2021 - 2023
    """
    doc_id = _create_mock_document(client, "eva.pdf", resume_text)
    res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id]})
    profile = res.json()
    profile_id = profile["id"]
    conflicts = profile["conflicts"]
    assert len(conflicts) > 0
    conflict_id = conflicts[0]["id"]

    # Initial state
    assert profile["verification_status"] == "unverified"
    assert profile["is_approved"] is False

    # 1. Resolve Conflict
    resolve_res = client.post(
        f"/api/v1/profiles/{profile_id}/conflicts/{conflict_id}/resolve",
        json={"resolution_status": "resolved", "resolution_notes": "CompanyB was part-time consulting."},
    )
    assert resolve_res.status_code == status.HTTP_200_OK
    updated_conflicts = resolve_res.json()["conflicts"]
    matched = next(c for c in updated_conflicts if c["id"] == conflict_id)
    assert matched["resolution_status"] == "resolved"
    assert matched["resolution_notes"] == "CompanyB was part-time consulting."

    # 2. Partial Approval
    exp_id = profile["experiences"][0]["id"]
    part_app_res = client.post(
        f"/api/v1/profiles/{profile_id}/approve",
        json={"approve_all": False, "experience_ids": [exp_id]},
    )
    assert part_app_res.status_code == status.HTTP_200_OK
    assert part_app_res.json()["verification_status"] == "partially_verified"

    # 3. Complete Approval
    full_app_res = client.post(
        f"/api/v1/profiles/{profile_id}/approve",
        json={"approve_all": True},
    )
    assert full_app_res.status_code == status.HTTP_200_OK
    assert full_app_res.json()["verification_status"] == "approved"
    assert full_app_res.json()["is_approved"] is True
    assert full_app_res.json()["approval_date"] is not None


def test_consolidation_failure_handling(client: TestClient) -> None:
    """Verify robust error envelopes for invalid inputs and missing documents."""
    # 1. Non-existent document ID -> 404
    missing_res = client.post(
        "/api/v1/profiles/consolidate",
        json={"document_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND
    assert missing_res.json()["status"] == "error"

    # 2. Document with failed extraction -> 400 DOCUMENTS_NOT_READY
    from app.database import get_db
    import uuid

    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)
    failed_doc_id = str(uuid.uuid4())
    doc = Document(
        id=failed_doc_id,
        filename="corrupted.pdf",
        file_format="pdf",
        file_size=100,
        file_hash="corrupt_hash",
        storage_path="storage/corrupt.pdf",
        status="failed",
        error_message="Corrupted file",
    )
    db.add(doc)
    db.commit()

    failed_res = client.post(
        "/api/v1/profiles/consolidate",
        json={"document_ids": [failed_doc_id]},
    )
    assert failed_res.status_code == status.HTTP_400_BAD_REQUEST
    assert failed_res.json()["error"]["code"] == "DOCUMENTS_NOT_READY"

    # 3. Empty document list -> 422 validation error
    empty_res = client.post("/api/v1/profiles/consolidate", json={"document_ids": []})
    assert empty_res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # 4. More than 10 documents -> 422 validation error
    too_many_ids = [str(uuid.uuid4()) for _ in range(11)]
    too_many_res = client.post("/api/v1/profiles/consolidate", json={"document_ids": too_many_ids})
    assert too_many_res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # 5. Non-existent profile -> 404
    missing_prof_res = client.get("/api/v1/profiles/00000000-0000-0000-0000-000000000000")
    assert missing_prof_res.status_code == status.HTTP_404_NOT_FOUND


def test_profile_items_crud_and_listing(client: TestClient) -> None:
    """Test creating, listing, adding items (experience, education, skill, cert, project), and deleting."""
    resume_text = """
    Alice Walker
    alice@example.com | 555-333-4444
    ## Work Experience
    Engineer at TechCorp | 2020 - 2022
    """
    doc_id = _create_mock_document(client, "alice.pdf", resume_text)
    init_res = client.post("/api/v1/profiles/consolidate", json={"document_ids": [doc_id]})
    assert init_res.status_code == status.HTTP_201_CREATED
    profile_id = init_res.json()["id"]

    # List profiles
    list_res = client.get("/api/v1/profiles")
    assert list_res.status_code == status.HTTP_200_OK
    assert any(p["id"] == profile_id for p in list_res.json())

    # Add experience
    exp_res = client.post(f"/api/v1/profiles/{profile_id}/experiences", json={
        "company": "NextGen AI",
        "job_title": "Senior AI Architect",
        "start_date": "2023",
        "is_current": True,
        "skills_used": ["Python", "PyTorch"],
    })
    assert exp_res.status_code == status.HTTP_201_CREATED
    exp_id = exp_res.json()["id"]

    # Delete experience
    del_exp = client.delete(f"/api/v1/profiles/{profile_id}/experiences/{exp_id}")
    assert del_exp.status_code == status.HTTP_204_NO_CONTENT

    # Add education
    edu_res = client.post(f"/api/v1/profiles/{profile_id}/education", json={
        "institution": "Stanford University",
        "degree": "M.S.",
        "field_of_study": "Computer Science",
    })
    assert edu_res.status_code == status.HTTP_201_CREATED
    edu_id = edu_res.json()["id"]

    del_edu = client.delete(f"/api/v1/profiles/{profile_id}/education/{edu_id}")
    assert del_edu.status_code == status.HTTP_204_NO_CONTENT

    # Add skill
    sk_res = client.post(f"/api/v1/profiles/{profile_id}/skills", json={
        "name": "Kubernetes",
        "category": "Cloud & DevOps",
        "proficiency": "advanced",
    })
    assert sk_res.status_code == status.HTTP_201_CREATED
    sk_id = sk_res.json()["id"]

    del_sk = client.delete(f"/api/v1/profiles/{profile_id}/skills/{sk_id}")
    assert del_sk.status_code == status.HTTP_204_NO_CONTENT

    # Add certification
    cert_res = client.post(f"/api/v1/profiles/{profile_id}/certifications", json={
        "name": "AWS Certified Solutions Architect",
        "issuing_organization": "Amazon Web Services",
    })
    assert cert_res.status_code == status.HTTP_201_CREATED
    cert_id = cert_res.json()["id"]

    del_cert = client.delete(f"/api/v1/profiles/{profile_id}/certifications/{cert_id}")
    assert del_cert.status_code == status.HTTP_204_NO_CONTENT

    # Add project
    proj_res = client.post(f"/api/v1/profiles/{profile_id}/projects", json={
        "name": "AI Resume Engine",
        "subtitle": "Built agentic resume parser",
        "technologies": ["Python", "FastAPI"],
        "bullets": ["Designed extraction pipeline"],
    })
    assert proj_res.status_code == status.HTTP_201_CREATED
    assert len(proj_res.json()["projects"]) >= 1

    # Update project
    up_proj = client.patch(f"/api/v1/profiles/{profile_id}/projects/0", json={
        "name": "AI Resume Engine Pro",
        "subtitle": "Production grade resume system",
        "technologies": ["Python", "FastAPI", "React"],
        "bullets": ["Integrated full-stack features"],
    })
    assert up_proj.status_code == status.HTTP_200_OK

    # Delete project
    del_proj = client.delete(f"/api/v1/profiles/{profile_id}/projects/0")
    assert del_proj.status_code == status.HTTP_204_NO_CONTENT

    # Delete profile
    del_prof = client.delete(f"/api/v1/profiles/{profile_id}")
    assert del_prof.status_code == status.HTTP_204_NO_CONTENT

