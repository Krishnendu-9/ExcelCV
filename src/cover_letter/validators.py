"""Validation and quality checks for cover letter generation."""

from __future__ import annotations

import re
from pathlib import Path

_PLACEHOLDER_PATTERNS = [
    re.compile(r"\[[^\]]{2,120}\]"),  # e.g. [Company Address]
    re.compile(r"<[^>]{2,120}>"),  # e.g. <insert something>
    re.compile(r"\b(?:lorem ipsum|to whom it may concern)\b", re.I),
]


# Length caps for the short free-text fields, from what each field is for. Over-long
# values are rejected with a message, never cut, like the CV and job description.
#   Job title: one line, used in "Subject: Application for <title> Position". Long real
#     titles ("Senior Staff Software Engineer, Machine Learning Infrastructure") run to
#     about 65 characters.
#   Company: a name. Long legal names ("The Hongkong and Shanghai Banking Corporation
#     Limited") run to about 55 characters.
#   Both use 120, the cap the app already applies to role and company for AI bullet
#     suggestions, which is about twice the longest real value.
#   Source: a site name or a short referral phrase ("Referral from Jane Smith at Acme"),
#     turned into one sentence of the letter. 100 is several times the longest such phrase.
#   Additional information: notes for a letter capped at 420 words (about 2,500
#     characters). 2,000 characters (roughly 300 words) is most of a letter and matches
#     the cap on context for AI bullet suggestions; more notes than that cannot all be used.
#   Candidate name is not typed by the user; it is guessed from the CV (lines of at most
#     60 characters) or the upload's file name, which the client supplies. 60 bounds both.
MAX_CANDIDATE_NAME_CHARS = 60
MAX_JOB_TITLE_CHARS = 120
MAX_COMPANY_NAME_CHARS = 120
MAX_APPLICATION_SOURCE_CHARS = 100
MAX_ADDITIONAL_INFO_CHARS = 2000

_FIELD_CAPS = (
    ("Job title", "job_title", MAX_JOB_TITLE_CHARS),
    ("Company name", "company_name", MAX_COMPANY_NAME_CHARS),
    ("Application source", "application_source", MAX_APPLICATION_SOURCE_CHARS),
    ("Additional information", "additional_information", MAX_ADDITIONAL_INFO_CHARS),
)


def validate_text_field_lengths(
    *,
    job_title: str,
    company_name: str,
    application_source: str,
    additional_information: str,
) -> None:
    """Raise ValueError naming the first free-text field that is over its cap."""
    values = {
        "job_title": job_title,
        "company_name": company_name,
        "application_source": application_source,
        "additional_information": additional_information,
    }
    for label, key, cap in _FIELD_CAPS:
        length = len((values[key] or "").strip())
        if length > cap:
            raise ValueError(
                f"{label} is too long ({length} characters). "
                f"Please keep it under {cap} characters."
            )


def validate_form_inputs(
    job_title: str,
    company_name: str,
    uploaded_file_name: str,
    cv_text: str,
) -> None:
    """Validate request data; raise ValueError for user-facing issues."""
    if not job_title.strip():
        raise ValueError("Please enter the job title.")
    if not company_name.strip():
        raise ValueError("Please enter the company name.")
    if not uploaded_file_name.strip():
        raise ValueError("Please upload your CV.")

    ext = Path(uploaded_file_name).suffix.lower()
    if ext not in {".pdf", ".docx"}:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX CV.")

    if not cv_text.strip():
        raise ValueError("Could not extract text from your CV. Please upload a readable file.")

    if len(cv_text.strip()) < 120:
        raise ValueError("The uploaded CV has too little readable text. Please try another file.")


def contains_placeholder_text(text: str) -> bool:
    """Return True if output likely contains unresolved placeholders."""
    value = text or ""
    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(value):
            return True
    return False


def validate_draft_quality(
    *,
    subject: str,
    greeting: str,
    paragraphs: list[str],
    closing: str,
    signature_name: str,
) -> None:
    """Validate structure and content quality of generated draft."""
    if not subject.strip():
        raise ValueError("Generated letter is missing a subject line.")
    if not greeting.strip():
        raise ValueError("Generated letter is missing a greeting.")
    if not closing.strip():
        raise ValueError("Generated letter is missing a closing line.")
    if not signature_name.strip():
        raise ValueError("Generated letter is missing a signature name.")
    if len(paragraphs) < 3:
        raise ValueError("Generated letter is too short. Please try again.")

    full_body = "\n".join(paragraphs)
    if contains_placeholder_text(subject) or contains_placeholder_text(full_body):
        raise ValueError("Generated letter contains unresolved placeholders. Please try again.")
