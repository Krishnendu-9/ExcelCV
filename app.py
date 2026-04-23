"""
ExcelCV: GenAI-Powered Vibecoded CV Reviewer - Main Streamlit Application

A professional CV analysis tool that uses Google Gemini AI to evaluate
CVs against job descriptions, providing ATS readiness scores, keyword
analysis, and actionable improvement suggestions.
"""

import base64
import json
import html
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from src.config import MAX_FILE_BYTES, MAX_FILE_MB
from src.evaluation import build_evaluation_record, summarize_evaluation
from src.gemini_client import analyze_cv_with_gemini
from src.pdf_utils import extract_cv_text, parse_confidence_chip
from src.ui_components import (
    inject_back_button_sync,
    inject_base_css,
    issue_count,
    render_report_page,
    render_upload_landing_sections,
    render_upload_preview_card,
)

APP_PAGES: Dict[str, str] = {
    "home": "Home",
    "upload-cv": "Upload CV",
    "compare-cv": "Compare Multiple CV",
    "career-blog": "Career Blog",
    "motivation-letter": "Motivation Letter",
    "resume-builder": "Resume Builder",
    "upload": "Resume Checker",
    "report": "Report",
    "ats-insights": "ATS Insights",
    "instant-report": "Instant Report",
    "evaluation-toolkit": "Evaluation Toolkit",
    "project-notes": "Project Notes",
    "how-it-works": "How It Works",
    "interview-prep": "Interview Prep",
    "privacy-policy": "Privacy Policy",
    "terms-of-service": "Terms of Service",
    "contact": "Contact",
}


def _build_page_href(page: str, include_rid: bool = False) -> str:
    """Build app-internal page URL with optional report snapshot id."""
    params: Dict[str, str] = {"page": page}
    if include_rid:
        rid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
        if rid:
            params["rid"] = str(rid)
    return f"/?{urlencode(params)}"

def _sanitize_cv_filename(raw_name: str) -> str:
    """Return a safe single-segment filename for display and downloads."""
    safe_name = str(raw_name or "CV.pdf").strip()
    safe_name = safe_name.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[\r\n\t]+", " ", safe_name)
    safe_name = re.sub(r'[<>:"/\\|?*]+', "-", safe_name).strip(" .")
    return safe_name or "CV.pdf"


def _coerce_score(value: Any, default: int = 0) -> int:
    """Convert score-like input to a bounded integer (0-100)."""
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, parsed))


def _normalize_missing_skills(value: Any, limit: int = 3) -> List[str]:
    """Return a de-duplicated list of display-ready missing skills."""
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        raw_items = [value]
    else:
        return []

    normalized: List[str] = []
    for item in raw_items:
        skill = str(item).strip()
        if not skill or skill in normalized:
            continue
        normalized.append(skill)
        if len(normalized) >= limit:
            break
    return normalized


@lru_cache(maxsize=1)
def _load_logo_data_uri() -> str:
    """Return logo as a data URI for stable rendering inside HTML markup."""
    base_dir = Path(__file__).resolve().parent / "templates"
    logo_path = base_dir / "ExcelCV_clean.png"
    if not logo_path.exists():
        logo_path = base_dir / "ExcelCV.png"
    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:image/png;base64,{encoded}"


@st.cache_resource
def _report_snapshot_store() -> Dict[str, Dict[str, Any]]:
    """Process-wide in-memory store for recent report snapshots."""
    return {}


def _build_report_snapshot() -> Dict[str, Any]:
    """Capture the minimum session fields required to restore a report page."""
    return {
        "analysis": st.session_state.get("analysis"),
        "cv_text": st.session_state.get("cv_text"),
        "job_description": st.session_state.get("job_description") or st.session_state.get("jd", ""),
        "cv_name": st.session_state.get("cv_name", "CV"),
        "cv_file_size": st.session_state.get("cv_file_size", 0),
        "issues": st.session_state.get("issues"),
    }


def _save_report_snapshot(snapshot_id: Optional[str] = None) -> str:
    """Save current report state and return a shareable snapshot id."""
    store = _report_snapshot_store()
    sid = snapshot_id or uuid4().hex
    store[sid] = _build_report_snapshot()

    # Keep memory bounded.
    while len(store) > 200:
        oldest_key = next(iter(store))
        del store[oldest_key]
    return sid


def _restore_report_snapshot(snapshot_id: str) -> bool:
    """Restore report state from snapshot id. Returns True on success."""
    store = _report_snapshot_store()
    snapshot = store.get(snapshot_id)
    if not snapshot or not snapshot.get("analysis"):
        return False

    st.session_state["analysis"] = snapshot.get("analysis")
    st.session_state["cv_text"] = snapshot.get("cv_text", "")
    st.session_state["job_description"] = snapshot.get("job_description", "")
    st.session_state["jd"] = snapshot.get("job_description", "")
    st.session_state["cv_name"] = snapshot.get("cv_name", "CV")
    st.session_state["cv_file_size"] = snapshot.get("cv_file_size", 0)
    st.session_state["issues"] = snapshot.get("issues", issue_count(snapshot["analysis"]))
    st.session_state["page"] = "report"
    st.session_state["report_snapshot_id"] = snapshot_id
    return True


def run_single_analysis(
    job_description: str,
    uploaded_cv,
    status_container: Optional[Any] = None,
) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Process a single CV analysis workflow.

    Args:
        job_description: The job description text
        uploaded_cv: Streamlit uploaded file object

    Returns:
        (analysis_dict, cv_text) if successful, None otherwise. cv_text is returned
        so the caller can keep extracted content in session.
    """
    if not job_description.strip():
        st.error("Please provide a job description.")
        return None

    if uploaded_cv is None:
        st.error("Please upload a PDF or DOCX CV.")
        return None

    if getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
        st.error(f"{uploaded_cv.name} is too large. Max {MAX_FILE_MB}MB.")
        return None

    cv_name = getattr(uploaded_cv, "name", "resume.pdf")
    try:
        cv_text = extract_cv_text(uploaded_cv, cv_name)
    except ValueError as exc:
        st.error(str(exc))
        return None

    # Show progress in the requested area (right panel under scorecard when provided).
    progress_area = status_container if status_container is not None else st.container()

    with progress_area:
        preview = cv_text[:900]
        if len(cv_text) > 900:
            preview += "..."
        with st.expander(f"Preview CV Text: {uploaded_cv.name}"):
            st.write(preview)

        # Show parse confidence
        ext = Path(cv_name).suffix.lower()
        label, cls = parse_confidence_chip(cv_text, ext)
        st.markdown(f"<span class='{cls}'>{label}</span>", unsafe_allow_html=True)

        # Run analysis
        with st.spinner(f"Analyzing {uploaded_cv.name} with Gemini..."):
            try:
                analysis = analyze_cv_with_gemini(
                    cv_text=cv_text,
                    job_desc=job_description,
                    file_name=cv_name,
                    file_size_bytes=getattr(uploaded_cv, "size", 0),
                )
                return (analysis, cv_text)
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
    return None


def _analyze_cv_payload(job_description: str, uploaded_cv) -> Tuple[Dict[str, Any], str]:
    """Extract CV text and run model analysis for one file."""
    if not job_description.strip():
        raise ValueError("Please provide a job description.")
    if uploaded_cv is None:
        raise ValueError("Please upload a PDF or DOCX CV.")
    if getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
        raise ValueError(f"{uploaded_cv.name} is too large. Max {MAX_FILE_MB}MB.")

    cv_name = getattr(uploaded_cv, "name", "resume.pdf")
    cv_text = extract_cv_text(uploaded_cv, cv_name)
    analysis = analyze_cv_with_gemini(
        cv_text=cv_text,
        job_desc=job_description,
        file_name=cv_name,
        file_size_bytes=getattr(uploaded_cv, "size", 0),
    )
    return analysis, cv_text


def run_multi_resume_comparison(job_description: str, uploaded_cvs: List[Any]) -> Dict[str, Any]:
    """Run analysis for multiple resumes and return comparison rows + errors."""
    if not job_description.strip():
        raise ValueError("Please provide a job description for comparison.")
    files = uploaded_cvs or []
    if len(files) < 2:
        raise ValueError("Please upload at least 2 resumes for comparison.")
    if len(files) > 5:
        raise ValueError("Please upload no more than 5 resumes at a time.")

    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for uploaded_cv in files:
        try:
            analysis, _ = _analyze_cv_payload(job_description, uploaded_cv)
            analysis = analysis if isinstance(analysis, dict) else {}
            tailoring_metrics = analysis.get("tailoring_metrics", {})
            content_metrics = analysis.get("content_metrics", {})
            sections_metrics = analysis.get("sections_metrics", {})
            if not isinstance(tailoring_metrics, dict):
                tailoring_metrics = {}
            if not isinstance(content_metrics, dict):
                content_metrics = {}
            if not isinstance(sections_metrics, dict):
                sections_metrics = {}

            missing_skills = _normalize_missing_skills(analysis.get("missing_skills", []))
            try:
                issues_total = int(issue_count(analysis))
            except Exception:
                issues_total = 0
            rows.append(
                {
                    "Resume": _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume")),
                    "Final Score": _coerce_score(analysis.get("match_score", 0)),
                    "JD Alignment": _coerce_score(tailoring_metrics.get("score", 0)),
                    "ATS Parse": _coerce_score(content_metrics.get("ats_parse_rate", 0)),
                    "Sections": _coerce_score(sections_metrics.get("score", 0)),
                    "Issues": max(0, issues_total),
                    "Top Missing Skills": ", ".join(missing_skills) if missing_skills else "None",
                }
            )
        except Exception as exc:  # pragma: no cover - UI path
            file_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume"))
            errors.append(f"{file_name}: {exc}")

    rows = sorted(rows, key=lambda row: row.get("Final Score", 0), reverse=True)
    return {"rows": rows, "errors": errors}


def render_theme_toggle(standalone: bool = True, key: str = "theme_toggle") -> None:
    """Render the theme switch button. If standalone=False, only the button (for use inside a column)."""
    if standalone:
        col_spacer, col_btn = st.columns([6, 1], gap="small")
        container = col_btn
    else:
        container = st.container()
    with container:
        current_theme = st.session_state.get("theme", "light")
        theme_icon = "\u2600\ufe0f" if current_theme == "light" else "\U0001F319"
        if st.button(
            theme_icon,
            key=key,
            use_container_width=standalone,
        ):
            st.session_state["theme"] = "dark" if current_theme == "light" else "light"
            st.rerun()


def render_site_header(show_theme_toggle: bool = True, current_page: str = "upload") -> None:
    """Render top branded header similar to modern landing pages."""
    if show_theme_toggle:
        col_brand, col_nav, col_theme = st.columns([1.3, 2.15, 0.55], gap="small")
    else:
        col_brand, col_nav = st.columns([1.3, 2.7], gap="small")
        col_theme = None
    logo_src = _load_logo_data_uri()
    logo_content_html = (
        f'<img src="{logo_src}" alt="ExcelCV logo" class="site-logo-wordmark" />'
        if logo_src
        else '<div class="site-logo-badge">EC</div><div class="site-brand-copy"><div class="site-name">ExcelCV</div></div>'
    )
    logo_target_url = f"/?page=home&_clear=1&_home={uuid4().hex}&_reload={uuid4().hex}"
    logo_html = (
        f'<a href="{logo_target_url}" target="_self" class="site-logo-link" aria-label="Go to homepage">'
        f'<div class="site-logo-shell">{logo_content_html}</div></a>'
    )

    with col_brand:
        st.markdown(
            f'<div class="site-brand">{logo_html}</div>',
            unsafe_allow_html=True,
        )

    nav_items = [
        ("Home", "home"),
        ("Upload CV", "upload-cv"),
        ("Compare Multiple CV", "compare-cv"),
        ("Contact", "contact"),
    ]
    if current_page in ("upload", "home"):
        active_page = "home"
    elif current_page == "report":
        active_page = "upload-cv"
    else:
        active_page = current_page

    nav_links: List[str] = []
    for label, page_key in nav_items:
        active_cls = " site-nav-item-active" if page_key == active_page else ""
        nav_links.append(
            f'<a href="{_build_page_href(page_key)}" target="_self" '
            f'class="site-nav-item{active_cls}" style="text-decoration:none;">{label}</a>'
        )

    with col_nav:
        st.markdown('<div class="site-nav">' + "".join(nav_links) + "</div>", unsafe_allow_html=True)

    if show_theme_toggle and col_theme is not None:
        with col_theme:
            st.markdown('<div class="theme-toggle-gap" aria-hidden="true"></div>', unsafe_allow_html=True)
            render_theme_toggle(standalone=False, key="theme_toggle_header")

    st.markdown('<div class="site-header-rule"></div>', unsafe_allow_html=True)


def render_site_footer() -> None:
    """Render a full-width professional footer band for all pages."""
    year = datetime.now().year
    footer_theme_cls = "footer-light" if st.session_state.get("theme", "light") == "light" else "footer-dark"
    logo_src = _load_logo_data_uri()
    footer_brand_heading = (
        f'<img src="{logo_src}" alt="ExcelCV logo" class="site-footer-brand-logo" />'
        if logo_src
        else '<div class="site-footer-brand-title">ExcelCV</div>'
    )
    footer_links = {
        "resume_checker": _build_page_href("home"),
        "ats_insights": _build_page_href("ats-insights"),
        "evaluation_toolkit": _build_page_href("evaluation-toolkit"),
        "project_notes": _build_page_href("project-notes"),
        "how_it_works": _build_page_href("how-it-works"),
        "interview_prep": _build_page_href("interview-prep"),
        "privacy_policy": _build_page_href("privacy-policy"),
        "terms_of_service": _build_page_href("terms-of-service"),
        "contact": _build_page_href("contact"),
    }

    footer_html = f"""
    <footer class="site-footer-band {footer_theme_cls}" role="contentinfo" aria-label="Website footer">
        <div class="site-footer-inner">
            <div class="site-footer-grid">
                <div class="site-footer-brand-col">
                    {footer_brand_heading}
                    <p class="site-footer-brand-text">
                        AI-powered resume analysis and actionable feedback to help you land your target role faster.
                    </p>
                </div>
                <div class="site-footer-link-col">
                    <h4>Product</h4>
                    <a href="{footer_links["resume_checker"]}" target="_self">Resume Checker</a>
                    <a href="{footer_links["ats_insights"]}" target="_self">ATS Insights</a>
                    <a href="{footer_links["evaluation_toolkit"]}" target="_self">Evaluation Toolkit</a>
                </div>
                <div class="site-footer-link-col">
                    <h4>Resources</h4>
                    <a href="{footer_links["project_notes"]}" target="_self">Project Notes</a>
                    <a href="{footer_links["how_it_works"]}" target="_self">How It Works</a>
                    <a href="{footer_links["interview_prep"]}" target="_self">Interview Prep</a>
                </div>
                <div class="site-footer-link-col">
                    <h4>Legal</h4>
                    <a href="{footer_links["privacy_policy"]}" target="_self">Privacy Policy</a>
                    <a href="{footer_links["terms_of_service"]}" target="_self">Terms of Service</a>
                    <a href="{footer_links["contact"]}" target="_self">Contact</a>
                </div>
            </div>
            <div class="site-footer-bottom">
                <span>&copy; {year} ExcelCV. All rights reserved.</span>
                <span class="site-footer-sep">&bull;</span>
                <span>Built for educational and portfolio demonstration purposes.</span>
            </div>
        </div>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


def inject_file_uploader_spacing_css() -> None:
    """
    Inject custom CSS to position labels directly on top of their boxes
    for both 'Job description' and 'Upload resume (PDF or DOCX)'.
    """
    st.markdown(
        """
        <style>
        /* Remove residual top whitespace above top controls */
        [data-testid="stAppViewContainer"] > section.main,
        [data-testid="stMainBlockContainer"],
        .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        [data-testid="stMainBlockContainer"] > div:first-child,
        [data-testid="stMainBlockContainer"] .element-container:first-child,
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }

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
            margin-bottom: 2px !important;
            margin-top: 0 !important;
            padding-bottom: 2px !important;
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
            margin-bottom: 0 !important;
            margin-top: 0 !important;
            padding-bottom: 0 !important;
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
            padding-top: 10px !important;
        }

        /* Ensure dropzone sits directly below label with no gap */
        [data-testid="stFileUploaderDropzone"],
        section[data-testid="stFileUploadDropzone"],
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            margin-top: 0 !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
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

        /* Tighten top controls and form rhythm so submit button stays above the fold on laptop screens */
        .stSelectbox,
        .stCheckbox,
        .stSelectbox label,
        .stCheckbox label {
            margin-top: 0 !important;
            margin-bottom: 2px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            line-height: 1.2 !important;
        }
        .stForm [data-testid="stVerticalBlock"] > div {
            margin-top: 0 !important;
            margin-bottom: 6px !important;
        }
        .stForm .stCaptionContainer {
            margin-top: 0 !important;
            margin-bottom: 2px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_compact_header_css() -> None:
    """Render a contained top bar visual style (geometry is fixed by JS sync)."""
    is_dark = st.session_state.get("theme", "light") == "dark"
    header_bg = "rgba(6, 12, 28, 0.66)" if is_dark else "rgba(255, 255, 255, 0.56)"
    toggle_btn_bg = "rgba(30, 41, 59, 0.52)" if is_dark else "rgba(226, 232, 240, 0.72)"
    toggle_btn_border = "rgba(148, 163, 184, 0.34)" if is_dark else "rgba(100, 116, 139, 0.34)"
    toggle_icon_color = "#f8fafc" if is_dark else "#0f172a"
    nav_active_color = "#38bdf8" if is_dark else "#1667d9"
    header_filter = (
        "blur(12px) saturate(120%)"
        if is_dark
        else "blur(12px) saturate(108%) brightness(1.04)"
    )
    header_shadow = (
        "0 4px 16px rgba(2, 6, 23, 0.20)"
        if is_dark
        else "none"
    )
    compare_box_border = "rgba(56, 189, 248, 0.24)" if is_dark else "rgba(148, 163, 184, 0.42)"
    compare_box_bg = (
        "radial-gradient(200px 130px at 78% 10%, rgba(45, 212, 191, 0.09), transparent 70%), "
        "linear-gradient(170deg, rgba(7, 16, 36, 0.82), rgba(2, 8, 24, 0.8))"
        if is_dark
        else "linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.98))"
    )
    compare_box_shadow = (
        "0 12px 24px rgba(2, 6, 23, 0.32)"
        if is_dark
        else "0 10px 20px rgba(15, 23, 42, 0.12)"
    )
    compare_label_color = "#e2e8f0" if is_dark else "#1e293b"
    compare_textarea_bg = "rgba(30, 41, 59, 0.62)" if is_dark else "rgba(255, 255, 255, 0.98)"
    compare_textarea_border = "rgba(100, 116, 139, 0.55)" if is_dark else "rgba(148, 163, 184, 0.62)"
    compare_textarea_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_placeholder = "#94a3b8" if is_dark else "#64748b"
    compare_dropzone_bg = "rgba(30, 41, 59, 0.56)" if is_dark else "rgba(248, 250, 252, 0.98)"
    compare_button_bg = "rgba(30, 41, 59, 0.88)" if is_dark else "rgba(226, 232, 240, 0.95)"
    compare_button_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_button_border = "rgba(71, 85, 105, 0.7)" if is_dark else "rgba(148, 163, 184, 0.7)"
    compare_hover_bg = "rgba(37, 99, 235, 0.16)" if is_dark else "rgba(239, 246, 255, 0.98)"
    compare_hover_border = "rgba(56, 189, 248, 0.65)" if is_dark else "rgba(37, 99, 235, 0.62)"
    compare_hover_shadow = (
        "0 0 0 3px rgba(56, 189, 248, 0.14)"
        if is_dark
        else "0 0 0 3px rgba(37, 99, 235, 0.14)"
    )
    css = """
        <style>
        :root {
            --excelcv-uniform-hover-bg: __COMPARE_HOVER_BG__;
            --excelcv-uniform-hover-border: __COMPARE_HOVER_BORDER__;
            --excelcv-uniform-hover-shadow: __COMPARE_HOVER_SHADOW__;
        }
        /* Contained top bar (fixed geometry applied by inject_fixed_top_bar JS). */
        [data-testid="stHorizontalBlock"]:has(.site-brand) {
            display: grid !important;
            grid-template-columns: minmax(230px, 1.05fr) minmax(420px, 2.15fr) auto !important;
            align-items: center !important;
            gap: 10px !important;
            width: min(1800px, calc(100vw - 90px)) !important;
            margin: 0 auto !important;
            padding: 6px 14px !important;
            box-sizing: border-box !important;
            background: __HEADER_BG__ !important;
            border: none !important;
            outline: none !important;
            border-radius: 10px !important;
            -webkit-backdrop-filter: __HEADER_FILTER__ !important;
            backdrop-filter: __HEADER_FILTER__ !important;
            box-shadow: __HEADER_SHADOW__ !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) > div {
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) > div > div {
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) [data-testid="stElementContainer"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        .site-brand {
            min-height: 42px !important;
            padding-top: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
        }
        .site-logo-link {
            display: inline-flex !important;
            align-items: center !important;
            text-decoration: none !important;
            cursor: pointer !important;
            position: relative !important;
            z-index: 30 !important;
            pointer-events: auto !important;
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            outline: none !important;
            -webkit-appearance: none !important;
            appearance: none !important;
            user-select: none !important;
            -webkit-user-select: none !important;
        }
        .site-logo-link * {
            pointer-events: none !important;
        }
        .site-logo-shell {
            display: inline-flex !important;
            align-items: center !important;
            padding: 0 4px !important;
            border-radius: 12px !important;
            overflow: visible !important;
        }
        body.theme-dark .site-logo-shell {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .site-logo-wordmark {
            height: 48px !important;
            width: auto !important;
            display: block !important;
            object-fit: contain !important;
            object-position: left center !important;
            transform: scale(1.34) !important;
            transform-origin: left center !important;
        }
        body.theme-dark .site-logo-wordmark {
            filter: brightness(1.48) saturate(1.18) contrast(1.08) drop-shadow(0 0 2px rgba(56,189,248,0.25)) !important;
        }
        .site-nav {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 26px !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            scrollbar-width: none !important;
            -ms-overflow-style: none !important;
            white-space: nowrap !important;
            min-width: 0 !important;
        }
        .site-nav::-webkit-scrollbar {
            display: none !important;
        }
        .site-nav-item {
            position: relative !important;
            display: inline-flex !important;
            align-items: center !important;
            padding: 6px 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            color: var(--text-secondary) !important;
            font-size: 1.01rem !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            text-decoration: none !important;
            transition: color 0.16s ease !important;
        }
        .site-nav-item:hover,
        .site-nav-item:focus-visible {
            color: __NAV_ACTIVE_COLOR__ !important;
        }
        .site-nav-item.site-nav-item-active {
            color: __NAV_ACTIVE_COLOR__ !important;
            font-weight: 600 !important;
        }
        .site-nav-item.site-nav-item-active::after {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            right: 0 !important;
            bottom: -8px !important;
            height: 2px !important;
            border-radius: 999px !important;
            background: __NAV_ACTIVE_COLOR__ !important;
        }
        .theme-toggle-gap {
            display: none !important;
        }
        .st-key-theme_toggle_header {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
        }
        .st-key-theme_toggle_header button,
        .st-key-theme_toggle_header button[data-testid="baseButton-secondary"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            min-height: 44px !important;
            height: 44px !important;
            min-width: 136px !important;
            width: 136px !important;
            padding: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid __TOGGLE_BTN_BORDER__ !important;
            border-color: __TOGGLE_BTN_BORDER__ !important;
            outline: none !important;
            background: __TOGGLE_BTN_BG__ !important;
            background-color: __TOGGLE_BTN_BG__ !important;
            box-shadow: none !important;
            border-radius: 10px !important;
            cursor: pointer !important;
            transition: border-color 0.14s ease !important;
            color: __TOGGLE_ICON_COLOR__ !important;
            font-size: 1.22rem !important;
            line-height: 1 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            min-width: 0 !important;
            min-height: 0 !important;
            width: auto !important;
            height: auto !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"] *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div > div * {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            transition: none !important;
            display: inline !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover > div > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus > div > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active > div > div {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button::before,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button::after,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]::before,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]::after {
            content: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:active,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:active {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid __TOGGLE_BTN_BORDER__ !important;
            border-color: __TOGGLE_BTN_BORDER__ !important;
            outline: none !important;
            box-shadow: none !important;
            background: __TOGGLE_BTN_BG__ !important;
            background-color: __TOGGLE_BTN_BG__ !important;
            background-image: none !important;
            color: __TOGGLE_ICON_COLOR__ !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .compare-section-shell {
            position: relative !important;
            margin-top: 22px !important;
            padding: 20px 8px 10px !important;
            border-radius: 18px !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            max-width: 1240px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .compare-section-title {
            margin: 0 0 8px 0 !important;
            font-size: 3rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            text-align: center !important;
            line-height: 1.05 !important;
        }
        .compare-section-subtitle {
            margin: 0 auto 20px auto !important;
            color: var(--text-secondary) !important;
            font-size: 1.05rem !important;
            line-height: 1.45 !important;
            text-align: center !important;
            max-width: none !important;
            white-space: nowrap !important;
        }
        .compare-mode-badge {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-bottom: 10px !important;
            padding: 6px 10px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(37, 99, 235, 0.35) !important;
            background: rgba(37, 99, 235, 0.1) !important;
            color: #1d4ed8 !important;
            font-size: 0.83rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
        }
        .compare-results-title {
            margin-top: 14px !important;
            margin-bottom: 8px !important;
            font-size: 1.02rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }
        .st-key-compare_form_box {
            margin-top: 14px !important;
            margin-bottom: 12px !important;
            padding: 20px 18px 16px 18px !important;
            border-radius: 14px !important;
            border: 1px solid __COMPARE_BOX_BORDER__ !important;
            background: __COMPARE_BOX_BG__ !important;
            box-shadow: __COMPARE_BOX_SHADOW__ !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] {
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] [data-testid="stVerticalBlock"] > div {
            margin-bottom: 12px !important;
        }
        .st-key-compare_form_box .stTextArea label,
        .st-key-compare_form_box .stFileUploader label {
            color: __COMPARE_LABEL_COLOR__ !important;
            font-weight: 700 !important;
        }
        .st-key-compare_form_box .stTextArea textarea {
            background: __COMPARE_TEXTAREA_BG__ !important;
            border: 1px solid __COMPARE_TEXTAREA_BORDER__ !important;
            color: __COMPARE_TEXTAREA_TEXT__ !important;
            border-radius: 10px !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stTextArea textarea:hover,
        .stForm .stTextArea textarea:focus,
        .stForm .stTextArea > div:hover textarea,
        .stForm .stTextArea > div:focus-within textarea {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box .stTextArea textarea::placeholder {
            color: __COMPARE_PLACEHOLDER__ !important;
        }
        .st-key-compare_form_box .stTextArea > div:hover textarea,
        .st-key-compare_form_box .stTextArea > div:focus-within textarea,
        .st-key-compare_form_box .stTextArea textarea:hover,
        .st-key-compare_form_box .stTextArea textarea:focus {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"] {
            border-radius: 10px !important;
            border: 1px solid __COMPARE_TEXTAREA_BORDER__ !important;
            background: __COMPARE_DROPZONE_BG__ !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stFileUploader [data-testid="stFileUploaderDropzone"]:hover,
        .stForm .stFileUploader [data-testid="stFileUploaderDropzone"]:focus-within {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"]:hover,
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"]:focus-within {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box .stFileUploader button,
        .st-key-compare_form_box .stFileUploader [data-baseweb="button"] {
            min-width: 170px !important;
            border-radius: 10px !important;
            border: 1px solid __COMPARE_BUTTON_BORDER__ !important;
            background: __COMPARE_BUTTON_BG__ !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stFileUploader button:hover,
        .stForm .stFileUploader [data-baseweb="button"]:hover {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button {
            min-height: 46px !important;
            border-radius: 10px !important;
            border: 1px solid __COMPARE_BUTTON_BORDER__ !important;
            background: __COMPARE_BUTTON_BG__ !important;
            background-image: none !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
            font-weight: 700 !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
            outline: none !important;
            box-shadow: none !important;
            filter: none !important;
            transform: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button:hover,
        .stForm [data-testid="stFormSubmitButton"] button:focus-visible,
        .stForm [data-testid="stFormSubmitButton"] button:focus,
        .stForm [data-testid="stFormSubmitButton"] button:active {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            outline: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"],
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:hover,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus-visible,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:active {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button *,
        .stForm [data-testid="stFormSubmitButton"] button > div,
        .stForm [data-testid="stFormSubmitButton"] button > div > p,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] *,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"],
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:focus-within,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:focus-within,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:focus-within {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button *,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button > div > p,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] *,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            border: none !important;
        }
        .st-key-compare_form_box .stFileUploader button:hover,
        .st-key-compare_form_box .stFileUploader [data-baseweb="button"]:hover {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:active {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            outline: none !important;
            filter: none !important;
            transform: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"],
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus-visible,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:active {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:active),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:active),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:active) {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button::before,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button::after,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]::before,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]::after {
            content: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        .compare-upload-icon {
            width: 74px !important;
            height: 74px !important;
            margin: 0 auto 12px auto !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 2rem !important;
            color: #ffffff !important;
            background: linear-gradient(135deg, #0f6ac9, #13c0b0) !important;
        }
        .compare-upload-title {
            text-align: center !important;
            margin: 0 0 6px 0 !important;
            font-size: 1.8rem !important;
            line-height: 1.08 !important;
            color: __COMPARE_LABEL_COLOR__ !important;
            font-weight: 800 !important;
        }
        .compare-upload-copy {
            text-align: center !important;
            margin: 0 0 16px 0 !important;
            color: __COMPARE_PLACEHOLDER__ !important;
            font-size: 1.0rem !important;
        }
        .compare-next-shell {
            max-width: 980px !important;
            margin: 14px auto 6px auto !important;
            padding: 22px 24px 16px 24px !important;
            border-radius: 16px !important;
            border: 1px solid var(--border-color) !important;
            background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
            box-shadow: 0 12px 24px var(--shadow) !important;
        }
        .compare-next-title {
            margin: 0 0 12px 0 !important;
            font-size: 2rem !important;
            color: var(--text-primary) !important;
            font-weight: 800 !important;
            text-align: center !important;
        }
        .compare-next-list {
            margin: 0 !important;
            padding-left: 0 !important;
            list-style: none !important;
        }
        .compare-next-list li {
            position: relative !important;
            padding-left: 30px !important;
            margin-bottom: 10px !important;
            color: var(--text-secondary) !important;
            font-size: 1.01rem !important;
            line-height: 1.45 !important;
        }
        .compare-next-list li::before {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            top: 0.58em !important;
            width: 12px !important;
            height: 12px !important;
            border-radius: 999px !important;
            border: 3px solid #0ea5b7 !important;
            transform: translateY(-50%) !important;
            box-sizing: border-box !important;
        }
        [data-testid="stAppViewContainer"] .landing-extended {
            margin-top: 24px !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 18px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-section {
            background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 18px !important;
            padding: 28px 26px !important;
            box-shadow: 0 12px 24px var(--shadow) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-head {
            text-align: center !important;
            margin-bottom: 16px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-tag {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 6px 14px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(37, 99, 235, 0.25) !important;
            background: rgba(37, 99, 235, 0.08) !important;
            color: #1d4ed8 !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.01em !important;
            text-transform: none !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-title {
            margin: 10px 0 8px 0 !important;
            color: var(--text-primary) !important;
            font-size: clamp(1.55rem, 3vw, 2.6rem) !important;
            line-height: 1.18 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-subtitle {
            margin: 0 auto !important;
            max-width: 760px !important;
            color: var(--text-secondary) !important;
            font-size: 1.03rem !important;
            line-height: 1.55 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-grid {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 14px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card {
            border: 1px solid var(--border-color) !important;
            border-radius: 14px !important;
            background: var(--bg-card) !important;
            padding: 18px !important;
            box-shadow: 0 8px 18px var(--shadow) !important;
            text-align: left !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card h4 {
            margin: 0 0 8px 0 !important;
            color: var(--text-primary) !important;
            font-size: 1.14rem !important;
            line-height: 1.28 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card p {
            margin: 0 !important;
            color: var(--text-secondary) !important;
            font-size: 0.99rem !important;
            line-height: 1.55 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-icon {
            width: 42px !important;
            height: 42px !important;
            border-radius: 999px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-bottom: 10px !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta {
            border-radius: 20px !important;
            border: 1px solid rgba(14, 116, 144, 0.25) !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
            padding: 34px 20px !important;
            text-align: center !important;
            box-shadow: 0 14px 28px rgba(15, 106, 201, 0.24) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta h3 {
            margin: 0 0 8px 0 !important;
            color: #ffffff !important;
            font-size: clamp(1.45rem, 2.4vw, 2.2rem) !important;
            line-height: 1.2 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta p {
            margin: 0 auto 14px auto !important;
            max-width: 760px !important;
            color: rgba(255, 255, 255, 0.94) !important;
            font-size: 1.05rem !important;
            line-height: 1.5 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta-pills {
            display: flex !important;
            justify-content: center !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta-pills span {
            display: inline-flex !important;
            align-items: center !important;
            padding: 7px 12px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(255, 255, 255, 0.32) !important;
            background: rgba(255, 255, 255, 0.12) !important;
            color: #ffffff !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card .story-tag {
            display: inline-flex !important;
            align-items: center !important;
            margin: 0 0 10px 0 !important;
            padding: 4px 9px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(16, 185, 129, 0.25) !important;
            background: rgba(16, 185, 129, 0.12) !important;
            color: #0f766e !important;
            font-size: 0.83rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card h5 {
            margin: 12px 0 2px 0 !important;
            color: var(--text-primary) !important;
            font-size: 1.06rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card span {
            color: var(--text-secondary) !important;
            font-size: 0.92rem !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-footnote {
            text-align: center !important;
            color: var(--text-secondary) !important;
            font-size: 0.94rem !important;
            padding: 2px 0 10px 0 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-tag {
            color: #7dd3fc !important;
            border-color: rgba(125, 211, 252, 0.28) !important;
            background: rgba(14, 116, 144, 0.22) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-card .story-tag {
            color: #86efac !important;
            border-color: rgba(134, 239, 172, 0.3) !important;
            background: rgba(22, 163, 74, 0.18) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-cta {
            background: linear-gradient(135deg, rgba(15, 106, 201, 0.72), rgba(20, 184, 166, 0.66)) !important;
            box-shadow: 0 18px 32px rgba(2, 8, 23, 0.36) !important;
        }
        .site-header-rule {
            display: none !important;
        }
        #excelcv-fixed-header-spacer {
            display: block !important;
            width: 100% !important;
            height: 80px !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }

        @media (max-width: 1100px) {
            [data-testid="stHorizontalBlock"]:has(.site-brand) {
                grid-template-columns: minmax(170px, 0.9fr) minmax(320px, 2fr) auto !important;
                width: calc(100vw - 34px) !important;
                padding: 6px 10px !important;
            }
            .site-logo-wordmark {
                height: 42px !important;
                transform: scale(1.28) !important;
            }
            .site-nav-item {
                font-size: 0.92rem !important;
            }
            .site-nav {
                gap: 16px !important;
            }
            .compare-section-subtitle {
                white-space: normal !important;
            }
            .compare-section-title {
                font-size: 2.3rem !important;
            }
            .compare-next-title {
                font-size: 1.45rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }

        @media (max-width: 820px) {
            [data-testid="stHorizontalBlock"]:has(.site-brand) {
                grid-template-columns: 1fr auto !important;
                width: calc(100vw - 20px) !important;
                border-radius: 12px !important;
            }
            .site-nav {
                display: none !important;
            }
            .site-logo-wordmark {
                height: 36px !important;
                transform: scale(1.2) !important;
            }
            #excelcv-fixed-header-spacer {
                height: 72px !important;
            }
            .compare-section-shell {
                padding: 8px 2px !important;
            }
            .compare-section-title {
                font-size: 1.9rem !important;
            }
            .compare-upload-title {
                font-size: 1.4rem !important;
            }
            .compare-next-title {
                font-size: 1.28rem !important;
            }
            .st-key-compare_form_box {
                padding: 14px 12px 12px 12px !important;
            }
            .compare-next-shell {
                padding: 16px 14px 12px 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-section {
                padding: 18px 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-grid {
                grid-template-columns: 1fr !important;
                gap: 10px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-title {
                font-size: 1.42rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-subtitle {
                font-size: 0.96rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-card {
                padding: 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-cta {
                padding: 24px 12px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-cta p {
                font-size: 0.96rem !important;
            }
        }
        </style>
        """
    css = (
        css.replace("__HEADER_BG__", header_bg)
        .replace("__TOGGLE_BTN_BG__", toggle_btn_bg)
        .replace("__TOGGLE_BTN_BORDER__", toggle_btn_border)
        .replace("__TOGGLE_ICON_COLOR__", toggle_icon_color)
        .replace("__NAV_ACTIVE_COLOR__", nav_active_color)
        .replace("__HEADER_FILTER__", header_filter)
        .replace("__HEADER_SHADOW__", header_shadow)
        .replace("__COMPARE_BOX_BORDER__", compare_box_border)
        .replace("__COMPARE_BOX_BG__", compare_box_bg)
        .replace("__COMPARE_BOX_SHADOW__", compare_box_shadow)
        .replace("__COMPARE_LABEL_COLOR__", compare_label_color)
        .replace("__COMPARE_TEXTAREA_BG__", compare_textarea_bg)
        .replace("__COMPARE_TEXTAREA_BORDER__", compare_textarea_border)
        .replace("__COMPARE_TEXTAREA_TEXT__", compare_textarea_text)
        .replace("__COMPARE_PLACEHOLDER__", compare_placeholder)
        .replace("__COMPARE_DROPZONE_BG__", compare_dropzone_bg)
        .replace("__COMPARE_BUTTON_BG__", compare_button_bg)
        .replace("__COMPARE_BUTTON_TEXT__", compare_button_text)
        .replace("__COMPARE_BUTTON_BORDER__", compare_button_border)
        .replace("__COMPARE_HOVER_BG__", compare_hover_bg)
        .replace("__COMPARE_HOVER_BORDER__", compare_hover_border)
        .replace("__COMPARE_HOVER_SHADOW__", compare_hover_shadow)
    )
    st.markdown(css, unsafe_allow_html=True)


def inject_fixed_top_bar() -> None:
    """Fix the contained top bar to viewport with a dynamic spacer."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;
            var HEADER_SELECTOR = '[data-testid="stHorizontalBlock"]:has(.site-brand)';
            var SPACER_ID = 'excelcv-fixed-header-spacer';
            var MAX_WIDTH = 1800;

            function getHeader() {
                var header = doc.querySelector(HEADER_SELECTOR);
                if (!header) return null;
                var rect = header.getBoundingClientRect();
                if (!rect || rect.width < 40 || rect.height < 24) return null;
                return header;
            }

            function viewportWidth() {
                return Math.max(
                    320,
                    (doc.documentElement && doc.documentElement.clientWidth) || target.innerWidth || 1200
                );
            }

            function computeTop(vw) {
                // Keep the top bar flush to the top edge (no visible upper gap).
                return 0;
            }

            function computeSidePad(vw) {
                if (vw <= 820) return 20;
                if (vw <= 1100) return 34;
                return 90;
            }

            function ensureSpacer(header) {
                var spacer = doc.getElementById(SPACER_ID);
                if (!spacer) {
                    spacer = doc.createElement('div');
                    spacer.id = SPACER_ID;
                }
                if (header.parentNode && spacer.nextSibling !== header) {
                    header.parentNode.insertBefore(spacer, header);
                }
                return spacer;
            }

            function applyFixedBar() {
                var header = getHeader();
                if (!header) return;

                var vw = viewportWidth();
                var top = computeTop(vw);
                var sidePad = computeSidePad(vw);
                var width = Math.max(320, Math.min(MAX_WIDTH, vw - sidePad));
                var spacer = ensureSpacer(header);

                header.style.position = 'fixed';
                header.style.top = top + 'px';
                header.style.left = '50%';
                header.style.transform = 'translateX(-50%)';
                header.style.width = width + 'px';
                header.style.zIndex = '1300';
                header.style.margin = '0';
                header.style.border = 'none';
                header.style.outline = 'none';

                var headerHeight = Math.max(
                    56,
                    Math.ceil(header.getBoundingClientRect().height || header.offsetHeight || 78)
                );
                spacer.style.display = 'block';
                spacer.style.width = '100%';
                spacer.style.height = (top + headerHeight + 6) + 'px';
                spacer.style.margin = '0';
                spacer.style.padding = '0';
                spacer.style.pointerEvents = 'none';
            }

            function scheduleApply() {
                applyFixedBar();
                target.requestAnimationFrame(applyFixedBar);
                setTimeout(applyFixedBar, 60);
                setTimeout(applyFixedBar, 220);
            }

            scheduleApply();

            if (!target.__excelcvFixedHeaderResizeBound) {
                target.__excelcvFixedHeaderResizeBound = true;
                target.addEventListener('resize', scheduleApply);
            }

            if (target.__excelcvFixedHeaderObserver) {
                target.__excelcvFixedHeaderObserver.disconnect();
            }
            target.__excelcvFixedHeaderObserver = new MutationObserver(function() {
                scheduleApply();
            });
            target.__excelcvFixedHeaderObserver.observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
    )


def inject_logo_home_click_behavior() -> None:
    """Keep logo home navigation reliable across Streamlit reruns/reloads."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;

            function buildHomeHref() {
                var current;
                try {
                    current = new URL(target.location.href);
                } catch (e) {
                    return '/?page=upload&_clear=1&_home=' + Date.now() + '&_reload=' + Date.now();
                }
                current.searchParams.set('page', 'upload');
                current.searchParams.set('_home', String(Date.now()));
                current.searchParams.set('_reload', String(Date.now()));
                current.searchParams.set('_clear', '1');
                current.searchParams.delete('rid');
                return current.pathname + '?' + current.searchParams.toString();
            }

            function bindLogos() {
                var logos = doc.querySelectorAll('.site-logo-link');
                logos.forEach(function(logo) {
                    if (logo.getAttribute('data-logo-home-bound') === '1') {
                        var cleanLogo = logo.cloneNode(true);
                        logo.parentNode.replaceChild(cleanLogo, logo);
                        logo = cleanLogo;
                    }
                    logo.setAttribute('data-logo-home-bound', '2');
                    logo.setAttribute('target', '_self');
                    logo.setAttribute('href', buildHomeHref());
                });
            }

            bindLogos();

            if (target.__excelcvLogoHomeObserver) {
                target.__excelcvLogoHomeObserver.disconnect();
            }
            target.__excelcvLogoHomeObserver = new MutationObserver(function() {
                bindLogos();
            });
            target.__excelcvLogoHomeObserver.observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
    )


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="ExcelCV",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Initialize theme in session state
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if st.session_state.get("page") not in APP_PAGES:
        st.session_state["page"] = "home"
    if "report_snapshot_id" not in st.session_state:
        st.session_state["report_snapshot_id"] = None

    # Explicit homepage reset trigger from logo click.
    if st.query_params.get("_clear"):
        st.session_state.pop("analysis", None)
        st.session_state.pop("cv_text", None)
        st.session_state.pop("job_description", None)
        st.session_state.pop("cv_name", None)
        st.session_state.pop("cv_file_size", None)
        st.session_state.pop("issues", None)
        st.session_state.pop("report_snapshot_id", None)
        st.session_state.pop("jd", None)
        st.session_state.pop("cvs", None)
        st.session_state.pop("comparison_results", None)
        st.session_state.pop("comparison_errors", None)
        st.session_state["page"] = "home"
        st.query_params["page"] = "home"
        if "rid" in st.query_params:
            del st.query_params["rid"]
        if "_clear" in st.query_params:
            del st.query_params["_clear"]
        if "_home" in st.query_params:
            del st.query_params["_home"]
        if "_reload" in st.query_params:
            del st.query_params["_reload"]

    # Sync page with URL so browser back/forward works
    url_page = st.query_params.get("page")
    url_rid = st.query_params.get("rid")
    if url_page in APP_PAGES:
        st.session_state["page"] = url_page
    if url_rid:
        st.session_state["report_snapshot_id"] = str(url_rid)

    # If report URL has a snapshot id but session was reset, restore it.
    if (
        st.session_state.get("page") == "report"
        and not st.session_state.get("analysis")
        and st.session_state.get("report_snapshot_id")
    ):
        _restore_report_snapshot(str(st.session_state["report_snapshot_id"]))

    # If user is on report page but nothing is stored, send them back.
    if st.session_state.get("page") == "report" and not st.session_state.get("analysis"):
        st.session_state["page"] = "home"
        st.query_params["page"] = "home"
        if "rid" in st.query_params:
            del st.query_params["rid"]

    # Global branded header visible on both upload and report pages.
    render_site_header(show_theme_toggle=True, current_page=str(st.session_state.get("page", "upload")))

    current_page = str(st.session_state.get("page", "upload"))
    if current_page in ("home", "upload", "upload-cv"):
        render_upload_page(compare_mode=False)
    elif current_page == "compare-cv":
        render_upload_page(compare_mode=True)
    elif current_page == "report":
        render_report_view()
    else:
        render_static_page(current_page)

    # Always use latest UI templates during runtime (avoid stale cached CSS/JS).
    template_loader = getattr(inject_base_css, "__globals__", {}).get("_load_ui_markup_template")
    if template_loader and hasattr(template_loader, "cache_clear"):
        template_loader.cache_clear()

    # Inject styles/scripts after visible UI so hidden injection containers
    # do not push the first row down.
    inject_base_css(st.session_state["theme"])
    inject_file_uploader_spacing_css()
    inject_compact_header_css()
    inject_fixed_top_bar()
    inject_back_button_sync()
    inject_logo_home_click_behavior()

    # Keep footer as the final visual block so nothing renders below it.
    render_site_footer()


def render_upload_page(compare_mode: bool = False) -> None:
    """Landing page: upload CV + JD."""
    left, right = st.columns([1.0, 1.0], gap="medium")
    with right:
        render_upload_preview_card()
        analysis_status_slot = st.container()

    with left:
        st.markdown(
            """
            <div class="hero-copy">
                <h1 class="hero-title">Is your resume <span>good enough?</span></h1>
                <p class="hero-subtitle">
                    Drop your resume, paste the JD, and get an ATS-ready report in seconds.
                </p>
                <div class="hero-chip-row">
                    <span class="hero-chip">100% free</span>
                    <span class="hero-chip">No signup</span>
                    <span class="hero-chip">Session-only data</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("upload_form"):
            jd = st.text_area(
                "Job description",
                key="jd",
                height=120,
                placeholder="Paste the role description, must-have skills, and seniority expectations.",
            )
            uploaded_cv = st.file_uploader(
                "Upload resume (PDF or DOCX)",
                type=["pdf", "docx"],
                key="cvs",
                accept_multiple_files=False,
                help="PDF or DOCX supported. Maximum file size: 2MB.",
            )
            submitted = st.form_submit_button("Upload & analyze", use_container_width=True)
            st.caption("Max 2MB per file.")
            st.markdown(
                '<div class="privacy-note">&#128274; Processed locally in-session. Nothing is stored.</div>',
                unsafe_allow_html=True,
            )

        if submitted:
            result = run_single_analysis(
                jd,
                uploaded_cv,
                status_container=analysis_status_slot,
            )
            if result:
                analysis, cv_text = result
                safe_cv_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "CV.pdf"))
                st.session_state["cv_text"] = cv_text
                st.session_state["job_description"] = jd
                st.session_state["analysis"] = analysis
                st.session_state["cv_name"] = safe_cv_name
                st.session_state["cv_file_size"] = getattr(uploaded_cv, "size", 0)
                st.session_state["issues"] = issue_count(analysis)
                st.session_state["page"] = "report"
                st.query_params["page"] = "report"
                snapshot_id = _save_report_snapshot()
                st.session_state["report_snapshot_id"] = snapshot_id
                st.query_params["rid"] = snapshot_id
                st.rerun()

    # Full-width comparison section (not one-sided).
    if compare_mode:
        components.html(
            """
            <script>
            (function() {
                var target = window.parent && window.parent !== window ? window.parent : window;
                var doc = target.document;
                setTimeout(function() {
                    var anchor = doc.getElementById("compare-section-anchor");
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }, 120);
            })();
            </script>
            """,
            height=0,
        )

    st.markdown('<div id="compare-section-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="compare-section-shell">', unsafe_allow_html=True)
    if compare_mode:
        st.markdown(
            '<div class="compare-mode-badge">Comparison mode active</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <h3 class="compare-section-title">Compare Multiple Resumes (2-5 files)</h3>
        <p class="compare-section-subtitle">
            Use one job description and rank candidates side-by-side using final score, ATS parse,
            section quality, issue count, and top missing skills.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="compare_form_box"):
        with st.form("comparison_form"):
            compare_jd = st.text_area(
                "Job description for comparison",
                key="compare_jd",
                value=st.session_state.get("jd", ""),
                height=130,
                placeholder="Paste the role description once and compare multiple resumes.",
            )
            compare_files = st.file_uploader(
                "Upload 2-5 resumes (PDF or DOCX)",
                type=["pdf", "docx"],
                key="compare_cvs",
                accept_multiple_files=True,
                help="Maximum 2MB per file. We will rank resumes by final score.",
            )
            run_compare = st.form_submit_button("Run comparison", use_container_width=True)

    if run_compare:
        try:
            with st.spinner("Comparing resumes..."):
                comparison = run_multi_resume_comparison(compare_jd, compare_files or [])
            st.session_state["comparison_results"] = comparison.get("rows", [])
            st.session_state["comparison_errors"] = comparison.get("errors", [])
        except ValueError as exc:
            st.error(str(exc))

    comparison_rows = st.session_state.get("comparison_results", [])
    comparison_errors = st.session_state.get("comparison_errors", [])
    if comparison_rows:
        st.markdown('<div class="compare-results-title">Comparison Results</div>', unsafe_allow_html=True)
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)
        best = comparison_rows[0]
        st.success(
            f"Top match: {best.get('Resume')} with final score {best.get('Final Score')}."
        )
    if comparison_errors:
        st.warning("Some files could not be analyzed:\n- " + "\n- ".join(comparison_errors))

    st.markdown(
        """
        <div class="compare-next-shell">
            <h4 class="compare-next-title">What happens next?</h4>
            <ul class="compare-next-list">
                <li>ExcelCV analyzes each resume for ATS quality, content strength, and role alignment.</li>
                <li>You get ranked comparison results with score breakdown and detected issue count.</li>
                <li>Top missing skills are highlighted so you can quickly compare candidate gaps.</li>
                <li>Use the same JD across files to keep ranking consistent and decision-ready.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    render_upload_landing_sections()


def _render_info_page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent heading block for non-analysis pages."""
    st.markdown(f"[← Back to Home]({_build_page_href('home')})")
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def render_static_page(page: str) -> None:
    """Render informational pages for navigation/footer sections."""
    page_key = str(page or "home")
    analysis = st.session_state.get("analysis", {}) if isinstance(st.session_state.get("analysis"), dict) else {}

    if page_key == "career-blog":
        _render_info_page_header(
            "Career Blog",
            "Practical career guidance for resume improvement, ATS strategy, and interview success.",
        )
        st.markdown("### Latest Topics")
        st.markdown(
            "1. **How to Quantify Resume Bullets**\n"
            "Turn generic tasks into measurable impact statements with clear metrics.\n\n"
            "2. **ATS Keyword Strategy Without Stuffing**\n"
            "Match role language naturally while keeping your resume recruiter-friendly.\n\n"
            "3. **Common Resume Rejections and Fixes**\n"
            "Spot structural issues that cause early screening drop-offs."
        )
        st.markdown("### Weekly Practice")
        st.markdown(
            "- Rewrite 3 bullets with numbers\n"
            "- Align top 10 role keywords from your target JD\n"
            "- Review one resume section per day"
        )
        return

    if page_key == "motivation-letter":
        _render_info_page_header(
            "Motivation Letter",
            "Build focused motivation letters that align with role goals and employer expectations.",
        )
        st.markdown("### Recommended Structure")
        st.markdown(
            "1. **Opening (Why this role/company)**\n"
            "2. **Proof of fit (skills + projects + outcomes)**\n"
            "3. **Value proposition (what you will contribute)**\n"
            "4. **Closing (confidence + call to action)**"
        )
        st.markdown("### Quick Writing Checklist")
        st.markdown(
            "- Mention the role title and company\n"
            "- Reference 1-2 relevant achievements with outcomes\n"
            "- Keep it concise (250-400 words)\n"
            "- Avoid generic copy-paste language"
        )
        return

    if page_key == "resume-builder":
        _render_info_page_header(
            "Resume Builder",
            "Create ATS-friendly resumes with clear structure, measurable impact, and role alignment.",
        )
        st.markdown("### Builder Blueprint")
        st.markdown(
            "- Header with professional contact links\n"
            "- Summary tailored to target role\n"
            "- Experience bullets using action + metric + outcome\n"
            "- Skills section mapped to JD keywords\n"
            "- Projects with scope, tools, and business impact"
        )
        st.markdown("### Suggested Workflow")
        st.markdown(
            "1. Draft resume content section-by-section\n"
            "2. Run `Resume Checker` to score and detect issues\n"
            "3. Apply recommendations and rerun analysis"
        )
        st.info("Use the Upload CV page to analyze your latest draft.")
        return

    if page_key == "ats-insights":
        _render_info_page_header(
            "ATS Insights",
            "Understand how ExcelCV measures recruiter and ATS readiness before final submission.",
        )
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("### What We Analyze")
            st.markdown(
                "- ATS Parse Rate\n"
                "- Quantifying Impact in bullet points\n"
                "- Repetition of action verbs\n"
                "- Spelling and grammar quality\n"
                "- Section completeness and ATS essentials"
            )
        with c2:
            st.markdown("### Score Interpretation")
            st.markdown(
                "- `80-100`: Strong ATS readiness\n"
                "- `60-79`: Moderate, needs targeted improvements\n"
                "- `0-59`: High risk for ATS/recruiter screening"
            )
        st.markdown("### Why It Matters")
        st.write(
            "Many resumes are rejected before a recruiter reads them. "
            "This page explains how ATS-visible structure and measurable outcomes improve selection chances."
        )
        return

    if page_key == "instant-report":
        _render_info_page_header(
            "Instant Report",
            "Generate a complete resume-vs-job-description report with structured and actionable feedback.",
        )
        st.markdown("### What You Get")
        st.markdown(
            "- Overall match score\n"
            "- Explainable weighted score breakdown\n"
            "- Missing skills and keyword gaps\n"
            "- Rewrite suggestions and priority action plan\n"
            "- Downloadable Markdown and JSON output"
        )
        if analysis:
            st.success("A recent report is available in this session.")
            if st.button("Open Latest Report", key="open_latest_report_btn", use_container_width=False):
                st.session_state["page"] = "report"
                st.query_params["page"] = "report"
                rid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
                if rid:
                    st.query_params["rid"] = str(rid)
                st.rerun()
        else:
            st.info("No report found in the current session. Upload a resume on the home page to generate one.")
        return

    if page_key == "evaluation-toolkit":
        _render_info_page_header(
            "Evaluation Toolkit",
            "Benchmark model output against human reviewer scores for project validation.",
        )
        st.markdown(
            "Use this toolkit to track model quality with:\n"
            "- Mean Absolute Error (MAE)\n"
            "- Root Mean Square Error (RMSE)\n"
            "- Pearson correlation"
        )
        if analysis:
            resume_name = str(st.session_state.get("cv_name", "CV"))
            render_evaluation_toolkit(analysis, resume_name)
        else:
            st.warning("Analyze at least one resume first to use the interactive toolkit.")
        return

    if page_key == "project-notes":
        _render_info_page_header(
            "Project Notes",
            "Technical overview of architecture, scoring strategy, and implementation choices.",
        )
        st.markdown("### Architecture")
        st.markdown(
            "- `app.py`: routing, session flow, page rendering\n"
            "- `src/gemini_client.py`: Gemini orchestration + deterministic merge\n"
            "- `src/scoring.py`: ATS/content/tailoring logic\n"
            "- `src/ui/*`: themed UI components and report builders"
        )
        st.markdown("### Engineering Decisions")
        st.markdown(
            "- Deterministic core scoring for explainability\n"
            "- Session-scoped analysis state for quick navigation\n"
            "- Export support (`Markdown`, `JSON`) for demos and records"
        )
        st.markdown("### Suggested Next Iterations")
        st.markdown(
            "- Add persistent benchmark storage\n"
            "- Introduce role-specific scoring profiles\n"
            "- Add automated regression dashboards for scoring changes"
        )
        return

    if page_key == "how-it-works":
        _render_info_page_header(
            "How It Works",
            "From upload to report in a transparent, reproducible flow.",
        )
        st.markdown("### 1. Input")
        st.write("Paste the job description and upload a PDF/DOCX resume.")
        st.markdown("### 2. Parsing")
        st.write("ExcelCV extracts text and checks parse confidence.")
        st.markdown("### 3. Analysis")
        st.write("Deterministic content checks run alongside model-based qualitative analysis.")
        st.markdown("### 4. Scoring")
        st.write("A weighted, explainable scoring breakdown computes final match score.")
        st.markdown("### 5. Actionable Output")
        st.write("You get missing skills, keyword gaps, rewrite suggestions, and downloadable reports.")
        return

    if page_key == "interview-prep":
        _render_info_page_header(
            "Interview Prep",
            "Prepare structured answers from strengths and identified skill gaps.",
        )
        prep_rows = analysis.get("interview_prep", []) if isinstance(analysis, dict) else []
        if prep_rows:
            st.markdown("### Questions Generated From Your Latest Analysis")
            for idx, row in enumerate(prep_rows, start=1):
                st.markdown(f"**{idx}. {row.get('type', 'Question')}**")
                st.write(row.get("question", ""))
                st.caption(row.get("why", ""))
        else:
            st.markdown("### Recommended Practice Areas")
            st.markdown(
                "- Explain a project with measurable impact\n"
                "- Defend technology choices with tradeoffs\n"
                "- Describe how you would close a missing-skill gap in 30 days\n"
                "- Prepare STAR-format stories for leadership and collaboration"
            )
            st.info("Run a resume analysis first to generate targeted interview questions.")
        return

    if page_key == "privacy-policy":
        _render_info_page_header("Privacy Policy", f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
        st.markdown("### 1. Introduction")
        st.write(
            "ExcelCV is designed for educational and portfolio use. We respect user privacy and keep data handling minimal."
        )
        st.markdown("### 2. Data We Process")
        st.markdown(
            "- Job description text entered by the user\n"
            "- Uploaded resume content for analysis\n"
            "- Optional evaluation notes provided by the user"
        )
        st.markdown("### 3. Storage & Retention")
        st.write(
            "Analysis data is handled in-session for app functionality. We do not provide user account storage in this project build."
        )
        st.markdown("### 4. Security")
        st.write("Reasonable safeguards are applied for processing within the app runtime environment.")
        st.markdown("### 5. Contact")
        st.write("For privacy-related questions, use the Contact page.")
        return

    if page_key == "terms-of-service":
        _render_info_page_header("Terms of Service", f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
        st.markdown("### 1. Acceptance")
        st.write("By using ExcelCV, you agree to these terms for this educational demo application.")
        st.markdown("### 2. Intended Use")
        st.write("The service provides resume feedback and does not guarantee hiring outcomes.")
        st.markdown("### 3. User Responsibility")
        st.write("Users are responsible for uploaded content and ensuring they have rights to submit it.")
        st.markdown("### 4. Prohibited Use")
        st.markdown(
            "- Uploading unlawful or malicious content\n"
            "- Attempting to disrupt or reverse-engineer the service"
        )
        st.markdown("### 5. Liability")
        st.write("The service is provided as-is for educational purposes without warranty.")
        st.markdown("### 6. Updates")
        st.write("Terms may be revised as the project evolves.")
        return

    if page_key == "contact":
        _render_info_page_header(
            "Contact Us",
            "Have questions or feedback? Send a message and we will review it for future project improvements.",
        )
        left, right = st.columns([1, 2], gap="large")
        with left:
            st.markdown("### Reach Us")
            st.write("Email: `support@excelcv.app`")
            st.write("Project Type: Academic / Portfolio Demo")
            st.markdown("### Typical Topics")
            st.markdown("- Feature requests\n- Bug reports\n- Resume scoring clarifications")
        with right:
            with st.form("contact_page_form", clear_on_submit=True):
                name = st.text_input("Your Name", placeholder="Enter your name")
                email = st.text_input("Email Address", placeholder="you@example.com")
                inquiry = st.radio(
                    "Inquiry Type",
                    ["General Inquiry", "Technical Support", "Feedback / Suggestion"],
                )
                subject = st.text_input("Subject", placeholder="How can we help?")
                message = st.text_area("Message", height=140, placeholder="Write your message...")
                sent = st.form_submit_button("Send Message", use_container_width=True)
            if sent:
                if not name.strip() or not email.strip() or not message.strip():
                    st.error("Please fill name, email, and message before submitting.")
                else:
                    st.success(
                        f"Thanks, {name.strip()}! Your '{inquiry}' message has been recorded for review."
                    )
                    st.caption("Demo note: this form is currently non-email and session-only.")
        return

    # Fallback for unknown routes.
    _render_info_page_header("Page Not Found")
    st.warning("The requested page is unavailable. Use the navigation links to continue.")


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
    safe_name = html.escape(str(name), quote=True)

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
            st.session_state["analysis"] = None
            st.session_state.pop("cv_text", None)
            st.session_state.pop("job_description", None)
            st.session_state.pop("cv_name", None)
            st.session_state.pop("cv_file_size", None)
            st.session_state.pop("issues", None)
            st.session_state.pop("report_snapshot_id", None)
            st.session_state.pop("jd", None)
            st.session_state.pop("cvs", None)
            st.session_state.pop("comparison_results", None)
            st.session_state.pop("comparison_errors", None)
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
