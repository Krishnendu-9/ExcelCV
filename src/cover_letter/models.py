"""Data models for the cover letter feature."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CoverLetterRequest:
    """Normalized cover letter generation request."""

    cv_text: str
    job_title: str
    company_name: str
    job_description: str = ""
    additional_information: str = ""
    application_source: str = ""
    source_file_name: str = ""
    candidate_name: str = ""
    candidate_email: str = ""
    candidate_phone: str = ""
    candidate_location: str = ""


@dataclass
class CoverLetterDraft:
    """Structured AI output used to render preview/docx."""

    subject: str
    greeting: str
    paragraphs: List[str]
    closing: str
    signature_name: str


@dataclass
class CoverLetterResult:
    """Final output payload for UI download + preview."""

    file_name: str
    docx_bytes: bytes
    full_text: str
    structured: Dict[str, Any]
