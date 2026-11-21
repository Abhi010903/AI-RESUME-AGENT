"""Combined end-to-end integration tests connecting Stages 1, 2, 3, 4, and 5.

Flow:
1. Document Ingestion & Extraction (Stage 2)
2. Profile Intelligence & Consolidation (Stage 3)
3. Conflict Resolution & Profile Approval (Stage 3)
4. Job Description Intelligence & Requirement Normalization (Stage 4)
5. Evidence-Based Skill Matching Engine (Stage 5)
6. Traceability Verification back to source documents
7. Score Breakdown & Gap Analysis Inspection
"""

import io
from fastapi import status
from fastapi.testclient import TestClient


def test_full_platform_end_to_end_workflow(client: TestClient) -> None:
    """Test full multi-stage pipeline from document upload to profile matching."""
    # =========================================================================
    # Step 1: Upload Multiple Resumes (Stage 2)
    # =========================================================================
    # Create valid mock PDF byte stream
    import pymupdf

    # Resume 1: Backend & Python experience
    doc1 = pymupdf.open()
    page1 = doc1.new_page()
    page1.insert_text(
        (50, 50),
        """
        Alex Mercer
        alex.mercer@example.com | +1 555-0144 | San Francisco, CA
        https://linkedin.com/in/alexmercer | https://github.com/alexmercer

        Summary:
        Senior Software Engineer specializing in backend systems, distributed architectures, and APIs.

        Work Experience:
        Staff Software Engineer at Apex Cloud
        2021-01 - Present
        Architected high-scale REST APIs using Python and FastAPI.
        Optimized PostgreSQL database performance and managed Docker containers.

        Senior Developer at DataWave
        2018-06 - 2020-12
        Built backend data pipelines using Python, Django, and Redis.

        Education:
        B.S. in Computer Science at UC Berkeley
        2014 - 2018

        Skills:
        Python, FastAPI, Django, PostgreSQL, Docker, Redis, REST APIs, Git

        Certifications:
        AWS Certified Solutions Architect
        Amazon Web Services | 2022
        """,
    )
    pdf_bytes1 = doc1.tobytes()
    doc1.close()

    upload_res1 = client.post(
        "/api/v1/resumes/upload",
        files=[("files", ("alex_mercer_resume.pdf", io.BytesIO(pdf_bytes1), "application/pdf"))],
    )
    assert upload_res1.status_code == status.HTTP_201_CREATED
    doc_id1 = upload_res1.json()["documents"][0]["id"]

    # =========================================================================
    # Step 2: Consolidate Candidate Profile (Stage 3)
    # =========================================================================
    cons_res = client.post(
        "/api/v1/profiles/consolidate",
        json={"document_ids": [doc_id1]},
    )
    assert cons_res.status_code == status.HTTP_201_CREATED
    profile_data = cons_res.json()
    profile_id = profile_data["id"]

    assert profile_data["full_name"] == "Alex Mercer"
    assert profile_data["email"] == "alex.mercer@example.com"
    assert len(profile_data["experiences"]) >= 2
    assert len(profile_data["skills"]) >= 4
    assert len(profile_data["education"]) >= 1

    # Verify source document traceability in profile entities
    skill_doc_ids = [s["source_document_id"] for s in profile_data["skills"]]
    assert all(d_id == doc_id1 for d_id in skill_doc_ids)

    # =========================================================================
    # Step 3: Candidate Review, Conflict Resolution & Approval (Stage 3)
    # =========================================================================
    # If any conflict exists, resolve it
    if profile_data["conflicts"]:
        conf_id = profile_data["conflicts"][0]["id"]
        res_conflict = client.post(
            f"/api/v1/profiles/{profile_id}/conflicts/{conf_id}",
            json={"resolution_status": "resolved", "resolution_notes": "Verified dates directly with Alex."},
        )
        assert res_conflict.status_code == status.HTTP_200_OK

    # Approve profile
    appr_res = client.post(
        f"/api/v1/profiles/{profile_id}/approve",
        json={"approve_all": True},
    )
    assert appr_res.status_code == status.HTTP_200_OK
    assert appr_res.json()["is_approved"] is True

    # =========================================================================
    # Step 4: Job Description Ingestion & Intelligence (Stage 4)
    # =========================================================================
    jd_text = """
    Principal Backend Engineer
    Company: ScaleTech Dynamics
    Location: Remote
    Employment Type: Full-time

    About ScaleTech:
    We are scaling our core platform and looking for a Principal Backend Engineer.

    Key Responsibilities:
    - Lead backend API design and architecture.
    - Scale PostgreSQL relational storage and distributed caching.
    - Drive best engineering practices across backend teams.

    Requirements:
    - At least 5 years of software development experience.
    - Must have deep production expertise with Python, FastAPI, and PostgreSQL.
    - Bachelor's degree in Computer Science or related technical discipline.
    - Strong understanding of Docker and containerization.

    Preferred Qualifications:
    - Experience with Kubernetes is a plus.
    - AWS Certified Solutions Architect is desirable.
    - Familiarity with Go or Rust.
    """

    job_res = client.post("/api/v1/jobs/analyze", json={"raw_text": jd_text})
    assert job_res.status_code == status.HTTP_201_CREATED
    job_data = job_res.json()
    job_id = job_data["id"]

    assert job_data["title"] == "Principal Backend Engineer"
    assert job_data["company"] == "ScaleTech Dynamics"
    assert job_data["min_years_experience"] == 5.0
    req_skill_names = [s["name"] for s in job_data["required_skills"]]
    pref_skill_names = [s["name"] for s in job_data["preferred_skills"]]

    assert "Python" in req_skill_names
    assert "FastAPI" in req_skill_names
    assert "PostgreSQL" in req_skill_names
    assert "Docker" in req_skill_names
    assert "Kubernetes" in pref_skill_names

    # =========================================================================
    # Step 5: Evidence-Based Skill Matching Engine (Stage 5)
    # =========================================================================
    match_res = client.post("/api/v1/matches", json={"profile_id": profile_id, "job_id": job_id})
    assert match_res.status_code == status.HTTP_201_CREATED
    match_data = match_res.json()
    match_id = match_data["id"]

    # Verify score components
    assert match_data["overall_score"] >= 80.0
    assert match_data["mandatory_skill_score"] >= 90.0  # Alex has Python, FastAPI, PostgreSQL, Docker
    assert match_data["experience_score"] == 100.0  # ~6 years experience vs 5 required
    assert match_data["education_score"] == 100.0  # B.S. in CS
    assert match_data["certification_score"] == 100.0  # AWS Certified Solutions Architect

    # =========================================================================
    # Step 6: Requirement-Level Traceability Verification
    # =========================================================================
    reqs_res = client.get(f"/api/v1/matches/{match_id}/requirements")
    assert reqs_res.status_code == status.HTTP_200_OK
    req_items = reqs_res.json()["requirements"]

    req_map = {r["requirement_name"]: r for r in req_items}

    # Verify direct match and source document preservation
    python_eval = req_map["Python"]
    assert python_eval["match_status"] == "STRONG_MATCH"
    assert python_eval["source_document_id"] == doc_id1

    fastapi_eval = req_map["FastAPI"]
    assert fastapi_eval["match_status"] == "STRONG_MATCH"
    assert fastapi_eval["source_document_id"] == doc_id1

    # Kubernetes is preferred; Alex has Docker, so it's a RELATED_MATCH (transferable)
    k8s_eval = req_map["Kubernetes"]
    assert k8s_eval["match_status"] == "RELATED_MATCH"
    assert k8s_eval["matched_candidate_skill"] == "Docker"

    # Rust is preferred and completely absent from Alex's profile (NO_EVIDENCE)
    rust_eval = req_map["Rust"]
    assert rust_eval["match_status"] == "NO_EVIDENCE"
    assert rust_eval["source_document_id"] is None

    # =========================================================================
    # Step 7: Score Breakdown and Gap Analysis Inspection
    # =========================================================================
    score_res = client.get(f"/api/v1/matches/{match_id}/score")
    assert score_res.status_code == status.HTTP_200_OK
    score_info = score_res.json()
    assert "mandatory_skills" in score_info["weights"]
    assert score_info["evidence_coverage"] >= 0.6
    assert "alignment indicator" in score_info["disclaimer"].lower()

    gaps_res = client.get(f"/api/v1/matches/{match_id}/gaps")
    assert gaps_res.status_code == status.HTTP_200_OK
    gaps_info = gaps_res.json()
    assert gaps_info["total_gaps"] >= 1
    # Kubernetes is present under related_transferable_skills (via Docker)
    assert any(g["requirement_name"] == "Kubernetes" for g in gaps_info["related_transferable_skills"])
    # Rust is present under missing_preferred_skills (NO_EVIDENCE)
    assert any(g["requirement_name"] == "Rust" for g in gaps_info["missing_preferred_skills"])
    # No missing mandatory skills for this strong candidate
    assert len(gaps_info["missing_mandatory_skills"]) == 0
