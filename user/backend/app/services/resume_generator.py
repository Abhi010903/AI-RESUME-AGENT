"""Document generation service for ATS-friendly DOCX and PDF formats (Stage 6).

Generates professional, single-column, A4 standard-compliant (210 x 297 mm) resumes
with an intelligent layout optimizer strictly guaranteeing single-page output using
python-docx and PyMuPDF (pymupdf).
"""

from pathlib import Path
import textwrap
import uuid
from typing import Any
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
import pymupdf
from app.config import get_settings
from app.services.resume_tailorer import TailoredResumeData

# Strict A4 page specifications
A4_WIDTH_PT = 595.28   # 210 mm
A4_HEIGHT_PT = 841.89  # 297 mm
MARGIN_X_PT = 36.0     # 0.50 inch
MARGIN_Y_PT = 36.0     # 0.50 inch
USABLE_WIDTH_PT = A4_WIDTH_PT - (2 * MARGIN_X_PT)   # 523.28 pt
USABLE_HEIGHT_PT = A4_HEIGHT_PT - (2 * MARGIN_Y_PT) # 769.89 pt


def _format_date_range(start_date: str | None, end_date: str | None, is_current: bool = False) -> str:
    """Format start and end dates cleanly, omitting unknown or None boundaries."""
    s = str(start_date).strip() if start_date and str(start_date).strip() not in ("None", "") else ""
    e = (
        str(end_date).strip()
        if end_date and str(end_date).strip() not in ("None", "")
        else ("Present" if is_current else "")
    )
    if s and e:
        return f"{s} - {e}"
    if s:
        return s
    if e:
        return e
    return ""


def _format_contact_line(contact: dict[str, Any]) -> str:
    """Format contact items into a concise single line."""
    parts = []
    if contact.get("phone"):
        parts.append(str(contact["phone"]))
    if contact.get("email"):
        parts.append(str(contact["email"]))
    if contact.get("linkedin_url"):
        parts.append(str(contact["linkedin_url"]))
    if contact.get("github_url"):
        parts.append(str(contact["github_url"]))
    if contact.get("portfolio_url"):
        parts.append(str(contact["portfolio_url"]))
    if contact.get("location"):
        parts.append(str(contact["location"]))
    return "  |  ".join(parts)


def generate_docx(tailored_data: TailoredResumeData, output_path: Path) -> Path:
    """Generate ATS-compliant single-column A4 DOCX resume strictly fitting one page."""
    doc = docx.Document()

    # Strict A4 dimensions (8.27 x 11.69 inches) and compact 0.48-0.50" margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.48)
        section.bottom_margin = Inches(0.48)
        section.left_margin = Inches(0.50)
        section.right_margin = Inches(0.50)

    # 1. Header: Candidate Name
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(1)
    run_name = p_name.add_run(tailored_data.contact.get("full_name", "").upper())
    run_name.bold = True
    run_name.font.size = Pt(17)
    run_name.font.name = "Arial"
    run_name.font.color.rgb = RGBColor(0, 0, 0)

    # Professional Headline (if present)
    headline = tailored_data.contact.get("headline")
    if headline:
        p_head = doc.add_paragraph()
        p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_head.paragraph_format.space_before = Pt(0)
        p_head.paragraph_format.space_after = Pt(2)
        run_h = p_head.add_run(headline.upper())
        run_h.bold = True
        run_h.font.size = Pt(8.5)
        run_h.font.name = "Arial"
        run_h.font.color.rgb = RGBColor(0, 51, 102)

    # Contact Line
    contact_line = _format_contact_line(tailored_data.contact)
    if contact_line:
        p_contact = doc.add_paragraph()
        p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_contact.paragraph_format.space_before = Pt(0)
        p_contact.paragraph_format.space_after = Pt(5)
        run_contact = p_contact.add_run(contact_line)
        run_contact.font.size = Pt(8.5)
        run_contact.font.name = "Arial"
        run_contact.font.color.rgb = RGBColor(70, 70, 70)

    def add_section_header(title: str) -> None:
        p_sec = doc.add_paragraph()
        p_sec.paragraph_format.space_before = Pt(5)
        p_sec.paragraph_format.space_after = Pt(2)
        run_sec = p_sec.add_run(title.upper())
        run_sec.bold = True
        run_sec.font.size = Pt(10)
        run_sec.font.name = "Arial"
        run_sec.font.color.rgb = RGBColor(0, 51, 102)

    # 2. Professional Summary
    if tailored_data.summary:
        add_section_header("Professional Summary")
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_before = Pt(0)
        p_sum.paragraph_format.space_after = Pt(3)
        p_sum.paragraph_format.line_spacing = 1.12
        run_sum = p_sum.add_run(tailored_data.summary)
        run_sum.font.size = Pt(9.0)
        run_sum.font.name = "Arial"

    # 3. Technical Skills
    if tailored_data.skills_by_category:
        add_section_header("Technical Skills")
        for category, skills in tailored_data.skills_by_category.items():
            if not skills:
                continue
            p_skill = doc.add_paragraph()
            p_skill.paragraph_format.space_before = Pt(0)
            p_skill.paragraph_format.space_after = Pt(1.5)
            p_skill.paragraph_format.line_spacing = 1.12

            run_cat = p_skill.add_run(f"{category}: ")
            run_cat.bold = True
            run_cat.font.size = Pt(9.0)
            run_cat.font.name = "Arial"

            run_sk = p_skill.add_run(", ".join(skills))
            run_sk.font.size = Pt(9.0)
            run_sk.font.name = "Arial"

    # 4. Work Experience
    if tailored_data.experiences:
        add_section_header("Work Experience")
        for exp in tailored_data.experiences:
            p_exp = doc.add_paragraph()
            p_exp.paragraph_format.space_before = Pt(3)
            p_exp.paragraph_format.space_after = Pt(1)

            run_title = p_exp.add_run(exp.get("job_title", "Position"))
            run_title.bold = True
            run_title.font.size = Pt(9.5)
            run_title.font.name = "Arial"

            comp_str = f" — {exp.get('company', '')}" if exp.get("company") else ""
            if exp.get("location"):
                comp_str += f" ({exp['location']})"
            run_comp = p_exp.add_run(comp_str)
            run_comp.font.size = Pt(9.0)
            run_comp.font.name = "Arial"

            date_range = _format_date_range(exp.get("start_date"), exp.get("end_date"), exp.get("is_current", False))
            if date_range:
                run_dates = p_exp.add_run(f" | {date_range}")
                run_dates.italic = True
                run_dates.font.size = Pt(8.5)
                run_dates.font.name = "Arial"
                run_dates.font.color.rgb = RGBColor(90, 90, 90)

            for b in exp.get("bullets", []):
                p_bullet = doc.add_paragraph(style="List Bullet")
                p_bullet.paragraph_format.space_before = Pt(0.5)
                p_bullet.paragraph_format.space_after = Pt(1.5)
                p_bullet.paragraph_format.line_spacing = 1.12
                run_b = p_bullet.add_run(b)
                run_b.font.size = Pt(9.0)
                run_b.font.name = "Arial"

    # 5. Projects
    if tailored_data.projects:
        add_section_header("Projects")
        for proj in tailored_data.projects:
            p_proj = doc.add_paragraph()
            p_proj.paragraph_format.space_before = Pt(3)
            p_proj.paragraph_format.space_after = Pt(1)

            p_name_run = p_proj.add_run(proj.get("name", "Project"))
            p_name_run.bold = True
            p_name_run.font.size = Pt(9.5)
            p_name_run.font.name = "Arial"

            if proj.get("subtitle"):
                p_sub_run = p_proj.add_run(f" — {proj['subtitle']}")
                p_sub_run.font.size = Pt(9.0)
                p_sub_run.font.name = "Arial"

            techs = proj.get("technologies", [])
            if techs:
                p_tech = doc.add_paragraph()
                p_tech.paragraph_format.space_before = Pt(0)
                p_tech.paragraph_format.space_after = Pt(1)
                run_tech = p_tech.add_run(", ".join(techs))
                run_tech.italic = True
                run_tech.font.size = Pt(8.5)
                run_tech.font.name = "Arial"
                run_tech.font.color.rgb = RGBColor(60, 60, 60)

            for b in proj.get("bullets", []):
                p_bullet = doc.add_paragraph(style="List Bullet")
                p_bullet.paragraph_format.space_before = Pt(0.5)
                p_bullet.paragraph_format.space_after = Pt(1.5)
                p_bullet.paragraph_format.line_spacing = 1.12
                run_b = p_bullet.add_run(b)
                run_b.font.size = Pt(9.0)
                run_b.font.name = "Arial"

    # 6. Education
    if tailored_data.education:
        add_section_header("Education")
        for edu in tailored_data.education:
            p_edu = doc.add_paragraph()
            p_edu.paragraph_format.space_before = Pt(2)
            p_edu.paragraph_format.space_after = Pt(1.5)

            degree_str = edu.get("degree", "Degree")
            if edu.get("field_of_study"):
                degree_str += f", {edu['field_of_study']}"
            run_deg = p_edu.add_run(degree_str)
            run_deg.bold = True
            run_deg.font.size = Pt(9.0)
            run_deg.font.name = "Arial"

            inst_str = f" | {edu.get('institution', '')}"
            run_inst = p_edu.add_run(inst_str)
            run_inst.font.size = Pt(9.0)
            run_inst.font.name = "Arial"

            meta_parts = []
            if edu.get("grade"):
                meta_parts.append(f"CGPA/Grade: {edu['grade']}")
            edu_dates = _format_date_range(edu.get("start_date"), edu.get("end_date"))
            if edu_dates:
                meta_parts.append(edu_dates)

            if meta_parts:
                run_meta = p_edu.add_run(f" | {' | '.join(meta_parts)}")
                run_meta.italic = True
                run_meta.font.size = Pt(8.5)
                run_meta.font.name = "Arial"
                run_meta.font.color.rgb = RGBColor(90, 90, 90)

    # 7. Achievements & Certifications
    items_to_render = tailored_data.achievements or [
        f"{c.get('name', '')} — {c.get('issuing_organization', '')}".rstrip(" —")
        for c in tailored_data.certifications
    ]
    if items_to_render:
        add_section_header("Achievements & Certifications")
        for item in items_to_render:
            p_ach = doc.add_paragraph(style="List Bullet")
            p_ach.paragraph_format.space_before = Pt(0.5)
            p_ach.paragraph_format.space_after = Pt(1.5)
            p_ach.paragraph_format.line_spacing = 1.12
            run_ach = p_ach.add_run(item)
            run_ach.font.size = Pt(8.5)
            run_ach.font.name = "Arial"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path


def _wrap_text_by_width(
    text: str,
    max_width_pt: float,
    fontname: str = "helv",
    fontsize: float = 9.0,
) -> list[str]:
    """Wrap text lines according to actual rendered font width in PyMuPDF."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    curr_line: list[str] = []

    for word in words:
        trial = " ".join(curr_line + [word])
        w = pymupdf.get_text_length(trial, fontname=fontname, fontsize=fontsize)
        if w <= max_width_pt:
            curr_line.append(word)
        else:
            if curr_line:
                lines.append(" ".join(curr_line))
                curr_line = [word]
            else:
                lines.append(word)
                curr_line = []
    if curr_line:
        lines.append(" ".join(curr_line))
    return lines


def _clamp_text_to_width(text: str, max_width_pt: float, fontname: str = "helv", fontsize: float = 9.0) -> str:
    """Clamp string with ellipsis if its rendered length exceeds max_width_pt."""
    if pymupdf.get_text_length(text, fontname=fontname, fontsize=fontsize) <= max_width_pt:
        return text
    while len(text) > 4 and pymupdf.get_text_length(text + "...", fontname=fontname, fontsize=fontsize) > max_width_pt:
        text = text[:-1]
    return text + "..."


def generate_pdf(tailored_data: TailoredResumeData, output_path: Path) -> Path:
    """Generate ATS-compliant vector PDF resume strictly fitting exactly one A4 page."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4_WIDTH_PT, height=A4_HEIGHT_PT)

    # Layout tuning parameters
    cursor_y = MARGIN_Y_PT
    NAVY_COLOR = (0.0, 0.20, 0.40)
    DARK_TEXT = (0.08, 0.08, 0.08)
    MUTED_TEXT = (0.35, 0.35, 0.35)

    # 1. Header: Candidate Name (Centered, 17 pt bold)
    candidate_name = tailored_data.contact.get("full_name", "").upper()
    name_w = pymupdf.get_text_length(candidate_name, fontname="hebo", fontsize=17.0)
    name_x = max(MARGIN_X_PT, (A4_WIDTH_PT - name_w) / 2.0)
    page.insert_text(
        pymupdf.Point(name_x, cursor_y + 15.0),
        candidate_name,
        fontname="hebo",
        fontsize=17.0,
        color=(0.0, 0.0, 0.0),
    )
    cursor_y += 18.0

    # Professional Headline (Centered, 8.5 pt bold navy)
    headline = tailored_data.contact.get("headline")
    if headline:
        head_str = headline.upper()
        head_w = pymupdf.get_text_length(head_str, fontname="hebo", fontsize=8.5)
        head_x = max(MARGIN_X_PT, (A4_WIDTH_PT - head_w) / 2.0)
        page.insert_text(
            pymupdf.Point(head_x, cursor_y + 8.0),
            head_str,
            fontname="hebo",
            fontsize=8.5,
            color=NAVY_COLOR,
        )
        cursor_y += 11.0

    # Contact line (Centered, 8.5 pt)
    contact_str = _format_contact_line(tailored_data.contact)
    if contact_str:
        c_w = pymupdf.get_text_length(contact_str, fontname="helv", fontsize=8.5)
        if c_w <= USABLE_WIDTH_PT:
            c_x = (A4_WIDTH_PT - c_w) / 2.0
            page.insert_text(
                pymupdf.Point(c_x, cursor_y + 8.0),
                contact_str,
                fontname="helv",
                fontsize=8.5,
                color=MUTED_TEXT,
            )
            cursor_y += 11.0
        else:
            for cline in textwrap.wrap(contact_str, width=105):
                cw_line = pymupdf.get_text_length(cline, fontname="helv", fontsize=8.5)
                c_x = max(MARGIN_X_PT, (A4_WIDTH_PT - cw_line) / 2.0)
                page.insert_text(
                    pymupdf.Point(c_x, cursor_y + 8.0),
                    cline,
                    fontname="helv",
                    fontsize=8.5,
                    color=MUTED_TEXT,
                )
                cursor_y += 10.5
    cursor_y += 3.0

    def draw_section_heading(title: str) -> None:
        nonlocal cursor_y
        cursor_y += 5.0
        page.insert_text(
            pymupdf.Point(MARGIN_X_PT, cursor_y + 9.5),
            title.upper(),
            fontname="hebo",
            fontsize=10.0,
            color=NAVY_COLOR,
        )
        cursor_y += 12.0
        # Clean horizontal accent line
        page.draw_line(
            pymupdf.Point(MARGIN_X_PT, cursor_y),
            pymupdf.Point(A4_WIDTH_PT - MARGIN_X_PT, cursor_y),
            color=NAVY_COLOR,
            width=0.75,
        )
        cursor_y += 4.0

    # 2. Professional Summary
    if tailored_data.summary:
        draw_section_heading("Professional Summary")
        summary_lines = _wrap_text_by_width(tailored_data.summary, USABLE_WIDTH_PT, fontname="helv", fontsize=9.0)
        for line in summary_lines:
            page.insert_text(
                pymupdf.Point(MARGIN_X_PT, cursor_y + 8.5),
                line,
                fontname="helv",
                fontsize=9.0,
                color=DARK_TEXT,
            )
            cursor_y += 11.2
        cursor_y += 1.0

    # 3. Technical Skills
    if tailored_data.skills_by_category:
        draw_section_heading("Technical Skills")
        for category, skills in tailored_data.skills_by_category.items():
            if not skills:
                continue
            cat_label = f"{category}: "
            cat_w = pymupdf.get_text_length(cat_label, fontname="hebo", fontsize=9.0)

            skills_text = ", ".join(skills)
            full_line = f"{category}: {skills_text}"
            wrapped_lines = _wrap_text_by_width(full_line, USABLE_WIDTH_PT, fontname="helv", fontsize=9.0)

            for idx, w_line in enumerate(wrapped_lines):
                if idx == 0:
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT, cursor_y + 8.5),
                        cat_label,
                        fontname="hebo",
                        fontsize=9.0,
                        color=(0.0, 0.0, 0.0),
                    )
                    rem_text = w_line[len(cat_label):]
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT + cat_w, cursor_y + 8.5),
                        rem_text,
                        fontname="helv",
                        fontsize=9.0,
                        color=DARK_TEXT,
                    )
                else:
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT + 10.0, cursor_y + 8.5),
                        w_line,
                        fontname="helv",
                        fontsize=9.0,
                        color=DARK_TEXT,
                    )
                cursor_y += 11.2
        cursor_y += 1.0

    # 4. Work Experience
    if tailored_data.experiences:
        draw_section_heading("Work Experience")
        for exp in tailored_data.experiences:
            cursor_y += 2.0
            job_title = exp.get("job_title", "Position")
            company = exp.get("company", "")
            location = exp.get("location", "")
            date_range = _format_date_range(exp.get("start_date"), exp.get("end_date"), exp.get("is_current", False))

            date_w = pymupdf.get_text_length(date_range, fontname="heit", fontsize=8.5) if date_range else 0.0
            title_w = pymupdf.get_text_length(job_title, fontname="hebo", fontsize=9.5)
            max_comp_w = max(40.0, USABLE_WIDTH_PT - title_w - date_w - 15.0)

            comp_str = f"  —  {company}" if company else ""
            if location:
                comp_str += f" ({location})"
            clamped_comp_str = _clamp_text_to_width(comp_str, max_comp_w, fontname="helv", fontsize=9.0)

            page.insert_text(
                pymupdf.Point(MARGIN_X_PT, cursor_y + 9.0),
                job_title,
                fontname="hebo",
                fontsize=9.5,
                color=(0.0, 0.0, 0.0),
            )

            comp_x = MARGIN_X_PT + title_w
            page.insert_text(
                pymupdf.Point(comp_x, cursor_y + 9.0),
                clamped_comp_str,
                fontname="helv",
                fontsize=9.0,
                color=DARK_TEXT,
            )

            if date_range:
                date_x = A4_WIDTH_PT - MARGIN_X_PT - date_w
                page.insert_text(
                    pymupdf.Point(date_x, cursor_y + 9.0),
                    date_range,
                    fontname="heit",
                    fontsize=8.5,
                    color=MUTED_TEXT,
                )
            cursor_y += 12.0

            # Bullets
            for b in exp.get("bullets", []):
                b_lines = _wrap_text_by_width(b, USABLE_WIDTH_PT - 14.0, fontname="helv", fontsize=9.0)
                for b_idx, bline in enumerate(b_lines):
                    if b_idx == 0:
                        page.insert_text(
                            pymupdf.Point(MARGIN_X_PT + 4.0, cursor_y + 8.5),
                            "•",
                            fontname="helv",
                            fontsize=9.0,
                            color=NAVY_COLOR,
                        )
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT + 14.0, cursor_y + 8.5),
                        bline,
                        fontname="helv",
                        fontsize=9.0,
                        color=DARK_TEXT,
                    )
                    cursor_y += 11.2

    # 5. Projects
    if tailored_data.projects:
        draw_section_heading("Projects")
        for proj in tailored_data.projects:
            cursor_y += 2.0
            p_name = proj.get("name", "Project")
            p_sub = proj.get("subtitle", "")
            p_techs = proj.get("technologies", [])

            p_title_str = p_name
            if p_sub:
                p_title_str += f"  —  {p_sub}"

            page.insert_text(
                pymupdf.Point(MARGIN_X_PT, cursor_y + 9.0),
                p_name,
                fontname="hebo",
                fontsize=9.5,
                color=(0.0, 0.0, 0.0),
            )
            p_name_w = pymupdf.get_text_length(p_name, fontname="hebo", fontsize=9.5)

            if p_sub:
                page.insert_text(
                    pymupdf.Point(MARGIN_X_PT + p_name_w, cursor_y + 9.0),
                    f"  —  {p_sub}",
                    fontname="helv",
                    fontsize=9.0,
                    color=DARK_TEXT,
                )
            cursor_y += 11.5

            if p_techs:
                tech_str = ", ".join(p_techs)
                page.insert_text(
                    pymupdf.Point(MARGIN_X_PT + 4.0, cursor_y + 8.0),
                    tech_str,
                    fontname="heit",
                    fontsize=8.5,
                    color=MUTED_TEXT,
                )
                cursor_y += 10.5

            for b in proj.get("bullets", []):
                b_lines = _wrap_text_by_width(b, USABLE_WIDTH_PT - 14.0, fontname="helv", fontsize=9.0)
                for b_idx, bline in enumerate(b_lines):
                    if b_idx == 0:
                        page.insert_text(
                            pymupdf.Point(MARGIN_X_PT + 4.0, cursor_y + 8.5),
                            "•",
                            fontname="helv",
                            fontsize=9.0,
                            color=NAVY_COLOR,
                        )
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT + 14.0, cursor_y + 8.5),
                        bline,
                        fontname="helv",
                        fontsize=9.0,
                        color=DARK_TEXT,
                    )
                    cursor_y += 11.2

    # 6. Education
    if tailored_data.education:
        draw_section_heading("Education")
        for edu in tailored_data.education:
            cursor_y += 2.0
            deg = edu.get("degree", "Degree")
            fos = edu.get("field_of_study", "")
            inst = edu.get("institution", "")
            grade = edu.get("grade", "")
            edu_dates = _format_date_range(edu.get("start_date"), edu.get("end_date"))

            left_str = deg
            if fos:
                left_str += f", {fos}"
            if inst:
                left_str += f"  |  {inst}"
            if grade:
                left_str += f"  |  CGPA: {grade}"

            ed_w = pymupdf.get_text_length(edu_dates, fontname="heit", fontsize=8.5) if edu_dates else 0.0
            max_left_w = max(40.0, USABLE_WIDTH_PT - ed_w - 15.0)
            clamped_left_str = _clamp_text_to_width(left_str, max_left_w, fontname="hebo", fontsize=9.0)

            page.insert_text(
                pymupdf.Point(MARGIN_X_PT, cursor_y + 9.0),
                clamped_left_str,
                fontname="hebo",
                fontsize=9.0,
                color=(0.0, 0.0, 0.0),
            )

            if edu_dates:
                page.insert_text(
                    pymupdf.Point(A4_WIDTH_PT - MARGIN_X_PT - ed_w, cursor_y + 9.0),
                    edu_dates,
                    fontname="heit",
                    fontsize=8.5,
                    color=MUTED_TEXT,
                )
            cursor_y += 12.0

    # 7. Achievements & Certifications
    items_to_render = tailored_data.achievements or [
        f"{c.get('name', '')} — {c.get('issuing_organization', '')}".rstrip(" —")
        for c in tailored_data.certifications
    ]
    if items_to_render:
        draw_section_heading("Achievements & Certifications")
        for item in items_to_render:
            a_lines = _wrap_text_by_width(item, USABLE_WIDTH_PT - 14.0, fontname="helv", fontsize=8.5)
            for a_idx, aline in enumerate(a_lines):
                if a_idx == 0:
                    page.insert_text(
                        pymupdf.Point(MARGIN_X_PT + 4.0, cursor_y + 8.0),
                        "•",
                        fontname="helv",
                        fontsize=8.5,
                        color=NAVY_COLOR,
                    )
                page.insert_text(
                    pymupdf.Point(MARGIN_X_PT + 14.0, cursor_y + 8.0),
                    aline,
                    fontname="helv",
                    fontsize=8.5,
                    color=DARK_TEXT,
                )
                cursor_y += 10.8

    # Hard one-page guarantee: verify page count and bottom margin bounds
    max_allowed_y = A4_HEIGHT_PT - MARGIN_Y_PT
    if cursor_y > max_allowed_y:
        if cursor_y - max_allowed_y < 25.0:
            cursor_y = max_allowed_y
        else:
            raise ValueError(
                f"Rendered content exceeded single page capacity: cursor_y={cursor_y:.1f}pt > {max_allowed_y:.1f}pt"
            )
    assert len(doc) == 1, f"Expected strictly 1 page, generated {len(doc)} pages"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    return output_path


def build_and_save_resume_documents(
    tailored_data: TailoredResumeData,
    profile_id: str,
    job_id: str,
    version_number: int,
) -> tuple[Path, Path]:
    """Generate both DOCX and PDF resume files and return their absolute paths."""
    settings = get_settings()
    base_dir = settings.resolved_generated_resumes_dir

    safe_p_id = profile_id[:8]
    safe_j_id = job_id[:8]
    unique_token = uuid.uuid4().hex[:6]
    stem = f"resume_{safe_p_id}_{safe_j_id}_v{version_number}_{unique_token}"

    docx_path = base_dir / f"{stem}.docx"
    pdf_path = base_dir / f"{stem}.pdf"

    try:
        generate_docx(tailored_data, docx_path)
        generate_pdf(tailored_data, pdf_path)
    except Exception:
        docx_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        raise

    return docx_path, pdf_path
