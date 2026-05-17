"""Streamlit page renderer for cover letter generation."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.config import MAX_FILE_BYTES, MAX_FILE_MB
from src.cover_letter.models import CoverLetterResult
from src.cover_letter.service import generate_cover_letter


_STATE_RESULT = "cover_letter_result"
_STATE_ERROR = "cover_letter_error"
_STATE_SUCCESS = "cover_letter_success"
_SOURCE_OPTIONS = [
    "Select (optional)",
    "LinkedIn",
    "Company Careers Page",
    "Employee Referral",
    "Recruiter Outreach",
    "Campus Placement",
    "Other",
]


def _cover_letter_icon_data_uri() -> str:
    icon_path = Path(__file__).resolve().parents[1] / "assets" / "images" / "cover-letter.png"
    if not icon_path.exists():
        return ""
    try:
        encoded = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:image/png;base64,{encoded}"


def _render_tips_card() -> None:
    st.markdown(
        """
        <section class="landing-clean-section">
            <article class="landing-clean-card">
                <h4>💡 Tips for best results:</h4>
                <p>- Make sure your CV is up-to-date and well-formatted</p>
                <p>- Include the complete job description for better personalization</p>
                <p>- Mention any specific achievements you want highlighted</p>
                <p>- Review and customize the generated letter before sending</p>
            </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_preview(result: CoverLetterResult) -> None:
    with st.expander("Preview generated letter", expanded=False):
        st.text_area(
            "Generated cover letter",
            value=result.full_text,
            height=280,
            key="cover_letter_preview_text",
            disabled=True,
        )


def render_cover_letter_page() -> None:
    """Render the independent cover letter page."""
    with st.container(key="cover_letter_page_shell"):
        st.markdown(
            """
            <style>
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput > label,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > label {
                font-size: 1.06rem !important;
                font-weight: 700 !important;
                color: var(--text-primary) !important;
                margin-bottom: 0.35rem !important;
            }
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput > label p,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > label p {
                font-size: 1.06rem !important;
                font-weight: 700 !important;
                color: var(--text-primary) !important;
            }
            /* Remove compare-card wrappers for textareas on this page only so they
               look like normal form fields (same style family as Job Title/Company). */
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
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea > label p,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .st-key-compare_form_box .stTextArea label p {
                font-size: 1.06rem !important;
                font-weight: 700 !important;
                color: var(--text-primary) !important;
                margin: 0 !important;
            }
            /* Match Job Description hover/focus treatment on Job Title + Company Name. */
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput [data-baseweb="input"]:hover,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stTextInput [data-baseweb="input"]:focus-within {
                background: var(--excelcv-uniform-hover-bg) !important;
                border-color: var(--excelcv-uniform-hover-border) !important;
                box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            }
            /* Hide combobox caret (text cursor) in source select field. */
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox input {
                caret-color: transparent !important;
            }
            /* Global theme applies border/background to select's internal input;
               neutralize it here to remove the tiny box beside selected text. */
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox [data-baseweb="select"] input,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stSelectbox > div > div > div input {
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                outline: none !important;
                padding: 0 !important;
            }
            /* Uploaded-file remove icon: keep it plain (no nested white box). */
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
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:hover,
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .stFileUploader [data-testid="stFileUploaderFile"] button:focus-visible {
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
            [data-testid="stAppViewContainer"] .st-key-cover_letter_page_shell .cover-letter-inline-head {
                margin: 0 0 0.85rem 0;
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
            </style>
            """,
            unsafe_allow_html=True,
        )
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
                                 Generate a professional cover letter from your CV and target role details.
                            </p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            uploaded_cv = st.file_uploader(
                "Upload Your CV (PDF or DOCX)",
                type=["pdf", "docx"],
                key="cover_letter_cv",
                help=f"Maximum file size: {MAX_FILE_MB}MB.",
            )
            job_title = st.text_input(
                "Job Title *",
                key="cover_letter_job_title",
                placeholder="e.g., Full Stack Developer",
            )
            company_name = st.text_input(
                "Company Name *",
                key="cover_letter_company_name",
                placeholder="e.g., Google",
            )
            source_choice = st.selectbox(
                "How did you find this role? (Optional)",
                options=_SOURCE_OPTIONS,
                key="cover_letter_source_choice",
            )
            source_other = ""
            if source_choice == "Other":
                source_other = st.text_input(
                    "Source details",
                    key="cover_letter_source_other",
                    placeholder="Please specify source",
                    label_visibility="collapsed",
                )
            job_description = st.text_area(
                "Job Description",
                key="cover_letter_job_description",
                height=170,
                placeholder="Paste the job description here to better tailor the letter...",
            )
            additional_info = st.text_area(
                "Additional Information (Optional)",
                key="cover_letter_additional_info",
                height=130,
                placeholder=(
                    "Any specific points to highlight. "
                    "Please add: How did you find this role? "
                    "(e.g., LinkedIn, employee referral, hiring manager outreach)"
                ),
            )
            submitted = st.button("Generate & Direct Download", width="stretch", key="cover_letter_submit")

    if submitted:
        st.session_state[_STATE_ERROR] = ""
        st.session_state[_STATE_SUCCESS] = ""
        st.session_state[_STATE_RESULT] = None

        if uploaded_cv is None:
            st.session_state[_STATE_ERROR] = "Please upload your CV."
        elif getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
            st.session_state[_STATE_ERROR] = (
                f"{getattr(uploaded_cv, 'name', 'Uploaded file')} is too large. Max {MAX_FILE_MB}MB."
            )
        else:
            try:
                with st.spinner("Generating personalized cover letter..."):
                    application_source = ""
                    if source_choice == "Other":
                        application_source = source_other.strip()
                    elif source_choice != "Select (optional)":
                        application_source = source_choice
                    result = generate_cover_letter(
                        uploaded_cv=uploaded_cv,
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

    error_msg = str(st.session_state.get(_STATE_ERROR, "") or "")
    success_msg = str(st.session_state.get(_STATE_SUCCESS, "") or "")
    result_obj = st.session_state.get(_STATE_RESULT)

    if error_msg:
        st.error(error_msg)
    if success_msg and isinstance(result_obj, CoverLetterResult):
        st.success(success_msg)
        st.download_button(
            "Generate & Direct Download",
            data=result_obj.docx_bytes,
            file_name=result_obj.file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
            key="cover_letter_download_btn",
            type="primary",
            on_click="ignore",
        )
        _render_preview(result_obj)

    _render_tips_card()
