"""
AI CV Reviewer - Main Streamlit Application

A professional CV analysis tool that uses Google Gemini AI to evaluate
CVs against job descriptions, providing ATS readiness scores, keyword
analysis, and actionable improvement suggestions.
"""

from typing import Any, Dict, Optional, Tuple

import streamlit as st

from src.config import MAX_FILE_BYTES, MAX_FILE_MB
from src.gemini_client import analyze_cv_with_gemini
from src.pdf_utils import extract_pdf_text, parse_confidence_chip
from src.ui_components import (
    inject_back_button_sync,
    inject_base_css,
    issue_count,
    render_report_page,
    render_upload_landing_sections,
    render_upload_preview_card,
)

ANALYSIS_MODES = ("General Review", "ATS Scan")


def run_single_analysis(job_description: str, uploaded_cv) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Process a single CV analysis workflow.

    Args:
        job_description: The job description text
        uploaded_cv: Streamlit uploaded file object

    Returns:
        (analysis_dict, cv_text) if successful, None otherwise. cv_text is returned
        so the caller can store it for re-analysis without re-reading the PDF.
    """
    if not job_description.strip():
        st.error("Please provide a job description.")
        return None

    if uploaded_cv is None:
        st.error("Please upload a PDF CV.")
        return None

    # File size validation
    if getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
        st.error(f"{uploaded_cv.name} is too large. Max {MAX_FILE_MB}MB.")
        return None

    # Extract PDF text
    try:
        cv_text = extract_pdf_text(uploaded_cv)
    except ValueError:
        st.error("Could not read this PDF. Please upload a text-based PDF CV.")
        return None

    # Show preview
    preview = cv_text[:500]
    if len(cv_text) > 500:
        preview += "..."

    with st.expander(f"Preview CV Text: {uploaded_cv.name}"):
        st.write(preview)

    # Show parse confidence
    label, cls = parse_confidence_chip(cv_text)
    st.markdown(f"<span class='{cls}'>{label}</span>", unsafe_allow_html=True)

    # Get mode and debug settings
    mode = st.session_state.get("mode", "General Review")
    debug = st.session_state.get("debug", False)

    # Run analysis
    with st.spinner(f"Analyzing {uploaded_cv.name} with Gemini..."):
        try:
            analysis = analyze_cv_with_gemini(
                cv_text=cv_text,
                job_desc=job_description,
                mode=mode,
                debug=debug,
                file_name=getattr(uploaded_cv, "name", "resume.pdf"),
                file_size_bytes=getattr(uploaded_cv, "size", 0),
            )
            return (analysis, cv_text)
        except RuntimeError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))
    return None


def render_theme_toggle(standalone: bool = True, key: str = "theme_toggle") -> None:
    """Render the theme switch button. If standalone=False, only the button (for use inside a column)."""
    if standalone:
        col_spacer, col_btn = st.columns([6, 1], gap="small")
        container = col_btn
    else:
        container = st.container()
    with container:
        current_theme = st.session_state.get("theme", "light")
        theme_icon = "☀️" if current_theme == "light" else "🌙"
        theme_label = "Dark" if current_theme == "light" else "Light"
        if st.button(
            theme_icon,
            key=key,
            use_container_width=True,
            help=f"Switch to {theme_label} mode",
        ):
            st.session_state["theme"] = "dark" if current_theme == "light" else "light"
            st.rerun()


def render_top_controls() -> None:
    """Render global controls (analysis mode, debug, theme) for all pages."""
    col_mode, col_debug, col_theme = st.columns([2.2, 1.1, 0.5], gap="small")

    with col_mode:
        st.selectbox(
            "Analysis mode",
            options=list(ANALYSIS_MODES),
            key="mode",
            help="General Review is holistic. ATS Scan is strict on keyword/format alignment.",
        )
    with col_debug:
        st.checkbox(
            "Debug mode",
            key="debug",
            help="Show raw AI response and parsing diagnostics.",
        )
    with col_theme:
        render_theme_toggle(standalone=False, key="theme_toggle_global")


def inject_file_uploader_spacing_css() -> None:
    """
    Inject custom CSS to position labels directly on top of their boxes
    for both 'Job description' and 'Upload resume (PDF only)'.
    """
    st.markdown(
        """
        <style>
        /* ── Position labels directly on top of boxes - Clean design ── */

        /* Textarea labels - Job description - Position directly on top */
        .stTextArea > label,
        .stTextArea label,
        [data-testid="stTextArea"] > label,
        [data-testid="stTextArea"] label,
        .stForm .stTextArea label,
        .stForm .stTextArea > label,
        form .stTextArea label,
        form .stTextArea > label,
        body.theme-light .stTextArea label,
        body.theme-light .stTextArea > label,
        body.theme-light [data-testid="stTextArea"] label,
        body.theme-dark .stTextArea label,
        body.theme-dark .stTextArea > label,
        body.theme-dark [data-testid="stTextArea"] label {
            margin-bottom: 4px !important;
            margin-top: 0 !important;
            padding-bottom: 6px !important;
        }

        /* File uploader labels - Upload resume - Position directly on top */
        .stFileUploader > label,
        .stFileUploader label,
        [data-testid="stFileUploader"] > label,
        [data-testid="stFileUploader"] label,
        .stForm .stFileUploader label,
        .stForm .stFileUploader > label,
        form .stFileUploader label,
        form .stFileUploader > label,
        body.theme-light .stFileUploader label,
        body.theme-light .stFileUploader > label,
        body.theme-light [data-testid="stFileUploader"] label,
        body.theme-dark .stFileUploader label,
        body.theme-dark .stFileUploader > label,
        body.theme-dark [data-testid="stFileUploader"] label {
            margin-bottom: 4px !important;
            margin-top: 0 !important;
            padding-bottom: 6px !important;
        }

        /* Remove ALL gaps between label containers and input boxes */
        .stTextArea > div:first-child,
        .stTextArea > div:first-of-type,
        .stTextArea > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
        }

        .stFileUploader > div:first-of-type,
        .stFileUploader > div,
        [data-testid="stFileUploader"] > div,
        [data-testid="stFileUploader"] > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Ensure textarea sits directly below label with no gap */
        .stTextArea textarea {
            margin-top: 0 !important;
            padding-top: 12px !important;
        }

        /* Ensure dropzone sits directly below label with no gap */
        [data-testid="stFileUploaderDropzone"],
        section[data-testid="stFileUploadDropzone"],
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            margin-top: 0 !important;
            padding-top: 0.75rem !important;
            padding-bottom: 0.75rem !important;
        }

        /* Remove any wrapper gaps completely */
        .stTextArea {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
        }

        .stFileUploader {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Remove spacing from form containers */
        .stForm .stTextArea,
        .stForm .stFileUploader,
        form .stTextArea,
        form .stFileUploader {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="AI CV Reviewer | Resume Checker",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Initialize theme in session state
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"
    if "page" not in st.session_state:
        st.session_state["page"] = "upload"
    if "mode" not in st.session_state:
        st.session_state["mode"] = ANALYSIS_MODES[0]
    if "debug" not in st.session_state:
        st.session_state["debug"] = False

    # Sync page with URL so browser back/forward works
    url_page = st.query_params.get("page")
    if url_page in ("upload", "report"):
        st.session_state["page"] = url_page

    # If user is on report page but nothing is stored, send them back.
    if st.session_state.get("page") == "report" and not st.session_state.get("analysis"):
        st.session_state["page"] = "upload"
        st.query_params["page"] = "upload"

    # Inject CSS with current theme
    inject_base_css(st.session_state["theme"])

    # Inject the file-uploader spacing fix
    inject_file_uploader_spacing_css()

    # Reload on browser back/forward so URL and page stay in sync
    inject_back_button_sync()

    # Global controls visible on both upload and report pages.
    render_top_controls()

    if st.session_state["page"] == "upload":
        render_upload_page()
    else:
        render_report_view()


def render_upload_page() -> None:
    """Landing page: upload CV + JD."""
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown(
            """
            <div class="hero-copy">
                <h1 class="hero-title">Is your resume <span>good enough?</span></h1>
                <p class="hero-subtitle">
                    Drop your resume, paste the JD, and get an ATS-ready report in seconds.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("upload_form"):
            jd = st.text_area(
                "Job description",
                key="jd",
                height=140,
                placeholder="Paste the role description, must-have skills, and seniority expectations.",
            )
            uploaded_cv = st.file_uploader(
                "Upload resume (PDF only)",
                type=["pdf"],
                key="cvs",
                accept_multiple_files=False,
                help="PDF recommended. Maximum file size: 2MB. Text-based PDFs work best.",
            )
            st.caption("Max 2MB per file.")
            st.markdown(
                '<div class="privacy-note">🔒 Processed locally in-session. Nothing is stored.</div>',
                unsafe_allow_html=True,
            )
            submitted = st.form_submit_button("Upload & analyze", use_container_width=True)

        if submitted:
            result = run_single_analysis(jd, uploaded_cv)
            if result:
                analysis, cv_text = result
                st.session_state["cv_text"] = cv_text
                st.session_state["job_description"] = jd
                st.session_state["analysis"] = analysis
                st.session_state["cv_name"] = getattr(uploaded_cv, "name", "CV.pdf")
                st.session_state["cv_file_size"] = getattr(uploaded_cv, "size", 0)
                st.session_state["issues"] = issue_count(analysis)
                st.session_state["analysis_mode"] = st.session_state.get("mode", "General Review")
                st.session_state["page"] = "report"
                st.query_params["page"] = "report"
                st.rerun()

    with right:
        render_upload_preview_card()

    render_upload_landing_sections()


def _reanalyze_with_mode(cv_text: str, job_description: str, mode: str, debug: bool) -> Optional[Dict[str, Any]]:
    """Re-run analysis with stored CV text and job description using the specified mode."""
    with st.spinner(f"Re-analyzing with {mode} mode..."):
        try:
            return analyze_cv_with_gemini(
                cv_text=cv_text,
                job_desc=job_description,
                mode=mode,
                debug=debug,
                file_name=st.session_state.get("cv_name", "resume.pdf"),
                file_size_bytes=st.session_state.get("cv_file_size", 0),
            )
        except RuntimeError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))
    return None


def render_report_view() -> None:
    """Results page based on stored analysis."""
    analysis = st.session_state.get("analysis")
    name = st.session_state.get("cv_name", "CV")

    if not analysis:
        st.info("No analysis found. Upload a resume to get started.")
        st.session_state["page"] = "upload"
        return

    # Check if mode has changed and re-analyze if needed
    current_mode = st.session_state.get("mode", "General Review")
    stored_mode = st.session_state.get("analysis_mode", "General Review")
    cv_text = st.session_state.get("cv_text")
    job_description = st.session_state.get("job_description")
    debug = st.session_state.get("debug", False)

    # If mode changed and we have stored CV text and JD, re-analyze
    if current_mode != stored_mode and cv_text and job_description:
        new_analysis = _reanalyze_with_mode(cv_text, job_description, current_mode, debug)
        if new_analysis:
            st.session_state["analysis"] = new_analysis
            st.session_state["issues"] = issue_count(new_analysis)
            st.session_state["analysis_mode"] = current_mode
            st.rerun()
        else:
            # If re-analysis failed, revert to stored mode
            st.session_state["mode"] = stored_mode
            st.error("⚠️ Re-analysis failed. Keeping previous results. Please try again.")

    analysis_mode = st.session_state.get("analysis_mode", "General Review")
    mode_description = (
        "ATS-focused analysis emphasizing keyword matching and format compliance."
        if analysis_mode == "ATS Scan"
        else "Comprehensive review focusing on overall quality and content alignment."
    )

    # Marker for CSS/JS: center theme + Upload buttons with PDF section
    st.markdown('<div id="report-pdf-row-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
    col_header, col_actions = st.columns([1.6, 0.5])
    with col_header:
        st.markdown(
            f"""
            <div class="report-hero">
                <div>
                    <p class="eyebrow">Resume report • {analysis_mode}</p>
                    <h2 class="report-title">{name}</h2>
                    <p class="hero-subtitle">{mode_description}</p>
                    <p style="color:#9ca3af;font-size:0.85rem;margin-top:8px;">
                        💡 Tip: Change the mode in the top bar to re-analyze with different criteria
                    </p>
                </div>
                <div class="score-pill">{analysis.get("match_score", 0)} / 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_actions:
        if st.button("Upload another resume", use_container_width=True, help="Upload a new resume"):
            st.session_state["analysis"] = None
            st.session_state["page"] = "upload"
            st.query_params["page"] = "upload"
            st.rerun()

    render_report_page(analysis, name=name)


if __name__ == "__main__":
    main()
