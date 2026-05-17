"""Dedicated Compare CV results page (homepage-style two-column hero + table)."""

import csv
import html
from io import StringIO
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.ui.app_utils import (
    _build_page_href,
    _clear_comparison_run_artifacts,
    _save_report_snapshot_from_data,
)


def _autosave_comparison(
    rows: list[dict[str, Any]],
    job_description: str,
    errors: list[str],
    warnings: list[str],
) -> str | None:
    """Persist a comparison run to the DB for the logged-in user. Silent on failure.

    Returns the new comparison's id on success, or None if the user is a guest
    or persistence failed. Called immediately after a successful comparison run
    so users can revisit the same ranked output without re-uploading files.
    """
    from src.auth_utils import get_session_user
    user = get_session_user()
    if not user or not rows:
        return None
    try:
        from src.database import Comparison, get_db
        top_row = rows[0] if rows else {}
        top_score = float(top_row.get("Final Score", 0) or 0)
        top_name = str(top_row.get("Resume", "") or "")
        db = get_db()
        try:
            record = Comparison(
                user_id=user["id"],
                job_description=job_description or "",
                rows=rows,
                errors=list(errors or []),
                warnings=list(warnings or []),
                resume_count=len(rows),
                top_score=top_score,
                top_resume_name=top_name,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return str(record.id)
        finally:
            db.close()
    except Exception:
        return None


def _load_saved_comparison_into_session(comparison_id: str) -> bool:
    """Hydrate session_state from a saved comparison record. Returns True on success."""
    from src.auth_utils import get_session_user
    user = get_session_user()
    if not user:
        return False
    try:
        from src.database import Comparison, get_db
        db = get_db()
        try:
            record = (
                db.query(Comparison)
                .filter(Comparison.id == comparison_id, Comparison.user_id == user["id"])
                .first()
            )
            if not record:
                return False
            st.session_state["comparison_results"] = list(record.rows or [])
            st.session_state["comparison_errors"] = list(record.errors or [])
            st.session_state["comparison_warnings"] = list(record.warnings or [])
            st.session_state["comparison_attempted"] = True
            st.session_state["compare_jd"] = record.job_description or ""
            # No signature stored — treat as "fresh load" so the form's stale-
            # detection won't immediately wipe it on first nav back to the form.
            st.session_state.pop("comparison_signature", None)
            st.session_state["scroll_compare_report_to_top"] = True
            return True
        finally:
            db.close()
    except Exception:
        return False


def _scroll_to_top_once() -> None:
    """Scroll viewport to (0,0) when arriving fresh on the report page.

    Triggered by ``scroll_compare_report_to_top`` flag set in upload.py right
    before navigating in. Pop-on-read so subsequent reruns (expander toggles,
    CSV download, etc.) don't yank the user's scroll position back to the top.
    """
    if not st.session_state.pop("scroll_compare_report_to_top", False):
        return
    components.html(
        """<script>
(function() {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;
    function go() {
        try { w.scrollTo({ top: 0, left: 0, behavior: "instant" }); }
        catch (_e) { try { w.scrollTo(0, 0); } catch (_e2) {} }
        var main = doc.querySelector('[data-testid="stAppViewContainer"]');
        if (main) {
            try { main.scrollTo({ top: 0, left: 0, behavior: "instant" }); }
            catch (_e3) { try { main.scrollTop = 0; } catch (_e4) {} }
        }
    }
    // Retry across a few frames — Streamlit can still be mounting content
    // when this fires, and scrolling before the page is full has no effect.
    go();
    [60, 180, 400].forEach(function(ms) { setTimeout(go, ms); });
})();
</script>""",
        height=0,
    )


def _comparison_rows_to_csv(rows: list[dict[str, object]], ordered_columns: list[str]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=ordered_columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in ordered_columns})
    return buffer.getvalue()


def _back_to_form_href() -> str:
    return _build_page_href("compare-cv")


def _build_top_match_card_html(best: dict[str, object]) -> str:
    """Winner card markup (mirrors the homepage ATS Resume Report visual position)."""
    best_score = max(0, min(100, int(best.get("Final Score", 0) or 0)))
    raw_missing = str(best.get("Top Missing Skills", "") or "").strip()
    if raw_missing and raw_missing.lower() != "none":
        missing_chips_html = "".join(
            f'<span class="compare-top-card__chip">{html.escape(skill.strip())}</span>'
            for skill in raw_missing.split(",")
            if skill.strip()
        )
        skills_label = "Top missing skills:"
    else:
        missing_chips_html = (
            '<span class="compare-top-card__chip compare-top-card__chip--ok">No major gaps</span>'
        )
        skills_label = "Skill match:"
    rank = int(best.get("Rank", 1) or 1)
    name = html.escape(str(best.get("Resume", "")))
    jd = int(best.get("JD Alignment", 0) or 0)
    ats = int(best.get("ATS Parse", 0) or 0)
    sections = int(best.get("Sections", 0) or 0)
    issues = int(best.get("Issues", 0) or 0)
    return (
        '<div class="compare-top-card compare-top-card--hero">'
        f'<span class="compare-top-card__tag">&#9733; Top Match &middot; Rank #{rank}</span>'
        '<div class="compare-top-card__head">'
        f'<h3 class="compare-top-card__name">{name}</h3>'
        '<div class="compare-top-card__score">'
        f'<span class="compare-top-card__score-value">{best_score}</span>'
        '<span class="compare-top-card__score-total">/100</span>'
        '</div>'
        '</div>'
        '<div class="compare-top-card__bar">'
        f'<div class="compare-top-card__bar-fill" style="width: {best_score}%;"></div>'
        '</div>'
        '<div class="compare-top-card__metrics">'
        f'<span class="compare-top-card__metric">JD Alignment <strong>{jd}</strong></span>'
        f'<span class="compare-top-card__metric">ATS Parse <strong>{ats}</strong></span>'
        f'<span class="compare-top-card__metric">Sections <strong>{sections}</strong></span>'
        f'<span class="compare-top-card__metric">Issues <strong>{issues}</strong></span>'
        '</div>'
        '<div class="compare-top-card__skills">'
        f'<span class="compare-top-card__skills-label">{skills_label}</span>'
        f'{missing_chips_html}'
        '</div>'
        '</div>'
    )


def _render_resume_drilldowns(rows: list[dict[str, Any]]) -> None:
    """Expandable per-resume detail panel sourced from the stashed analysis dict.

    The runner stores the full Gemini analysis under each row's ``_analysis``
    key so we can show "why this score" without re-running the model. Falls
    back to row metrics when no stashed analysis is present (e.g. results
    produced by an older session before drill-down was added).
    """
    if not rows:
        return
    st.markdown('<div class="compare-drilldown-title">Per-resume details</div>', unsafe_allow_html=True)
    for row in rows:
        rank = int(row.get("Rank", 0) or 0)
        name = str(row.get("Resume", ""))
        final_score = int(row.get("Final Score", 0) or 0)
        with st.expander(f"#{rank}  {name}  —  {final_score}/100", expanded=False):
            analysis = row.get("_analysis") if isinstance(row, dict) else None
            metric_cols = st.columns(4)
            metric_cols[0].metric("JD Alignment", int(row.get("JD Alignment", 0) or 0))
            metric_cols[1].metric("ATS Parse", int(row.get("ATS Parse", 0) or 0))
            metric_cols[2].metric("Sections", int(row.get("Sections", 0) or 0))
            metric_cols[3].metric("Issues", int(row.get("Issues", 0) or 0))

            if not isinstance(analysis, dict):
                st.caption(
                    "Full analysis not available for this row (older session). "
                    "Re-run the comparison to see detailed reasoning."
                )
                continue

            summary = str(analysis.get("summary", "")).strip()
            if summary:
                st.markdown(f"**Summary** — {html.escape(summary)}")

            missing_skills = analysis.get("missing_skills") or []
            if isinstance(missing_skills, list) and missing_skills:
                chips = " ".join(
                    f'<span class="compare-top-card__chip">{html.escape(str(s))}</span>'
                    for s in missing_skills[:8]
                    if str(s).strip()
                )
                st.markdown(
                    f'<div class="compare-top-card__skills"><span class="compare-top-card__skills-label">Top missing skills:</span>{chips}</div>',
                    unsafe_allow_html=True,
                )

            suggestions = [str(s).strip() for s in (analysis.get("suggestions") or []) if str(s).strip()]
            if suggestions:
                st.markdown("**Suggestions**")
                for tip in suggestions[:6]:
                    st.markdown(f"- {tip}")

            missing_keywords = [str(k).strip() for k in (analysis.get("missing_keywords") or []) if str(k).strip()]
            if missing_keywords:
                st.markdown("**Missing keywords**: " + ", ".join(missing_keywords[:12]))

            # "Open as full report" — saves a report-page snapshot from the
            # stashed analysis dict and navigates to the single-CV report view.
            # Lets the user dig into the full scoring breakdown for any
            # compared resume without re-uploading and re-analyzing.
            with st.container(key=f"compare_open_report_box_{rank}"):
                if st.button(
                    "Open as full report  &rarr;",
                    key=f"compare_open_report_{rank}",
                    type="primary",
                    width="content",
                ):
                    jd = str(st.session_state.get("compare_jd", "") or "")
                    snapshot_id = _save_report_snapshot_from_data(
                        analysis=analysis,
                        cv_name=name,
                        job_description=jd,
                    )
                    st.session_state["report_snapshot_id"] = snapshot_id
                    st.session_state["page"] = "report"
                    try:
                        st.query_params["page"] = "report"
                        st.query_params["rid"] = snapshot_id
                    except Exception:
                        pass
                    st.rerun()


def _render_empty_state(attempted: bool = False, error_count: int = 0) -> None:
    """Render the no-results empty state.

    When ``attempted`` is True, the copy reflects that a comparison ran but
    produced no ranked rows (every file failed) — pointing the user at the
    per-file error list below. Otherwise it reads as a first-visit prompt.
    """
    if attempted:
        icon = "&#9888;&#65039;"  # ⚠️
        title = "Comparison didn't produce ranked results"
        if error_count:
            detail = (
                f"None of the {error_count} uploaded resume{'s' if error_count != 1 else ''} "
                "could be analyzed. See the details below to find out why "
                "(common causes: API rate limit, unreadable PDF, or empty file)."
            )
        else:
            detail = (
                "The comparison ran but no resumes returned analyzable results. "
                "Try again with different files or wait a moment before retrying."
            )
        cta_label = "Retry comparison &rarr;"
    else:
        icon = "&#128202;"  # 📊
        title = "No comparison yet"
        detail = (
            "Upload 2&ndash;5 resumes against a single job description to see ranked, "
            "side-by-side comparison results here."
        )
        cta_label = "Start a comparison &rarr;"
    st.markdown(
        f"""
        <div class="compare-report-empty">
            <div class="compare-report-empty__icon">{icon}</div>
            <h2 class="compare-report-empty__title">{title}</h2>
            <p class="compare-report-empty__copy">{detail}</p>
            <a href="{_back_to_form_href()}" target="_self" class="guest-auth-cta">
                {cta_label}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_tier_class(score: int) -> str:
    """Return the CSS modifier class for a 0-100 score (matches single-report colors)."""
    if score >= 80:
        return "score-good"
    if score >= 60:
        return "score-medium"
    return "score-low"


def _issue_tier_class(issues: int) -> str:
    """Inverse of score tier — fewer issues is better."""
    if issues <= 5:
        return "issue-good"
    if issues <= 15:
        return "issue-medium"
    return "issue-high"


def _render_jd_context_expander() -> None:
    """Collapsed JD reminder so users don't have to navigate back to recall context."""
    jd = str(st.session_state.get("compare_jd", "") or "").strip()
    if not jd:
        return
    preview = jd if len(jd) <= 140 else jd[:139].rstrip() + "…"
    label = f"Job description used  ·  {preview}"
    with st.expander(label, expanded=False):
        st.markdown(jd)


# (label, sort_key, descending) — descending=True for scores (high is good),
# False for issues/names (low/A-Z is "first"). Default is "Final Score (high → low)"
# which matches the ranking the runner originally applied.
_SORT_OPTIONS: list[tuple[str, str, bool]] = [
    ("Final Score (high → low)", "Final Score", True),
    ("Final Score (low → high)", "Final Score", False),
    ("JD Alignment (high → low)", "JD Alignment", True),
    ("ATS Parse (high → low)", "ATS Parse", True),
    ("Sections (high → low)", "Sections", True),
    ("Issues (low → high)", "Issues", False),
    ("Issues (high → low)", "Issues", True),
    ("Resume name (A → Z)", "Resume", False),
]


def _apply_sort(rows: list[dict[str, Any]], sort_label: str) -> list[dict[str, Any]]:
    """Return a re-ordered copy of ``rows`` based on the selected sort label.

    Rank numbers are re-assigned post-sort so the table's #1 always matches
    the user's current sort criterion (e.g. sorting by Issues low→high makes
    the cleanest resume #1 even if its Final Score isn't the highest).
    """
    spec = next(
        ((label, key, desc) for label, key, desc in _SORT_OPTIONS if label == sort_label),
        _SORT_OPTIONS[0],
    )
    _label, key, desc = spec
    if key == "Resume":
        sorted_rows = sorted(rows, key=lambda r: str(r.get("Resume", "")).lower(), reverse=desc)
    else:
        sorted_rows = sorted(rows, key=lambda r: int(r.get(key, 0) or 0), reverse=desc)
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(sorted_rows, start=1):
        copy = dict(row)
        copy["Rank"] = idx
        out.append(copy)
    return out


@st.cache_data(show_spinner=False, max_entries=20)
def _build_comparison_pdf_bytes(
    rows: list[dict[str, Any]],
    job_description: str,
    avg_score: float,
    errors: list[str],
    warnings: list[str],
) -> bytes:
    """Cache the rendered PDF so re-runs (sort changes, expander toggles)
    don't re-invoke ReportLab. Cache key is the full args tuple — different
    sort = different rows order = fresh PDF, which is what we want."""
    from src.services.comparison_pdf import generate_comparison_pdf
    return generate_comparison_pdf(
        rows=rows,
        job_description=job_description,
        avg_score=avg_score,
        errors=errors,
        warnings=warnings,
    )


def _render_sort_selector(default_label: str = "Final Score (high → low)") -> str:
    """Render the sort selector + return the chosen label. Persisted per-session.

    Stacked layout (label above selectbox) so it stays readable inside a
    half-width column on the two-column primary section. Streamlit forbids
    nesting columns more than one level deep, so a flat layout here also
    keeps us safe inside a parent column.
    """
    with st.container(key="compare_sort_row"):
        st.markdown(
            '<div class="compare-sort-label">Sort by</div>',
            unsafe_allow_html=True,
        )
        return st.selectbox(
            "Sort the comparison table by",
            options=[label for label, _k, _d in _SORT_OPTIONS],
            index=0,
            key="compare_report_sort_choice",
            label_visibility="collapsed",
        )


def _render_comparison_table_html(
    rows: list[dict[str, Any]],
    top_match_name: str = "",
) -> None:
    """Custom HTML table with winner-row highlight and color-coded score cells.

    Replaces ``st.dataframe`` for two reasons:
      1. ``st.dataframe`` can't tint individual rows or color cells based on
         value bands without pulling in pandas Styler with limited Streamlit
         support.
      2. Hand-rolled HTML lets the table inherit ``var(--*)`` theme variables
         so light/dark mode and color tokens stay consistent.

    "Top Missing Skills" is intentionally dropped from this table — it was
    truncating mid-word and the same content already lives in the top-match
    card (for #1) and the drill-down expanders (for every row).

    ``top_match_name`` decouples the ★ marker from the user's chosen sort
    order. The star always belongs to the actual top match (the resume the
    Top Match card on the right is showing), so if the user re-sorts the
    table by e.g. "Issues high → low", the true top match keeps its star
    even if it's no longer at the top row of the table.
    """
    columns = [
        ("Rank", "compare-th compare-th--rank"),
        ("Resume", "compare-th compare-th--name"),
        ("Final", "compare-th compare-th--num"),
        ("JD Align", "compare-th compare-th--num"),
        ("ATS Parse", "compare-th compare-th--num"),
        ("Sections", "compare-th compare-th--num"),
        ("Issues", "compare-th compare-th--num"),
    ]
    head = "".join(f'<th class="{cls}">{html.escape(label)}</th>' for label, cls in columns)

    body_rows: list[str] = []
    for row in rows:
        rank = int(row.get("Rank", 0) or 0)
        row_name = str(row.get("Resume", "") or "")
        # is_winner is now identity-based (matches the true top match), not
        # position-based (whoever Streamlit's current sort put at row 1).
        is_winner = bool(top_match_name) and row_name == top_match_name
        row_cls = "compare-row compare-row--winner" if is_winner else "compare-row"
        name = html.escape(row_name)
        if is_winner:
            rank_cell = f'<td class="compare-td compare-td--rank"><span class="compare-winner-pill">&#9733; {rank}</span></td>'
        else:
            rank_cell = f'<td class="compare-td compare-td--rank">{rank}</td>'

        score_cells = ""
        for key in ("Final Score", "JD Alignment", "ATS Parse", "Sections"):
            val = int(row.get(key, 0) or 0)
            tier = _score_tier_class(val)
            # Inline meter: a fixed-width track with a tier-colored fill +
            # the numeric value to the right. ``currentColor`` on the fill
            # picks up the tier class color so green/amber/red is automatic.
            score_cells += (
                f'<td class="compare-td compare-td--num compare-td--{tier}">'
                f'<div class="compare-meter">'
                f'<div class="compare-meter__track">'
                f'<div class="compare-meter__fill" style="width:{val}%;"></div>'
                f'</div>'
                f'<span class="compare-meter__val">{val}</span>'
                f'</div>'
                f'</td>'
            )

        issues = int(row.get("Issues", 0) or 0)
        issue_tier = _issue_tier_class(issues)
        issues_cell = (
            f'<td class="compare-td compare-td--num compare-td--{issue_tier}">{issues}</td>'
        )

        body_rows.append(
            f'<tr class="{row_cls}">{rank_cell}'
            f'<td class="compare-td compare-td--name" title="{name}">{name}</td>'
            f"{score_cells}{issues_cell}</tr>"
        )

    st.markdown(
        '<div class="compare-table-wrap">'
        f'<table class="compare-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_compare_report_page() -> None:
    """Render the dedicated comparison results page."""
    _scroll_to_top_once()
    # Set "return-to-compare" hints so any subsequent home render (typically
    # the user pressing the browser back button) lands on the compare section
    # with the right nav highlight, instead of dumping the user at the top of
    # the Analyze CV upload form. Cleared by the Analyze CV nav action in
    # main() so an explicit nav click still respects the user's intent.
    st.session_state["scroll_to_compare_anchor"] = True
    st.session_state["home_nav_focus_compare"] = True
    comparison_rows = list(st.session_state.get("comparison_results", []) or [])
    comparison_errors = list(st.session_state.get("comparison_errors", []) or [])
    comparison_warnings = list(st.session_state.get("comparison_warnings", []) or [])
    comparison_attempted = bool(st.session_state.get("comparison_attempted", False))

    if not comparison_rows:
        _render_empty_state(
            attempted=comparison_attempted,
            error_count=len(comparison_errors),
        )
        if comparison_warnings:
            st.info("\n".join(comparison_warnings))
        if comparison_errors:
            st.warning("Some files could not be analyzed:\n- " + "\n- ".join(comparison_errors))
        return

    avg_score = round(
        sum(int(row.get("Final Score", 0)) for row in comparison_rows) / len(comparison_rows),
        1,
    )
    top_score = int(comparison_rows[0].get("Final Score", 0) or 0)
    resumes_compared = len(comparison_rows)

    resume_word = "resume" if resumes_compared == 1 else "resumes"
    # Hero now carries only the title + subtitle; the chip strip moved INSIDE
    # the primary section (next to the Sort by selector) for a tighter,
    # single-card layout matching the home page treatment.
    st.markdown(
        """
        <div class="compare-report-hero">
            <h1 class="compare-report-hero__title">Ranked <span>comparison</span></h1>
            <p class="compare-report-hero__subtitle">Resumes ranked by final score, then by issue count. Use this view to shortlist the strongest candidate against the same job description.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # JD context renders full-width above the primary section so users don't
    # forget what they're comparing against.
    _render_jd_context_expander()

    # CSV export keeps the original column set (including Top Missing Skills)
    # so downstream spreadsheet users get the full picture. The HTML table
    # drops Top Missing Skills to keep the page readable.
    csv_columns = [
        "Rank",
        "Resume",
        "Final Score",
        "JD Alignment",
        "ATS Parse",
        "Sections",
        "Issues",
        "Top Missing Skills",
    ]

    # Primary section mirrors the Analyze CV homepage layout:
    #   LEFT  → the working data (ranked Comparison Results table + sort)
    #   RIGHT → the spotlight visual (Top Match card + Why #1? rationale)
    # Ratio leans slightly to the left so the table doesn't get cramped at
    # ~half-width; Streamlit auto-stacks both columns vertically on narrow
    # viewports (< ~640px) so mobile users still get a sensible layout.
    with st.container(key="compare_primary_section"):
        primary_left, primary_right = st.columns([1.4, 1.0], gap="large")
        with primary_left:
            st.markdown(
                '<div class="compare-results-title">Comparison Results</div>',
                unsafe_allow_html=True,
            )
            # Chips on the left, Sort by stack on the right — the SORT BY
            # label is then nudged up via CSS to sit on the same baseline as
            # the "Comparison Results" title above, without moving the
            # selectbox below it.
            chips_html = (
                '<div class="compare-results-chips">'
                f'<span class="hero-chip">&#10003; {resumes_compared} {resume_word} compared</span>'
                f'<span class="hero-chip">&#10003; Top score {top_score}</span>'
                f'<span class="hero-chip">&#10003; Average {avg_score}</span>'
                '</div>'
            )
            chip_cols = st.columns([2.4, 1.4], gap="small")
            with chip_cols[0]:
                st.markdown(chips_html, unsafe_allow_html=True)
            with chip_cols[1]:
                sort_label = _render_sort_selector()
            sorted_rows = _apply_sort(comparison_rows, sort_label)
            # Pin the ★ to the true top match (rank-1 row from the original,
            # unsorted scoring order) so the star stays glued to the resume
            # the Top Match card on the right is showing — regardless of what
            # the user picks in the Sort by dropdown.
            true_top_match_name = str(comparison_rows[0].get("Resume", "") or "")
            _render_comparison_table_html(sorted_rows, top_match_name=true_top_match_name)
        with primary_right:
            st.markdown(
                _build_top_match_card_html(comparison_rows[0]),
                unsafe_allow_html=True,
            )

    # Drill-down expanders use the SAME sort order so #1 in the table = first
    # expander = the candidate the user is currently inspecting at the top.
    _render_resume_drilldowns(sorted_rows)

    # Right-aligned action row: Clear (secondary) · Download CSV · Download PDF
    # (primary). Reads naturally as "discard ← keep ← share".
    with st.container(key="compare_report_actions"):
        action_cols = st.columns([3.4, 1.2, 1.2, 1.2], gap="small")
        with action_cols[1]:
            if st.button("Clear results", key="clear_compare_results_report", width="stretch"):
                _clear_comparison_run_artifacts()
                st.session_state["page"] = "compare-cv"
                try:
                    st.query_params["page"] = "compare-cv"
                except Exception:
                    pass
                st.rerun()
        with action_cols[2]:
            comparison_csv = _comparison_rows_to_csv(sorted_rows, csv_columns)
            st.download_button(
                "Download CSV",
                data=comparison_csv,
                file_name="resume-comparison.csv",
                mime="text/csv",
                key="download_compare_csv_report",
                width="stretch",
            )
        with action_cols[3]:
            pdf_bytes = _build_comparison_pdf_bytes(
                sorted_rows,
                str(st.session_state.get("compare_jd", "") or ""),
                avg_score,
                comparison_errors,
                comparison_warnings,
            )
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="resume-comparison.pdf",
                mime="application/pdf",
                key="download_compare_pdf_report",
                width="stretch",
                type="primary",
            )

    if comparison_errors:
        st.warning("Some files could not be analyzed:\n- " + "\n- ".join(comparison_errors))
    if comparison_warnings:
        st.info("\n".join(comparison_warnings))
