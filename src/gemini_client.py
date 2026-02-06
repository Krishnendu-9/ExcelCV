import json
import re
from collections import Counter
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import streamlit as st

from src.config import get_api_key, preferred_models


def _is_quota_error(exc: Exception) -> bool:
    """Return True if the exception is a 429 / quota exceeded error."""
    msg = str(exc).lower()
    return "429" in str(exc) or "quota" in msg or "rate limit" in msg or "resource exhausted" in msg


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
                    "If you're on the free tier, daily limits also apply—see https://ai.google.dev/gemini-api/docs/rate-limits."
                ).format(int(sec) + 1)
    return (
        "Gemini API quota exceeded. You can try again later, or check your plan and billing at "
        "https://ai.google.dev/gemini-api/docs/rate-limits. Free tier has limited requests per day per model."
    )


def _pick_model_id() -> str:
    """Pick a working model id by listing available models."""
    try:
        models = list(genai.list_models())
        for m in models:
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                return m.name
    except Exception:
        pass
    return "models/gemini-1.5-flash-latest"


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


def analyze_cv_with_gemini(cv_text: str, job_desc: str, mode: str = "General Review", debug: bool = False) -> Dict[str, Any]:
    """Call Gemini to analyze CV vs job description and return JSON-friendly dict."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY. Set it in your .env file.")

    genai.configure(api_key=api_key)
    preferred_raw = preferred_models()
    # Normalize model names to ensure they have the 'models/' prefix
    preferred = [_normalize_model_name(m) for m in preferred_raw if _normalize_model_name(m)]

    # Different prompts based on mode
    if mode == "ATS Scan":
        analysis_focus = """
You are an ATS (Applicant Tracking System) optimization specialist. Your primary goal is to evaluate how well this resume will pass through automated screening systems.

PRIORITY FOCUS:
1. Keyword matching: Extract ALL important keywords from the job description and check if they appear in the CV
2. ATS format compliance: Check for proper section headers (Experience, Skills, Education, Contact), standard formatting, text-based PDF (not scanned images)
3. Keyword density: Ensure critical skills and terms appear multiple times appropriately
4. Section completeness: Verify all essential sections are present and properly labeled
5. Missing keywords: Be EXTENSIVE in listing keywords from the JD that are missing from the CV

Be STRICT in scoring. Missing keywords should be prominently flagged. ATS systems reject resumes that lack matching keywords.
"""
    else:  # General Review mode
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
\"\"\"{job_desc.strip()[:4000]}\"\"\"

CV:
\"\"\"{cv_text.strip()[:6000]}\"\"\"
"""

    raw_text = ""
    last_exc: Optional[Exception] = None
    tried: List[str] = []
    used_model = None

    # Generation config to encourage JSON output
    generation_config = {
        "temperature": 0.1,  # Lower temperature for more consistent JSON
        "top_p": 0.95,
    }
    
    for candidate in preferred:
        if not candidate:
            continue
        tried.append(candidate)
        try:
            model = genai.GenerativeModel(candidate)
            # Try with JSON response format if supported (for newer models)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        **generation_config,
                        response_mime_type="application/json"
                    )
                )
            except (AttributeError, TypeError, ValueError):
                # Fallback for models that don't support response_mime_type
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**generation_config)
                )
            raw_text = response.text or ""
            used_model = candidate
            break
        except Exception as exc:  # pragma: no cover - depends on network
            last_exc = exc
            continue
    else:
        # All preferred models failed; try one auto-picked model
        auto_model = _pick_model_id()
        tried.append(auto_model)
        try:
            model = genai.GenerativeModel(auto_model)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        **generation_config,
                        response_mime_type="application/json"
                    )
                )
            except (AttributeError, TypeError, ValueError):
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**generation_config)
                )
            raw_text = response.text or ""
            used_model = auto_model
        except Exception as exc:  # pragma: no cover - depends on network
            if _is_quota_error(exc):
                raise RuntimeError(_user_friendly_quota_message(exc)) from exc
            raise RuntimeError(f"Gemini API error after trying {tried}: {exc}") from exc

    if debug:
        with st.expander("Debug: Raw AI Response"):
            st.write(f"**Model used:** {used_model}")
            st.code(raw_text, language="text")

    # Try to extract and parse JSON
    json_text = _extract_json_from_text(raw_text)
    
    if not json_text:
        error_msg = f"Could not extract JSON from response. Raw response:\n\n{raw_text[:500]}"
        if debug:
            st.error(error_msg)
        raise ValueError("AI response was not in expected JSON format. Enable debug mode to see the raw response.")
    
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        error_msg = (
            f"Failed to parse JSON. Error: {exc}\n\n"
            f"Extracted JSON text:\n{json_text[:1000]}\n\n"
            f"Raw response (first 500 chars):\n{raw_text[:500]}"
        )
        if debug:
            st.error(error_msg)
        raise ValueError("AI response was not in expected JSON format. Enable debug mode to see details.") from exc

    # Normalize and ensure keys exist
    def _as_list(val: Any) -> List[str]:
        if isinstance(val, list):
            return [str(item) for item in val if str(item).strip()]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    score = parsed.get("match_score", 0)
    try:
        score = int(float(score))
    except Exception:
        score = 0
    score = max(0, min(100, score))

    subscores = parsed.get("subscores", {}) or {}

    def _score(val: Any) -> int:
        try:
            v = int(float(val))
        except Exception:
            v = 0
        return max(0, min(100, v))

    def _get_metric_status(score_val: int, ok_min: int = 80, warn_min: int = 60) -> str:
        """Convert score to status: ok, warn, or error. Use metric-specific thresholds."""
        if score_val >= ok_min:
            return "ok"
        elif score_val >= warn_min:
            return "warn"
        else:
            return "error"

    def _calculate_quantifying_impact(cv_text: str) -> tuple:
        """Score 0-100 based on presence of numbers, %, $, and measurable results in CV text.
        Returns (score, details_string)."""
        import re as _re
        text = (cv_text or "").strip()
        if not text:
            return 0, "No content to analyze."
        lines = [ln.strip() for ln in _re.split(r"[\n•·\-]\s*", text) if ln.strip() and len(ln.strip()) > 10]
        total = max(1, len(lines))
        quantified = 0
        for line in lines:
            # Numbers (digits), percentages (e.g. 25%, 25 %), currency ($, USD), or quantity words
            if _re.search(r"\d", line):
                quantified += 1
            elif _re.search(r"%|percent|\\$|usd|eur|k\b|million|billion|\d+x|\d+\s*%", line, _re.I):
                quantified += 1
            elif _re.search(
                r"increas(e|ed|ing)|decreas(e|ed|ing)|reduc(e|ed|ing)|improv(e|ed|ing)|sav(e|ed|ing)|by\s+\d+",
                line,
                _re.I,
            ):
                quantified += 1
        pct = (quantified / total) * 100
        score = min(100, int(40 + pct * 0.6))  # 40–100 range so some bullets give 70+
        details = (
            f"{quantified} of {total} bullet points or lines contain numbers or measurable results."
            if total else "No bullet points found."
        )
        return score, details

    def _calculate_repetition(cv_text: str) -> tuple:
        """Score 0-100: higher = less repetition. Based on word frequency (lower repeat ratio = better).
        Returns (score, details_string)."""
        import re as _re
        text = (cv_text or "").strip().lower()
        if not text:
            return 0, "No content to analyze."
        words = _re.findall(r"[a-z0-9]+", text)
        total = len(words)
        if total < 5:
            return 80, "Too little text to assess repetition."
        counts = Counter(words)
        # Penalize: words repeated many times (e.g. same word 5+ times)
        repeat_penalty = sum((c - 2) for w, c in counts.most_common(20) if c > 2)
        # Unique ratio: more unique words = better
        unique_ratio = len(counts) / total
        # Score: base from unique ratio, minus penalty for heavy repetition
        raw = min(100, int(50 + unique_ratio * 50 - min(40, repeat_penalty)))
        score = max(0, raw)
        top_repeated = [w for w, _ in counts.most_common(5) if counts[w] > 2]
        details = (
            f"Unique words: {len(counts)} of {total}. "
            + (f"Consider varying: {', '.join(top_repeated[:3])}." if top_repeated else "Good variety.")
        )
        return score, details

    def _calculate_spelling_grammar(cv_text: str) -> tuple:
        """Heuristic score 0-100 for formatting/consistency (no spell-check lib). Penalize double spaces, etc.
        Returns (score, details_string)."""
        import re as _re
        text = (cv_text or "").strip()
        if not text:
            return 0, "No content to analyze."
        score = 100
        issues = []
        if _re.search(r"  +", text):
            double = len(_re.findall(r"  +", text))
            deduction = min(15, double * 2)
            score -= deduction
            issues.append("multiple consecutive spaces")
        if _re.search(r"\s+([.,;:])\s*[a-z]", text):
            # possible missing space after punctuation
            issues.append("spacing after punctuation")
            score -= min(10, len(_re.findall(r"\s+([.,;:])\s*[a-z]", text)) * 2)
        # All-caps words (likely acronyms are ok; long all-caps might be shouting)
        long_caps = _re.findall(r"\b[A-Z]{4,}\b", text)
        if len(long_caps) > 3:
            score -= min(10, len(long_caps))
            issues.append("excessive all-caps")
        score = max(0, min(100, score))
        details = "No major formatting issues found." if score >= 85 else (
            "Consider fixing: " + "; ".join(issues) + "." if issues else "Review formatting and punctuation."
        )
        return score, details

    def _calculate_sections(cv_text: str) -> tuple:
        """Score 0-100 based on presence of standard resume sections. Returns (score, details_dict)."""
        text = (cv_text or "").strip().lower()
        if not text:
            return 0, {"missing_sections": ["Contact", "Experience", "Education", "Skills", "Summary/Objective"]}
        section_keywords = {
            "contact": ["contact", "email", "phone", "mobile", "address", "@", "linkedin"],
            "experience": ["experience", "work history", "employment", "professional experience", "career"],
            "education": ["education", "academic", "degree", "university", "college", "bachelor", "master", "phd"],
            "skills": ["skills", "technical skills", "competencies", "expertise"],
            "summary": ["summary", "objective", "profile", "about me", "professional summary"],
        }
        found = {}
        missing = []
        for name, keywords in section_keywords.items():
            found[name] = any(kw in text for kw in keywords)
            if not found[name]:
                missing.append(name.replace("summary", "Summary/Objective").replace("contact", "Contact").replace("experience", "Experience").replace("education", "Education").replace("skills", "Skills").title())
        # Score: 20 per section present, 100 if all 5
        n = sum(1 for v in found.values() if v)
        score = min(100, n * 20)
        details = {
            "has_contact": found.get("contact", False),
            "has_experience": found.get("experience", False),
            "has_education": found.get("education", False),
            "has_skills": found.get("skills", False),
            "has_summary": found.get("summary", False),
            "missing_sections": missing,
        }
        return score, details

    def _calculate_ats_essentials(cv_text: str) -> tuple:
        """Score 0-100: section headers, text-based (we have text), no obvious format issues. Returns (score, details_dict)."""
        text = (cv_text or "").strip()
        if not text:
            return 0, {"standard_formatting": False, "section_headers_present": False, "text_based": True, "issues": ["No content"]}
        cv_lower = text.lower()
        has_headers = any(h in cv_lower for h in ["experience", "education", "skills", "summary", "objective", "contact", "work", "employment"])
        # Assume text-based since we received extracted text
        text_based = True
        issues = []
        if not has_headers:
            issues.append("Standard section headers not clearly found")
        # Simple keyword density: at least some substantive words
        words = re.findall(r"[a-z0-9]+", cv_lower)
        word_count = len(words)
        score = 60
        if has_headers:
            score += 25
        if text_based:
            score += 10
        if word_count >= 200:
            score += 5
        score = min(100, score)
        details = {
            "standard_formatting": True,
            "keyword_density": min(100, word_count // 5),
            "section_headers_present": has_headers,
            "text_based": text_based,
            "issues": issues if issues else [],
        }
        return score, details

    def _calculate_tailoring(cv_text: str, job_desc: str) -> tuple:
        """Score 0-100 based on keyword overlap between CV and job description. Returns (score, details_dict)."""
        cv = (cv_text or "").strip().lower()
        jd = (job_desc or "").strip().lower()
        if not jd:
            return 80, {"keyword_match_rate": 80, "skill_match_rate": 80, "experience_relevance": 80, "alignment_score": 80}
        if not cv:
            return 0, {"keyword_match_rate": 0, "skill_match_rate": 0, "experience_relevance": 0, "alignment_score": 0}
        # Extract significant words (3+ chars, alphabetic) from JD
        jd_words = set(re.findall(r"[a-z]{3,}", jd))
        cv_words = set(re.findall(r"[a-z]{3,}", cv))
        # Remove very common words
        stop = {"the", "and", "for", "with", "from", "this", "that", "have", "has", "are", "was", "were", "been", "being", "will", "your", "you", "their", "they", "would", "could", "should", "about", "when", "which", "what", "where", "into", "through", "during", "before", "after", "above", "below"}
        jd_key = jd_words - stop
        if not jd_key:
            return 70, {"keyword_match_rate": 70, "skill_match_rate": 70, "experience_relevance": 70, "alignment_score": 70}
        overlap = len(jd_key & cv_words) / len(jd_key)
        keyword_match_rate = min(100, int(overlap * 100))
        # Skill-like words (common in JDs): words that appear in both
        skill_match = keyword_match_rate  # reuse for simplicity
        alignment_score = int((keyword_match_rate + skill_match) / 2)
        alignment_score = max(0, min(100, alignment_score))
        details = {
            "keyword_match_rate": keyword_match_rate,
            "skill_match_rate": skill_match,
            "experience_relevance": alignment_score,
            "alignment_score": alignment_score,
        }
        return alignment_score, details

    # Calculate ATS Parse Rate programmatically based on CV text quality
    def _calculate_ats_parse_rate(cv_text: str, ai_parse_rate: Optional[int] = None) -> int:
        """Calculate ATS parse rate based on CV text quality."""
        text_length = len(cv_text.strip())
        
        # Base score from text extraction quality
        if text_length >= 800:
            base_score = 85  # Good text extraction
        elif text_length >= 400:
            base_score = 70  # Moderate text extraction
        elif text_length >= 100:
            base_score = 50  # Poor text extraction
        else:
            base_score = 20  # Very poor text extraction
        
        # Check for common ATS-friendly indicators
        cv_lower = cv_text.lower()
        has_sections = any(keyword in cv_lower for keyword in [
            "experience", "education", "skills", "summary", "objective", "contact"
        ])
        if has_sections:
            base_score = min(100, base_score + 10)
        
        # If AI provided a parse rate, average it with programmatic calculation
        if ai_parse_rate is not None:
            return int((base_score + ai_parse_rate) / 2)
        return base_score

    # Extract content metrics
    content_metrics_raw = parsed.get("content_metrics", {}) or {}
    ai_parse_rate = None
    try:
        ai_parse_rate = _score(content_metrics_raw.get("ats_parse_rate"))
    except Exception:
        pass
    
    # Calculate final ATS parse rate (combine AI analysis with programmatic calculation)
    ats_parse_rate = _calculate_ats_parse_rate(cv_text, ai_parse_rate)
    
    # Quantifying Impact: programmatic calculation (with optional AI blend)
    quant_impact_raw = content_metrics_raw.get("quantifying_impact", {}) or {}
    quant_prog_score, quant_prog_details = _calculate_quantifying_impact(cv_text)
    ai_quant = None
    try:
        ai_quant = _score(quant_impact_raw.get("score", 0))
    except Exception:
        pass
    if ai_quant is not None and quant_impact_raw.get("score") is not None:
        quant_score = int((quant_prog_score + ai_quant) / 2)
        quant_details = quant_impact_raw.get("details", "").strip() or quant_prog_details
    else:
        quant_score = quant_prog_score
        quant_details = quant_prog_details
    quant_score = max(0, min(100, quant_score))
    quant_status = _get_metric_status(quant_score, 70, 50)
    
    # Repetition: programmatic calculation (with optional AI blend)
    repetition_raw = content_metrics_raw.get("repetition", {}) or {}
    rep_prog_score, rep_prog_details = _calculate_repetition(cv_text)
    ai_rep = None
    try:
        ai_rep = _score(repetition_raw.get("score", 0))
    except Exception:
        pass
    if ai_rep is not None and repetition_raw.get("score") is not None:
        rep_score = int((rep_prog_score + ai_rep) / 2)
        rep_details = repetition_raw.get("details", "").strip() or rep_prog_details
    else:
        rep_score = rep_prog_score
        rep_details = rep_prog_details
    rep_score = max(0, min(100, rep_score))
    rep_status = _get_metric_status(rep_score, 80, 60)
    
    # Spelling & Grammar: programmatic calculation (with optional AI blend)
    spelling_raw = content_metrics_raw.get("spelling_grammar", {}) or {}
    spell_prog_score, spell_prog_details = _calculate_spelling_grammar(cv_text)
    ai_spell = None
    try:
        ai_spell = _score(spelling_raw.get("score", 0))
    except Exception:
        pass
    if ai_spell is not None and spelling_raw.get("score") is not None:
        spell_score = int((spell_prog_score + ai_spell) / 2)
        spell_details = spelling_raw.get("details", "").strip() or spell_prog_details
    else:
        spell_score = spell_prog_score
        spell_details = spell_prog_details
    spell_score = max(0, min(100, spell_score))
    spell_status = _get_metric_status(spell_score, 90, 70)
    
    # Sections: programmatic (with optional AI blend)
    sections_raw = parsed.get("sections_metrics", {}) or {}
    sections_prog_score, sections_prog_details = _calculate_sections(cv_text)
    ai_sections = None
    try:
        ai_sections = _score(sections_raw.get("score", 0))
    except Exception:
        pass
    if ai_sections is not None and sections_raw.get("score") is not None:
        sections_score = int((sections_prog_score + ai_sections) / 2)
        sections_details = sections_raw.get("details", sections_prog_details)
        if not isinstance(sections_details, dict):
            sections_details = sections_prog_details
    else:
        sections_score = sections_prog_score
        sections_details = sections_prog_details
    sections_score = max(0, min(100, sections_score))

    # ATS Essentials: programmatic (with optional AI blend)
    ats_essentials_raw = parsed.get("ats_essentials_metrics", {}) or {}
    ats_prog_score, ats_prog_details = _calculate_ats_essentials(cv_text)
    ai_ats = None
    try:
        ai_ats = _score(ats_essentials_raw.get("score", 0))
    except Exception:
        pass
    if ai_ats is not None and ats_essentials_raw.get("score") is not None:
        ats_essentials_score = int((ats_prog_score + ai_ats) / 2)
        ats_essentials_details = ats_essentials_raw.get("details", ats_prog_details)
        if not isinstance(ats_essentials_details, dict):
            ats_essentials_details = ats_prog_details
    else:
        ats_essentials_score = ats_prog_score
        ats_essentials_details = ats_prog_details
    ats_essentials_score = max(0, min(100, ats_essentials_score))

    # Tailoring: programmatic (CV vs job description; with optional AI blend)
    tailoring_raw = parsed.get("tailoring_metrics", {}) or {}
    tailoring_prog_score, tailoring_prog_details = _calculate_tailoring(cv_text, job_desc)
    ai_tailoring = None
    try:
        ai_tailoring = _score(tailoring_raw.get("score", 0))
    except Exception:
        pass
    if ai_tailoring is not None and tailoring_raw.get("score") is not None:
        tailoring_score = int((tailoring_prog_score + ai_tailoring) / 2)
        tailoring_details = tailoring_raw.get("details", tailoring_prog_details)
        if not isinstance(tailoring_details, dict):
            tailoring_details = tailoring_prog_details
    else:
        tailoring_score = tailoring_prog_score
        tailoring_details = tailoring_prog_details
    tailoring_score = max(0, min(100, tailoring_score))

    return {
        "match_score": score,
        "strengths": _as_list(parsed.get("strengths", [])),
        "missing_skills": _as_list(parsed.get("missing_skills", [])),
        "suggestions": _as_list(parsed.get("suggestions", [])),
        "missing_keywords": _as_list(parsed.get("missing_keywords", [])),
        "subscores": {
            "skills_alignment": _score(subscores.get("skills_alignment", score)),
            "experience_alignment": _score(subscores.get("experience_alignment", score)),
            "ats_readiness": _score(subscores.get("ats_readiness", score)),
        },
        "content_metrics": {
            "ats_parse_rate": ats_parse_rate,
            "quantifying_impact": {
                "score": quant_score,
                "status": quant_status,
                "details": quant_details,
            },
            "repetition": {
                "score": rep_score,
                "status": rep_status,
                "details": rep_details,
            },
            "spelling_grammar": {
                "score": spell_score,
                "status": spell_status,
                "details": spell_details,
            },
        },
        "sections_metrics": {
            "score": sections_score,
            "details": sections_details
        },
        "ats_essentials_metrics": {
            "score": ats_essentials_score,
            "details": ats_essentials_details
        },
        "tailoring_metrics": {
            "score": tailoring_score,
            "details": tailoring_details
        }
    }

