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

