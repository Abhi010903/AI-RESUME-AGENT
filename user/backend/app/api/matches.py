"""REST API endpoints for Evidence-Based Skill Matching Engine (Stage 5)."""

import json
import logging
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import CandidateProfile, JobDescription, MatchResult, User
from app.services.activity_logger import record_activity
from app.schemas import (
    GapAnalysisResponse,
    MatchRequest,
    MatchResultListItemResponse,
    MatchResultResponse,
    RequirementMatchItem,
    RequirementMatchListResponse,
    ScoreBreakdownResponse,
)
from app.services.experience_matcher import evaluate_experience_match
from app.services.gap_analyzer import build_gap_analysis
from app.services.match_scorer import compute_match_score
from app.services.qualification_matcher import (
    evaluate_certifications_match,
    evaluate_education_match,
)
from app.services.skill_matcher import evaluate_skill_matches

logger = logging.getLogger("app.api.matches")

router = APIRouter(prefix="/api/v1/matches", tags=["Skill Matching Engine"])


@router.post(
    "",
    response_model=MatchResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Match candidate profile against job description",
)
def create_match(
    payload: MatchRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
) -> MatchResult:
    """Run evidence-based matching engine between candidate profile and structured job description."""
    profile = db.get(CandidateProfile, payload.profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID '{payload.profile_id}' not found.",
        )

    job = db.get(JobDescription, payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{payload.job_id}' not found.",
        )

    # 1. Evaluate Skills
    skill_evals = evaluate_skill_matches(profile, job)

    # 2. Evaluate Experience
    exp_outcome = evaluate_experience_match(profile, job)

    # 3. Evaluate Education & Certifications
    edu_outcome = evaluate_education_match(profile, job)
    cert_outcomes = evaluate_certifications_match(profile, job)

    # Check unresolved conflicts in candidate profile
    has_conflicts = any(c.get("resolution_status") == "unresolved" for c in profile.conflicts)

    # 4. Compute Scores
    score_res = compute_match_score(
        skill_evaluations=skill_evals,
        experience_outcome=exp_outcome,
        education_outcome=edu_outcome,
        certification_outcomes=cert_outcomes,
        custom_weights=payload.scoring_config,
        has_unresolved_conflicts=has_conflicts,
    )

    # 5. Build Gap Analysis
    gap_res = build_gap_analysis(
        skill_evaluations=skill_evals,
        experience_outcome=exp_outcome,
        education_outcome=edu_outcome,
        certification_outcomes=cert_outcomes,
    )

    # Format requirement match items
    requirement_match_records: list[dict[str, object]] = []
    for ev in skill_evals:
        requirement_match_records.append({
            "requirement_name": ev.requirement_name,
            "category": ev.category,
            "is_mandatory": ev.is_mandatory,
            "match_status": ev.match_status,
            "matched_candidate_skill": ev.matched_candidate_skill,
            "matched_entity_id": ev.matched_entity_id,
            "source_document_id": ev.source_document_id,
            "evidence_excerpt": ev.evidence_excerpt,
            "relation_note": ev.relation_note,
            "confidence": ev.confidence,
            "score_contribution": ev.score_contribution,
        })

    # Add experience to requirement matches
    requirement_match_records.append({
        "requirement_name": f"Experience ({job.min_years_experience or 0}+ years)",
        "category": "experience",
        "is_mandatory": True,
        "match_status": exp_outcome.match_status,
        "matched_candidate_skill": None,
        "matched_entity_id": None,
        "source_document_id": None,
        "evidence_excerpt": "; ".join(exp_outcome.evidence_excerpts[:2]),
        "relation_note": None,
        "confidence": exp_outcome.confidence,
        "score_contribution": round(score_res.experience_score / 100.0, 2),
    })

    # Add education
    requirement_match_records.append({
        "requirement_name": edu_outcome.requirement_name,
        "category": "education",
        "is_mandatory": edu_outcome.is_mandatory,
        "match_status": edu_outcome.match_status,
        "matched_candidate_skill": None,
        "matched_entity_id": edu_outcome.matched_entity_id,
        "source_document_id": edu_outcome.source_document_id,
        "evidence_excerpt": edu_outcome.evidence_excerpt,
        "relation_note": None,
        "confidence": edu_outcome.confidence,
        "score_contribution": round(score_res.education_score / 100.0, 2),
    })

    # Add certifications
    for cert in cert_outcomes:
        requirement_match_records.append({
            "requirement_name": cert.requirement_name,
            "category": "certification",
            "is_mandatory": cert.is_mandatory,
            "match_status": cert.match_status,
            "matched_candidate_skill": None,
            "matched_entity_id": cert.matched_entity_id,
            "source_document_id": cert.source_document_id,
            "evidence_excerpt": cert.evidence_excerpt,
            "relation_note": None,
            "confidence": cert.confidence,
            "score_contribution": 1.0 if cert.match_status == "STRONG_MATCH" else 0.0,
        })

    # Compile all gaps
    all_gaps: list[dict[str, object]] = (
        gap_res.missing_mandatory_skills
        + gap_res.missing_preferred_skills
        + gap_res.partially_met_requirements
        + gap_res.related_transferable_skills
        + gap_res.experience_gaps
        + gap_res.education_gaps
        + gap_res.certification_gaps
    )

    match_id = str(uuid.uuid4())
    match_record = MatchResult(
        id=match_id,
        profile_id=profile.id,
        job_id=job.id,
        overall_score=score_res.overall_score,
        mandatory_skill_score=score_res.mandatory_skill_score,
        preferred_skill_score=score_res.preferred_skill_score,
        experience_score=score_res.experience_score,
        education_score=score_res.education_score,
        certification_score=score_res.certification_score,
        domain_score=score_res.domain_score,
        evidence_coverage=score_res.evidence_coverage,
        conflict_impact=score_res.conflict_impact,
        score_breakdown_json=json.dumps(score_res.breakdown),
        requirement_matches_json=json.dumps(requirement_match_records),
        gaps_json=json.dumps(all_gaps),
        scoring_config_json=json.dumps(score_res.config_used),
        matching_version="1.0.0",
        is_stale=False,
        stale_reason=None,
        user_id=current_user.id if current_user else profile.user_id,
    )

    db.add(match_record)
    db.commit()
    db.refresh(match_record)

    record_activity(
        db=db,
        user_id=match_record.user_id,
        action="match_generated",
        title=f"Computed match fit {round(match_record.overall_score)}% for {job.title}",
        description=f"Coverage: {round(match_record.evidence_coverage * 100)}%, Mand. score: {round(match_record.mandatory_skill_score)}%",
        entity_type="match",
        entity_id=match_record.id,
    )

    logger.info(
        "Computed and stored match result",
        extra={"match_id": match_record.id, "score": match_record.overall_score},
    )
    return match_record


@router.get(
    "/{match_id}",
    response_model=MatchResultResponse,
    summary="Get match result by ID",
)
def get_match(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> MatchResult:
    """Retrieve full match assessment outcome and evidence breakdown."""
    match_rec = db.get(MatchResult, match_id)
    if not match_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result with ID '{match_id}' not found.",
        )
    return match_rec


@router.get(
    "",
    response_model=list[MatchResultListItemResponse],
    summary="List match results",
)
def list_matches(
    db: Annotated[Session, Depends(get_db)],
    profile_id: Annotated[str | None, Query()] = None,
    job_id: Annotated[str | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[MatchResult]:
    """Retrieve paginated match results with optional profile or job filters."""
    query = select(MatchResult).order_by(MatchResult.created_at.desc())
    if profile_id:
        query = query.where(MatchResult.profile_id == profile_id)
    if job_id:
        query = query.where(MatchResult.job_id == job_id)
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())


@router.get(
    "/{match_id}/requirements",
    response_model=RequirementMatchListResponse,
    summary="Get requirement-level evidence explanation",
)
def get_match_requirements(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> RequirementMatchListResponse:
    """Retrieve requirement-level evaluation with linked source documents and evidence."""
    match_rec = db.get(MatchResult, match_id)
    if not match_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result with ID '{match_id}' not found.",
        )

    items = [
        RequirementMatchItem(**item) for item in match_rec.requirement_matches
    ]
    return RequirementMatchListResponse(
        match_id=match_rec.id,
        profile_id=match_rec.profile_id,
        job_id=match_rec.job_id,
        requirements=items,
    )


@router.get(
    "/{match_id}/gaps",
    response_model=GapAnalysisResponse,
    summary="Get skill and experience gap analysis",
)
def get_match_gaps(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> GapAnalysisResponse:
    """Retrieve structured gap analysis with recommended evidence paths."""
    match_rec = db.get(MatchResult, match_id)
    if not match_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result with ID '{match_id}' not found.",
        )

    all_gaps = match_rec.gaps
    missing_mand = [
        g for g in all_gaps
        if g.get("category") not in ("experience", "education", "certification")
        and g.get("is_mandatory")
        and g.get("match_status") == "NO_EVIDENCE"
    ]
    missing_pref = [
        g for g in all_gaps
        if g.get("category") not in ("experience", "education", "certification")
        and not g.get("is_mandatory")
        and g.get("match_status") == "NO_EVIDENCE"
    ]
    partial_reqs = [g for g in all_gaps if g.get("match_status") == "PARTIAL_MATCH"]
    related_skills = [g for g in all_gaps if g.get("match_status") == "RELATED_MATCH"]
    exp_gaps = [g for g in all_gaps if g.get("category") == "experience"]
    edu_gaps = [g for g in all_gaps if g.get("category") == "education"]
    cert_gaps = [g for g in all_gaps if g.get("category") == "certification"]

    return GapAnalysisResponse(
        match_id=match_rec.id,
        profile_id=match_rec.profile_id,
        job_id=match_rec.job_id,
        total_gaps=len(all_gaps),
        missing_mandatory_skills=missing_mand,
        missing_preferred_skills=missing_pref,
        partially_met_requirements=partial_reqs,
        related_transferable_skills=related_skills,
        experience_gaps=exp_gaps,
        education_gaps=edu_gaps,
        certification_gaps=cert_gaps,
    )


@router.get(
    "/{match_id}/score",
    response_model=ScoreBreakdownResponse,
    summary="Get score breakdown and explainability",
)
def get_match_score(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ScoreBreakdownResponse:
    """Retrieve score breakdown with weights, sub-scores, penalties, and disclaimers."""
    match_rec = db.get(MatchResult, match_id)
    if not match_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result with ID '{match_id}' not found.",
        )

    bd = match_rec.score_breakdown
    return ScoreBreakdownResponse(
        overall_score=match_rec.overall_score,
        mandatory_skill_score=match_rec.mandatory_skill_score,
        preferred_skill_score=match_rec.preferred_skill_score,
        experience_score=match_rec.experience_score,
        education_score=match_rec.education_score,
        certification_score=match_rec.certification_score,
        domain_score=match_rec.domain_score,
        evidence_coverage=match_rec.evidence_coverage,
        conflict_impact=match_rec.conflict_impact,
        weights=bd.get("weights", {}),
        penalties_applied=bd.get("penalties_applied", []),
        disclaimer=bd.get("disclaimer", "Platform-generated alignment indicator."),
    )
