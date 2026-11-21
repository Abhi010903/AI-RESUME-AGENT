"""Service for evaluating candidate work experience against job experience requirements."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import re
from typing import Any
from app.models import CandidateProfile, JobDescription, WorkExperience

logger = logging.getLogger("app.experience_matcher")


@dataclass
class ExperienceMatchOutcome:
    required_years_min: float | None
    required_years_max: float | None
    candidate_years_total: float
    candidate_years_relevant: float
    is_met: bool
    gap_years: float
    match_status: str  # STRONG_MATCH, PARTIAL_MATCH, NO_EVIDENCE, CONFLICTED_EVIDENCE
    evidence_excerpts: list[str] = field(default_factory=list)
    confidence: float = 1.0
    assessment_notes: str = ""


def _current_year_fraction() -> float:
    """Return current year plus elapsed months as a fractional year."""
    now = datetime.now(timezone.utc)
    return now.year + (now.month - 1.0) / 12.0


def _parse_year_float(date_str: str | None, is_end: bool = False) -> float | None:
    """Extract a decimal year representation (e.g. 2020.5 for mid-2020)."""
    if not date_str:
        return None

    cleaned = date_str.strip().lower()
    if cleaned in ("present", "current", "now"):
        return _current_year_fraction()

    # Extract 4-digit year
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)
    if not year_match:
        return None
    year = float(year_match.group(1))

    # Look for month (01-12)
    month_match = re.search(r"\b(0?[1-9]|1[0-2])\b", cleaned)
    if month_match and ("/" in cleaned or "-" in cleaned):
        month = float(month_match.group(1))
        return year + (month - 1.0) / 12.0

    return year + (0.99 if is_end else 0.0)


def calculate_non_overlapping_years(experiences: list[WorkExperience]) -> tuple[float, list[str]]:
    """Compute non-overlapping calendar experience duration and evidence excerpts."""
    intervals: list[tuple[float, float, str]] = []
    current_year = _current_year_fraction()

    for exp in experiences:
        start = _parse_year_float(exp.start_date, is_end=False)
        end = _parse_year_float(exp.end_date, is_end=True) if not exp.is_current else current_year

        if start is not None:
            if exp.is_current:
                end = current_year
            elif end is None:
                end = start + 0.25
            elif end < start:
                # Invalid reversed date range (e.g. 2018-01 to 2017-12)
                # Exclude from credited duration to prevent unsupported experience inflation
                continue
            label = f"{exp.job_title} at {exp.company} ({exp.start_date or '?'} - {exp.end_date or 'Present'})"
            intervals.append((start, end, label))

    if not intervals:
        return 0.0, []

    # Sort intervals by start date
    intervals.sort(key=lambda x: x[0])

    merged_intervals: list[tuple[float, float]] = []
    excerpts: list[str] = []

    cur_start, cur_end, cur_label = intervals[0]
    excerpts.append(cur_label)

    for start, end, label in intervals[1:]:
        excerpts.append(label)
        if start <= cur_end:
            # Overlap: extend end if needed
            cur_end = max(cur_end, end)
        else:
            merged_intervals.append((cur_start, cur_end))
            cur_start, cur_end = start, end

    merged_intervals.append((cur_start, cur_end))

    total_years = sum(max(0.0, end - start) for start, end in merged_intervals)
    return round(total_years, 1), excerpts


def evaluate_experience_match(
    profile: CandidateProfile,
    job: JobDescription,
) -> ExperienceMatchOutcome:
    """Evaluate candidate work experience against job description requirements."""
    required_min = job.min_years_experience
    required_max = job.max_years_experience

    experiences = profile.experiences or []
    if not experiences:
        return ExperienceMatchOutcome(
            required_years_min=required_min,
            required_years_max=required_max,
            candidate_years_total=0.0,
            candidate_years_relevant=0.0,
            is_met=required_min is None or required_min == 0,
            gap_years=required_min or 0.0,
            match_status="NO_EVIDENCE",
            evidence_excerpts=[],
            confidence=1.0,
            assessment_notes="No work experience records demonstrated in candidate profile.",
        )

    # Check for chronology conflicts in profile
    has_chronology_conflict = any(
        c.get("conflict_type") in ("chronology_conflict", "overlapping_employment", "EMPLOYMENT_DATE_INVALID", "EMPLOYMENT_DATE_OVERLAP")
        and c.get("resolution_status") == "unresolved"
        for c in profile.conflicts
    )

    total_years, excerpts = calculate_non_overlapping_years(experiences)

    # Calculate relevant years (aligned with job domain, title, or skills)
    raw_skills = (job.required_skills or []) + (job.preferred_skills or [])
    job_skills_norm = {
        (s.get("name", "") if isinstance(s, dict) else str(s)).lower()
        for s in raw_skills
        if s
    }

    target_job_keywords = set(re.findall(r"[a-z]+", job.title.lower())) - {
        "junior", "senior", "lead", "intern", "staff", "principal", "associate", "level", "ii", "iii", "at", "and", "the"
    }

    def _is_exp_relevant(e: WorkExperience) -> bool:
        t_low = (e.job_title or "").lower()
        d_low = (e.description or "").lower()
        # Direct skill overlap
        if any(s in t_low or s in d_low for s in job_skills_norm):
            return True
        # Title alignment with target job keywords
        exp_title_tokens = set(re.findall(r"[a-z]+", t_low))
        if target_job_keywords and bool(target_job_keywords & exp_title_tokens):
            return True
        return False

    relevant_exps = [e for e in experiences if _is_exp_relevant(e)]
    if relevant_exps:
        relevant_years, _ = calculate_non_overlapping_years(relevant_exps)
    else:
        relevant_years = 0.0

    if required_min is None or required_min == 0:
        return ExperienceMatchOutcome(
            required_years_min=None,
            required_years_max=required_max,
            candidate_years_total=total_years,
            candidate_years_relevant=relevant_years,
            is_met=True,
            gap_years=0.0,
            match_status="STRONG_MATCH",
            evidence_excerpts=excerpts,
            confidence=1.0,
            assessment_notes=f"No minimum experience required; candidate demonstrates {total_years} years.",
        )

    gap = max(0.0, round(required_min - relevant_years, 1))
    is_met = relevant_years >= required_min

    if has_chronology_conflict:
        match_status = "CONFLICTED_EVIDENCE"
        confidence = 0.6
        notes = (
            f"Candidate demonstrates ~{relevant_years} years against {required_min} required, "
            f"but has unresolved employment date conflicts."
        )
    elif is_met:
        match_status = "STRONG_MATCH"
        confidence = 1.0
        notes = f"Candidate demonstrates {relevant_years} years, meeting the {required_min} years required."
    elif relevant_years >= (required_min * 0.5):
        match_status = "PARTIAL_MATCH"
        confidence = 0.8
        notes = (
            f"Candidate demonstrates {relevant_years} years, which is a partial match for {required_min} years "
            f"({gap} years gap)."
        )
    else:
        match_status = "NO_EVIDENCE" if relevant_years == 0 else "PARTIAL_MATCH"
        confidence = 0.7
        notes = f"Significant experience gap: {relevant_years} years demonstrated vs {required_min} required."

    return ExperienceMatchOutcome(
        required_years_min=required_min,
        required_years_max=required_max,
        candidate_years_total=total_years,
        candidate_years_relevant=relevant_years,
        is_met=is_met,
        gap_years=gap,
        match_status=match_status,
        evidence_excerpts=excerpts,
        confidence=confidence,
        assessment_notes=notes,
    )
