"""API endpoints for candidate profile intelligence, consolidation, review, and approval."""

import uuid
from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.errors import AppException, NotFoundError
from app.models import (
    CandidateProfile,
    Certification,
    Document,
    Education,
    MatchResult,
    Skill,
    User,
    WorkExperience,
)
from app.schemas import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    ConsolidationRequest,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ProfileApprovalRequest,
    ProjectItem,
    ResolveConflictRequest,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
    WorkExperienceCreate,
    WorkExperienceResponse,
    WorkExperienceUpdate,
)
from app.services.activity_logger import record_activity
from app.services.profile_consolidator import consolidate_documents_into_profile

logger = logging.getLogger("app.api.profiles")

router = APIRouter(prefix="/api/v1/profiles", tags=["Candidate Profile Intelligence"])


def _invalidate_profile_matches(db: Session, profile_id: str, reason: str = "Candidate profile updated") -> None:
    """Invalidate all downstream matches for this profile when career claims change."""
    db.execute(
        update(MatchResult)
        .where(MatchResult.profile_id == profile_id)
        .values(is_stale=True, stale_reason=reason)
    )


def _load_profile(db: Session, profile_id: str, current_user: User | None = None) -> CandidateProfile:
    """Retrieve CandidateProfile ORM instance with all child relationships eagerly loaded."""
    stmt = (
        select(CandidateProfile)
        .where(CandidateProfile.id == profile_id)
        .options(
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.education),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.certifications),
        )
    )
    profile = db.scalars(stmt).first()
    if not profile or (current_user is not None and profile.user_id is not None and profile.user_id != current_user.id):
        raise NotFoundError(f"Candidate profile '{profile_id}' not found.")
    return profile


@router.get(
    "",
    response_model=list[CandidateProfileResponse],
    summary="List Candidate Profiles",
    description="List all profiles accessible to the user, with child relationships.",
)
def list_candidate_profiles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[CandidateProfile]:
    """List candidate profiles accessible to the user."""
    stmt = (
        select(CandidateProfile)
        .options(
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.education),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.certifications),
        )
        .order_by(CandidateProfile.created_at.desc())
    )
    if current_user:
        stmt = stmt.where(
            (CandidateProfile.user_id == current_user.id) | (CandidateProfile.user_id.is_(None))
        )
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.post(
    "/consolidate",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Consolidate Resumes into Candidate Profile",
    description="Fuses 1 to 10 ingested resumes, deduplicates records, preserves source traceability, and runs conflict detection.",
)
def consolidate_resumes(
    payload: ConsolidationRequest,
    db: Session = Depends(get_db),
) -> CandidateProfile:
    """Consolidate multiple resume documents into a single profile."""
    # Verify unique document IDs
    doc_ids = list(dict.fromkeys(payload.document_ids))
    if not doc_ids:
        raise AppException(
            message="At least one document ID is required.",
            code="INVALID_DOCUMENT_SELECTION",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Fetch documents from database
    docs = db.scalars(select(Document).where(Document.id.in_(doc_ids))).all()
    found_ids = {d.id for d in docs}
    missing_ids = set(doc_ids) - found_ids
    if missing_ids:
        raise NotFoundError(f"Document IDs not found: {', '.join(sorted(missing_ids))}")

    # Check that documents have completed extraction
    unready = [d.id for d in docs if d.status != "completed"]
    if unready:
        raise AppException(
            message=f"Documents not ready for consolidation (must be completed): {', '.join(unready)}",
            code="DOCUMENTS_NOT_READY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Perform consolidation
    profile = consolidate_documents_into_profile(docs, user_id=payload.user_id)
    db.add(profile)
    db.commit()

    record_activity(
        db=db,
        user_id=profile.user_id,
        action="profile_consolidated",
        title=f"Consolidated profile for {profile.full_name}",
        description=f"Merged {len(doc_ids)} resume document(s) with {len(profile.skills)} skills and {len(profile.experiences)} experiences",
        entity_type="profile",
        entity_id=profile.id,
    )
    _invalidate_profile_matches(db, profile.id, reason="Candidate profile re-consolidated")

    return _load_profile(db, profile.id)


@router.get(
    "/{profile_id}",
    response_model=CandidateProfileResponse,
    summary="Get Candidate Profile",
    description="Retrieves the consolidated candidate profile with experiences, education, skills, certifications, and conflicts.",
)
def get_candidate_profile(
    profile_id: str,
    db: Session = Depends(get_db),
) -> CandidateProfile:
    """Retrieve candidate profile by ID."""
    return _load_profile(db, profile_id)


@router.patch(
    "/{profile_id}",
    response_model=CandidateProfileResponse,
    summary="Update Candidate Profile",
    description="Allows candidate to manually update profile contact details, headline, or summary.",
)
def update_candidate_profile(
    profile_id: str,
    payload: CandidateProfileUpdate,
    db: Session = Depends(get_db),
) -> CandidateProfile:
    """Update general candidate profile fields."""
    profile = _load_profile(db, profile_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    _invalidate_profile_matches(db, profile.id, reason="Candidate profile details updated")
    db.commit()
    record_activity(
        db=db,
        user_id=profile.user_id,
        action="profile_updated",
        title=f"Updated profile fields for {profile.full_name}",
        description=f"Fields changed: {', '.join(update_data.keys())}",
        entity_type="profile",
        entity_id=profile.id,
    )
    return _load_profile(db, profile.id)


@router.patch(
    "/{profile_id}/experiences/{exp_id}",
    response_model=WorkExperienceResponse,
    summary="Update Work Experience",
    description="Update a specific employment record and set approval status.",
)
def update_work_experience(
    profile_id: str,
    exp_id: str,
    payload: WorkExperienceUpdate,
    db: Session = Depends(get_db),
) -> WorkExperience:
    """Update work experience record."""
    stmt = select(WorkExperience).where(
        WorkExperience.id == exp_id, WorkExperience.profile_id == profile_id
    )
    exp = db.scalars(stmt).first()
    if not exp:
        raise NotFoundError(f"Work experience '{exp_id}' not found for profile '{profile_id}'.")

    update_data = payload.model_dump(exclude_unset=True)
    if "skills_used" in update_data:
        exp.set_skills_used(update_data.pop("skills_used"))

    for field, value in update_data.items():
        setattr(exp, field, value)

    _invalidate_profile_matches(db, profile_id, reason="Work experience updated")
    db.commit()
    db.refresh(exp)
    return exp


@router.patch(
    "/{profile_id}/education/{edu_id}",
    response_model=EducationResponse,
    summary="Update Education Record",
    description="Update an academic qualification and set approval status.",
)
def update_education(
    profile_id: str,
    edu_id: str,
    payload: EducationUpdate,
    db: Session = Depends(get_db),
) -> Education:
    """Update education record."""
    stmt = select(Education).where(
        Education.id == edu_id, Education.profile_id == profile_id
    )
    edu = db.scalars(stmt).first()
    if not edu:
        raise NotFoundError(f"Education record '{edu_id}' not found for profile '{profile_id}'.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(edu, field, value)

    _invalidate_profile_matches(db, profile_id, reason="Education updated")
    db.commit()
    db.refresh(edu)
    return edu


@router.patch(
    "/{profile_id}/skills/{skill_id}",
    response_model=SkillResponse,
    summary="Update Skill",
    description="Update skill name, category, proficiency, or approval status.",
)
def update_skill(
    profile_id: str,
    skill_id: str,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
) -> Skill:
    """Update skill record."""
    stmt = select(Skill).where(
        Skill.id == skill_id, Skill.profile_id == profile_id
    )
    sk = db.scalars(stmt).first()
    if not sk:
        raise NotFoundError(f"Skill '{skill_id}' not found for profile '{profile_id}'.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sk, field, value)

    _invalidate_profile_matches(db, profile_id, reason="Skill updated")
    db.commit()
    db.refresh(sk)
    return sk


@router.patch(
    "/{profile_id}/certifications/{cert_id}",
    response_model=CertificationResponse,
    summary="Update Certification",
    description="Update certification record and approval status.",
)
def update_certification(
    profile_id: str,
    cert_id: str,
    payload: CertificationUpdate,
    db: Session = Depends(get_db),
) -> Certification:
    """Update certification record."""
    stmt = select(Certification).where(
        Certification.id == cert_id, Certification.profile_id == profile_id
    )
    cert = db.scalars(stmt).first()
    if not cert:
        raise NotFoundError(f"Certification '{cert_id}' not found for profile '{profile_id}'.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cert, field, value)

    _invalidate_profile_matches(db, profile_id, reason="Certification updated")
    db.commit()
    db.refresh(cert)
    return cert


@router.post(
    "/{profile_id}/conflicts/{conflict_id}/resolve",
    response_model=CandidateProfileResponse,
    summary="Resolve or Dismiss Conflict",
    description="Marks a detected conflict as resolved or dismissed with candidate notes.",
)
def resolve_conflict(
    profile_id: str,
    conflict_id: str,
    payload: ResolveConflictRequest,
    db: Session = Depends(get_db),
) -> CandidateProfile:
    """Resolve a detected conflict on the candidate profile."""
    profile = _load_profile(db, profile_id)
    conflicts = profile.conflicts

    found = False
    for c in conflicts:
        if c.get("id") == conflict_id:
            c["resolution_status"] = payload.resolution_status
            c["resolution_notes"] = payload.resolution_notes
            found = True
            break

    if not found:
        raise NotFoundError(f"Conflict '{conflict_id}' not found in profile '{profile_id}'.")

    profile.set_conflicts(conflicts)
    _invalidate_profile_matches(db, profile.id, reason="Candidate profile conflict resolved")
    db.commit()

    record_activity(
        db=db,
        user_id=profile.user_id,
        action="conflict_resolved",
        title=f"Resolved conflict {conflict_id}",
        description=f"Status: {payload.resolution_status}, Notes: {payload.resolution_notes or 'None'}",
        entity_type="profile",
        entity_id=profile.id,
    )

    return _load_profile(db, profile.id)


@router.post(
    "/{profile_id}/approve",
    response_model=CandidateProfileResponse,
    summary="Approve Candidate Profile or Entities",
    description="Approves specified entities or the complete profile, updating the verification status.",
)
def approve_profile(
    profile_id: str,
    payload: ProfileApprovalRequest,
    db: Session = Depends(get_db),
) -> CandidateProfile:
    """Approve candidate profile facts and verify the profile."""
    profile = _load_profile(db, profile_id)

    if payload.approve_all:
        profile.is_approved = True
        profile.verification_status = "approved"
        profile.approval_date = datetime.now(timezone.utc)
        for exp in profile.experiences:
            exp.is_approved = True
        for edu in profile.education:
            edu.is_approved = True
        for sk in profile.skills:
            sk.is_approved = True
        for cert in profile.certifications:
            cert.is_approved = True
    else:
        exp_ids = set(payload.experience_ids)
        edu_ids = set(payload.education_ids)
        sk_ids = set(payload.skill_ids)
        cert_ids = set(payload.certification_ids)

        for exp in profile.experiences:
            if exp.id in exp_ids:
                exp.is_approved = True
        for edu in profile.education:
            if edu.id in edu_ids:
                edu.is_approved = True
        for sk in profile.skills:
            if sk.id in sk_ids:
                sk.is_approved = True
        for cert in profile.certifications:
            if cert.id in cert_ids:
                cert.is_approved = True

        all_items = (
            profile.experiences
            + profile.education
            + profile.skills
            + profile.certifications
        )
        approved_count = sum(1 for item in all_items if item.is_approved)

        if all_items and approved_count == len(all_items):
            profile.is_approved = True
            profile.verification_status = "approved"
            profile.approval_date = datetime.now(timezone.utc)
        elif approved_count > 0:
            profile.verification_status = "partially_verified"

    db.commit()

    if profile.is_approved:
        record_activity(
            db=db,
            user_id=profile.user_id,
            action="profile_approved",
            title=f"Approved candidate profile for {profile.full_name}",
            description="Profile verified and locked as authoritative source of truth for resume tailoring",
            entity_type="profile",
            entity_id=profile.id,
        )

    return _load_profile(db, profile.id)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Candidate Profile",
)
def delete_candidate_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete a candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    db.delete(profile)
    db.commit()


@router.post(
    "/{profile_id}/experiences",
    response_model=WorkExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Work Experience",
)
def add_work_experience(
    profile_id: str,
    payload: WorkExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> WorkExperience:
    """Add work experience record to candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    source_doc = getattr(payload, "source_document_id", None) or (profile.source_document_ids[0] if profile.source_document_ids else "manual_entry")
    confidence_score = getattr(payload, "confidence_score", None) or 1.0
    exp = WorkExperience(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        company=payload.company,
        job_title=payload.job_title,
        location=payload.location,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        description=payload.description,
        source_document_id=source_doc,
        confidence_score=confidence_score,
        is_approved=True,
    )
    if payload.skills_used:
        exp.set_skills_used(payload.skills_used)
    db.add(exp)
    _invalidate_profile_matches(db, profile.id, reason="Work experience added")
    db.commit()
    db.refresh(exp)
    return exp


@router.delete(
    "/{profile_id}/experiences/{exp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Work Experience",
)
def delete_work_experience(
    profile_id: str,
    exp_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete work experience record."""
    profile = _load_profile(db, profile_id, current_user)
    stmt = select(WorkExperience).where(
        WorkExperience.id == exp_id, WorkExperience.profile_id == profile.id
    )
    exp = db.scalars(stmt).first()
    if not exp:
        raise NotFoundError(f"Work experience '{exp_id}' not found for profile '{profile_id}'.")
    db.delete(exp)
    _invalidate_profile_matches(db, profile.id, reason="Work experience deleted")
    db.commit()


@router.post(
    "/{profile_id}/education",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Education Record",
)
def add_education(
    profile_id: str,
    payload: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Education:
    """Add education record to candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    source_doc = getattr(payload, "source_document_id", None) or (profile.source_document_ids[0] if profile.source_document_ids else "manual_entry")
    edu = Education(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        institution=payload.institution,
        degree=payload.degree,
        field_of_study=payload.field_of_study,
        start_date=payload.start_date,
        end_date=payload.end_date,
        grade=payload.grade,
        source_document_id=source_doc,
        is_approved=True,
    )
    db.add(edu)
    _invalidate_profile_matches(db, profile.id, reason="Education added")
    db.commit()
    db.refresh(edu)
    return edu


@router.delete(
    "/{profile_id}/education/{edu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Education Record",
)
def delete_education(
    profile_id: str,
    edu_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete education record."""
    profile = _load_profile(db, profile_id, current_user)
    stmt = select(Education).where(
        Education.id == edu_id, Education.profile_id == profile.id
    )
    edu = db.scalars(stmt).first()
    if not edu:
        raise NotFoundError(f"Education record '{edu_id}' not found for profile '{profile_id}'.")
    db.delete(edu)
    _invalidate_profile_matches(db, profile.id, reason="Education deleted")
    db.commit()


@router.post(
    "/{profile_id}/skills",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Skill",
)
def add_skill(
    profile_id: str,
    payload: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Skill:
    """Add skill to candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    source_doc = getattr(payload, "source_document_id", None) or (profile.source_document_ids[0] if profile.source_document_ids else "manual_entry")
    sk = Skill(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        name=payload.name,
        category=payload.category or "Other",
        proficiency=payload.proficiency or "intermediate",
        years_of_experience=payload.years_of_experience or 1.0,
        source_document_id=source_doc,
        is_approved=True,
    )
    db.add(sk)
    _invalidate_profile_matches(db, profile.id, reason="Skill added")
    db.commit()
    db.refresh(sk)
    return sk


@router.delete(
    "/{profile_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Skill",
)
def delete_skill(
    profile_id: str,
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete skill record."""
    profile = _load_profile(db, profile_id, current_user)
    stmt = select(Skill).where(
        Skill.id == skill_id, Skill.profile_id == profile.id
    )
    sk = db.scalars(stmt).first()
    if not sk:
        raise NotFoundError(f"Skill '{skill_id}' not found for profile '{profile_id}'.")
    db.delete(sk)
    _invalidate_profile_matches(db, profile.id, reason="Skill deleted")
    db.commit()


@router.post(
    "/{profile_id}/certifications",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Certification",
)
def add_certification(
    profile_id: str,
    payload: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Certification:
    """Add certification to candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    source_doc = getattr(payload, "source_document_id", None) or (profile.source_document_ids[0] if profile.source_document_ids else "manual_entry")
    cert = Certification(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        name=payload.name,
        issuing_organization=payload.issuing_organization,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        credential_id=payload.credential_id,
        credential_url=payload.credential_url,
        source_document_id=source_doc,
        is_approved=True,
    )
    db.add(cert)
    _invalidate_profile_matches(db, profile.id, reason="Certification added")
    db.commit()
    db.refresh(cert)
    return cert


@router.delete(
    "/{profile_id}/certifications/{cert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Certification",
)
def delete_certification(
    profile_id: str,
    cert_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete certification record."""
    profile = _load_profile(db, profile_id, current_user)
    stmt = select(Certification).where(
        Certification.id == cert_id, Certification.profile_id == profile.id
    )
    cert = db.scalars(stmt).first()
    if not cert:
        raise NotFoundError(f"Certification '{cert_id}' not found for profile '{profile_id}'.")
    db.delete(cert)
    _invalidate_profile_matches(db, profile.id, reason="Certification deleted")
    db.commit()


@router.post(
    "/{profile_id}/projects",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Project",
)
def add_project(
    profile_id: str,
    payload: ProjectItem,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CandidateProfile:
    """Add project item to candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    projects = list(profile.projects)
    projects.append(payload.model_dump())
    profile.set_projects(projects)
    _invalidate_profile_matches(db, profile.id, reason="Project added")
    db.commit()
    return _load_profile(db, profile.id, current_user)


@router.patch(
    "/{profile_id}/projects/{project_index}",
    response_model=CandidateProfileResponse,
    summary="Update Project",
)
def update_project(
    profile_id: str,
    project_index: int,
    payload: ProjectItem,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CandidateProfile:
    """Update project item in candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    projects = list(profile.projects)
    if project_index < 0 or project_index >= len(projects):
        raise NotFoundError(f"Project index '{project_index}' out of range.")
    projects[project_index] = payload.model_dump()
    profile.set_projects(projects)
    _invalidate_profile_matches(db, profile.id, reason="Project updated")
    db.commit()
    return _load_profile(db, profile.id, current_user)


@router.delete(
    "/{profile_id}/projects/{project_index}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
)
def delete_project(
    profile_id: str,
    project_index: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Delete project item from candidate profile."""
    profile = _load_profile(db, profile_id, current_user)
    projects = list(profile.projects)
    if project_index < 0 or project_index >= len(projects):
        raise NotFoundError(f"Project index '{project_index}' out of range.")
    projects.pop(project_index)
    profile.set_projects(projects)
    _invalidate_profile_matches(db, profile.id, reason="Project deleted")
    db.commit()
