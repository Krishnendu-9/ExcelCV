"""AI generation logic for cover letters."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

import google.generativeai as genai

from src.config import get_api_key, preferred_models
from src.cover_letter.models import CoverLetterDraft, CoverLetterRequest
from src.cover_letter.validators import validate_draft_quality


def _normalize_model_name(name: str) -> str:
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
        for part in (getattr(content, "parts", []) if content is not None else []):
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
            parsed = json.loads(raw if raw.strip().startswith("{") else _extract_json_from_text(raw))
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Invalid non-object JSON returned by model.")
        except Exception as exc:
            if idx < attempts - 1:
                time.sleep(1.0 + idx)
                continue
            raise exc
    raise RuntimeError("Unexpected generation failure")


def _build_prompt(req: CoverLetterRequest) -> str:
    jd_text = req.job_description.strip() or "Not provided."
    add_text = req.additional_information.strip() or "Not provided."
    source_text = req.application_source.strip() or "Not provided."
    cv_text = re.sub(r"\s+", " ", req.cv_text.strip())[:9000]
    name_line = req.candidate_name.strip() or "Candidate"

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
- Candidate Name: {req.candidate_name.strip() or "Not provided"}
- Job Title: {req.job_title.strip()}
- Company Name: {req.company_name.strip()}
- Application Source: {source_text}
- Job Description: {jd_text}
- Additional Information: {add_text}
- CV Text: {cv_text}
"""


def generate_cover_letter_draft(req: CoverLetterRequest) -> CoverLetterDraft:
    """Generate a structured cover letter draft using Gemini."""
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
