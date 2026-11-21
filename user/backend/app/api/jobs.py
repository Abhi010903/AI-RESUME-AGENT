"""REST API endpoints for Job Description Intelligence (Stage 4)."""

import logging
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from pathlib import Path
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import JobDescription, MatchResult, User
from app.services.activity_logger import record_activity
from app.services.extractor import extract_document_text
from fastapi import File, Form, UploadFile
from app.schemas import (
    JobDescriptionAnalyzeRequest,
    JobDescriptionCreate,
    JobDescriptionListItemResponse,
    JobDescriptionResponse,
    JobDescriptionUpdate,
    JobRequirementsResponse,
    JobSkillsResponse,
    NormalizedSkillItem,
    RequirementItem,
)
from app.services.job_description_parser import parse_job_description

logger = logging.getLogger("app.api.jobs")

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Description Intelligence"])


@router.post(
    "/analyze",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze and persist a job description",
)
def analyze_job_description(
    payload: JobDescriptionAnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
) -> JobDescription:
    """Ingest unstructured job description text, extract requirements, and persist."""
    parsed = parse_job_description(
        raw_text=payload.raw_text,
        supplied_title=payload.title,
        supplied_company=payload.company,
        supplied_location=payload.location,
        supplied_employment_type=payload.employment_type,
        supplied_seniority=payload.seniority_level,
    )

    job_id = str(uuid.uuid4())
    job = JobDescription(
        id=job_id,
        title=parsed.title,
        company=parsed.company,
        location=parsed.location,
        employment_type=parsed.employment_type,
        seniority_level=parsed.seniority_level,
        summary=parsed.summary,
        raw_text=parsed.raw_text,
        normalized_text=parsed.normalized_text,
        min_years_experience=parsed.min_years_experience,
        max_years_experience=parsed.max_years_experience,
        education_level=parsed.education_level,
        status="analyzed",
        user_id=payload.user_id or (current_user.id if current_user else None),
    )
    job.set_responsibilities(parsed.responsibilities)
    job.set_required_skills(parsed.required_skills)
    job.set_preferred_skills(parsed.preferred_skills)
    job.set_required_qualifications(parsed.required_qualifications)
    job.set_preferred_qualifications(parsed.preferred_qualifications)
    job.set_certifications(parsed.certifications)
    job.set_soft_skills(parsed.soft_skills)
    job.set_quality_warnings(parsed.quality_warnings)

    db.add(job)
    db.commit()
    db.refresh(job)

    record_activity(
        db=db,
        user_id=job.user_id,
        action="job_analyzed",
        title=f"Analyzed job description: {job.title} at {job.company or 'Company'}",
        description=f"Identified {len(job.required_skills)} required skills, {len(job.preferred_skills)} preferred skills",
        entity_type="job",
        entity_id=job.id,
    )

    logger.info("Analyzed and stored job description", extra={"job_id": job.id, "title": job.title})
    return job


@router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job description",
)
def create_job_description(
    payload: JobDescriptionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
) -> JobDescription:
    """Create a new job description record with automatic requirement extraction."""
    parsed = parse_job_description(
        raw_text=payload.raw_text,
        supplied_title=payload.title,
        supplied_company=payload.company,
        supplied_location=payload.location,
        supplied_employment_type=payload.employment_type,
        supplied_seniority=payload.seniority_level,
    )

    job_id = str(uuid.uuid4())
    job = JobDescription(
        id=job_id,
        title=payload.title or parsed.title,
        company=payload.company or parsed.company,
        location=payload.location or parsed.location,
        employment_type=payload.employment_type or parsed.employment_type,
        seniority_level=payload.seniority_level or parsed.seniority_level,
        summary=payload.summary or parsed.summary,
        raw_text=payload.raw_text,
        normalized_text=parsed.normalized_text,
        min_years_experience=payload.min_years_experience
        if payload.min_years_experience is not None
        else parsed.min_years_experience,
        max_years_experience=payload.max_years_experience
        if payload.max_years_experience is not None
        else parsed.max_years_experience,
        education_level=payload.education_level or parsed.education_level,
        status="analyzed",
        user_id=payload.user_id or (current_user.id if current_user else None),
    )
    job.set_responsibilities(parsed.responsibilities)
    job.set_required_skills(parsed.required_skills)
    job.set_preferred_skills(parsed.preferred_skills)
    job.set_required_qualifications(parsed.required_qualifications)
    job.set_preferred_qualifications(parsed.preferred_qualifications)
    job.set_certifications(parsed.certifications)
    job.set_soft_skills(parsed.soft_skills)
    job.set_quality_warnings(parsed.quality_warnings)

    db.add(job)
    db.commit()
    db.refresh(job)

    record_activity(
        db=db,
        user_id=job.user_id,
        action="job_analyzed",
        title=f"Added target job: {job.title} at {job.company or 'Company'}",
        description=f"Identified {len(job.required_skills)} required skills, {len(job.preferred_skills)} preferred skills",
        entity_type="job",
        entity_id=job.id,
    )

    logger.info("Created job description", extra={"job_id": job.id, "title": job.title})
    return job


@router.get(
    "",
    response_model=list[JobDescriptionListItemResponse],
    summary="List job descriptions",
)
def list_job_descriptions(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    seniority: Annotated[str | None, Query()] = None,
) -> list[JobDescription]:
    """Retrieve paginated list of job descriptions with optional seniority filtering."""
    query = select(JobDescription).order_by(JobDescription.created_at.desc())
    if seniority:
        query = query.where(JobDescription.seniority_level.ilike(f"%{seniority}%"))
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())


@router.get(
    "/{job_id}",
    response_model=JobDescriptionResponse,
    summary="Get job description by ID",
)
def get_job_description(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobDescription:
    """Retrieve full structured job description details."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )
    return job


@router.patch(
    "/{job_id}",
    response_model=JobDescriptionResponse,
    summary="Update job description",
)
def update_job_description(
    job_id: str,
    payload: JobDescriptionUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> JobDescription:
    """Update editable fields of a job description."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(job, field_name, value)

    db.execute(
        update(MatchResult)
        .where(MatchResult.job_id == job.id)
        .values(is_stale=True, stale_reason="Job description updated")
    )
    db.commit()
    db.refresh(job)

    record_activity(
        db=db,
        user_id=job.user_id,
        action="job_updated",
        title=f"Updated job description: {job.title}",
        entity_type="job",
        entity_id=job.id,
    )
    logger.info("Updated job description", extra={"job_id": job.id})
    return job


@router.get(
    "/{job_id}/requirements",
    response_model=JobRequirementsResponse,
    summary="Get extracted requirements",
)
def get_job_requirements(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobRequirementsResponse:
    """Retrieve categorized mandatory and preferred requirements for a job."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )

    mandatory_items: list[RequirementItem] = []
    preferred_items: list[RequirementItem] = []

    # Map required skills
    for s in job.required_skills:
        mandatory_items.append(
            RequirementItem(
                name=s["name"],
                category="technical_skill",
                is_mandatory=True,
                raw_text=s.get("raw_mention", s["name"]),
                normalized_name=s["name"],
                priority="high",
                confidence=1.0,
            )
        )

    # Map preferred skills
    for s in job.preferred_skills:
        preferred_items.append(
            RequirementItem(
                name=s["name"],
                category="technical_skill",
                is_mandatory=False,
                raw_text=s.get("raw_mention", s["name"]),
                normalized_name=s["name"],
                priority="medium",
                confidence=1.0,
            )
        )

    # Map required qualifications
    for q in job.required_qualifications:
        mandatory_items.append(
            RequirementItem(
                name=q[:100],
                category="qualification",
                is_mandatory=True,
                raw_text=q,
                normalized_name=q[:100],
                priority="high",
                confidence=1.0,
            )
        )

    # Map preferred qualifications
    for q in job.preferred_qualifications:
        preferred_items.append(
            RequirementItem(
                name=q[:100],
                category="qualification",
                is_mandatory=False,
                raw_text=q,
                normalized_name=q[:100],
                priority="medium",
                confidence=1.0,
            )
        )

    return JobRequirementsResponse(
        job_id=job.id,
        title=job.title,
        mandatory_requirements=mandatory_items,
        preferred_requirements=preferred_items,
        responsibilities=job.responsibilities,
        min_years_experience=job.min_years_experience,
        max_years_experience=job.max_years_experience,
        education_level=job.education_level,
        certifications=job.certifications,
    )


@router.get(
    "/{job_id}/skills",
    response_model=JobSkillsResponse,
    summary="Get normalized job skills",
)
def get_job_skills(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobSkillsResponse:
    """Retrieve normalized technical skills classified into required and preferred."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )

    req_skills = [
        NormalizedSkillItem(
            name=s["name"],
            category=s.get("category", "General"),
            is_mandatory=True,
            raw_mention=s.get("raw_mention", s["name"]),
            importance=s.get("importance", "high"),
        )
        for s in job.required_skills
    ]

    pref_skills = [
        NormalizedSkillItem(
            name=s["name"],
            category=s.get("category", "General"),
            is_mandatory=False,
            raw_mention=s.get("raw_mention", s["name"]),
            importance=s.get("importance", "medium"),
        )
        for s in job.preferred_skills
    ]

    return JobSkillsResponse(
        job_id=job.id,
        title=job.title,
        required_skills=req_skills,
        preferred_skills=pref_skills,
    )



@router.post(
    "/upload",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze job description document",
)
async def upload_job_description(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    company: str | None = Form(None),
    location: str | None = Form(None),
    employment_type: str | None = Form(None),
    seniority_level: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> JobDescription:
    """Upload a file (PDF, DOCX, TXT, MD) containing a job description and extract requirements."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    filename = file.filename or "job_description.txt"
    ext = Path(filename).suffix.lower()

    raw_text = ""
    if ext in [".txt", ".md"]:
        raw_text = content.decode("utf-8", errors="replace")
    elif ext in [".pdf", ".docx"]:
        extracted = extract_document_text(content, ext.lstrip("."))
        raw_text = extracted.text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: .pdf, .docx, .txt, .md",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract readable text from uploaded file.",
        )

    parsed = parse_job_description(
        raw_text=raw_text,
        supplied_title=title,
        supplied_company=company,
        supplied_location=location,
        supplied_employment_type=employment_type,
        supplied_seniority=seniority_level,
    )

    job_id = str(uuid.uuid4())
    job = JobDescription(
        id=job_id,
        title=parsed.title or (title or "Untitled Position"),
        company=parsed.company or company,
        location=parsed.location or location,
        employment_type=parsed.employment_type or employment_type,
        seniority_level=parsed.seniority_level or seniority_level,
        summary=parsed.summary,
        raw_text=parsed.raw_text,
        normalized_text=parsed.normalized_text,
        min_years_experience=parsed.min_years_experience,
        max_years_experience=parsed.max_years_experience,
        education_level=parsed.education_level,
        status="analyzed",
        user_id=current_user.id if current_user else None,
    )
    job.set_responsibilities(parsed.responsibilities)
    job.set_required_skills(parsed.required_skills)
    job.set_preferred_skills(parsed.preferred_skills)
    job.set_required_qualifications(parsed.required_qualifications)
    job.set_preferred_qualifications(parsed.preferred_qualifications)
    job.set_certifications(parsed.certifications)
    job.set_soft_skills(parsed.soft_skills)
    job.set_quality_warnings(parsed.quality_warnings)

    db.add(job)
    db.commit()
    db.refresh(job)

    record_activity(
        db=db,
        user_id=job.user_id,
        action="job_analyzed",
        title=f"Uploaded and analyzed job description: {job.title} at {job.company or 'Company'}",
        description=f"Identified {len(job.required_skills)} required skills, {len(job.preferred_skills)} preferred skills",
        entity_type="job",
        entity_id=job.id,
    )

    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job description",
)
def delete_job_description(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete a job description and associated records."""
    job = db.get(JobDescription, job_id)
    if not job or (current_user is not None and job.user_id is not None and job.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{job_id}' not found.",
        )
    deleted_title = job.title
    user_id = job.user_id
    db.delete(job)
    db.commit()

    record_activity(
        db=db,
        user_id=user_id,
        action="job_deleted",
        title=f"Deleted target job: {deleted_title}",
        entity_type="job",
        entity_id=job_id,
    )
