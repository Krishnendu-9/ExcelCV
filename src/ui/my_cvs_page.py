"""My CVs page — lists saved CVs with load / export / delete actions."""

import html
import json

import streamlit as st

from src.auth_utils import get_session_user
from src.database import CV, get_db
from src.services.pdf_generator import generate_cv_pdf
from src.ui.list_pages import (
    fmt_dt,
    inject_list_page_css,
    render_delete_confirm,
    render_empty_state,
    render_meta_line,
    render_page_header,
)


@st.cache_data(show_spinner=False)
def _generate_cv_pdf_cached(data_json: str, template: str) -> bytes:
    """Render a saved CV to PDF bytes, cached on (data, template).

    Cache invalidates automatically whenever the CV is edited: a save in the
    Resume Builder updates ``cv.data``, the serialized JSON changes, and the
    cache miss regenerates. Returns ``b""`` on any rendering failure so the
    caller can show a disabled "PDF unavailable" button without crashing.
    """
    try:
        cv_data = json.loads(data_json) if data_json else {}
        return generate_cv_pdf(cv_data, template) or b""
    except Exception:
        return b""


def _go_to_builder() -> None:
    st.session_state["page"] = "resume-builder"
    st.rerun()


def render_my_cvs_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your saved CVs.")
        return

    inject_list_page_css()

    with st.container(key="lp_shell_mycvs"):
        db = get_db()
        try:
            cvs = (
                db.query(CV)
                .filter(CV.user_id == user["id"])
                .order_by(CV.updated_at.desc())
                .all()
            )
        finally:
            db.close()

        render_page_header(
            title="My CVs",
            subtitle="Open any saved resume back into the builder, export a fresh PDF, or remove it.",
            count=len(cvs),
            count_label_singular="saved CV",
            count_label_plural="saved CVs",
        )

        if not cvs:
            render_empty_state(
                icon="📄",
                title="No saved CVs yet",
                body="Build your first resume in the Resume Builder — pick a template, fill in your details, and it'll show up here.",
                cta_label="Open Resume Builder",
                cta_key="mycvs_empty_cta",
                on_cta=_go_to_builder,
            )
            return

        for cv in cvs:
            with st.container(key=f"lp_card_cv_{cv.id}"):
                meta = render_meta_line(
                    [
                        f"Created {fmt_dt(cv.created_at)}",
                        f"Updated {fmt_dt(cv.updated_at)}",
                    ]
                )
                st.markdown(
                    f"""
                    <div class="lp-card-row">
                        <p class="lp-card-title">
                            {html.escape(str(cv.title))}
                            <span class="lp-chip lp-chip--brand">{html.escape(str(cv.template).title())}</span>
                        </p>
                    </div>
                    <p class="lp-card-meta">{meta}</p>
                    """,
                    unsafe_allow_html=True,
                )

                col_load, col_export, col_delete = st.columns([2, 2, 1])

                with col_load:
                    if st.button("Open in Builder", key=f"mycvs_load_{cv.id}", width="stretch"):
                        st.session_state["cvb_load_id"] = cv.id
                        st.session_state["page"] = "resume-builder"
                        st.rerun()

                with col_export:
                    # Single-click download. _generate_cv_pdf_cached caches by
                    # (data_json, template), so first render pays the rendering
                    # cost once per CV and every later interaction is instant.
                    # Editing the CV in the builder changes data_json → cache
                    # auto-invalidates on next visit.
                    data_json = json.dumps(cv.data, sort_keys=True, default=str)
                    pdf_bytes = _generate_cv_pdf_cached(data_json, str(cv.template))
                    if pdf_bytes:
                        safe_title = str(cv.title).replace(" ", "_") or "resume"
                        st.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name=f"{safe_title}.pdf",
                            mime="application/pdf",
                            key=f"mycvs_dl_{cv.id}",
                            width="stretch",
                        )
                    else:
                        st.button(
                            "PDF unavailable",
                            disabled=True,
                            key=f"mycvs_dl_err_{cv.id}",
                            width="stretch",
                        )

                with col_delete:
                    with st.container(key=f"lp_action_delete_cv_{cv.id}"):
                        if st.button("Delete", key=f"mycvs_del_{cv.id}", width="stretch"):
                            st.session_state[f"confirm_delete_cv_{cv.id}"] = True

                if st.session_state.get(f"confirm_delete_cv_{cv.id}"):
                    def _delete_cv(target_id=cv.id, target_title=str(cv.title)):
                        db2 = get_db()
                        try:
                            rec = db2.query(CV).filter(CV.id == target_id).first()
                            if rec:
                                db2.delete(rec)
                                db2.commit()
                        finally:
                            db2.close()
                        st.session_state.pop(f"confirm_delete_cv_{target_id}", None)
                        st.session_state["ui_toast"] = {
                            "message": f"Deleted '{target_title}'.",
                            "icon": "🗑️",
                        }
                        st.rerun()

                    render_delete_confirm(
                        key=f"cv_{cv.id}",
                        message=f"Delete '{str(cv.title)}'?",
                        on_confirm=_delete_cv,
                    )
