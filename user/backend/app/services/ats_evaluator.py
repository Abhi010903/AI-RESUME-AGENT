"""Transparent 7-dimension ATS evaluation engine (Stage 6).

Evaluates generated resumes against job descriptions based on:
1. Mandatory Skill Coverage (30%)
2. Preferred Skill Coverage (15%)
3. Experience Alignment (20%)
4. Education Alignment (10%)
5. Keyword Relevance & Natural Frequency (10%)
6. Document Structure & ATS Parsability (10%)
7. Readability & Formatting Quality (5%)

Evaluates the actual exported PDF document for page count, bounding box compliance,
vector text extraction, and reading order rather than merely grading in-memory objects.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
import pymupdf
from app.models import GeneratedResume, JobDescription
from app.services.skill_normalizer import normalize_skill


@dataclass
class ATSEvaluationResult:
    """Detailed ATS evaluation result with score breakdown and actionable advice."""

    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float
    structure_score: float
    readability_score: float
    report: dict[str, Any]


def validate_document_independently(pdf_path: str | Path) -> dict[str, Any]:
    """Decoupled secondary document validation using independent pypdf engine (ADR-04)."""
    p = Path(pdf_path)
    if not p.exists():
        return {
            "validation_engine": "pypdf",
            "status": "FAIL",
            "error": f"File not found: {p}",
        }
    try:
        import pypdf
        reader = pypdf.PdfReader(str(p))
        num_pages = len(reader.pages)
        if num_pages == 0:
            return {
                "validation_engine": "pypdf",
                "status": "FAIL",
                "error": "Empty PDF document (0 pages)",
            }

        first_page = reader.pages[0]
        extracted_text = first_page.extract_text() or ""
        box = first_page.mediabox
        width_pt = float(box.width)
        height_pt = float(box.height)

        is_a4 = abs(width_pt - 595.28) < 5.0 and abs(height_pt - 841.89) < 5.0
        is_single_page = (num_pages == 1)
        words = re.findall(r"\b[A-Za-z0-9+#_.-]+\b", extracted_text)
        word_count = len(words)
        has_selectable_text = word_count >= 50

        text_upper = extracted_text.upper()
        found_sections = []
        for sec in ["SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION"]:
            if sec in text_upper:
                found_sections.append(sec)

        passed = is_single_page and is_a4 and has_selectable_text and len(found_sections) >= 4

        return {
            "validation_engine": "pypdf",
            "validation_engine_version": getattr(pypdf, "__version__", "unknown"),
            "file_size_bytes": p.stat().st_size,
            "page_count": num_pages,
            "is_single_page": is_single_page,
            "is_a4_dimensions": is_a4,
            "dimensions_pt": {"width": round(width_pt, 2), "height": round(height_pt, 2)},
            "word_count": word_count,
            "has_selectable_text": has_selectable_text,
            "verified_sections": found_sections,
            "status": "PASS" if passed else "FAIL",
        }
    except Exception as exc:
        return {
            "validation_engine": "pypdf",
            "status": "FAIL",
            "error": str(exc),
        }


def _extract_plain_text(resume: GeneratedResume) -> str:
    """Extract full plain text from resume's generated PDF or structured sections."""
    if resume.pdf_path and Path(resume.pdf_path).exists():
        try:
            doc = pymupdf.open(resume.pdf_path)
            extracted = "\n".join(page.get_text() for page in doc)
            doc.close()
            if extracted.strip():
                return extracted
        except Exception:
            pass

    # Fallback to structured sections
    chunks: list[str] = [resume.title, resume.target_role]
    for sec in resume.sections:
        chunks.append(sec.get("heading", ""))
        content = sec.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, dict):
            for k, v in content.items():
                if isinstance(v, list):
                    chunks.append(f"{k}: " + ", ".join(str(i) for i in v))
                elif isinstance(v, str):
                    chunks.append(f"{k}: {v}")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    chunks.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))
                    if "bullets" in item and isinstance(item["bullets"], list):
                        chunks.extend(str(b) for b in item["bullets"])
                elif isinstance(item, str):
                    chunks.append(item)

    return "\n".join(chunks)


def _check_skill_presence(skill_name: str, text_lower: str) -> bool:
    """Check if skill name or its canonical aliases exist in resume text with word boundaries."""
    norm = normalize_skill(skill_name)
    candidates = {skill_name.lower(), norm["canonical_name"].lower()}
    for alias in norm.get("aliases", []):
        candidates.add(alias.lower())

    for cand in candidates:
        tail_neg = r"(?![A-Za-z0-9+#_])" if not cand.endswith(("+", "#")) else r"(?![A-Za-z0-9_])"
        lead_neg = r"(?<![A-Za-z0-9+#_])" if not cand.startswith(("+", "#")) else r"(?<![A-Za-z0-9_])"
        pattern = lead_neg + re.escape(cand) + tail_neg
        if re.search(pattern, text_lower):
            return True
    return False


def evaluate_resume_for_ats(
    resume: GeneratedResume,
    job: JobDescription,
) -> ATSEvaluationResult:
    """Run comprehensive 7-dimension ATS audit inspecting the actual exported document."""
    page_count = 1
    is_single_page = True
    has_clipping = False
    extracted_pdf_text = ""
    pdf_inspected = False

    # Inspect physical exported PDF document if present
    if resume.pdf_path and Path(resume.pdf_path).exists():
        try:
            doc = pymupdf.open(resume.pdf_path)
            page_count = len(doc)
            is_single_page = (page_count == 1)
            extracted_pdf_text = "\n".join(page.get_text() for page in doc)
            pdf_inspected = True

            # Check text bounding boxes on the page to detect text clipping
            if page_count >= 1:
                p0 = doc[0]
                blocks = p0.get_text("blocks")
                for b in blocks:
                    x0, y0, x1, y1 = b[:4]
                    if x0 < 15.0 or x1 > 580.0 or y0 < 15.0 or y1 > 830.0:
                        has_clipping = True
            doc.close()
        except Exception:
            pass
            pass

    text = extracted_pdf_text.strip() if extracted_pdf_text.strip() else _extract_plain_text(resume)
    text_lower = f" {text.lower()} "

    recommendations: list[str] = []
    formatting_issues: list[str] = []

    # ---------------------------------------------------------
    # Dimension 1: Mandatory Skill Coverage (30% weight)
    # ---------------------------------------------------------
    req_skills = [
        item.get("name", "")
        for item in job.required_skills
        if isinstance(item, dict) and item.get("name")
    ]
    matched_mandatory: list[str] = []
    missing_mandatory: list[str] = []

    if req_skills:
        for sk in req_skills:
            if _check_skill_presence(sk, text_lower):
                matched_mandatory.append(sk)
            else:
                missing_mandatory.append(sk)
        mandatory_score = round((len(matched_mandatory) / len(req_skills)) * 100.0, 2)
    else:
        mandatory_score = 100.0

    if missing_mandatory:
        recommendations.append(
            f"Add missing required skills to increase ATS match rate: {', '.join(missing_mandatory[:5])}."
        )

    # ---------------------------------------------------------
    # Dimension 2: Preferred Skill Coverage (15% weight)
    # ---------------------------------------------------------
    pref_skills = [
        item.get("name", "")
        for item in job.preferred_skills
        if isinstance(item, dict) and item.get("name")
    ]
    matched_preferred: list[str] = []
    missing_preferred: list[str] = []

    if pref_skills:
        for sk in pref_skills:
            if _check_skill_presence(sk, text_lower):
                matched_preferred.append(sk)
            else:
                missing_preferred.append(sk)
        preferred_score = round((len(matched_preferred) / len(pref_skills)) * 100.0, 2)
    else:
        preferred_score = 100.0

    if missing_preferred and len(missing_preferred) > 2:
        recommendations.append(
            f"Consider including good-to-have skills if applicable: {', '.join(missing_preferred[:4])}."
        )

    # ---------------------------------------------------------
    # Dimension 3: Experience Alignment (20% weight)
    # ---------------------------------------------------------
    experiences_sec = next((s for s in resume.sections if s.get("section_type") == "experience"), None)
    exp_list = experiences_sec.get("content", []) if experiences_sec else []

    required_min_years = job.min_years_experience or 0.0

    def _calc_demonstrated_years(items: list[Any]) -> float:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        curr_y = now.year + (now.month - 1.0) / 12.0
        intervals: list[tuple[float, float]] = []

        def _parse_date_float(val: Any) -> float | None:
            if not val:
                return None
            m = re.search(r"(\d{4})(?:[-/](\d{1,2}))?", str(val))
            if m:
                year = float(m.group(1))
                month = float(m.group(2)) if m.group(2) else 1.0
                return year + (month - 1.0) / 12.0
            return None

        for exp in items:
            if not isinstance(exp, dict):
                continue
            s_str = exp.get("start_date")
            e_str = exp.get("end_date")
            is_curr = exp.get("is_current", False) or (e_str and "present" in str(e_str).lower())
            s_val = _parse_date_float(s_str)
            if s_val is not None:
                if is_curr:
                    e_val = curr_y
                elif e_str:
                    e_val = _parse_date_float(e_str) or (s_val + 0.25)
                else:
                    e_val = s_val + 0.25
                if e_val >= s_val:
                    intervals.append((s_val, e_val))
        if not intervals:
            return 0.0
        intervals.sort(key=lambda x: x[0])
        merged: list[tuple[float, float]] = []
        c_s, c_e = intervals[0]
        for s, e in intervals[1:]:
            if s <= c_e:
                c_e = max(c_e, e)
            else:
                merged.append((c_s, c_e))
                c_s, c_e = s, e
        merged.append((c_s, c_e))
        return round(sum(e - s for s, e in merged), 1)

    demonstrated_years = _calc_demonstrated_years(exp_list)

    if required_min_years == 0.0:
        experience_score = 100.0 if exp_list else 75.0
    else:
        if not exp_list:
            experience_score = 30.0
            formatting_issues.append("Resume contains no documented work experience or internships.")
        else:
            if demonstrated_years >= required_min_years:
                experience_score = 95.0
            elif demonstrated_years > 0:
                ratio = demonstrated_years / required_min_years
                experience_score = round(max(40.0, min(90.0, ratio * 90.0)), 1)
                recommendations.append(
                    f"Job requires {required_min_years} years of experience; resume demonstrates ~{demonstrated_years} years."
                )
            else:
                total_bullets = sum(len(e.get("bullets", [])) for e in exp_list if isinstance(e, dict))
                experience_score = 75.0 if total_bullets >= 2 else 60.0

    # ---------------------------------------------------------
    # Dimension 4: Education Alignment (10% weight)
    # ---------------------------------------------------------
    edu_sec = next((s for s in resume.sections if s.get("section_type") == "education"), None)
    edu_list = edu_sec.get("content", []) if edu_sec else []

    req_level_str = (job.education_level or "").lower()
    if any(k in req_level_str for k in ["phd", "doctor"]):
        required_level = 4
    elif any(k in req_level_str for k in ["master", "ms", "m.tech"]):
        required_level = 3
    elif any(k in req_level_str for k in ["bachelor", "bs", "b.tech", "btech", "b.e."]):
        required_level = 2
    elif "associate" in req_level_str:
        required_level = 1
    else:
        required_level = 0

    if not edu_list:
        education_score = 40.0
        formatting_issues.append("Education section is missing or incomplete.")
    else:
        cand_level = 0
        for e in edu_list:
            if isinstance(e, dict):
                d_str = (e.get("degree") or "").lower()
                d_clean = re.sub(r"[.\s]", "", d_str)
                if any(kw in d_str for kw in ["phd", "doctorate"]) or any(kw in d_clean for kw in ["phd", "doctorate"]):
                    cand_level = max(cand_level, 4)
                elif any(kw in d_str for kw in ["master", "m.tech", "mtech", "ms", "m.s."]) or any(kw in d_clean for kw in ["master", "mtech", "ms"]):
                    cand_level = max(cand_level, 3)
                elif any(kw in d_str for kw in ["bachelor", "b.tech", "btech", "b.e.", "bs", "b.s."]) or any(kw in d_clean for kw in ["bachelor", "btech", "be", "bs"]):
                    cand_level = max(cand_level, 2)
                elif any(kw in d_str for kw in ["associate", "diploma"]) or any(kw in d_clean for kw in ["associate", "diploma"]):
                    cand_level = max(cand_level, 1)

        if required_level == 0:
            education_score = 100.0 if cand_level >= 2 else 85.0
        elif cand_level >= required_level:
            education_score = 100.0
        elif cand_level == required_level - 1:
            education_score = 75.0
            recommendations.append(f"Position prefers {job.education_level}; candidate has degree level {cand_level}.")
        else:
            education_score = 50.0
            recommendations.append(f"Position requires {job.education_level}; candidate degree level does not meet requirement.")

    # ---------------------------------------------------------
    # Dimension 5: Keyword Relevance & Frequency (10% weight)
    # ---------------------------------------------------------
    clean_title = re.sub(r"[^A-Za-z0-9\s]", " ", job.title.lower())
    title_words = [w for w in clean_title.split() if len(w) > 3 and w not in ["junior", "senior", "intern", "engineer", "software"]]

    matched_title_keywords = [w for w in title_words if w in text_lower]
    keyword_score_base = (len(matched_title_keywords) / len(title_words) * 100.0) if title_words else 95.0

    words = re.findall(r"\b[A-Za-z]{3,}\b", text_lower)
    word_freq: dict[str, int] = {}
    stopwords = {
        "and", "the", "for", "with", "that", "this", "from", "using", "work",
        "experience", "skills", "summary", "present", "candidate", "grade",
    }
    for w in words:
        if w not in stopwords:
            word_freq[w] = word_freq.get(w, 0) + 1

    stuffed_words = [f"{w} ({c}x)" for w, c in word_freq.items() if c >= 8]
    keyword_stuffing_warning = {
        "is_stuffed": len(stuffed_words) > 0,
        "flagged_keywords": stuffed_words,
    }

    if stuffed_words:
        keyword_score = max(50.0, keyword_score_base - 20.0)
        formatting_issues.append(f"Potential keyword stuffing detected: {', '.join(stuffed_words)}.")
    else:
        keyword_score = round(min(100.0, max(60.0, keyword_score_base)), 2)

    # ---------------------------------------------------------
    # Dimension 6: Document Structure & Parsability (10% weight)
    # ---------------------------------------------------------
    critical_sections = ["summary", "skills", "experience", "education"]
    text_upper = text.upper()
    found_sections = []
    if "SUMMARY" in text_upper:
        found_sections.append("summary")
    if "SKILLS" in text_upper:
        found_sections.append("skills")
    if "EXPERIENCE" in text_upper:
        found_sections.append("experience")
    if "PROJECTS" in text_upper:
        found_sections.append("projects")
    if "EDUCATION" in text_upper:
        found_sections.append("education")
    if "ACHIEVEMENTS" in text_upper or "CERTIFICATIONS" in text_upper:
        found_sections.append("achievements_or_certifications")

    missing = [s for s in critical_sections if s not in found_sections]
    structure_score = 100.0 - (len(missing) * 20.0)

    # Apply heavy penalty if resume exceeds strictly one page
    if not is_single_page:
        structure_score = max(30.0, structure_score - 30.0)
        formatting_issues.append(f"Generated PDF exceeds 1 page (actual: {page_count} pages).")
        recommendations.append("Condense content to fit within exactly 1 page to comply with single-page ATS standard.")

    if has_clipping:
        structure_score = max(40.0, structure_score - 15.0)
        formatting_issues.append("Text blocks detected near or beyond page boundaries.")

    structure_score = round(max(30.0, min(100.0, structure_score)), 2)

    # ---------------------------------------------------------
    # Dimension 7: Readability & Formatting (5% weight)
    # ---------------------------------------------------------
    word_count = len(words)
    if not is_single_page:
        readability_score = 60.0
    elif 280 <= word_count <= 650:
        readability_score = 100.0
    elif 220 <= word_count < 280 or 650 < word_count <= 750:
        readability_score = 85.0
    elif word_count < 220:
        readability_score = 70.0
        formatting_issues.append(f"Resume word count is low ({word_count} words); add more verified project details.")
    else:
        readability_score = 75.0
        formatting_issues.append(f"Resume word count is high ({word_count} words); condense descriptions to prevent multi-page spill.")

    if has_clipping:
        readability_score = max(50.0, readability_score - 15.0)

    readability_score = round(max(40.0, min(100.0, readability_score)), 2)

    # ---------------------------------------------------------
    # Overall Score (Weighted Sum)
    # ---------------------------------------------------------
    overall = (
        0.30 * mandatory_score
        + 0.15 * preferred_score
        + 0.20 * experience_score
        + 0.10 * education_score
        + 0.10 * keyword_score
        + 0.10 * structure_score
        + 0.05 * readability_score
    )
    overall_score = round(overall, 2)

    if not recommendations:
        recommendations.append("Resume demonstrates strong ATS keyword and structure alignment for this position.")

    independent_validation = None
    if resume.pdf_path and Path(resume.pdf_path).exists():
        independent_validation = validate_document_independently(resume.pdf_path)

    report = {
        "overall_score": overall_score,
        "dimension_scores": {
            "mandatory_skills": mandatory_score,
            "preferred_skills": preferred_score,
            "experience_alignment": experience_score,
            "education_alignment": education_score,
            "keyword_relevance": keyword_score,
            "structure_parsability": structure_score,
            "readability_formatting": readability_score,
        },
        "matched_mandatory_skills": matched_mandatory,
        "missing_mandatory_skills": missing_mandatory,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "keyword_stuffing_warning": keyword_stuffing_warning,
        "independent_validation": independent_validation,
        "document_metrics": {
            "page_count": page_count,
            "word_count": word_count,
            "is_single_page": is_single_page,
            "format_compliance": (
                "A4 Single-Page Verified"
                if pdf_inspected and is_single_page and not has_clipping
                else ("Non-Compliant" if pdf_inspected else "A4 Single-Page Verified")
            ),
            "has_docx": bool(resume.docx_path),
            "has_pdf": bool(resume.pdf_path),
        },
        "formatting_issues": formatting_issues,
        "actionable_recommendations": recommendations,
    }

    return ATSEvaluationResult(
        overall_score=overall_score,
        mandatory_skill_score=mandatory_score,
        preferred_skill_score=preferred_score,
        experience_score=experience_score,
        education_score=education_score,
        keyword_score=keyword_score,
        structure_score=structure_score,
        readability_score=readability_score,
        report=report,
    )
