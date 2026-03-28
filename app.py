"""
ExcelCV: GenAI-Powered Vibecoded CV Reviewer - Main Streamlit Application

A professional CV analysis tool that uses Google Gemini AI to evaluate
CVs against job descriptions, providing ATS readiness scores, keyword
analysis, and actionable improvement suggestions.
"""

import base64
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

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

STANDARD_ANALYSIS_MODE = "General Review"


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

    # Show progress in the requested area (right panel under scorecard when provided).
    progress_area = status_container if status_container is not None else st.container()

    with progress_area:
        # Keep upload-page live status compact so progress remains visible above the fold.
        if status_container is None:
            preview = cv_text[:500]
            if len(cv_text) > 500:
                preview += "..."
            with st.expander(f"Preview CV Text: {uploaded_cv.name}"):
                st.write(preview)

        # Show parse confidence
        label, cls = parse_confidence_chip(cv_text)
        st.markdown(f"<span class='{cls}'>{label}</span>", unsafe_allow_html=True)

        # Use one standard analysis mode for a consistent scoring workflow.
        mode = STANDARD_ANALYSIS_MODE
        # Run analysis
        with st.spinner(f"Analyzing {uploaded_cv.name} with Gemini..."):
            try:
                analysis = analyze_cv_with_gemini(
                    cv_text=cv_text,
                    job_desc=job_description,
                    mode=mode,
                    debug=False,
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
        theme_icon = "\u2600\ufe0f" if current_theme == "light" else "\U0001F319"
        theme_label = "Dark" if current_theme == "light" else "Light"
        if st.button(
            theme_icon,
            key=key,
            use_container_width=True,
            help=f"Switch to {theme_label} mode",
        ):
            st.session_state["theme"] = "dark" if current_theme == "light" else "light"
            st.rerun()


def render_site_header() -> None:
    """Render top branded header similar to modern landing pages."""
    col_brand, col_nav, col_theme = st.columns([1.3, 2.15, 0.55], gap="small")
    logo_src = _load_logo_data_uri()
    logo_content_html = (
        f'<img src="{logo_src}" alt="ExcelCV logo" class="site-logo-wordmark" />'
        if logo_src
        else '<div class="site-logo-badge">EC</div><div class="site-brand-copy"><div class="site-name">ExcelCV</div></div>'
    )
    logo_target_url = f"/?page=upload&_reload={uuid4().hex}"
    logo_html = (
        f'<a href="{logo_target_url}" target="_self" class="site-logo-link" aria-label="Go to homepage">'
        f'<div class="site-logo-shell">{logo_content_html}</div></a>'
    )

    with col_brand:
        st.markdown(
            f"""
            <div class="site-brand">
                {logo_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_nav:
        st.markdown(
            """
            <div class="site-nav">
                <span class="site-nav-item">Resume Checker</span>
                <span class="site-nav-item">ATS Insights</span>
                <span class="site-nav-item">Instant Report</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_theme:
        st.markdown('<div class="theme-toggle-gap" aria-hidden="true"></div>', unsafe_allow_html=True)
        render_theme_toggle(standalone=False, key="theme_toggle_header")

    st.markdown('<div class="site-header-rule"></div>', unsafe_allow_html=True)


def inject_file_uploader_spacing_css() -> None:
    """
    Inject custom CSS to position labels directly on top of their boxes
    for both 'Job description' and 'Upload resume (PDF only)'.
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
    """Compact and vertically align the top header row to the theme switch baseline."""
    is_dark = st.session_state.get("theme", "light") == "dark"
    header_bg = "rgba(6, 12, 28, 0.66)" if is_dark else "rgba(255, 255, 255, 0.56)"
    header_border = "rgba(148, 163, 184, 0.24)" if is_dark else "rgba(148, 163, 184, 0.36)"
    header_filter = (
        "blur(12px) saturate(120%)"
        if is_dark
        else "blur(12px) saturate(108%) brightness(1.04)"
    )
    header_shadow = (
        "0 4px 16px rgba(2, 6, 23, 0.20)"
        if is_dark
        else "0 2px 10px rgba(15, 23, 42, 0.07)"
    )
    css = """
        <style>
        /* Fixed top bar styling; JS handles fixed positioning + spacer */
        [data-testid="stHorizontalBlock"]:has(.site-brand) {
            align-items: center !important;
            height: 78px !important;
            min-height: 78px !important;
            max-height: 78px !important;
            margin: 0 !important;
            padding: 0 22px !important;
            box-sizing: border-box !important;
            background: __HEADER_BG__ !important;
            border-top: none !important;
            border-bottom: 1px solid __HEADER_BORDER__ !important;
            -webkit-backdrop-filter: __HEADER_FILTER__ !important;
            backdrop-filter: __HEADER_FILTER__ !important;
            box-shadow: __HEADER_SHADOW__ !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) > div {
            display: flex !important;
            align-items: center !important;
            height: 78px !important;
            min-height: 78px !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) > div > div {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 100% !important;
            min-height: 100% !important;
        }
        [data-testid="stHorizontalBlock"]:has(.site-brand) [data-testid="stElementContainer"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        .site-brand {
            min-height: 100% !important;
            height: 100% !important;
            padding-top: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            transform: none !important;
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
            padding: 2px 4px !important;
        }
        .site-logo-wordmark {
            height: 56px !important;
        }
        .site-nav {
            padding-top: 0 !important;
            min-height: 100% !important;
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        .site-nav-item {
            padding: 8px 14px !important;
            font-size: 1rem !important;
            line-height: 1 !important;
        }
        .theme-toggle-gap {
            height: 0 !important;
        }
        .st-key-theme_toggle_header {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
            transform: none !important;
        }
        .st-key-theme_toggle_header button {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            min-height: 56px !important;
            height: 56px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .site-header-rule {
            display: none !important;
        }
        #excelcv-fixed-header-spacer {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }
        @media (max-width: 980px) {
            [data-testid="stHorizontalBlock"]:has(.site-brand) {
                height: 72px !important;
                min-height: 72px !important;
                max-height: 72px !important;
                padding: 0 12px !important;
            }
            .site-logo-wordmark {
                height: 44px !important;
            }
            .site-nav-item {
                padding: 7px 11px !important;
                font-size: 0.84rem !important;
            }
        }
        </style>
        """
    css = (
        css.replace("__HEADER_BG__", header_bg)
        .replace("__HEADER_BORDER__", header_border)
        .replace("__HEADER_FILTER__", header_filter)
        .replace("__HEADER_SHADOW__", header_shadow)
    )
    st.markdown(css, unsafe_allow_html=True)


def inject_fixed_top_bar() -> None:
    """Keep the header fixed at the top with a spacer to avoid content overlap."""
    theme_mode = st.session_state.get("theme", "light")
    script = """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;
            var HEADER_SELECTOR = '[data-testid="stHorizontalBlock"]:has(.site-brand)';
            var SPACER_ID = 'excelcv-fixed-header-spacer';
            var BAR_HEIGHT = 78;
            var THEME_MODE = '__THEME_MODE__';

            function getHeader() {
                var header = doc.querySelector(HEADER_SELECTOR);
                if (!header) return null;
                var rect = header.getBoundingClientRect();
                if (rect.width < 20 || rect.height < 20) return null;
                return header;
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

            function applyFixedHeader() {
                var header = getHeader();
                if (!header) return;

                var rect = header.getBoundingClientRect();
                var height = BAR_HEIGHT;
                var spacer = ensureSpacer(header);
                var viewportWidth = Math.max(
                    320,
                    (doc.documentElement && doc.documentElement.clientWidth) || target.innerWidth || rect.width
                );

                spacer.style.height = (height + 1) + 'px';
                spacer.style.width = '100%';
                spacer.style.display = 'block';
                spacer.style.pointerEvents = 'none';

                header.style.position = 'fixed';
                header.style.top = '0';
                header.style.left = '0';
                header.style.width = viewportWidth + 'px';
                header.style.height = height + 'px';
                header.style.minHeight = height + 'px';
                header.style.zIndex = '1300';
                header.style.margin = '0';
                header.style.padding = '0 22px';
                header.style.boxSizing = 'border-box';
                var darkTheme = THEME_MODE === 'dark';
                header.style.background = darkTheme
                    ? 'rgba(6, 12, 28, 0.66)'
                    : 'rgba(255, 255, 255, 0.56)';
                header.style.borderTop = 'none';
                header.style.borderBottom = darkTheme
                    ? '1px solid rgba(148, 163, 184, 0.24)'
                    : '1px solid rgba(148, 163, 184, 0.36)';
                header.style.backdropFilter = darkTheme
                    ? 'blur(12px) saturate(120%)'
                    : 'blur(12px) saturate(108%) brightness(1.04)';
                header.style.webkitBackdropFilter = darkTheme
                    ? 'blur(12px) saturate(120%)'
                    : 'blur(12px) saturate(108%) brightness(1.04)';
                header.style.boxShadow = darkTheme
                    ? '0 4px 16px rgba(2, 6, 23, 0.20)'
                    : '0 2px 10px rgba(15, 23, 42, 0.07)';
                header.style.display = 'flex';
                header.style.alignItems = 'center';

                doc.querySelectorAll('.site-header-rule').forEach(function(rule) {
                    rule.style.display = 'none';
                    rule.style.height = '0';
                    rule.style.margin = '0';
                });

                // Hard center all topbar elements (logo/nav/theme) to the same
                // vertical centerline of the topbar.
                var headerRect = header.getBoundingClientRect();
                var headerCenter = headerRect.top + (headerRect.height / 2);
                ['.site-brand', '.site-nav', '.st-key-theme_toggle_header'].forEach(function(sel) {
                    var el = header.querySelector(sel);
                    if (!el) return;
                    el.style.transform = 'translateY(0px)';
                    var rect2 = el.getBoundingClientRect();
                    var center2 = rect2.top + (rect2.height / 2);
                    var delta2 = headerCenter - center2;
                    el.style.transform = 'translateY(' + delta2.toFixed(2) + 'px)';
                });
            }

            function scheduleApply() {
                applyFixedHeader();
                target.requestAnimationFrame(applyFixedHeader);
                setTimeout(applyFixedHeader, 60);
                setTimeout(applyFixedHeader, 220);
            }

            scheduleApply();

            if (!target.__excelcvFixedHeaderResizeBound) {
                target.__excelcvFixedHeaderResizeBound = true;
                target.addEventListener('resize', scheduleApply);
                target.addEventListener('scroll', scheduleApply, { passive: true });
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
        """
    script = script.replace("__THEME_MODE__", theme_mode)
    components.html(script, height=0)


def inject_scroll_to_top_once() -> None:
    """Scroll the page to top once after logo click on homepage."""
    if not st.session_state.pop("_home_logo_scroll_top", False):
        return
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            function scrollTopNow() {
                try {
                    var doc = target.document;
                    var nodes = [
                        target,
                        doc.scrollingElement,
                        doc.documentElement,
                        doc.body,
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stAppViewContainer"] > section.main'),
                        doc.querySelector('section.main'),
                        doc.querySelector('.main'),
                        doc.querySelector('.main .block-container')
                    ];
                    nodes.forEach(function(node) {
                        if (!node) return;
                        if (node === target) {
                            target.scrollTo(0, 0);
                            return;
                        }
                        if (typeof node.scrollTo === 'function') {
                            node.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                        }
                        node.scrollTop = 0;
                        node.scrollLeft = 0;
                    });
                } catch (e) {}
            }
            scrollTopNow();
            target.requestAnimationFrame(scrollTopNow);
            setTimeout(scrollTopNow, 50);
            setTimeout(scrollTopNow, 180);
            setTimeout(scrollTopNow, 350);
            setTimeout(scrollTopNow, 650);
            setTimeout(scrollTopNow, 1100);
            var attempts = 0;
            var timer = setInterval(function() {
                scrollTopNow();
                attempts += 1;
                if (attempts >= 12) {
                    clearInterval(timer);
                }
            }, 120);
        })();
        </script>
        """,
        height=0,
    )


def inject_logo_home_click_behavior() -> None:
    """Make logo click always open homepage in same window and land at top."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;

            function scrollTopNow() {
                try {
                    var nodes = [
                        target,
                        doc.scrollingElement,
                        doc.documentElement,
                        doc.body,
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stAppViewContainer"] > section.main'),
                        doc.querySelector('section.main'),
                        doc.querySelector('.main'),
                        doc.querySelector('.main .block-container')
                    ];
                    nodes.forEach(function(node) {
                        if (!node) return;
                        if (node === target) {
                            target.scrollTo(0, 0);
                            return;
                        }
                        if (typeof node.scrollTo === 'function') {
                            node.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                        }
                        node.scrollTop = 0;
                        node.scrollLeft = 0;
                    });
                } catch (e) {}
            }

            function forceScrollTopBurst() {
                scrollTopNow();
                target.requestAnimationFrame(scrollTopNow);
                [40, 120, 220, 380, 700, 1100].forEach(function(ms) {
                    setTimeout(scrollTopNow, ms);
                });
            }

            function onLogoClick(ev) {
                ev.preventDefault();
                ev.stopPropagation();
                var current;
                try {
                    current = new URL(target.location.href);
                } catch (e) {
                    forceScrollTopBurst();
                    return;
                }

                var currentPage = current.searchParams.get('page') || 'upload';
                current.searchParams.set('page', 'upload');
                current.searchParams.set('_home', String(Date.now()));
                if (currentPage === 'upload') {
                    current.searchParams.set('_reload', String(Date.now()));
                }
                target.location.assign(current.toString());
            }

            function bindLogoClick() {
                var logos = doc.querySelectorAll('.site-logo-link');
                logos.forEach(function(logo) {
                    if (logo.getAttribute('data-logo-home-bound') === '1') return;
                    logo.setAttribute('data-logo-home-bound', '1');
                    logo.setAttribute('role', 'link');
                    logo.setAttribute('tabindex', '0');
                    logo.addEventListener('click', onLogoClick, true);
                    logo.addEventListener('keydown', function(ev) {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                            onLogoClick(ev);
                        }
                    }, true);
                });
            }

            function consumeHomeFlagAndScroll() {
                var current;
                try {
                    current = new URL(target.location.href);
                } catch (e) {
                    return;
                }
                if (!current.searchParams.has('_home')) return;

                forceScrollTopBurst();
                current.searchParams.delete('_home');
                var newUrl = current.pathname + (current.searchParams.toString() ? ('?' + current.searchParams.toString()) : '');
                target.history.replaceState({}, '', newUrl);
            }

            bindLogoClick();
            consumeHomeFlagAndScroll();

            if (target.__excelcvLogoHomeObserver) {
                target.__excelcvLogoHomeObserver.disconnect();
            }
            target.__excelcvLogoHomeObserver = new MutationObserver(function() {
                bindLogoClick();
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
        st.session_state["page"] = "upload"
    # Sync page with URL so browser back/forward works
    url_page = st.query_params.get("page")
    if url_page in ("upload", "report"):
        st.session_state["page"] = url_page

    # If user is on report page but nothing is stored, send them back.
    if st.session_state.get("page") == "report" and not st.session_state.get("analysis"):
        st.session_state["page"] = "upload"
        st.query_params["page"] = "upload"

    # Global branded header visible on both upload and report pages.
    render_site_header()

    if st.session_state["page"] == "upload":
        render_upload_page()
    else:
        render_report_view()

    # Inject styles/scripts after visible UI so hidden injection containers
    # do not push the first row down.
    inject_base_css(st.session_state["theme"])
    inject_file_uploader_spacing_css()
    inject_compact_header_css()
    inject_fixed_top_bar()
    inject_back_button_sync()
    inject_scroll_to_top_once()


def render_upload_page() -> None:
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
                "Upload resume (PDF only)",
                type=["pdf"],
                key="cvs",
                accept_multiple_files=False,
                help="PDF recommended. Maximum file size: 2MB. Text-based PDFs work best.",
            )
            submitted = st.form_submit_button("Upload & analyze", use_container_width=True)
            st.caption("Max 2MB per file.")
            st.markdown(
                '<div class="privacy-note">&#128274; Processed locally in-session. Nothing is stored.</div>',
                unsafe_allow_html=True,
            )

        if submitted:
            result = run_single_analysis(jd, uploaded_cv, status_container=analysis_status_slot)
            if result:
                analysis, cv_text = result
                st.session_state["cv_text"] = cv_text
                st.session_state["job_description"] = jd
                st.session_state["analysis"] = analysis
                st.session_state["cv_name"] = getattr(uploaded_cv, "name", "CV.pdf")
                st.session_state["cv_file_size"] = getattr(uploaded_cv, "size", 0)
                st.session_state["issues"] = issue_count(analysis)
                st.session_state["page"] = "report"
                st.query_params["page"] = "report"
                st.rerun()

    render_upload_landing_sections()


def render_report_view() -> None:
    """Results page based on stored analysis."""
    analysis = st.session_state.get("analysis")
    name = st.session_state.get("cv_name", "CV")

    if not analysis:
        st.info("No analysis found. Upload a resume to get started.")
        st.session_state["page"] = "upload"
        return

    mode_description = "Standard scoring across ATS readiness, content quality, and resume strength."

    # Marker for CSS/JS: center theme + Upload buttons with PDF section
    st.markdown('<div id="report-pdf-row-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
    col_header, col_actions = st.columns([1.6, 0.5])
    with col_header:
        st.markdown(
            f"""
            <div class="report-hero">
                <div>
                    <p class="eyebrow">Resume report - Standard scoring</p>
                    <h2 class="report-title">{name}</h2>
                    <p class="hero-subtitle">{mode_description}</p>
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
