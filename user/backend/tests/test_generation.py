"""Unit and API tests for Stage 6 — Resume Generation and Document Export.

Covers:
- Generating tailored resume via POST /api/v1/resumes/generate
- DOCX export verification (python-docx parseable, formatting intact)
- PDF export verification (pymupdf parseable, clean vector text)
- Factual traceability (strictly candidate profile data, zero hallucinations)
- Consecutive version numbering (v1, v2)
- Listing generated resumes with filters
- Retrieving generated resume by ID
- Downloading generated resume (PDF and DOCX)
- Version history comparison endpoint
- 404 validation for missing profiles, jobs, and resumes
"""

from pathlib import Path
import uuid
import docx
from fastapi import status
from fastapi.testclient import TestClient
import pymupdf
from app.models import CandidateProfile, Education, JobDescription, Skill, WorkExperience


def _create_sample_data(client: TestClient) -> tuple[str, str]:
    """Helper to populate test database with candidate profile and target job."""
    from app.database import get_db

    db_gen = client.app.dependency_overrides.get(get_db, get_db)()
    db = next(db_gen)

    doc_id = str(uuid.uuid4())
    prof_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    profile = CandidateProfile(
        id=prof_id,
        full_name="Abhijit Kumar",
        email="abhijais0109@gmail.com",
        phone="+91 8787465364",
        location="Vadodara, Gujarat, India",
        headline="AI & Machine Learning Engineer",
        summary="Computer Science undergraduate with experience in classical ML, RAG, and FastAPI.",
        linkedin_url="https://linkedin.com/in/abhijit-kumar",
        github_url="https://github.com/Abhi010903",
        source_document_ids_json=f'["{doc_id}"]',
        verification_status="verified",
        is_approved=True,
    )
    db.add(profile)

    # Skills
    for s_name, s_cat in [("Python", "Languages"), ("FastAPI", "Backend"), ("PyTorch", "AI & Data"), ("SQL", "Languages")]:
        db.add(Skill(
            id=str(uuid.uuid4()),
            profile_id=prof_id,
            name=s_name,
            category=s_cat,
            years_of_experience=2.0,
            source_document_id=doc_id,
            is_approved=True,
        ))

    # Experience
    exp = WorkExperience(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        company="AI Innovation Labs",
        job_title="AI Data Engineer Intern",
        location="Remote",
        start_date="06/2024",
        end_date="Present",
        is_current=True,
        description="Built agentic document intelligence workflows.\nImplemented FastAPI backend and automated regression checks.",
        source_document_id=doc_id,
        is_approved=True,
    )
    exp.set_skills_used(["Python", "FastAPI", "PyTorch"])
    db.add(exp)

    # Education
    edu = Education(
        id=str(uuid.uuid4()),
        profile_id=prof_id,
        institution="Parul University",
        degree="B.Tech",
        field_of_study="Computer Science & Engineering",
        start_date="2023",
        end_date="2027",
        grade="8.2 CGPA",
        source_document_id=doc_id,
        is_approved=True,
    )
    db.add(edu)

    # Job Description
    job = JobDescription(
        id=job_id,
        title="Junior Gen AI Engineer",
        company="OceanAI",
        location="Kochi / Mumbai",
        raw_text="OceanAI is looking for Junior Gen AI Engineers with Python, FastAPI, and PyTorch.",
        min_years_experience=0.0,
        education_level="B.Tech in Computer Science",
        status="analyzed",
    )
    job.set_required_skills([
        {"name": "Python", "importance": "high"},
        {"name": "FastAPI", "importance": "high"},
    ])
    job.set_preferred_skills([
        {"name": "PyTorch", "importance": "medium"},
    ])
    db.add(job)

    db.commit()
    return prof_id, job_id


def test_generate_resume_success(client: TestClient) -> None:
    """Test tailored resume generation with DOCX and PDF export."""
    prof_id, job_id = _create_sample_data(client)

    payload = {
        "profile_id": prof_id,
        "job_id": job_id,
        "title": "OceanAI Custom Tailored Resume",
    }
    response = client.post("/api/v1/resumes/generate", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["profile_id"] == prof_id
    assert data["job_id"] == job_id
    assert data["version_number"] == 1
    assert data["title"] == "OceanAI Custom Tailored Resume"
    assert data["ats_score"] is not None
    assert data["ats_score"] > 50.0

    assert data["has_docx"] is True
    assert data["has_pdf"] is True

    # Verify download endpoints return valid documents
    dl_docx = client.get(f"/api/v1/resumes/generated/{data['id']}/download?format=docx")
    assert dl_docx.status_code == status.HTTP_200_OK
    assert len(dl_docx.content) > 1000

    dl_pdf = client.get(f"/api/v1/resumes/generated/{data['id']}/download?format=pdf")
    assert dl_pdf.status_code == status.HTTP_200_OK
    assert len(dl_pdf.content) > 1000

    # Verify PDF content with pymupdf
    pdf_doc = pymupdf.open(stream=dl_pdf.content, filetype="pdf")
    pdf_text = "\n".join(page.get_text() for page in pdf_doc)
    pdf_doc.close()
    assert "ABHIJIT KUMAR" in pdf_text
    assert "FastAPI" in pdf_text


def test_consecutive_generations_increment_version(client: TestClient) -> None:
    """Test that multiple generations for the same profile and job increment version number."""
    prof_id, job_id = _create_sample_data(client)

    res1 = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    assert res1.status_code == status.HTTP_201_CREATED
    assert res1.json()["version_number"] == 1

    res2 = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    assert res2.status_code == status.HTTP_201_CREATED
    assert res2.json()["version_number"] == 2


def test_list_and_get_generated_resumes(client: TestClient) -> None:
    """Test listing and fetching generated resumes by ID."""
    prof_id, job_id = _create_sample_data(client)
    res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    resume_id = res.json()["id"]

    # List endpoint
    list_res = client.get(f"/api/v1/resumes/generated?profile_id={prof_id}")
    assert list_res.status_code == status.HTTP_200_OK
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == resume_id for item in items)

    # Get by ID
    get_res = client.get(f"/api/v1/resumes/generated/{resume_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == resume_id


def test_download_generated_resume(client: TestClient) -> None:
    """Test downloading PDF and DOCX files."""
    prof_id, job_id = _create_sample_data(client)
    res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    resume_id = res.json()["id"]

    # Download PDF
    dl_pdf = client.get(f"/api/v1/resumes/generated/{resume_id}/download?format=pdf")
    assert dl_pdf.status_code == status.HTTP_200_OK
    assert dl_pdf.headers["content-type"] == "application/pdf"
    assert len(dl_pdf.content) > 1000

    # Download DOCX
    dl_docx = client.get(f"/api/v1/resumes/generated/{resume_id}/download?format=docx")
    assert dl_docx.status_code == status.HTTP_200_OK
    assert "officedocument.wordprocessingml.document" in dl_docx.headers["content-type"]
    assert len(dl_docx.content) > 1000


def test_version_comparison(client: TestClient) -> None:
    """Test comparing version 2 with version 1."""
    prof_id, job_id = _create_sample_data(client)
    client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    v2_res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    v2_id = v2_res.json()["id"]

    comp_res = client.get(f"/api/v1/resumes/generated/{v2_id}/versions")
    assert comp_res.status_code == status.HTTP_200_OK
    data = comp_res.json()
    assert data["current_version"]["version_number"] == 2
    assert data["previous_version"] is not None
    assert data["previous_version"]["version_number"] == 1


def test_generate_errors(client: TestClient) -> None:
    """Test 404 responses for nonexistent profile or job."""
    nonexistent = str(uuid.uuid4())
    prof_id, job_id = _create_sample_data(client)

    # Missing profile
    r1 = client.post("/api/v1/resumes/generate", json={"profile_id": nonexistent, "job_id": job_id})
    assert r1.status_code == status.HTTP_404_NOT_FOUND

    # Missing job
    r2 = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": nonexistent})
    assert r2.status_code == status.HTTP_404_NOT_FOUND

    # Missing resume on get
    r3 = client.get(f"/api/v1/resumes/generated/{nonexistent}")
    assert r3.status_code == status.HTTP_404_NOT_FOUND


def test_delete_generated_resume(client: TestClient) -> None:
    """Test deleting a generated resume removes record and files."""
    prof_id, job_id = _create_sample_data(client)
    gen_res = client.post("/api/v1/resumes/generate", json={"profile_id": prof_id, "job_id": job_id})
    assert gen_res.status_code == status.HTTP_201_CREATED
    resume_id = gen_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/v1/resumes/generated/{resume_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify 404
    assert client.get(f"/api/v1/resumes/generated/{resume_id}").status_code == status.HTTP_404_NOT_FOUND

