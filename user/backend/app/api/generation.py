"""Resume Generation API Router (Stage 6).

Endpoints:
- POST /api/v1/resumes/generate
- GET  /api/v1/resumes/generated
- GET  /api/v1/resumes/generated/{id}
- GET  /api/v1/resumes/generated/{id}/download
- GET  /api/v1/resumes/generated/{id}/versions
"""

import logging
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import ATSEvaluation, CandidateProfile, GeneratedResume, JobDescription, MatchResult, User
from app.schemas import (
    GeneratedResumeCreate,
    GeneratedResumeListItemResponse,
    GeneratedResumeResponse,
    ResumeVersionComparisonResponse,
)
from app.services.activity_logger import record_activity
from app.services.ats_evaluator import evaluate_resume_for_ats
from app.services.resume_generator import build_and_save_resume_documents
from app.services.resume_tailorer import tailor_resume

logger = logging.getLogger("app.api.generation")

router = APIRouter(prefix="/api/v1/resumes", tags=["Resume Generation"])


@router.post(
    "/generate",
    response_model=GeneratedResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate tailored ATS-optimized resume",
)
def generate_tailored_resume(
    payload: GeneratedResumeCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> GeneratedResumeResponse:
    """Generate job-specific tailored resume in DOCX and PDF formats with ATS scoring."""
    # Validate profile exists
    profile = db.execute(
        select(CandidateProfile).where(CandidateProfile.id == payload.profile_id)
    ).scalar_one_or_none()
    if not profile or (profile.user_id is not None and (current_user is None or profile.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile {payload.profile_id} not found",
        )

    # Validate job exists
    job = db.execute(
        select(JobDescription).where(JobDescription.id == payload.job_id)
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {payload.job_id} not found",
        )

    # Optional match result
    match: MatchResult | None = None
    if payload.match_id:
        match = db.execute(
            select(MatchResult).where(MatchResult.id == payload.match_id)
        ).scalar_one_or_none()
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match result {payload.match_id} not found",
            )
        if match.profile_id != profile.id or match.job_id != job.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="match_id does not belong to the specified profile and job",
            )
    else:
        # Check if match result exists for this profile and job
        match = db.execute(
            select(MatchResult)
            .where(MatchResult.profile_id == payload.profile_id, MatchResult.job_id == payload.job_id)
            .order_by(desc(MatchResult.created_at))
        ).scalars().first()

    # Determine next version number for (profile_id, job_id) safely with func.max
    # Serialize version allocation for concurrency safety if dialect supports row locking
    if db.bind and db.bind.dialect.name != "sqlite":
        try:
            db.execute(select(CandidateProfile.id).where(CandidateProfile.id == payload.profile_id).with_for_update())
        except Exception:
            pass

    max_ver = db.execute(
        select(func.max(GeneratedResume.version_number))
        .where(GeneratedResume.profile_id == payload.profile_id, GeneratedResume.job_id == payload.job_id)
    ).scalar()
    next_version = (max_ver or 0) + 1

    # Tailor resume
    tailored = tailor_resume(
        profile=profile,
        job=job,
        match=match,
        custom_title=payload.title,
    )

    # Build DOCX and PDF documents
    docx_path, pdf_path = build_and_save_resume_documents(
        tailored_data=tailored,
        profile_id=profile.id,
        job_id=job.id,
        version_number=next_version,
    )

    resume_id = str(uuid.uuid4())
    generated = GeneratedResume(
        id=resume_id,
        profile_id=profile.id,
        job_id=job.id,
        match_id=match.id if match else None,
        title=tailored.title,
        target_role=tailored.target_role,
        target_company=tailored.target_company,
        version_number=next_version,
        docx_path=str(docx_path),
        pdf_path=str(pdf_path),
        user_id=current_user.id if current_user else profile.user_id,
    )
    generated.set_sections(tailored.sections)
    generated.set_claim_provenance(getattr(tailored, "claim_provenance", []))

    # Run initial ATS evaluation
    ats_result = evaluate_resume_for_ats(generated, job)
    generated.ats_score = ats_result.overall_score

    db.add(generated)
    db.flush()

    # Save initial ATS report record
    eval_record = ATSEvaluation(
        id=str(uuid.uuid4()),
        resume_id=generated.id,
        job_id=job.id,
        overall_score=ats_result.overall_score,
        mandatory_skill_score=ats_result.mandatory_skill_score,
        preferred_skill_score=ats_result.preferred_skill_score,
        experience_score=ats_result.experience_score,
        education_score=ats_result.education_score,
        keyword_score=ats_result.keyword_score,
        structure_score=ats_result.structure_score,
        readability_score=ats_result.readability_score,
        user_id=current_user.id if current_user else profile.user_id,
    )
    eval_record.set_report(ats_result.report)
    db.add(eval_record)

    db.commit()
    db.refresh(generated)

    record_activity(
        db=db,
        user_id=generated.user_id,
        action="resume_generated",
        title=f"Generated tailored resume v{next_version}: {generated.title}",
        description=f"Single-page A4 PDF/DOCX generated for {generated.target_role} (ATS Score: {round(generated.ats_score or 0)})",
        entity_type="resume",
        entity_id=generated.id,
    )

    logger.info("Generated resume %s (v%d) with ATS score %.1f", generated.id, next_version, generated.ats_score)
    return GeneratedResumeResponse.model_validate(generated)


@router.get(
    "/generated",
    response_model=list[GeneratedResumeListItemResponse],
    summary="List generated resumes",
)
def list_generated_resumes(
    profile_id: str | None = None,
    job_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[GeneratedResumeListItemResponse]:
    """Retrieve list of generated resumes with optional filtering and tenant isolation."""
    query = select(GeneratedResume)
    if current_user:
        query = query.where(GeneratedResume.user_id == current_user.id)
    else:
        query = query.where(GeneratedResume.user_id.is_(None))
    if profile_id:
        query = query.where(GeneratedResume.profile_id == profile_id)
    if job_id:
        query = query.where(GeneratedResume.job_id == job_id)

    query = query.order_by(desc(GeneratedResume.created_at)).offset(offset).limit(limit)
    resumes = db.execute(query).scalars().all()
    return [GeneratedResumeListItemResponse.model_validate(r) for r in resumes]


@router.get(
    "/generated/{resume_id}",
    response_model=GeneratedResumeResponse,
    summary="Get generated resume by ID",
)
def get_generated_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> GeneratedResumeResponse:
    """Retrieve complete metadata and section content for a generated resume."""
    resume = db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    ).scalar_one_or_none()
    if not resume or (resume.user_id is not None and (current_user is None or resume.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated resume {resume_id} not found",
        )
    return GeneratedResumeResponse.model_validate(resume)


@router.get(
    "/generated/{resume_id}/download",
    summary="Download generated resume file",
)
def download_generated_resume(
    resume_id: str,
    format: str = Query("pdf", pattern="^(pdf|docx)$"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> FileResponse:
    """Download the generated resume document as PDF or DOCX attachment."""
    resume = db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    ).scalar_one_or_none()
    if not resume or (resume.user_id is not None and (current_user is None or resume.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated resume {resume_id} not found",
        )

    file_path_str = resume.pdf_path if format.lower() == "pdf" else resume.docx_path
    if not file_path_str:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume file in {format} format is not available",
        )

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file not found on disk at {file_path.name}",
        )

    media_type = (
        "application/pdf"
        if format.lower() == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    clean_filename = f"{resume.title.replace(' ', '_')}_v{resume.version_number}.{format.lower()}"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=clean_filename,
    )


@router.get(
    "/generated/{resume_id}/versions",
    response_model=ResumeVersionComparisonResponse,
    summary="Compare resume versions",
)
def get_resume_version_history(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ResumeVersionComparisonResponse:
    """Fetch version comparison between current resume and previous generation."""
    current = db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    ).scalar_one_or_none()
    if not current or (current.user_id is not None and (current_user is None or current.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated resume {resume_id} not found",
        )

    # Find previous version (scoped to same tenant/user)
    prev_query = (
        select(GeneratedResume)
        .where(
            GeneratedResume.profile_id == current.profile_id,
            GeneratedResume.job_id == current.job_id,
            GeneratedResume.version_number < current.version_number,
        )
    )
    higher_query = (
        select(GeneratedResume.id)
        .where(
            GeneratedResume.profile_id == current.profile_id,
            GeneratedResume.job_id == current.job_id,
            GeneratedResume.version_number > current.version_number,
        )
    )

    if current.user_id is not None:
        prev_query = prev_query.where(GeneratedResume.user_id == current.user_id)
        higher_query = higher_query.where(GeneratedResume.user_id == current.user_id)
    elif current_user is not None:
        prev_query = prev_query.where(GeneratedResume.user_id == current_user.id)
        higher_query = higher_query.where(GeneratedResume.user_id == current_user.id)

    previous = db.execute(prev_query.order_by(desc(GeneratedResume.version_number))).scalars().first()
    higher_exists = db.execute(higher_query.limit(1)).scalar_one_or_none() is not None

    diff: dict[str, object] = {
        "version_difference": current.version_number - (previous.version_number if previous else 0),
        "ats_score_change": round((current.ats_score or 0.0) - (previous.ats_score or 0.0), 2) if previous else 0.0,
        "is_latest": not higher_exists,
    }

    return ResumeVersionComparisonResponse(
        profile_id=current.profile_id,
        job_id=current.job_id,
        current_version=GeneratedResumeResponse.model_validate(current),
        previous_version=GeneratedResumeResponse.model_validate(previous) if previous else None,
        differences=diff,
    )


@router.delete(
    "/generated/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete generated resume",
)
def delete_generated_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete a generated resume record and remove exported files from disk."""
    resume = db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    ).scalar_one_or_none()
    if not resume or (current_user is not None and resume.user_id is not None and resume.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated resume {resume_id} not found",
        )
    deleted_title = resume.title
    user_id = resume.user_id
    if resume.docx_path:
        Path(resume.docx_path).unlink(missing_ok=True)
    if resume.pdf_path:
        Path(resume.pdf_path).unlink(missing_ok=True)
    db.delete(resume)
    db.commit()

    record_activity(
        db=db,
        user_id=user_id,
        action="resume_deleted",
        title=f"Deleted resume {deleted_title}",
        entity_type="resume",
        entity_id=resume_id,
    )

