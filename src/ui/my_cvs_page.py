"""My CVs page - lists saved CVs with load/delete/export actions."""

from datetime import datetime

import streamlit as st

from src.auth_utils import get_session_user
from src.database import CV, get_db
from src.services.pdf_generator import generate_cv_pdf


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y %H:%M") if dt else "-"


def render_my_cvs_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your saved CVs.")
        return

    is_dark = st.session_state.get("theme", "light") == "dark"
    card_bg = "#1f2937" if is_dark else "#ffffff"
    card_border = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)"
    hover_border = "rgba(59,130,246,0.4)" if is_dark else "rgba(59,130,246,0.3)"
    title_color = "#f1f5f9" if is_dark else "#1e293b"
    meta_color = "#64748b"
    badge_bg = "rgba(59,130,246,0.15)" if is_dark else "rgba(59,130,246,0.1)"
    badge_color = "#93c5fd" if is_dark else "#2563eb"

    st.markdown(
        f"""
        <style>
        .cv-card {{
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            transition: border-color 0.2s;
        }}
        .cv-card:hover {{ border-color: {hover_border}; }}
        .cv-title {{ color: {title_color}; font-size: 1.05rem; font-weight: 700; margin: 0 0 0.25rem; }}
        .cv-meta {{ color: {meta_color}; font-size: 0.8rem; margin: 0; }}
        .cv-template-badge {{
            display: inline-block;
            background: {badge_bg};
            color: {badge_color};
            border-radius: 999px;
            padding: 0.1rem 0.6rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        [data-testid="stAppViewContainer"] .st-key-mycvs-root {{
            margin-top: -72px !important;
        }}
        @media (max-width: 900px) {{
            [data-testid="stAppViewContainer"] .st-key-mycvs-root {{
                margin-top: -38px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="mycvs-root"):
        st.markdown("## My CVs")

        db = get_db()
        try:
            cvs = db.query(CV).filter(CV.user_id == user["id"]).order_by(CV.updated_at.desc()).all()
        finally:
            db.close()

        if not cvs:
            st.info("You haven't saved any CVs yet. Head to the **Resume Builder** to create one!")
            if st.button("Go to Resume Builder", type="primary"):
                st.session_state["page"] = "resume-builder"
                st.rerun()
            return

        st.markdown(f"**{len(cvs)} saved CV{'s' if len(cvs) != 1 else ''}**")
        st.markdown("")

        for cv in cvs:
            with st.container():
                st.markdown(
                    f"""
                    <div class="cv-card">
                        <p class="cv-title">
                            {cv.title}
                            <span class="cv-template-badge">{cv.template}</span>
                        </p>
                        <p class="cv-meta">
                            Created {_format_dt(cv.created_at)} &nbsp;&middot;&nbsp;
                            Updated {_format_dt(cv.updated_at)}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_load, col_export, col_delete = st.columns([2, 2, 1])

                with col_load:
                    if st.button("Open in Builder", key=f"load_{cv.id}", width="stretch"):
                        st.session_state["cvb_load_id"] = cv.id
                        st.session_state["page"] = "resume-builder"
                        st.rerun()

                with col_export:
                    try:
                        pdf_bytes = generate_cv_pdf(cv.data, cv.template)
                        safe_title = cv.title.replace(" ", "_")
                        st.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name=f"{safe_title}.pdf",
                            mime="application/pdf",
                            key=f"dl_{cv.id}",
                            width="stretch",
                        )
                    except Exception:
                        st.button("PDF unavailable", disabled=True, key=f"dl_err_{cv.id}", width="stretch")

                with col_delete:
                    if st.button("Delete", key=f"del_{cv.id}", width="stretch", type="secondary"):
                        st.session_state[f"confirm_delete_{cv.id}"] = True

                if st.session_state.get(f"confirm_delete_{cv.id}"):
                    st.warning(f"Delete **{cv.title}**? This cannot be undone.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, delete", key=f"yes_del_{cv.id}", type="primary"):
                            db2 = get_db()
                            try:
                                rec = db2.query(CV).filter(CV.id == cv.id).first()
                                if rec:
                                    db2.delete(rec)
                                    db2.commit()
                            finally:
                                db2.close()
                            st.session_state.pop(f"confirm_delete_{cv.id}", None)
                            st.success("CV deleted.")
                            st.rerun()
                    with c2:
                        if st.button("Cancel", key=f"no_del_{cv.id}"):
                            st.session_state.pop(f"confirm_delete_{cv.id}", None)
                            st.rerun()

                st.markdown("---")
