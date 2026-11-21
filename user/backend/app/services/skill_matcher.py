"""Evidence-based skill matching engine evaluating candidate profile against job requirements."""

from dataclasses import dataclass, field
import logging
import re
from typing import Any
from app.models import CandidateProfile, JobDescription, Skill, WorkExperience
from app.services.skill_normalizer import (
    are_skills_related,
    get_related_skills,
    normalize_skill,
)

logger = logging.getLogger("app.skill_matcher")


@dataclass
class SkillMatchEvaluation:
    requirement_name: str
    category: str
    is_mandatory: bool
    match_status: str  # STRONG_MATCH, PARTIAL_MATCH, RELATED_MATCH, NO_EVIDENCE, CONFLICTED_EVIDENCE, NOT_ASSESSED
    matched_candidate_skill: str | None = None
    matched_entity_id: str | None = None
    source_document_id: str | None = None
    evidence_excerpt: str | None = None
    relation_note: str | None = None
    confidence: float = 1.0
    score_contribution: float = 0.0
    reason: str = ""


def _find_mention_in_experiences(
    skill_canonical: str,
    experiences: list[WorkExperience],
) -> tuple[WorkExperience | None, str | None]:
    """Search work experiences for direct mentions of a skill."""
    skill_lower = skill_canonical.lower()
    for exp in experiences:
        # Check skills_used
        for s in exp.skills_used:
            if normalize_skill(s)["canonical_name"].lower() == skill_lower:
                excerpt = f"Used in role '{exp.job_title}' at {exp.company}"
                return exp, excerpt
        # Check description with boundary lookaround supporting punctuation skills (e.g. C++, C#)
        if exp.description:
            pat = r"(?<![A-Za-z0-9_])" + re.escape(skill_lower) + r"(?![A-Za-z0-9_])"
            if re.search(pat, exp.description.lower()):
                excerpt = f"Demonstrated in experience at {exp.company}: {exp.description[:100]}..."
                return exp, excerpt
    return None, None


def evaluate_skill_matches(
    profile: CandidateProfile,
    job: JobDescription,
) -> list[SkillMatchEvaluation]:
    """Evaluate every required and preferred job skill against candidate profile evidence."""
    evaluations: list[SkillMatchEvaluation] = []

    candidate_skills: list[Skill] = profile.skills or []
    candidate_experiences: list[WorkExperience] = profile.experiences or []

    # Map candidate skills by canonical name
    cand_skill_map: dict[str, Skill] = {}
    for cs in candidate_skills:
        c_norm = normalize_skill(cs.name)["canonical_name"]
        cand_skill_map[c_norm.lower()] = cs

    # Track unresolved conflicts in profile
    conflict_entity_ids = set()
    for conf in profile.conflicts:
        if conf.get("resolution_status") == "unresolved":
            for aff in conf.get("affected_entities", []):
                conflict_entity_ids.add(aff)

    # Combine required and preferred skills from job
    all_job_skills: list[tuple[dict[str, Any], bool]] = []
    for s in job.required_skills:
        all_job_skills.append((s, True))
    for s in job.preferred_skills:
        all_job_skills.append((s, False))

    seen_req_skills: set[str] = set()

    for skill_dict, is_mandatory in all_job_skills:
        req_name = skill_dict["name"]
        canonical_req = normalize_skill(req_name)["canonical_name"]
        req_key = canonical_req.lower()

        if req_key in seen_req_skills:
            continue
        seen_req_skills.add(req_key)

        category = skill_dict.get("category", "General")

        # 1. Direct candidate skill match
        if req_key in cand_skill_map:
            cs = cand_skill_map[req_key]
            # Check if skill is tainted by unresolved conflict
            if cs.id in conflict_entity_ids:
                evaluations.append(
                    SkillMatchEvaluation(
                        requirement_name=canonical_req,
                        category=category,
                        is_mandatory=is_mandatory,
                        match_status="CONFLICTED_EVIDENCE",
                        matched_candidate_skill=cs.name,
                        matched_entity_id=cs.id,
                        source_document_id=cs.source_document_id,
                        evidence_excerpt=f"Extracted skill '{cs.name}' has unresolved conflict in candidate profile.",
                        confidence=0.5,
                        score_contribution=0.2,
                        reason="Candidate profile contains unresolved conflict affecting this skill.",
                    )
                )
                continue

            confidence = 1.0 if cs.is_approved else 0.9
            excerpt = f"Direct skill '{cs.name}' documented in candidate profile."
            if cs.years_of_experience:
                excerpt += f" ({cs.years_of_experience} yrs exp)"

            evaluations.append(
                SkillMatchEvaluation(
                    requirement_name=canonical_req,
                    category=category,
                    is_mandatory=is_mandatory,
                    match_status="STRONG_MATCH",
                    matched_candidate_skill=cs.name,
                    matched_entity_id=cs.id,
                    source_document_id=cs.source_document_id,
                    evidence_excerpt=excerpt,
                    confidence=confidence,
                    score_contribution=1.0,
                    reason=f"Candidate demonstrably possesses verified evidence of '{canonical_req}'.",
                )
            )
            continue

        # 2. Check Work Experience mentions
        exp_match, exp_excerpt = _find_mention_in_experiences(canonical_req, candidate_experiences)
        if exp_match:
            is_conflicted = exp_match.id in conflict_entity_ids
            status = "CONFLICTED_EVIDENCE" if is_conflicted else "STRONG_MATCH"
            score_contrib = 0.2 if is_conflicted else 0.9
            confidence = 0.6 if is_conflicted else (1.0 if exp_match.is_approved else 0.85)

            evaluations.append(
                SkillMatchEvaluation(
                    requirement_name=canonical_req,
                    category=category,
                    is_mandatory=is_mandatory,
                    match_status=status,
                    matched_candidate_skill=canonical_req,
                    matched_entity_id=exp_match.id,
                    source_document_id=exp_match.source_document_id,
                    evidence_excerpt=exp_excerpt or f"Demonstrated at {exp_match.company}",
                    confidence=confidence,
                    score_contribution=score_contrib,
                    reason=f"Demonstrated in work experience at {exp_match.company}.",
                )
            )
            continue

        # 3. Check Transferable / Related Skills
        best_related_eval: SkillMatchEvaluation | None = None
        for cand_key, cs in cand_skill_map.items():
            if cs.id in conflict_entity_ids:
                continue
            is_rel, note, strength = are_skills_related(canonical_req, cs.name)
            if is_rel and strength >= 0.5:
                # Related skill match
                contrib = round(0.35 * strength, 2)
                related_eval = SkillMatchEvaluation(
                    requirement_name=canonical_req,
                    category=category,
                    is_mandatory=is_mandatory,
                    match_status="RELATED_MATCH",
                    matched_candidate_skill=cs.name,
                    matched_entity_id=cs.id,
                    source_document_id=cs.source_document_id,
                    evidence_excerpt=f"Candidate has transferable skill '{cs.name}'. {note}",
                    relation_note=note,
                    confidence=0.7,
                    score_contribution=contrib,
                    reason=f"Transferable skill alignment: Candidate possesses '{cs.name}' which relates to '{canonical_req}'.",
                )
                if best_related_eval is None or contrib > (best_related_eval.score_contribution or 0.0):
                    best_related_eval = related_eval

        if best_related_eval:
            evaluations.append(best_related_eval)
            continue

        # 4. No Evidence
        evaluations.append(
            SkillMatchEvaluation(
                requirement_name=canonical_req,
                category=category,
                is_mandatory=is_mandatory,
                match_status="NO_EVIDENCE",
                confidence=1.0,
                score_contribution=0.0,
                reason="Not demonstrated in the available profile.",
            )
        )

    return evaluations
