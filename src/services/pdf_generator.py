"""Generates professional CVs as PDFs from structured JSON data."""
from io import BytesIO
from typing import Any
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


def generate_cv_pdf(data: dict[str, Any], template: str = "classic") -> bytes:
    cfg = TEMPLATES.get(template, TEMPLATES["classic"])
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    primary = colors.HexColor(cfg["primary"])
    accent = colors.HexColor(cfg["accent"])
    link_color = colors.HexColor(cfg["link"])
    rule_color = colors.HexColor(cfg["rule"])

    name_s = ParagraphStyle("name", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=primary, spaceAfter=3)
    contact_s = ParagraphStyle("contact", fontSize=9, fontName="Helvetica", alignment=TA_CENTER, textColor=accent, spaceAfter=10)
    section_s = ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold", textColor=primary, spaceBefore=10, spaceAfter=2)
    title_s = ParagraphStyle("title", fontSize=10, fontName="Helvetica-Bold", spaceAfter=1, leading=13)
    sub_s = ParagraphStyle("sub", fontSize=9, fontName="Helvetica", textColor=accent, spaceAfter=2, leading=12)
    body_s = ParagraphStyle("body", fontSize=9, fontName="Helvetica", spaceAfter=3, leading=13)
    bullet_s = ParagraphStyle("bullet", fontSize=9, fontName="Helvetica", leftIndent=10, spaceAfter=1, leading=13)
    date_s = ParagraphStyle("date", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT, textColor=accent)
    skill_s = ParagraphStyle("skill", fontSize=9, fontName="Helvetica", spaceAfter=3, leading=13)
    link_s = ParagraphStyle("link", fontSize=8, fontName="Helvetica", textColor=link_color, spaceAfter=2)

    story: list = []
    personal = data.get("personal", {})

    story.append(Paragraph(personal.get("full_name") or "Your Name", name_s))

    contact_fields = ["email", "phone", "location", "website", "linkedin", "github"]
    contact_parts = [personal.get(f, "") for f in contact_fields if personal.get(f)]
    if contact_parts:
        story.append(Paragraph(" · ".join(contact_parts), contact_s))

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
        story.append(Paragraph(summary, body_s))

    experience = data.get("experience", [])
    if experience:
        section_header("Experience")
        for exp in experience:
            start = exp.get("start_date", "")
            end = "Present" if exp.get("current") else exp.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{exp.get('role', '')}</b>", date_range)
            loc = exp.get("location", "")
            story.append(Paragraph(f"{exp.get('company', '')}{', ' + loc if loc else ''}", sub_s))
            for b in exp.get("bullets", []):
                if b.strip():
                    story.append(Paragraph(f"• {b}", bullet_s))
            story.append(Spacer(1, 5))

    education = data.get("education", [])
    if education:
        section_header("Education")
        for edu in education:
            start = edu.get("start_date", "")
            end = edu.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{edu.get('institution', '')}</b>", date_range)
            deg = edu.get("degree", "")
            field = edu.get("field", "")
            gpa = edu.get("gpa", "")
            degree_line = f"{deg}{', ' + field if field else ''}{' | GPA: ' + gpa if gpa else ''}"
            story.append(Paragraph(degree_line, sub_s))
            for h in edu.get("highlights", []):
                if h.strip():
                    story.append(Paragraph(f"• {h}", bullet_s))
            story.append(Spacer(1, 5))

    categories = data.get("skills", {}).get("categories", [])
    if categories:
        section_header("Skills")
        for cat in categories:
            items = cat.get("items", [])
            if items:
                story.append(Paragraph(f"<b>{cat.get('name', '')}:</b> {', '.join(items)}", skill_s))

    projects = data.get("projects", [])
    if projects:
        section_header("Projects")
        for proj in projects:
            start = proj.get("start_date", "")
            end = proj.get("end_date", "")
            date_range = f"{start} – {end}" if start else end
            role_date_row(f"<b>{proj.get('name', '')}</b>", date_range)
            tech = proj.get("tech_stack", [])
            if tech:
                story.append(Paragraph(f"<i>Tech: {', '.join(tech)}</i>", sub_s))
            desc = proj.get("description", "")
            if desc:
                story.append(Paragraph(desc, body_s))
            link = proj.get("link", "")
            if link:
                story.append(Paragraph(link, link_s))
            story.append(Spacer(1, 5))

    certifications = data.get("certifications", [])
    if certifications:
        section_header("Certifications")
        for cert in certifications:
            name_ = cert.get("name", "")
            issuer = cert.get("issuer", "")
            date = cert.get("date", "")
            parts = f"<b>{name_}</b>"
            if issuer:
                parts += f" — {issuer}"
            if date:
                parts += f" ({date})"
            story.append(Paragraph(f"• {parts}", body_s))

    doc.build(story)
    return buffer.getvalue()
