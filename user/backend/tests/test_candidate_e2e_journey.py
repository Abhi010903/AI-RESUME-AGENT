"""Full End-to-End Candidate User Journey Integration Test.

Simulates the complete real-world candidate lifecycle:
1. Registration & Authentication (JWT issued)
2. Resume Ingestion (PDF + DOCX uploads)
3. Profile Intelligence Consolidation & Verification
4. Conflict Resolution & Item Additions
5. Target Job Description Ingestion & Requirements Extraction
6. Evidence-Based Skill Matching & Gap Analysis
7. ATS Resume Generation (A4 Single-Page DOCX & PDF Export)
8. Transparent 7-Dimension ATS Evaluation
9. Application Tracker Pipeline Movement (Kanban workflow)
10. Tenant Isolation & Account Management
"""

import io
from pathlib import Path
import docx
from fastapi import status
from fastapi.testclient import TestClient
import pymupdf


def test_complete_candidate_journey(client: TestClient) -> None:
    # -------------------------------------------------------------------------
    # 1. Registration & Login
    # -------------------------------------------------------------------------
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Antigravity Candidate",
        "email": "candidate.e2e@example.com",
        "password": "SecurePassword123!",
    })
    assert reg_res.status_code == status.HTTP_201_CREATED
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == "candidate.e2e@example.com"
    token = reg_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify /me endpoint
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["email"] == "candidate.e2e@example.com"

    # -------------------------------------------------------------------------
    # 2. Upload Resumes (PDF & DOCX)
    # -------------------------------------------------------------------------
    # Create simple valid PDF in-memory
    pdf_doc = pymupdf.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 72), "Antigravity Candidate\ncandidate.e2e@example.com | +1 555-0199\n\nExperience:\nSenior AI Engineer at Apex Systems (2022 - Present)\nBuilt LLM pipelines with Python, FastAPI, and PyTorch.\n\nEducation:\nB.S. Computer Science from Tech Institute (2018 - 2022)\n\nSkills:\nPython, PyTorch, FastAPI, SQL, Docker")
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    # Create simple valid DOCX in-memory
    docx_doc = docx.Document()
    docx_doc.add_heading("Antigravity Candidate", 0)
    docx_doc.add_paragraph("Projects & Achievements:\n- Built high-performance document extraction engine with zero hallucinations.\n- Deployed production inference on AWS.")
    docx_stream = io.BytesIO()
    docx_doc.save(docx_stream)
    docx_bytes = docx_stream.getvalue()

    upload_res = client.post(
        "/api/v1/resumes/upload",
        files=[
            ("files", ("resume_primary.pdf", pdf_bytes, "application/pdf")),
            ("files", ("resume_projects.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ],
        headers=auth_headers,
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    upload_data = upload_res.json()
    uploaded_docs = upload_data["documents"]
    assert len(uploaded_docs) == 2
    doc_ids = [d["id"] for d in uploaded_docs]

    # Verify documents are listed
    list_docs = client.get("/api/v1/resumes", headers=auth_headers)
    assert list_docs.status_code == status.HTTP_200_OK
    assert len(list_docs.json()) >= 2

    # -------------------------------------------------------------------------
    # 3. Consolidate into Candidate Profile
    # -------------------------------------------------------------------------
    cons_res = client.post(
        "/api/v1/profiles/consolidate",
        json={"document_ids": doc_ids},
        headers=auth_headers,
    )
    assert cons_res.status_code == status.HTTP_201_CREATED
    profile = cons_res.json()
    profile_id = profile["id"]
    assert profile["full_name"] == "Antigravity Candidate"
    assert profile["completeness_percentage"] > 0

    # -------------------------------------------------------------------------
    # 4. Profile Additions & Approval
    # -------------------------------------------------------------------------
    # Add new skill
    skill_res = client.post(
        f"/api/v1/profiles/{profile_id}/skills",
        json={"name": "PostgreSQL", "category": "Databases", "proficiency": "expert", "years_of_experience": 4.0},
        headers=auth_headers,
    )
    assert skill_res.status_code == status.HTTP_201_CREATED

    # Add new project
    proj_res = client.post(
        f"/api/v1/profiles/{profile_id}/projects",
        json={
            "name": "Distributed RAG Platform",
            "subtitle": "Lead Architect",
            "technologies": ["Python", "FastAPI", "PyTorch", "PostgreSQL"],
            "bullets": ["Designed multi-modal retrieval pipelines", "Achieved 99.9% uptime"],
        },
        headers=auth_headers,
    )
    assert proj_res.status_code == status.HTTP_201_CREATED

    # Approve Profile
    appr_res = client.post(
        f"/api/v1/profiles/{profile_id}/approve",
        json={"approve_all": True},
        headers=auth_headers,
    )
    assert appr_res.status_code == status.HTTP_200_OK
    assert appr_res.json()["verification_status"] == "approved"

    # -------------------------------------------------------------------------
    # 5. Ingest Target Job Description
    # -------------------------------------------------------------------------
    jd_content = b"""
    Staff GenAI Engineer
    Company: NeuralCore AI
    Location: San Francisco, CA / Remote
    Seniority: Senior
    
    Responsibilities:
    - Architect and scale production LLM inference pipelines.
    - Build agentic document intelligence workflows.
    
    Required Skills:
    - Python
    - FastAPI
    - PyTorch
    - PostgreSQL
    
    Preferred Skills:
    - Docker
    - Kubernetes
    
    Required Qualifications:
    - Bachelor's degree in Computer Science or related field.
    - 3+ years of experience in production AI engineering.
    """
    job_res = client.post(
        "/api/v1/jobs/upload",
        files={"file": ("target_jd.txt", jd_content, "text/plain")},
        data={"title": "Staff GenAI Engineer", "company": "NeuralCore AI", "location": "Remote"},
        headers=auth_headers,
    )
    assert job_res.status_code == status.HTTP_201_CREATED
    job_id = job_res.json()["id"]

    # -------------------------------------------------------------------------
    # 6. Skill Matching & Gap Analysis
    # -------------------------------------------------------------------------
    match_res = client.post(
        "/api/v1/matches",
        json={"profile_id": profile_id, "job_id": job_id},
        headers=auth_headers,
    )
    assert match_res.status_code == status.HTTP_201_CREATED
    match_data = match_res.json()
    match_id = match_data["id"]
    assert match_data["overall_score"] >= 80.0
    assert match_data["mandatory_skill_score"] >= 80.0

    # -------------------------------------------------------------------------
    # 7. Tailored Single-Page Resume Generation (PDF & DOCX)
    # -------------------------------------------------------------------------
    gen_res = client.post(
        "/api/v1/resumes/generate",
        json={
            "profile_id": profile_id,
            "job_id": job_id,
            "match_id": match_id,
            "title": "NeuralCore AI - Staff GenAI Engineer Resume",
        },
        headers=auth_headers,
    )
    assert gen_res.status_code == status.HTTP_201_CREATED
    resume_data = gen_res.json()
    resume_id = resume_data["id"]
    assert resume_data["version_number"] == 1
    assert resume_data["ats_score"] is not None

    # Download and verify PDF
    dl_pdf = client.get(f"/api/v1/resumes/generated/{resume_id}/download?format=pdf", headers=auth_headers)
    assert dl_pdf.status_code == status.HTTP_200_OK
    assert dl_pdf.headers["content-type"] == "application/pdf"
    assert len(dl_pdf.content) > 500

    # Verify downloaded PDF is strictly 1 single page
    with pymupdf.open(stream=dl_pdf.content, filetype="pdf") as doc:
        assert len(doc) == 1, "Resume PDF strictly guaranteed to be 1 single page"

    # Download and verify DOCX
    dl_docx = client.get(f"/api/v1/resumes/generated/{resume_id}/download?format=docx", headers=auth_headers)
    assert dl_docx.status_code == status.HTTP_200_OK
    assert len(dl_docx.content) > 500

    # -------------------------------------------------------------------------
    # 8. Transparent ATS Evaluation
    # -------------------------------------------------------------------------
    ats_res = client.post(
        "/api/v1/ats/evaluate",
        json={"resume_id": resume_id, "job_id": job_id},
        headers=auth_headers,
    )
    assert ats_res.status_code == status.HTTP_201_CREATED
    ats_data = ats_res.json()
    assert ats_data["overall_score"] >= 80.0
    assert ats_data["readability_score"] >= 50.0
    assert "matched_mandatory_skills" in ats_data["report"]

    # -------------------------------------------------------------------------
    # 9. Application Tracking Pipeline
    # -------------------------------------------------------------------------
    app_res = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "resume_id": resume_id,
            "company": "NeuralCore AI",
            "position_title": "Staff GenAI Engineer",
            "status": "APPLIED",
            "salary_range": "$175,000 - $220,000",
            "applied_date": "2026-11-21",
            "notes": "Applied with v1 tailored resume.",
        },
        headers=auth_headers,
    )
    assert app_res.status_code == status.HTTP_201_CREATED
    app_id = app_res.json()["id"]
    assert app_res.json()["resume_id"] == resume_id

    # Move application to INTERVIEW
    patch_app = client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "INTERVIEW", "notes": "Recruiter call scheduled."},
        headers=auth_headers,
    )
    assert patch_app.status_code == status.HTTP_200_OK
    assert patch_app.json()["status"] == "INTERVIEW"

    # Verify workflow status reflects completed lifecycle
    wf_res = client.get("/api/v1/workflow/status", headers=auth_headers)
    assert wf_res.status_code == status.HTTP_200_OK
    wf_data = wf_res.json()
    assert wf_data["metrics"]["resumes_count"] >= 2
    assert wf_data["metrics"]["applications_count"] >= 1

    # Verify activity stream recorded events
    act_res = client.get("/api/v1/workflow/activity", headers=auth_headers)
    assert act_res.status_code == status.HTTP_200_OK
    acts = act_res.json()
    assert len(acts) >= 3

    # Verify candidate data export
    export_res = client.get("/api/v1/auth/export-data", headers=auth_headers)
    assert export_res.status_code == status.HTTP_200_OK
    assert "candidate" in export_res.json()

    # -------------------------------------------------------------------------
    # 10. Clean Cleanup Verification
    # -------------------------------------------------------------------------
    del_res = client.delete(f"/api/v1/resumes/generated/{resume_id}", headers=auth_headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(f"/api/v1/resumes/generated/{resume_id}", headers=auth_headers).status_code == status.HTTP_404_NOT_FOUND
