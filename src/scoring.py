"""
Scoring Module - Programmatic score calculations for CV analysis.

This module contains all scoring calculation functions that analyze CV text
programmatically, independent of AI analysis. These scores can be blended
with AI-provided scores for more accurate results.
"""

import re
from collections import Counter
from typing import Any, Dict, Optional, Tuple

from src.scoring_constants import (
    ATS_PARSE_BASE_SCORE_GOOD,
    ATS_PARSE_BASE_SCORE_MODERATE,
    ATS_PARSE_BASE_SCORE_POOR,
    ATS_PARSE_BASE_SCORE_VERY_POOR,
    ATS_PARSE_SECTION_BONUS,
    ATS_PARSE_TEXT_LENGTH_GOOD,
    ATS_PARSE_TEXT_LENGTH_MODERATE,
    ATS_PARSE_TEXT_LENGTH_POOR,
    ATS_ESSENTIALS_BASE_SCORE,
    ATS_ESSENTIALS_HEADERS_BONUS,
    ATS_ESSENTIALS_KEYWORD_DENSITY_DIVISOR,
    ATS_ESSENTIALS_TEXT_BASED_BONUS,
    ATS_ESSENTIALS_WORD_COUNT_BONUS,
    ATS_ESSENTIALS_WORD_COUNT_BONUS_THRESHOLD,
    MAX_SCORE,
    MIN_SCORE,
    QUANTIFY_BASE_SCORE,
    QUANTIFY_MIN_LINE_LENGTH,
    QUANTIFY_SCORE_MULTIPLIER,
    REPETITION_BASE_SCORE,
    REPETITION_MAX_PENALTY,
    REPETITION_MIN_WORDS,
    REPETITION_PENALTY_THRESHOLD,
    REPETITION_SUGGEST_THRESHOLD,
    REPETITION_TOP_WORDS_TO_CHECK,
    REPETITION_TOP_WORDS_TO_SUGGEST,
    REPETITION_UNIQUE_RATIO_MULTIPLIER,
    SECTIONS_MAX_SCORE,
    SECTIONS_SCORE_PER_SECTION,
    SECTION_KEYWORDS,
    SPELLING_ALL_CAPS_MAX_PENALTY,
    SPELLING_ALL_CAPS_MIN_LENGTH,
    SPELLING_ALL_CAPS_THRESHOLD,
    SPELLING_BASE_SCORE,
    SPELLING_DOUBLE_SPACE_MAX_PENALTY,
    SPELLING_DOUBLE_SPACE_PENALTY_PER_INSTANCE,
    SPELLING_GOOD_SCORE_THRESHOLD,
    SPELLING_PUNCTUATION_MAX_PENALTY,
    SPELLING_PUNCTUATION_PENALTY_PER_INSTANCE,
    STOP_WORDS,
    TAILORING_DEFAULT_SCORE_NO_CV,
    TAILORING_DEFAULT_SCORE_NO_JD,
    TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
    TAILORING_MIN_WORD_LENGTH,
)


def normalize_score(value: Any) -> int:
    """
    Normalize a score value to 0-100 range.
    
    Args:
        value: Score value (can be int, float, or string)
    
    Returns:
        Integer score clamped to 0-100 range
    """
    try:
        score = int(float(value))
    except (ValueError, TypeError):
        score = 0
    return max(MIN_SCORE, min(MAX_SCORE, score))


def get_metric_status(score: int, ok_min: int = 80, warn_min: int = 60) -> str:
    """
    Convert score to status: ok, warn, or error.
    
    Args:
        score: The score value (0-100)
        ok_min: Minimum score for "ok" status
        warn_min: Minimum score for "warn" status
    
    Returns:
        Status string: "ok", "warn", or "error"
    """
    if score >= ok_min:
        return "ok"
    elif score >= warn_min:
        return "warn"
    else:
        return "error"


def calculate_ats_parse_rate(cv_text: str, ai_parse_rate: Optional[int] = None) -> int:
    """
    Calculate ATS parse rate based on CV text quality.
    
    Args:
        cv_text: The extracted CV text
        ai_parse_rate: Optional AI-provided parse rate to blend with
    
    Returns:
        ATS parse rate score (0-100)
    """
    text_length = len(cv_text.strip())
    
    # Base score from text extraction quality
    if text_length >= ATS_PARSE_TEXT_LENGTH_GOOD:
        base_score = ATS_PARSE_BASE_SCORE_GOOD
    elif text_length >= ATS_PARSE_TEXT_LENGTH_MODERATE:
        base_score = ATS_PARSE_BASE_SCORE_MODERATE
    elif text_length >= ATS_PARSE_TEXT_LENGTH_POOR:
        base_score = ATS_PARSE_BASE_SCORE_POOR
    else:
        base_score = ATS_PARSE_BASE_SCORE_VERY_POOR
    
    # Check for common ATS-friendly indicators
    cv_lower = cv_text.lower()
    has_sections = any(
        keyword in cv_lower
        for keyword in ["experience", "education", "skills", "summary", "objective", "contact"]
    )
    if has_sections:
        base_score = min(MAX_SCORE, base_score + ATS_PARSE_SECTION_BONUS)
    
    # If AI provided a parse rate, average it with programmatic calculation
    if ai_parse_rate is not None:
        ai_score = normalize_score(ai_parse_rate)
        return int((base_score + ai_score) / 2)
    
    return base_score


def calculate_quantifying_impact(cv_text: str) -> Tuple[int, str]:
    """
    Score 0-100 based on presence of numbers, %, $, and measurable results in CV text.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_string)
    """
    text = (cv_text or "").strip()
    if not text:
        return 0, "No content to analyze."
    
    # Split into lines/bullets
    lines = [
        ln.strip()
        for ln in re.split(r"[\n•·\-]\s*", text)
        if ln.strip() and len(ln.strip()) > QUANTIFY_MIN_LINE_LENGTH
    ]
    total = max(1, len(lines))
    quantified = 0
    
    for line in lines:
        # Check for numbers, percentages, currency, or measurable language
        if re.search(r"\d", line):
            quantified += 1
        elif re.search(r"%|percent|\$|usd|eur|k\b|million|billion|\d+x|\d+\s*%", line, re.I):
            quantified += 1
        elif re.search(
            r"increas(e|ed|ing)|decreas(e|ed|ing)|reduc(e|ed|ing)|improv(e|ed|ing)|sav(e|ed|ing)|by\s+\d+",
            line,
            re.I,
        ):
            quantified += 1
    
    pct = (quantified / total) * 100
    score = min(MAX_SCORE, int(QUANTIFY_BASE_SCORE + pct * QUANTIFY_SCORE_MULTIPLIER))
    
    details = (
        f"{quantified} of {total} bullet points or lines contain numbers or measurable results."
        if total
        else "No bullet points found."
    )
    
    return score, details


def calculate_repetition(cv_text: str) -> Tuple[int, str]:
    """
    Score 0-100: higher = less repetition. Based on word frequency.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_string)
    """
    text = (cv_text or "").strip().lower()
    if not text:
        return 0, "No content to analyze."
    
    words = re.findall(r"[a-z0-9]+", text)
    total = len(words)
    
    if total < REPETITION_MIN_WORDS:
        return 80, "Too little text to assess repetition."
    
    counts = Counter(words)
    
    # Penalize: words repeated many times (e.g. same word 5+ times)
    repeat_penalty = sum(
        (c - REPETITION_PENALTY_THRESHOLD)
        for w, c in counts.most_common(REPETITION_TOP_WORDS_TO_CHECK)
        if c > REPETITION_PENALTY_THRESHOLD
    )
    
    # Unique ratio: more unique words = better
    unique_ratio = len(counts) / total
    
    # Score: base from unique ratio, minus penalty for heavy repetition
    raw = min(
        MAX_SCORE,
        int(
            REPETITION_BASE_SCORE
            + unique_ratio * REPETITION_UNIQUE_RATIO_MULTIPLIER
            - min(REPETITION_MAX_PENALTY, repeat_penalty)
        ),
    )
    score = max(MIN_SCORE, raw)
    
    # Suggest words to vary
    top_repeated = [
        w for w, _ in counts.most_common(REPETITION_TOP_WORDS_TO_SUGGEST) if counts[w] > REPETITION_SUGGEST_THRESHOLD
    ]
    
    details = (
        f"Unique words: {len(counts)} of {total}. "
        + (f"Consider varying: {', '.join(top_repeated[:3])}." if top_repeated else "Good variety.")
    )
    
    return score, details


def calculate_spelling_grammar(cv_text: str) -> Tuple[int, str]:
    """
    Heuristic score 0-100 for formatting/consistency (no spell-check lib).
    Penalizes double spaces, spacing issues, excessive all-caps.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_string)
    """
    text = (cv_text or "").strip()
    if not text:
        return 0, "No content to analyze."
    
    score = SPELLING_BASE_SCORE
    issues = []
    
    # Check for double spaces
    if re.search(r"  +", text):
        double = len(re.findall(r"  +", text))
        deduction = min(SPELLING_DOUBLE_SPACE_MAX_PENALTY, double * SPELLING_DOUBLE_SPACE_PENALTY_PER_INSTANCE)
        score -= deduction
        issues.append("multiple consecutive spaces")
    
    # Check for spacing after punctuation
    if re.search(r"\s+([.,;:])\s*[a-z]", text):
        punctuation_issues = len(re.findall(r"\s+([.,;:])\s*[a-z]", text))
        deduction = min(
            SPELLING_PUNCTUATION_MAX_PENALTY,
            punctuation_issues * SPELLING_PUNCTUATION_PENALTY_PER_INSTANCE
        )
        score -= deduction
        issues.append("spacing after punctuation")
    
    # Check for excessive all-caps (likely acronyms are ok; long all-caps might be shouting)
    long_caps = re.findall(rf"\b[A-Z]{{{SPELLING_ALL_CAPS_MIN_LENGTH},}}\b", text)
    if len(long_caps) > SPELLING_ALL_CAPS_THRESHOLD:
        score -= min(SPELLING_ALL_CAPS_MAX_PENALTY, len(long_caps))
        issues.append("excessive all-caps")
    
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    
    details = (
        "No major formatting issues found."
        if score >= SPELLING_GOOD_SCORE_THRESHOLD
        else (
            "Consider fixing: " + "; ".join(issues) + "."
            if issues
            else "Review formatting and punctuation."
        )
    )
    
    return score, details


def calculate_sections(cv_text: str) -> Tuple[int, Dict[str, any]]:
    """
    Score 0-100 based on presence of standard resume sections.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_dict)
    """
    text = (cv_text or "").strip().lower()
    if not text:
        return 0, {
            "missing_sections": ["Contact", "Experience", "Education", "Skills", "Summary/Objective"]
        }
    
    found = {}
    missing = []
    
    for name, keywords in SECTION_KEYWORDS.items():
        found[name] = any(kw in text for kw in keywords)
        if not found[name]:
            # Format section name for display
            display_name = (
                name.replace("summary", "Summary/Objective")
                .replace("contact", "Contact")
                .replace("experience", "Experience")
                .replace("education", "Education")
                .replace("skills", "Skills")
                .title()
            )
            missing.append(display_name)
    
    # Score: points per section present
    n = sum(1 for v in found.values() if v)
    score = min(SECTIONS_MAX_SCORE, n * SECTIONS_SCORE_PER_SECTION)
    
    details = {
        "has_contact": found.get("contact", False),
        "has_experience": found.get("experience", False),
        "has_education": found.get("education", False),
        "has_skills": found.get("skills", False),
        "has_summary": found.get("summary", False),
        "missing_sections": missing,
    }
    
    return score, details


def calculate_ats_essentials(cv_text: str) -> Tuple[int, Dict[str, any]]:
    """
    Score 0-100: section headers, text-based format, no obvious format issues.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_dict)
    """
    text = (cv_text or "").strip()
    if not text:
        return 0, {
            "standard_formatting": False,
            "section_headers_present": False,
            "text_based": True,
            "issues": ["No content"],
        }
    
    cv_lower = text.lower()
    has_headers = any(
        h in cv_lower
        for h in [
            "experience",
            "education",
            "skills",
            "summary",
            "objective",
            "contact",
            "work",
            "employment",
        ]
    )
    
    # Assume text-based since we received extracted text
    text_based = True
    issues = []
    
    if not has_headers:
        issues.append("Standard section headers not clearly found")
    
    # Simple keyword density: at least some substantive words
    words = re.findall(r"[a-z0-9]+", cv_lower)
    word_count = len(words)
    
    score = ATS_ESSENTIALS_BASE_SCORE
    if has_headers:
        score += ATS_ESSENTIALS_HEADERS_BONUS
    if text_based:
        score += ATS_ESSENTIALS_TEXT_BASED_BONUS
    if word_count >= ATS_ESSENTIALS_WORD_COUNT_BONUS_THRESHOLD:
        score += ATS_ESSENTIALS_WORD_COUNT_BONUS
    
    score = min(MAX_SCORE, score)
    
    details = {
        "standard_formatting": True,
        "keyword_density": min(MAX_SCORE, word_count // ATS_ESSENTIALS_KEYWORD_DENSITY_DIVISOR),
        "section_headers_present": has_headers,
        "text_based": text_based,
        "issues": issues if issues else [],
    }
    
    return score, details


def calculate_tailoring(cv_text: str, job_desc: str) -> Tuple[int, Dict[str, int]]:
    """
    Score 0-100 based on keyword overlap between CV and job description.
    
    Args:
        cv_text: The CV text
        job_desc: The job description text
    
    Returns:
        Tuple of (score, details_dict)
    """
    cv = (cv_text or "").strip().lower()
    jd = (job_desc or "").strip().lower()
    
    if not jd:
        return TAILORING_DEFAULT_SCORE_NO_JD, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_JD,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_JD,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_JD,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_JD,
        }
    
    if not cv:
        return TAILORING_DEFAULT_SCORE_NO_CV, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_CV,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_CV,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_CV,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_CV,
        }
    
    # Extract significant words (min length, alphabetic) from JD
    jd_words = set(re.findall(rf"[a-z]{{{TAILORING_MIN_WORD_LENGTH},}}", jd))
    cv_words = set(re.findall(rf"[a-z]{{{TAILORING_MIN_WORD_LENGTH},}}", cv))
    
    # Remove stop words
    jd_key = jd_words - STOP_WORDS
    
    if not jd_key:
        return TAILORING_DEFAULT_SCORE_NO_KEYWORDS, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
        }
    
    # Calculate overlap
    overlap = len(jd_key & cv_words) / len(jd_key)
    keyword_match_rate = min(MAX_SCORE, int(overlap * 100))
    
    # Skill-like words: reuse keyword match for simplicity
    skill_match = keyword_match_rate
    
    # Alignment score: average of keyword and skill match
    alignment_score = int((keyword_match_rate + skill_match) / 2)
    alignment_score = max(MIN_SCORE, min(MAX_SCORE, alignment_score))
    
    details = {
        "keyword_match_rate": keyword_match_rate,
        "skill_match_rate": skill_match,
        "experience_relevance": alignment_score,
        "alignment_score": alignment_score,
    }
    
    return alignment_score, details


def blend_scores(programmatic_score: int, ai_score: Optional[int]) -> int:
    """
    Blend programmatic and AI scores by averaging them.
    
    Args:
        programmatic_score: Score calculated programmatically
        ai_score: Optional AI-provided score
    
    Returns:
        Blended score (0-100)
    """
    if ai_score is None:
        return programmatic_score
    
    ai_normalized = normalize_score(ai_score)
    return int((programmatic_score + ai_normalized) / 2)
