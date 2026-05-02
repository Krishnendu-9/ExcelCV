"""
Report-page rendering and interactive sidebar utilities.
"""

import json
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from src.reporting import build_report_pdf_bytes
from src.ui.common import (
    _markdown_inline_to_html,
    get_score_color_class,
    issue_count,
)

def _build_sidebar_html(score: int, issues: int, categories: list) -> str:
    """Build the entire sidebar as one complete HTML string."""
    issues_cls = 'clickable' if issues > 0 else ''
    issues_attr = 'data-section-id="suggestions"' if issues > 0 else ''

    html = f"""
    <div class="report-sidebar">
        <div class="score-card">
            <div class="score-title text-muted" style="font-size:0.95rem;">Your Score</div>
            <div class="score-number">{score}<span>/100</span></div>
            <div class="issues-text {issues_cls}" {issues_attr}>{issues} issues</div>
        </div>"""

    for title, cat_score, items in categories:
        safe_score = int(cat_score) if cat_score is not None else 0
        badge_cls = get_score_color_class(safe_score)
        category_id = title.lower().replace(" ", "-")
        has_items = len(items) > 0
        cursor = 'cursor:pointer;' if has_items else ''
        chevron = '<span class="category-chevron">&#9660;</span>' if has_items else ''

        html += f"""
        <div class="category">
            <div class="category-head" id="cat-head-{category_id}" style="{cursor}">
                <span class="category-title">
                    <span>{title}</span>
                    {chevron}
                </span>
                <span class="category-score {badge_cls}">{safe_score}%</span>
            </div>"""

        if has_items:
            html += f'<div class="category-items collapsed" id="cat-items-{category_id}">'
            for item in items:
                item_label, status = item[0], item[1]
                score_val = item[2] if len(item) > 2 else None
                badge_class = {"ok": "badge badge-ok", "warn": "badge badge-warn",
                               "error": "badge badge-warn", "lock": "badge badge-lock"
                               }.get(status, "badge badge-warn")

                # For Content category metrics, always show percentage score.
                # always show percentage score, not issue count
                is_content_metric = item_label in (
                    "Explainable Scoring",
                    "ATS Parse Rate",
                    "Quantifying Impact",
                    "Repetition",
                    "Spelling & Grammar",
                )
                
                if is_content_metric:
                    # Always show percentage for content metrics
                    if score_val is not None and isinstance(score_val, (int, float)):
                        badge_text = f"{int(score_val)}%"
                    else:
                        badge_text = "N/A"
                elif status in ("warn", "error"):
                    # For other metrics, show issue count if available
                    if score_val is not None and isinstance(score_val, (int, float)):
                        badge_text = f"{int(score_val)} {'issue' if int(score_val) == 1 else 'issues'}"
                    else:
                        badge_text = "Review"
                else:
                    badge_text = {"ok": "No issues", "lock": "Locked"}.get(status, "Review")

                section_id = item_label.lower().replace(" & ", "-").replace(" ", "-").replace("--", "-").strip("-")
                icon_cls = "icon-ok" if status == "ok" else "icon-warn"
                icon = "&#10003;" if status == "ok" else "&#10005;"
                clickable = "clickable" if status != "lock" else ""
                data = f'data-section-id="{section_id}"' if status != "lock" else ""

                html += f"""
                <div class="subitem {clickable}" {data}>
                    <span class="subitem-label-wrap">
                        <span class="subitem-icon {icon_cls}">{icon}</span>
                        <span>{item_label}</span>
                    </span>
                    <span class="{badge_class}">{badge_text}</span>
                </div>"""
            html += '</div>'  # close category-items

        html += '</div>'  # close category

    html += '</div>'  # close report-sidebar
    return html



def _escape_html(value: Any) -> str:
    """Escape text for safe insertion into HTML snippets."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_ats_parse_rate_html(ats_val: int) -> str:
    ats_badge_cls = "badge-ok" if ats_val >= 80 else "badge-warn"
    ats_badge_txt = "Excellent" if ats_val >= 80 else ("Good" if ats_val >= 60 else "Needs Improvement")
    ats_msg = (
        f"Great! We parsed {ats_val}% of your resume successfully."
        if ats_val >= 80
        else f"We could parse {ats_val}% of your resume. Consider improving formatting for better ATS compatibility."
    )
    ats_card_cls = "good-card" if ats_val >= 80 else ""
    return f"""
            <div class="detail-card section-anchor" id="ats-parse-rate">
                <div class="detail-head">
                    <h3>ATS Parse Rate</h3>
                    <span class="badge {ats_badge_cls}">{ats_badge_txt}</span>
                </div>
                <div class="section-body">
                    <p class="section-body-item text-description">A high parse rate ensures the ATS can read your resume, experience, and skills.</p>
                    <div class="progress-track dark"><div class="progress-fill dark" style="width:{ats_val}%"></div></div>
                    <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                        <span>Score</span><span>{ats_val}%</span>
                    </div>
                    <div class="issue-card {ats_card_cls}" style="margin-top:14px;">
                        <div class="issue-heading">{ats_msg}</div>
                    </div>
                </div>
            </div>
            """


def _build_explainable_scoring_html(score_breakdown: Dict[str, Any]) -> str:
    """Build explainable weighted scoring card."""
    final_score = int(score_breakdown.get("final_score", 0))
    mode = score_breakdown.get("mode", "jd_aligned")
    content_avg = int(score_breakdown.get("content_average", 0))
    components = score_breakdown.get("components", []) or []

    mode_text = (
        "JD-aligned mode (job description provided)"
        if mode == "jd_aligned"
        else "No-JD mode (weights redistributed)"
    )
    html = f"""
        <div class="detail-card section-anchor" id="explainable-scoring">
            <div class="detail-head">
                <h3>Explainable Scoring</h3>
                <span class="badge badge-ok">{final_score}%</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Final score is calculated by weighted deterministic components. Mode: {mode_text}.
                    Content average is {content_avg}% from ATS Parse, Quantifying Impact, Repetition, and Spelling.
                </p>
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">Weighted score breakdown</div>
    """
    for component in components:
        label = _escape_html(component.get("label", "Component"))
        score = int(component.get("score", 0))
        weight = float(component.get("weight", 0))
        weighted_points = float(component.get("weighted_points", 0))
        html += f"""
                    <div class="contact-row">
                        <span class="contact-label">{label}</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value">{score}% x {weight:.2f} = {weighted_points:.2f}</span>
                    </div>
        """
    html += """
                </div>
            </div>
        </div>
    """
    return html


def _build_skill_matrix_html(skill_matrix: List[Dict[str, Any]]) -> str:
    """Build JD-to-skill evidence matrix card."""
    if not skill_matrix:
        return """
        <div class="detail-card section-anchor" id="jd-skill-matrix">
            <div class="detail-head">
                <h3>JD Skill Matrix</h3>
                <span class="badge badge-lock">Locked</span>
            </div>
            <div class="section-body">
                <div class="issue-card">
                    <div class="issue-heading">Add a job description to generate the skill evidence matrix.</div>
                </div>
            </div>
        </div>
        """

    found = sum(1 for row in skill_matrix if row.get("status") == "Found")
    partial = sum(1 for row in skill_matrix if row.get("status") == "Partial")
    missing = sum(1 for row in skill_matrix if row.get("status") == "Missing")
    badge_cls = "ok" if missing == 0 else "warn"
    badge_text = "All covered" if missing == 0 else f"{missing} missing"

    html = f"""
        <div class="detail-card section-anchor" id="jd-skill-matrix">
            <div class="detail-head">
                <h3>JD Skill Matrix</h3>
                <span class="badge badge-{badge_cls}">{badge_text}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Skill evidence mapping: {found} found, {partial} partial, {missing} missing.
                </p>
                <div class="issue-card" style="margin-top:10px;">
    """
    for row in skill_matrix:
        skill = _escape_html(row.get("skill", ""))
        status = row.get("status", "Missing")
        evidence = _escape_html(row.get("evidence", ""))
        icon = "&#10003;" if status == "Found" else ("&#9888;" if status == "Partial" else "&#10005;")
        icon_cls = "found" if status == "Found" else "missing"
        html += f"""
                    <div class="contact-row">
                        <span class="contact-icon {icon_cls}">{icon}</span>
                        <span class="contact-label">{skill}</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{status}: {evidence}</span>
                    </div>
        """
    html += """
                </div>
            </div>
        </div>
    """
    return html


def _build_rewrite_assistant_html(rewrite_recommendations: List[Dict[str, Any]]) -> str:
    """Build before/after rewrite suggestions card."""
    if not rewrite_recommendations:
        return """
        <div class="detail-card section-anchor" id="rewrite-assistant">
            <div class="detail-head">
                <h3>Rewrite Assistant</h3>
                <span class="badge badge-ok">No issues</span>
            </div>
            <div class="section-body">
                <div class="issue-card good-card">
                    <div class="issue-heading">No rewrite recommendations generated from current analysis.</div>
                </div>
            </div>
        </div>
        """

    html = f"""
        <div class="detail-card section-anchor" id="rewrite-assistant">
            <div class="detail-head">
                <h3>Rewrite Assistant</h3>
                <span class="badge badge-warn">{len(rewrite_recommendations)} suggestions</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Before/after rewrites to strengthen impact and clarity. Replace placeholders with real metrics.
                </p>
    """
    for row in rewrite_recommendations:
        before = _escape_html(row.get("before", ""))
        after = _escape_html(row.get("after", ""))
        rationale = _escape_html(row.get("rationale", ""))
        html += f"""
                <div class="issue-card" style="margin-top:10px;">
                    <div class="contact-row">
                        <span class="contact-label">Before</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{before}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">After</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{after}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Why</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{rationale}</span>
                    </div>
                </div>
        """
    html += """
            </div>
        </div>
    """
    return html


def _build_recruiter_snapshot_html(snapshot: Dict[str, Any]) -> str:
    verdict = _escape_html(snapshot.get("verdict", "Snapshot"))
    summary = _escape_html(snapshot.get("summary", "No recruiter snapshot available."))
    badge = "ok" if verdict == "Strong Fit" else ("warn" if verdict == "Potential Fit" else "warn")
    return f"""
        <div class="detail-card section-anchor" id="recruiter-snapshot">
            <div class="detail-head">
                <h3>Recruiter Snapshot</h3>
                <span class="badge badge-{badge}">{verdict}</span>
            </div>
            <div class="section-body">
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">Quick recruiter-view summary</div>
                    <div class="text-description" style="margin-top:8px;">{summary}</div>
                </div>
            </div>
        </div>
    """


def _build_priority_action_plan_html(action_plan: List[Dict[str, Any]]) -> str:
    if not action_plan:
        return """
        <div class="detail-card section-anchor" id="priority-action-plan">
            <div class="detail-head">
                <h3>Priority Action Plan</h3>
                <span class="badge badge-ok">No issues</span>
            </div>
            <div class="section-body">
                <div class="issue-card good-card">
                    <div class="issue-heading">No immediate high-priority actions detected.</div>
                </div>
            </div>
        </div>
        """

    html = f"""
        <div class="detail-card section-anchor" id="priority-action-plan">
            <div class="detail-head">
                <h3>Priority Action Plan</h3>
                <span class="badge badge-warn">{len(action_plan)} actions</span>
            </div>
            <div class="section-body">
    """
    for idx, item in enumerate(action_plan, start=1):
        title = _escape_html(item.get("title", "Action item"))
        priority = _escape_html(item.get("priority", "Medium"))
        impact = _escape_html(item.get("impact", "Medium"))
        effort = _escape_html(item.get("effort", "Medium"))
        action = _escape_html(item.get("action", ""))
        html += f"""
                <div class="issue-card" style="margin-top:10px;text-align:left;">
                    <div class="issue-heading">{idx}. {title}</div>
                    <div class="text-description" style="margin-top:6px;">Priority: {priority} | Impact: {impact} | Effort: {effort}</div>
                    <div class="contact-row" style="margin-top:10px;">
                        <span class="contact-label">Next Step</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{action}</span>
                    </div>
                </div>
        """
    html += """
            </div>
        </div>
    """
    return html


def _build_interview_prep_html(interview_prep: List[Dict[str, Any]]) -> str:
    if not interview_prep:
        return """
        <div class="detail-card section-anchor" id="interview-prep">
            <div class="detail-head">
                <h3>Interview Prep</h3>
                <span class="badge badge-lock">Locked</span>
            </div>
            <div class="section-body">
                <div class="issue-card">
                    <div class="issue-heading">Not enough data to generate interview prep prompts.</div>
                </div>
            </div>
        </div>
        """

    html = f"""
        <div class="detail-card section-anchor" id="interview-prep">
            <div class="detail-head">
                <h3>Interview Prep</h3>
                <span class="badge badge-ok">{len(interview_prep)} questions</span>
            </div>
            <div class="section-body">
    """
    for row in interview_prep:
        q_type = _escape_html(row.get("type", "Question"))
        question = _escape_html(row.get("question", ""))
        why = _escape_html(row.get("why", ""))
        html += f"""
                <div class="issue-card" style="margin-top:10px;text-align:left;">
                    <div class="issue-heading">{q_type}</div>
                    <div class="contact-row">
                        <span class="contact-label">Q</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{question}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Why</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{why}</span>
                    </div>
                </div>
        """
    html += """
            </div>
        </div>
    """
    return html


def _build_learning_roadmap_html(roadmap: List[Dict[str, Any]]) -> str:
    if not roadmap:
        return """
        <div class="detail-card section-anchor" id="learning-roadmap">
            <div class="detail-head">
                <h3>Learning Roadmap</h3>
                <span class="badge badge-ok">On track</span>
            </div>
            <div class="section-body">
                <div class="issue-card good-card">
                    <div class="issue-heading">No significant skill-gap roadmap required right now.</div>
                </div>
            </div>
        </div>
        """

    html = f"""
        <div class="detail-card section-anchor" id="learning-roadmap">
            <div class="detail-head">
                <h3>Learning Roadmap</h3>
                <span class="badge badge-warn">{len(roadmap)} targets</span>
            </div>
            <div class="section-body">
    """
    for row in roadmap:
        skill = _escape_html(row.get("skill", "Skill"))
        target = _escape_html(row.get("target", ""))
        plan = _escape_html(row.get("plan", ""))
        html += f"""
                <div class="issue-card" style="margin-top:10px;text-align:left;">
                    <div class="issue-heading">{skill}</div>
                    <div class="contact-row">
                        <span class="contact-label">Target</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{target}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Plan</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{plan}</span>
                    </div>
                </div>
        """
    html += """
            </div>
        </div>
    """
    return html


def _build_design_html(ats_issues: List[str]) -> str:
    """Build ATS design recommendations card."""
    badge_type = "ok" if not ats_issues else "warn"
    badge_text = "No issues" if not ats_issues else f"{len(ats_issues)} issues"
    html = f"""
        <div class="detail-card section-anchor" id="design">
            <div class="detail-head">
                <h3>Design</h3>
                <span class="badge badge-{badge_type}">{badge_text}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Keep your layout clean and ATS-friendly by avoiding heavy graphics, complex columns, and decorative elements that reduce parse quality.
                </p>"""
    if ats_issues:
        html += """
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">Design elements to review:</div>"""
        for issue in ats_issues:
            html += f"""
                    <div class="issue-item">
                        <span class="issue-x">&#10005;</span>
                        <span>{_escape_html(issue)}</span>
                    </div>"""
        html += "</div>"
    else:
        html += """
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">Design is ATS-safe and easy to scan.</div>
                </div>"""
    html += "</div></div>"
    return html


def _build_quantifying_impact_html(quant_impact: Dict[str, Any]) -> str:
    q_score = quant_impact.get("score", 0)
    q_status = quant_impact.get("status", "ok")
    q_non_quant = quant_impact.get("non_quantified_lines", [])
    q_total = quant_impact.get("total_lines", 0)
    q_count = quant_impact.get("quantified_count", 0)
    q_badge = "ok" if q_status == "ok" else "warn"
    q_label = "No issues" if q_status == "ok" else f"{q_score}%"

    quant_html = f"""
        <div class="detail-card section-anchor" id="quantifying-impact">
            <div class="detail-head">
                <h3>Quantifying Impact</h3>
                <span class="badge badge-{q_badge}">{q_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Your resume should include quantifiable achievements with numbers, metrics, and measurable results.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{q_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score</span><span>{q_score}%</span>
                </div>"""

    if q_non_quant:
        quant_html += f"""
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">Your experience section lacks quantifiable achievements</div>
                    <div class="issue-desc">{q_count} of {q_total} bullet points contain numbers. The following need quantification:</div>"""
        for line in q_non_quant:
            quant_html += f'<div class="issue-item"><span class="issue-x">&#10005;</span><span>{_escape_html(line)}</span></div>'
        quant_html += '</div>'
    elif q_status == "ok":
        quant_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">Great job! Your achievements are well quantified.</div>
                </div>"""

    quant_html += '</div></div>'
    return quant_html


def _build_repetition_html(repetition: Dict[str, Any]) -> str:
    r_score = repetition.get("score", 0)
    r_status = repetition.get("status", "ok")
    r_repeated = repetition.get("repeated_words", [])
    r_badge = "ok" if r_status == "ok" else "warn"
    r_label = "No issues" if r_status == "ok" else f"{r_score}%"

    rep_html = f"""
        <div class="detail-card section-anchor" id="repetition">
            <div class="detail-head">
                <h3>Repetition</h3>
                <span class="badge badge-{r_badge}">{r_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Avoid excessive repetition of words and phrases to improve readability and professionalism.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{r_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score (higher = less repetition)</span><span>{r_score}%</span>
                </div>"""

    if r_repeated:
        rep_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">The following words are repeated frequently in your resume:</div>"""
        for rw in r_repeated:
            word = rw.get("word", "")
            count = rw.get("count", 0)
            suggestions = rw.get("suggestions", [])
            rep_html += '<div class="repeat-group">'
            rep_html += f'<span class="repeat-word-tag">{count} times: {word}</span>'
            if suggestions:
                rep_html += '<span class="repeat-label">try replacing with</span>'
                for suggestion in suggestions:
                    rep_html += f'<span class="repeat-suggestion">{suggestion}</span>'
            rep_html += '</div>'
        rep_html += '</div>'
    elif r_status == "ok":
        rep_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">Good variety in language and phrasing throughout the resume.</div>
                </div>"""

    rep_html += '</div></div>'
    return rep_html


def _build_spelling_grammar_html(spelling_grammar: Dict[str, Any]) -> str:
    s_score = spelling_grammar.get("score", 0)
    s_status = spelling_grammar.get("status", "ok")
    s_issues = spelling_grammar.get("issues_list", [])
    s_badge = "ok" if s_status == "ok" else "warn"
    s_label = "No issues" if s_status == "ok" else f"{len(s_issues)} issues"

    spell_html = f"""
        <div class="detail-card section-anchor" id="spelling-grammar">
            <div class="detail-head">
                <h3>Spelling &amp; Grammar</h3>
                <span class="badge badge-{s_badge}">{s_label}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">Ensure your resume is free of spelling and grammatical errors for a professional appearance.</p>
                <div class="progress-track dark"><div class="progress-fill dark" style="width:{s_score}%"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                    <span>Score</span><span>{s_score}%</span>
                </div>"""

    if s_issues:
        spell_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">We found the following issues in your resume:</div>"""
        for issue in s_issues:
            label = issue.get("label", "Issue")
            examples = issue.get("examples", [])
            count = issue.get("count", 0)
            spell_html += f'<div class="spell-issue-row"><span class="spell-tag"><span class="spell-tag-label">{count}x</span> {label}</span></div>'
            if examples:
                for ex in examples[:2]:
                    spell_html += f'<div class="issue-item"><span class="issue-x">&#10005;</span><span style="font-family:monospace;font-size:0.85rem;">{_escape_html(ex)}</span></div>'
        spell_html += '</div>'
    elif s_status == "ok":
        spell_html += """
                <div class="issue-card good-card" style="margin-top:14px;">
                    <div class="issue-heading">No significant spelling or grammar errors detected.</div>
                </div>"""

    spell_html += '</div></div>'
    return spell_html


def _build_essential_sections_html(sections_details: Dict[str, Any]) -> str:
    essential_sections_map = [
        ("contact", "Contact", sections_details.get("has_contact", False)),
        ("experience", "Experience", sections_details.get("has_experience", False)),
        ("education", "Education", sections_details.get("has_education", False)),
        ("skills", "Skills", sections_details.get("has_skills", False)),
        ("summary", "Summary/Objective", sections_details.get("has_summary", False)),
    ]
    es_missing = [s for s in essential_sections_map if not s[2]]
    es_badge = "ok" if not es_missing else "warn"
    es_label = "All found" if not es_missing else f"{len(es_missing)} missing"

    es_html = f"""
        <div class="detail-card section-anchor" id="essential-sections">
            <div class="detail-head">
                <h3>Essential Sections</h3>
                <span class="badge badge-{es_badge}">{es_label}</span>
            </div>
            <div class="section-body">"""

    if es_missing:
        es_html += """
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">We've found the following <strong>essential sections</strong> in your resume. However, some are missing:</div>"""
    else:
        es_html += """
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">All essential sections are present in your resume:</div>"""

    for _key, label, present in essential_sections_map:
        icon_cls = "found" if present else "missing"
        icon_char = "&#10003;" if present else "&#10005;"
        es_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon {icon_cls}">{icon_char}</span>
                        <span class="contact-label">{label}</span>
                    </div>"""

    es_html += "</div></div></div>"
    return es_html


def _build_contact_information_html(contact_found: List[Dict[str, Any]], contact_missing: List[Dict[str, Any]]) -> str:
    ci_badge = "ok" if not contact_missing else "warn"
    ci_label = "All found" if not contact_missing else f"{len(contact_missing)} missing"

    contact_html = f"""
        <div class="detail-card section-anchor" id="contact-information">
            <div class="detail-head">
                <h3>Contact Information</h3>
                <span class="badge badge-{ci_badge}">{ci_label}</span>
            </div>
            <div class="section-body">"""

    if contact_found:
        contact_html += """
                <div class="issue-card good-card" style="margin-top:10px;">
                    <div class="issue-heading">We've found the following contact information in your resume:</div>"""
        for item in contact_found:
            label = item.get("label", "")
            value = item.get("value", "")
            contact_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon found">&#10003;</span>
                        <span class="contact-label">{label}:</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value">{_escape_html(value)}</span>
                    </div>"""
        contact_html += "</div>"

    if contact_missing:
        contact_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">Although, you are missing essential contact information:</div>"""
        for item in contact_missing:
            label = item.get("label", "")
            message = item.get("message", "")
            contact_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-label">{label}</span>
                        <span class="contact-sep">&mdash;</span>
                        <span class="contact-value contact-msg">{_escape_html(message)}</span>
                    </div>"""
        contact_html += "</div>"
    elif not contact_found:
        contact_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">No contact information could be extracted from your resume.</div>
                </div>"""

    contact_html += "</div></div>"
    return contact_html


def _build_file_format_size_html(file_format_info: Dict[str, Any]) -> str:
    ff_is_pdf = bool(file_format_info.get("is_pdf", False))
    ff_is_docx = bool(file_format_info.get("is_docx", False))
    ff_is_supported = bool(file_format_info.get("is_supported_format", ff_is_pdf or ff_is_docx))
    ff_size_ok = file_format_info.get("size_ok", True)
    ff_name = file_format_info.get("file_name", "")
    ff_size_kb = file_format_info.get("file_size_kb", 0)
    ff_size_mb = file_format_info.get("file_size_mb", 0)
    ff_all_good = ff_is_supported and ff_size_ok
    ff_badge = "ok" if ff_all_good else "warn"
    ff_badge_txt = "No issues" if ff_all_good else "Issues found"
    ff_ext = ff_name.rsplit(".", 1)[-1].upper() if "." in ff_name else ("DOCX" if ff_is_docx else "PDF")

    ff_html = f"""
        <div class="detail-card section-anchor" id="file-format-size">
            <div class="detail-head">
                <h3>File Format &amp; Size</h3>
                <span class="badge badge-{ff_badge}">{ff_badge_txt}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    When you're uploading your resume on platforms like Indeed, you're likely to meet a file size limit.
                    Ideally, your resume should be less than 2MB in size. Your file type also plays an important role
                    in ATS screening. PDF and DOCX are supported when the document is text-based and machine-readable.
                </p>"""

    if ff_all_good:
        size_str = f"{ff_size_kb:.0f}KB" if ff_size_kb < 1024 else f"{ff_size_mb:.1f}MB"
        ff_html += f"""
                <div class="issue-card good-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Good job!</div>
                    <div class="text-description" style="margin-top:6px;">
                        Your resume file is <strong>{size_str}</strong> and your file type is <strong>{ff_ext}</strong>.
                    </div>
                </div>"""
    else:
        ff_issues_html = ""
        if not ff_is_supported:
            ff_issues_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-value contact-msg">Your file type is <strong>{ff_ext}</strong>. Please use PDF or DOCX for ATS compatibility.</span>
                    </div>"""
        if not ff_size_ok:
            ff_issues_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon missing">&#10005;</span>
                        <span class="contact-value contact-msg">Your file is <strong>{ff_size_mb:.1f}MB</strong>. It should be under 2MB for most platforms.</span>
                    </div>"""
        ff_html += f"""
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">File format or size issues detected:</div>
                    {ff_issues_html}
                </div>"""

    ff_html += "</div></div>"
    return ff_html


def _build_email_address_html(email_check_info: Dict[str, Any]) -> str:
    em_found = email_check_info.get("found", False)
    em_email = email_check_info.get("email", "")
    em_prof = email_check_info.get("is_professional", True)
    em_badge = "ok" if (em_found and em_prof) else "warn"
    em_badge_txt = "No issues" if (em_found and em_prof) else ("Unprofessional" if em_found else "Not found")

    em_html = f"""
        <div class="detail-card section-anchor" id="email-address">
            <div class="detail-head">
                <h3>Email Address</h3>
                <span class="badge badge-{em_badge}">{em_badge_txt}</span>
            </div>
            <div class="section-body">
                <p class="section-body-item text-description">
                    Emails are important in today's world. It's one of the go-to ways for recruiters to get in touch with you,
                    especially if you're applying for a job that's remote and in another country.
                </p>"""

    safe_email = _escape_html(em_email)
    if em_found and em_prof:
        em_html += f"""
                <div class="issue-card good-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Good job!</div>
                    <div class="text-description" style="margin-top:6px;">Your email address seems professional.</div>
                    <div style="margin-top:12px;padding:8px 20px;border-radius:8px;background:rgba(255,255,255,0.08);display:inline-block;font-size:0.95rem;color:var(--text-primary);">
                        {safe_email}
                    </div>
                </div>"""
    elif em_found:
        em_html += f"""
                <div class="issue-card" style="margin-top:14px;text-align:center;">
                    <div class="issue-heading">Your email address may not appear professional:</div>
                    <div style="margin-top:12px;padding:8px 20px;border-radius:8px;background:rgba(255,255,255,0.08);display:inline-block;font-size:0.95rem;color:var(--text-primary);">
                        {safe_email}
                    </div>
                    <div class="text-description" style="margin-top:8px;">Consider using a professional email format (e.g. firstname.lastname@domain.com).</div>
                </div>"""
    else:
        em_html += """
                <div class="issue-card" style="margin-top:14px;">
                    <div class="issue-heading">No email address was found in your resume.</div>
                    <div class="text-description" style="margin-top:6px;">Include a professional email address so recruiters can contact you.</div>
                </div>"""

    em_html += "</div></div>"
    return em_html


def _build_header_links_html(header_links_info: Dict[str, Any]) -> str:
    hl_has = header_links_info.get("has_links", False)
    hl_links = header_links_info.get("links", [])
    hl_full = header_links_info.get("has_full_url", False)
    hl_badge = "ok" if hl_has else "warn"
    hl_badge_txt = "No issues" if hl_has else "Not found"

    hl_html = f"""
        <div class="detail-card section-anchor" id="header-links">
            <div class="detail-head">
                <h3>Header Links</h3>
                <span class="badge badge-{hl_badge}">{hl_badge_txt}</span>
            </div>
            <div class="section-body">"""

    if hl_has and hl_full:
        hl_html += """
                <div class="issue-card good-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading" style="font-size:1.1rem;">Full link detected</div>
                    <div class="text-description" style="margin-top:6px;">
                        Your header includes a complete URL, ensuring proper recognition by ATS systems.
                    </div>
                </div>"""
        if hl_links:
            hl_html += '<div style="margin-top:10px;">'
            for link in hl_links:
                hl_html += f"""
                    <div class="contact-row">
                        <span class="contact-icon found">&#10003;</span>
                        <span class="contact-value">{_escape_html(link)}</span>
                    </div>"""
            hl_html += '</div>'
    elif hl_has:
        hl_html += """
                <div class="issue-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading">Partial link detected</div>
                    <div class="text-description" style="margin-top:6px;">
                        We found link references in your header, but consider using complete URLs (e.g. https://linkedin.com/in/yourname)
                        for better ATS recognition.
                    </div>
                </div>"""
    else:
        hl_html += """
                <div class="issue-card" style="margin-top:10px;">
                    <div class="issue-heading">No links found in your resume header</div>
                    <div class="text-description" style="margin-top:6px;">
                        Include links to your LinkedIn profile, GitHub, or portfolio in your resume header.
                        ATS systems often look for these to verify your online presence.
                    </div>
                </div>"""

    hl_html += "</div></div>"
    return hl_html


def _build_list_card(
    title: str,
    items: List[str],
    section_id: str,
    badge_type: str,
    badge_label: str,
    icon: str,
    empty_msg: str,
) -> str:
    """Build a uniform detail-card HTML string for list-based sections."""
    html = f"""
            <div class="detail-card section-anchor" id="{section_id}">
                <div class="detail-head">
                    <h3>{title}</h3>
                    <span class="badge badge-{badge_type}">{badge_label}</span>
                </div>
                <div class="section-body">"""
    if items:
        html += (
            '<div class="issue-card good-card" style="margin-top:10px;">'
            if badge_type == "ok"
            else '<div class="issue-card" style="margin-top:10px;">'
        )
        for item in items:
            safe_item = _markdown_inline_to_html(item)
            html += f"""
                    <div class="contact-row" style="align-items:flex-start;">
                        <span class="contact-icon {'found' if badge_type == 'ok' else 'missing'}">{icon}</span>
                        <span class="contact-value" style="line-height:1.5;">{safe_item}</span>
                    </div>"""
        html += "</div>"
    else:
        html += f"""
                <div class="issue-card good-card" style="margin-top:10px;text-align:center;">
                    <div class="issue-heading">{empty_msg}</div>
                </div>"""
    html += "</div></div>"
    return html


def _render_download_buttons(name: str, analysis: Dict[str, Any]) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Download Reports", unsafe_allow_html=False)
    col1, col2 = st.columns(2, gap="medium")
    pdf_bytes = b""
    pdf_error = ""
    try:
        pdf_bytes = build_report_pdf_bytes(name, analysis)
    except RuntimeError as exc:
        pdf_error = str(exc)

    with col1:
        st.download_button(
            "\U0001F4C4 Download PDF Report",
            data=pdf_bytes,
            file_name=f"{name}-analysis.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf_main",
            disabled=not bool(pdf_bytes),
        )
    with col2:
        st.download_button(
            "\U0001F9FE Download JSON Export",
            data=json.dumps(analysis, indent=2),
            file_name=f"{name}-analysis.json",
            mime="application/json",
            use_container_width=True,
            key="download_json_main",
        )
    if pdf_error:
        st.caption(pdf_error)



def _build_sidebar_js() -> str:
    """
    Build JavaScript for sidebar interactions + sticky top-offset sync.
    """
    js = """
    <script>
    (function() {
        var win = window.parent;
        var doc = win.document;
        var DESKTOP_MIN = 1100;
        var DEFAULT_TOP = 96;
        var MIN_TOP = 72;
        var MAX_TOP = 220;
        var TOP_GAP = 12;

        if (win.__excelcvSidebarCleanup) {
            try { win.__excelcvSidebarCleanup(); } catch (e) {}
            win.__excelcvSidebarCleanup = null;
        }

        function closeCategoryById(categoryId) {
            var head = doc.getElementById('cat-head-' + categoryId);
            var items = doc.getElementById('cat-items-' + categoryId);
            if (!head || !items) return;
            head.classList.remove('expanded');
            items.classList.remove('expanded');
            items.classList.add('collapsed');
        }

        function closeOtherCategories(activeCategoryId) {
            var expandedHeads = Array.prototype.slice.call(doc.querySelectorAll('.category-head.expanded'));
            for (var i = 0; i < expandedHeads.length; i++) {
                var h = expandedHeads[i];
                if (!h || !h.id || h.id.indexOf('cat-head-') !== 0) continue;
                var cid = h.id.replace('cat-head-', '');
                if (cid === activeCategoryId) continue;
                closeCategoryById(cid);
            }
        }

        function toggleCategory(categoryId) {
            var head = doc.getElementById('cat-head-' + categoryId);
            var items = doc.getElementById('cat-items-' + categoryId);
            if (!head || !items) return;

            if (head.classList.contains('expanded')) {
                closeCategoryById(categoryId);
                return;
            }

            closeOtherCategories(categoryId);
            head.classList.add('expanded');
            items.classList.remove('collapsed');
            items.classList.add('expanded');
        }

        function scrollToSection(sectionId) {
            var el = doc.getElementById(sectionId);
            if (!el) return;
            expandDetailCardForElement(el);

            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            el.style.transition = 'background-color 0.3s ease';
            var origBg = el.style.backgroundColor || '';
            el.style.backgroundColor = 'rgba(16,185,129,0.15)';
            setTimeout(function() {
                el.style.backgroundColor = origBg;
            }, 1200);
        }

        function collapseDetailCard(cardId) {
            var card = doc.getElementById(cardId);
            if (!card) return;
            var head = card.querySelector('.detail-head');
            var body = card.querySelector('.section-body');
            if (!head || !body) return;
            card.classList.remove('expanded');
            card.classList.add('collapsed');
            body.classList.remove('expanded');
            body.classList.add('collapsed');
            head.setAttribute('aria-expanded', 'false');
        }

        function expandDetailCard(cardId) {
            var card = doc.getElementById(cardId);
            if (!card) return;
            var head = card.querySelector('.detail-head');
            var body = card.querySelector('.section-body');
            if (!head || !body) return;
            card.classList.remove('collapsed');
            card.classList.add('expanded');
            body.classList.remove('collapsed');
            body.classList.add('expanded');
            head.setAttribute('aria-expanded', 'true');
        }

        function toggleDetailCard(cardId) {
            var card = doc.getElementById(cardId);
            if (!card) return;
            if (card.classList.contains('expanded')) {
                collapseDetailCard(cardId);
            } else {
                expandDetailCard(cardId);
            }
        }

        function expandDetailCardForElement(el) {
            var card = el.closest('.detail-card');
            if (card && card.id) {
                expandDetailCard(card.id);
            }
        }

        function prepareDetailCards() {
            var cards = Array.prototype.slice.call(doc.querySelectorAll('.detail-card'));
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i];
                if (!card || !card.id) continue;
                var head = card.querySelector('.detail-head');
                var body = card.querySelector('.section-body');
                if (!head || !body) continue;

                if (head.getAttribute('data-collapsible-ready') !== '1') {
                    head.setAttribute('data-collapsible-ready', '1');
                    head.setAttribute('role', 'button');
                    head.setAttribute('tabindex', '0');
                    head.classList.add('detail-head-collapsible');
                    if (!head.querySelector('.detail-chevron')) {
                        var h3 = head.querySelector('h3');
                        if (h3) {
                            var chev = doc.createElement('span');
                            chev.className = 'detail-chevron';
                            chev.innerHTML = '&#9660;';
                            h3.appendChild(chev);
                        }
                    }
                }

                collapseDetailCard(card.id);
            }
        }

        function handleClick(e) {
            var t = e.target;
            if (!t || !t.closest) return;

            var detailHead = t.closest('.detail-card .detail-head');
            if (detailHead) {
                var detailCard = detailHead.closest('.detail-card');
                if (detailCard && detailCard.id) {
                    toggleDetailCard(detailCard.id);
                    e.stopPropagation();
                    e.preventDefault();
                    return;
                }
            }

            var groupHead = t.closest('.report-group-head');
            if (groupHead && groupHead.id && groupHead.id.indexOf('group-head-') === 0) {
                e.stopPropagation();
                e.preventDefault();
                return;
            }

            var head = t.closest('.category-head');
            if (head && head.id && head.id.indexOf('cat-head-') === 0) {
                toggleCategory(head.id.replace('cat-head-', ''));
                e.stopPropagation();
                e.preventDefault();
                return;
            }

            var subitem = t.closest('.subitem');
            if (subitem) {
                var sid = subitem.getAttribute('data-section-id');
                if (sid) {
                    scrollToSection(sid);
                    e.stopPropagation();
                    e.preventDefault();
                    return;
                }
            }

            var issueEl = t.closest('.issues-text');
            if (issueEl) {
                var isid = issueEl.getAttribute('data-section-id');
                if (isid) {
                    scrollToSection(isid);
                    e.stopPropagation();
                    e.preventDefault();
                }
            }
        }

        function handleKeydown(e) {
            var t = e.target;
            if (!t || !t.closest) return;
            var detailHead = t.closest('.detail-card .detail-head');
            if (!detailHead) return;
            var detailCard = detailHead.closest('.detail-card');
            if (!detailCard || !detailCard.id) return;
            if (e.key === 'Enter' || e.key === ' ') {
                toggleDetailCard(detailCard.id);
                e.stopPropagation();
                e.preventDefault();
            }
        }

        function computeStickyTop() {
            var headers = Array.prototype.slice.call(
                doc.querySelectorAll('[data-testid="stHorizontalBlock"]:has(.site-brand)')
            );
            var bestRect = null;

            for (var i = 0; i < headers.length; i++) {
                var h = headers[i];
                if (!h || !h.getBoundingClientRect) continue;
                var r = h.getBoundingClientRect();
                if (!r || r.width < 120 || r.height < 24) continue;
                if (r.bottom < 20 || r.top > 220) continue;
                if (!bestRect || Math.abs(r.top) < Math.abs(bestRect.top)) {
                    bestRect = r;
                }
            }

            if (!bestRect) return DEFAULT_TOP;
            var computed = Math.round(bestRect.bottom + TOP_GAP);
            return Math.min(MAX_TOP, Math.max(MIN_TOP, computed));
        }

        function unpinSidebar() {
            var sidebar = doc.querySelector('.report-sidebar');
            if (!sidebar) return;
            var anchor = sidebar.parentElement;
            if (anchor && anchor.style) {
                anchor.style.position = '';
                anchor.style.minHeight = '';
            }
            // Keep layout controlled by CSS sticky; clear JS overrides only.
            sidebar.style.removeProperty('position');
            sidebar.style.removeProperty('top');
            sidebar.style.removeProperty('bottom');
            sidebar.style.removeProperty('left');
            sidebar.style.removeProperty('right');
            sidebar.style.removeProperty('width');
            sidebar.style.removeProperty('max-height');
            sidebar.style.removeProperty('overflow-y');
            sidebar.style.removeProperty('z-index');
        }

        function pinSidebar(topValue, baseTopValue) {
            var sidebar = doc.querySelector('.report-sidebar');
            if (!sidebar) return;
            var anchor = sidebar.parentElement;
            if (!anchor || !anchor.getBoundingClientRect) return;
            var rect = anchor.getBoundingClientRect();
            if (!rect || rect.width < 140) return;

            var maxHeightTop = Math.max(12, Math.round(baseTopValue || topValue || DEFAULT_TOP));
            sidebar.style.setProperty('position', 'fixed', 'important');
            sidebar.style.setProperty('top', Math.round(topValue) + 'px', 'important');
            sidebar.style.setProperty('left', Math.round(rect.left) + 'px', 'important');
            sidebar.style.setProperty('width', Math.round(rect.width) + 'px', 'important');
            sidebar.style.setProperty('max-height', 'calc(100vh - ' + maxHeightTop + 'px - 12px)', 'important');
            sidebar.style.setProperty('overflow-y', 'auto', 'important');
            sidebar.style.setProperty('z-index', '20', 'important');
        }

        function dockSidebarBottom() {
            // Legacy compatibility helper; sidebar clamping is handled in syncStickyTop().
            unpinSidebar();
        }

        function syncStickyTop() {
            var topValue = DEFAULT_TOP;
            var isDesktop = win.innerWidth >= DESKTOP_MIN;
            if (isDesktop) {
                topValue = computeStickyTop();
            }
            if (doc.documentElement && doc.documentElement.style) {
                doc.documentElement.style.setProperty('--excelcv-report-top', topValue + 'px');
            }
            if (!isDesktop) {
                unpinSidebar();
                return;
            }

            var sidebar = doc.querySelector('.report-sidebar');
            var anchor = sidebar ? sidebar.parentElement : null;
            if (!sidebar || !anchor || !anchor.getBoundingClientRect) {
                unpinSidebar();
                return;
            }

            var rect = anchor.getBoundingClientRect();
            var triggerTop = topValue + 6;
            if (rect.top > triggerTop) {
                unpinSidebar();
                return;
            }

            var sidebarRect = sidebar.getBoundingClientRect();
            var sidebarHeight = Math.max(220, Math.ceil(sidebarRect.height || sidebar.offsetHeight || 0));
            var clampedTop = topValue;
            var footer = doc.querySelector('.site-footer-band');
            if (footer && footer.getBoundingClientRect) {
                var footerRect = footer.getBoundingClientRect();
                var maxAllowedTop = Math.floor(footerRect.top - sidebarHeight - 8);
                clampedTop = Math.min(topValue, maxAllowedTop);
            }

            pinSidebar(clampedTop, topValue);
            return;
        }

        if (win.__sidebarSimpleClickHandler) {
            doc.removeEventListener('click', win.__sidebarSimpleClickHandler, true);
        }
        if (win.__sidebarSimpleKeyHandler) {
            doc.removeEventListener('keydown', win.__sidebarSimpleKeyHandler, true);
        }
        win.__sidebarSimpleClickHandler = handleClick;
        win.__sidebarSimpleKeyHandler = handleKeydown;
        doc.addEventListener('click', handleClick, true);
        doc.addEventListener('keydown', handleKeydown, true);

        function initContent() {
            // Keep all scorecard categories collapsed on first load.
            var heads = Array.prototype.slice.call(doc.querySelectorAll('.category-head'));
            var itemGroups = Array.prototype.slice.call(doc.querySelectorAll('.category-items'));
            for (var i = 0; i < heads.length; i++) {
                heads[i].classList.remove('expanded');
            }
            for (var j = 0; j < itemGroups.length; j++) {
                itemGroups[j].classList.remove('expanded');
                itemGroups[j].classList.add('collapsed');
            }
            prepareDetailCards();
        }

        var initDone = false;
        function runInit() {
            if (!initDone) {
                initContent();
                initDone = true;
            }
            syncStickyTop();
        }

        var onResize = function() {
            clearTimeout(win.__excelcvSidebarResizeTick);
            win.__excelcvSidebarResizeTick = setTimeout(function() {
                syncStickyTop();
            }, 30);
        };

        var onScroll = function() {
            if (win.__excelcvSidebarScrollTick) return;
            win.__excelcvSidebarScrollTick = win.requestAnimationFrame(function() {
                win.__excelcvSidebarScrollTick = null;
                syncStickyTop();
            });
        };

        var observer = null;
        if (doc.body) {
            observer = new MutationObserver(function() {
                clearTimeout(win.__excelcvSidebarInitTimeout);
                win.__excelcvSidebarInitTimeout = setTimeout(runInit, 120);
            });
            observer.observe(doc.body, { childList: true, subtree: true });
        }

        win.addEventListener('resize', onResize, true);
        win.addEventListener('scroll', onScroll, true);

        win.__excelcvSidebarCleanup = function() {
            try { unpinSidebar(); } catch (e) {}
            try { win.removeEventListener('resize', onResize, true); } catch (e) {}
            try { win.removeEventListener('scroll', onScroll, true); } catch (e) {}
            try { doc.removeEventListener('keydown', win.__sidebarSimpleKeyHandler, true); } catch (e) {}
            try { if (observer) observer.disconnect(); } catch (e) {}
            try { if (win.__excelcvSidebarScrollTick) win.cancelAnimationFrame(win.__excelcvSidebarScrollTick); } catch (e) {}
            win.__excelcvSidebarScrollTick = null;
        };

        setTimeout(runInit, 40);
        setTimeout(runInit, 220);
        setTimeout(runInit, 700);
    })();
    </script>
    """
    return js

def _build_group_card(title: str, group_id: str, issues_found: int, body_html: str) -> str:
    """Wrap detail cards in a report section block."""
    issue_text = "No issues found" if issues_found <= 0 else f"{issues_found} issues found"
    normalized_body = "\n".join(
        line.strip()
        for line in str(body_html).splitlines()
        if line.strip()
    )
    return (
        f'<div class="report-group section-anchor" id="{group_id}">'
        f'<div class="report-group-head"><h3>{title}</h3><span class="report-group-pill">{issue_text}</span></div>'
        f'<div class="report-group-body">{normalized_body}</div>'
        "</div>"
    )


def render_report_page(analysis: Dict[str, Any], name: str = "CV") -> None:
    """Render the two-column report view inspired by the HTML mock."""
    score = analysis.get("match_score", 0)
    subs = analysis.get("subscores", {}) or {}
    issues = issue_count(analysis)

    # Extract content metrics
    content_metrics = analysis.get("content_metrics", {}) or {}
    ats_parse_rate = content_metrics.get("ats_parse_rate", 0)
    quant_impact = content_metrics.get("quantifying_impact", {}) or {}
    repetition = content_metrics.get("repetition", {}) or {}
    spelling_grammar = content_metrics.get("spelling_grammar", {}) or {}
    score_breakdown = analysis.get("score_breakdown", {}) or {}

    # Calculate Content category score as average of content metrics
    content_items = [
        ats_parse_rate,
        quant_impact.get("score", 0),
        repetition.get("score", 0),
        spelling_grammar.get("score", 0),
    ]
    content_score = int(sum(content_items) / len(content_items)) if content_items else subs.get("ats_readiness", score)

    # Build Content category items: (label, status, score)
    content_items_list = [
        ("Explainable Scoring", "ok", score),
        ("ATS Parse Rate", "ok" if ats_parse_rate >= 80 else "warn" if ats_parse_rate >= 60 else "error", ats_parse_rate),
        ("Quantifying Impact", quant_impact.get("status", "ok"), quant_impact.get("score", 0)),
        ("Repetition", repetition.get("status", "ok"), repetition.get("score", 0)),
        ("Spelling & Grammar", spelling_grammar.get("status", "ok"), spelling_grammar.get("score", 0)),
    ]

    # Extract other category metrics
    sections_metrics = analysis.get("sections_metrics", {}) or {}
    sections_score = sections_metrics.get("score", subs.get("experience_alignment", score)) or 0
    sections_details = sections_metrics.get("details", {}) or {}

    # Extract contact info
    contact_info = analysis.get("contact_info", {}) or {}
    contact_found = contact_info.get("found", [])
    contact_missing = contact_info.get("missing", [])

    # Build Sections category items
    sections_items_list = []
    missing_sections = sections_details.get("missing_sections", [])
    if missing_sections:
        sections_items_list.append(("Essential Sections", "error", len(missing_sections)))
    else:
        sections_items_list.append(("Essential Sections", "ok", None))

    if contact_missing:
        sections_items_list.append(("Contact Information", "error", len(contact_missing)))
    else:
        sections_items_list.append(("Contact Information", "ok", None))

    ats_essentials_metrics = analysis.get("ats_essentials_metrics", {}) or {}
    ats_essentials_score = ats_essentials_metrics.get("score", subs.get("ats_readiness", score)) or 0
    ats_essentials_details = ats_essentials_metrics.get("details", {}) or {}

    # Extract ATS sub-section details
    file_format_info = ats_essentials_details.get("file_format", {}) or {}
    email_check_info = ats_essentials_details.get("email_check", {}) or {}
    header_links_info = ats_essentials_details.get("header_links", {}) or {}

    # Build ATS Essentials category items
    ats_items_list = []
    ats_issues = ats_essentials_details.get("issues", [])

    ff_ok = file_format_info.get(
        "is_supported_format",
        file_format_info.get("is_pdf", False) or file_format_info.get("is_docx", False),
    ) and file_format_info.get("size_ok", True)
    ats_items_list.append(("File Format & Size", "ok" if ff_ok else "warn", None if ff_ok else 1))

    if ats_issues:
        ats_items_list.append(("Design", "warn", len(ats_issues)))

    email_found = email_check_info.get("found", False)
    email_prof = email_check_info.get("is_professional", True)
    if email_found and email_prof:
        ats_items_list.append(("Email Address", "ok", None))
    elif email_found:
        ats_items_list.append(("Email Address", "warn", 1))
    else:
        ats_items_list.append(("Email Address", "error", 1))

    has_links = header_links_info.get("has_links", False)
    ats_items_list.append(("Header Links", "ok" if has_links else "warn", None if has_links else 1))

    # Build Insights category items
    strengths_list = analysis.get("strengths", [])
    missing_skills_list = analysis.get("missing_skills", [])
    missing_keywords_list = analysis.get("missing_keywords", [])
    suggestions_list = analysis.get("suggestions", [])
    jd_skill_matrix = analysis.get("jd_skill_matrix", []) or []
    rewrite_recommendations = analysis.get("rewrite_recommendations", []) or []
    recruiter_snapshot = analysis.get("recruiter_snapshot", {}) or {}
    priority_action_plan = analysis.get("priority_action_plan", []) or []
    interview_prep = analysis.get("interview_prep", []) or []
    learning_roadmap = analysis.get("learning_roadmap", []) or []
    portfolio_checklist = analysis.get("portfolio_checklist", {}) or {}
    portfolio_missing = portfolio_checklist.get("missing", []) or []

    matrix_missing_count = sum(1 for row in jd_skill_matrix if row.get("status") == "Missing")
    matrix_partial_count = sum(1 for row in jd_skill_matrix if row.get("status") == "Partial")
    matrix_issue_count = matrix_missing_count + matrix_partial_count

    insights_items_list = [
        ("Strengths", "ok" if strengths_list else "warn", len(strengths_list) if strengths_list else None),
        ("Missing Skills", "warn" if missing_skills_list else "ok", len(missing_skills_list) if missing_skills_list else None),
        ("Missing Keywords", "warn" if missing_keywords_list else "ok", len(missing_keywords_list) if missing_keywords_list else None),
        ("Suggestions", "ok" if suggestions_list else "warn", len(suggestions_list) if suggestions_list else None),
        ("Recruiter Snapshot", "ok", None),
        (
            "Priority Action Plan",
            "warn" if priority_action_plan else "ok",
            len(priority_action_plan) if priority_action_plan else None,
        ),
        (
            "Interview Prep",
            "ok" if interview_prep else "lock",
            len(interview_prep) if interview_prep else None,
        ),
        (
            "Learning Roadmap",
            "warn" if learning_roadmap else "ok",
            len(learning_roadmap) if learning_roadmap else None,
        ),
        (
            "Portfolio Checklist",
            "warn" if portfolio_missing else "ok",
            len(portfolio_missing) if portfolio_missing else None,
        ),
        (
            "JD Skill Matrix",
            "lock" if not jd_skill_matrix else ("warn" if matrix_issue_count > 0 else "ok"),
            None if not jd_skill_matrix else (matrix_issue_count if matrix_issue_count > 0 else 0),
        ),
        (
            "Rewrite Assistant",
            "warn" if rewrite_recommendations else "ok",
            len(rewrite_recommendations) if rewrite_recommendations else None,
        ),
    ]

    total_insights = len(strengths_list) + len(missing_skills_list) + len(missing_keywords_list)
    insights_score = int((len(strengths_list) / total_insights) * 100) if total_insights else 80

    categories = [
        ("Content", content_score, content_items_list),
        ("Sections", sections_score, sections_items_list),
        ("ATS Essentials", ats_essentials_score, ats_items_list),
        ("Insights", insights_score, insights_items_list),
    ]

    # Two-column layout: scoring sidebar + main content
    sidebar, main = st.columns([1, 1.6], gap="large")

    with sidebar:
        sidebar_html = _build_sidebar_html(score, issues, categories)
        st.markdown(sidebar_html, unsafe_allow_html=True)
        components.html(_build_sidebar_js(), height=0)

    with main:
        strengths_html = _build_list_card(
            "Strengths",
            strengths_list,
            "strengths",
            "ok",
            f"{len(strengths_list)} found" if strengths_list else "None",
            "&#10003;",
            "No specific strengths identified yet.",
        )

        missing_skills_html = _build_list_card(
            "Missing Skills",
            missing_skills_list,
            "missing-skills",
            "warn" if missing_skills_list else "ok",
            f"{len(missing_skills_list)} missing" if missing_skills_list else "All covered",
            "&#10005;",
            "No missing skills detected - great job!",
        )

        missing_kw_html = _build_list_card(
            "Missing Keywords (ATS)",
            missing_keywords_list,
            "missing-keywords",
            "warn" if missing_keywords_list else "ok",
            f"{len(missing_keywords_list)} missing" if missing_keywords_list else "All covered",
            "&#10005;",
            "No missing ATS keywords detected - your resume is well-optimized!",
        )

        suggestions_html = _build_list_card(
            "Suggestions",
            suggestions_list,
            "suggestions",
            "ok",
            f"{len(suggestions_list)} tips" if suggestions_list else "None",
            "Tip",
            "No additional suggestions at this time.",
        )

        content_issue_count = 0
        if ats_parse_rate < 80:
            content_issue_count += 1
        if quant_impact.get("status", "ok") != "ok":
            content_issue_count += max(1, len(quant_impact.get("non_quantified_lines", [])))
        if repetition.get("status", "ok") != "ok":
            content_issue_count += max(1, len(repetition.get("repeated_words", [])))
        if spelling_grammar.get("status", "ok") != "ok":
            content_issue_count += max(1, len(spelling_grammar.get("issues_list", [])))

        sections_issue_count = len(missing_sections) + len(contact_missing)

        ats_issue_count = 0
        if not ff_ok:
            ats_issue_count += 1
        ats_issue_count += len(ats_issues)
        if not (email_found and email_prof):
            ats_issue_count += 1
        if not has_links:
            ats_issue_count += 1

        insights_issue_count = (
            len(missing_skills_list)
            + len(missing_keywords_list)
            + matrix_issue_count
            + len(rewrite_recommendations)
            + len(priority_action_plan)
            + len(learning_roadmap)
            + len(portfolio_missing)
        )

        content_group_html = _build_group_card(
            "Content",
            "group-content",
            content_issue_count,
            "".join(
                [
                    _build_explainable_scoring_html(score_breakdown),
                    _build_ats_parse_rate_html(content_metrics.get("ats_parse_rate", 0)),
                    _build_quantifying_impact_html(quant_impact),
                    _build_repetition_html(repetition),
                    _build_spelling_grammar_html(spelling_grammar),
                ]
            ),
        )
        sections_group_html = _build_group_card(
            "Sections",
            "group-sections",
            sections_issue_count,
            "".join(
                [
                    _build_essential_sections_html(sections_details),
                    _build_contact_information_html(contact_found, contact_missing),
                ]
            ),
        )
        ats_group_html = _build_group_card(
            "ATS Essentials",
            "group-ats-essentials",
            ats_issue_count,
            "".join(
                [
                    _build_file_format_size_html(file_format_info),
                    _build_design_html(ats_issues),
                    _build_email_address_html(email_check_info),
                    _build_header_links_html(header_links_info),
                ]
            ),
        )
        insights_group_html = _build_group_card(
            "Insights",
            "group-insights",
            insights_issue_count,
            "".join(
                [
                    _build_recruiter_snapshot_html(recruiter_snapshot),
                    _build_priority_action_plan_html(priority_action_plan),
                    _build_interview_prep_html(interview_prep),
                    _build_learning_roadmap_html(learning_roadmap),
                    _build_list_card(
                        "Portfolio Checklist",
                        portfolio_missing,
                        "portfolio-checklist",
                        "warn" if portfolio_missing else "ok",
                        f"{len(portfolio_missing)} pending" if portfolio_missing else "Ready",
                        "&#10005;" if portfolio_missing else "&#10003;",
                        "Portfolio checklist is complete for current review.",
                    ),
                    _build_skill_matrix_html(jd_skill_matrix),
                    _build_rewrite_assistant_html(rewrite_recommendations),
                    strengths_html,
                    missing_skills_html,
                    missing_kw_html,
                    suggestions_html,
                ]
            ),
        )

        report_main_html = (
            '<div class="report-main">'
            f'<div class="report-group-wrap">{content_group_html}</div>'
            f'<div class="report-group-wrap">{sections_group_html}</div>'
            f'<div class="report-group-wrap">{ats_group_html}</div>'
            f'<div class="report-group-wrap">{insights_group_html}</div>'
            '</div>'
        )
        st.markdown(report_main_html, unsafe_allow_html=True)

        _render_download_buttons(name, analysis)

import html as _html

from src.evaluation import build_evaluation_record, summarize_evaluation
from src.ui.app_utils import _clear_analysis_state, _save_report_snapshot

def render_evaluation_toolkit(analysis: Dict[str, Any], resume_name: str) -> None:
    """Render benchmark/evaluation controls for model-vs-human validation."""
    st.markdown("### Evaluation Toolkit")
    st.caption(
        "Add human-review scores to validate model quality (MAE, RMSE, correlation) for your final project."
    )

    with st.form("evaluation_form", clear_on_submit=True):
        human_score = st.number_input(
            "Human reviewer score (0-100)",
            min_value=0,
            max_value=100,
            value=75,
            step=1,
        )
        notes = st.text_input("Reviewer notes (optional)", placeholder="Example: strong projects, weak impact metrics")
        add_record = st.form_submit_button("Add benchmark record")

    if add_record:
        record = build_evaluation_record(
            resume_name=resume_name,
            model_score=int(analysis.get("match_score", 0)),
            human_score=int(human_score),
            notes=notes,
        )
        records = st.session_state.setdefault("evaluation_records", [])
        records.append(record)
        st.success("Benchmark record added.")

    records = st.session_state.get("evaluation_records", [])
    summary = summarize_evaluation(records)
    if summary.get("count", 0) > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", summary.get("count", 0))
        c2.metric("MAE", summary.get("mae", "-"))
        c3.metric("RMSE", summary.get("rmse", "-"))
        corr = summary.get("correlation")
        c4.metric("Correlation", "-" if corr is None else corr)

        st.dataframe(records, use_container_width=True, hide_index=True)
        st.download_button(
            "Download benchmark JSON",
            data=json.dumps(records, indent=2),
            file_name="excelcv-benchmark.json",
            mime="application/json",
            use_container_width=True,
            key="download_benchmark_json",
        )


def render_report_view() -> None:
    """Results page based on stored analysis."""
    analysis = st.session_state.get("analysis")
    name = st.session_state.get("cv_name", "CV")
    safe_name = _html.escape(str(name), quote=True)

    if not analysis:
        st.info("No analysis found. Upload a resume to get started.")
        st.session_state["page"] = "home"
        st.query_params["page"] = "home"
        if "rid" in st.query_params:
            del st.query_params["rid"]
        return

    # Keep URL snapshot up to date so browser refresh preserves report page.
    current_sid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
    persisted_sid = _save_report_snapshot(str(current_sid) if current_sid else None)
    st.session_state["report_snapshot_id"] = persisted_sid
    st.query_params["page"] = "report"
    st.query_params["rid"] = persisted_sid

    # Marker for CSS/JS: center theme + Upload buttons with PDF section
    st.markdown('<div id="report-pdf-row-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
    top_left, top_right = st.columns([1.72, 0.88], gap="small")
    with top_left:
        st.markdown(
            f"""
            <div class="report-topline report-fileline">
                <span class="report-mode-label">Resume report - Standard scoring</span>
                <div class="report-file-row">
                    <h2 class="report-file-title">{safe_name}</h2>
                    <div class="score-pill">{analysis.get("match_score", 0)} / 100</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.markdown('<div id="report-top-actions-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Upload another resume", use_container_width=True, help="Upload a new resume"):
            _clear_analysis_state(clear_comparison=True)
            st.session_state["page"] = "upload-cv"
            st.query_params["page"] = "upload-cv"
            if "rid" in st.query_params:
                del st.query_params["rid"]
            st.rerun()

    render_report_page(analysis, name=name)

    # Keep post-report tools aligned with the right report lane so the sticky
    # left score sidebar behavior remains unchanged.
    toolkit_spacer, toolkit_main = st.columns([1, 1.6], gap="large")
    with toolkit_main:
        render_evaluation_toolkit(analysis, str(name))


if __name__ == "__main__":
    main()
