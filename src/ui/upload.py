"""
Upload-page preview card rendering.
"""

import csv
import hashlib
import html
from io import BytesIO, StringIO
from textwrap import dedent

import streamlit as st


def render_upload_preview_card() -> None:
    """Animated 'live report' illustration shown beside the hero copy."""
    st.markdown(
        """
        <div class="hero-visual">
            <div class="hv-glow"></div>
            <div class="hv-header">
                <span class="hv-dot"></span>
                <span class="hv-title">ATS Resume Report</span>
                <span class="hv-live">SAMPLE</span>
            </div>
            <div class="hv-ring-wrap">
                <div class="hv-ring"></div>
                <div class="hv-ring-label">
                    <span class="hv-score">92</span>
                    <span class="hv-out">OUT OF 100</span>
                </div>
            </div>
            <div class="hv-grade">Strong match &mdash; recruiter-ready</div>
            <div class="hv-bars">
                <div class="hv-bar-row">
                    <span class="hv-bar-name">Content</span>
                    <span class="hv-bar"><span class="hv-bar-fill" style="--w:92%"></span></span>
                    <span class="hv-bar-val">92%</span>
                </div>
                <div class="hv-bar-row">
                    <span class="hv-bar-name">Sections</span>
                    <span class="hv-bar"><span class="hv-bar-fill" style="--w:88%"></span></span>
                    <span class="hv-bar-val">88%</span>
                </div>
                <div class="hv-bar-row">
                    <span class="hv-bar-name">ATS Essentials</span>
                    <span class="hv-bar"><span class="hv-bar-fill" style="--w:100%"></span></span>
                    <span class="hv-bar-val">100%</span>
                </div>
                <div class="hv-bar-row">
                    <span class="hv-bar-name">Insights</span>
                    <span class="hv-bar"><span class="hv-bar-fill" style="--w:80%"></span></span>
                    <span class="hv-bar-val">80%</span>
                </div>
            </div>
            <div class="hv-tips">
                <span class="hv-tip">Quantify achievements with concrete metrics</span>
                <span class="hv-tip">Add missing keyword: &ldquo;Kubernetes&rdquo;</span>
                <span class="hv-tip">Trim the summary to three sharp lines</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_landing_sections() -> None:
    """Render simple homepage sections under the main upload/compare area."""
    landing_html = dedent(
        """
        <div class="landing-extended">
            <section class="landing-clean-section landing-intro-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">ExcelCV workflow</span>
                    <h2 class="landing-clean-title">How our free resume checker works</h2>
                    <p class="landing-clean-subtitle">
                        Our AI-powered scanner analyzes your resume like top ATS systems and recruiters.
                    </p>
                </div>
                <div class="landing-clean-grid steps-grid">
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">1</div>
                        <h4>Upload your resume</h4>
                        <p>Upload PDF or DOCX and we extract resume text for ATS-friendly evaluation.</p>
                    </article>
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">2</div>
                        <h4>ATS compatibility analysis</h4>
                        <p>We check ATS parse diagnostics, sections, and formatting strength.</p>
                    </article>
                    <article class="landing-clean-card">
                        <div class="landing-clean-icon">3</div>
                        <h4>Get your resume score</h4>
                        <p>Receive actionable feedback and downloadable report output for improvements.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Complete resume analysis</span>
                    <h3 class="landing-clean-title">Advanced resume scanner features</h3>
                    <p class="landing-clean-subtitle">
                        Everything you need to create an ATS-friendly resume that gets noticed.
                    </p>
                </div>
                <div class="landing-clean-grid features-grid">
                    <article class="landing-clean-card">
                        <h4>ATS parse diagnostics</h4>
                        <p>Evaluate how applicant tracking systems read and parse your resume structure.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Resume score calculator</h4>
                        <p>Get an instant score with strengths, weaknesses, and clear improvement direction.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Keyword optimization</h4>
                        <p>Find missing role keywords and improve JD relevance for better shortlisting.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>CV format analysis</h4>
                        <p>Check file formatting for readability and ATS compatibility across systems.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Industry feedback</h4>
                        <p>Receive practical recommendations aligned with your target role and domain.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Free review</h4>
                        <p>Use the full analysis workflow without sign-up requirements or hidden costs.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Common Questions</span>
                    <h3 class="landing-clean-title">Frequently asked questions</h3>
                    <p class="landing-clean-subtitle">
                        Quick answers before you upload your next resume draft.
                    </p>
                </div>
                <div class="landing-clean-grid faq-clean-grid">
                    <article class="landing-clean-card">
                        <h4>Is the resume checker really free?</h4>
                        <p>Yes. Resume analysis and report download are available at no cost in this app.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>What file formats are supported?</h4>
                        <p>PDF and DOCX are supported. Text-based resumes typically produce best results.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>Do you store my resume data?</h4>
                        <p>Resume content is processed in session and is not retained for long-term storage.</p>
                    </article>
                    <article class="landing-clean-card">
                        <h4>How long does analysis take?</h4>
                        <p>Most runs complete quickly and return a structured report in under a minute.</p>
                    </article>
                </div>
            </section>
            <section class="landing-clean-cta">
                <h3>Start your free resume analysis now</h3>
                <p>Join more job seekers who improved their resumes with clear ATS feedback.</p>
                <div class="landing-clean-cta-pills">
                    <span>No registration required</span>
                    <span>Instant results</span>
                    <span>100% free</span>
                </div>
            </section>
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Why choose ExcelCV</span>
                    <h3 class="landing-clean-title">Built for clarity, speed, and practical feedback</h3>
                </div>
                <div class="landing-clean-grid benefits-grid">
                    <article class="landing-clean-card"><p>Compare your resume against role expectations.</p></article>
                    <article class="landing-clean-card"><p>Improve interview callback chance with better keyword coverage.</p></article>
                    <article class="landing-clean-card"><p>Detect formatting issues that block ATS parsing.</p></article>
                    <article class="landing-clean-card"><p>Identify missing sections and contact information quickly.</p></article>
                    <article class="landing-clean-card"><p>Get JD alignment feedback with explainable scoring context.</p></article>
                    <article class="landing-clean-card"><p>Track actionable next steps for resume improvement.</p></article>
                </div>
            </section>
            <!-- COMMENTED OUT: Resume checker success stories (fake testimonials — restore when real data available)
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">Success stories</span>
                    <h3 class="landing-clean-title">Resume checker success stories</h3>
                </div>
                <div class="landing-clean-grid stories-grid">
                    <article class="landing-clean-card">
                        <p class="story-tag">CV score: 65 -> 92</p>
                        <p>"The ATS scanner found issues I never knew existed. I landed more interviews quickly."</p>
                        <h5>Sara J.</h5>
                        <span>Software Engineer</span>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Interview rate: +80%</p>
                        <p>"Keyword suggestions helped me pass ATS filters that I was missing before."</p>
                        <h5>James C.</h5>
                        <span>Marketing Manager</span>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">ATS score: 58 -> 95</p>
                        <p>"Detailed feedback made my resume stronger and easier for recruiters to review."</p>
                        <h5>Jessica W.</h5>
                        <span>Financial Analyst</span>
                    </article>
                </div>
            </section>
            -->
            <!-- COMMENTED OUT: Latest resume and career tips (blog cards have no links — restore when blog pages are complete)
            <section class="landing-clean-section">
                <div class="landing-clean-head">
                    <span class="landing-clean-tag">From the blog</span>
                    <h3 class="landing-clean-title">Latest resume and career tips</h3>
                </div>
                <div class="landing-clean-grid blog-grid">
                    <article class="landing-clean-card">
                        <p class="story-tag">Resume Help</p>
                        <h4>10 resume tips that help you get hired</h4>
                        <p>Learn practical steps to make your resume stand out to ATS and recruiters.</p>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Job Interviews</p>
                        <h4>How to prepare for your next interview</h4>
                        <p>A structured checklist to convert resume shortlists into interview success.</p>
                    </article>
                    <article class="landing-clean-card">
                        <p class="story-tag">Job Search</p>
                        <h4>Effective job search strategy in 2026</h4>
                        <p>Simple, consistent steps for better applications and stronger profile visibility.</p>
                    </article>
                </div>
            </section>
            -->
        </div>
        """
    ).strip()

    landing_html = "\n".join(line.lstrip() for line in landing_html.splitlines())

    st.markdown(
        landing_html,
        unsafe_allow_html=True,
    )

import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.ui.analysis_runner import (
    _autosave_analysis,
    run_multi_resume_comparison,
    run_single_analysis,
)
from src.ui.app_utils import _build_page_href, _sanitize_cv_filename, _save_report_snapshot
from src.ui.common import issue_count


def _comparison_input_signature(job_description: str, uploaded_cvs: list[object]) -> tuple[str, tuple[tuple[str, int], ...]]:
    """Build a stable signature for comparison inputs to detect stale results."""
    normalized_jd = (job_description or "").strip().lower()
    file_tokens: list[tuple[str, int]] = []
    for uploaded_cv in uploaded_cvs or []:
        safe_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume")).lower()
        file_size = int(getattr(uploaded_cv, "size", 0) or 0)
        file_tokens.append((safe_name, file_size))
    return normalized_jd, tuple(sorted(file_tokens))


class _InMemoryUploadedFile:
    """Minimal uploaded-file compatible wrapper backed by bytes."""

    def __init__(self, name: str, raw_bytes: bytes) -> None:
        self.name = name
        self.size = len(raw_bytes)
        self._raw_bytes = raw_bytes
        self._buffer = BytesIO(raw_bytes)

    def read(self, *args, **kwargs):
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buffer.seek(*args, **kwargs)

    def getvalue(self) -> bytes:
        return self._raw_bytes


def _format_file_size(file_size_bytes: int) -> str:
    """Return display-friendly file size text."""
    if file_size_bytes >= 1024 * 1024:
        return f"{file_size_bytes / (1024 * 1024):.1f}MB"
    return f"{file_size_bytes / 1024:.1f}KB"


def _build_staged_compare_uploads(staged_files: list[dict[str, object]]) -> list[object]:
    """Convert staged file records into uploaded-file compatible wrappers."""
    uploads: list[object] = []
    for item in staged_files:
        file_name = str(item.get("name", "resume.pdf"))
        raw_bytes = item.get("bytes")
        if isinstance(raw_bytes, bytes):
            uploads.append(_InMemoryUploadedFile(file_name, raw_bytes))
    return uploads


def _render_selected_compare_files(staged_files: list[dict[str, object]]) -> int | None:
    """Render compact selected-file rows with inline delete actions."""
    if not staged_files:
        return None

    st.markdown(
        """
        <style>
        .st-key-compare_selected_list_box [data-testid="stVerticalBlock"] > div {
            margin-bottom: 8px !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] {
            border: 1px solid rgba(148, 163, 184, 0.32);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.66);
            padding: 0 10px;
            min-height: 54px;
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] > [data-testid="stVerticalBlock"] {
            width: 100%;
            min-height: 54px !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] > [data-testid="stVerticalBlock"] > div {
            margin: 0 !important;
            width: 100%;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: center !important;
            min-height: 54px !important;
            height: 54px !important;
            margin: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            align-self: stretch !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] {
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] > div {
            width: 100%;
            height: 100%;
            display: flex !important;
            align-items: center !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] [data-testid="stVerticalBlock"] {
            width: 100%;
            height: 100%;
            display: flex !important;
            justify-content: center !important;
            gap: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="column"] [data-testid="stVerticalBlock"] > div {
            margin: 0 !important;
        }
        body.theme-dark .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] {
            border-color: rgba(100, 116, 139, 0.5);
            background: rgba(15, 23, 42, 0.5);
        }
        .st-key-compare_selected_list_box .compare-file-icon {
            font-size: 1.25rem;
            line-height: 1;
            opacity: 0.9;
        }
        .st-key-compare_selected_list_box .compare-file-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
            width: 100%;
            line-height: 1;
            min-height: 30px;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            line-height: 1 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_row_"] [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            line-height: 1 !important;
        }
        .st-key-compare_selected_list_box .compare-file-meta > span {
            display: inline-flex;
            align-items: center;
        }
        .st-key-compare_selected_list_box .compare-file-name {
            font-weight: 600;
            color: #1f2937;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.15;
        }
        body.theme-dark .st-key-compare_selected_list_box .compare-file-name {
            color: #e2e8f0;
        }
        .st-key-compare_selected_list_box .compare-file-size {
            color: #64748b;
            font-size: 0.92rem;
            white-space: nowrap;
            line-height: 1.15;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button[data-testid="baseButton-secondary"],
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] {
            min-height: 30px !important;
            min-width: 30px !important;
            width: 30px !important;
            padding: 0 !important;
            border-radius: 7px !important;
            border: 1px solid rgba(148, 163, 184, 0.5) !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            filter: none !important;
            color: #334155 !important;
            transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] > div > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button > div > div,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button *,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] * {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:hover,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:focus-visible,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:hover,
        [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:focus-visible {
            background: rgba(239, 68, 68, 0.12) !important;
            border-color: rgba(239, 68, 68, 0.75) !important;
            color: #dc2626 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"] {
            color: #cbd5e1 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:hover,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] button:focus-visible,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:hover,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-baseweb="button"]:focus-visible {
            background: rgba(239, 68, 68, 0.18) !important;
            border-color: rgba(248, 113, 113, 0.8) !important;
            color: #fca5a5 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"],
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] > [data-testid="stVerticalBlock"],
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] > [data-testid="stVerticalBlock"] > div {
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-testid="stButton"] {
            width: 100%;
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            margin: 0 !important;
        }
        .st-key-compare_selected_list_box [class*="st-key-compare_file_delete_btn_"] [data-testid="stButton"] > button {
            margin: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    deleted_index: int | None = None
    with st.container(key="compare_selected_list_box"):
        for row_start in range(0, len(staged_files), 2):
            row_cols = st.columns(2, gap="small")
            for col_offset, col in enumerate(row_cols):
                idx = row_start + col_offset
                if idx >= len(staged_files):
                    continue
                item = staged_files[idx]
                file_name = str(item.get("name", "resume.pdf"))
                file_size = int(item.get("size", 0) or 0)
                with col:
                    with st.container(key=f"compare_file_row_{idx}"):
                        row_col, action_col = st.columns([14, 1], gap="small")
                        with row_col:
                            st.markdown(
                                f"""
                                <div class="compare-file-meta">
                                    <span class="compare-file-icon">CV</span>
                                    <span class="compare-file-name">{html.escape(file_name)}</span>
                                    <span class="compare-file-size">{_format_file_size(file_size)}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with action_col:
                            with st.container(key=f"compare_file_delete_btn_{idx}"):
                                if st.button(":material/delete:", key=f"compare_delete_{idx}", type="tertiary"):
                                    deleted_index = idx
    return deleted_index


def _clear_comparison_session_state() -> None:
    """Clear comparison-related session state keys."""
    _clear_comparison_run_artifacts()
    st.session_state.pop("compare_jd", None)
    st.session_state.pop("compare_selected_files", None)
    st.session_state.pop("compare_cvs_rev", None)
    for key in list(st.session_state.keys()):
        if str(key).startswith("compare_cvs_input_"):
            st.session_state.pop(key, None)


def _clear_comparison_run_artifacts() -> None:
    """Clear only computed comparison outputs and signatures."""
    st.session_state.pop("comparison_results", None)
    st.session_state.pop("comparison_errors", None)
    st.session_state.pop("comparison_warnings", None)
    st.session_state.pop("comparison_signature", None)


def _comparison_rows_to_csv(rows: list[dict[str, object]], ordered_columns: list[str]) -> str:
    """Serialize comparison rows into a CSV string with stable column order."""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=ordered_columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in ordered_columns})
    return buffer.getvalue()


def render_upload_page(compare_mode: bool = False) -> None:
    """Landing page: upload CV + JD."""
    _current_user = get_session_user()
    # Set when the upload form is submitted; the analysis itself runs *after* the
    # whole page is rendered and all layout contexts have closed (see end of fn).
    pending_analysis = None  # tuple[str, UploadedFile] | None
    with st.container(key="hero_wrapper"):
        left, right = st.columns([1.0, 1.0], gap="medium")
        with right:
            render_upload_preview_card()
            analysis_status_slot = st.container(key="analysis_status_box")

        with left:
            st.markdown(
                """
                <div class="hero-copy">
                    <h1 class="hero-title">Is your resume <span>good enough?</span></h1>
                    <p class="hero-subtitle">Drop your resume, paste the job description, and get an ATS-ready score with &mdash; in seconds.</p>
                    <div class="hero-chip-row">
                        <span class="hero-chip">&#10003; 100% free</span>
                        <span class="hero-chip">&#10003; ATS-scored</span>
                        <span class="hero-chip">&#10003; Instant fixes</span>
                        <span class="hero-chip">&#10003; History saved</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if _current_user:
                # ── Logged-in: show full upload form ──────────────────────────────
                with st.form("upload_form"):
                    jd = st.text_area(
                        "Job description",
                        key="jd",
                        height=92,
                        placeholder="Paste the role description, must-have skills, and seniority expectations.",
                    )
                    uploaded_cv = st.file_uploader(
                        "Upload resume (PDF or DOCX)",
                        type=["pdf", "docx"],
                        key="cvs",
                        accept_multiple_files=False,
                        help="PDF or DOCX supported. Maximum file size: 2MB.",
                    )
                    submitted = st.form_submit_button("Upload & analyze", width="stretch")

                if submitted:
                    pending_analysis = (jd, uploaded_cv)

            else:
                # ── Guest: JD preview + sign-in prompt in place of file uploader ──
                st.text_area(
                    "Job description",
                    key="jd_guest",
                    height=92,
                    placeholder="Paste the role description, must-have skills, and seniority expectations.",
                )
                _auth_href = _build_page_href("auth", next_page="upload-cv")
                with st.container(key="upload_guest_box"):
                    st.markdown(
                        f"""
                        <div class="guest-auth-shell">
                            <div class="guest-auth-icon">&#128274;</div>
                            <p class="guest-auth-title">
                                Sign in to upload your resume
                            </p>
                            <p class="guest-auth-copy">
                                Get AI-powered ATS scores, keyword gaps, and save your full
                                analysis history &mdash; free forever.
                            </p>
                            <a href="{_auth_href}" target="_self" class="guest-auth-cta">
                                Sign In / Create Account &rarr;
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Smooth landing for compare section (top-nav action or first dedicated compare-page load).
    should_anchor_compare = st.session_state.pop("scroll_to_compare_anchor", False)
    if compare_mode and not st.session_state.get("_compare_mode_anchor_scrolled", False):
        should_anchor_compare = True
    if should_anchor_compare:
        components.html(
            """
            <script>
            (function() {
                var target = window.parent && window.parent !== window ? window.parent : window;
                var doc = target.document;
                var tryScroll = function() {
                    var anchor = doc.getElementById("compare-section-anchor");
                    if (anchor) {
                        try { anchor.scrollIntoView({ behavior: "smooth", block: "start" }); }
                        catch (_e) { anchor.scrollIntoView(true); }
                    }
                };
                [80, 260, 700].forEach(function(ms) { setTimeout(tryScroll, ms); });
            })();
            </script>
            """,
            height=0,
        )
    if compare_mode:
        st.session_state["_compare_mode_anchor_scrolled"] = True
    else:
        st.session_state["_compare_mode_anchor_scrolled"] = False

    st.markdown('<div id="compare-section-anchor"></div>', unsafe_allow_html=True)
    with st.container(key="compare_section_shell"):
        if compare_mode:
            st.markdown(
                '<div class="compare-mode-badge">Comparison mode active</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            """
            <div class="landing-clean-head">
                <span class="landing-clean-tag">Side-by-side ranking</span>
                <h2 class="landing-clean-title">Compare Multiple Resumes (2-5 files)</h2>
                <p class="landing-clean-subtitle">
                    Use one job description and rank candidates side-by-side using final score,
                    ATS parse, section quality, issue count, and top missing skills.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="compare_form_box"):
            if _current_user:
                if "compare_jd" not in st.session_state and st.session_state.get("jd"):
                    st.session_state["compare_jd"] = st.session_state.get("jd", "")
                if "compare_selected_files" not in st.session_state:
                    st.session_state["compare_selected_files"] = []
                if "compare_cvs_rev" not in st.session_state:
                    st.session_state["compare_cvs_rev"] = 0

                compare_jd = st.text_area(
                    "Job description for comparison",
                    key="compare_jd",
                    height=50,
                    placeholder="Paste the role description once and compare multiple resumes.",
                )
                compare_uploader_key = f"compare_cvs_input_{int(st.session_state.get('compare_cvs_rev', 0))}"
                newly_uploaded = st.file_uploader(
                    "Upload 2-5 resumes (PDF or DOCX)",
                    type=["pdf", "docx"],
                    key=compare_uploader_key,
                    accept_multiple_files=True,
                    help="Maximum 2MB per file. We will rank resumes by final score.",
                )

                staged_files: list[dict[str, object]] = list(st.session_state.get("compare_selected_files", []))
                if newly_uploaded:
                    seen_signatures = {str(item.get("signature", "")) for item in staged_files}
                    duplicate_names: list[str] = []
                    skipped_over_limit = 0
                    for uploaded_cv in newly_uploaded:
                        raw_bytes = uploaded_cv.getvalue()
                        if not isinstance(raw_bytes, bytes):
                            continue
                        safe_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume.pdf"))
                        file_size = len(raw_bytes)
                        file_hash = hashlib.sha256(raw_bytes).hexdigest()
                        signature = f"{safe_name.lower()}|{file_size}|{file_hash}"
                        if signature in seen_signatures:
                            duplicate_names.append(safe_name)
                            continue
                        if len(staged_files) >= 5:
                            skipped_over_limit += 1
                            continue
                        staged_files.append(
                            {
                                "name": safe_name,
                                "size": file_size,
                                "bytes": raw_bytes,
                                "signature": signature,
                            }
                        )
                        seen_signatures.add(signature)

                    warnings_for_ui = list(st.session_state.get("comparison_warnings", []))
                    if duplicate_names:
                        warnings_for_ui.append(
                            "Already selected and skipped: " + ", ".join(duplicate_names)
                        )
                    if skipped_over_limit > 0:
                        warnings_for_ui.append(
                            f"Only 5 resumes are allowed. Skipped {skipped_over_limit} extra file(s)."
                        )
                    st.session_state["comparison_warnings"] = warnings_for_ui
                    st.session_state["compare_selected_files"] = staged_files
                    st.session_state["compare_cvs_rev"] = int(st.session_state.get("compare_cvs_rev", 0)) + 1
                    st.rerun()

                staged_files = list(st.session_state.get("compare_selected_files", []))
                if staged_files:
                    st.markdown("**Selected resumes**")
                    deleted_index = _render_selected_compare_files(staged_files)
                    if deleted_index is not None:
                        del staged_files[deleted_index]
                        st.session_state["compare_selected_files"] = staged_files
                        st.rerun()

                compare_files = _build_staged_compare_uploads(staged_files)
                run_compare = st.button("Run comparison", key="run_compare_btn", width="stretch")
            else:
                run_compare = False
                compare_jd = ""
                compare_files = []
                _auth_href2 = _build_page_href("auth", next_page="compare-cv")
                st.markdown(
                    f"""
                    <div class="guest-auth-shell">
                        <div class="guest-auth-icon">&#128274;</div>
                        <p class="guest-auth-title">
                            Sign in to compare resumes
                        </p>
                        <p class="guest-auth-copy">
                            Upload 2–5 resumes and rank them side-by-side — free forever.
                        </p>
                        <a href="{_auth_href2}" target="_self" class="guest-auth-cta">
                            Sign In / Create Account &rarr;
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        comparison_signature = _comparison_input_signature(compare_jd, compare_files or [])
        last_signature = st.session_state.get("comparison_signature")
        if _current_user and last_signature and last_signature != comparison_signature and not run_compare:
            _clear_comparison_run_artifacts()
            st.info("Comparison inputs changed. Run comparison again to refresh results.")

        if run_compare:
            try:
                with st.spinner("Comparing resumes..."):
                    comparison = run_multi_resume_comparison(compare_jd, compare_files or [])
                st.session_state["comparison_results"] = comparison.get("rows", [])
                st.session_state["comparison_errors"] = comparison.get("errors", [])
                st.session_state["comparison_warnings"] = comparison.get("warnings", [])
                st.session_state["comparison_signature"] = comparison_signature
            except ValueError as exc:
                _clear_comparison_run_artifacts()
                st.error(str(exc))

        comparison_rows = st.session_state.get("comparison_results", [])
        comparison_errors = st.session_state.get("comparison_errors", [])
        comparison_warnings = st.session_state.get("comparison_warnings", [])
        if comparison_rows:
            summary_cols = st.columns(3, gap="small")
            avg_score = round(
                sum(int(row.get("Final Score", 0)) for row in comparison_rows) / len(comparison_rows),
                1,
            )
            summary_cols[0].metric("Resumes Compared", len(comparison_rows))
            summary_cols[1].metric("Top Score", f"{comparison_rows[0].get('Final Score', 0)}")
            summary_cols[2].metric("Average Score", f"{avg_score}")
            st.markdown('<div class="compare-results-title">Comparison Results</div>', unsafe_allow_html=True)
            ordered_columns = [
                "Rank",
                "Resume",
                "Final Score",
                "JD Alignment",
                "ATS Parse",
                "Sections",
                "Issues",
                "Top Missing Skills",
            ]
            st.dataframe(comparison_rows, width="stretch", hide_index=True, column_order=ordered_columns)
            comparison_csv = _comparison_rows_to_csv(comparison_rows, ordered_columns)
            st.download_button(
                "Download comparison CSV",
                data=comparison_csv,
                file_name="resume-comparison.csv",
                mime="text/csv",
                key="download_compare_csv",
            )
            best = comparison_rows[0]
            st.success(
                f"Top match: {best.get('Resume')} with final score {best.get('Final Score')}/100."
            )
            if st.button("Clear comparison results", key="clear_compare_results", width="content"):
                _clear_comparison_session_state()
                st.rerun()
        elif run_compare:
            st.warning("No comparison rows were generated. Please retry with different files.")
        if comparison_errors:
            st.warning("Some files could not be analyzed:\n- " + "\n- ".join(comparison_errors))
        if comparison_warnings:
            st.info("\n".join(comparison_warnings))

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

    render_upload_landing_sections()

    # ── Run the submitted analysis last ───────────────────────────────────────
    # Doing it here — after the whole page is rendered and every `with` layout
    # context (hero_wrapper, columns, the form) has closed cleanly — means the
    # st.rerun() that navigates to the report fires from the function's top
    # level, not from deep inside the hero. That avoids the stale duplicate-hero
    # render that occurred when rerun unwound those contexts mid-render.
    if pending_analysis is not None:
        jd, uploaded_cv = pending_analysis
        result = run_single_analysis(jd, uploaded_cv, status_container=analysis_status_slot)
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
            _autosave_analysis(safe_cv_name, jd, analysis)
            st.rerun()

