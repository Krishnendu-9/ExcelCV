"""Final-project career enhancement helpers.

These helpers build deterministic, presentation-friendly add-ons from the
existing analysis payload without changing core scoring behavior.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _normalize_items(value: Any, limit: int = 8) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = str(item).strip()
        if not text or text in out:
            continue
        out.append(text)
        if len(out) >= limit:
            break
    return out


def build_recruiter_snapshot(analysis: Dict[str, Any], resume_name: str) -> Dict[str, str]:
    """Build a concise recruiter-facing summary from analysis data."""
    score = int(analysis.get("match_score", 0) or 0)
    strengths = _normalize_items(analysis.get("strengths", []), limit=2)
    gaps = _normalize_items(analysis.get("missing_skills", []), limit=2)

    if score >= 80:
        verdict = "Strong Fit"
    elif score >= 65:
        verdict = "Potential Fit"
    else:
        verdict = "Needs Improvement"

    top_strength = strengths[0] if strengths else "resume structure and ATS readiness"
    top_gap = gaps[0] if gaps else "role-specific depth in key requirements"
    summary = (
        f"{resume_name} is currently rated {score}/100 ({verdict}). "
        f"Top positive signal: {top_strength}. "
        f"Main risk before applying: {top_gap}."
    )

    return {
        "verdict": verdict,
        "summary": summary,
    }


def build_priority_action_plan(
    analysis: Dict[str, Any], max_items: int = 8
) -> List[Dict[str, str]]:
    """Build a prioritized action plan from detected weaknesses."""
    content = analysis.get("content_metrics", {}) or {}
    quant_score = int((content.get("quantifying_impact", {}) or {}).get("score", 0))
    repetition_score = int((content.get("repetition", {}) or {}).get("score", 0))
    spelling_score = int((content.get("spelling_grammar", {}) or {}).get("score", 0))
    parse_score = int(content.get("ats_parse_rate", 0) or 0)
    sections_details = (analysis.get("sections_metrics", {}) or {}).get("details", {}) or {}
    missing_sections = _normalize_items(sections_details.get("missing_sections", []), limit=4)
    missing_skills = _normalize_items(analysis.get("missing_skills", []), limit=4)
    missing_keywords = _normalize_items(analysis.get("missing_keywords", []), limit=4)

    actions: List[Dict[str, str]] = []

    def add_action(title: str, priority: str, impact: str, effort: str, action: str) -> None:
        if len(actions) >= max_items:
            return
        actions.append(
            {
                "title": title,
                "priority": priority,
                "impact": impact,
                "effort": effort,
                "action": action,
            }
        )

    if parse_score < 80:
        add_action(
            "Improve ATS Parse Reliability",
            "High",
            "High",
            "Medium",
            "Use standard section headings and simplify complex formatting/graphics.",
        )
    if quant_score < 70:
        add_action(
            "Quantify Achievement Bullets",
            "High",
            "High",
            "Medium",
            "Add metrics (%/$/counts/time) to each experience bullet to prove business impact.",
        )
    if spelling_score < 90:
        add_action(
            "Fix Spelling and Grammar Errors",
            "High",
            "Medium",
            "Low",
            "Run proofreading and remove all grammatical/spelling issues before final submission.",
        )
    if repetition_score < 80:
        add_action(
            "Reduce Repeated Action Verbs",
            "Medium",
            "Medium",
            "Low",
            "Replace overused words with varied verbs to improve readability and professionalism.",
        )
    if missing_sections:
        add_action(
            "Complete Missing Resume Sections",
            "High",
            "High",
            "Low",
            f"Add these sections first: {', '.join(missing_sections)}.",
        )
    if missing_skills:
        add_action(
            "Close Critical Skill Gaps",
            "High",
            "High",
            "High",
            f"Address top missing skills in projects/certifications: {', '.join(missing_skills[:3])}.",
        )
    if missing_keywords:
        add_action(
            "Increase JD Keyword Coverage",
            "Medium",
            "High",
            "Low",
            f"Naturally include role keywords in relevant bullets: {', '.join(missing_keywords[:3])}.",
        )

    if not actions:
        add_action(
            "Maintain Current Resume Quality",
            "Low",
            "Medium",
            "Low",
            "Your resume is in good shape. Keep content updated for each application.",
        )

    return actions[:max_items]


def build_interview_prep_questions(
    analysis: Dict[str, Any],
    job_desc: str,
    max_items: int = 8,
) -> List[Dict[str, str]]:
    """Generate targeted interview preparation questions."""
    missing_skills = _normalize_items(analysis.get("missing_skills", []), limit=5)
    strengths = _normalize_items(analysis.get("strengths", []), limit=3)
    jd_present = bool(str(job_desc or "").strip())

    questions: List[Dict[str, str]] = []

    for skill in missing_skills:
        if len(questions) >= max_items:
            break
        questions.append(
            {
                "type": "Gap Mitigation",
                "question": f"How would you ramp up quickly on {skill} in your first 30 days?",
                "why": "Interviewers test ownership and learning strategy for missing skills.",
            }
        )

    for point in strengths:
        if len(questions) >= max_items:
            break
        questions.append(
            {
                "type": "Strength Deep Dive",
                "question": f"Can you share a specific example where you demonstrated: {point}?",
                "why": "You should convert strengths into quantifiable stories using STAR format.",
            }
        )

    if len(questions) < max_items:
        questions.append(
            {
                "type": "Behavioral",
                "question": "Describe a project where you handled ambiguity and delivered under deadline pressure.",
                "why": "Common final-round question to evaluate execution maturity.",
            }
        )
    if len(questions) < max_items and jd_present:
        questions.append(
            {
                "type": "Role Alignment",
                "question": "Which JD requirement best matches your strongest project, and what measurable result did you deliver?",
                "why": "Directly connects your experience to the target role.",
            }
        )

    return questions[:max_items]


def build_learning_roadmap(analysis: Dict[str, Any], max_items: int = 6) -> List[Dict[str, str]]:
    """Build a concise skill-closure roadmap for missing capabilities."""
    missing_skills = _normalize_items(analysis.get("missing_skills", []), limit=max_items)
    missing_keywords = _normalize_items(analysis.get("missing_keywords", []), limit=max_items)
    gaps = missing_skills or missing_keywords
    if not gaps:
        return []

    roadmap: List[Dict[str, str]] = []
    for gap in gaps[:max_items]:
        roadmap.append(
            {
                "skill": gap,
                "target": "Demonstrate evidence in resume within 2-3 weeks",
                "plan": "Build one mini-project bullet with measurable outcome and add it to Experience/Projects.",
            }
        )
    return roadmap


def build_portfolio_checklist(analysis: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build completed/missing portfolio checklist items for final project readiness."""
    completed: List[str] = []
    missing: List[str] = []

    sections = (analysis.get("sections_metrics", {}) or {}).get("details", {}) or {}
    contact = analysis.get("contact_info", {}) or {}
    header_links = (
        (analysis.get("ats_essentials_metrics", {}) or {}).get("details", {}) or {}
    ).get("header_links", {}) or {}
    suggestions = _normalize_items(analysis.get("suggestions", []), limit=6)

    if sections.get("has_experience"):
        completed.append("Experience section present")
    else:
        missing.append("Add a strong Experience section")
    if sections.get("has_skills"):
        completed.append("Skills section present")
    else:
        missing.append("Add a Skills section aligned to target role")
    if contact.get("found"):
        completed.append("Contact details extracted")
    else:
        missing.append("Add complete contact details")
    if header_links.get("has_links"):
        completed.append("Header links detected (LinkedIn/GitHub/portfolio)")
    else:
        missing.append("Add LinkedIn or GitHub URL in resume header")
    if suggestions:
        missing.append("Apply top suggestions before final submission")

    return {
        "completed": completed,
        "missing": missing,
    }
