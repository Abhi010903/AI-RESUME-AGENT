"""Configurable scoring engine for evidence-based candidate-to-job matching."""

from dataclasses import dataclass, field
import logging
from typing import Any
from app.services.experience_matcher import ExperienceMatchOutcome
from app.services.qualification_matcher import QualificationEvaluationItem
from app.services.skill_matcher import SkillMatchEvaluation

logger = logging.getLogger("app.match_scorer")

DEFAULT_SCORING_WEIGHTS: dict[str, float] = {
    "mandatory_skills": 0.40,
    "experience": 0.20,
    "preferred_skills": 0.15,
    "education": 0.10,
    "domain": 0.10,
    "certifications": 0.05,
}

DISCLAIMER_TEXT = (
    "This score is a platform-generated alignment indicator based strictly on "
    "evidence in the candidate profile, not a hiring guarantee or probability."
)


@dataclass
class ComputedScore:
    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    domain_score: float
    evidence_coverage: float
    conflict_impact: float
    breakdown: dict[str, Any]
    config_used: dict[str, float]


def compute_match_score(
    skill_evaluations: list[SkillMatchEvaluation],
    experience_outcome: ExperienceMatchOutcome,
    education_outcome: QualificationEvaluationItem,
    certification_outcomes: list[QualificationEvaluationItem],
    custom_weights: dict[str, float] | None = None,
    has_unresolved_conflicts: bool = False,
) -> ComputedScore:
    """Compute weighted alignment score with evidence breakdown and penalty controls."""
    weights = dict(DEFAULT_SCORING_WEIGHTS)
    if custom_weights:
        # Merge custom weights and re-normalize to 1.0 sum
        total_w = sum(custom_weights.values())
        if total_w > 0:
            weights = {k: custom_weights.get(k, DEFAULT_SCORING_WEIGHTS[k]) / total_w for k in DEFAULT_SCORING_WEIGHTS}

    # 1. Mandatory Skills Score
    mand_evals = [e for e in skill_evaluations if e.is_mandatory]
    if mand_evals:
        mand_score = sum(e.score_contribution for e in mand_evals) / len(mand_evals) * 100.0
    else:
        mand_score = 100.0

    # 2. Preferred Skills Score
    pref_evals = [e for e in skill_evaluations if not e.is_mandatory]
    if pref_evals:
        pref_score = sum(e.score_contribution for e in pref_evals) / len(pref_evals) * 100.0
    else:
        pref_score = 100.0

    # 3. Experience Score
    if experience_outcome.required_years_min is None or experience_outcome.required_years_min == 0:
        exp_score = 100.0
    elif experience_outcome.candidate_years_relevant >= experience_outcome.required_years_min:
        exp_score = 100.0
    else:
        exp_score = min(100.0, (experience_outcome.candidate_years_relevant / experience_outcome.required_years_min) * 100.0)

    if experience_outcome.match_status == "CONFLICTED_EVIDENCE":
        exp_score = max(0.0, exp_score - 25.0)

    # 4. Education Score
    if education_outcome.match_status == "STRONG_MATCH":
        edu_score = 100.0
    elif education_outcome.match_status == "PARTIAL_MATCH":
        edu_score = 70.0
    elif education_outcome.match_status == "NOT_ASSESSED":
        edu_score = 100.0
    else:
        edu_score = 0.0

    # 5. Certifications Score
    if not certification_outcomes:
        cert_score = 100.0
    else:
        cert_points = 0.0
        for c in certification_outcomes:
            if c.match_status == "STRONG_MATCH":
                cert_points += 1.0
            elif c.match_status == "PARTIAL_MATCH":
                cert_points += 0.5
        cert_score = (cert_points / len(certification_outcomes)) * 100.0

    # 6. Domain Score (inferred from mandatory skills & experience alignment)
    domain_score = round((mand_score * 0.6) + (exp_score * 0.4), 1)

    # Weighted Sum
    raw_overall = (
        (mand_score * weights["mandatory_skills"])
        + (exp_score * weights["experience"])
        + (pref_score * weights["preferred_skills"])
        + (edu_score * weights["education"])
        + (domain_score * weights["domain"])
        + (cert_score * weights["certifications"])
    )

    # Penalties
    penalties_applied: list[str] = []
    conflict_impact = 0.0

    # Missing mandatory skills penalty:
    missing_mand_count = sum(1 for e in mand_evals if e.match_status in ("NO_EVIDENCE", "CONFLICTED_EVIDENCE"))
    if mand_evals and missing_mand_count > 0:
        penalty_ratio = missing_mand_count / len(mand_evals)
        mand_penalty = round(penalty_ratio * 25.0, 1)  # Up to 25% deduction
        raw_overall = max(0.0, raw_overall - mand_penalty)
        if penalty_ratio == 1.0:
            raw_overall = min(raw_overall, 25.0)
        penalties_applied.append(
            f"Missing {missing_mand_count}/{len(mand_evals)} mandatory skills resulted in a -{mand_penalty}% deduction."
        )

    # Unresolved profile conflicts penalty
    if has_unresolved_conflicts:
        conflict_impact = 8.0
        raw_overall = max(0.0, raw_overall - conflict_impact)
        penalties_applied.append("Unresolved conflicts in candidate profile resulted in an 8.0% score adjustment.")

    overall_score = round(max(0.0, min(100.0, raw_overall)), 1)

    # Evidence coverage calculation
    all_evals_count = len(skill_evaluations) + (1 if experience_outcome.required_years_min else 0)
    supported_count = sum(1 for e in skill_evaluations if e.match_status != "NO_EVIDENCE")
    if experience_outcome.candidate_years_total > 0 and experience_outcome.required_years_min:
        supported_count += 1
    evidence_cov = round(supported_count / all_evals_count, 2) if all_evals_count > 0 else 1.0

    breakdown = {
        "overall_score": overall_score,
        "mandatory_skill_score": round(mand_score, 1),
        "preferred_skill_score": round(pref_score, 1),
        "experience_score": round(exp_score, 1),
        "education_score": round(edu_score, 1),
        "certification_score": round(cert_score, 1),
        "domain_score": round(domain_score, 1),
        "evidence_coverage": evidence_cov,
        "conflict_impact": conflict_impact,
        "weights": weights,
        "penalties_applied": penalties_applied,
        "disclaimer": DISCLAIMER_TEXT,
    }

    return ComputedScore(
        overall_score=overall_score,
        mandatory_skill_score=round(mand_score, 1),
        preferred_skill_score=round(pref_score, 1),
        experience_score=round(exp_score, 1),
        education_score=round(edu_score, 1),
        certification_score=round(cert_score, 1),
        domain_score=round(domain_score, 1),
        evidence_coverage=evidence_cov,
        conflict_impact=conflict_impact,
        breakdown=breakdown,
        config_used=weights,
    )
