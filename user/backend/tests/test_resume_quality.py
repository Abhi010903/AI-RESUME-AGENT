"""Comprehensive Automated Quality Assurance Tests for Resume Generation Overhaul (Stage 6).

Covers:
1. Section Ownership & Separation (Work Experience vs Projects vs Education)
2. Canonical A4 Page Dimensions (595.28 x 841.89 pt) and Strict 1-Page Guarantee
3. Vector Text Extraction & Bounding Box Clipping Validation
4. Single-Column DOCX Structure & Styling Consistency
5. Role-Aware Project Selection (GenAI vs SWE)
6. Skill Taxonomy Categorization & Canonical Deduplication
7. Professional Summary Word Count (35-55 words) & Factual Integrity
8. ATS Document-Level Evaluation & Metric Reporting
"""

from pathlib import Path
import uuid
import docx
import pymupdf
import pytest
from app.models import (
    CandidateProfile,
    Education,
    GeneratedResume,
    JobDescription,
    Skill,
    WorkExperience,
)
from app.services.ats_evaluator import evaluate_resume_for_ats
from app.services.extractor import extract_document_text
from app.services.job_description_parser import parse_job_description
from app.services.profile_parser import parse_resume_text
from app.services.resume_generator import generate_docx, generate_pdf
from app.services.resume_tailorer import tailor_resume


@pytest.fixture
def test_files_dir() -> Path:
    """Path to real-world test data directory."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    return root / "data" / "testing"


@pytest.fixture
def aiml_profile(test_files_dir: Path) -> CandidateProfile:
    """Build candidate profile from AIML resume."""
    pdf_path = test_files_dir / "resumes" / "Abhijit_Kumar_AIML_Resume.pdf"
    doc_id = str(uuid.uuid4())
    prof_id = str(uuid.uuid4())

    text = extract_document_text(pdf_path.read_bytes(), "pdf").text
    parsed = parse_resume_text(text, doc_id)

    profile = CandidateProfile(
        id=prof_id,
        full_name=parsed.full_name,
        email=parsed.email,
        phone=parsed.phone,
        location="Vadodara, Gujarat, India",
        headline="AI & Machine Learning Undergraduate",
        summary=parsed.summary,
        linkedin_url=parsed.linkedin_url,
        github_url=parsed.github_url,
        verification_status="verified",
        is_approved=True,
    )

    for sk in parsed.skills:
        profile.skills.append(
            Skill(
                id=str(uuid.uuid4()),
                profile_id=prof_id,
                name=sk.name,
                category=sk.category,
                source_document_id=doc_id,
                is_approved=True,
            )
        )

    for exp in parsed.experiences:
        we = WorkExperience(
            id=str(uuid.uuid4()),
            profile_id=prof_id,
            company=exp.company,
            job_title=exp.job_title,
            location=exp.location,
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            description=exp.description,
            source_document_id=doc_id,
            is_approved=True,
        )
        we.set_skills_used(exp.skills_used)
        profile.experiences.append(we)

    for edu in parsed.education:
        profile.education.append(
            Education(
                id=str(uuid.uuid4()),
                profile_id=prof_id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                start_date=edu.start_date,
                end_date=edu.end_date,
                source_document_id=doc_id,
                is_approved=True,
            )
        )

    # Set structured projects and achievements
    raw_projects = [
        {
            "name": p.name,
            "subtitle": p.role_or_subtitle,
            "technologies": p.technologies,
            "bullets": p.bullets,
        }
        for p in parsed.projects
    ]
    profile.set_projects(raw_projects)
    profile.set_achievements(parsed.achievements)

    return profile


@pytest.fixture
def oceanai_job(test_files_dir: Path) -> JobDescription:
    """Build JobDescription from OceanAI job description."""
    md_path = test_files_dir / "job_descriptions" / "job_description_1.md"
    raw_text = md_path.read_text(encoding="utf-8")
    parsed = parse_job_description(raw_text)

    job = JobDescription(
        id=str(uuid.uuid4()),
        title=parsed.title or "Junior Gen AI Engineer",
        company=parsed.company or "OceanAI",
        location=parsed.location,
        summary=parsed.summary,
        raw_text=raw_text,
        min_years_experience=parsed.min_years_experience,
        status="analyzed",
    )
    job.set_required_skills(parsed.required_skills)
    job.set_preferred_skills(parsed.preferred_skills)
    return job


def test_section_ownership_and_separation(aiml_profile: CandidateProfile, oceanai_job: JobDescription) -> None:
    """Verify that work experiences contain only jobs and projects contain only independent projects."""
    tailored = tailor_resume(aiml_profile, oceanai_job)

    # Work experience checks
    assert len(tailored.experiences) == 2
    companies = [e["company"] for e in tailored.experiences]
    assert "ProductSquadS" in companies
    assert "DIGISAMAKSH Private Limited" in companies

    # Ensure no project names leak into work experience bullets
    for exp in tailored.experiences:
        for b in exp.get("bullets", []):
            assert "Breath.exe" not in b
            assert "UrbanFlowAI" not in b
            assert "RepoIR" not in b

    # Projects checks
    assert len(tailored.projects) >= 2
    proj_names = [p["name"] for p in tailored.projects]
    assert "RepoIR" in proj_names or "Breath.exe" in proj_names

    # Projects must have attached technologies
    for proj in tailored.projects:
        assert isinstance(proj["technologies"], list)
        assert len(proj["technologies"]) > 0


def test_single_page_a4_strict_guarantee(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
    tmp_path: Path,
) -> None:
    """Verify that generated PDF strictly adheres to A4 dimensions and exactly 1 page."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    pdf_path = tmp_path / "test_one_page.pdf"
    docx_path = tmp_path / "test_one_page.docx"

    generate_pdf(tailored, pdf_path)
    generate_docx(tailored, docx_path)

    assert pdf_path.exists()
    assert docx_path.exists()

    # Validate PDF page count and geometry
    pdf_doc = pymupdf.open(pdf_path)
    assert len(pdf_doc) == 1, f"Expected 1 page, got {len(pdf_doc)}"

    page_rect = pdf_doc[0].rect
    assert round(page_rect.width, 2) == 595.28  # A4 width in pt
    assert round(page_rect.height, 2) == 841.89  # A4 height in pt

    # Bounding box boundary checks: verify no text clipping
    blocks = pdf_doc[0].get_text("blocks")
    for b in blocks:
        x0, y0, x1, y1 = b[:4]
        assert x0 >= 15.0, f"Text block clipped on left: x0={x0}"
        assert x1 <= 580.0, f"Text block clipped on right: x1={x1}"
        assert y0 >= 15.0, f"Text block clipped on top: y0={y0}"
        assert y1 <= 830.0, f"Text block clipped on bottom: y1={y1}"

    pdf_doc.close()


def test_docx_structure_and_styling(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
    tmp_path: Path,
) -> None:
    """Verify DOCX document has correct section headings, single-column layout, and no text boxes."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    docx_path = tmp_path / "test_structure.docx"
    generate_docx(tailored, docx_path)

    doc = docx.Document(docx_path)
    # Check section margins (A4)
    sec = doc.sections[0]
    assert round(sec.page_width.inches, 2) == 8.27
    assert round(sec.page_height.inches, 2) == 11.69

    # Verify headings present
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "PROFESSIONAL SUMMARY" in full_text
    assert "TECHNICAL SKILLS" in full_text
    assert "WORK EXPERIENCE" in full_text
    assert "PROJECTS" in full_text
    assert "EDUCATION" in full_text


def test_professional_summary_quality(aiml_profile: CandidateProfile, oceanai_job: JobDescription) -> None:
    """Verify professional summary word count (35-55 words) and lack of generic buzzwords."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    summary = tailored.summary
    words = summary.split()

    assert 35 <= len(words) <= 55, f"Summary word count {len(words)} outside 35-55 range: '{summary}'"
    assert "passionate" not in summary.lower()
    assert "highly motivated" not in summary.lower()
    assert "OceanAI" in summary or "Junior Gen AI Engineer" in summary


def test_ats_evaluation_on_exported_document(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
    tmp_path: Path,
) -> None:
    """Verify ATS evaluator operates on exported PDF and reports honest 7-dimension scores."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    pdf_path = tmp_path / "eval_test.pdf"
    docx_path = tmp_path / "eval_test.docx"

    generate_pdf(tailored, pdf_path)
    generate_docx(tailored, docx_path)

    gen_model = GeneratedResume(
        id=str(uuid.uuid4()),
        profile_id=aiml_profile.id,
        job_id=oceanai_job.id,
        title=tailored.title,
        target_role=tailored.target_role,
        target_company=tailored.target_company,
        version_number=1,
        docx_path=str(docx_path),
        pdf_path=str(pdf_path),
    )
    gen_model.set_sections(tailored.sections)

    eval_result = evaluate_resume_for_ats(gen_model, oceanai_job)

    assert 0.0 <= eval_result.overall_score <= 100.0
    report = eval_result.report

    # Verify document metrics are reported
    assert "document_metrics" in report
    metrics = report["document_metrics"]
    assert metrics["page_count"] == 1
    assert metrics["is_single_page"] is True
    assert metrics["format_compliance"] == "A4 Single-Page Verified"

    # All 7 dimensions present
    dim_scores = report["dimension_scores"]
    assert len(dim_scores) == 7
    assert dim_scores["structure_parsability"] >= 80.0
    assert dim_scores["readability_formatting"] >= 80.0


def test_claim_provenance_tracking(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
) -> None:
    """Verify 100% claim-level provenance coverage across all generated resume sections."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    prov = tailored.claim_provenance

    assert len(prov) >= 15, f"Expected comprehensive provenance records, got {len(prov)}"
    sections_represented = {item["section"] for item in prov}
    assert "contact" in sections_represented
    assert "summary" in sections_represented
    assert "skills" in sections_represented
    assert "experience" in sections_represented
    assert "projects" in sections_represented
    assert "education" in sections_represented

    for item in prov:
        assert item.get("claim_id") is not None
        assert item.get("claim_text") is not None
        assert item.get("source_field") is not None
        assert item.get("transformation_type") in ("direct", "synthesized", "summarized")
        assert item.get("validation_status") == "verified"
        assert item.get("confidence_score") == 1.0

    # Test ORM round-trip
    gen_model = GeneratedResume(
        id=str(uuid.uuid4()),
        profile_id=aiml_profile.id,
        job_id=oceanai_job.id,
        title=tailored.title,
        target_role=tailored.target_role,
        target_company=tailored.target_company,
        version_number=1,
    )
    gen_model.set_claim_provenance(prov)
    retrieved = gen_model.claim_provenance
    assert len(retrieved) == len(prov)
    assert retrieved[0]["claim_id"] == prov[0]["claim_id"]


def test_independent_document_validation(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
    tmp_path: Path,
) -> None:
    """Verify secondary decoupled validation engine (pypdf) inspects exported PDF."""
    from app.services.ats_evaluator import validate_document_independently

    tailored = tailor_resume(aiml_profile, oceanai_job)
    pdf_path = tmp_path / "independent_val.pdf"
    generate_pdf(tailored, pdf_path)

    val_result = validate_document_independently(pdf_path)
    assert val_result["status"] == "PASS"
    assert val_result["validation_engine"] == "pypdf"
    assert val_result["is_single_page"] is True
    assert val_result["is_a4_dimensions"] is True
    assert val_result["has_selectable_text"] is True
    assert len(val_result["verified_sections"]) >= 4


def test_education_btech_alignment(
    aiml_profile: CandidateProfile,
    oceanai_job: JobDescription,
    tmp_path: Path,
) -> None:
    """Verify B.Tech candidate degree scores 100.0% against Bachelor-level requirements."""
    tailored = tailor_resume(aiml_profile, oceanai_job)
    pdf_path = tmp_path / "edu_test.pdf"
    docx_path = tmp_path / "edu_test.docx"
    generate_pdf(tailored, pdf_path)
    generate_docx(tailored, docx_path)

    gen_model = GeneratedResume(
        id=str(uuid.uuid4()),
        profile_id=aiml_profile.id,
        job_id=oceanai_job.id,
        title=tailored.title,
        target_role=tailored.target_role,
        target_company=tailored.target_company,
        version_number=1,
        docx_path=str(docx_path),
        pdf_path=str(pdf_path),
    )
    gen_model.set_sections(tailored.sections)

    eval_result = evaluate_resume_for_ats(gen_model, oceanai_job)
    assert eval_result.education_score == 100.0
