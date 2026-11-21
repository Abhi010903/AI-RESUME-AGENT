"""ATS Evaluation API Router (Stage 6).

Endpoints:
- POST /api/v1/ats/evaluate
- GET  /api/v1/ats/reports/{id}
- GET  /api/v1/ats/reports
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import ATSEvaluation, GeneratedResume, JobDescription, User
from app.schemas import ATSEvaluateRequest, ATSEvaluationReportResponse
from app.services.activity_logger import record_activity
from app.services.ats_evaluator import evaluate_resume_for_ats

logger = logging.getLogger("app.api.ats")

router = APIRouter(prefix="/api/v1/ats", tags=["ATS Evaluation"])


@router.post(
    "/evaluate",
    response_model=ATSEvaluationReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate resume against job description",
)
def evaluate_resume(
    payload: ATSEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ATSEvaluationReportResponse:
    """Run comprehensive 7-dimension ATS audit and persist report."""
    resume = db.execute(
        select(GeneratedResume).where(GeneratedResume.id == payload.resume_id)
    ).scalar_one_or_none()
    if not resume or (resume.user_id is not None and (current_user is None or resume.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated resume {payload.resume_id} not found",
        )

    job = db.execute(
        select(JobDescription).where(JobDescription.id == payload.job_id)
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {payload.job_id} not found",
        )

    result = evaluate_resume_for_ats(resume, job)

    eval_record = ATSEvaluation(
        id=str(uuid.uuid4()),
        resume_id=resume.id,
        job_id=job.id,
        overall_score=result.overall_score,
        mandatory_skill_score=result.mandatory_skill_score,
        preferred_skill_score=result.preferred_skill_score,
        experience_score=result.experience_score,
        education_score=result.education_score,
        keyword_score=result.keyword_score,
        structure_score=result.structure_score,
        readability_score=result.readability_score,
        user_id=current_user.id if current_user else resume.user_id,
    )
    eval_record.set_report(result.report)

    # Update resume's latest ATS score only when evaluating against the targeted job
    if job.id == resume.job_id:
        resume.ats_score = result.overall_score

    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)

    record_activity(
        db=db,
        user_id=eval_record.user_id,
        action="ats_evaluated",
        title=f"Evaluated ATS score {round(result.overall_score)}% for {resume.title}",
        description=f"Mandatory skills: {round(result.mandatory_skill_score)}%, Keywords: {round(result.keyword_score)}%",
        entity_type="ats",
        entity_id=eval_record.id,
    )

    logger.info("ATS evaluation completed for resume %s: score %.1f", resume.id, result.overall_score)
    return ATSEvaluationReportResponse.model_validate(eval_record)


@router.get(
    "/reports/{report_id}",
    response_model=ATSEvaluationReportResponse,
    summary="Get ATS evaluation report by ID",
)
def get_ats_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ATSEvaluationReportResponse:
    """Retrieve full ATS report including dimension scores and recommendations."""
    report = db.execute(
        select(ATSEvaluation).where(ATSEvaluation.id == report_id)
    ).scalar_one_or_none()
    if not report or (report.user_id is not None and (current_user is None or report.user_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ATS evaluation report {report_id} not found",
        )
    return ATSEvaluationReportResponse.model_validate(report)


@router.get(
    "/reports",
    response_model=list[ATSEvaluationReportResponse],
    summary="List ATS evaluation reports",
)
def list_ats_reports(
    resume_id: str | None = None,
    job_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ATSEvaluationReportResponse]:
    """List recent ATS evaluation reports with optional filtering and tenant isolation."""
    query = select(ATSEvaluation)
    if current_user:
        query = query.where(ATSEvaluation.user_id == current_user.id)
    else:
        query = query.where(ATSEvaluation.user_id.is_(None))
    if resume_id:
        query = query.where(ATSEvaluation.resume_id == resume_id)
    if job_id:
        query = query.where(ATSEvaluation.job_id == job_id)

    query = query.order_by(desc(ATSEvaluation.created_at)).offset(offset).limit(limit)
    reports = db.execute(query).scalars().all()
    return [ATSEvaluationReportResponse.model_validate(r) for r in reports]
