"""My Comparisons page — lists the signed-in user's persisted multi-resume runs.

Mirrors the structure of ``my_analyses_page.py`` (card list + view/delete
actions) so saved comparisons feel native alongside saved analyses.
"""

from datetime import datetime
import html

import streamlit as st

from src.auth_utils import get_session_user
from src.database import Comparison, get_db
from src.ui.compare_report import _load_saved_comparison_into_session


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y %H:%M") if dt else "-"


def _score_color(score: float) -> str:
    if score >= 75:
        return "#22c55e"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def render_my_comparisons_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your saved comparisons.")
        return

    is_dark = st.session_state.get("theme", "light") == "dark"
    card_bg = "#1f2937" if is_dark else "#ffffff"
    card_border = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)"
    hover_border = "rgba(59,130,246,0.3)"
    name_color = "#f1f5f9" if is_dark else "#1e293b"
    meta_color = "#64748b"
    jd_color = "#94a3b8" if is_dark else "#64748b"

    st.markdown(
        f"""
        <style>
        .comparison-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .comparison-card:hover {{ border-color: {hover_border}; }}
        .comparison-top-name {{ color: {name_color}; font-size: 1rem; font-weight: 700; margin: 0 0 0.2rem; }}
        .comparison-meta {{ color: {meta_color}; font-size: 0.8rem; margin: 0; }}
        .comparison-score-badge {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.15rem 0.75rem;
            font-size: 0.85rem;
            font-weight: 700;
        }}
        .comparison-count-chip {{
            display: inline-block;
            margin-left: 0.5rem;
            padding: 0.15rem 0.65rem;
            border-radius: 999px;
            background: rgba(59,130,246,0.14);
            color: #1d4ed8;
            font-size: 0.78rem;
            font-weight: 700;
        }}
        body.theme-dark .comparison-count-chip {{
            background: rgba(59,130,246,0.22);
            color: #93c5fd;
        }}
        .comparison-jd-preview {{
            color: {jd_color};
            font-size: 0.82rem;
            margin-top: 0.5rem;
            font-style: italic;
        }}
        [data-testid="stAppViewContainer"] .st-key-mycomparisons-root {{
            margin-top: -72px !important;
        }}
        @media (max-width: 900px) {{
            [data-testid="stAppViewContainer"] .st-key-mycomparisons-root {{
                margin-top: -38px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="mycomparisons-root"):
        st.markdown("## My Comparisons")

        db = get_db()
        try:
            comparisons = (
                db.query(Comparison)
                .filter(Comparison.user_id == user["id"])
                .order_by(Comparison.created_at.desc())
                .all()
            )
        finally:
            db.close()

        if not comparisons:
            st.info(
                "No saved comparisons yet. Run a comparison on the "
                "**Compare Resumes** page to save one here automatically."
            )
            if st.button("Go to Compare Resumes", type="primary"):
                st.session_state["page"] = "compare-cv"
                st.rerun()
            return

        st.markdown(
            f"**{len(comparisons)} saved comparison{'s' if len(comparisons) != 1 else ''}**"
        )
        st.markdown("")

        for comparison in comparisons:
            top_score = float(comparison.top_score or 0)
            color = _score_color(top_score)
            badge_bg = (
                "rgba(34,197,94,0.15)"
                if top_score >= 75
                else "rgba(245,158,11,0.15)"
                if top_score >= 50
                else "rgba(239,68,68,0.15)"
            )
            jd_preview = (comparison.job_description or "")[:140]
            if len(comparison.job_description or "") > 140:
                jd_preview += "..."
            top_name = comparison.top_resume_name or "(unnamed)"
            safe_top_name = html.escape(str(top_name))
            safe_jd_preview = html.escape(jd_preview)
            resume_count = int(comparison.resume_count or 0)
            resume_word = "resume" if resume_count == 1 else "resumes"

            st.markdown(
                f"""
                <div class="comparison-card">
                    <p class="comparison-top-name">
                        Top match: {safe_top_name}
                        &nbsp;
                        <span class="comparison-score-badge" style="background:{badge_bg};color:{color}">
                            {top_score:.0f}/100
                        </span>
                        <span class="comparison-count-chip">{resume_count} {resume_word}</span>
                    </p>
                    <p class="comparison-meta">{_format_dt(comparison.created_at)}</p>
                    <p class="comparison-jd-preview">Job: {safe_jd_preview}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_view, col_delete = st.columns([3, 1])

            with col_view:
                if st.button(
                    "View Comparison",
                    key=f"view_cmp_{comparison.id}",
                    width="stretch",
                ):
                    if _load_saved_comparison_into_session(str(comparison.id)):
                        st.session_state["page"] = "compare-report"
                        try:
                            st.query_params["page"] = "compare-report"
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error("Could not load this comparison. It may have been deleted.")

            with col_delete:
                if st.button("Delete", key=f"del_cmp_{comparison.id}", width="stretch"):
                    st.session_state[f"confirm_del_cmp_{comparison.id}"] = True

            if st.session_state.get(f"confirm_del_cmp_{comparison.id}"):
                st.warning("Delete this saved comparison? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "Yes, delete",
                        key=f"yes_del_cmp_{comparison.id}",
                        type="primary",
                    ):
                        db2 = get_db()
                        try:
                            rec = (
                                db2.query(Comparison)
                                .filter(Comparison.id == comparison.id)
                                .first()
                            )
                            if rec:
                                db2.delete(rec)
                                db2.commit()
                        finally:
                            db2.close()
                        st.session_state.pop(f"confirm_del_cmp_{comparison.id}", None)
                        st.success("Comparison deleted.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"no_del_cmp_{comparison.id}"):
                        st.session_state.pop(f"confirm_del_cmp_{comparison.id}", None)
                        st.rerun()

            st.markdown("---")
