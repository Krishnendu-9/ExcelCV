"""My Analyses page - lists saved CV analysis history."""

import html
from datetime import datetime

import streamlit as st

from src.auth_utils import get_session_user
from src.database import Analysis, get_db


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y %H:%M") if dt else "-"


def _score_color(score: float) -> str:
    if score >= 75:
        return "#22c55e"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def render_my_analyses_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your analysis history.")
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
        .analysis-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .analysis-card:hover {{ border-color: {hover_border}; }}
        .analysis-cv-name {{ color: {name_color}; font-size: 1rem; font-weight: 700; margin: 0 0 0.2rem; }}
        .analysis-meta {{ color: {meta_color}; font-size: 0.8rem; margin: 0; }}
        .score-badge {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.15rem 0.75rem;
            font-size: 0.85rem;
            font-weight: 700;
        }}
        .analysis-jd-preview {{
            color: {jd_color};
            font-size: 0.82rem;
            margin-top: 0.5rem;
            font-style: italic;
        }}
        [data-testid="stAppViewContainer"] .st-key-myanalyses-root {{
            margin-top: -72px !important;
        }}
        @media (max-width: 900px) {{
            [data-testid="stAppViewContainer"] .st-key-myanalyses-root {{
                margin-top: -38px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="myanalyses-root"):
        st.markdown("## My Analyses")

        db = get_db()
        try:
            analyses = (
                db.query(Analysis)
                .filter(Analysis.user_id == user["id"])
                .order_by(Analysis.created_at.desc())
                .all()
            )
        finally:
            db.close()

        if not analyses:
            st.info("No analysis history yet. Upload your CV on the **Home** page to get started!")
            if st.button("Analyse a CV", type="primary"):
                st.session_state["page"] = "home"
                st.rerun()
            return

        st.markdown(f"**{len(analyses)} analysis result{'s' if len(analyses) != 1 else ''}**")
        st.markdown("")

        for analysis in analyses:
            score = analysis.match_score
            color = _score_color(score)
            jd_preview = (analysis.job_description or "")[:120]
            if len(analysis.job_description or "") > 120:
                jd_preview += "..."
            safe_cv_name = html.escape(str(analysis.cv_name or ""))
            safe_jd_preview = html.escape(jd_preview)

            st.markdown(
                f"""
                <div class="analysis-card">
                    <p class="analysis-cv-name">
                        {safe_cv_name}
                        &nbsp;
                        <span class="score-badge" style="background:{'rgba(34,197,94,0.15)' if score>=75 else 'rgba(245,158,11,0.15)' if score>=50 else 'rgba(239,68,68,0.15)'};color:{color}">
                            {score:.0f}% match
                        </span>
                    </p>
                    <p class="analysis-meta">{_format_dt(analysis.created_at)}</p>
                    <p class="analysis-jd-preview">Job: {safe_jd_preview}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_view, col_delete = st.columns([3, 1])

            with col_view:
                if st.button("View Full Report", key=f"view_{analysis.id}", width="stretch"):
                    st.session_state["analysis"] = analysis.result
                    st.session_state["cv_name"] = analysis.cv_name
                    st.session_state["jd"] = analysis.job_description
                    st.session_state["report_snapshot_id"] = analysis.id
                    st.session_state["page"] = "report"
                    st.rerun()

            with col_delete:
                if st.button("Delete", key=f"del_a_{analysis.id}", width="stretch"):
                    st.session_state[f"confirm_del_a_{analysis.id}"] = True

            if st.session_state.get(f"confirm_del_a_{analysis.id}"):
                st.warning("Delete this analysis? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, delete", key=f"yes_del_a_{analysis.id}", type="primary"):
                        db2 = get_db()
                        try:
                            rec = db2.query(Analysis).filter(Analysis.id == analysis.id).first()
                            if rec:
                                db2.delete(rec)
                                db2.commit()
                        finally:
                            db2.close()
                        st.session_state.pop(f"confirm_del_a_{analysis.id}", None)
                        st.success("Analysis deleted.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"no_del_a_{analysis.id}"):
                        st.session_state.pop(f"confirm_del_a_{analysis.id}", None)
                        st.rerun()

            st.markdown("---")
