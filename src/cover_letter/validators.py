"""Validation and quality checks for cover letter generation."""

from __future__ import annotations

import re
from pathlib import Path

_PLACEHOLDER_PATTERNS = [
    re.compile(r"\[[^\]]{2,120}\]"),  # e.g. [Company Address]
    re.compile(r"<[^>]{2,120}>"),  # e.g. <insert something>
    re.compile(r"\b(?:lorem ipsum|to whom it may concern)\b", re.I),
]


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
