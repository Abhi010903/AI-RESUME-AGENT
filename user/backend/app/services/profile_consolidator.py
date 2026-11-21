"""Consolidation service for candidate profile intelligence.

Fuses extracted resume information across 1 to 10 documents, deduplicating
records, preserving source document evidence, and running conflict evaluation.
"""

from collections.abc import Sequence
import json
import logging
from typing import Any
import uuid
from app.models import (
    CandidateProfile,
    Certification,
    Document,
    Education,
    Skill,
    WorkExperience,
)
from app.services.conflict_detector import detect_all_conflicts
from app.services.profile_parser import (
    ParsedCertification,
    ParsedEducation,
    ParsedExperience,
    ParsedProject,
    ParsedResume,
    ParsedSkill,
    parse_resume_text,
)

logger = logging.getLogger("app.profile_consolidator")


def normalize_entity_key(text: str) -> str:
    """Normalize text strings for fuzzy/canonical matching."""
    return "".join(ch for ch in text.lower() if ch.isalnum())


def normalize_skill_key(text: str) -> str:
    """Normalize skill names while preserving +, #, and . (e.g. C++, C#, .NET)."""
    cleaned = "".join(ch for ch in text.strip().lower() if ch.isalnum() or ch in {"+", "#", "."})
    return cleaned or normalize_entity_key(text)


def _parse_year_month(date_str: str | None) -> tuple[int, int] | None:
    if not date_str:
        return None
    import re
    m = re.search(r"(\d{4})(?:[-/](\d{1,2}))?", str(date_str))
    if m:
        year = int(m.group(1))
        month = int(m.group(2)) if m.group(2) else 1
        return (year, month)
    return None


def _earlier_date(d1: str | None, d2: str | None) -> str | None:
    if not d1:
        return d2
    if not d2:
        return d1
    ym1 = _parse_year_month(d1)
    ym2 = _parse_year_month(d2)
    if ym1 and ym2:
        return d1 if ym1 <= ym2 else d2
    return d1 or d2


def _later_date(d1: str | None, d2: str | None) -> str | None:
    if not d1:
        return d2
    if not d2:
        return d1
    if "present" in d1.lower() or "current" in d1.lower():
        return d1
    if "present" in d2.lower() or "current" in d2.lower():
        return d2
    ym1 = _parse_year_month(d1)
    ym2 = _parse_year_month(d2)
    if ym1 and ym2:
        return d1 if ym1 >= ym2 else d2
    return d1 or d2


def merge_experiences(all_parsed: list[tuple[str, ParsedExperience]]) -> list[tuple[str, ParsedExperience]]:
    """Merge duplicate experiences at the same company with similar titles and overlapping/compatible dates."""
    merged: list[tuple[str, ParsedExperience]] = []

    for doc_id, exp in all_parsed:
        comp_key = normalize_entity_key(exp.company)
        title_key = normalize_entity_key(exp.job_title)

        matched_idx = -1
        for i, (ex_doc_id, existing_exp) in enumerate(merged):
            if normalize_entity_key(existing_exp.company) == comp_key and normalize_entity_key(existing_exp.job_title) == title_key:
                ym_ex_start = _parse_year_month(existing_exp.start_date)
                ym_ex_end = _parse_year_month(existing_exp.end_date)
                ym_new_start = _parse_year_month(exp.start_date)
                ym_new_end = _parse_year_month(exp.end_date)

                if not (ym_ex_start and ym_new_start):
                    matched_idx = i
                    break

                ex_is_curr = existing_exp.is_current or (existing_exp.end_date and "present" in existing_exp.end_date.lower())
                new_is_curr = exp.is_current or (exp.end_date and "present" in exp.end_date.lower())

                dates_overlap = True
                if ym_ex_end and ym_new_start and not ex_is_curr and ym_ex_end < ym_new_start:
                    dates_overlap = False
                elif ym_new_end and ym_ex_start and not new_is_curr and ym_new_end < ym_ex_start:
                    dates_overlap = False

                if dates_overlap:
                    matched_idx = i
                    break

        if matched_idx >= 0:
            existing_doc_id, existing_exp = merged[matched_idx]
            # Merge descriptions
            descs = [d for d in [existing_exp.description, exp.description] if d]
            combined_desc = "\n".join(dict.fromkeys(descs)) if descs else None

            # Merge skills used
            combined_skills = list(dict.fromkeys(existing_exp.skills_used + exp.skills_used))

            # Retain earliest start date & latest end date
            start = _earlier_date(existing_exp.start_date, exp.start_date)
            is_curr = existing_exp.is_current or exp.is_current or ("present" in (existing_exp.end_date or "").lower()) or ("present" in (exp.end_date or "").lower())
            end = "Present" if is_curr else _later_date(existing_exp.end_date, exp.end_date)

            # Retain provenance from both source documents
            combined_doc_id = ", ".join(dict.fromkeys(filter(None, [existing_doc_id, doc_id])))

            merged[matched_idx] = (
                combined_doc_id,
                ParsedExperience(
                    company=existing_exp.company,
                    job_title=existing_exp.job_title,
                    location=existing_exp.location or exp.location,
                    start_date=start,
                    end_date=end,
                    is_current=is_curr,
                    description=combined_desc,
                    skills_used=combined_skills,
                    raw_text=f"{existing_exp.raw_text or ''}\n---\n{exp.raw_text or ''}".strip(),
                    confidence_score=max(existing_exp.confidence_score, exp.confidence_score),
                ),
            )
        else:
            merged.append((doc_id, exp))

    return merged


def merge_education(all_parsed: list[tuple[str, ParsedEducation]]) -> list[tuple[str, ParsedEducation]]:
    """Deduplicate education entries by institution and degree."""
    merged: dict[str, tuple[str, ParsedEducation]] = {}

    for doc_id, edu in all_parsed:
        key = f"{normalize_entity_key(edu.institution)}:{normalize_entity_key(edu.degree)}:{normalize_entity_key(edu.field_of_study or '')}"

        if key in merged:
            existing_doc_id, existing_edu = merged[key]
            combined_doc_id = ", ".join(dict.fromkeys(filter(None, [existing_doc_id, doc_id])))
            merged[key] = (
                combined_doc_id,
                ParsedEducation(
                    institution=existing_edu.institution,
                    degree=existing_edu.degree,
                    field_of_study=existing_edu.field_of_study or edu.field_of_study,
                    start_date=existing_edu.start_date or edu.start_date,
                    end_date=existing_edu.end_date or edu.end_date,
                    grade=existing_edu.grade or edu.grade,
                    raw_text=existing_edu.raw_text or edu.raw_text,
                ),
            )
        else:
            merged[key] = (doc_id, edu)

    return list(merged.values())


def merge_skills(all_parsed: list[tuple[str, ParsedSkill]]) -> list[tuple[str, ParsedSkill]]:
    """Deduplicate skills case-insensitively, preserving canonical casing and distinct punctuation (C, C++, C#)."""
    merged: dict[str, tuple[str, ParsedSkill]] = {}

    for doc_id, skill in all_parsed:
        key = normalize_skill_key(skill.name)
        if key not in merged:
            merged[key] = (doc_id, skill)

    return list(merged.values())


def merge_certifications(all_parsed: list[tuple[str, ParsedCertification]]) -> list[tuple[str, ParsedCertification]]:
    """Deduplicate professional certifications by name."""
    merged: dict[str, tuple[str, ParsedCertification]] = {}

    for doc_id, cert in all_parsed:
        key = normalize_entity_key(cert.name)
        if key in merged:
            existing_doc_id, existing_cert = merged[key]
            merged[key] = (
                existing_doc_id,
                ParsedCertification(
                    name=existing_cert.name,
                    issuing_organization=existing_cert.issuing_organization or cert.issuing_organization,
                    issue_date=existing_cert.issue_date or cert.issue_date,
                    expiry_date=existing_cert.expiry_date or cert.expiry_date,
                    credential_id=existing_cert.credential_id or cert.credential_id,
                    credential_url=existing_cert.credential_url or cert.credential_url,
                    raw_text=existing_cert.raw_text or cert.raw_text,
                ),
            )
        else:
            merged[key] = (doc_id, cert)

    return list(merged.values())


def merge_projects(all_parsed: list[tuple[str, ParsedProject]]) -> list[dict[str, Any]]:
    """Merge duplicate projects with similar names, unioning technologies, bullets, and provenance."""
    merged: dict[str, dict[str, Any]] = {}
    for doc_id, proj in all_parsed:
        key = normalize_entity_key(proj.name)
        if not key:
            continue
        if key in merged:
            existing = merged[key]
            all_tech = existing["technologies"] + [t for t in proj.technologies if t not in existing["technologies"]]
            all_bullets = existing["bullets"] + [b for b in proj.bullets if b not in existing["bullets"]]
            existing["technologies"] = all_tech
            existing["bullets"] = all_bullets
            if not existing.get("subtitle") and proj.role_or_subtitle:
                existing["subtitle"] = proj.role_or_subtitle
            # Retain provenance from both source documents
            existing_doc_id = existing.get("source_document_id")
            existing["source_document_id"] = ", ".join(dict.fromkeys(filter(None, [existing_doc_id, doc_id])))
        else:
            merged[key] = {
                "name": proj.name,
                "subtitle": proj.role_or_subtitle,
                "technologies": list(proj.technologies),
                "description": proj.description,
                "bullets": list(proj.bullets),
                "source_document_id": doc_id,
            }
    return list(merged.values())


def merge_achievements(all_parsed: list[list[str]]) -> list[str]:
    """Deduplicate achievements preserving original phrasing and order."""
    seen = set()
    merged = []
    for ach_list in all_parsed:
        for a in ach_list:
            cleaned = a.strip()
            key = normalize_entity_key(cleaned)
            if key and key not in seen:
                seen.add(key)
                merged.append(cleaned)
    return merged


def consolidate_documents_into_profile(
    documents: Sequence[Document],
    user_id: str | None = None,
    existing_profile: CandidateProfile | None = None,
) -> CandidateProfile:
    """Consolidate multiple resume documents into a single unified CandidateProfile ORM instance."""
    if not documents:
        raise ValueError("At least one document is required for consolidation.")

    # 1. Parse each resume individually
    parsed_resumes: list[ParsedResume] = []
    all_raw_experiences: list[tuple[str, ParsedExperience]] = []
    all_raw_education: list[tuple[str, ParsedEducation]] = []
    all_raw_skills: list[tuple[str, ParsedSkill]] = []
    all_raw_certs: list[tuple[str, ParsedCertification]] = []
    all_raw_projects: list[tuple[str, ParsedProject]] = []
    all_raw_achievements: list[list[str]] = []

    for doc in documents:
        text = doc.extracted_text or ""
        parsed = parse_resume_text(text, doc.id)
        parsed_resumes.append(parsed)

        for exp in parsed.experiences:
            all_raw_experiences.append((doc.id, exp))
        for edu in parsed.education:
            all_raw_education.append((doc.id, edu))
        for sk in parsed.skills:
            all_raw_skills.append((doc.id, sk))
        for ct in parsed.certifications:
            all_raw_certs.append((doc.id, ct))
        for prj in parsed.projects:
            all_raw_projects.append((doc.id, prj))
        if parsed.achievements:
            all_raw_achievements.append(parsed.achievements)

    # 2. Merge overlapping entities
    consolidated_experiences = merge_experiences(all_raw_experiences)
    consolidated_education = merge_education(all_raw_education)
    consolidated_skills = merge_skills(all_raw_skills)
    consolidated_certs = merge_certifications(all_raw_certs)
    consolidated_projects = merge_projects(all_raw_projects)
    consolidated_achievements = merge_achievements(all_raw_achievements)

    # 3. Detect conflicts
    raw_exp_list = [exp for _, exp in consolidated_experiences]
    raw_edu_list = [edu for _, edu in consolidated_education]
    detected_conflicts = detect_all_conflicts(parsed_resumes, raw_exp_list, raw_edu_list)

    # 4. Construct candidate profile attributes
    full_name = "Candidate"
    email = None
    phone = None
    linkedin_url = None
    github_url = None
    summaries: list[str] = []

    for pr in parsed_resumes:
        if pr.full_name and pr.full_name != "Candidate" and full_name == "Candidate":
            full_name = pr.full_name
        if pr.email and not email:
            email = pr.email
        if pr.phone and not phone:
            phone = pr.phone
        if pr.linkedin_url and not linkedin_url:
            linkedin_url = pr.linkedin_url
        if pr.github_url and not github_url:
            github_url = pr.github_url
        if pr.summary:
            summaries.append(pr.summary)

    profile_id = existing_profile.id if existing_profile else str(uuid.uuid4())
    doc_ids = [d.id for d in documents]

    profile = existing_profile or CandidateProfile(id=profile_id)
    profile.user_id = user_id or profile.user_id
    profile.full_name = full_name
    profile.email = email
    profile.phone = phone
    profile.linkedin_url = linkedin_url
    profile.github_url = github_url
    profile.summary = "\n\n".join(dict.fromkeys(summaries)) if summaries else None
    profile.set_source_document_ids(doc_ids)
    profile.set_conflicts([c.to_dict() for c in detected_conflicts])
    profile.set_projects(consolidated_projects)
    profile.set_achievements(consolidated_achievements)
    profile.verification_status = "unverified"
    profile.is_approved = False

    # 5. Populate child models with source traceability
    profile.experiences = [
        WorkExperience(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            company=exp.company,
            job_title=exp.job_title,
            location=exp.location,
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            description=exp.description,
            skills_used_json=json.dumps(exp.skills_used) if exp.skills_used else None,
            source_document_id=src_doc_id,
            confidence_score=exp.confidence_score,
            is_approved=False,
            raw_text=exp.raw_text,
        )
        for src_doc_id, exp in consolidated_experiences
    ]

    profile.education = [
        Education(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            institution=edu.institution,
            degree=edu.degree,
            field_of_study=edu.field_of_study,
            start_date=edu.start_date,
            end_date=edu.end_date,
            grade=edu.grade,
            source_document_id=src_doc_id,
            is_approved=False,
            raw_text=edu.raw_text,
        )
        for src_doc_id, edu in consolidated_education
    ]

    profile.skills = [
        Skill(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            name=sk.name,
            category=sk.category,
            proficiency=sk.proficiency,
            source_document_id=src_doc_id,
            is_approved=False,
        )
        for src_doc_id, sk in consolidated_skills
    ]

    profile.certifications = [
        Certification(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            name=ct.name,
            issuing_organization=ct.issuing_organization,
            issue_date=ct.issue_date,
            expiry_date=ct.expiry_date,
            credential_id=ct.credential_id,
            credential_url=ct.credential_url,
            source_document_id=src_doc_id,
            is_approved=False,
            raw_text=ct.raw_text,
        )
        for src_doc_id, ct in consolidated_certs
    ]

    logger.info(
        "Consolidated profile %s across %d documents with %d conflicts",
        profile.id,
        len(documents),
        len(detected_conflicts),
    )
    return profile
