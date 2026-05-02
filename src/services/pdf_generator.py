"""Generates professional CVs as PDFs from structured JSON data."""
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape as _esc
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TEMPLATES = {
    "classic": {"primary": "#1a1a2e", "accent": "#16213e", "link": "#2980b9", "rule": "#1a1a2e"},
    "modern": {"primary": "#2c7be5", "accent": "#444444", "link": "#2c7be5", "rule": "#2c7be5"},
    "minimal": {"primary": "#333333", "accent": "#666666", "link": "#333333", "rule": "#aaaaaa"},
}


def _pdf_base_font(font_family: str) -> str:
    """Map a CSS font-family string to a ReportLab built-in font name."""
    f = (font_family or "").lower()
    if "times" in f or ("serif" in f and "sans" not in f) or "georgia" in f:
        return "Times-Roman"
    return "Helvetica"


def generate_cv_pdf(
    data: dict[str, Any],
    template: str = "classic",
    accent_color: str | None = None,
    font_family: str | None = None,
    font_size: int = 11,
    line_height: float = 1.4,
    margin_lr: int = 15,
    margin_tb: int = 5,
    entry_spacing: int = 8,
) -> bytes:
    cfg = dict(TEMPLATES.get(template, TEMPLATES["classic"]))
    if accent_color:
        cfg["primary"] = accent_color
        cfg["rule"] = accent_color
    buffer = BytesIO()

    # Scale PDF body font size from HTML px: HTML 11px ≈ PDF 9pt (base)
    body_pt  = max(7, font_size - 2)
    small_pt = max(6, font_size - 3)
    leading  = round(body_pt * line_height) + 1
    spacer_h = max(2, round(entry_spacing * 0.6))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin_lr * mm,
        rightMargin=margin_lr * mm,
        topMargin=margin_tb * mm,
        bottomMargin=margin_tb * mm,
    )

    primary = colors.HexColor(cfg["primary"])
    accent = colors.HexColor(cfg["accent"])
    link_color = colors.HexColor(cfg["link"])
    rule_color = colors.HexColor(cfg["rule"])
    base_font = _pdf_base_font(font_family or "")
    base_font_bold = base_font.replace("Roman", "Bold") if "Times" in base_font else base_font + "-Bold"

    name_s    = ParagraphStyle("name",    fontSize=22, leading=28, fontName=base_font_bold, alignment=TA_CENTER, textColor=primary, spaceAfter=3)
    contact_s = ParagraphStyle("contact", fontSize=small_pt,  fontName=base_font,      alignment=TA_CENTER, textColor=accent,  spaceAfter=10)
    section_s = ParagraphStyle("section", fontSize=body_pt,   fontName=base_font_bold, textColor=primary,   spaceBefore=spacer_h+2, spaceAfter=2)
    title_s   = ParagraphStyle("title",   fontSize=body_pt,   fontName=base_font_bold, spaceAfter=1, leading=leading)
    sub_s     = ParagraphStyle("sub",     fontSize=small_pt,  fontName=base_font,      textColor=accent, spaceAfter=2, leading=leading-1)
    body_s    = ParagraphStyle("body",    fontSize=body_pt,   fontName=base_font,      spaceAfter=3, leading=leading)
    bullet_s  = ParagraphStyle("bullet",  fontSize=small_pt,  fontName=base_font,      leftIndent=10, spaceAfter=1, leading=leading-1)
    date_s    = ParagraphStyle("date",    fontSize=small_pt,  fontName=base_font,      alignment=TA_RIGHT, textColor=accent)
    skill_s   = ParagraphStyle("skill",   fontSize=body_pt,   fontName=base_font,      spaceAfter=3, leading=leading)
    link_s    = ParagraphStyle("link",    fontSize=max(6,small_pt-1), fontName=base_font, textColor=link_color, spaceAfter=2)

    story: list = []
    personal = data.get("personal", {})

    contact_fields = ["email", "phone", "location", "website", "linkedin", "github"]
    contact_parts = [personal.get(f, "") for f in contact_fields if personal.get(f)]

    if template == "modern":
        # Colored banner header — matches the HTML preview's blue header block
        name_white_s    = ParagraphStyle("name_w",    fontSize=22,       leading=28,         fontName=base_font_bold, alignment=TA_CENTER, textColor=colors.white,                spaceAfter=0)
        contact_light_s = ParagraphStyle("contact_l", fontSize=small_pt, fontName=base_font, alignment=TA_CENTER,     textColor=colors.HexColor("#bfdbfe"), spaceAfter=0)
        banner_rows = [[Paragraph(_esc(personal.get("full_name") or "Your Name"), name_white_s)]]
        if contact_parts:
            banner_rows.append([Paragraph(" · ".join(_esc(p) for p in contact_parts), contact_light_s)])
        content_w = A4[0] - margin_lr * mm * 2
        banner = Table(banner_rows, colWidths=[content_w])
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), primary),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("LEFTPADDING",   (0, 0), (-1, -1), 20),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ]))
        story.append(banner)
        story.append(Spacer(1, 10))
    else:
        # Classic / Minimal: centered name, centered contact row, horizontal rule
        story.append(Paragraph(_esc(personal.get("full_name") or "Your Name"), name_s))
        if contact_parts:
            story.append(Paragraph(" · ".join(_esc(p) for p in contact_parts), contact_s))
        story.append(HRFlowable(width="100%", thickness=1.5, color=rule_color))
        story.append(Spacer(1, 4))

    def section_header(label: str) -> None:
        story.append(Paragraph(label.upper(), section_s))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 3))

    def role_date_row(left: str, right: str) -> None:
        row = [[Paragraph(left, title_s), Paragraph(right, date_s)]]
        t = Table(row, colWidths=["75%", "25%"])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(t)

    summary = personal.get("summary", "")
    if summary:
        section_header("Professional Summary")
        story.append(Paragraph(_esc(summary), body_s))

    experience = data.get("experience", [])
    if experience:
        section_header("Experience")
        for exp in experience:
            start = exp.get("start_date", "")
            end = "Present" if exp.get("current") else exp.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{_esc(exp.get('role', ''))}</b>", date_range)
            loc = exp.get("location", "")
            story.append(Paragraph(f"{_esc(exp.get('company', ''))}{', ' + _esc(loc) if loc else ''}", sub_s))
            for b in exp.get("bullets", []):
                if b.strip():
                    story.append(Paragraph(f"• {_esc(b)}", bullet_s))
            story.append(Spacer(1, 5))

    education = data.get("education", [])
    if education:
        section_header("Education")
        for edu in education:
            start = edu.get("start_date", "")
            end = edu.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{_esc(edu.get('institution', ''))}</b>", date_range)
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field", ""))
            gpa = _esc(edu.get("gpa", ""))
            degree_line = f"{deg}{', ' + field if field else ''}{' | GPA: ' + gpa if gpa else ''}"
            story.append(Paragraph(degree_line, sub_s))
            for h in edu.get("highlights", []):
                if h.strip():
                    story.append(Paragraph(f"• {_esc(h)}", bullet_s))
            story.append(Spacer(1, 5))

    categories = data.get("skills", {}).get("categories", [])
    if categories:
        section_header("Skills")
        for cat in categories:
            items = cat.get("items", [])
            if items:
                story.append(Paragraph(f"<b>{_esc(cat.get('name', ''))}:</b> {', '.join(_esc(i) for i in items)}", skill_s))

    projects = data.get("projects", [])
    if projects:
        section_header("Projects")
        for proj in projects:
            start = proj.get("start_date", "")
            end = proj.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{_esc(proj.get('name', ''))}</b>", date_range)
            tech = proj.get("tech_stack", [])
            if tech:
                story.append(Paragraph(f"<i>Tech: {', '.join(_esc(t) for t in tech)}</i>", sub_s))
            desc = proj.get("description", "")
            if desc:
                story.append(Paragraph(_esc(desc), body_s))
            link = proj.get("link", "")
            if link:
                story.append(Paragraph(_esc(link), link_s))
            story.append(Spacer(1, 5))

    certifications = data.get("certifications", [])
    if certifications:
        section_header("Certifications")
        for cert in certifications:
            name_ = cert.get("name", "")
            issuer = cert.get("issuer", "")
            date = cert.get("date", "")
            parts = f"<b>{_esc(name_)}</b>"
            if issuer:
                parts += f" — {_esc(issuer)}"
            if date:
                parts += f" ({_esc(date)})"
            story.append(Paragraph(f"• {parts}", body_s))

    doc.build(story)
    return buffer.getvalue()
