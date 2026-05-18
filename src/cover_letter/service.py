"""Service orchestrator for the cover letter page."""

from __future__ import annotations

import re
from pathlib import Path

from src.cover_letter.docx_builder import build_cover_letter_docx
from src.cover_letter.generator import generate_cover_letter_draft
from src.cover_letter.models import CoverLetterRequest, CoverLetterResult
from src.cover_letter.validators import validate_form_inputs
from src.pdf_utils import extract_cv_text
from src.services.scoring import calculate_contact_info
from src.ui.app_utils import _sanitize_cv_filename

_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _guess_candidate_name(cv_text: str, file_name: str) -> str:
    lines = [line.strip() for line in (cv_text or "").splitlines() if line.strip()]
    for line in lines[:25]:
        clean = re.sub(r"\s+", " ", line).strip(" -|,")
        if len(clean) < 3 or len(clean) > 60:
            continue
        if _EMAIL_RE.search(clean) or _PHONE_RE.search(clean):
            continue
        if re.search(r"\b(?:experience|education|skills|summary|project|contact)\b", clean, re.I):
            continue
        words = clean.split()
        if 2 <= len(words) <= 4 and all(w[:1].isalpha() for w in words):
            return clean

    stem = Path(file_name).stem
    stem = re.sub(r"[_\-.]+", " ", stem).strip()
    if stem:
        return stem.title()
    return "Candidate"


def _guess_candidate_location(cv_text: str) -> str:
    lines = [line.strip() for line in (cv_text or "").splitlines() if line.strip()]
    header_lines = lines[:12]
    for line in header_lines:
        if "," not in line:
            continue
        if _EMAIL_RE.search(line) or _PHONE_RE.search(line):
            continue
        if len(line) > 45:
            continue
        words = re.findall(r"[A-Za-z]+", line)
        if not (1 <= len(words) <= 4):
            continue
        if re.search(
            r"\b(?:engineered|designed|developed|built|managed|implemented|experience|project)\b",
            line,
            re.I,
        ):
            continue
        return line.strip(" -|.")
    return ""


def _sanitize_email_with_name(email: str, candidate_name: str) -> str:
    value = (email or "").strip()
    if not value or "@" not in value:
        return value
    local, _, domain = value.partition("@")
    clean_local = local.strip(" .-_")
    if not clean_local:
        return value

    # Some PDF icon artifacts prepend one stray character to the email local-part.
    # If dropping the first character makes it strongly match the candidate name,
    # prefer that cleaned variant.
    if len(clean_local) >= 4:
        lowered_local = clean_local.lower()
        lowered_trimmed = lowered_local[1:]
        name_tokens = [t.lower() for t in re.findall(r"[a-zA-Z]+", candidate_name or "")]
        name_joined = "".join(name_tokens)
        if name_tokens:
            strong_name_match = (
                (name_joined and lowered_trimmed.startswith(name_joined[: min(len(name_joined), 6)]))
                or any(lowered_trimmed.startswith(token) for token in name_tokens if len(token) >= 4)
            )
            weak_original_match = not (
                (name_joined and lowered_local.startswith(name_joined[: min(len(name_joined), 6)]))
                or any(lowered_local.startswith(token) for token in name_tokens if len(token) >= 4)
            )
            if strong_name_match and weak_original_match:
                clean_local = clean_local[1:]
    return f"{clean_local}@{domain}"


def _guess_candidate_email(cv_text: str, candidate_name: str, contact_found: list[dict]) -> str:
    for item in contact_found:
        if item.get("type") == "email":
            return _sanitize_email_with_name(str(item.get("value", "")), candidate_name)

    # Header-focused fallback: only scan first lines to avoid body noise.
    lines = [line.strip() for line in (cv_text or "").splitlines() if line.strip()]
    header_blob = " ".join(lines[:8])
    match = _EMAIL_RE.search(header_blob)
    if match:
        return _sanitize_email_with_name(match.group(0), candidate_name)
    return ""


def _guess_candidate_phone(cv_text: str, contact_found: list[dict]) -> str:
    for item in contact_found:
        if item.get("type") == "phone":
            return str(item.get("value", "")).strip()

    lines = [line.strip() for line in (cv_text or "").splitlines() if line.strip()]
    header_blob = " ".join(lines[:8])
    match = _PHONE_RE.search(header_blob)
    return match.group(0).strip() if match else ""


def _build_download_name(candidate_name: str, company_name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9]+", "_", candidate_name).strip("_") or "Candidate"
    company = re.sub(r"[^A-Za-z0-9]+", "_", company_name).strip("_") or "Company"
    return f"cover_letter_{name}_{company}.docx"


def generate_cover_letter(
    *,
    uploaded_cv,
    job_title: str,
    company_name: str,
    job_description: str = "",
    additional_information: str = "",
    application_source: str = "",
) -> CoverLetterResult:
    """Generate a cover letter and return docx bytes + metadata."""
    safe_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume.pdf"))
    cv_text = extract_cv_text(uploaded_cv, safe_name)
    validate_form_inputs(
        job_title=job_title,
        company_name=company_name,
        uploaded_file_name=safe_name,
        cv_text=cv_text,
    )

    candidate_name = _guess_candidate_name(cv_text, safe_name)
    contact_info = calculate_contact_info(cv_text)
    contact_found = contact_info.get("found", []) if isinstance(contact_info, dict) else []
    if not isinstance(contact_found, list):
        contact_found = []

    candidate_location = ""
    for item in contact_found:
        if item.get("type") == "location":
            candidate_location = str(item.get("value", "")).strip()
            break
    if not candidate_location:
        candidate_location = _guess_candidate_location(cv_text)

    req = CoverLetterRequest(
        cv_text=cv_text,
        job_title=job_title.strip(),
        company_name=company_name.strip(),
        job_description=job_description.strip(),
        additional_information=additional_information.strip(),
        application_source=application_source.strip(),
        source_file_name=safe_name,
        candidate_name=candidate_name,
        candidate_email=_guess_candidate_email(cv_text, candidate_name, contact_found),
        candidate_phone=_guess_candidate_phone(cv_text, contact_found),
        candidate_location=candidate_location,
    )

    draft = generate_cover_letter_draft(req)
    file_name = _build_download_name(candidate_name, req.company_name)

    docx_bytes = build_cover_letter_docx(
        candidate_name=req.candidate_name,
        candidate_location=req.candidate_location,
        candidate_email=req.candidate_email,
        candidate_phone=req.candidate_phone,
        company_name=req.company_name,
        subject=draft.subject,
        greeting=draft.greeting,
        paragraphs=draft.paragraphs,
        closing=draft.closing,
        signature_name=draft.signature_name,
    )

    full_text = "\n\n".join(
        [draft.subject, draft.greeting, *draft.paragraphs, draft.closing, draft.signature_name]
    )
    return CoverLetterResult(
        file_name=file_name,
        docx_bytes=docx_bytes,
        full_text=full_text,
        structured={
            "subject": draft.subject,
            "greeting": draft.greeting,
            "paragraphs": draft.paragraphs,
            "closing": draft.closing,
            "signature_name": draft.signature_name,
        },
    )
