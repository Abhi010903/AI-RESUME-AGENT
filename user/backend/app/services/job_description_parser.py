"""Deterministic parser and classifier for unstructured job descriptions."""

from dataclasses import dataclass, field
import logging
import re
from typing import Any
from app.services.skill_normalizer import (
    extract_known_skills_from_text,
    normalize_skill,
)

logger = logging.getLogger("app.job_description_parser")

# Section Header Regex Patterns
SECTION_HEADERS = {
    "responsibilities": re.compile(
        r"^(?:##\s*)?(?:responsibilities|key\s+responsibilities|what\s+you(?:'ll|\s+will)\s+do|duties|the\s+role|role\s+responsibilities|day\s+to\s+day)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
    "required": re.compile(
        r"^(?:##\s*)?(?:requirements|required(?:\s+(?:qualifications|skills|requirements))?|basic\s+qualifications|minimum\s+qualifications|must\s+haves?|what\s+you\s+need|what\s+we(?:'re|\s+are)\s+looking\s+for|essential\s+skills)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
    "preferred": re.compile(
        r"^(?:##\s*)?(?:preferred(?:\s+(?:qualifications|skills|requirements))?|nice\s+to\s+haves?|bonus(?:\s+points?)?|pluses?|desirable|what\s+gives\s+you\s+an\s+edge|good\s+to\s+have)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:##\s*)?(?:education|academic\s+requirements|degrees)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:##\s*)?(?:certifications|licenses|credentials)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
    "about": re.compile(
        r"^(?:##\s*)?(?:about\s+the\s+company|about\s+us|who\s+we\s+are|company\s+overview|job\s+summary|overview)(?:\s*:|\b)",
        re.IGNORECASE,
    ),
}

# Explicit phrase patterns for classification
MANDATORY_MARKERS = re.compile(
    r"\b(?:must\s+have|must\s+possess|required|mandatory|essential|minimum\s+of|strictly\s+required|at\s+least)\b",
    re.IGNORECASE,
)
PREFERRED_MARKERS = re.compile(
    r"\b(?:preferred|nice\s+to\s+have|bonus|is\s+a\s+plus|desirable|advantageous|a\s+plus|optional|good\s+to\s+have)\b",
    re.IGNORECASE,
)

# Experience extraction pattern
YEARS_EXP_REGEX = re.compile(
    r"\b(?:(?:at\s+least|minimum(?:\s+of)?)\s+)?(\d{1,2})(?:\s*(?:-|to)\s*(\d{1,2}))?\+?\s*years?(?:\s+of)?\s*(?:[A-Za-z\s-]{0,35})?\s*(?:experience|exp)",
    re.IGNORECASE,
)

# Seniority level regex
SENIORITY_REGEX = re.compile(
    r"\b(Intern|Junior|Jr\.?|Entry[\s-]level|Associate|Mid[\s-]level|Senior|Sr\.?|Lead|Principal|Staff|Director|VP|Head\s+of)\b",
    re.IGNORECASE,
)

# Employment type regex
EMPLOYMENT_TYPE_REGEX = re.compile(
    r"\b(Full[\s-]time|Part[\s-]time|Contract(?:or)?|Temporary|Freelance|Internship)\b",
    re.IGNORECASE,
)

# Location / Work style regex
LOCATION_REGEX = re.compile(
    r"\b(Remote|Hybrid|On[\s-]site|Onsite)\b",
    re.IGNORECASE,
)

# Education level regex
EDUCATION_REGEX = re.compile(
    r"\b(Bachelor(?:'s)?(?:\s+degree)?|Master(?:'s)?(?:\s+degree)?|Ph\.?D\.?|Doctorate|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|B\.?Tech|M\.?Tech|Associate(?:'s)?(?:\s+degree)?)\b(?:\s+(?:in|of)\s+([A-Za-z\s,\/]+))?",
    re.IGNORECASE,
)

# Certifications regex
CERTIFICATION_REGEX = re.compile(
    r"\b(AWS\s+Certified(?:\s+[A-Za-z]+)?|Azure\s+Certified|GCP\s+Certified|CKA|CKAD|CISSP|PMP|CompTIA(?:\s+[A-Za-z0-9\+]+)?|Scrum\s+Master|CSM)\b",
    re.IGNORECASE,
)

# Soft skills keywords
SOFT_SKILLS = [
    "Communication",
    "Leadership",
    "Problem-solving",
    "Collaboration",
    "Teamwork",
    "Mentorship",
    "Critical Thinking",
    "Time Management",
    "Adaptability",
    "Ownership",
    "Creativity",
]


@dataclass
class ParsedJobRequirement:
    name: str
    category: str
    is_mandatory: bool
    raw_text: str
    normalized_name: str
    priority: str = "high"
    confidence: float = 1.0
    is_ambiguous: bool = False


@dataclass
class ParsedJobDescription:
    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    summary: str | None = None
    raw_text: str = ""
    normalized_text: str | None = None
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    education_level: str | None = None

    responsibilities: list[str] = field(default_factory=list)
    required_skills: list[dict[str, Any]] = field(default_factory=list)
    preferred_skills: list[dict[str, Any]] = field(default_factory=list)
    required_qualifications: list[str] = field(default_factory=list)
    preferred_qualifications: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    quality_warnings: list[str] = field(default_factory=list)

    detailed_requirements: list[ParsedJobRequirement] = field(default_factory=list)


def parse_job_description(
    raw_text: str,
    supplied_title: str | None = None,
    supplied_company: str | None = None,
    supplied_location: str | None = None,
    supplied_employment_type: str | None = None,
    supplied_seniority: str | None = None,
) -> ParsedJobDescription:
    """Parse unstructured job description into structured requirements and entities."""
    warnings: list[str] = []

    # Clean text
    clean_text = raw_text.strip()
    if not clean_text:
        return ParsedJobDescription(
            title=supplied_title or "Untitled Position",
            raw_text=raw_text,
            quality_warnings=["Empty job description text submitted."],
        )

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    word_count = len(clean_text.split())

    if word_count < 40:
        warnings.append("Job description is unusually short and may lack complete requirements.")

    # 1. Section Segmentation
    current_section = "overview"
    section_lines: dict[str, list[str]] = {
        "overview": [],
        "responsibilities": [],
        "required": [],
        "preferred": [],
        "education": [],
        "certifications": [],
        "about": [],
    }

    for line in lines:
        header_matched = None
        for sec_name, sec_regex in SECTION_HEADERS.items():
            if sec_regex.match(line):
                header_matched = sec_name
                break

        if header_matched:
            current_section = header_matched
        else:
            section_lines[current_section].append(line)

    # 2. Extract Metadata (Title, Company, Location, Seniority, Employment Type)
    title = supplied_title
    if not title:
        # Check first line or lines starting with Job Title / Role
        for line in lines[:5]:
            title_match = re.match(r"^(?:Job\s+Title|Title|Position|Role):\s*(.+)$", line, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                break
        if not title and lines:
            first_line = re.sub(r"^[#\s*\-]+", "", lines[0]).strip()
            # If first line looks like a title (short, no period at end)
            if len(first_line) < 80 and not first_line.endswith("."):
                title = first_line

    if title:
        title = re.sub(r"^[#\s*\-]+", "", title).strip()
        # Separate title and company if formatted as "Role — Company"
        if not supplied_company and any(sep in title for sep in [" — ", " – ", " | "]):
            t_parts = re.split(r"\s*(?:—|–|\|)\s*", title, maxsplit=1)
            title = t_parts[0].strip()
            if len(t_parts) > 1 and not supplied_company:
                supplied_company = t_parts[1].strip()

    if not title:
        title = "Untitled Position"
        warnings.append("Missing job title in job description.")

    company = supplied_company
    if not company:
        for line in lines[:8]:
            company_match = re.match(r"^(?:Company|Organization|Employer):\s*(.+)$", line, re.IGNORECASE)
            if company_match:
                company = company_match.group(1).strip()
                break
            at_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&., ]{2,30})\b", line)
            if at_match and not company:
                company = at_match.group(1).strip()

    location = supplied_location
    if not location:
        for line in lines[:10]:
            loc_match = re.match(r"^(?:Location|Work\s+Location):\s*(.+)$", line, re.IGNORECASE)
            if loc_match:
                location = loc_match.group(1).strip()
                break
        if not location:
            loc_style = LOCATION_REGEX.search(clean_text[:500])
            if loc_style:
                location = loc_style.group(1)

    seniority = supplied_seniority
    if not seniority:
        sen_match = SENIORITY_REGEX.search(title) or SENIORITY_REGEX.search(clean_text[:600])
        if sen_match:
            seniority = sen_match.group(1).title()

    employment_type = supplied_employment_type
    if not employment_type:
        emp_match = EMPLOYMENT_TYPE_REGEX.search(clean_text[:800])
        if emp_match:
            employment_type = emp_match.group(1).title()

    # 3. Extract Experience Requirements
    min_exp: float | None = None
    max_exp: float | None = None
    exp_matches = list(YEARS_EXP_REGEX.finditer(clean_text))
    for m in exp_matches:
        min_val = float(m.group(1))
        # Ignore unreasonable year values that might be years AD (e.g. 2024)
        if min_val > 40:
            continue
        max_val = float(m.group(2)) if m.group(2) else None
        if min_exp is None or min_val < min_exp:
            min_exp = min_val
        if max_val and (max_exp is None or max_val > max_exp):
            max_exp = max_val

    # 4. Extract Education and Certifications
    education_level: str | None = None
    edu_match = EDUCATION_REGEX.search(clean_text)
    if edu_match:
        education_level = edu_match.group(1)
        if edu_match.group(2):
            education_level += f" in {edu_match.group(2).strip()}"

    certifications: list[str] = []
    for cert_match in CERTIFICATION_REGEX.finditer(clean_text):
        cert_name = cert_match.group(1).strip()
        if cert_name not in certifications:
            certifications.append(cert_name)

    # 5. Extract Responsibilities
    responsibilities: list[str] = []
    for line in section_lines["responsibilities"]:
        # Strip bullets
        cleaned = re.sub(r"^[\*\-•\d+\.]\s*", "", line).strip()
        if len(cleaned) > 10 and not any(h.match(cleaned) for h in SECTION_HEADERS.values()):
            responsibilities.append(cleaned)

    # 6. Extract Requirements and Classify Mandatory vs Preferred
    required_qualifications: list[str] = []
    preferred_qualifications: list[str] = []
    detailed_requirements: list[ParsedJobRequirement] = []

    # Process explicit required section
    for line in section_lines["required"]:
        cleaned = re.sub(r"^[\*\-•\d+\.]\s*", "", line).strip()
        if len(cleaned) < 5 or any(h.match(cleaned) for h in SECTION_HEADERS.values()):
            continue
        # Even inside required section, look for "preferred" marker inside bullet
        if PREFERRED_MARKERS.search(cleaned):
            preferred_qualifications.append(cleaned)
            is_mandatory = False
            priority = "medium"
        else:
            required_qualifications.append(cleaned)
            is_mandatory = True
            priority = "high"

        detailed_requirements.append(
            ParsedJobRequirement(
                name=cleaned[:100],
                category="qualification",
                is_mandatory=is_mandatory,
                raw_text=cleaned,
                normalized_name=cleaned[:100],
                priority=priority,
                confidence=1.0,
                is_ambiguous=False,
            )
        )

    # Process explicit preferred section
    for line in section_lines["preferred"]:
        cleaned = re.sub(r"^[\*\-•\d+\.]\s*", "", line).strip()
        if len(cleaned) < 5 or any(h.match(cleaned) for h in SECTION_HEADERS.values()):
            continue
        preferred_qualifications.append(cleaned)
        detailed_requirements.append(
            ParsedJobRequirement(
                name=cleaned[:100],
                category="qualification",
                is_mandatory=False,
                raw_text=cleaned,
                normalized_name=cleaned[:100],
                priority="medium",
                confidence=1.0,
                is_ambiguous=False,
            )
        )

    # If no separate required/preferred sections were detected, inspect lines in overview
    if not required_qualifications and not preferred_qualifications:
        for line in lines:
            cleaned = re.sub(r"^[\*\-•\d+\.]\s*", "", line).strip()
            if len(cleaned) < 10:
                continue
            if MANDATORY_MARKERS.search(cleaned):
                required_qualifications.append(cleaned)
                detailed_requirements.append(
                    ParsedJobRequirement(
                        name=cleaned[:100],
                        category="qualification",
                        is_mandatory=True,
                        raw_text=cleaned,
                        normalized_name=cleaned[:100],
                        priority="high",
                        confidence=0.9,
                        is_ambiguous=False,
                    )
                )
            elif PREFERRED_MARKERS.search(cleaned):
                preferred_qualifications.append(cleaned)
                detailed_requirements.append(
                    ParsedJobRequirement(
                        name=cleaned[:100],
                        category="qualification",
                        is_mandatory=False,
                        raw_text=cleaned,
                        normalized_name=cleaned[:100],
                        priority="medium",
                        confidence=0.9,
                        is_ambiguous=False,
                    )
                )

    # 7. Extract & Normalize Skills from Entire Description and Sections
    required_text = " ".join(section_lines["required"]) + " " + " ".join(required_qualifications)
    preferred_text = " ".join(section_lines["preferred"]) + " " + " ".join(preferred_qualifications)
    resp_text = " ".join(section_lines["responsibilities"]) + " " + " ".join(responsibilities)
    all_known_skills = extract_known_skills_from_text(clean_text)

    required_skills: list[dict[str, Any]] = []
    preferred_skills: list[dict[str, Any]] = []
    seen_skills: set[str] = set()

    for s in all_known_skills:
        skill_name = s["name"]
        raw_mention = s["raw_mention"]
        category = s["category"]

        # Classification precedence:
        # 1. In preferred section -> preferred
        # 2. In required section or responsibilities -> mandatory
        # 3. Check specific lines containing the mention for preferred vs mandatory markers
        mention_pat = re.compile(r"\b" + re.escape(raw_mention) + r"\b", re.IGNORECASE)

        if mention_pat.search(preferred_text) and not mention_pat.search(required_text):
            is_pref = True
        elif mention_pat.search(required_text) or mention_pat.search(resp_text):
            is_pref = False
        else:
            # Check lines where the mention occurs
            line_pref = False
            for line in lines:
                if mention_pat.search(line):
                    if PREFERRED_MARKERS.search(line):
                        line_pref = True
                        break
            is_pref = line_pref

        item = {
            "name": skill_name,
            "category": category,
            "is_mandatory": not is_pref,
            "raw_mention": raw_mention,
            "importance": "medium" if is_pref else "high",
        }

        if is_pref:
            preferred_skills.append(item)
        else:
            required_skills.append(item)
        seen_skills.add(skill_name.lower())

        detailed_requirements.append(
            ParsedJobRequirement(
                name=skill_name,
                category="technical_skill",
                is_mandatory=not is_pref,
                raw_text=raw_mention,
                normalized_name=skill_name,
                priority="medium" if is_pref else "high",
                confidence=1.0,
                is_ambiguous=False,
            )
        )

    # 8. Extract Soft Skills
    soft_skills_found: list[str] = []
    clean_lower = clean_text.lower()
    for soft in SOFT_SKILLS:
        if re.search(r"\b" + re.escape(soft.lower()) + r"\b", clean_lower):
            soft_skills_found.append(soft)

    # 9. Extract Summary (from overview or about section)
    summary_parts = section_lines["overview"][:3] or section_lines["about"][:3]
    summary = " ".join(summary_parts) if summary_parts else None

    # 10. Quality Warnings and Sanity Checks
    if not required_skills and not preferred_skills:
        warnings.append("No technical skills were explicitly identified in this job description.")

    if min_exp is None:
        warnings.append("No specific years of experience requirement identified.")
    elif seniority and seniority.lower() in ("junior", "entry-level", "intern") and min_exp >= 5:
        warnings.append(
            f"Contradictory experience requirements: role listed as {seniority} but asks for {min_exp}+ years of experience."
        )

    # Check for duplicate requirements
    seen_req_text: set[str] = set()
    for req in detailed_requirements:
        norm_r = req.raw_text.strip().lower()
        if norm_r in seen_req_text and len(norm_r) > 10:
            warnings.append(f"Duplicate requirement detected: '{req.raw_text[:50]}...'")
        seen_req_text.add(norm_r)

    # Normalized clean text for indexing
    normalized_text = f"Title: {title}\n"
    if company:
        normalized_text += f"Company: {company}\n"
    if location:
        normalized_text += f"Location: {location}\n"
    if min_exp is not None:
        normalized_text += f"Experience: {min_exp} years minimum\n"
    if required_skills:
        normalized_text += f"Required Skills: {', '.join(s['name'] for s in required_skills)}\n"
    if preferred_skills:
        normalized_text += f"Preferred Skills: {', '.join(s['name'] for s in preferred_skills)}\n"

    return ParsedJobDescription(
        title=title,
        company=company,
        location=location,
        employment_type=employment_type,
        seniority_level=seniority,
        summary=summary,
        raw_text=raw_text,
        normalized_text=normalized_text,
        min_years_experience=min_exp,
        max_years_experience=max_exp,
        education_level=education_level,
        responsibilities=responsibilities,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        required_qualifications=required_qualifications,
        preferred_qualifications=preferred_qualifications,
        certifications=certifications,
        soft_skills=soft_skills_found,
        quality_warnings=warnings,
        detailed_requirements=detailed_requirements,
    )
