"""Streamlit page renderer for cover letter generation."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.config import MAX_FILE_BYTES, MAX_FILE_MB
from src.cover_letter.models import CoverLetterResult
from src.cover_letter.service import generate_cover_letter
from src.database import CV, get_db
from src.services.pdf_generator import generate_cv_pdf

_STATE_RESULT = "cover_letter_result"
_STATE_ERROR = "cover_letter_error"
_STATE_SUCCESS = "cover_letter_success"
_SOURCE_OPTIONS = [
    "LinkedIn",
    "Company Careers Page",
    "Employee Referral",
    "Recruiter Outreach",
    "Campus Placement",
    "Other",
]
_RESUME_SOURCE_UPLOAD = "Upload a new file"
_RESUME_SOURCE_SAVED = "Use a saved CV"


class _SavedCVUpload:
    """Adapter so a saved-DB CV can be passed to ``generate_cover_letter``.

    ``generate_cover_letter`` expects an UploadedFile-like object with
    ``.name`` and a readable buffer. We render the saved CV to PDF bytes via
    ``generate_cv_pdf`` (the same renderer used in the Resume Builder export)
    and wrap the bytes here.
    """

    def __init__(self, name: str, raw: bytes) -> None:
        self.name = name
        self.size = len(raw)
        self._raw = raw
        self._buf = BytesIO(raw)

    def read(self, *args, **kwargs):
        return self._buf.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buf.seek(*args, **kwargs)

    def getvalue(self) -> bytes:
        return self._raw


def _cover_letter_icon_data_uri() -> str:
    icon_path = Path(__file__).resolve().parents[1] / "assets" / "images" / "cover-letter.png"
    if not icon_path.exists():
        return ""
    try:
        encoded = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:image/png;base64,{encoded}"


def _load_user_saved_cvs(user_id: str) -> list[CV]:
    """Return the signed-in user's saved CVs ordered by most-recent edit."""
    if not user_id:
        return []
    db = get_db()
    try:
        return (
            db.query(CV)
            .filter(CV.user_id == user_id)
            .order_by(CV.updated_at.desc())
            .all()
        )
    finally:
        db.close()


def _render_section_heading(step: int, title: str, subtitle: str = "") -> None:
    """Compact numbered heading shown above each form section."""
    sub_html = f'<p class="cl-section-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="cl-section-head">
            <span class="cl-section-step">{step}</span>
            <div class="cl-section-copy">
                <p class="cl-section-title">{title}</p>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_tips_card() -> None:
    st.markdown(
        """
        <section class="cl-tips-section">
            <div class="cl-tips-card">
                <div class="cl-tips-head">
                    <span class="cl-tips-icon">💡</span>
                    <h4>Tips for best results</h4>
                </div>
                <ul class="cl-tips-list">
                    <li>Make sure your CV is up-to-date and well-formatted.</li>
                    <li>Paste the full job description — more context yields better personalization.</li>
                    <li>Mention specific achievements you want highlighted in the additional info field.</li>
                    <li>Always review and customize the generated letter before sending.</li>
                </ul>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_success_card(result: CoverLetterResult) -> None:
    """Result panel: download CTA + collapsible preview, presented as one card."""
    st.markdown(
        """
        <div class="cl-success-card">
            <div class="cl-success-head">
                <span class="cl-success-icon">✓</span>
                <div>
                    <p class="cl-success-title">Your cover letter is ready</p>
                    <p class="cl-success-sub">Download the .docx or preview the text before sending.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download .docx",
        data=result.docx_bytes,
        file_name=result.file_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        width="stretch",
        key="cover_letter_download_btn",
        type="primary",
        on_click="ignore",
    )
    with st.expander("Preview generated letter", expanded=False):
        st.text_area(
            "Generated cover letter",
            value=result.full_text,
            height=320,
            key="cover_letter_preview_text",
            disabled=True,
            label_visibility="collapsed",
        )


def _inject_styles() -> None:
    """Idempotent CSS injection — must run every script run (Streamlit removes
    elements that aren't re-emitted, so a session-state gate would cause the
    style block to vanish after the first render)."""
    st.markdown(
        """
        <style>
        /* ── Field labels ────────────────────────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput > label,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > label,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextArea > label,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio > label {
            font-size: 1.0rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            margin-bottom: 0.35rem !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput > label p,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > label p,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextArea > label p,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio > label p {
            font-size: 1.0rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }

        /* Neutralize compare-form textarea wrappers on this page. */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box [data-testid="stTextArea"] {
            display: block !important;
            border: none !important;
            background: transparent !important;
            border-radius: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            box-shadow: none !important;
            overflow: visible !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea > label,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea label,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea > div:first-child {
            display: block !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
            position: static !important;
            transform: none !important;
            order: 0 !important;
            width: auto !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput [data-baseweb="input"]:hover,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput [data-baseweb="input"]:focus-within {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox input {
            caret-color: transparent !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox [data-baseweb="select"] input,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > div > div > div input {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
        }

        /* ── Header (icon + title) ──────────────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-head {
            margin: 0 0 1.2rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-row {
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 0.85rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-icon {
            display: block;
            width: 78px;
            height: 78px;
            margin: 0;
            object-fit: contain;
            flex: 0 0 auto;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-copy {
            text-align: left;
            display: flex;
            flex-direction: column;
            gap: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-head .landing-clean-title {
            margin: 0 !important;
            line-height: 1.02 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-head .landing-clean-subtitle {
            margin: 0 !important;
            max-width: none !important;
            line-height: 1.18 !important;
        }
        @media (max-width: 780px) {
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-row {
                flex-direction: column;
                gap: 0.55rem;
            }
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-copy {
                text-align: center;
            }
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-icon {
                width: 62px;
                height: 62px;
            }
        }

        /* ── Numbered section headings ──────────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-section-head {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin: 1.1rem 0 0.55rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-section-step {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border-radius: 999px;
            background: linear-gradient(135deg, #3b82f6, #6366f1);
            color: #fff;
            font-weight: 800;
            font-size: 0.82rem;
            flex-shrink: 0;
            box-shadow: 0 3px 8px rgba(99, 102, 241, 0.32);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-section-copy {
            display: flex;
            flex-direction: column;
            gap: 0.05rem;
            line-height: 1.2;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-section-title {
            margin: 0;
            font-size: 1.02rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-section-sub {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.82rem;
        }

        /* ── Resume source radio: inline pills ──────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 0.85rem;
        }
        /* Two distinct selectors because Streamlit's radio markup varies
           across versions: label-wrapping (BaseWeb) vs. sibling-input. */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 999px;
            padding: 0.32rem 0.85rem 0.32rem 0.55rem;
            margin: 0 !important;
            cursor: pointer;
            transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label:hover {
            border-color: rgba(99, 102, 241, 0.45);
            background: rgba(99, 102, 241, 0.04);
        }
        /* Selected state — covers both DOM shapes Streamlit ships with. */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label:has(input:checked),
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label[data-baseweb]:has(input:checked),
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label[aria-checked="true"] {
            background: rgba(99, 102, 241, 0.14) !important;
            border-color: rgba(99, 102, 241, 0.6) !important;
            box-shadow: 0 1px 3px rgba(99, 102, 241, 0.2) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label:has(input:checked) p,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label[aria-checked="true"] p {
            color: #4338ca !important;
            font-weight: 600 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label:has(input:checked) p,
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stRadio [role="radiogroup"] label[aria-checked="true"] p {
            color: #c7d2fe !important;
        }

        /* ── File uploader: tighter polish ──────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:focus,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:focus-visible {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            min-width: auto !important;
            min-height: auto !important;
            padding: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:hover {
            background: rgba(220, 38, 38, 0.14) !important;
            border-radius: 6px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] [role="button"] *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] [data-testid="stIconMaterial"] {
            background: transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:hover *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:focus-visible *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:hover [data-testid="stIconMaterial"],
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:focus-visible [data-testid="stIconMaterial"] {
            color: #dc2626 !important;
        }

        /* ── JD char counter: overlay pill INSIDE the textarea ──
           The JS in page.py (a) moves ``.cl-char-count-overlay`` into the
           ``[data-testid="stTextArea"]`` node so absolute positioning is
           measured against the textarea wrapper, (b) hides the now-empty
           element-container the overlay was originally rendered into, and
           (c) binds an ``input`` listener for real-time updates. No CSS
           ``:has`` selectors needed — using them caused the textarea wrapper
           itself to match after the move and collapsed its height to 0. */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-char-count-overlay {
            position: absolute;
            right: 22px;          /* clear of the native resize grabber */
            bottom: 12px;
            padding: 0.1rem 0.5rem;
            background: rgba(255, 255, 255, 0.92);
            color: var(--text-secondary);
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            pointer-events: none;
            line-height: 1.4;
            z-index: 3;
            backdrop-filter: blur(2px);
            white-space: nowrap;
            transition: opacity 0.12s ease;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-char-count-overlay {
            background: rgba(15, 23, 42, 0.82);
            color: var(--text-secondary);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-char-count-overlay--low {
            color: #b45309;
            border-color: rgba(217, 119, 6, 0.4);
            background: rgba(254, 243, 199, 0.94);
        }
        body.theme-dark [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-char-count-overlay--low {
            color: #fbbf24;
            background: rgba(120, 53, 15, 0.6);
            border-color: rgba(251, 191, 36, 0.4);
        }

        /* ── File uploader: tighter dropzone + soften nested border ── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell [data-testid="stFileUploaderDropzone"] {
            min-height: 84px !important;
            padding: 0.85rem 1rem !important;
            border-style: dashed !important;
            border-color: rgba(99, 102, 241, 0.28) !important;
            background: rgba(99, 102, 241, 0.03) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(99, 102, 241, 0.5) !important;
            background: rgba(99, 102, 241, 0.06) !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell [data-testid="stFileUploaderDropzoneInstructions"] {
            font-size: 0.92rem !important;
        }
        /* Drop the heavy outer card that Streamlit/global CSS gives the
           uploader so it inherits the form-card surface (flatter hierarchy). */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader > section {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        /* ── Required-field asterisks (Job Title + Company Name) ── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_job_title .stTextInput > label::after,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_company_name .stTextInput > label::after {
            content: " *";
            color: #ef4444;
            font-weight: 800;
            margin-left: 1px;
        }

        /* ── Submit button: full primary CTA ────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit {
            margin-top: 1.1rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:hover,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:focus {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
            background-color: #2563eb !important;
            background-image: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
            border: 1px solid transparent !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            letter-spacing: 0.01em !important;
            min-height: 48px !important;
            padding: 0.7rem 1.4rem !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 22px rgba(37, 99, 235, 0.32) !important;
            transition: transform 0.12s ease, box-shadow 0.18s ease !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button p {
            color: #ffffff !important;
            background: transparent !important;
            background-color: transparent !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.4) !important;
        }
        /* Disabled state: muted gradient, no hover lift, not-allowed cursor.
           Doubled specificity outranks the unscoped global button rules. */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:disabled,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button[disabled],
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:disabled:hover {
            background: linear-gradient(135deg, #94a3b8 0%, #cbd5e1 100%) !important;
            background-color: #94a3b8 !important;
            background-image: linear-gradient(135deg, #94a3b8 0%, #cbd5e1 100%) !important;
            color: #ffffff !important;
            box-shadow: none !important;
            transform: none !important;
            cursor: not-allowed !important;
            opacity: 0.85 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button:disabled *,
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-cover_letter_submit button[disabled] * {
            color: #ffffff !important;
            background: transparent !important;
        }

        /* ── Success card ───────────────────────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-success-card {
            margin: 1.1rem 0 0.6rem;
            padding: 1rem 1.25rem;
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.10), rgba(16, 185, 129, 0.04));
            border: 1px solid rgba(34, 197, 94, 0.32);
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.08);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-success-head {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-success-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: #22c55e;
            color: #fff;
            font-weight: 800;
            font-size: 1rem;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.35);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-success-title {
            margin: 0;
            font-weight: 700;
            color: var(--text-primary);
            font-size: 1rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-success-sub {
            margin: 0.1rem 0 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        /* ── Tips card ──────────────────────────────────────────── */
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-section {
            margin-top: 1.4rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-left: 3px solid rgba(99, 102, 241, 0.55);
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 1px 2px var(--shadow);
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-head {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.6rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-icon {
            font-size: 1.15rem;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-card h4 {
            margin: 0;
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 700;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-list {
            margin: 0;
            padding: 0 0 0 1.1rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.7;
        }
        [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cl-tips-list li {
            margin: 0 0 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cover_letter_page() -> None:
    """Render the independent cover letter page."""
    user = get_session_user()
    saved_cvs = _load_user_saved_cvs(user.get("id", "") if user else "")

    with st.container(key="cover_letter_page_shell"):
        _inject_styles()
        st.session_state.setdefault(_STATE_RESULT, None)
        st.session_state.setdefault(_STATE_ERROR, "")
        st.session_state.setdefault(_STATE_SUCCESS, "")
        icon_uri = _cover_letter_icon_data_uri()
        icon_markup = (
            f'<img class="cover-letter-inline-icon" src="{icon_uri}" alt="Cover letter icon" />'
            if icon_uri
            else ""
        )

        with st.container(key="compare_form_box"):
            st.markdown(
                f"""
                <div class="landing-clean-head cover-letter-inline-head">
                    <div class="cover-letter-inline-row">
                        {icon_markup}
                        <div class="cover-letter-inline-copy">
                            <h2 class="landing-clean-title">AI Cover Letter Generator</h2>
                            <p class="landing-clean-subtitle">
                                Tailor a professional cover letter to a specific role in three quick steps.
                            </p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ── Step 1: Resume ────────────────────────────────────
            _render_section_heading(
                1,
                "Your resume",
                "Upload a PDF / DOCX, or reuse a CV you've already built.",
            )

            chosen_saved_cv_id: str = ""
            if saved_cvs:
                source_choice = st.radio(
                    "Resume source",
                    options=[_RESUME_SOURCE_UPLOAD, _RESUME_SOURCE_SAVED],
                    key="cover_letter_resume_source",
                    horizontal=True,
                    label_visibility="collapsed",
                )
            else:
                source_choice = _RESUME_SOURCE_UPLOAD

            uploaded_cv = None
            if source_choice == _RESUME_SOURCE_SAVED and saved_cvs:
                cv_labels = {f"{cv.title} · {cv.template.title()}": cv.id for cv in saved_cvs}
                pick = st.selectbox(
                    "Pick a saved CV",
                    options=list(cv_labels.keys()),
                    key="cover_letter_saved_cv_pick",
                )
                chosen_saved_cv_id = cv_labels.get(pick, "")
            else:
                uploaded_cv = st.file_uploader(
                    "Upload your CV (PDF or DOCX)",
                    type=["pdf", "docx"],
                    key="cover_letter_cv",
                    help=f"Maximum file size: {MAX_FILE_MB}MB.",
                )

            # ── Step 2: Target role ───────────────────────────────
            _render_section_heading(
                2,
                "Target role",
                "Who are you applying to, and how did you discover the opening?",
            )
            col_title, col_company = st.columns(2, gap="medium")
            with col_title:
                # Asterisk is added via the cl-required-star CSS rule below so
                # the red color renders independently of label text.
                job_title = st.text_input(
                    "Job Title",
                    key="cover_letter_job_title",
                    placeholder="e.g., Full Stack Developer",
                )
            with col_company:
                company_name = st.text_input(
                    "Company Name",
                    key="cover_letter_company_name",
                    placeholder="e.g., Google",
                )
            source_pick = st.selectbox(
                "How did you find this role? (Optional)",
                options=_SOURCE_OPTIONS,
                index=None,
                placeholder="Choose a source…",
                key="cover_letter_source_choice",
            )
            source_other = ""
            if source_pick == "Other":
                source_other = st.text_input(
                    "Source details",
                    key="cover_letter_source_other",
                    placeholder="Please specify source",
                    label_visibility="collapsed",
                )

            # ── Step 3: Tailoring ─────────────────────────────────
            _render_section_heading(
                3,
                "Tailor it (optional)",
                "More context yields better personalization — paste the JD and add any specifics.",
            )
            with st.container(key="cl_jd_textarea_box"):
                job_description = st.text_area(
                    "Job Description",
                    key="cover_letter_job_description",
                    height=180,
                    placeholder="Paste the job description here to better tailor the letter…",
                )
                jd_chars = len(job_description or "")
                # The counter is always rendered (JS will move it into the
                # textarea wrapper and toggle visibility on input). Initial
                # state mirrors the server-side count for the first paint
                # before the input listener fires.
                jd_low = jd_chars < 300
                init_class = " cl-char-count-overlay--low" if (jd_chars > 0 and jd_low) else ""
                init_style = "display:none;" if jd_chars == 0 else ""
                st.markdown(
                    f'<div class="cl-char-count-overlay{init_class}" style="{init_style}">'
                    f"{jd_chars}/300</div>",
                    unsafe_allow_html=True,
                )
                # 1) Move overlay into the textarea wrapper so its absolute
                #    positioning is measured against the textarea itself.
                # 2) Hide the now-empty element container the overlay was
                #    rendered into (otherwise it leaves a vertical gap).
                # 3) Bind an ``input`` listener so the count updates on every
                #    keystroke instead of only on Streamlit reruns (which
                #    happen on blur / Enter / Tab — not while typing).
                components.html(
                    """<script>
(function () {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;
    function setup() {
        var box = doc.querySelector('.st-key-cl_jd_textarea_box');
        if (!box) return false;
        var ta_wrap = box.querySelector('[data-testid="stTextArea"]');
        var overlay = box.querySelector('.cl-char-count-overlay');
        if (!ta_wrap || !overlay) return false;
        ta_wrap.style.position = 'relative';
        var ta_outer = ta_wrap.closest('[data-testid="stElementContainer"]');
        if (overlay.parentElement !== ta_wrap) {
            // Hide the now-empty element-container that originally wrapped
            // the overlay markdown, so the parent vertical block doesn't
            // leave a flex-gap below the textarea.
            var orig_outer = overlay.closest('[data-testid="stElementContainer"]');
            if (orig_outer && orig_outer !== ta_outer) {
                orig_outer.style.display = 'none';
            }
            ta_wrap.appendChild(overlay);
        }
        var textarea = ta_wrap.querySelector('textarea');
        if (textarea && !textarea.__cl_count_bound) {
            textarea.__cl_count_bound = true;
            var update = function () {
                var len = (textarea.value || '').length;
                if (len === 0) {
                    overlay.style.display = 'none';
                    return;
                }
                overlay.style.display = '';
                overlay.textContent = len + '/300';
                if (len < 300) {
                    overlay.classList.add('cl-char-count-overlay--low');
                } else {
                    overlay.classList.remove('cl-char-count-overlay--low');
                }
            };
            textarea.addEventListener('input', update);
            // Sync once on bind — guarantees the overlay matches the textarea
            // even if Python's initial render disagrees (rare but possible
            // on the very first paint while session state is hydrating).
            update();
        }
        return true;
    }
    if (!setup()) {
        var tries = 0;
        var iv = setInterval(function () {
            tries += 1;
            if (setup() || tries > 30) {
                w.clearInterval(iv);
            }
        }, 30);
    }
})();
</script>""",
                    height=0,
                )

            additional_info = st.text_area(
                "Additional Information (Optional)",
                key="cover_letter_additional_info",
                height=120,
                placeholder=(
                    "Specific achievements, projects, or tone notes you want emphasised."
                ),
            )

            # Disable Generate until both required fields and a CV are present.
            # Server-side validate_form_inputs() is still the source of truth —
            # this is just a UX guard so the user doesn't waste a click.
            cv_present = (
                (source_choice == _RESUME_SOURCE_UPLOAD and uploaded_cv is not None)
                or (source_choice == _RESUME_SOURCE_SAVED and bool(chosen_saved_cv_id))
            )
            can_submit = bool(job_title.strip()) and bool(company_name.strip()) and cv_present
            if can_submit:
                disabled_help = None
            else:
                missing = []
                if not job_title.strip():
                    missing.append("Job Title")
                if not company_name.strip():
                    missing.append("Company Name")
                if not cv_present:
                    missing.append("a CV")
                disabled_help = "Required to continue: " + ", ".join(missing) + "."
            submitted = st.button(
                "Generate cover letter",
                width="stretch",
                key="cover_letter_submit",
                type="primary",
                disabled=not can_submit,
                help=disabled_help,
            )

        # ── Submit handling ───────────────────────────────────────
        if submitted:
            st.session_state[_STATE_ERROR] = ""
            st.session_state[_STATE_SUCCESS] = ""
            st.session_state[_STATE_RESULT] = None

            resolved_cv = None
            if source_choice == _RESUME_SOURCE_SAVED and saved_cvs:
                if not chosen_saved_cv_id:
                    st.session_state[_STATE_ERROR] = "Please pick a saved CV."
                else:
                    saved = next((c for c in saved_cvs if c.id == chosen_saved_cv_id), None)
                    if saved is None:
                        st.session_state[_STATE_ERROR] = "Saved CV not found. Please pick another."
                    else:
                        try:
                            pdf_bytes = generate_cv_pdf(saved.data, saved.template)
                        except Exception:
                            pdf_bytes = b""
                        if not pdf_bytes:
                            st.session_state[_STATE_ERROR] = (
                                "Could not render the saved CV to PDF. Upload a fresh file instead."
                            )
                        else:
                            file_name = f"{(saved.title or 'resume').strip().replace(' ', '_')}.pdf"
                            resolved_cv = _SavedCVUpload(file_name, pdf_bytes)
            else:
                if uploaded_cv is None:
                    st.session_state[_STATE_ERROR] = "Please upload your CV."
                elif getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
                    st.session_state[_STATE_ERROR] = (
                        f"{getattr(uploaded_cv, 'name', 'Uploaded file')} is too large. Max {MAX_FILE_MB}MB."
                    )
                else:
                    resolved_cv = uploaded_cv

            if resolved_cv is not None and not st.session_state[_STATE_ERROR]:
                try:
                    with st.spinner("Generating personalized cover letter…"):
                        application_source = ""
                        if source_pick == "Other":
                            application_source = source_other.strip()
                        elif source_pick:
                            application_source = source_pick
                        result = generate_cover_letter(
                            uploaded_cv=resolved_cv,
                            job_title=job_title,
                            company_name=company_name,
                            job_description=job_description,
                            additional_information=additional_info,
                            application_source=application_source,
                        )
                    st.session_state[_STATE_RESULT] = result
                    st.session_state[_STATE_SUCCESS] = "Cover letter generated successfully! Download is ready."
                except (RuntimeError, ValueError) as exc:
                    st.session_state[_STATE_ERROR] = str(exc)
                except Exception:
                    st.session_state[_STATE_ERROR] = "Something went wrong while generating the cover letter."

        # ── Result + tips (kept inside the shell so scoped CSS hits) ──
        error_msg = str(st.session_state.get(_STATE_ERROR, "") or "")
        success_msg = str(st.session_state.get(_STATE_SUCCESS, "") or "")
        result_obj = st.session_state.get(_STATE_RESULT)

        if error_msg:
            st.error(error_msg)
        if success_msg and isinstance(result_obj, CoverLetterResult):
            _render_success_card(result_obj)

        _render_tips_card()
