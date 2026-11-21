"""Service for evaluating candidate Education and Certifications against job requirements."""

from dataclasses import dataclass, field
import logging
import re
from typing import Any
from app.models import CandidateProfile, Certification, Education, JobDescription

logger = logging.getLogger("app.qualification_matcher")

DEGREE_LEVELS = {
    "doctorate": 4,
    "ph.d": 4,
    "phd": 4,
    "master": 3,
    "m.s": 3,
    "ms": 3,
    "m.tech": 3,
    "mtech": 3,
    "bachelor": 2,
    "b.s": 2,
    "bs": 2,
    "b.a": 2,
    "ba": 2,
    "b.tech": 2,
    "btech": 2,
    "associate": 1,
}


@dataclass
class QualificationEvaluationItem:
    requirement_name: str
    category: str  # "education" or "certification"
    is_mandatory: bool
    match_status: str  # STRONG_MATCH, PARTIAL_MATCH, NO_EVIDENCE, NOT_ASSESSED
    matched_entity_id: str | None = None
    source_document_id: str | None = None
    evidence_excerpt: str | None = None
    confidence: float = 1.0
    notes: str = ""


def _infer_degree_level(degree_str: str | None) -> int:
    """Infer numeric hierarchy level of an academic degree."""
    if not degree_str:
        return 0
    lower = degree_str.lower()
    for key, lvl in DEGREE_LEVELS.items():
        if re.search(r"\b" + re.escape(key) + r"\b", lower):
            return lvl
    return 1  # Default non-zero level if degree text exists


def evaluate_education_match(
    profile: CandidateProfile,
    job: JobDescription,
) -> QualificationEvaluationItem:
    """Evaluate candidate education records against job education requirements."""
    required_edu = job.education_level
    if not required_edu:
        return QualificationEvaluationItem(
            requirement_name="Education",
            category="education",
            is_mandatory=False,
            match_status="NOT_ASSESSED",
            notes="No explicit education requirement specified in job description.",
        )

    educations = profile.education or []
    if not educations:
        return QualificationEvaluationItem(
            requirement_name=required_edu,
            category="education",
            is_mandatory=True,
            match_status="NO_EVIDENCE",
            notes="No education credentials demonstrated in candidate profile.",
        )

    required_level = _infer_degree_level(required_edu)

    req_edu_lower = required_edu.lower()
    subject_keywords = [
        "computer science", "software", "information technology", "data science",
        "engineering", "artificial intelligence", "machine learning", "mathematics",
        "statistics",
    ]
    req_subject = next((s for s in subject_keywords if s in req_edu_lower), None)

    def _check_subject(edu: Education) -> bool:
        if not req_subject:
            return True
        c_text = f"{edu.degree or ''} {edu.field_of_study or ''}".lower()
        if req_subject in c_text:
            return True
        if any(s in c_text for s in ["computer", "engineering", "tech", "software"]):
            return True
        if re.search(r"\bcs\b", c_text):
            return True
        return False

    best_match: Education | None = None
    best_level = 0
    best_has_subj = False

    for edu in educations:
        cand_level = _infer_degree_level(edu.degree)
        cand_has_subj = _check_subject(edu)

        if best_match is None:
            best_match = edu
            best_level = cand_level
            best_has_subj = cand_has_subj
        elif cand_has_subj and not best_has_subj and cand_level >= required_level:
            best_match = edu
            best_level = cand_level
            best_has_subj = True
        elif cand_has_subj == best_has_subj and cand_level > best_level:
            best_match = edu
            best_level = cand_level
            best_has_subj = cand_has_subj

    if best_match and best_level >= required_level:
        excerpt = f"{best_match.degree} from {best_match.institution}"
        if best_match.field_of_study:
            excerpt += f" in {best_match.field_of_study}"

        if req_subject and not best_has_subj:
            return QualificationEvaluationItem(
                requirement_name=required_edu,
                category="education",
                is_mandatory=True,
                match_status="PARTIAL_MATCH",
                matched_entity_id=best_match.id,
                source_document_id=best_match.source_document_id,
                evidence_excerpt=excerpt,
                confidence=0.75,
                notes=f"Candidate possesses {best_match.degree}, meeting degree level, but field of study does not establish required {req_subject}.",
            )

        return QualificationEvaluationItem(
            requirement_name=required_edu,
            category="education",
            is_mandatory=True,
            match_status="STRONG_MATCH",
            matched_entity_id=best_match.id,
            source_document_id=best_match.source_document_id,
            evidence_excerpt=excerpt,
            confidence=1.0,
            notes=f"Candidate possesses {best_match.degree}, meeting or exceeding {required_edu}.",
        )
    elif best_match:
        excerpt = f"{best_match.degree} from {best_match.institution}"
        return QualificationEvaluationItem(
            requirement_name=required_edu,
            category="education",
            is_mandatory=True,
            match_status="PARTIAL_MATCH",
            matched_entity_id=best_match.id,
            source_document_id=best_match.source_document_id,
            evidence_excerpt=excerpt,
            confidence=0.8,
            notes=f"Candidate has {best_match.degree}, which partially satisfies {required_edu}.",
        )

    return QualificationEvaluationItem(
        requirement_name=required_edu,
        category="education",
        is_mandatory=True,
        match_status="NO_EVIDENCE",
        notes=f"Education credentials do not establish required {required_edu}.",
    )


def evaluate_certifications_match(
    profile: CandidateProfile,
    job: JobDescription,
) -> list[QualificationEvaluationItem]:
    """Evaluate candidate professional certifications against job requirements."""
    results: list[QualificationEvaluationItem] = []
    job_certs = job.certifications or []
    candidate_certs = profile.certifications or []

    for req_cert in job_certs:
        req_norm = req_cert.lower().strip()
        matched_cert: Certification | None = None
        match_status = "NO_EVIDENCE"
        confidence = 1.0

        def _extract_cert_tier(val: str) -> str | None:
            m = re.search(r"\b(i{1,3}|iv|v|1|2|3|associate|professional|expert|practitioner|fundamentals|foundation)\b", val)
            return m.group(1) if m else None

        req_tier = _extract_cert_tier(req_norm)

        for cand_cert in candidate_certs:
            cand_norm = cand_cert.name.lower().strip()
            cand_tier = _extract_cert_tier(cand_norm)

            if req_norm == cand_norm:
                matched_cert = cand_cert
                match_status = "STRONG_MATCH"
                break

            # If both have explicit tiers and they differ, treat as partial at best
            if req_tier and cand_tier and req_tier != cand_tier:
                vendor_match = re.search(r"\b(aws|azure|gcp|kubernetes|scrum|pmp|cissp)\b", req_norm)
                if vendor_match and vendor_match.group(1) in cand_norm:
                    matched_cert = cand_cert
                    match_status = "PARTIAL_MATCH"
                    confidence = 0.6
                continue

            # Substring match if tiers do not conflict
            if (req_norm in cand_norm or cand_norm in req_norm) and (not req_tier or req_tier == cand_tier):
                matched_cert = cand_cert
                match_status = "STRONG_MATCH"
                break

            # Partial vendor match (e.g. AWS Certified vs AWS)
            vendor_match = re.search(r"\b(aws|azure|gcp|kubernetes|scrum|pmp|cissp)\b", req_norm)
            if vendor_match and vendor_match.group(1) in cand_norm:
                matched_cert = cand_cert
                match_status = "PARTIAL_MATCH"
                confidence = 0.7

        if matched_cert and match_status == "STRONG_MATCH":
            results.append(
                QualificationEvaluationItem(
                    requirement_name=req_cert,
                    category="certification",
                    is_mandatory=False,  # default certs to preferred unless specified
                    match_status="STRONG_MATCH",
                    matched_entity_id=matched_cert.id,
                    source_document_id=matched_cert.source_document_id,
                    evidence_excerpt=f"{matched_cert.name} (Issued by {matched_cert.issuing_organization or 'Unknown'})",
                    confidence=confidence,
                    notes=f"Verified certification '{matched_cert.name}' in candidate profile.",
                )
            )
        elif matched_cert and match_status == "PARTIAL_MATCH":
            results.append(
                QualificationEvaluationItem(
                    requirement_name=req_cert,
                    category="certification",
                    is_mandatory=False,
                    match_status="PARTIAL_MATCH",
                    matched_entity_id=matched_cert.id,
                    source_document_id=matched_cert.source_document_id,
                    evidence_excerpt=f"{matched_cert.name} (Issued by {matched_cert.issuing_organization or 'Unknown'})",
                    confidence=confidence,
                    notes=f"Related certification '{matched_cert.name}' demonstrated, partially meeting '{req_cert}'.",
                )
            )
        else:
            results.append(
                QualificationEvaluationItem(
                    requirement_name=req_cert,
                    category="certification",
                    is_mandatory=False,
                    match_status="NO_EVIDENCE",
                    notes="Not demonstrated in the available profile.",
                )
            )

    return results
