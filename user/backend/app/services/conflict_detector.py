"""Conflict detection engine for candidate profile intelligence.

Identifies date contradictions, overlapping roles, gaps, duplicate credentials,
and missing contact data across multiple ingested candidate resumes.
"""

from dataclasses import dataclass, field
import re
import uuid
from typing import Any
from app.services.profile_parser import ParsedEducation, ParsedExperience, ParsedResume


def parse_to_month_ordinal(date_str: str | None, is_end_boundary: bool = False) -> int | None:
    """Convert YYYY-MM or YYYY string into an integer month index for chronological comparison."""
    if not date_str:
        return None
    cleaned = date_str.strip().lower()
    if cleaned in ("present", "current", "now"):
        return 9999 * 12

    # Match YYYY-MM
    match_ym = re.match(r"^(\d{4})-(\d{1,2})$", cleaned)
    if match_ym:
        year = int(match_ym.group(1))
        month = int(match_ym.group(2))
        return year * 12 + month

    # Match Year only: YYYY
    match_y = re.match(r"^(\d{4})$", cleaned)
    if match_y:
        year = int(match_y.group(1))
        month = 12 if is_end_boundary else 1
        return year * 12 + month

    return None


@dataclass
class DetectedConflict:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: str = "GENERIC_CONFLICT"
    severity: str = "warning"  # "error", "warning", "info"
    description: str = ""
    affected_entities: list[str] = field(default_factory=list)
    resolution_status: str = "unresolved"
    resolution_notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "description": self.description,
            "affected_entities": self.affected_entities,
            "resolution_status": self.resolution_status,
            "resolution_notes": self.resolution_notes,
        }


def detect_contact_conflicts(parsed_resumes: list[ParsedResume]) -> list[DetectedConflict]:
    """Detect missing contact information or identity discrepancies across documents."""
    conflicts: list[DetectedConflict] = []

    # 1. Missing contact details
    primary_email = None
    primary_phone = None
    names: set[str] = set()
    emails: set[str] = set()

    for r in parsed_resumes:
        if r.full_name and r.full_name != "Candidate":
            names.add(r.full_name.strip().lower())
        if r.email:
            emails.add(r.email.strip().lower())
            if not primary_email:
                primary_email = r.email
        if r.phone and not primary_phone:
            primary_phone = r.phone

    if not primary_email:
        conflicts.append(
            DetectedConflict(
                conflict_type="MISSING_CONTACT_INFO",
                severity="warning",
                description="No contact email address could be extracted from submitted resume(s).",
                affected_entities=["email"],
            )
        )

    if not primary_phone:
        conflicts.append(
            DetectedConflict(
                conflict_type="MISSING_CONTACT_INFO",
                severity="info",
                description="No telephone or contact number was detected.",
                affected_entities=["phone"],
            )
        )

    # 2. Identity contradictions across multiple resumes
    if len(names) > 1:
        conflicts.append(
            DetectedConflict(
                conflict_type="IDENTITY_CONFLICT",
                severity="error",
                description=f"Differing candidate names detected across resumes: {', '.join(sorted(names))}",
                affected_entities=["full_name"],
            )
        )

    if len(emails) > 1:
        conflicts.append(
            DetectedConflict(
                conflict_type="IDENTITY_CONFLICT",
                severity="warning",
                description=f"Multiple distinct email addresses found: {', '.join(sorted(emails))}",
                affected_entities=["email"],
            )
        )

    return conflicts


def detect_experience_conflicts(experiences: list[ParsedExperience]) -> list[DetectedConflict]:
    """Detect date chronology errors, concurrent overlapping roles, and career gaps."""
    conflicts: list[DetectedConflict] = []
    dated_roles: list[tuple[int, int, ParsedExperience]] = []

    for exp in experiences:
        start_ord = parse_to_month_ordinal(exp.start_date, is_end_boundary=False)
        end_ord = parse_to_month_ordinal(exp.end_date, is_end_boundary=True)

        # 1. Invalid date sequence
        if start_ord is not None and end_ord is not None and start_ord > end_ord:
            conflicts.append(
                DetectedConflict(
                    conflict_type="EMPLOYMENT_DATE_INVALID",
                    severity="error",
                    description=(
                        f"End date '{exp.end_date}' precedes start date '{exp.start_date}' "
                        f"for role '{exp.job_title}' at '{exp.company}'."
                    ),
                    affected_entities=[f"{exp.company}:{exp.job_title}"],
                )
            )

        if start_ord is not None and end_ord is not None:
            dated_roles.append((start_ord, end_ord, exp))

    # Sort dated roles chronologically by start date
    dated_roles.sort(key=lambda item: item[0])

    # 2. Check for overlapping concurrent positions across different companies
    for i in range(len(dated_roles)):
        start_a, end_a, exp_a = dated_roles[i]
        for j in range(i + 1, len(dated_roles)):
            start_b, end_b, exp_b = dated_roles[j]

            # If role B starts before role A ends
            if start_b < end_a and exp_a.company.lower() != exp_b.company.lower():
                # Overlap detected
                conflicts.append(
                    DetectedConflict(
                        conflict_type="EMPLOYMENT_DATE_OVERLAP",
                        severity="warning",
                        description=(
                            f"Overlapping employment detected: '{exp_a.job_title}' at '{exp_a.company}' "
                            f"({exp_a.start_date} to {exp_a.end_date}) overlaps with '{exp_b.job_title}' "
                            f"at '{exp_b.company}' ({exp_b.start_date} to {exp_b.end_date})."
                        ),
                        affected_entities=[
                            f"{exp_a.company}:{exp_a.job_title}",
                            f"{exp_b.company}:{exp_b.job_title}",
                        ],
                    )
                )

    # 3. Detect significant unexplained employment gaps (> 6 months)
    max_end_so_far = -1
    for i in range(len(dated_roles) - 1):
        _, end_a, exp_a = dated_roles[i]
        start_b, _, exp_b = dated_roles[i + 1]

        max_end_so_far = max(max_end_so_far, end_a)

        # Ignore if an earlier role is ongoing or already covers past start_b
        if max_end_so_far >= 9999 * 12 or max_end_so_far >= start_b:
            continue

        gap_months = start_b - max_end_so_far
        if gap_months > 6:
            conflicts.append(
                DetectedConflict(
                    conflict_type="EMPLOYMENT_GAP",
                    severity="info",
                    description=(
                        f"Employment gap of approximately {gap_months} months detected between "
                        f"'{exp_a.company}' (ended {exp_a.end_date}) and '{exp_b.company}' "
                        f"(started {exp_b.start_date})."
                    ),
                    affected_entities=[exp_a.company, exp_b.company],
                )
            )

    return conflicts


def detect_education_conflicts(educations: list[ParsedEducation]) -> list[DetectedConflict]:
    """Detect inconsistent graduation dates or chronology contradictions."""
    conflicts: list[DetectedConflict] = []

    for edu in educations:
        start_ord = parse_to_month_ordinal(edu.start_date, is_end_boundary=False)
        end_ord = parse_to_month_ordinal(edu.end_date, is_end_boundary=True)

        if start_ord is not None and end_ord is not None and start_ord > end_ord:
            conflicts.append(
                DetectedConflict(
                    conflict_type="EDUCATION_DATE_CONFLICT",
                    severity="error",
                    description=(
                        f"Completion date '{edu.end_date}' occurs before start date '{edu.start_date}' "
                        f"for qualification '{edu.degree}' at '{edu.institution}'."
                    ),
                    affected_entities=[f"{edu.institution}:{edu.degree}"],
                )
            )

    return conflicts


def detect_all_conflicts(
    parsed_resumes: list[ParsedResume],
    consolidated_experiences: list[ParsedExperience],
    consolidated_education: list[ParsedEducation],
) -> list[DetectedConflict]:
    """Run comprehensive conflict evaluation suite across extracted and consolidated candidate facts."""
    all_conflicts: list[DetectedConflict] = []
    all_conflicts.extend(detect_contact_conflicts(parsed_resumes))
    all_conflicts.extend(detect_experience_conflicts(consolidated_experiences))
    all_conflicts.extend(detect_education_conflicts(consolidated_education))
    return all_conflicts
