"""Security tests for Multi-Tenant Data Isolation and IDOR Prevention (Stage 7).

Covers:
- Tenant data isolation across candidate resources
- Inability for User B to read User A's generated resume (IDOR rejected with 404)
- Inability for User B to download User A's generated PDF/DOCX files
- Inability for User B to access User A's resume version comparison
- Inability for User B to evaluate or access User A's ATS reports
- Verification that User A has full normal access to own resources
"""

from fastapi import status
from fastapi.testclient import TestClient
from tests.test_generation import _create_sample_data


def test_tenant_isolation_and_idor_prevention(client: TestClient) -> None:
    """Verify that User B cannot access, download, or evaluate User A's resume resources."""
    # 1. Register User A
    user_a_res = client.post("/api/v1/auth/register", json={
        "email": "candidate_a@example.com",
        "password": "PasswordUserA123!",
        "full_name": "Candidate A",
    })
    assert user_a_res.status_code == status.HTTP_201_CREATED
    token_a = user_a_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_res = client.post("/api/v1/auth/register", json={
        "email": "candidate_b@example.com",
        "password": "PasswordUserB123!",
        "full_name": "Candidate B",
    })
    assert user_b_res.status_code == status.HTTP_201_CREATED
    token_b = user_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A generates a resume
    prof_id, job_id = _create_sample_data(client)
    gen_res = client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": prof_id, "job_id": job_id},
        headers=headers_a,
    )
    assert gen_res.status_code == status.HTTP_201_CREATED
    resume_a_id = gen_res.json()["id"]

    # 4. User A can access their own resume
    get_a = client.get(f"/api/v1/resumes/generated/{resume_a_id}", headers=headers_a)
    assert get_a.status_code == status.HTTP_200_OK

    # 5. User B attempts to access User A's resume -> IDOR blocked (404)
    get_b = client.get(f"/api/v1/resumes/generated/{resume_a_id}", headers=headers_b)
    assert get_b.status_code == status.HTTP_404_NOT_FOUND

    # 6. User B attempts to download User A's resume PDF/DOCX -> IDOR blocked (404)
    dl_pdf_b = client.get(f"/api/v1/resumes/generated/{resume_a_id}/download?format=pdf", headers=headers_b)
    assert dl_pdf_b.status_code == status.HTTP_404_NOT_FOUND

    dl_docx_b = client.get(f"/api/v1/resumes/generated/{resume_a_id}/download?format=docx", headers=headers_b)
    assert dl_docx_b.status_code == status.HTTP_404_NOT_FOUND

    # 7. User B attempts to view User A's resume versions -> IDOR blocked (404)
    ver_b = client.get(f"/api/v1/resumes/generated/{resume_a_id}/versions", headers=headers_b)
    assert ver_b.status_code == status.HTTP_404_NOT_FOUND

    # 8. User B attempts to evaluate User A's resume -> IDOR blocked (404)
    eval_b = client.post(
        "/api/v1/ats/evaluate",
        json={"resume_id": resume_a_id, "job_id": job_id},
        headers=headers_b,
    )
    assert eval_b.status_code == status.HTTP_404_NOT_FOUND

    # 9. User A can evaluate their own resume
    eval_a = client.post(
        "/api/v1/ats/evaluate",
        json={"resume_id": resume_a_id, "job_id": job_id},
        headers=headers_a,
    )
    assert eval_a.status_code == status.HTTP_201_CREATED
    report_a_id = eval_a.json()["id"]

    # 10. User B attempts to get User A's ATS report -> IDOR blocked (404)
    rep_b = client.get(f"/api/v1/ats/reports/{report_a_id}", headers=headers_b)
    assert rep_b.status_code == status.HTTP_404_NOT_FOUND

    # 11. Anonymous user cannot access User A's resume or reports
    anon_get = client.get(f"/api/v1/resumes/generated/{resume_a_id}")
    assert anon_get.status_code == status.HTTP_404_NOT_FOUND

    anon_dl = client.get(f"/api/v1/resumes/generated/{resume_a_id}/download?format=pdf")
    assert anon_dl.status_code == status.HTTP_404_NOT_FOUND

    anon_eval = client.post("/api/v1/ats/evaluate", json={"resume_id": resume_a_id, "job_id": job_id})
    assert anon_eval.status_code == status.HTTP_404_NOT_FOUND

    anon_rep = client.get(f"/api/v1/ats/reports/{report_a_id}")
    assert anon_rep.status_code == status.HTTP_404_NOT_FOUND

    # 12. User A can retrieve their own report
    rep_a = client.get(f"/api/v1/ats/reports/{report_a_id}", headers=headers_a)
    assert rep_a.status_code == status.HTTP_200_OK
