"""
Gemini Client Module

This module handles communication with Google Gemini AI for CV analysis.
It orchestrates AI analysis and blends it with programmatic scoring calculations.
"""

import json
import logging
import os
import re
import threading
import time
from functools import lru_cache
from json import JSONDecodeError
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from src import prompt_fence
from src.config import MAX_FILE_BYTES, get_api_key, preferred_models
from src.services.career_tools import (
    build_interview_prep_questions,
    build_learning_roadmap,
    build_portfolio_checklist,
    build_priority_action_plan,
    build_recruiter_snapshot,
)
from src.services.scoring import (
    build_jd_skill_matrix,
    calculate_ats_essentials,
    calculate_ats_parse_rate,
    calculate_bullets_consistency,
    calculate_contact_info,
    calculate_file_name_quality,
    calculate_final_score_breakdown,
    calculate_quantifying_impact,
    calculate_repetition,
    calculate_sections,
    calculate_sections_order,
    calculate_spelling_grammar,
    calculate_tailoring,
    generate_section_rewrite_recommendations,
    get_metric_status,
    normalize_score,
)
from src.services.scoring_constants import (
    QUANTIFYING_IMPACT_THRESHOLDS,
    REPETITION_THRESHOLDS,
    SPELLING_GRAMMAR_THRESHOLDS,
)

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        value = int(str(os.environ.get(name, str(default))).strip() or str(default))
    except Exception:
        value = default
    return max(minimum, value)


_GEMINI_WINDOW_SECONDS = _env_int("GEMINI_RATE_WINDOW_SECONDS", 60, 10)
_GEMINI_MAX_REQUESTS_PER_WINDOW = _env_int("GEMINI_MAX_REQUESTS_PER_WINDOW", 20, 1)
# Default CV cap: the text of four A4 pages packed edge to edge at 10 pt, which no real
# resume reaches. Everything accepted is sent to the model whole, so this is also the
# prompt cap. Derivation (the values marked "est." are estimates, not measurements):
#   A4 is 595 x 842 pt; with 0.5 in (36 pt) margins the text area is 523 x 770 pt.
#   At 10 pt with an average glyph width of ~0.5 em (est., proportional sans incl.
#   spaces) that is 104 chars per line; at 1.2 line height (est.), 64 lines.
#   104 * 64 = 6,656 chars for a completely full page: an upper bound, since headings,
#   spacing and short lines leave real pages well under it.
#   Four pages (est.: allows a senior three-page resume with room to spare) = 26,624.
_DENSE_PAGE_CHARS = 104 * 64
DEFAULT_MAX_CV_INPUT_CHARS = 4 * _DENSE_PAGE_CHARS
_MAX_CV_INPUT_CHARS = _env_int("GEMINI_MAX_CV_CHARS", DEFAULT_MAX_CV_INPUT_CHARS, 2000)
_MAX_JD_INPUT_CHARS = _env_int("GEMINI_MAX_JD_CHARS", 40000, 1000)


def _file_size_cap() -> int:
    """Return the Gemini file-size guardrail, never above the app's upload cap.

    Streamlit's maxUploadSize and config.MAX_FILE_BYTES (both 2 MB) reject larger files
    before analysis runs, so a higher value here would be unreachable.
    GEMINI_MAX_FILE_SIZE_BYTES can only lower it.
    """
    return min(_env_int("GEMINI_MAX_FILE_SIZE_BYTES", MAX_FILE_BYTES, 1), MAX_FILE_BYTES)


_MAX_FILE_SIZE_BYTES = _file_size_cap()
_ANALYSIS_MAX_OUTPUT_TOKENS = _env_int("GEMINI_ANALYSIS_MAX_OUTPUT_TOKENS", 2400, 256)

_REQUEST_LOCK = threading.Lock()
_REQUEST_BUCKETS: dict[str, list[float]] = {}


def _request_actor_key() -> str:
    """Return a stable best-effort key for per-user/session rate limiting."""
    try:
        import streamlit as st

        user = st.session_state.get("user")
        user_id = str((user or {}).get("id", "")).strip() if isinstance(user, dict) else ""
        if user_id:
            return f"user:{user_id}"

        guest_id = str(st.session_state.get("guest_session_id", "")).strip()
        if guest_id:
            return f"guest:{guest_id}"

        headers = getattr(st.context, "headers", {}) or {}
        forwarded = str(headers.get("X-Forwarded-For", "")).strip()
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
    except Exception:
        pass
    return "global"


def _enforce_gemini_rate_limit() -> None:
    """Raise a user-facing error when request rate exceeds configured window."""
    key = _request_actor_key()
    now_ts = time.time()
    with _REQUEST_LOCK:
        timestamps = [
            ts for ts in _REQUEST_BUCKETS.get(key, []) if now_ts - ts < _GEMINI_WINDOW_SECONDS
        ]
        if len(timestamps) >= _GEMINI_MAX_REQUESTS_PER_WINDOW:
            retry_after = int(_GEMINI_WINDOW_SECONDS - (now_ts - min(timestamps)))
            raise RuntimeError(
                "AI request rate limit reached for this session. "
                f"Please wait about {max(1, retry_after)} seconds and try again."
            )
        timestamps.append(now_ts)
        _REQUEST_BUCKETS[key] = timestamps


def enforce_rate_limit() -> None:
    """Public entry to the per-user Gemini rate limit, for call paths outside this module."""
    _enforce_gemini_rate_limit()


def max_jd_input_chars() -> int:
    """Return the configured job-description cap (GEMINI_MAX_JD_CHARS)."""
    return _MAX_JD_INPUT_CHARS


def validate_job_description_length(job_desc: str) -> None:
    """Raise ValueError when a job description exceeds GEMINI_MAX_JD_CHARS."""
    if len(job_desc or "") > _MAX_JD_INPUT_CHARS:
        raise ValueError(
            f"Job description is too large ({len(job_desc)} chars). "
            f"Please keep it under {_MAX_JD_INPUT_CHARS} characters."
        )


def max_cv_input_chars() -> int:
    """Return the configured CV cap (GEMINI_MAX_CV_CHARS)."""
    return _MAX_CV_INPUT_CHARS


def validate_cv_length(cv_text: str) -> None:
    """Raise ValueError when CV text exceeds GEMINI_MAX_CV_CHARS."""
    if len(cv_text or "") > _MAX_CV_INPUT_CHARS:
        raise ValueError(
            f"CV content is too large ({len(cv_text)} chars). "
            f"Please keep it under {_MAX_CV_INPUT_CHARS} characters."
        )


def _validate_analysis_inputs(cv_text: str, job_desc: str, file_size_bytes: int) -> None:
    validate_cv_length(cv_text)
    validate_job_description_length(job_desc)
    if file_size_bytes and file_size_bytes > _MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Uploaded file is too large ({file_size_bytes} bytes). "
            f"Maximum supported size is {_MAX_FILE_SIZE_BYTES} bytes."
        )


def _is_quota_error(exc: Exception) -> bool:
    """Return True if the exception is a 429 / quota exceeded error."""
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "rate limit" in msg or "resource exhausted" in msg


def _user_friendly_quota_message(exc: Exception) -> str:
    """Build a short, actionable message for quota/429 errors."""
    msg = str(exc)
    if "retry in" in msg.lower() or "retry_delay" in msg.lower():
        # Try to extract seconds (e.g. "Please retry in 43.73746345s" or retry_delay { seconds: 43 })
        sec_match = re.search(r"retry in ([\d.]+)s", msg, re.I) or re.search(
            r"seconds[:\s]*(\d+)", msg, re.I
        )
        if sec_match:
            sec = float(sec_match.group(1))
            if sec <= 120:
                return (
                    "Gemini API rate limit reached. Please wait about {} seconds and try again. "
                    "If you're on the free tier, daily limits also apply - see https://ai.google.dev/gemini-api/docs/rate-limits."
                ).format(int(sec) + 1)
    return (
        "Gemini API quota exceeded. You can try again later, or check your plan and billing at "
        "https://ai.google.dev/gemini-api/docs/rate-limits. Free tier has limited requests per day per model."
    )


def _is_retryable_error(exc: Exception) -> bool:
    """Return True for transient transport/service errors worth retrying."""
    if _is_quota_error(exc):
        return False
    msg = str(exc).lower()
    transient_markers = (
        "timeout",
        "timed out",
        "deadline exceeded",
        "service unavailable",
        "temporarily unavailable",
        "connection reset",
        "connection aborted",
        "internal",
        "500",
        "503",
    )
    return any(marker in msg for marker in transient_markers)


@lru_cache(maxsize=1)
def _pick_model_id() -> str:
    """Pick a working model id by listing available models."""
    default_model = "models/gemini-2.0-flash"
    try:
        models = list(genai.list_models())
        supported_model_names: List[str] = []
        for model in models:
            methods = getattr(model, "supported_generation_methods", []) or []
            model_name = str(getattr(model, "name", "") or "").strip()
            if model_name and "generateContent" in methods:
                supported_model_names.append(model_name)

        if not supported_model_names:
            return default_model

        supported_lookup = set(supported_model_names)
        for preferred in preferred_models():
            normalized = _normalize_model_name(preferred)
            if normalized and normalized in supported_lookup:
                return normalized

        return supported_model_names[0]
    except Exception:
        return default_model


def _extract_json_from_text(text: str) -> str:
    """Extract JSON from text that might be wrapped in markdown code blocks or have extra text."""
    if not text:
        return ""

    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    text = re.sub(r"```(?:json)?\s*\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)

    # Prefer the first *balanced* JSON object to avoid over-capturing when
    # the model adds extra braces before/after the payload.
    balanced = _extract_balanced_json_object(text)
    if balanced:
        return balanced.strip()

    return text.strip()


def _extract_balanced_json_object(text: str) -> str:
    """Return the first balanced JSON object substring from text, if any."""
    start = -1
    depth = 0
    in_string = False
    escaped = False

    for idx, ch in enumerate(text):
        if start == -1:
            if ch == "{":
                start = idx
                depth = 1
                in_string = False
                escaped = False
            continue

        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    return ""


def _load_model_json_payload(raw_text: str) -> Dict[str, Any]:
    """Best-effort parse of model JSON payload; returns {} on failure."""
    json_text = _extract_json_from_text(raw_text)
    if not json_text:
        return {}

    candidate_texts = [json_text]
    # Common model glitch: trailing commas before object/array close.
    candidate_texts.append(re.sub(r",\s*([}\]])", r"\1", json_text))

    for candidate in candidate_texts:
        try:
            parsed = json.loads(candidate)
        except JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _extract_response_text(response: Any) -> str:
    """Safely extract text from Gemini responses across SDK response shapes."""
    text = getattr(response, "text", "") or ""
    if text.strip():
        return text.strip()

    # Fallback shape: response.candidates[].content.parts[].text
    candidates = getattr(response, "candidates", []) or []
    parts_text: List[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", []) if content is not None else []
        for part in parts:
            part_text = getattr(part, "text", "") or ""
            if part_text.strip():
                parts_text.append(part_text.strip())
    return "\n".join(parts_text).strip()


def _normalize_model_name(model: Optional[str]) -> Optional[str]:
    """Ensure model name has the 'models/' prefix if it's a valid model identifier."""
    if not model:
        return None

    model = model.strip()
    # If it doesn't start with 'models/', add it (unless it's already a full path)
    if not model.startswith("models/") and "/" not in model:
        # Check if it looks like a model name (e.g., "gemini-2.0-flash-exp")
        if model.startswith("gemini-"):
            return f"models/{model}"

    return model


def _as_dict(value: Any) -> Dict[str, Any]:
    """Return a dict or an empty dict when value is not a dict."""
    return value if isinstance(value, dict) else {}


def _merge_unique_items(primary: List[str], secondary: List[str], limit: int = 40) -> List[str]:
    """Merge two ordered string lists, preserving order and removing duplicates."""
    out: List[str] = []
    for item in [*primary, *secondary]:
        text = str(item).strip()
        if not text or text in out:
            continue
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _is_informative_term(value: str) -> bool:
    """Return True for terms that are meaningful enough for insights display."""
    text = str(value or "").strip().lower()
    if not text:
        return False
    if len(text) < 4:
        return False
    generic = {
        "role",
        "team",
        "work",
        "skill",
        "skills",
        "project",
        "projects",
        "manager",
        "management",
        "experience",
        "developer",
        "engineer",
        "required",
        "requiring",
        "requirement",
        "requirements",
        "responsibility",
        "responsibilities",
        "qualification",
        "qualifications",
        "candidate",
    }
    return text not in generic


def _is_noise_keyword(value: str) -> bool:
    """Return True for non-skill boilerplate tokens often present in JD prose."""
    text = str(value or "").strip().lower()
    noise = {
        "role",
        "required",
        "requiring",
        "requirement",
        "requirements",
        "responsibility",
        "responsibilities",
        "qualification",
        "qualifications",
        "candidate",
    }
    return text in noise


def _normalize_gap_term(value: str) -> str:
    """Normalize skill/keyword text for overlap checks."""
    text = str(value or "").strip().lower()
    if not text:
        return ""
    # Remove explanatory suffixes like "(partial evidence)".
    text = re.sub(r"\s*\(.*?\)\s*", " ", text)
    text = re.sub(r"[^a-z0-9\+\#/\.\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_overlaps_skills(keyword: str, skills: List[str]) -> bool:
    """Return True when a keyword is effectively already covered by skill gaps."""
    k_norm = _normalize_gap_term(keyword)
    if not k_norm:
        return False
    for skill in skills:
        s_norm = _normalize_gap_term(skill)
        if not s_norm:
            continue
        if k_norm == s_norm:
            return True
        if len(k_norm) >= 5 and k_norm in s_norm:
            return True
        if len(s_norm) >= 5 and s_norm in k_norm:
            return True
    return False


def _derive_deterministic_insight_fallbacks(
    *,
    ats_parse_rate: int,
    sections_score: int,
    contact_info: Dict[str, Any],
    tailoring_score: int,
    has_job_description: bool,
    tailoring_details: Dict[str, Any],
    jd_skill_matrix: List[Dict[str, str]],
    rewrite_recommendations: List[Dict[str, str]],
    quant_score: int,
    repetition_score: int,
    spelling_score: int,
    bullets_score: int,
) -> Dict[str, List[str]]:
    """Build evidence-based insight lists from CV/JD signals."""
    strengths: List[str] = []
    missing_skills: List[str] = []
    missing_keywords: List[str] = []
    suggestions: List[str] = []

    found_matrix_terms: List[str] = []
    missing_matrix_terms: List[str] = []
    partial_matrix_terms: List[str] = []
    found_evidence: Dict[str, str] = {}
    partial_evidence: Dict[str, str] = {}
    for row in jd_skill_matrix:
        status = str(row.get("status", "")).strip().lower()
        skill = str(row.get("skill", "")).strip()
        evidence = str(row.get("evidence", "")).strip()
        if not skill:
            continue
        if not _is_informative_term(skill):
            continue
        if status == "found" and skill not in found_matrix_terms:
            found_matrix_terms.append(skill)
            if evidence and "no direct evidence" not in evidence.lower():
                found_evidence[skill] = evidence
        elif status == "missing" and skill not in missing_matrix_terms:
            missing_matrix_terms.append(skill)
        elif status == "partial" and skill not in partial_matrix_terms:
            partial_matrix_terms.append(skill)
            if evidence and "no direct evidence" not in evidence.lower():
                partial_evidence[skill] = evidence

    if has_job_description and found_matrix_terms:
        strengths.append("Matched JD skills: " + ", ".join(found_matrix_terms[:5]) + ".")
        for skill in found_matrix_terms[:2]:
            evidence = found_evidence.get(skill, "")
            if evidence:
                strengths.append(f'{skill}: evidence in CV - "{evidence}".')
    elif has_job_description and partial_matrix_terms:
        strengths.append(
            "Related JD exposure (partial): " + ", ".join(partial_matrix_terms[:4]) + "."
        )
    elif has_job_description:
        matched_from_tailoring = [
            str(x).strip()
            for x in tailoring_details.get("matched_skills", [])
            if str(x).strip() and _is_informative_term(str(x).strip())
        ][:4]
        if matched_from_tailoring:
            strengths.append(
                "Some role-relevant overlap detected: " + ", ".join(matched_from_tailoring) + "."
            )
        else:
            strengths.append("No strong JD-specific strengths found yet for this role.")
    if ats_parse_rate >= 80:
        strengths.append(f"ATS parse quality is strong ({ats_parse_rate}/100).")
    if sections_score >= 80:
        strengths.append(f"Section structure is solid ({sections_score}/100).")
    if int(contact_info.get("score", 0) or 0) >= 67:
        strengths.append(
            f"Contact completeness is good ({int(contact_info.get('score', 0) or 0)}/100)."
        )
    if has_job_description and tailoring_score >= 75:
        strengths.append(f"Overall JD alignment is strong ({tailoring_score}/100).")
    jd_specificity = tailoring_details.get("jd_specificity", {})
    if isinstance(jd_specificity, dict) and str(jd_specificity.get("status", "")).lower() == "low":
        suggestions.append(
            "The provided job description looks very short/generic. Paste a fuller JD (responsibilities + skills) for accurate tailoring."
        )
    role_baseline = tailoring_details.get("role_baseline", {})
    if isinstance(role_baseline, dict):
        baseline_missing = [
            str(x).strip()
            for x in role_baseline.get("missing", [])
            if str(x).strip() and _is_informative_term(str(x).strip())
        ]
        for skill in baseline_missing:
            if skill not in missing_skills:
                missing_skills.append(skill)
            if len(missing_skills) >= 12:
                break

    for skill in missing_matrix_terms:
        if skill not in missing_skills:
            missing_skills.append(skill)
        if len(missing_skills) >= 12:
            break

    for skill in partial_matrix_terms:
        if skill in missing_skills:
            continue
        evidence = partial_evidence.get(skill, "")
        if evidence:
            missing_skills.append(f'{skill} (partial: "{evidence}")')
        else:
            missing_skills.append(f"{skill} (partial evidence)")
        if len(missing_skills) >= 12:
            break

    mk = tailoring_details.get("missing_keywords", [])
    if isinstance(mk, list):
        for item in mk:
            token = str(item).strip()
            if _is_noise_keyword(token):
                continue
            if _keyword_overlaps_skills(token, missing_skills):
                continue
            if token and token not in missing_keywords:
                missing_keywords.append(token)
            if len(missing_keywords) >= 20:
                break

    # Final fallback: use informative missing keywords as skill gaps.
    if len(missing_skills) < 2 and has_job_description:
        for token in missing_keywords:
            if not _is_informative_term(token):
                continue
            if token in missing_skills:
                continue
            missing_skills.append(token)
            if len(missing_skills) >= 12:
                break

    for rec in rewrite_recommendations[:4]:
        rationale = str(rec.get("rationale", "")).strip()
        if not rationale:
            continue
        text = f"Improve experience bullets: {rationale}."
        if text not in suggestions:
            suggestions.append(text)

    if missing_skills:
        suggestions.append(
            "Add concrete role-specific evidence for these JD skills: "
            + ", ".join(missing_skills[:4])
            + "."
        )
    if missing_keywords:
        suggestions.append(
            "Naturally include missing JD keywords in relevant bullets: "
            + ", ".join(missing_keywords[:5])
            + "."
        )
    if has_job_description and tailoring_score < 70 and missing_skills:
        suggestions.append(
            f"JD alignment is currently {tailoring_score}/100. Prioritize closing the top missing skills first."
        )
    if quant_score < 70:
        suggestions.append(
            f"Quantifying Impact is low ({quant_score}/100). Add measurable outcomes (%, counts, time, revenue)."
        )
    if repetition_score < 80:
        suggestions.append(
            f"Repetition score is {repetition_score}/100. Reduce repeated wording and vary action verbs."
        )
    if spelling_score < 90:
        suggestions.append(
            f"Spelling & Grammar is {spelling_score}/100. Fix language issues for a cleaner professional impression."
        )
    if bullets_score < 80:
        suggestions.append(
            f"Bullets Consistency is {bullets_score}/100. Keep bullets concise and impact-focused."
        )

    return {
        "strengths": _merge_unique_items(strengths, [], limit=8),
        "missing_skills": _merge_unique_items(missing_skills, [], limit=12),
        "missing_keywords": _merge_unique_items(missing_keywords, [], limit=20),
        "suggestions": _merge_unique_items(suggestions, [], limit=12),
    }


def _generate_with_retry(
    model: genai.GenerativeModel, prompt: str, generation_config: Dict[str, Any]
) -> Any:
    """Generate content with a short retry on transient errors."""
    attempts = 2
    for attempt in range(attempts):
        try:
            # Try with JSON response format if supported (for newer models)
            try:
                return model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        **generation_config,
                        response_mime_type="application/json",
                    ),
                )
            except (AttributeError, TypeError, ValueError):
                return model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**generation_config),
                )
        except Exception as exc:
            if attempt < attempts - 1 and _is_retryable_error(exc):
                time.sleep(1.0 + attempt)
                continue
            raise
    raise RuntimeError("Unexpected generation failure")


def _build_analysis_prompt(cv_text: str, job_desc: str, delimiter: str = "") -> str:
    """Build the analysis prompt, fencing the untrusted CV and JD with a random delimiter.

    A fresh delimiter is generated per call unless one is passed (tests pass one).
    """
    analysis_focus = """
You are a career advisor and resume reviewer. Your goal is to provide comprehensive feedback on resume quality, content, and alignment with the job description.

PRIORITY FOCUS:
1. Overall quality: Evaluate resume structure, clarity, professionalism, and presentation
2. Content relevance: Assess how well the resume content matches the job requirements holistically
3. Experience alignment: Compare work history and projects against job requirements
4. Skills assessment: Identify both matching and missing skills, considering transferable skills
5. Improvement suggestions: Provide actionable advice for enhancing the resume

Be BALANCED in scoring. Consider the overall fit and potential, not just exact keyword matches.
"""

    delimiter = delimiter or prompt_fence.new_delimiter()
    # The prompt caps are the validation caps: text that passes _validate_analysis_inputs
    # reaches the model whole, and text over a cap is rejected with a message rather than
    # silently cut. Bound prompt size with GEMINI_MAX_CV_CHARS / GEMINI_MAX_JD_CHARS.
    job_desc_prompt = prompt_fence.sanitize_untrusted(
        job_desc, _MAX_JD_INPUT_CHARS, delimiter=delimiter
    )
    cv_text_prompt = prompt_fence.sanitize_untrusted(
        cv_text, _MAX_CV_INPUT_CHARS, delimiter=delimiter
    )
    untrusted_notice = prompt_fence.untrusted_input_notice(delimiter)
    job_desc_block = prompt_fence.fence("JOB_DESCRIPTION", job_desc_prompt, delimiter)
    cv_block = prompt_fence.fence("CV", cv_text_prompt, delimiter)

    prompt = f"""{analysis_focus}

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanations, no extra text. Just the raw JSON object.

Required JSON format:
{{
  "match_score": <number 0-100>,
  "strengths": ["string1", "string2", ...],
  "missing_skills": ["string1", "string2", ...],
  "suggestions": ["string1", "string2", ...],
  "subscores": {{
    "skills_alignment": <number 0-100>,
    "experience_alignment": <number 0-100>,
    "ats_readiness": <number 0-100>
  }},
  "missing_keywords": ["string1", "string2", ...],
  "content_metrics": {{
    "ats_parse_rate": <number 0-100>,
    "quantifying_impact": {{
      "score": <number 0-100>,
      "status": "ok" | "warn" | "error",
      "details": "brief explanation"
    }},
    "repetition": {{
      "score": <number 0-100>,
      "status": "ok" | "warn" | "error",
      "details": "brief explanation"
    }},
    "spelling_grammar": {{
      "score": <number 0-100>,
      "status": "ok" | "warn" | "error",
      "details": "brief explanation"
    }}
  }},
  "sections_metrics": {{
    "score": <number 0-100>,
    "details": {{
      "has_contact": <boolean>,
      "has_experience": <boolean>,
      "has_education": <boolean>,
      "has_skills": <boolean>,
      "has_summary": <boolean>,
      "missing_sections": ["section1", "section2", ...]
    }}
  }},
  "ats_essentials_metrics": {{
    "score": <number 0-100>,
    "details": {{
      "standard_formatting": <boolean>,
      "keyword_density": <number 0-100>,
      "section_headers_present": <boolean>,
      "text_based": <boolean>,
      "issues": ["issue1", "issue2", ...]
    }}
  }},
  "tailoring_metrics": {{
    "score": <number 0-100>,
    "details": {{
      "keyword_match_rate": <number 0-100>,
      "skill_match_rate": <number 0-100>,
      "experience_relevance": <number 0-100>,
      "alignment_score": <number 0-100>
    }}
  }}
}}

CALCULATION GUIDELINES:
- ats_parse_rate: Estimate how well ATS systems can parse the CV based on text extraction quality, formatting clarity, and structure (0-100). Consider: text-based vs scanned, clear section headers, standard formatting, readable fonts.
- quantifying_impact: Score based on how well achievements use numbers/metrics (0-100). Status: "ok" if >=70, "warn" if 50-69, "error" if <50.
- repetition: Score based on word/phrase repetition frequency (0-100, higher = less repetition). Status: "ok" if >=80, "warn" if 60-79, "error" if <60.
- spelling_grammar: Score based on spelling and grammar accuracy (0-100). Status: "ok" if >=90, "warn" if 70-89, "error" if <70.
- sections_metrics: Score based on presence of standard resume sections (0-100). Check for: Contact, Experience, Education, Skills, Summary/Objective.
- ats_essentials_metrics: Score based on ATS-friendly formatting and structure (0-100). Check: standard section headers, keyword density, text-based format, proper formatting.
- tailoring_metrics: Score based on alignment with job description (0-100). Calculate: keyword match percentage, skill match percentage, experience relevance.

Start your response with {{ and end with }}. No other text before or after.

{untrusted_notice}

{job_desc_block}

{cv_block}
"""
    return prompt


def analyze_cv_with_gemini(
    cv_text: str,
    job_desc: str,
    file_name: str = "",
    file_size_bytes: int = 0,
) -> Dict[str, Any]:
    """Call Gemini to analyze CV vs job description and return JSON-friendly dict."""
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a readable PDF or DOCX CV.")
    _validate_analysis_inputs(cv_text, job_desc, file_size_bytes)
    _enforce_gemini_rate_limit()

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY. Set it in your .env file.")

    genai.configure(api_key=api_key)
    preferred_raw = preferred_models()
    # Normalize model names to ensure they have the 'models/' prefix
    preferred: List[str] = []
    for model_name in preferred_raw:
        normalized = _normalize_model_name(model_name)
        if normalized:
            preferred.append(normalized)

    prompt = _build_analysis_prompt(cv_text, job_desc)

    raw_text = ""
    tried: List[str] = []
    last_exception: Optional[Exception] = None

    # Generation config: temperature=0 for deterministic output
    generation_config = {
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": _ANALYSIS_MAX_OUTPUT_TOKENS,
    }

    for candidate in preferred:
        if not candidate:
            continue
        tried.append(candidate)
        try:
            model = genai.GenerativeModel(candidate)
            response = _generate_with_retry(model, prompt, generation_config)
            raw_text = _extract_response_text(response)
            if not raw_text:
                raise ValueError("Empty response text from model.")
            break
        except Exception as exc:  # pragma: no cover - depends on network
            last_exception = exc
            continue
    else:
        # All preferred models failed; try one auto-picked model
        auto_model = _pick_model_id()
        tried.append(auto_model)
        try:
            model = genai.GenerativeModel(auto_model)
            response = _generate_with_retry(model, prompt, generation_config)
            raw_text = _extract_response_text(response)
            if not raw_text:
                raise ValueError("Empty response text from model.")
        except Exception as exc:  # pragma: no cover - depends on network
            if _is_quota_error(exc):
                raise RuntimeError(_user_friendly_quota_message(exc)) from exc
            if last_exception and _is_quota_error(last_exception):
                raise RuntimeError(_user_friendly_quota_message(last_exception)) from exc
            if last_exception:
                raise RuntimeError(
                    f"Gemini API error after trying {tried}: {exc} (last preferred model error: {last_exception})"
                ) from exc
            raise RuntimeError(f"Gemini API error after trying {tried}: {exc}") from exc

    parsed = _load_model_json_payload(raw_text)
    if not parsed:
        logger.warning(
            "Gemini response JSON parse failed. tried_models=%s raw_preview=%r",
            tried,
            raw_text[:800],
        )

    # Normalize and ensure keys exist
    def _as_list(val: Any, max_items: int = 40) -> List[str]:
        """Convert value to list of strings, filtering empty items."""
        items: List[str] = []
        if isinstance(val, list):
            items = [str(item).strip() for item in val if str(item).strip()]
        elif isinstance(val, str) and val.strip():
            items = [val.strip()]

        # Keep stable order and avoid duplicates/noisy large payloads.
        seen = set()
        unique_items: List[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique_items.append(item)
            if len(unique_items) >= max_items:
                break
        return unique_items

    # Normalize match score (final score is recomputed via calculate_final_score_breakdown below)
    subscores = _as_dict(parsed.get("subscores"))

    # â”€â”€ Programmatic-only scores (deterministic â€” same CV always = same score) â”€â”€

    # ATS Parse Rate: purely programmatic
    ats_parse_rate = calculate_ats_parse_rate(cv_text)

    # Quantifying Impact: purely programmatic
    quant_prog_score, quant_prog_data = calculate_quantifying_impact(cv_text)
    quant_score = quant_prog_score
    quant_details = quant_prog_data["details"]
    quant_status = get_metric_status(quant_score, *QUANTIFYING_IMPACT_THRESHOLDS)

    # Repetition: purely programmatic
    rep_prog_score, rep_prog_data = calculate_repetition(cv_text)
    rep_score = rep_prog_score
    rep_details = rep_prog_data["details"]
    rep_status = get_metric_status(rep_score, *REPETITION_THRESHOLDS)

    # Spelling & Grammar: purely programmatic
    spell_prog_score, spell_prog_data = calculate_spelling_grammar(cv_text)
    spell_score = spell_prog_score
    spell_details = spell_prog_data["details"]
    spell_status = get_metric_status(spell_score, *SPELLING_GRAMMAR_THRESHOLDS)

    # Bullets Consistency: purely programmatic (bullet-length range)
    bullets_prog_score, bullets_prog_data = calculate_bullets_consistency(cv_text)
    bullets_score = bullets_prog_score
    bullets_status = bullets_prog_data.get("status", "ok")
    bullets_details = bullets_prog_data.get("details", "")

    # Contact Information: purely programmatic
    contact_info = calculate_contact_info(cv_text)

    # Sections: purely programmatic
    sections_prog_score, sections_prog_details = calculate_sections(cv_text)
    sections_score = sections_prog_score
    section_order_score, section_order_data = calculate_sections_order(cv_text)

    # ATS Essentials: purely programmatic
    ats_prog_score, ats_prog_details = calculate_ats_essentials(cv_text, file_name, file_size_bytes)
    ats_essentials_score = ats_prog_score

    # File-name quality (purely from the file-name string we already have).
    file_name_score, file_name_data = calculate_file_name_quality(file_name)
    ats_prog_details["file_name_check"] = {"score": file_name_score, **file_name_data}

    # Use the cleaned email from contact_info (has PDF icon artifact removal)
    ci_emails = [c for c in contact_info.get("found", []) if c.get("type") == "email"]
    if ci_emails:
        clean_email = ci_emails[0].get("value", "")
        ats_prog_details["email_check"] = {
            "found": True,
            "email": clean_email,
            "is_professional": ats_prog_details.get("email_check", {}).get("is_professional", True),
        }

    # Tailoring: purely programmatic (CV vs job description keyword overlap)
    tailoring_prog_score, tailoring_prog_details = calculate_tailoring(cv_text, job_desc)
    tailoring_score = tailoring_prog_score

    # Build JD-to-skill evidence matrix.
    jd_skill_matrix = build_jd_skill_matrix(
        cv_text=cv_text,
        job_desc=job_desc,
        tailoring_details=tailoring_prog_details,
    )

    # Build section-level rewrite recommendations.
    rewrite_recommendations = generate_section_rewrite_recommendations(
        cv_text=cv_text,
        quantifying_impact_data=quant_prog_data,
        repetition_data=rep_prog_data,
    )

    has_job_description = bool(job_desc and job_desc.strip())
    fallback_insights = _derive_deterministic_insight_fallbacks(
        ats_parse_rate=ats_parse_rate,
        sections_score=sections_score,
        contact_info=contact_info,
        tailoring_score=tailoring_score,
        has_job_description=has_job_description,
        tailoring_details=tailoring_prog_details,
        jd_skill_matrix=jd_skill_matrix,
        rewrite_recommendations=rewrite_recommendations,
        quant_score=quant_score,
        repetition_score=rep_score,
        spelling_score=spell_score,
        bullets_score=bullets_score,
    )

    # Insights sections are evidence-first and deterministic so they remain
    # grounded in CV↔JD signals and do not vary randomly across model runs.
    merged_strengths = list(fallback_insights["strengths"])
    merged_missing_skills = list(fallback_insights["missing_skills"])
    merged_suggestions = list(fallback_insights["suggestions"])
    merged_missing_keywords = list(fallback_insights["missing_keywords"])

    # Compute deterministic final score with explainable breakdown.
    contact_score_val = contact_info.get("score", 0)
    score_breakdown = calculate_final_score_breakdown(
        ats_parse_rate=ats_parse_rate,
        quant_score=quant_score,
        repetition_score=rep_score,
        spelling_score=spell_score,
        tailoring_score=tailoring_score,
        sections_score=sections_score,
        ats_essentials_score=ats_essentials_score,
        contact_score=contact_score_val,
        has_job_description=has_job_description,
        bullets_consistency_score=bullets_score,
    )
    match_score = score_breakdown.get("final_score", normalize_score(parsed.get("match_score", 0)))

    # Final-project enhancement layer (deterministic and safe).
    recruiter_snapshot = build_recruiter_snapshot(
        parsed | {"match_score": match_score}, file_name or "Resume"
    )
    priority_action_plan = build_priority_action_plan(
        {
            "match_score": match_score,
            "strengths": merged_strengths,
            "missing_skills": merged_missing_skills,
            "missing_keywords": merged_missing_keywords,
            "suggestions": merged_suggestions,
            "content_metrics": {
                "ats_parse_rate": ats_parse_rate,
                "quantifying_impact": {"score": quant_score},
                "repetition": {"score": rep_score},
                "spelling_grammar": {"score": spell_score},
            },
            "sections_metrics": {"details": sections_prog_details},
        }
    )
    interview_prep = build_interview_prep_questions(
        {
            "strengths": merged_strengths,
            "missing_skills": merged_missing_skills,
        },
        job_desc=job_desc,
    )
    learning_roadmap = build_learning_roadmap(
        {
            "missing_skills": merged_missing_skills,
            "missing_keywords": merged_missing_keywords,
        }
    )
    portfolio_checklist = build_portfolio_checklist(
        {
            "sections_metrics": {"details": sections_prog_details},
            "contact_info": contact_info,
            "ats_essentials_metrics": {"details": ats_prog_details},
            "suggestions": merged_suggestions,
        }
    )

    return {
        "match_score": match_score,
        "strengths": merged_strengths,
        "missing_skills": merged_missing_skills,
        "suggestions": merged_suggestions,
        "missing_keywords": merged_missing_keywords,
        "subscores": {
            "skills_alignment": normalize_score(subscores.get("skills_alignment", match_score)),
            "experience_alignment": normalize_score(
                subscores.get("experience_alignment", match_score)
            ),
            "ats_readiness": normalize_score(subscores.get("ats_readiness", match_score)),
        },
        "content_metrics": {
            "ats_parse_rate": ats_parse_rate,
            "quantifying_impact": {
                "score": quant_score,
                "status": quant_status,
                "details": quant_details,
                "total_lines": quant_prog_data.get("total_lines", 0),
                "quantified_count": quant_prog_data.get("quantified_count", 0),
                "non_quantified_lines": quant_prog_data.get("non_quantified_lines", []),
            },
            "repetition": {
                "score": rep_score,
                "status": rep_status,
                "details": rep_details,
                "repeated_words": rep_prog_data.get("repeated_words", []),
            },
            "spelling_grammar": {
                "score": spell_score,
                "status": spell_status,
                "details": spell_details,
                "issues_list": spell_prog_data.get("issues_list", []),
            },
            "bullets_consistency": {
                "score": bullets_score,
                "status": bullets_status,
                "details": bullets_details,
                "total_bullets": bullets_prog_data.get("total_bullets", 0),
                "out_of_range": bullets_prog_data.get("out_of_range", []),
                "min_words": bullets_prog_data.get("min_words", 15),
                "max_words": bullets_prog_data.get("max_words", 45),
            },
        },
        "contact_info": contact_info,
        "sections_metrics": {
            "score": sections_score,
            "details": sections_prog_details,
            "section_order": {"score": section_order_score, **section_order_data},
        },
        "ats_essentials_metrics": {
            "score": ats_essentials_score,
            "details": ats_prog_details,
        },
        "tailoring_metrics": {
            "score": tailoring_score,
            "details": tailoring_prog_details,
        },
        "score_breakdown": score_breakdown,
        "jd_skill_matrix": jd_skill_matrix,
        "rewrite_recommendations": rewrite_recommendations,
        "recruiter_snapshot": recruiter_snapshot,
        "priority_action_plan": priority_action_plan,
        "interview_prep": interview_prep,
        "learning_roadmap": learning_roadmap,
        "portfolio_checklist": portfolio_checklist,
    }


def suggest_cv_bullets(role: str, company: str, context: str = "") -> List[str]:
    """Return up to 5 ATS-optimised bullet points for the given role and company."""
    role = (role or "").strip()
    company = (company or "").strip()
    context = (context or "").strip()
    if not role or not company:
        raise ValueError("Role and company are required for bullet suggestions.")
    if len(role) > 120 or len(company) > 120:
        raise ValueError("Role/company input is too long. Please keep each under 120 characters.")
    if len(context) > 2000:
        raise ValueError("Additional context is too long. Please keep it under 2000 characters.")
    _enforce_gemini_rate_limit()

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    genai.configure(api_key=api_key)

    context_line = f"\nAdditional context: {context}" if context else ""
    prompt = (
        f"You are an expert resume writer. Write exactly 4 strong, ATS-optimized resume bullet points "
        f"for a {role} role at {company}.{context_line}\n\n"
        "Requirements:\n"
        "- Begin each bullet with a strong action verb (Led, Built, Reduced, Designed, Delivered, etc.)\n"
        "- Include quantified impact where plausible (%, numbers, time saved, scale)\n"
        "- Keep each bullet concise (one to two lines)\n"
        "- Do not include bullet symbols or numbering in the text\n\n"
        "Respond with ONLY a JSON array of 4 strings. No markdown, no code blocks, no explanation.\n"
        'Example: ["Bullet one.", "Bullet two.", "Bullet three.", "Bullet four."]'
    )

    try:
        model_id = _pick_model_id()
        model = genai.GenerativeModel(model_id)
        response = _generate_with_retry(
            model, prompt, {"temperature": 0.7, "max_output_tokens": 512}
        )
        raw = _extract_response_text(response)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = json.loads(_extract_json_from_text(raw))
        if isinstance(result, list):
            return [str(b).strip().lstrip("•-– ") for b in result if str(b).strip()][:5]
    except Exception as exc:
        if _is_quota_error(exc):
            raise RuntimeError(_user_friendly_quota_message(exc)) from exc
        raise

    return []
