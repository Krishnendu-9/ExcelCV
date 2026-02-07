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
    WORD_SYNONYMS,
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


def calculate_ats_parse_rate(cv_text: str) -> int:
    """
    Calculate ATS parse rate based on CV text quality (deterministic).
    
    Args:
        cv_text: The extracted CV text
    
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
    
    return base_score


def calculate_quantifying_impact(cv_text: str) -> Tuple[int, Dict]:
    """
    Score 0-100 based on presence of numbers, %, $, and measurable results in CV text.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_dict) with keys:
            details: summary string
            total_lines: total bullet points analyzed
            quantified_count: how many have numbers/metrics
            non_quantified_lines: list of bullet points lacking quantification
    """
    text = (cv_text or "").strip()
    if not text:
        return 0, {
            "details": "No content to analyze.",
            "total_lines": 0,
            "quantified_count": 0,
            "non_quantified_lines": [],
        }
    
    # Split into lines/bullets
    lines = [
        ln.strip()
        for ln in re.split(r"[\n•·\-]\s*", text)
        if ln.strip() and len(ln.strip()) > QUANTIFY_MIN_LINE_LENGTH
    ]
    total = max(1, len(lines))
    quantified = 0
    non_quantified = []
    
    for line in lines:
        has_metric = False
        if re.search(r"\d", line):
            has_metric = True
        elif re.search(r"%|percent|\$|usd|eur|k\b|million|billion|\d+x|\d+\s*%", line, re.I):
            has_metric = True
        elif re.search(
            r"increas(e|ed|ing)|decreas(e|ed|ing)|reduc(e|ed|ing)|improv(e|ed|ing)|sav(e|ed|ing)|by\s+\d+",
            line,
            re.I,
        ):
            has_metric = True
        
        if has_metric:
            quantified += 1
        else:
            non_quantified.append(line)
    
    pct = (quantified / total) * 100
    score = min(MAX_SCORE, int(QUANTIFY_BASE_SCORE + pct * QUANTIFY_SCORE_MULTIPLIER))
    
    details = (
        f"{quantified} of {total} bullet points contain numbers or measurable results."
        if total
        else "No bullet points found."
    )
    
    return score, {
        "details": details,
        "total_lines": total,
        "quantified_count": quantified,
        "non_quantified_lines": non_quantified[:10],  # Limit to 10 for display
    }


def calculate_repetition(cv_text: str) -> Tuple[int, Dict]:
    """
    Score 0-100: higher = less repetition. Based on word frequency.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_dict) with keys:
            details: summary string
            repeated_words: list of dicts with word, count, suggestions
    """
    text = (cv_text or "").strip().lower()
    if not text:
        return 0, {"details": "No content to analyze.", "repeated_words": []}
    
    words = re.findall(r"[a-z]+", text)
    total = len(words)
    
    if total < REPETITION_MIN_WORDS:
        return 80, {"details": "Too little text to assess repetition.", "repeated_words": []}
    
    counts = Counter(words)
    
    # Penalize: words repeated many times
    repeat_penalty = sum(
        (c - REPETITION_PENALTY_THRESHOLD)
        for w, c in counts.most_common(REPETITION_TOP_WORDS_TO_CHECK)
        if c > REPETITION_PENALTY_THRESHOLD
    )
    
    unique_ratio = len(counts) / total
    
    raw = min(
        MAX_SCORE,
        int(
            REPETITION_BASE_SCORE
            + unique_ratio * REPETITION_UNIQUE_RATIO_MULTIPLIER
            - min(REPETITION_MAX_PENALTY, repeat_penalty)
        ),
    )
    score = max(MIN_SCORE, raw)
    
    # Build repeated words with synonym suggestions
    repeated_words = []
    for word, count in counts.most_common(REPETITION_TOP_WORDS_TO_SUGGEST):
        if count <= REPETITION_SUGGEST_THRESHOLD:
            break
        # Skip very short or stop words
        if len(word) < 4 or word in STOP_WORDS:
            continue
        suggestions = WORD_SYNONYMS.get(word, [])
        repeated_words.append({
            "word": word,
            "count": count,
            "suggestions": suggestions[:3],
        })
    
    top_names = [rw["word"] for rw in repeated_words[:3]]
    details = (
        f"Unique words: {len(counts)} of {total}. "
        + (f"Consider varying: {', '.join(top_names)}." if top_names else "Good variety.")
    )
    
    return score, {
        "details": details,
        "repeated_words": repeated_words[:8],  # Limit to 8 for display
    }


def calculate_spelling_grammar(cv_text: str) -> Tuple[int, Dict]:
    """
    Heuristic score 0-100 for formatting/consistency (no spell-check lib).
    Penalizes double spaces, spacing issues, excessive all-caps.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Tuple of (score, details_dict) with keys:
            details: summary string
            issues_list: list of dicts with type, count, examples
    """
    text = (cv_text or "").strip()
    if not text:
        return 0, {"details": "No content to analyze.", "issues_list": []}
    
    score = SPELLING_BASE_SCORE
    issue_labels = []
    issues_list = []
    
    # Check for double spaces
    double_matches = re.findall(r".{0,20}  +.{0,20}", text)
    if double_matches:
        double_count = len(re.findall(r"  +", text))
        deduction = min(SPELLING_DOUBLE_SPACE_MAX_PENALTY,
                        double_count * SPELLING_DOUBLE_SPACE_PENALTY_PER_INSTANCE)
        score -= deduction
        issue_labels.append("multiple consecutive spaces")
        issues_list.append({
            "type": "double_space",
            "label": "Multiple consecutive spaces",
            "count": double_count,
            "examples": [m.strip() for m in double_matches[:3]],
        })
    
    # Check for spacing after punctuation
    punct_matches = re.findall(r".{0,15}\s+[.,;:]\s*[a-z].{0,15}", text)
    if punct_matches:
        punct_count = len(punct_matches)
        deduction = min(SPELLING_PUNCTUATION_MAX_PENALTY,
                        punct_count * SPELLING_PUNCTUATION_PENALTY_PER_INSTANCE)
        score -= deduction
        issue_labels.append("spacing around punctuation")
        issues_list.append({
            "type": "punctuation",
            "label": "Incorrect spacing around punctuation",
            "count": punct_count,
            "examples": [m.strip() for m in punct_matches[:3]],
        })
    
    # Check for excessive all-caps
    long_caps = re.findall(rf"\b[A-Z]{{{SPELLING_ALL_CAPS_MIN_LENGTH},}}\b", text)
    if len(long_caps) > SPELLING_ALL_CAPS_THRESHOLD:
        score -= min(SPELLING_ALL_CAPS_MAX_PENALTY, len(long_caps))
        issue_labels.append("excessive all-caps words")
        issues_list.append({
            "type": "all_caps",
            "label": "Excessive all-caps words",
            "count": len(long_caps),
            "examples": list(set(long_caps))[:5],
        })
    
    # Check for inconsistent bullet characters
    bullet_chars = re.findall(r"^[\s]*([•·▪▸►➤\-\*])", text, re.MULTILINE)
    unique_bullets = set(bullet_chars)
    if len(unique_bullets) > 2:
        issues_list.append({
            "type": "inconsistent_bullets",
            "label": "Inconsistent bullet point characters",
            "count": len(unique_bullets),
            "examples": list(unique_bullets),
        })
    
    # Check for missing periods at end of bullet points
    lines = [ln.strip() for ln in text.split("\n") if len(ln.strip()) > 20]
    lines_no_period = [ln for ln in lines if ln and ln[-1] not in ".!?:;"]
    if len(lines_no_period) > 3:
        issues_list.append({
            "type": "missing_period",
            "label": "Bullet points missing ending punctuation",
            "count": len(lines_no_period),
            "examples": [ln[:80] + ("..." if len(ln) > 80 else "") for ln in lines_no_period[:3]],
        })
    
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    
    details = (
        "No significant spelling or grammar errors detected."
        if score >= SPELLING_GOOD_SCORE_THRESHOLD
        else (
            "Consider fixing: " + "; ".join(issue_labels) + "."
            if issue_labels
            else "Review formatting and punctuation."
        )
    )
    
    return score, {
        "details": details,
        "issues_list": issues_list,
    }


def calculate_contact_info(cv_text: str) -> Dict[str, Any]:
    """
    Extract and validate contact information from CV text (deterministic).

    Checks for: phone number, email address, LinkedIn, GitHub, portfolio/website.

    Args:
        cv_text: The CV text to analyze

    Returns:
        Dict with keys:
            found: list of dicts {type, label, value}
            missing: list of dicts {type, label, message}
            score: 0-100 based on completeness
    """
    text = (cv_text or "").strip()
    if not text:
        return {
            "found": [],
            "missing": [
                {"type": "phone", "label": "Phone number", "message": "No phone number found in your resume."},
                {"type": "email", "label": "Email address", "message": "No email address found in your resume."},
                {"type": "linkedin", "label": "LinkedIn", "message": "No LinkedIn profile found in your resume."},
            ],
            "score": 0,
        }

    # Pre-clean PDF icon artifacts that bleed into adjacent text.
    # PDF icon fonts (e.g. FontAwesome) are extracted as garbled unicode + ASCII
    # remnants like "/envel⌢pe" for envelope or "♂phone-alt" for phone icon.
    # Only clean the header area (first ~5 lines) to avoid damaging body text.
    lines = text.split("\n")
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i < 5:
            # Replace non-ASCII char(s) + up to 2 trailing ASCII remnants with space
            line = re.sub(r"[^\x00-\x7f]+.{0,2}", " ", line)
            # Remove known icon-name remnants (e.g. "/envel", "phone-alt", "/linkedin-in")
            line = re.sub(r"/envel\w*", " ", line, flags=re.I)
            line = re.sub(r"phone[\-_]?alt", " ", line, flags=re.I)
            # Extract LinkedIn username from icon pattern BEFORE removing it
            li_match = re.search(r"/linkedin[\-_]?in\s*([\w\-]+)", line, re.I)
            if li_match:
                line = re.sub(
                    r"/linkedin[\-_]?in\s*[\w\-]+",
                    f" linkedin.com/in/{li_match.group(1)} ",
                    line,
                    flags=re.I,
                )
            else:
                line = re.sub(r"/linkedin[\-_]?in", " linkedin ", line, flags=re.I)
            # Collapse multiple spaces
            line = re.sub(r"\s{2,}", " ", line).strip()
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)

    found = []
    missing = []

    # ── Phone number ──
    phone_patterns = [
        r"(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}",
        r"\+\d{1,3}\s?\d{4,14}",
    ]
    phone_match = None
    for pattern in phone_patterns:
        match = re.search(pattern, cleaned)
        if match:
            phone_val = match.group().strip()
            # Validate: must have at least 7 digits total
            digits = re.sub(r"\D", "", phone_val)
            if len(digits) >= 7:
                phone_match = phone_val
                break

    if phone_match:
        found.append({"type": "phone", "label": "Phone number", "value": phone_match})
    else:
        missing.append({
            "type": "phone",
            "label": "Phone number",
            "message": "No phone number found. Include a professional contact number.",
        })

    # ── Email address ──
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", cleaned)
    if email_match:
        found.append({"type": "email", "label": "Email address", "value": email_match.group()})
    else:
        missing.append({
            "type": "email",
            "label": "Email address",
            "message": "No email address found. Include a professional email.",
        })

    # ── LinkedIn ──
    # Standard URL format
    linkedin_match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/([\w\-]+)/?",
        cleaned,
        re.I,
    )
    if linkedin_match:
        found.append({"type": "linkedin", "label": "LinkedIn", "value": linkedin_match.group()})
    else:
        # PDF icon extraction: "/linkedin-in" followed by username (no space)
        # e.g. "/linkedin-innelay-karmakar-09692a288"
        li_icon_match = re.search(r"linkedin[\-_]?in\s*([\w\-]+)", cleaned, re.I)
        if li_icon_match:
            username = li_icon_match.group(1)
            found.append({"type": "linkedin", "label": "LinkedIn", "value": f"linkedin.com/in/{username}"})
        elif re.search(r"linkedin", cleaned, re.I):
            found.append({"type": "linkedin", "label": "LinkedIn", "value": "(detected but URL not parsed)"})
        else:
            missing.append({
                "type": "linkedin",
                "label": "LinkedIn",
                "message": "You are either not using an ATS friendly template, or you are missing your LinkedIn in your resume.",
            })

    # ── GitHub ──
    github_match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/([\w\-]+)/?",
        cleaned,
        re.I,
    )
    if github_match:
        found.append({"type": "github", "label": "GitHub", "value": github_match.group()})
    else:
        # PDF icon extraction: "github" followed by username
        gh_icon_match = re.search(r"github[\-_]?\s*([\w\-]+)", cleaned, re.I)
        if gh_icon_match:
            username = gh_icon_match.group(1)
            if username.lower() not in ("com", "io"):
                found.append({"type": "github", "label": "GitHub", "value": f"github.com/{username}"})
        elif re.search(r"github", cleaned, re.I):
            found.append({"type": "github", "label": "GitHub", "value": "(detected but URL not parsed)"})

    # ── Portfolio / Website ──
    website_match = re.search(
        r"(?:https?://)?(?:www\.)?(?!linkedin\.com|github\.com)[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/\S*)?",
        cleaned,
    )
    if website_match:
        val = website_match.group()
        # Filter out common non-portfolio domains
        skip_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "email.com", "google.com"]
        if not any(d in val.lower() for d in skip_domains):
            found.append({"type": "website", "label": "Portfolio/Website", "value": val})

    # ── Location / Address ──
    # Simple heuristic: look for city/country patterns near "address" or at top of resume
    location_patterns = [
        r"(?:address|location|city)\s*[:\-]?\s*(.+)",
    ]
    for pattern in location_patterns:
        loc_match = re.search(pattern, cleaned, re.I)
        if loc_match:
            found.append({"type": "location", "label": "Location", "value": loc_match.group(1).strip()[:60]})
            break

    # Score: based on how many essential items are found
    essential_types = {"phone", "email", "linkedin"}
    found_types = {item["type"] for item in found}
    essential_found = len(essential_types & found_types)
    total_essential = len(essential_types)
    score = int((essential_found / total_essential) * 100) if total_essential else 100

    return {
        "found": found,
        "missing": missing,
        "score": score,
    }


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


def calculate_ats_essentials(cv_text: str, file_name: str = "", file_size_bytes: int = 0) -> Tuple[int, Dict[str, Any]]:
    """
    Score 0-100: section headers, text-based format, no obvious format issues.
    Also checks file format, email professionalism, and header links.

    Args:
        cv_text: The CV text to analyze
        file_name: Original file name (e.g. "resume.pdf")
        file_size_bytes: File size in bytes

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
            "file_format": {"is_pdf": False, "file_name": "", "file_size_kb": 0, "size_ok": False},
            "email_check": {"found": False, "email": "", "is_professional": False},
            "header_links": {"has_links": False, "links": []},
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

    # ── File Format & Size ──
    is_pdf = file_name.lower().endswith(".pdf") if file_name else True  # assume PDF
    file_size_kb = round(file_size_bytes / 1024, 1) if file_size_bytes else 0
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2) if file_size_bytes else 0
    size_ok = file_size_bytes <= 2 * 1024 * 1024 if file_size_bytes else True  # <=2MB
    file_format_info = {
        "is_pdf": is_pdf,
        "file_name": file_name,
        "file_size_kb": file_size_kb,
        "file_size_mb": file_size_mb,
        "size_ok": size_ok,
    }

    # ── Email Address Check ──
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    email_str = email_match.group() if email_match else ""
    # Check email professionalism (not generic/unprofessional prefixes)
    unprofessional_prefixes = [
        "sexy", "hot", "babe", "cool", "dude", "party", "gamer",
        "xxx", "420", "love", "cute", "angel", "devil", "ninja",
    ]
    is_professional = True
    if email_str:
        local = email_str.split("@")[0].lower()
        if any(local.startswith(p) for p in unprofessional_prefixes):
            is_professional = False
        # Check for excessive numbers (like random123456@)
        digits_in_local = sum(1 for c in local if c.isdigit())
        if digits_in_local > len(local) * 0.6 and len(local) > 4:
            is_professional = False
    email_check = {
        "found": bool(email_str),
        "email": email_str,
        "is_professional": is_professional,
    }

    # ── Header Links (URLs in the header/top area) ──
    # Check top ~5 lines for full URLs
    top_lines = "\n".join(text.split("\n")[:6])
    url_pattern = r"(?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[\w\-./]*)*"
    header_urls = re.findall(url_pattern, top_lines)
    # Filter out email domains
    email_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "email.com"]
    links = [u for u in header_urls if not any(d in u.lower() for d in email_domains)]
    has_full_link = any(
        "linkedin.com" in u.lower() or "github.com" in u.lower() or u.startswith("http")
        for u in links
    )
    # Also check for partial social presence (from PDF icon extraction)
    if not has_full_link:
        has_full_link = bool(re.search(r"linkedin|github", top_lines, re.I))
    header_links = {
        "has_links": has_full_link or len(links) > 0,
        "links": links[:5],  # limit to 5
        "has_full_url": has_full_link,
    }

    details = {
        "standard_formatting": True,
        "keyword_density": min(MAX_SCORE, word_count // ATS_ESSENTIALS_KEYWORD_DENSITY_DIVISOR),
        "section_headers_present": has_headers,
        "text_based": text_based,
        "issues": issues if issues else [],
        "file_format": file_format_info,
        "email_check": email_check,
        "header_links": header_links,
    }

    return score, details


def calculate_tailoring(cv_text: str, job_desc: str) -> Tuple[int, Dict[str, Any]]:
    """
    Score 0-100 based on keyword/skill/phrase overlap between CV and job description.

    Uses multi-word phrase matching, tech-skill detection, and role-keyword extraction
    so that different job descriptions produce meaningfully different scores.

    Args:
        cv_text: The CV text
        job_desc: The job description text

    Returns:
        Tuple of (score, details_dict) with matched/missing keywords
    """
    cv = (cv_text or "").strip().lower()
    jd = (job_desc or "").strip().lower()

    if not jd:
        return TAILORING_DEFAULT_SCORE_NO_JD, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_JD,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_JD,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_JD,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_JD,
            "matched_keywords": [],
            "missing_keywords": [],
        }

    if not cv:
        return TAILORING_DEFAULT_SCORE_NO_CV, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_CV,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_CV,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_CV,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_CV,
            "matched_keywords": [],
            "missing_keywords": [],
        }

    # ── 1. Extract multi-word tech phrases from JD (e.g. "machine learning", "google cloud") ──
    tech_phrases = set()
    # Common multi-word tech/skill patterns
    multi_word_patterns = [
        r"(?:machine|deep)\s+learning",
        r"(?:natural\s+language\s+processing|nlp)",
        r"(?:computer\s+vision)",
        r"(?:data\s+(?:science|engineering|analysis|analytics|pipeline|warehouse))",
        r"(?:(?:full|front|back)[\s\-]?(?:end|stack))",
        r"(?:(?:google|amazon|microsoft|azure)\s+cloud)",
        r"(?:cloud\s+(?:computing|infrastructure|services|platform))",
        r"(?:(?:ci|cd)[\s/]+(?:cd|ci))",
        r"(?:version\s+control)",
        r"(?:(?:rest|graphql)\s*api)",
        r"(?:unit\s+test(?:ing|s)?)",
        r"(?:agile|scrum|kanban)\s*(?:methodology)?",
        r"(?:project\s+management)",
        r"(?:problem\s+solving)",
        r"(?:team\s+(?:lead(?:ership)?|management|work))",
        r"(?:software\s+(?:development|engineering|design))",
        r"(?:web\s+(?:development|application|services))",
        r"(?:mobile\s+(?:development|application|app))",
        r"(?:devops|dev\s+ops)",
        r"(?:micro\s*services?)",
        r"(?:object[\s\-]oriented)",
        r"(?:(?:sql|no[\s\-]?sql)\s+(?:database)?)",
    ]
    for pattern in multi_word_patterns:
        matches = re.findall(pattern, jd)
        for m in matches:
            tech_phrases.add(m.strip())

    # ── 2. Extract single-word tech/skill keywords from JD ──
    jd_words = set(re.findall(rf"[a-z][a-z0-9\+\#\.]*(?:[a-z0-9\+\#])", jd))
    cv_words_text = cv  # keep full text for phrase matching
    cv_words = set(re.findall(rf"[a-z][a-z0-9\+\#\.]*(?:[a-z0-9\+\#])", cv))

    # Remove stop words and very short words
    extra_stop = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
                  "her", "was", "one", "our", "out", "has", "with", "this", "that", "from",
                  "they", "been", "have", "will", "each", "make", "like", "long", "look",
                  "many", "some", "them", "than", "its", "over", "such", "into", "other",
                  "more", "very", "your", "what", "when", "which", "their", "about", "would",
                  "there", "could", "should", "these", "where", "being", "those", "after",
                  "most", "also", "made", "well", "back", "just", "know", "take", "come",
                  "only", "work", "need", "part", "must", "role", "join", "able", "team",
                  "good", "great", "strong", "experience", "required", "preferred",
                  "including", "working", "ability", "responsible", "responsibilities",
                  "requirements", "qualifications", "looking", "opportunity", "company",
                  "position", "ideal", "candidate", "years", "minimum", "plus", "etc"}
    all_stop = STOP_WORDS | extra_stop
    jd_key = {w for w in jd_words if w not in all_stop and len(w) >= TAILORING_MIN_WORD_LENGTH}

    if not jd_key and not tech_phrases:
        return TAILORING_DEFAULT_SCORE_NO_KEYWORDS, {
            "keyword_match_rate": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "skill_match_rate": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "experience_relevance": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "alignment_score": TAILORING_DEFAULT_SCORE_NO_KEYWORDS,
            "matched_keywords": [],
            "missing_keywords": [],
        }

    # ── 3. Match single keywords ──
    matched_single = jd_key & cv_words
    missing_single = jd_key - cv_words

    # ── 4. Match multi-word phrases ──
    matched_phrases = set()
    missing_phrases = set()
    for phrase in tech_phrases:
        if phrase in cv_words_text:
            matched_phrases.add(phrase)
        else:
            missing_phrases.add(phrase)

    # ── 5. Calculate scores ──
    total_items = len(jd_key) + len(tech_phrases)
    matched_items = len(matched_single) + len(matched_phrases)

    if total_items == 0:
        keyword_match_rate = TAILORING_DEFAULT_SCORE_NO_KEYWORDS
    else:
        keyword_match_rate = min(MAX_SCORE, int((matched_items / total_items) * 100))

    # Skill match: weight tech phrases higher (they're more specific)
    if tech_phrases:
        phrase_rate = len(matched_phrases) / len(tech_phrases) if tech_phrases else 0
        single_rate = len(matched_single) / len(jd_key) if jd_key else 0
        skill_match = min(MAX_SCORE, int(phrase_rate * 60 + single_rate * 40))
    else:
        skill_match = keyword_match_rate

    # Experience relevance: based on how many role-specific terms match
    experience_relevance = int((keyword_match_rate + skill_match) / 2)

    # Final alignment score: weighted combination
    alignment_score = int(keyword_match_rate * 0.4 + skill_match * 0.35 + experience_relevance * 0.25)
    alignment_score = max(MIN_SCORE, min(MAX_SCORE, alignment_score))

    # Build readable lists (top keywords only, min 3 chars)
    matched_list = sorted(matched_phrases | {w for w in matched_single if len(w) >= 3})[:20]
    missing_list = sorted(missing_phrases | {w for w in missing_single if len(w) >= 3})[:20]

    details = {
        "keyword_match_rate": keyword_match_rate,
        "skill_match_rate": skill_match,
        "experience_relevance": experience_relevance,
        "alignment_score": alignment_score,
        "matched_keywords": matched_list,
        "missing_keywords": missing_list,
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
