from io import BytesIO
from typing import Any, Dict, List


def build_report_md(name: str, analysis: Dict[str, Any]) -> str:
    subs = analysis.get("subscores", {}) or {}

    def _section(title: str, items: List[str]) -> str:
        if not items:
            return f"### {title}\n- None noted\n"
        return f"### {title}\n" + "\n".join([f"- {item}" for item in items]) + "\n"

    md = [
        f"# CV Analysis Report - {name}",
        f"- Match Score: {analysis.get('match_score', 0)}%",
        f"- Skills Alignment: {subs.get('skills_alignment', 0)}%",
        f"- Experience Alignment: {subs.get('experience_alignment', 0)}%",
        f"- ATS Readiness: {subs.get('ats_readiness', 0)}%",
        "",
        _section("Strengths", analysis.get("strengths", [])),
        _section("Missing Skills", analysis.get("missing_skills", [])),
        _section("Missing Keywords (ATS)", analysis.get("missing_keywords", [])),
        _section("Suggestions", analysis.get("suggestions", [])),
    ]
    return "\n".join(md)


def build_report_pdf_bytes(name: str, analysis: Dict[str, Any]) -> bytes:
    """Build a compact PDF report and return bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError(
            "PDF export requires reportlab. Install it from requirements.txt."
        ) from exc

    def _normalize_lines(title: str, items: Any) -> List[str]:
        values = items if isinstance(items, list) else []
        if not values:
            return [f"{title}: None noted"]
        lines = [f"{title}:"]
        for item in values:
            text = str(item).strip()
            if text:
                lines.append(f"- {text}")
        return lines if len(lines) > 1 else [f"{title}: None noted"]

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 50
    line_h = 15
    max_chars = 105

    subs = analysis.get("subscores", {}) or {}
    content_lines = [
        f"CV Analysis Report - {name}",
        f"Match Score: {analysis.get('match_score', 0)}%",
        f"Skills Alignment: {subs.get('skills_alignment', 0)}%",
        f"Experience Alignment: {subs.get('experience_alignment', 0)}%",
        f"ATS Readiness: {subs.get('ats_readiness', 0)}%",
        "",
    ]
    content_lines.extend(_normalize_lines("Strengths", analysis.get("strengths", [])))
    content_lines.append("")
    content_lines.extend(_normalize_lines("Missing Skills", analysis.get("missing_skills", [])))
    content_lines.append("")
    content_lines.extend(
        _normalize_lines("Missing Keywords (ATS)", analysis.get("missing_keywords", []))
    )
    content_lines.append("")
    content_lines.extend(_normalize_lines("Suggestions", analysis.get("suggestions", [])))

    pdf.setFont("Helvetica", 11)
    for raw_line in content_lines:
        line = str(raw_line or "")
        chunks = [line[i : i + max_chars] for i in range(0, len(line), max_chars)] or [""]
        for chunk in chunks:
            if y <= 45:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = height - 50
            pdf.drawString(x, y, chunk)
            y -= line_h

    pdf.save()
    return buffer.getvalue()
