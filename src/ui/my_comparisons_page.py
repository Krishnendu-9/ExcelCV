"""My Comparisons page — lists the signed-in user's persisted multi-resume runs.

Mirrors ``my_analyses_page.py`` (card list + view/delete actions) so saved
comparisons feel native alongside saved analyses.
"""

import html

import streamlit as st

from src.auth_utils import get_session_user
from src.database import Comparison, get_db
from src.ui.compare_report import _load_saved_comparison_into_session
from src.ui.list_pages import (
    fmt_dt,
    inject_list_page_css,
    render_delete_confirm,
    render_empty_state,
    render_meta_line,
    render_page_header,
    score_badge_html,
)


def _go_to_compare() -> None:
    st.session_state["page"] = "compare-cv"
    st.rerun()


def render_my_comparisons_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your saved comparisons.")
        return

    inject_list_page_css()

    with st.container(key="lp_shell_mycomparisons"):
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

        render_page_header(
            title="My Comparisons",
            subtitle="Multi-resume ranking runs you've saved. Reopen any to inspect the side-by-side breakdown.",
            count=len(comparisons),
            count_label_singular="saved comparison",
            count_label_plural="saved comparisons",
        )

        if not comparisons:
            render_empty_state(
                icon="📊",
                title="No comparisons saved yet",
                body="Run the Compare Resumes flow with 2–5 CVs against one job description. We'll save your ranked results here automatically.",
                cta_label="Compare Resumes",
                cta_key="mycomparisons_empty_cta",
                on_cta=_go_to_compare,
            )
            return

        for comparison in comparisons:
            top_score = float(comparison.top_score or 0)
            jd_raw = comparison.job_description or ""
            jd_preview = jd_raw[:160] + ("…" if len(jd_raw) > 160 else "")
            top_name = comparison.top_resume_name or "(unnamed)"
            safe_top_name = html.escape(str(top_name))
            safe_jd_preview = html.escape(jd_preview) if jd_preview else ""
            resume_count = int(comparison.resume_count or 0)
            resume_word = "resume" if resume_count == 1 else "resumes"

            with st.container(key=f"lp_card_cmp_{comparison.id}"):
                meta = render_meta_line(
                    [
                        fmt_dt(comparison.created_at),
                        f"Top match: {top_name}",
                    ]
                )
                jd_block = (
                    f'<p class="lp-card-jd"><strong>JD:</strong> {safe_jd_preview}</p>'
                    if safe_jd_preview
                    else ""
                )
                st.markdown(
                    f"""
                    <div class="lp-card-row">
                        <p class="lp-card-title">
                            {safe_top_name}
                            <span class="lp-chip lp-chip--brand">{resume_count} {resume_word}</span>
                        </p>
                        {score_badge_html(top_score, suffix="")}
                    </div>
                    <p class="lp-card-meta">{meta}</p>
                    {jd_block}
                    """,
                    unsafe_allow_html=True,
                )

                col_view, col_delete = st.columns([3, 1])

                with col_view:
                    if st.button(
                        "View Comparison",
                        key=f"mycomparisons_view_{comparison.id}",
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
                    with st.container(key=f"lp_action_delete_cmp_{comparison.id}"):
                        if st.button(
                            "Delete",
                            key=f"mycomparisons_del_{comparison.id}",
                            width="stretch",
                        ):
                            st.session_state[f"confirm_delete_cmp_{comparison.id}"] = True

                if st.session_state.get(f"confirm_delete_cmp_{comparison.id}"):
                    def _delete_cmp(target_id=comparison.id):
                        db2 = get_db()
                        try:
                            rec = (
                                db2.query(Comparison)
                                .filter(Comparison.id == target_id)
                                .first()
                            )
                            if rec:
                                db2.delete(rec)
                                db2.commit()
                        finally:
                            db2.close()
                        st.session_state.pop(f"confirm_delete_cmp_{target_id}", None)
                        st.session_state["ui_toast"] = {
                            "message": "Comparison deleted.",
                            "icon": "🗑️",
                        }
                        st.rerun()

                    render_delete_confirm(
                        key=f"cmp_{comparison.id}",
                        message="Delete this saved comparison?",
                        on_confirm=_delete_cmp,
                    )
