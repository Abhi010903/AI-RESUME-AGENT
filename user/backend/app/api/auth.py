"""Authentication & User Profile API Router (Stage 7).

Endpoints:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET  /api/v1/auth/me
"""

import logging
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.config import Settings, get_settings
from app.database import get_db
from app.models import User
from app.schemas import (
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth import (
    authenticate_user,
    check_rate_limit,
    create_access_token,
    create_password_reset_token,
    create_user,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
    verify_password,
    verify_password_reset_token,
)

logger = logging.getLogger("app.api.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Accounts"])


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Extract and authenticate candidate from Bearer JWT token header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = decode_access_token(token, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Optional authentication: returns User if valid Bearer token provided, None if no header.

    If an invalid or expired token is sent, raises 401 instead of silently degrading to anonymous.
    """
    if not authorization:
        return None
    return get_current_user(authorization=authorization, db=db, settings=settings)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new candidate account",
)
def register_candidate(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Register candidate account, hash password with PBKDF2-SHA256, and return JWT token."""
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists",
        )

    user = create_user(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )

    token = create_access_token(user_id=user.id, email=user.email, settings=settings)

    logger.info("Registered candidate user %s (%s)", user.id, user.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate candidate credentials",
)
def login_candidate(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate email and password, returning signed JWT bearer token."""
    client_ip = payload.email.strip().lower()
    if not check_rate_limit(f"login_{client_ip}", max_attempts=8, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )

    user = authenticate_user(db=db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=user.id, email=user.email, settings=settings)

    logger.info("Candidate logged in successfully: %s", user.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated candidate profile",
)
def get_current_candidate(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile data for currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update candidate account settings",
)
def update_current_candidate(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update authenticated candidate full name or basic details."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post(
    "/password-change",
    status_code=status.HTTP_200_OK,
    summary="Change candidate password",
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Change password for authenticated user after verifying old password."""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed",
        )
    update_user_password(db, current_user, payload.new_password)
    logger.info("User %s successfully updated password", current_user.id)
    return {"status": "success", "message": "Password changed successfully"}


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_200_OK,
    summary="Request password reset token",
)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Generate time-limited password reset token."""
    email_clean = payload.email.strip().lower()
    if not check_rate_limit(f"reset_{email_clean}", max_attempts=4, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later.",
        )

    user = get_user_by_email(db, email_clean)
    # Always return success message to prevent user enumeration
    if not user:
        return {"status": "success", "message": "If this email is registered, a reset token has been issued."}

    reset_token = create_password_reset_token(user.id, user.email, settings=settings)
    # In a local / self-hosted setup, the reset token is returned directly for testing and UI fulfillment
    return {
        "status": "success",
        "message": "Password reset token generated.",
        "reset_token": reset_token,
    }


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset with token",
)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Validate reset token and set new password."""
    try:
        user_id = verify_password_reset_token(payload.token, settings=settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or expired password reset token: {exc}",
        ) from exc

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_user_password(db, user, payload.new_password)
    logger.info("Password reset successfully confirmed for user %s", user.id)
    return {"status": "success", "message": "Password has been reset successfully"}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout candidate session",
)
def logout_candidate() -> dict[str, str]:
    """Client drops token; endpoint provides confirmed server response."""
    return {"status": "success", "message": "Logged out successfully"}


@router.get(
    "/export-data",
    summary="Export complete candidate data archive",
)
def export_candidate_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Export complete candidate career knowledge base, profiles, applications, and documents metadata in JSON."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models import CandidateProfile, Document, GeneratedResume, JobApplication, JobDescription, ActivityLog

    # Fetch user profiles with relationships
    prof_stmt = (
        select(CandidateProfile)
        .where(CandidateProfile.user_id == current_user.id)
        .options(
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.education),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.certifications),
        )
    )
    profiles = list(db.scalars(prof_stmt).all())

    # Fetch documents
    docs = list(db.scalars(select(Document).where(Document.user_id == current_user.id)).all())

    # Fetch jobs
    jobs = list(db.scalars(select(JobDescription).where(JobDescription.user_id == current_user.id)).all())

    # Fetch generated resumes
    resumes = list(db.scalars(select(GeneratedResume).where(GeneratedResume.user_id == current_user.id)).all())

    # Fetch applications
    apps = list(db.scalars(select(JobApplication).where(JobApplication.user_id == current_user.id)).all())

    # Fetch activities
    activities = list(db.scalars(select(ActivityLog).where(ActivityLog.user_id == current_user.id).order_by(ActivityLog.created_at.desc())).all())

    return {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat(),
        },
        "profiles": [
            {
                "id": p.id,
                "full_name": p.full_name,
                "email": p.email,
                "headline": p.headline,
                "summary": p.summary,
                "verification_status": p.verification_status,
                "is_approved": p.is_approved,
                "experiences": [
                    {
                        "company": e.company,
                        "job_title": e.job_title,
                        "start_date": e.start_date,
                        "end_date": e.end_date,
                        "description": e.description,
                        "skills_used": e.skills_used,
                    }
                    for e in p.experiences
                ],
                "education": [
                    {
                        "institution": ed.institution,
                        "degree": ed.degree,
                        "field_of_study": ed.field_of_study,
                        "start_date": ed.start_date,
                        "end_date": ed.end_date,
                    }
                    for ed in p.education
                ],
                "skills": [
                    {
                        "name": s.name,
                        "category": s.category,
                        "proficiency": s.proficiency,
                        "is_approved": s.is_approved,
                    }
                    for s in p.skills
                ],
                "certifications": [
                    {
                        "name": c.name,
                        "issuing_organization": c.issuing_organization,
                        "issue_date": c.issue_date,
                    }
                    for c in p.certifications
                ],
                "projects": p.projects,
            }
            for p in profiles
        ],
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_format": d.file_format,
                "file_size": d.file_size,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
        "target_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "required_skills": j.required_skills,
                "preferred_skills": j.preferred_skills,
            }
            for j in jobs
        ],
        "generated_resumes": [
            {
                "id": r.id,
                "title": r.title,
                "target_role": r.target_role,
                "target_company": r.target_company,
                "version_number": r.version_number,
                "ats_score": r.ats_score,
                "created_at": r.created_at.isoformat(),
            }
            for r in resumes
        ],
        "job_applications": [
            {
                "id": a.id,
                "company": a.company,
                "position_title": a.position_title,
                "status": a.status,
                "applied_date": a.applied_date,
                "notes": a.notes,
                "interviews": a.interviews,
            }
            for a in apps
        ],
        "recent_activity": [
            {
                "action": act.action,
                "title": act.title,
                "created_at": act.created_at.isoformat(),
            }
            for act in activities
        ],
    }


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete candidate account",
)
def delete_candidate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Permanently delete user account and cascade delete owned records."""
    db.delete(current_user)
    db.commit()
    logger.info("Deleted candidate account %s", current_user.id)
    return {"status": "success", "message": "Account deleted successfully"}
