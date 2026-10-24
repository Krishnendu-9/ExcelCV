"""AI generation logic for cover letters."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

import google.generativeai as genai

from src import gemini_client, prompt_fence
from src.config import get_api_key, preferred_models
from src.cover_letter.models import CoverLetterDraft, CoverLetterRequest
from src.cover_letter.validators import (
    MAX_ADDITIONAL_INFO_CHARS,
    MAX_APPLICATION_SOURCE_CHARS,
    MAX_CANDIDATE_NAME_CHARS,
    MAX_COMPANY_NAME_CHARS,
    MAX_JOB_TITLE_CHARS,
    validate_draft_quality,
    validate_text_field_lengths,
)


def _normalize_model_name(name: str | None) -> str:
    model = (name or "").strip()
    if not model:
        return ""
    if model.startswith("models/"):
        return model
    if model.startswith("gemini-"):
        return f"models/{model}"
    return model


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", "") or ""
    if text.strip():
        return text.strip()

    collected: List[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) if content is not None else []:
            part_text = getattr(part, "text", "") or ""
            if part_text.strip():
                collected.append(part_text.strip())
    return "\n".join(collected).strip()


def _extract_json_from_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"```(?:json)?\s*\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return ""


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "resource exhausted" in msg or "rate limit" in msg


def _quota_message(exc: Exception) -> str:
    msg = str(exc)
    sec_match = re.search(r"retry in ([\d.]+)s", msg, re.I)
    if sec_match:
        sec = int(float(sec_match.group(1))) + 1
        return f"Gemini API rate limit reached. Please wait about {sec} seconds and try again."
    return "Gemini API quota exceeded. Please try again later."


def _generate_json(model_name: str, prompt: str) -> Dict[str, Any]:
    model = genai.GenerativeModel(model_name)
    attempts = 2
    for idx in range(attempts):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.35,
                    top_p=0.9,
                    response_mime_type="application/json",
                ),
            )
            raw = _extract_response_text(response)
            parsed = json.loads(
                raw if raw.strip().startswith("{") else _extract_json_from_text(raw)
            )
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Invalid non-object JSON returned by model.")
        except Exception as exc:
            if idx < attempts - 1:
                time.sleep(1.0 + idx)
                continue
            raise exc
    raise RuntimeError("Unexpected generation failure")


def _build_prompt(req: CoverLetterRequest, delimiter: str = "") -> str:
    """Build the cover-letter prompt, fencing the CV and JD with a random delimiter.

    A fresh delimiter is generated per call unless one is passed (tests pass one).
    """
    delimiter = delimiter or prompt_fence.new_delimiter()
    jd_text = (
        prompt_fence.sanitize_untrusted(
            req.job_description, gemini_client.max_jd_input_chars(), delimiter=delimiter
        )
        or "Not provided."
    )
    # The short fields are validated in generate_cover_letter_draft(); slicing here only
    # keeps the prompt bounded if the builder is ever called without that check.
    job_title = req.job_title.strip()[:MAX_JOB_TITLE_CHARS]
    company_name = req.company_name.strip()[:MAX_COMPANY_NAME_CHARS]
    candidate_name = req.candidate_name.strip()[:MAX_CANDIDATE_NAME_CHARS]
    add_text = req.additional_information.strip()[:MAX_ADDITIONAL_INFO_CHARS] or "Not provided."
    source_text = req.application_source.strip()[:MAX_APPLICATION_SOURCE_CHARS] or "Not provided."
    # Same rule as the analysis prompt: the prompt cap is the validation cap, so an
    # accepted CV reaches the model whole and a longer one is rejected, never cut.
    cv_text = prompt_fence.sanitize_untrusted(
        req.cv_text, gemini_client.max_cv_input_chars(), delimiter=delimiter
    )
    name_line = candidate_name or "Candidate"
    untrusted_notice = prompt_fence.untrusted_input_notice(delimiter)
    jd_block = prompt_fence.fence("JOB_DESCRIPTION", jd_text, delimiter)
    cv_block = prompt_fence.fence("CV", cv_text, delimiter)

    return f"""
You are an expert career writing assistant.
Generate a professional, personalized cover letter and return ONLY valid JSON.

STRICT OUTPUT JSON SCHEMA:
{{
  "subject": "Subject: Application for <Job Title> Position",
  "greeting": "Dear Hiring Manager,",
  "paragraphs": ["p1", "p2", "p3", "p4"],
  "closing": "Sincerely,",
  "signature_name": "{name_line}"
}}

RULES:
1. Keep letter between 280 and 420 words.
2. Use natural, human tone (not robotic), business professional.
3. Use CV evidence; do not invent fake facts.
4. If Job Description is provided, tailor strongly to it.
5. If Additional Information is provided, include it naturally.
6. If Application Source is provided, add exactly one concise sentence in the opening about it.
7. If Application Source is not provided, do NOT mention "as advertised on..." or any source sentence.
8. NEVER include placeholders like [Company Address], [Platform], <...>.
9. Do not use markdown, bullet points, or headings in paragraphs.

INPUTS:
- Candidate Name: {candidate_name or "Not provided"}
- Job Title: {job_title}
- Company Name: {company_name}
- Application Source: {source_text}
- Additional Information: {add_text}
- Job Description and CV Text: in the fenced blocks below.

{untrusted_notice}

{jd_block}

{cv_block}
"""


def generate_cover_letter_draft(req: CoverLetterRequest) -> CoverLetterDraft:
    """Generate a structured cover letter draft using Gemini."""
    # Same GEMINI_MAX_CV_CHARS / GEMINI_MAX_JD_CHARS caps as CV analysis, checked
    # before any API setup.
    gemini_client.validate_cv_length(req.cv_text)
    gemini_client.validate_job_description_length(req.job_description)
    validate_text_field_lengths(
        job_title=req.job_title,
        company_name=req.company_name,
        application_source=req.application_source,
        additional_information=req.additional_information,
    )
    # Every Gemini path is metered by the same per-user limit; checked after the free
    # length checks so a rejected input never spends a slot.
    gemini_client.enforce_rate_limit()
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY. Set it in your .env file.")
    genai.configure(api_key=api_key)

    candidates = [_normalize_model_name(m) for m in preferred_models()]
    candidates = [m for m in candidates if m]
    prompt = _build_prompt(req)

    last_exc: Exception | None = None
    payload: Dict[str, Any] | None = None
    for model_name in candidates:
        try:
            payload = _generate_json(model_name, prompt)
            break
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            last_exc = exc
            continue

    if payload is None:
        if last_exc and _is_quota_error(last_exc):
            raise RuntimeError(_quota_message(last_exc)) from last_exc
        raise RuntimeError("Could not generate cover letter right now. Please try again.")

    subject = str(payload.get("subject", "")).strip()
    greeting = str(payload.get("greeting", "Dear Hiring Manager,")).strip()
    paragraphs = [str(p).strip() for p in payload.get("paragraphs", []) if str(p).strip()]
    closing = str(payload.get("closing", "Sincerely,")).strip()
    signature_name = str(payload.get("signature_name", "")).strip() or req.candidate_name.strip()

    validate_draft_quality(
        subject=subject,
        greeting=greeting,
        paragraphs=paragraphs,
        closing=closing,
        signature_name=signature_name,
    )

    return CoverLetterDraft(
        subject=subject,
        greeting=greeting,
        paragraphs=paragraphs,
        closing=closing,
        signature_name=signature_name,
    )
