"""Unit and API tests for Stage 6 — Transparent 7-Dimension ATS Evaluation Engine.

Covers:
- ATS evaluation execution via POST /api/v1/ats/evaluate
- Scoring transparency across all 7 dimensions
- Matched and missing mandatory/preferred skill reporting
- Keyword relevance and keyword stuffing detection
- Document structure and parsability checks
- Readability scoring
- Report retrieval by ID via GET /api/v1/ats/reports/{id}
- Report list filtering via GET /api/v1/ats/reports
- 404 error cases
"""

import uuid
from fastapi import status
from fastapi.testclient import TestClient
from tests.test_generation import _create_sample_data


def test_ats_evaluate_endpoint(client: TestClient) -> None:
    """Test full ATS evaluation on a generated resume."""
    prof_id, job_id = _create_sample_data(client)

    # 1. Generate resume
    gen_res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    assert gen_res.status_code == status.HTTP_201_CREATED
    resume_id = gen_res.json()["id"]

    # 2. Evaluate resume
    eval_res = client.post("/api/v1/ats/evaluate", json={"resume_id": resume_id, "job_id": job_id})
    assert eval_res.status_code == status.HTTP_201_CREATED
    data = eval_res.json()

    assert data["resume_id"] == resume_id
    assert data["job_id"] == job_id
    assert 0.0 <= data["overall_score"] <= 100.0
    assert 0.0 <= data["mandatory_skill_score"] <= 100.0
    assert 0.0 <= data["preferred_skill_score"] <= 100.0
    assert 0.0 <= data["experience_score"] <= 100.0
    assert 0.0 <= data["education_score"] <= 100.0
    assert 0.0 <= data["keyword_score"] <= 100.0
    assert 0.0 <= data["structure_score"] <= 100.0
    assert 0.0 <= data["readability_score"] <= 100.0

    report = data["report"]
    assert "dimension_scores" in report
    assert "matched_mandatory_skills" in report
    assert "keyword_stuffing_warning" in report
    assert "actionable_recommendations" in report
    assert isinstance(report["actionable_recommendations"], list)


def test_get_and_list_ats_reports(client: TestClient) -> None:
    """Test fetching and listing ATS reports."""
    prof_id, job_id = _create_sample_data(client)
    gen_res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    resume_id = gen_res.json()["id"]

    eval_res = client.post("/api/v1/ats/evaluate", json={"resume_id": resume_id, "job_id": job_id})
    report_id = eval_res.json()["id"]

    # Get by ID
    get_res = client.get(f"/api/v1/ats/reports/{report_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == report_id

    # List reports
    list_res = client.get(f"/api/v1/ats/reports?resume_id={resume_id}")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) >= 1


def test_ats_evaluation_errors(client: TestClient) -> None:
    """Test 404 validation in ATS endpoints."""
    nonexistent = str(uuid.uuid4())
    prof_id, job_id = _create_sample_data(client)
    gen_res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    resume_id = gen_res.json()["id"]

    # Nonexistent resume
    r1 = client.post("/api/v1/ats/evaluate", json={"resume_id": nonexistent, "job_id": job_id})
    assert r1.status_code == status.HTTP_404_NOT_FOUND

    # Nonexistent job
    r2 = client.post("/api/v1/ats/evaluate", json={"resume_id": resume_id, "job_id": nonexistent})
    assert r2.status_code == status.HTTP_404_NOT_FOUND

    # Nonexistent report
    r3 = client.get(f"/api/v1/ats/reports/{nonexistent}")
    assert r3.status_code == status.HTTP_404_NOT_FOUND
