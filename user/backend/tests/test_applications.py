"""Unit and API tests for Job Application Tracking (Pipeline & Kanban)."""

import uuid
from fastapi import status
from fastapi.testclient import TestClient


def test_create_and_get_job_application(client: TestClient) -> None:
    """Test creating and retrieving a tracked job application."""
    payload = {
        "company": "Anthropic",
        "position_title": "AI Alignment Researcher",
        "job_url": "https://anthropic.com/careers/alignment",
        "location": "San Francisco, CA / Remote",
        "salary_range": "$180,000 - $240,000",
        "status": "APPLIED",
        "applied_date": "2026-11-20",
        "notes": "Referred via network.",
        "interviews": [
            {
                "stage": "Recruiter Screen",
                "scheduled_at": "2026-11-25T15:00:00Z",
                "completed": False,
                "notes": "Discuss ML background",
            }
        ],
    }

    res = client.post("/api/v1/applications", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["id"] is not None
    assert data["company"] == "Anthropic"
    assert data["position_title"] == "AI Alignment Researcher"
    assert data["status"] == "APPLIED"
    assert len(data["interviews"]) == 1
    assert data["interviews"][0]["stage"] == "Recruiter Screen"

    app_id = data["id"]
    get_res = client.get(f"/api/v1/applications/{app_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == app_id


def test_list_and_filter_applications(client: TestClient) -> None:
    """Test listing applications with status and keyword filters."""
    # Create two applications
    client.post("/api/v1/applications", json={
        "company": "Google DeepMind",
        "position_title": "Research Scientist",
        "status": "INTERVIEWING",
    })
    client.post("/api/v1/applications", json={
        "company": "OpenAI",
        "position_title": "Software Engineer",
        "status": "SAVED",
    })

    # List all
    all_res = client.get("/api/v1/applications")
    assert all_res.status_code == status.HTTP_200_OK
    assert len(all_res.json()) >= 2

    # Filter by status
    status_res = client.get("/api/v1/applications?status=INTERVIEWING")
    assert status_res.status_code == status.HTTP_200_OK
    assert all(a["status"] == "INTERVIEWING" for a in status_res.json())

    # Filter by search
    search_res = client.get("/api/v1/applications?search=DeepMind")
    assert search_res.status_code == status.HTTP_200_OK
    assert any(a["company"] == "Google DeepMind" for a in search_res.json())


def test_update_and_delete_application(client: TestClient) -> None:
    """Test updating application status and deleting."""
    res = client.post("/api/v1/applications", json={
        "company": "Cohere",
        "position_title": "NLP Engineer",
        "status": "SAVED",
    })
    app_id = res.json()["id"]

    # Update
    patch_res = client.patch(f"/api/v1/applications/{app_id}", json={
        "status": "OFFERED",
        "notes": "Offer received!",
    })
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["status"] == "OFFERED"
    assert patch_res.json()["notes"] == "Offer received!"

    # Delete
    del_res = client.delete(f"/api/v1/applications/{app_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify not found
    get_res = client.get(f"/api/v1/applications/{app_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND
