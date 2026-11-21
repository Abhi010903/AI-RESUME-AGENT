"""REST API endpoints for Job Application Tracking."""

import logging
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import JobApplication, User
from app.schemas import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from app.services.activity_logger import record_activity

logger = logging.getLogger("app.api.applications")

router = APIRouter(prefix="/api/v1/applications", tags=["Job Application Tracker"])


@router.post(
    "",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tracked job application",
)
def create_application(
    payload: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> JobApplication:
    """Create a new job application record to track in the candidate pipeline."""
    app_id = str(uuid.uuid4())
    application = JobApplication(
        id=app_id,
        user_id=current_user.id if current_user else None,
        job_id=payload.job_id,
        resume_id=payload.resume_id,
        company=payload.company,
        position_title=payload.position_title,
        job_url=payload.job_url,
        location=payload.location,
        salary_range=payload.salary_range,
        status=payload.status,
        applied_date=payload.applied_date,
        notes=payload.notes,
    )
    if payload.interviews:
        application.set_interviews([iv if isinstance(iv, dict) else iv.model_dump() for iv in payload.interviews])
    else:
        application.set_interviews([])

    db.add(application)
    db.commit()
    db.refresh(application)

    record_activity(
        db=db,
        user_id=application.user_id,
        action="application_created",
        title=f"Created application for {application.position_title} at {application.company}",
        description=f"Status: {application.status}, Date: {application.applied_date or 'Not specified'}",
        entity_type="application",
        entity_id=application.id,
    )
    logger.info("Created application tracker %s for %s at %s", application.id, application.position_title, application.company)
    return application


@router.get(
    "",
    response_model=list[JobApplicationResponse],
    summary="List tracked job applications",
)
def list_applications(
    status: str | None = Query(None, description="Status filter: SAVED, APPLIED, INTERVIEWING, OFFERED, REJECTED, WITHDRAWN"),
    search: str | None = Query(None, description="Search company or position title"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[JobApplication]:
    """Retrieve tracked applications for the candidate with optional filtering and pagination."""
    stmt = select(JobApplication).order_by(JobApplication.updated_at.desc())

    if current_user:
        stmt = stmt.where((JobApplication.user_id == current_user.id) | (JobApplication.user_id.is_(None)))

    if status:
        stmt = stmt.where(JobApplication.status == status.upper())

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (JobApplication.company.ilike(pattern)) | (JobApplication.position_title.ilike(pattern))
        )

    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.get(
    "/{application_id}",
    response_model=JobApplicationResponse,
    summary="Get single tracked job application",
)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> JobApplication:
    """Retrieve single application by ID with tenant isolation check."""
    application = db.get(JobApplication, application_id)
    if not application or (current_user is not None and application.user_id is not None and application.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application '{application_id}' not found.",
        )
    return application


@router.patch(
    "/{application_id}",
    response_model=JobApplicationResponse,
    summary="Update tracked job application",
)
def update_application(
    application_id: str,
    payload: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> JobApplication:
    """Update application details, stage status, notes, or interview stages."""
    application = db.get(JobApplication, application_id)
    if not application or (current_user is not None and application.user_id is not None and application.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application '{application_id}' not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "interviews" in update_data:
        iv_data = update_data.pop("interviews")
        if iv_data is not None:
            application.set_interviews([iv if isinstance(iv, dict) else iv.model_dump() for iv in iv_data])

    old_status = application.status
    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    if "status" in update_data and update_data["status"] != old_status:
        record_activity(
            db=db,
            user_id=application.user_id,
            action="application_status_changed",
            title=f"Moved {application.position_title} to {application.status}",
            description=f"Status transitioned from {old_status} to {application.status}",
            entity_type="application",
            entity_id=application.id,
        )

    return application


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tracked job application",
)
def delete_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Remove a job application from the tracker."""
    application = db.get(JobApplication, application_id)
    if not application or (current_user is not None and application.user_id is not None and application.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application '{application_id}' not found.",
        )
    user_id = application.user_id
    pos_title = application.position_title
    comp = application.company
    db.delete(application)
    db.commit()

    record_activity(
        db=db,
        user_id=user_id,
        action="application_deleted",
        title=f"Deleted application for {pos_title} at {comp}",
        entity_type="application",
        entity_id=application_id,
    )
