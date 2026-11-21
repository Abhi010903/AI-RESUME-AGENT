"""Structured gap analysis service between candidate profile and job requirements."""

from dataclasses import dataclass, field
import logging
from typing import Any
from app.services.experience_matcher import ExperienceMatchOutcome
from app.services.qualification_matcher import QualificationEvaluationItem
from app.services.skill_matcher import SkillMatchEvaluation

logger = logging.getLogger("app.gap_analyzer")


@dataclass
class GapAnalysisReport:
    total_gaps: int
    missing_mandatory_skills: list[dict[str, Any]] = field(default_factory=list)
    missing_preferred_skills: list[dict[str, Any]] = field(default_factory=list)
    partially_met_requirements: list[dict[str, Any]] = field(default_factory=list)
    related_transferable_skills: list[dict[str, Any]] = field(default_factory=list)
    experience_gaps: list[dict[str, Any]] = field(default_factory=list)
    education_gaps: list[dict[str, Any]] = field(default_factory=list)
    certification_gaps: list[dict[str, Any]] = field(default_factory=list)


def build_gap_analysis(
    skill_evaluations: list[SkillMatchEvaluation],
    experience_outcome: ExperienceMatchOutcome,
    education_outcome: QualificationEvaluationItem,
    certification_outcomes: list[QualificationEvaluationItem],
) -> GapAnalysisReport:
    """Analyze missing qualifications, partial evidence, and experience gaps."""
    missing_mand: list[dict[str, Any]] = []
    missing_pref: list[dict[str, Any]] = []
    partial_reqs: list[dict[str, Any]] = []
    related_skills: list[dict[str, Any]] = []
    exp_gaps: list[dict[str, Any]] = []
    edu_gaps: list[dict[str, Any]] = []
    cert_gaps: list[dict[str, Any]] = []

    # Process skills
    for ev in skill_evaluations:
        if ev.match_status == "NO_EVIDENCE":
            item = {
                "requirement_name": ev.requirement_name,
                "category": ev.category,
                "is_mandatory": ev.is_mandatory,
                "match_status": "NO_EVIDENCE",
                "reason": "Not demonstrated in the available candidate profile.",
                "recommended_evidence": (
                    f"Provide project, open-source repository, or employment bullet points "
                    f"demonstrating hands-on work with '{ev.requirement_name}'."
                ),
            }
            if ev.is_mandatory:
                missing_mand.append(item)
            else:
                missing_pref.append(item)
        elif ev.match_status == "PARTIAL_MATCH":
            partial_reqs.append({
                "requirement_name": ev.requirement_name,
                "category": ev.category,
                "is_mandatory": ev.is_mandatory,
                "match_status": "PARTIAL_MATCH",
                "reason": ev.reason or "Partial evidence found, but lacking verified depth or duration.",
                "recommended_evidence": f"Document production metrics and responsibilities using '{ev.requirement_name}'.",
            })
        elif ev.match_status == "RELATED_MATCH":
            related_skills.append({
                "requirement_name": ev.requirement_name,
                "category": ev.category,
                "is_mandatory": ev.is_mandatory,
                "match_status": "RELATED_MATCH",
                "reason": ev.reason,
                "recommended_evidence": (
                    f"Transferable experience present via '{ev.matched_candidate_skill}'. "
                    f"Highlight specific bridge projects using '{ev.requirement_name}' directly."
                ),
            })

    # Process experience
    if not experience_outcome.is_met and experience_outcome.required_years_min:
        exp_gaps.append({
            "requirement_name": f"{experience_outcome.required_years_min} years experience",
            "category": "experience",
            "is_mandatory": True,
            "match_status": experience_outcome.match_status,
            "reason": experience_outcome.assessment_notes,
            "recommended_evidence": (
                f"Candidate demonstrates {experience_outcome.candidate_years_relevant} years. "
                f"Highlight freelance, consulting, or project work to demonstrate the additional "
                f"{experience_outcome.gap_years} years."
            ),
        })

    # Process education
    if education_outcome.match_status == "NO_EVIDENCE":
        edu_gaps.append({
            "requirement_name": education_outcome.requirement_name,
            "category": "education",
            "is_mandatory": education_outcome.is_mandatory,
            "match_status": "NO_EVIDENCE",
            "reason": education_outcome.notes,
            "recommended_evidence": "Add formal academic degrees or equivalent accredited coursework.",
        })
    elif education_outcome.match_status == "PARTIAL_MATCH":
        edu_gaps.append({
            "requirement_name": education_outcome.requirement_name,
            "category": "education",
            "is_mandatory": education_outcome.is_mandatory,
            "match_status": "PARTIAL_MATCH",
            "reason": education_outcome.notes,
            "recommended_evidence": "Highlight degree equivalency or relevant certifications to bridge academic requirement.",
        })

    # Process certifications
    for cert in certification_outcomes:
        if cert.match_status == "NO_EVIDENCE":
            cert_gaps.append({
                "requirement_name": cert.requirement_name,
                "category": "certification",
                "is_mandatory": cert.is_mandatory,
                "match_status": "NO_EVIDENCE",
                "reason": cert.notes,
                "recommended_evidence": f"Acquire or link credential verification URL for '{cert.requirement_name}'.",
            })

    total = (
        len(missing_mand)
        + len(missing_pref)
        + len(partial_reqs)
        + len(related_skills)
        + len(exp_gaps)
        + len(edu_gaps)
        + len(cert_gaps)
    )

    return GapAnalysisReport(
        total_gaps=total,
        missing_mandatory_skills=missing_mand,
        missing_preferred_skills=missing_pref,
        partially_met_requirements=partial_reqs,
        related_transferable_skills=related_skills,
        experience_gaps=exp_gaps,
        education_gaps=edu_gaps,
        certification_gaps=cert_gaps,
    )
