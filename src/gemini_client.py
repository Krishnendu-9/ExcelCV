"""
Gemini Client Module

This module handles communication with Google Gemini AI for CV analysis.
It orchestrates AI analysis and blends it with programmatic scoring calculations.
"""

import json
import logging
import re
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from src.career_tools import (
    build_interview_prep_questions,
    build_learning_roadmap,
    build_portfolio_checklist,
    build_priority_action_plan,
    build_recruiter_snapshot,
)
from src.config import get_api_key, preferred_models
from src.scoring import (
    build_jd_skill_matrix,
    calculate_ats_essentials,
    calculate_ats_parse_rate,
    calculate_contact_info,
    calculate_final_score_breakdown,
    calculate_quantifying_impact,
    calculate_repetition,
    calculate_sections,
    calculate_spelling_grammar,
    calculate_tailoring,
    generate_section_rewrite_recommendations,
    get_metric_status,
    normalize_score,
)
from src.scoring_constants import (
    QUANTIFYING_IMPACT_THRESHOLDS,
    REPETITION_THRESHOLDS,
    SPELLING_GRAMMAR_THRESHOLDS,
)

logger = logging.getLogger(__name__)


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
    text = re.sub(r'```(?:json)?\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
    
    # Try to find JSON object boundaries
    # Look for first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace + 1]
    
    return text.strip()


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


def _sanitize_prompt_text(text: str, limit: int) -> str:
    """Trim and normalize input text to keep prompts stable and size-bounded."""
    compact = " ".join((text or "").replace("\x00", " ").split())
    return compact[:limit]


def _normalize_model_name(model: Optional[str]) -> Optional[str]:
    """Ensure model name has the 'models/' prefix if it's a valid model identifier."""
    if not model:
        return None
    
    model = model.strip()
    # If it doesn't start with 'models/', add it (unless it's already a full path)
    if not model.startswith('models/') and not '/' in model:
        # Check if it looks like a model name (e.g., "gemini-2.0-flash-exp")
        if model.startswith('gemini-'):
            return f"models/{model}"
    
    return model


def _as_dict(value: Any) -> Dict[str, Any]:
    """Return a dict or an empty dict when value is not a dict."""
    return value if isinstance(value, dict) else {}


def _generate_with_retry(model: genai.GenerativeModel, prompt: str, generation_config: Dict[str, Any]) -> Any:
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


def analyze_cv_with_gemini(
    cv_text: str,
    job_desc: str,
    file_name: str = "",
    file_size_bytes: int = 0,
) -> Dict[str, Any]:
    """Call Gemini to analyze CV vs job description and return JSON-friendly dict."""
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a readable PDF or DOCX CV.")

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

    job_desc_prompt = _sanitize_prompt_text(job_desc, 4000)
    cv_text_prompt = _sanitize_prompt_text(cv_text, 6000)

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

Job Description:
\"\"\"{job_desc_prompt}\"\"\"

CV:
\"\"\"{cv_text_prompt}\"\"\"
"""

    raw_text = ""
    tried: List[str] = []
    last_exception: Optional[Exception] = None

    # Generation config: temperature=0 for deterministic output
    generation_config = {
        "temperature": 0.0,
        "top_p": 1.0,
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

    # Try to extract and parse JSON
    json_text = _extract_json_from_text(raw_text)
    
    if not json_text:
        logger.warning("Gemini response JSON extraction failed. tried_models=%s raw_preview=%r", tried, raw_text[:800])
        raise ValueError("AI response was not in expected JSON format.")
    
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        logger.warning("Gemini response JSON parse failed. tried_models=%s json_preview=%r raw_preview=%r error=%s", tried, json_text[:800], raw_text[:800], exc)
        raise ValueError("AI response was not in expected JSON format.") from exc

    if not isinstance(parsed, dict):
        parsed = {}

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

    # Normalize match score
    score = normalize_score(parsed.get("match_score", 0))
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

    # Contact Information: purely programmatic
    contact_info = calculate_contact_info(cv_text)

    # Sections: purely programmatic
    sections_prog_score, sections_prog_details = calculate_sections(cv_text)
    sections_score = sections_prog_score

    # ATS Essentials: purely programmatic
    ats_prog_score, ats_prog_details = calculate_ats_essentials(cv_text, file_name, file_size_bytes)
    ats_essentials_score = ats_prog_score

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
        has_job_description=bool(job_desc and job_desc.strip()),
    )
    match_score = score_breakdown.get("final_score", normalize_score(parsed.get("match_score", 0)))

    # Final-project enhancement layer (deterministic and safe).
    recruiter_snapshot = build_recruiter_snapshot(parsed | {"match_score": match_score}, file_name or "Resume")
    priority_action_plan = build_priority_action_plan(
        {
            "match_score": match_score,
            "strengths": _as_list(parsed.get("strengths", [])),
            "missing_skills": _as_list(parsed.get("missing_skills", [])),
            "missing_keywords": _as_list(parsed.get("missing_keywords", [])),
            "suggestions": _as_list(parsed.get("suggestions", [])),
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
            "strengths": _as_list(parsed.get("strengths", [])),
            "missing_skills": _as_list(parsed.get("missing_skills", [])),
        },
        job_desc=job_desc,
    )
    learning_roadmap = build_learning_roadmap(
        {
            "missing_skills": _as_list(parsed.get("missing_skills", [])),
            "missing_keywords": _as_list(parsed.get("missing_keywords", [])),
        }
    )
    portfolio_checklist = build_portfolio_checklist(
        {
            "sections_metrics": {"details": sections_prog_details},
            "contact_info": contact_info,
            "ats_essentials_metrics": {"details": ats_prog_details},
            "suggestions": _as_list(parsed.get("suggestions", [])),
        }
    )

    return {
        "match_score": match_score,
        "strengths": _as_list(parsed.get("strengths", [])),
        "missing_skills": _as_list(parsed.get("missing_skills", [])),
        "suggestions": _as_list(parsed.get("suggestions", [])),
        "missing_keywords": _as_list(parsed.get("missing_keywords", [])),
        "subscores": {
            "skills_alignment": normalize_score(subscores.get("skills_alignment", match_score)),
            "experience_alignment": normalize_score(subscores.get("experience_alignment", match_score)),
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
        },
        "contact_info": contact_info,
        "sections_metrics": {
            "score": sections_score,
            "details": sections_prog_details,
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
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    genai.configure(api_key=api_key)

    context_line = f"\nAdditional context: {context.strip()}" if context.strip() else ""
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
            return [str(b).strip().lstrip("•\-– ") for b in result if str(b).strip()][:5]
    except Exception as exc:
        if _is_quota_error(exc):
            raise RuntimeError(_user_friendly_quota_message(exc)) from exc
        raise

    return []


