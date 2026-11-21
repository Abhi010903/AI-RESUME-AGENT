"""Deterministic parser for extracting structured candidate information from resume text."""

from dataclasses import dataclass, field
import logging
import re
from typing import Any

logger = logging.getLogger("app.profile_parser")

# Email regex
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

# Phone regex (international & domestic formats)
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}\b"
)

# Social / Profile links
LINKEDIN_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[A-Za-z0-9_\-\.]+", re.IGNORECASE
)
GITHUB_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?github\.com\/[A-Za-z0-9_\-\.]+", re.IGNORECASE
)
URL_REGEX = re.compile(r"https?:\/\/[^\s,]+", re.IGNORECASE)

# Date range pattern (e.g. "Jan 2020 - Present", "2018 - 2022", "06/2019 – 08/2021")
MONTHS_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

_MONTH_NAME = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
_DATE_PAT = rf"(?:(?:{_MONTH_NAME}\s+)?\b\d{{4}}(?:[-\/]\d{{1,2}})?\b|(?:\d{{1,2}}[-\/])?\b\d{{4}}\b|{_MONTH_NAME})"
DATE_RANGE_REGEX = re.compile(
    rf"(?P<start>{_DATE_PAT})\s*(?:-|–|—|to)\s*(?P<end>{_DATE_PAT}|present|current|now)",
    re.IGNORECASE,
)

# Section Header Keywords
SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(?:##\s*)?(?:summary|professional\s+summary|profile|about\s+me|objective|career\s+objective)\b",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:##\s*)?(?:work\s+experience|professional\s+experience|employment(?:\s+history)?|experience|career\s+history|work\s+history)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:##\s*)?(?:projects|technical\s+projects|key\s+projects|academic\s+projects|personal\s+projects)\b",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:##\s*)?(?:education|academic\s+background|qualifications|academic\s+history|degrees)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:##\s*)?(?:skills|technical\s+skills|core\s+competencies|technologies|expertise|skills\s+&\s+abilities)\b",
        re.IGNORECASE,
    ),
    "achievements": re.compile(
        r"^(?:##\s*)?(?:achievements(?:\s*&\s*certifications)?|awards(?:\s*&\s*honors)?|honors|extracurricular\s+activities)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:##\s*)?(?:certifications|certificates|licenses(?:\s*&\s*certifications)?|professional\s+certifications)\b",
        re.IGNORECASE,
    ),
}

# Common skills taxonomy and categorization
KNOWN_SKILLS_CATEGORIES = {
    "python": "Languages",
    "javascript": "Languages",
    "typescript": "Languages",
    "java": "Languages",
    "c++": "Languages",
    "c#": "Languages",
    "golang": "Languages",
    "go": "Languages",
    "rust": "Languages",
    "ruby": "Languages",
    "php": "Languages",
    "sql": "Languages",
    "html": "Frontend",
    "css": "Frontend",
    "react": "Frontend",
    "vue": "Frontend",
    "angular": "Frontend",
    "next.js": "Frontend",
    "tailwind": "Frontend",
    "fastapi": "Backend",
    "django": "Backend",
    "flask": "Backend",
    "express": "Backend",
    "node.js": "Backend",
    "spring": "Backend",
    "spring boot": "Backend",
    "postgresql": "Databases",
    "mysql": "Databases",
    "sqlite": "Databases",
    "mongodb": "Databases",
    "redis": "Databases",
    "docker": "DevOps & Cloud",
    "kubernetes": "DevOps & Cloud",
    "aws": "DevOps & Cloud",
    "azure": "DevOps & Cloud",
    "gcp": "DevOps & Cloud",
    "linux": "DevOps & Cloud",
    "git": "Tools",
    "jira": "Tools",
    "machine learning": "AI & Data",
    "deep learning": "AI & Data",
    "nlp": "AI & Data",
    "pytorch": "AI & Data",
    "tensorflow": "AI & Data",
}


@dataclass
class ParsedExperience:
    company: str
    job_title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = field(default_factory=list)
    raw_text: str | None = None
    confidence_score: float = 1.0


@dataclass
class ParsedEducation:
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    raw_text: str | None = None


@dataclass
class ParsedSkill:
    name: str
    category: str | None = None
    proficiency: str | None = None


@dataclass
class ParsedCertification:
    name: str
    issuing_organization: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    raw_text: str | None = None


@dataclass
class ParsedProject:
    name: str
    role_or_subtitle: str | None = None
    technologies: list[str] = field(default_factory=list)
    description: str | None = None
    bullets: list[str] = field(default_factory=list)
    raw_text: str | None = None
    source_document_id: str | None = None


@dataclass
class ParsedResume:
    source_document_id: str
    full_name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    experiences: list[ParsedExperience] = field(default_factory=list)
    projects: list[ParsedProject] = field(default_factory=list)
    education: list[ParsedEducation] = field(default_factory=list)
    skills: list[ParsedSkill] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    certifications: list[ParsedCertification] = field(default_factory=list)


def normalize_date_string(date_str: str | None, default_year: str | None = None) -> str | None:
    """Normalize extracted date string to YYYY-MM, YYYY, or Present."""
    if not date_str:
        return None
    cleaned = date_str.strip().lower()
    if cleaned in ("present", "current", "now", "ongoing"):
        return "Present"

    # Match Year: "2021"
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)
    year = year_match.group(1) if year_match else default_year

    # Match Month name
    month = None
    for name, num in MONTHS_MAP.items():
        if re.search(rf"\b{name}\b", cleaned):
            month = num
            break

    # Match numeric month (MM/YYYY or YYYY-MM)
    if not month and year_match:
        num_month = re.search(r"\b(0?[1-9]|1[0-2])[\/\-](?:19\d{2}|20\d{2})\b", cleaned)
        if num_month:
            val = num_month.group(1).zfill(2)
            month = val
        else:
            ym_month = re.search(r"\b(?:19\d{2}|20\d{2})[\/\-](0?[1-9]|1[0-2])\b", cleaned)
            if ym_month:
                month = ym_month.group(1).zfill(2)

    if year and month:
        return f"{year}-{month}"
    if year:
        return year
    return cleaned


def parse_contact_info(text: str) -> dict[str, str | None]:
    """Extract candidate contact details from header lines."""
    email_match = EMAIL_REGEX.search(text)
    email = email_match.group(0) if email_match else None

    phone_match = None
    for m in PHONE_REGEX.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 7 <= len(digits) <= 15:
            phone_match = m.group(0).strip()
            break

    linkedin_match = LINKEDIN_REGEX.search(text)
    linkedin_url = linkedin_match.group(0) if linkedin_match else None

    github_match = GITHUB_REGEX.search(text)
    github_url = github_match.group(0) if github_match else None

    # Detect candidate name (typically the first non-empty line before contact info)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_name = "Candidate"
    for line in lines[:5]:
        clean_line = re.sub(r"^##\s*", "", line).strip()
        # Skip lines that are URLs, emails, or phone numbers
        if (
            not EMAIL_REGEX.search(clean_line)
            and not PHONE_REGEX.search(clean_line)
            and not LINKEDIN_REGEX.search(clean_line)
            and not URL_REGEX.search(clean_line)
            and len(clean_line.split()) <= 5
            and re.match(r"^[A-Za-z\s\.\,\'-]+$", clean_line)
        ):
            full_name = clean_line
            break

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone_match,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
    }


def split_into_sections(text: str) -> dict[str, list[str]]:
    """Partition extracted document text into logical resume sections."""
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "experience": [],
        "projects": [],
        "education": [],
        "skills": [],
        "achievements": [],
        "certifications": [],
    }

    current_section = "header"
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue

        # Check if line matches a known section header
        matched_section = None
        for sec_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(trimmed):
                matched_section = sec_name
                break

        if matched_section:
            current_section = matched_section
            m_inline = re.match(r"^[^:]+:\s*(.+)$", trimmed)
            if m_inline and m_inline.group(1).strip():
                sections[current_section].append(m_inline.group(1).strip())
        else:
            sections[current_section].append(trimmed)

    return sections


def parse_experience_section(lines: list[str]) -> list[ParsedExperience]:
    """Parse work experience lines into structured employment records."""
    experiences: list[ParsedExperience] = []
    current_entry: dict[str, Any] | None = None
    description_lines: list[str] = []

    def flush_entry() -> None:
        nonlocal current_entry, description_lines
        if current_entry:
            desc = "\n".join(description_lines).strip()
            # Extract skills mentioned in description
            found_skills = []
            for skill_name in KNOWN_SKILLS_CATEGORIES:
                if re.search(rf"\b{re.escape(skill_name)}\b", desc, re.IGNORECASE):
                    found_skills.append(skill_name.title())

            experiences.append(
                ParsedExperience(
                    company=current_entry["company"],
                    job_title=current_entry["job_title"],
                    location=current_entry.get("location"),
                    start_date=current_entry.get("start_date"),
                    end_date=current_entry.get("end_date"),
                    is_current=current_entry.get("is_current", False),
                    description=desc if desc else None,
                    skills_used=found_skills,
                    raw_text=f"{current_entry['raw_header']}\n{desc}".strip(),
                )
            )
            current_entry = None
            description_lines = []

    for line in lines:
        date_match = DATE_RANGE_REGEX.search(line)

        # Check if this line provides the dates for the current entry (e.g. date on line following title)
        if current_entry and current_entry.get("start_date") is None and date_match:
            non_date = DATE_RANGE_REGEX.sub("", line).strip(" |-–,")
            if len(non_date) < 20 and not any(sep in non_date for sep in [" at ", " @ "]):
                current_entry["start_date"] = normalize_date_string(date_match.group("start"))
                end_raw = date_match.group("end")
                current_entry["end_date"] = normalize_date_string(end_raw)
                current_entry["is_current"] = current_entry["end_date"] == "Present"
                continue

        # Identify title/company line: e.g. "Software Engineer at Google | 2020 - 2022" or "Google - Software Engineer"
        # Must not be a bullet point item
        is_bullet_line = line.strip().startswith(("•", "-", "*", "·"))
        if not is_bullet_line and (date_match or (any(sep in line for sep in [" at ", " - ", " | ", " – "]) and len(line) < 120)):
            start_date = None
            end_date = None
            is_current = False

            header_text = line
            if date_match:
                end_raw = date_match.group("end")
                end_date = normalize_date_string(end_raw)
                is_current = end_date == "Present"
                end_year = end_date[:4] if end_date and re.match(r"^\d{4}", end_date) else None
                start_date = normalize_date_string(date_match.group("start"), default_year=end_year)
                # Remove dates from header to extract title & company
                header_text = DATE_RANGE_REGEX.sub("", line).strip(" |-–,")

            parts = [
                p.strip()
                for p in re.split(r"\s*(?:\bat\b|\@|\||–|—|\s+-\s+)\s*", header_text)
                if p.strip()
            ]

            if len(parts) >= 2:
                flush_entry()
                p0, p1 = parts[0], parts[1]
                # Check whether company or title is first
                title_keywords = {
                    "engineer", "developer", "intern", "lead", "manager", "architect",
                    "scientist", "analyst", "consultant", "specialist", "administrator",
                    "director", "designer", "officer", "programmer", "trainee", "associate",
                    "fellow", "assistant", "head", "instructor", "researcher",
                }
                p0_lower = set(re.findall(r"[a-z]+", p0.lower()))
                p1_lower = set(re.findall(r"[a-z]+", p1.lower()))
                p0_has_title = bool(p0_lower & title_keywords)
                p1_has_title = bool(p1_lower & title_keywords)

                if p1_has_title and not p0_has_title:
                    # Company - Job Title (e.g. Google - Software Engineer)
                    job_title = p1
                    company = p0
                else:
                    # Default: Job Title - Company (or Job Title at Company)
                    job_title = p0
                    company = p1

                location = parts[2] if len(parts) > 2 else None
                current_entry = {
                    "company": company,
                    "job_title": job_title,
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_current": is_current,
                    "raw_header": line,
                }
                continue
            elif date_match and len(parts) == 1:
                flush_entry()
                current_entry = {
                    "company": parts[0],
                    "job_title": "Professional",
                    "location": None,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_current": is_current,
                    "raw_header": line,
                }
                continue

        if current_entry:
            description_lines.append(line)

    flush_entry()
    return experiences


def parse_education_section(lines: list[str]) -> list[ParsedEducation]:
    """Parse education lines into structured degree records."""
    educations: list[ParsedEducation] = []
    degree_keywords = [
        "bachelor", "master", "phd", "doctor", "b.s", "b.a", "b.tech", "b.e",
        "m.s", "m.a", "m.tech", "mba", "associate", "diploma", "degree"
    ]

    for line in lines:
        lower = line.lower()
        if any(dk in lower for dk in degree_keywords) or any(
            inst in lower for inst in ["university", "college", "institute", "school"]
        ):
            date_match = DATE_RANGE_REGEX.search(line)
            start_date = None
            end_date = None
            line_no_date = line
            if date_match:
                start_date = normalize_date_string(date_match.group("start"))
                end_date = normalize_date_string(date_match.group("end"))
                line_no_date = DATE_RANGE_REGEX.sub("", line).strip(" |-–,")

            parts = [p.strip() for p in re.split(r"\s*(?:from|\-|\||–|—)\s*", line_no_date) if p.strip()]
            if not parts:
                continue

            degree = parts[0]
            institution = "Institution"
            field_of_study = None
            grade = None

            # Check if degree part contains both degree and field of study e.g. "B. Tech, Computer Science & Engineering (AI)"
            if "," in degree:
                deg_split = [x.strip() for x in degree.split(",", 1)]
                degree = deg_split[0]
                if not field_of_study:
                    field_of_study = deg_split[1]

            # Classify remaining parts
            for p in parts[1:]:
                p_low = p.lower()
                cgpa_match = re.search(r"(?:cgpa|gpa|grade|score)[\s:]*([\d.]+(?:\s*/\s*[\d.]+)?%?)", p, re.IGNORECASE)
                if cgpa_match or any(kw in p_low for kw in ["cgpa", "gpa", "grade"]):
                    grade = p
                elif any(kw in p_low for kw in ["university", "college", "institute", "school", "academy"]):
                    institution = p
                elif any(kw in p_low for kw in ["computer", "engineering", "science", "arts", "commerce", "technology", "ai"]):
                    field_of_study = p
                elif field_of_study is None:
                    field_of_study = p
                else:
                    institution = p

            # If first part looks like an institution name, swap
            if any(inst in degree.lower() for inst in ["university", "college", "institute"]):
                institution, degree = degree, institution

            educations.append(
                ParsedEducation(
                    institution=institution,
                    degree=degree,
                    field_of_study=field_of_study,
                    start_date=start_date,
                    end_date=end_date,
                    grade=grade,
                    raw_text=line,
                )
            )

    return educations


def parse_skills_section(lines: list[str]) -> list[ParsedSkill]:
    """Parse technical and professional skills from skills section lines, stripping taxonomy category labels."""
    skills_map: dict[str, ParsedSkill] = {}

    for line in lines:
        clean = re.sub(r"^[-•*]\s*", "", line).strip()
        if not clean:
            continue

        line_category = None
        # Check for category prefix e.g. "Languages: Python, Java" or "Backend & Tools: FastAPI"
        if ":" in clean:
            prefix, rest = clean.split(":", 1)
            # If prefix looks like a category name (< 40 chars, no commas)
            if len(prefix.strip()) < 40 and "," not in prefix:
                line_category = prefix.strip()
                clean = rest.strip()

        tokens = re.split(r"[,|;•\n\t]+", clean)
        for token in tokens:
            name = token.strip()
            # If token still contains a colon (e.g. nested prefix), strip it
            if ":" in name:
                name = name.split(":", 1)[-1].strip()

            if not name or len(name) > 50:
                continue

            # Strip any leading bullets or quotes
            name = re.sub(r"^[-•*\"'\s]+|[-•*\"'\s]+$", "", name)
            if not name or len(name) < 2:
                continue

            lower_name = name.lower()
            category = KNOWN_SKILLS_CATEGORIES.get(lower_name, line_category or "General Skills")
            canonical_name = name.title() if lower_name in KNOWN_SKILLS_CATEGORIES else name

            if lower_name not in skills_map:
                skills_map[lower_name] = ParsedSkill(
                    name=canonical_name,
                    category=category,
                )

    return list(skills_map.values())


def parse_certifications_section(lines: list[str]) -> list[ParsedCertification]:
    """Parse certifications from certification lines."""
    certs: list[ParsedCertification] = []
    for line in lines:
        clean = re.sub(r"^[-•*]\s*", "", line).strip()
        if not clean or len(clean) < 3:
            continue

        date_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean)
        issue_date = date_match.group(0) if date_match else None
        clean_name = re.sub(r"\b(?:19\d{2}|20\d{2})\b", "", clean).strip(" |-–,()")

        parts = [p.strip() for p in re.split(r"\s*(?:\bby\b|\bfrom\b|\-|\|)\s*", clean_name) if p.strip()]
        cert_name = parts[0] if parts else clean_name
        issuer = parts[1] if len(parts) > 1 else None

        certs.append(
            ParsedCertification(
                name=cert_name,
                issuing_organization=issuer,
                issue_date=issue_date,
                raw_text=line,
            )
        )

    return certs


def parse_project_section(lines: list[str], document_id: str) -> list[ParsedProject]:
    """Parse projects section lines into structured project records with attached technologies and preserved bullet continuity."""
    projects: list[ParsedProject] = []
    current_proj: dict[str, Any] | None = None
    bullets: list[str] = []

    def flush_proj() -> None:
        nonlocal current_proj, bullets
        if current_proj:
            desc = "\n".join(bullets).strip()
            projects.append(
                ParsedProject(
                    name=current_proj["name"],
                    role_or_subtitle=current_proj.get("subtitle"),
                    technologies=current_proj.get("technologies", []),
                    description=desc if desc else None,
                    bullets=list(bullets),
                    raw_text=f"{current_proj.get('raw_header', '')}\n{desc}".strip(),
                    source_document_id=document_id,
                )
            )
            current_proj = None
            bullets = []

    def _is_header(clean: str) -> tuple[bool, str, str | None]:
        if clean.startswith(("•", "-", "*", "·")):
            return False, "", None

        # Check for dash / pipe separator e.g. "Breath.exe — ML Classification Research"
        has_sep = any(sep in clean for sep in [" — ", " – ", " - ", " | "])
        if has_sep:
            parts = [p.strip() for p in re.split(r"\s*(?:—|–|\||\s+-\s+)\s*", clean) if p.strip()]
            if parts:
                return True, parts[0], parts[1] if len(parts) > 1 else None

        # Check standalone title: must be short, capitalized, not starting with action/conjunction words, not ending in punctuation
        words = clean.split()
        if len(words) <= 5 and len(clean) < 45 and clean[0].isupper():
            if not clean.endswith((".", ",", ";", ":")):
                lower_first = words[0].lower()
                verb_rejects = {
                    "worked", "built", "developed", "integrated", "exposed", "evaluation",
                    "cover", "including", "using", "for", "and", "with", "the", "an", "a",
                    "responsible", "led", "created", "designed", "implemented", "achieved",
                }
                if lower_first not in verb_rejects:
                    if current_proj is None or len(bullets) > 0:
                        return True, clean, None

        return False, "", None

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        is_bullet = clean.startswith(("•", "-", "*", "·"))
        lower_clean = clean.lower()
        is_tech_line = (
            lower_clean.startswith(("technologies:", "tech stack:", "tools:", "stack:", "built with:"))
            or ("," in clean and any(kw in clean for kw in ["Python", "FastAPI", "React", "Docker", "SQL", "Pandas", "PyTorch", "C#", "Java", "AWS", "Azure", "Git"]))
        )

        is_hdr, name, subtitle = _is_header(clean)
        if is_hdr and not is_tech_line:
            flush_proj()
            current_proj = {
                "name": name,
                "subtitle": subtitle,
                "technologies": [],
                "raw_header": clean,
            }
            continue

        # Detect technologies line (typically immediately follows project title)
        if current_proj and not current_proj["technologies"] and not is_bullet:
            cleaned_tech_line = re.sub(r"^(?:technologies|tech stack|tools|stack|built with)\s*:\s*", "", clean, flags=re.IGNORECASE)
            tech_tokens = [t.strip() for t in cleaned_tech_line.split(",") if t.strip()]
            if len(tech_tokens) >= 2 or any(
                kw in clean for kw in ["Python", "FastAPI", "React", "Docker", "SQL", "Pandas", "PyTorch", "C#", "Java", "AWS", "Azure", "Git"]
            ):
                current_proj["technologies"] = tech_tokens
                continue

        # Bullet point or wrapped bullet continuation line
        if current_proj:
            if is_bullet:
                bullet_text = re.sub(r"^[\s•\-\*·]+\s*", "", clean).strip()
                if bullet_text:
                    bullets.append(bullet_text)
            else:
                # Wrapped continuation of previous bullet
                if bullets:
                    bullets[-1] = f"{bullets[-1]} {clean}".strip()
                else:
                    bullets.append(clean)

    flush_proj()
    return projects


def parse_achievements_section(lines: list[str]) -> list[str]:
    """Parse achievements and awards into clean bullet strings."""
    achievements: list[str] = []
    for line in lines:
        clean = re.sub(r"^[\s•\-\*·]+\s*", "", line).strip()
        if clean and len(clean) > 5:
            achievements.append(clean)
    return achievements


def parse_resume_text(text: str, document_id: str) -> ParsedResume:
    """Master dispatcher: extract structured candidate resume from plain text."""
    sections = split_into_sections(text)

    # 1. Contact & Header
    header_text = "\n".join(sections["header"] + sections.get("summary", []))
    contact = parse_contact_info(header_text)

    # 2. Summary
    summary_text = "\n".join(sections.get("summary", [])).strip()

    # 3. Work Experience
    experiences = parse_experience_section(sections.get("experience", []))

    # 4. Projects
    projects = parse_project_section(sections.get("projects", []), document_id)

    # 5. Education
    education = parse_education_section(sections.get("education", []))

    # 6. Skills
    skills = parse_skills_section(sections.get("skills", []))

    # 7. Achievements
    achievements = parse_achievements_section(sections.get("achievements", []))

    # 8. Certifications
    certifications = parse_certifications_section(sections.get("certifications", []))

    return ParsedResume(
        source_document_id=document_id,
        full_name=contact["full_name"] or "Candidate",
        email=contact["email"],
        phone=contact["phone"],
        linkedin_url=contact["linkedin_url"],
        github_url=contact["github_url"],
        summary=summary_text if summary_text else None,
        experiences=experiences,
        projects=projects,
        education=education,
        skills=skills,
        achievements=achievements,
        certifications=certifications,
    )
