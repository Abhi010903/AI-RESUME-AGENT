"""Tests for Candidate Workflow Engine, Activity Logging, Stale Match Invalidation, and Data Export."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CandidateProfile, JobDescription, MatchResult, User
from app.services.activity_logger import record_activity


def _get_db(client: TestClient) -> Session:
    return next(client.app.dependency_overrides.get(get_db, get_db)())


def test_workflow_status_empty(client: TestClient):
    """Test workflow engine status when candidate has no data."""
    res = client.get("/api/v1/workflow/status")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "stages" in data
    assert len(data["stages"]) == 12
    assert "primary_action" in data
    assert data["primary_action"]["action_label"] == "Upload Resumes"
    assert data["primary_action"]["action_url"] == "/resumes"


def test_activity_feed_and_logging(client: TestClient):
    """Test recording and retrieving candidate activity events."""
    db = _get_db(client)
    record_activity(
        db=db,
        user_id=None,
        action="test_action",
        title="Test Activity Title",
        description="Testing activity logger",
        entity_type="test",
        entity_id="test-123",
    )

    res = client.get("/api/v1/workflow/activity?limit=10")
    assert res.status_code == 200
    activities = res.json()
    assert len(activities) >= 1
    assert any(a["title"] == "Test Activity Title" for a in activities)


def test_stale_match_invalidation_on_profile_update(client: TestClient):
    """Test that modifying a candidate profile automatically invalidates downstream match results."""
    db = _get_db(client)
    # Create profile
    profile = CandidateProfile(
        id="prof-stale-test",
        full_name="Stale Test Candidate",
        verification_status="approved",
        is_approved=True,
    )
    db.add(profile)

    # Create job
    job = JobDescription(
        id="job-stale-test",
        title="Test Engineer",
        raw_text="Required: Python, FastAPI",
    )
    db.add(job)

    # Create fresh match
    match = MatchResult(
        id="match-stale-test",
        profile_id=profile.id,
        job_id=job.id,
        overall_score=85.0,
        mandatory_skill_score=80.0,
        preferred_skill_score=90.0,
        experience_score=85.0,
        education_score=90.0,
        certification_score=80.0,
        score_breakdown_json="{}",
        requirement_matches_json="[]",
        gaps_json="[]",
        scoring_config_json="{}",
        is_stale=False,
    )
    db.add(match)
    db.commit()

    # Verify match is currently fresh
    assert match.is_stale is False

    # Update profile via API
    res = client.patch(f"/api/v1/profiles/{profile.id}", json={"headline": "Senior AI Architect"})
    assert res.status_code == 200

    # Refresh match from DB
    db.refresh(match)
    assert match.is_stale is True
    assert "updated" in (match.stale_reason or "").lower()


def test_stale_match_invalidation_on_job_update(client: TestClient):
    """Test that modifying a job description automatically invalidates downstream match results."""
    db = _get_db(client)
    # Create profile
    profile = CandidateProfile(
        id="prof-job-stale-test",
        full_name="Job Stale Candidate",
    )
    db.add(profile)

    # Create job
    job = JobDescription(
        id="job-update-stale-test",
        title="Backend Engineer",
        raw_text="Required: Go, Docker",
    )
    db.add(job)

    # Create fresh match
    match = MatchResult(
        id="match-job-stale-test",
        profile_id=profile.id,
        job_id=job.id,
        overall_score=78.0,
        mandatory_skill_score=75.0,
        preferred_skill_score=80.0,
        experience_score=70.0,
        education_score=85.0,
        certification_score=80.0,
        score_breakdown_json="{}",
        requirement_matches_json="[]",
        gaps_json="[]",
        scoring_config_json="{}",
        is_stale=False,
    )
    db.add(match)
    db.commit()

    # Update job via API
    res = client.patch(f"/api/v1/jobs/{job.id}", json={"title": "Staff Backend Engineer"})
    assert res.status_code == 200

    # Refresh match
    db.refresh(match)
    assert match.is_stale is True
    assert "Job description updated" in (match.stale_reason or "")


def test_export_data_endpoint(client: TestClient):
    """Test candidate data export JSON generation."""
    # Register candidate
    reg_payload = {
        "email": "export_test@example.com",
        "password": "Password123!",
        "full_name": "Export Test User",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]

    # Request export
    res = client.get("/api/v1/auth/export-data", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    export_json = res.json()
    assert "export_timestamp" in export_json
    assert export_json["candidate"]["email"] == "export_test@example.com"
    assert "profiles" in export_json
    assert "target_jobs" in export_json
    assert "job_applications" in export_json
    assert "recent_activity" in export_json
