"""Generate a printable PDF artifact of a multi-resume comparison run.

ReportLab-based (matches the project's existing CV PDF generator) so users get
a shareable shortlist document for recruiters / hiring managers without
needing them to log into the app.
"""

from datetime import datetime
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape as _esc

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
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

_PRIMARY = colors.HexColor("#1d4ed8")
_TEXT = colors.HexColor("#0f172a")
_MUTED = colors.HexColor("#64748b")
_RULE = colors.HexColor("#e2e8f0")
_WIN_BG = colors.HexColor("#ecfdf5")
_WIN_BORDER = colors.HexColor("#22c55e")


def _tier_color(score: int) -> colors.Color:
    if score >= 80:
        return colors.HexColor("#15803d")
    if score >= 60:
        return colors.HexColor("#b45309")
    return colors.HexColor("#dc2626")


def _issue_color(issues: int) -> colors.Color:
    if issues <= 5:
        return colors.HexColor("#15803d")
    if issues <= 15:
        return colors.HexColor("#b45309")
    return colors.HexColor("#dc2626")


def generate_comparison_pdf(
    rows: list[dict[str, Any]],
    job_description: str,
    avg_score: float,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> bytes:
    """Render a comparison PDF and return its bytes.

    Layout: title + meta strip → JD block → ranked table (color-coded scores,
    winner row tinted) → per-resume summary blocks (one paragraph each with
    summary text + top missing skills + top suggestions).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Resume Comparison Report",
    )

    styles = {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=_TEXT
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=10, leading=13, textColor=_MUTED
        ),
        "h2": ParagraphStyle(
            "H2",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=_PRIMARY,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=_TEXT
        ),
        "muted": ParagraphStyle(
            "Muted", fontName="Helvetica", fontSize=8.5, leading=11, textColor=_MUTED
        ),
        "meta_right": ParagraphStyle(
            "MetaRight",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=_MUTED,
            alignment=TA_RIGHT,
        ),
    }

    story: list[Any] = []

    # Header
    story.append(Paragraph("Resume Comparison Report", styles["title"]))
    generated_on = datetime.now().strftime("%b %d, %Y · %H:%M")
    top_row = rows[0] if rows else {}
    top_name = str(top_row.get("Resume", "—") or "—")
    top_score = int(top_row.get("Final Score", 0) or 0)
    meta_line = (
        f"{len(rows)} resume{'s' if len(rows) != 1 else ''} compared  ·  "
        f"top match <b>{_esc(top_name)}</b> at {top_score}/100  ·  "
        f"average {avg_score:.1f}  ·  generated {generated_on}"
    )
    story.append(Paragraph(meta_line, styles["subtitle"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.6, color=_RULE))
    story.append(Spacer(1, 8))

    # JD block (truncated to keep the PDF focused on the comparison itself —
    # full JD is in the user's records; this is just enough to anchor context).
    jd = (job_description or "").strip()
    if jd:
        story.append(Paragraph("Job Description", styles["h2"]))
        jd_display = jd if len(jd) <= 1200 else jd[:1199].rstrip() + "…"
        story.append(Paragraph(_esc(jd_display).replace("\n", "<br/>"), styles["body"]))
        story.append(Spacer(1, 8))

    # Ranked table
    story.append(Paragraph("Ranked Comparison", styles["h2"]))
    table_header = ["Rank", "Resume", "Final", "JD Align", "ATS Parse", "Sections", "Issues"]
    table_data: list[list[Any]] = [table_header]
    for row in rows:
        rank = int(row.get("Rank", 0) or 0)
        final = int(row.get("Final Score", 0) or 0)
        jd_align = int(row.get("JD Alignment", 0) or 0)
        ats = int(row.get("ATS Parse", 0) or 0)
        sections = int(row.get("Sections", 0) or 0)
        issues = int(row.get("Issues", 0) or 0)
        name = str(row.get("Resume", "") or "")
        # Truncate very long file names so the row doesn't overflow.
        if len(name) > 36:
            name = name[:33] + "…"
        table_data.append(
            [
                f"#{rank}",
                _esc(name),
                str(final),
                str(jd_align),
                str(ats),
                str(sections),
                str(issues),
            ]
        )

    col_widths = [14 * mm, 60 * mm, 18 * mm, 22 * mm, 22 * mm, 20 * mm, 18 * mm]
    table = Table(table_data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style_cmds: list[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), _MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), _TEXT),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, _RULE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, _RULE),
    ]
    # Per-cell color tinting for score columns + winner row highlight.
    for i, row in enumerate(rows, start=1):
        final = int(row.get("Final Score", 0) or 0)
        jd_align = int(row.get("JD Alignment", 0) or 0)
        ats = int(row.get("ATS Parse", 0) or 0)
        sections = int(row.get("Sections", 0) or 0)
        issues = int(row.get("Issues", 0) or 0)
        style_cmds.append(("TEXTCOLOR", (2, i), (2, i), _tier_color(final)))
        style_cmds.append(("TEXTCOLOR", (3, i), (3, i), _tier_color(jd_align)))
        style_cmds.append(("TEXTCOLOR", (4, i), (4, i), _tier_color(ats)))
        style_cmds.append(("TEXTCOLOR", (5, i), (5, i), _tier_color(sections)))
        style_cmds.append(("TEXTCOLOR", (6, i), (6, i), _issue_color(issues)))
        style_cmds.append(("FONTNAME", (2, i), (6, i), "Helvetica-Bold"))
        if int(row.get("Rank", 0) or 0) == 1:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), _WIN_BG))
            style_cmds.append(("LINEBEFORE", (0, i), (0, i), 2.4, _WIN_BORDER))
            style_cmds.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_cmds))
    story.append(table)
    story.append(Spacer(1, 10))

    # Per-resume summaries (one block per row, no nested page break)
    story.append(Paragraph("Per-Resume Details", styles["h2"]))
    for row in rows:
        analysis = row.get("_analysis") if isinstance(row, dict) else None
        rank = int(row.get("Rank", 0) or 0)
        name = str(row.get("Resume", "") or "")
        score = int(row.get("Final Score", 0) or 0)
        header = f"<b>#{rank}  {_esc(name)}</b>  &nbsp;·&nbsp;  {score}/100"
        story.append(Paragraph(header, styles["body"]))
        if isinstance(analysis, dict):
            summary = str(analysis.get("summary", "") or "").strip()
            if summary:
                if len(summary) > 600:
                    summary = summary[:599].rstrip() + "…"
                story.append(Paragraph(_esc(summary), styles["muted"]))
            missing = [
                str(s).strip() for s in (analysis.get("missing_skills") or []) if str(s).strip()
            ]
            if missing:
                story.append(
                    Paragraph(
                        "<b>Top missing skills:</b> " + _esc(", ".join(missing[:6])),
                        styles["muted"],
                    )
                )
            tips = [str(s).strip() for s in (analysis.get("suggestions") or []) if str(s).strip()]
            if tips:
                bullet_html = "<br/>".join("• " + _esc(t) for t in tips[:4])
                story.append(Paragraph(bullet_html, styles["muted"]))
        else:
            top_missing = str(row.get("Top Missing Skills", "") or "").strip()
            if top_missing and top_missing.lower() != "none":
                story.append(
                    Paragraph(
                        "<b>Top missing skills:</b> " + _esc(top_missing),
                        styles["muted"],
                    )
                )
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.3, color=_RULE))
        story.append(Spacer(1, 6))

    # Errors / warnings appendix (only when present)
    err_list = [e for e in (errors or []) if str(e).strip()]
    warn_list = [w for w in (warnings or []) if str(w).strip()]
    if err_list or warn_list:
        story.append(Paragraph("Notes", styles["h2"]))
        for w in warn_list:
            story.append(Paragraph("• " + _esc(str(w)), styles["muted"]))
        for e in err_list:
            story.append(Paragraph("⚠ " + _esc(str(e)), styles["muted"]))

    doc.build(story)
    return buffer.getvalue()
