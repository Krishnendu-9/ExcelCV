"""
Scoring Module - Programmatic score calculations for CV analysis.

This module contains all scoring calculation functions that analyze CV text
programmatically, independent of AI analysis. These scores can be blended
with AI-provided scores for more accurate results.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from src.services.scoring_constants import (
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
    QUANTIFY_SCORE_MULTIPLIER,
    REPETITION_MIN_WORDS,
    REPETITION_VERB_REPEAT_THRESHOLD,
    REPETITION_PENALTY_PER_EXTRA,
    REPETITION_MAX_FLAGGED_DISPLAY,
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
    STOP_WORDS,
    TECH_ACRONYMS,
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


def _extract_experience_sections(cv_text: str) -> str:
    """
    Extract text from experience and project sections of a CV.

    Identifies section headers and returns only the content between
    experience/project headers and the next section header.
    Falls back to the full text if no clear sections are detected.
    """
    text = (cv_text or "").strip()
    if not text:
        return ""

    lines = text.split("\n")

    # Patterns for experience / project section headers
    exp_pattern = re.compile(
        r"^(?:professional\s+)?(?:work\s+)?experience"
        r"|^work\s+history|^employment(?:\s+history)?"
        r"|^career(?:\s+history)?"
        r"|^(?:personal|academic|key|side)?\s*projects?"
        r"|^internships?",
        re.I,
    )

    # Patterns for ANY section header (used to find where sections end)
    any_section_pattern = re.compile(
        r"^(?:professional\s+)?(?:work\s+)?experience"
        r"|^work\s+history|^employment(?:\s+history)?"
        r"|^career(?:\s+history)?"
        r"|^(?:personal|academic|key|side)?\s*projects?"
        r"|^internships?"
        r"|^education|^academic\s+(?:background|qualifications?)"
        r"|^(?:technical\s+)?skills?|^core\s+competenc|^expertise"
        r"|^(?:professional\s+)?summary|^objectives?|^profiles?"
        r"|^about\s+me"
        r"|^contact(?:\s+(?:info|information|details))?"
        r"|^personal\s+(?:information|details)"
        r"|^certifications?|^licen[sc]es?"
        r"|^awards?|^honou?rs?|^achievements?"
        r"|^languages?|^interests?|^hobbies|^references"
        r"|^publications?|^volunteer(?:ing)?|^activities"
        r"|^training|^courses?|^extracurricular",
        re.I,
    )

    # Detect section boundaries
    section_starts: list = []  # [(line_index, is_experience_section)]
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Section headers are typically short and standalone
        clean = re.sub(r"[:\-â€“â€”|/\\]+$", "", stripped).strip()
        if len(clean) > 60:
            continue
        if any_section_pattern.search(clean):
            is_exp = bool(exp_pattern.search(clean))
            section_starts.append((i, is_exp))

    if not section_starts:
        # No recognisable sections â†’ return full text as fallback
        return text

    # Collect text from experience-related sections only
    chunks: list = []
    for idx, (start_line, is_exp) in enumerate(section_starts):
        if not is_exp:
            continue
        end_line = (
            section_starts[idx + 1][0]
            if idx + 1 < len(section_starts)
            else len(lines)
        )
        chunk = "\n".join(lines[start_line + 1 : end_line])
        chunks.append(chunk)

    return "\n".join(chunks) if chunks else text


# Common bullet-point lead characters found in PDF-extracted text
_BULLET_CHARS_RE = re.compile(r"^[â€¢Â·â–ªâ–¸â–ºâž¤\u2022\u2023\u25E6\u2043\u2219\*]\s*")

# Date patterns that appear in job-title / header lines
_DATE_RANGE_RE = re.compile(
    r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s*)?\d{4}\s*[-â€“â€”/]+\s*"
    r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s*)?(?:Present|Current|Now|\d{4})",
    re.I,
)

# Past-tense action verbs that typically START a resume bullet point.
# Used to detect bullet boundaries in PDF-extracted text where the
# bullet character (â€¢) may be absent or already stripped.
_ACTION_VERB_START_RE = re.compile(
    r"^(?:Accelerated|Achieved|Administered|Analyzed|Analysed|Applied|"
    r"Architected|Assembled|Assisted|Automated|"
    r"Built|Coached|Collaborated|Communicated|Compiled|Completed|"
    r"Conducted|Configured|Consolidated|Constructed|Contributed|"
    r"Coordinated|Created|Customized|"
    r"Decreased|Delivered|Deployed|Designed|Developed|Directed|"
    r"Drove|"
    r"Eliminated|Enabled|Engineered|Enhanced|Ensured|Established|"
    r"Evaluated|Executed|Expanded|"
    r"Facilitated|Formulated|Founded|"
    r"Generated|Guided|"
    r"Handled|Headed|"
    r"Identified|Implemented|Improved|Increased|Initiated|Integrated|"
    r"Introduced|Investigated|"
    r"Launched|Led|Leveraged|"
    r"Maintained|Managed|Mentored|Migrated|Modernized|Monitored|"
    r"Negotiated|"
    r"Operated|Optimized|Orchestrated|Organized|Overhauled|Oversaw|"
    r"Partnered|Performed|Pioneered|Planned|Prepared|Presented|"
    r"Produced|Programmed|Provided|Published|"
    r"Rebuilt|Reconciled|Redesigned|Reduced|Re-?engineered|"
    r"Refactored|Resolved|Restructured|Revamped|Reviewed|"
    r"Secured|Set\s+up|Simplified|Spearheaded|Standardized|"
    r"Streamlined|Strengthened|Supervised|Supported|"
    r"Trained|Transformed|Translated|Troubleshot|"
    r"Unified|Updated|Upgraded|Utilized|"
    r"Validated|Wrote)\b",
)


def _rejoin_pdf_lines(text: str) -> list:
    """
    Reassemble PDF-fragmented text into complete bullet points.

    PDF text extraction breaks lines at visual line-wrap boundaries, so one
    bullet point spanning 2-3 visual lines becomes 2-3 separate ``\\n``-separated
    lines.  This function:
      1. Fixes hyphenated word breaks  (``prop-\\nerty`` â†’ ``property``)
      2. Detects bullet boundaries via bullet chars (â€¢) **and** action-verb starts
      3. Joins continuation lines with the previous bullet
      4. Returns a list of complete text items (bullets + non-bullet lines)
    """
    if not text or not text.strip():
        return []

    # â”€â”€ Step 1: fix hyphenated word breaks at line endings â”€â”€
    # "prop-\nerty" â†’ "property",  "conser-\nvation" â†’ "conservation"
    text = re.sub(r"-\s*\n\s*([a-z])", r"\1", text)

    # â”€â”€ Step 2: walk lines, merging continuations â”€â”€
    raw_lines = text.split("\n")
    items: list = []
    current = ""

    for raw in raw_lines:
        stripped = raw.strip()

        # Blank line â†’ flush current item
        if not stripped:
            if current:
                items.append(current)
                current = ""
            continue

        # Does this line start with a bullet character?
        is_bullet_start = bool(_BULLET_CHARS_RE.match(stripped))

        if is_bullet_start:
            # Save previous item, start a new bullet (strip the marker)
            if current:
                items.append(current)
            current = _BULLET_CHARS_RE.sub("", stripped).strip()
            continue

        # Does this line start with a past-tense action verb?
        # (very strong signal that a new bullet point begins here)
        is_action_start = bool(_ACTION_VERB_START_RE.match(stripped))

        if is_action_start:
            if current:
                items.append(current)
            current = stripped
            continue

        # If there's no current buffer, start a new item
        if not current:
            current = stripped
            continue

        # â”€â”€ Decide: continuation of current item  vs  new item â”€â”€
        prev_ends_sentence = current.rstrip()[-1:] in ".!?;"
        starts_lower = stripped[0:1].islower()

        # Continuation when:  previous line didn't end a sentence, OR
        #                     this line starts with a lowercase letter
        if not prev_ends_sentence or starts_lower:
            current = current.rstrip() + " " + stripped
        else:
            items.append(current)
            current = stripped

    if current:
        items.append(current)

    return items


def _is_experience_bullet(line: str) -> bool:
    """
    Return True if *line* looks like an experience / achievement bullet point
    rather than a job title, company name, date range, or section header.

    Expects *line* to already be rejoined (not a PDF fragment).
    """
    stripped = line.strip()

    # Too short â†’ likely a title, company name, or date
    if len(stripped) < 35:
        return False

    # Lines that contain a date-range pattern are usually job-title / header lines
    # e.g. "Junior AI Developer AKC Techno Solz, Feb 2025 â€“ Present"
    if _DATE_RANGE_RE.search(stripped):
        return False

    # Lines that are mostly just a job-title / company-name pattern
    # (high ratio of title-case words, no verb-like content)
    words = stripped.split()
    if len(words) <= 10:
        title_words = sum(1 for w in words if w[0:1].isupper() and len(w) > 1)
        if title_words / max(1, len(words)) >= 0.6:
            return False

    # Skip lines that look like a tech-stack / skills listing
    # e.g. "Python, Computer Vision, TensorFlow, OpenCV"
    if len(words) <= 12:
        comma_count = stripped.count(",")
        if comma_count >= 3 and comma_count >= len(words) // 2:
            return False

    # Skip lines that look like location / company-name combos
    # e.g. "ABC Corp, New York, NY" or "Remote | Full-time"
    if len(stripped) < 70 and re.match(r"^[A-Z][\w\s&.,]+(?:\|[^|]+)?$", stripped):
        comma_count = stripped.count(",")
        if comma_count >= 2 or re.search(
            r"\b(?:remote|full[\s-]?time|part[\s-]?time|contract|freelance|hybrid)\b",
            stripped,
            re.I,
        ):
            return False

    return True


def _line_has_metric(line: str) -> bool:
    """
    Return True only if the line contains a **real quantifiable metric** â€”
    an actual number, percentage, dollar amount, or measurable result.

    Vague improvement words (improved, reduced, increasing) WITHOUT
    accompanying numbers do NOT count as quantification.

    Date/year references embedded in the text (from PDF extraction merging
    company info) are stripped before checking so they don't produce false
    positives.
    """
    # â”€â”€ Strip date / year references â”€â”€
    # Remove "Month Year" patterns  (e.g. "Feb 2025", "January 2024")
    cleaned = re.sub(
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\.?\s*\d{1,4}",
        "",
        line,
        flags=re.I,
    )
    # Remove standalone 4-digit years (1990â€“2039 covers typical CVs)
    cleaned = re.sub(r"\b(?:19|20)\d{2}\b", "", cleaned)
    # Remove "â€“ Present" / "â€“ Current" date-range tails left over
    cleaned = re.sub(r"[-â€“â€”]\s*(?:Present|Current|Now)\b", "", cleaned, flags=re.I)

    # â”€â”€ Check if any digit remains â†’ actual metric â”€â”€
    if re.search(r"\d", cleaned):
        return True

    # â”€â”€ Written-out large-scale numbers (without digits) â”€â”€
    if re.search(r"\b(?:million|billion|trillion)\b", cleaned, re.I):
        return True

    return False


def calculate_quantifying_impact(cv_text: str) -> Tuple[int, Dict]:
    """
    Score 0-100 based on presence of numbers, %, $, and measurable results
    in experience / project bullet points of the CV.

    Only analyses lines from the experience and project sections, filtering
    out names, section headers, job titles, company names, and date lines.
    PDF-wrapped lines are rejoined before analysis so each bullet point is
    treated as a single item.

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

    # 1) Extract only the experience / project sections
    experience_text = _extract_experience_sections(text)

    # 2) Rejoin PDF-fragmented lines into complete bullet points
    all_items = _rejoin_pdf_lines(experience_text)

    # 3) Keep only lines that look like genuine achievement/responsibility bullets
    lines = [item for item in all_items if _is_experience_bullet(item)]

    if not lines:
        # No experience bullet points found â€” give a moderate baseline score
        return QUANTIFY_BASE_SCORE, {
            "details": "No experience bullet points detected to analyse.",
            "total_lines": 0,
            "quantified_count": 0,
            "non_quantified_lines": [],
        }

    total = len(lines)
    quantified = 0
    non_quantified = []

    for line in lines:
        if _line_has_metric(line):
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
        "non_quantified_lines": non_quantified[:15],  # Limit for display
    }


def calculate_repetition(cv_text: str) -> Tuple[int, Dict]:
    """
    Score 0-100: higher = less repetition.

    Focuses on **action verbs and descriptive words** that the candidate can
    actually replace with synonyms (words present in ``WORD_SYNONYMS``).
    Generic domain terms like "data", "system", "application" are ignored
    because flagging them is not actionable.

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
        return MAX_SCORE, {
            "details": "Too little text to assess repetition.",
            "repeated_words": [],
        }

    # Count frequencies only for words that have synonym suggestions.
    # Skip present-participle (-ing) forms: these are structural connector
    # words in mid-sentence ("...using Django", "...ensuring availability")
    # and not the bullet-starting action verbs that recruiters want varied.
    verb_counts: Dict[str, int] = {}
    for w in words:
        if w in WORD_SYNONYMS and not w.endswith("ing"):
            verb_counts[w] = verb_counts.get(w, 0) + 1

    # Flag verbs repeated >= threshold times
    flagged: list[Dict[str, Any]] = []
    for word, count in sorted(verb_counts.items(), key=lambda x: -x[1]):
        if count < REPETITION_VERB_REPEAT_THRESHOLD:
            continue
        flagged.append({
            "word": word,
            "count": count,
            "suggestions": WORD_SYNONYMS[word][:3],
        })

    # â”€â”€ Scoring â”€â”€
    # Start at 100; deduct for each extra repeat beyond (threshold âˆ’ 1).
    penalty = 0
    for item in flagged:
        extra = item["count"] - (REPETITION_VERB_REPEAT_THRESHOLD - 1)
        penalty += extra * REPETITION_PENALTY_PER_EXTRA
    score = max(MIN_SCORE, min(MAX_SCORE, 100 - penalty))

    top_names = [f["word"] for f in flagged[:3]]
    details = (
        f"Checked {len(verb_counts)} action verbs across {total} words. "
        + (
            f"Consider varying: {', '.join(top_names)}."
            if top_names
            else "Good variety in action verbs."
        )
    )

    return score, {
        "details": details,
        "repeated_words": flagged[:REPETITION_MAX_FLAGGED_DISPLAY],
    }


def calculate_spelling_grammar(cv_text: str) -> Tuple[int, Dict]:
    """
    Heuristic score 0-100 for formatting / consistency (no spell-check lib).

    Checks performed:
      1. Multiple consecutive spaces
      2. Excessive all-caps words (excluding known tech acronyms & CV headers)
      3. Inconsistent bullet-point characters
      4. Bullet points missing ending punctuation (on *rejoined* lines only)

    Note: "Incorrect spacing around punctuation" was removed because PDF text
    extraction routinely introduces phantom spaces before commas / periods
    that do not exist in the actual document.

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
    issue_labels: list[str] = []
    issues_list: list[Dict] = []

    # â”€â”€ 1. Multiple consecutive spaces â”€â”€
    # Only flag runs of exactly 2 spaces between content characters.
    # Runs of 3+ spaces are almost always PDF column-alignment artefacts
    # (e.g. "Junior AI Developer                AKC Techno Solz") and should
    # not be reported as formatting errors.
    double_count = len(re.findall(r"(?<!\s)  (?!\s)", text))
    if double_count > 0:
        double_matches = re.findall(
            r".{0,20}(?<!\s)  (?!\s).{0,20}", text
        )
        deduction = min(
            SPELLING_DOUBLE_SPACE_MAX_PENALTY,
            double_count * SPELLING_DOUBLE_SPACE_PENALTY_PER_INSTANCE,
        )
        score -= deduction
        issue_labels.append("multiple consecutive spaces")
        issues_list.append({
            "type": "double_space",
            "label": "Multiple consecutive spaces",
            "count": double_count,
            "examples": [m.strip() for m in double_matches[:3]],
        })

    # â”€â”€ 2. Excessive all-caps words (skip tech acronyms & section headers) â”€â”€
    long_caps = re.findall(
        rf"\b[A-Z]{{{SPELLING_ALL_CAPS_MIN_LENGTH},}}\b", text
    )
    non_tech_caps = [w for w in long_caps if w not in TECH_ACRONYMS]
    if len(non_tech_caps) > SPELLING_ALL_CAPS_THRESHOLD:
        score -= min(SPELLING_ALL_CAPS_MAX_PENALTY, len(non_tech_caps))
        issue_labels.append("excessive all-caps words")
        issues_list.append({
            "type": "all_caps",
            "label": "Excessive all-caps words",
            "count": len(non_tech_caps),
            "examples": list(dict.fromkeys(non_tech_caps))[:5],
        })

    # â”€â”€ 3. Inconsistent bullet-point characters â”€â”€
    bullet_chars = re.findall(
        r"^[\s]*([â€¢Â·â–ªâ–¸â–ºâž¤\-\*])", text, re.MULTILINE
    )
    unique_bullets = set(bullet_chars)
    if len(unique_bullets) > 2:
        issues_list.append({
            "type": "inconsistent_bullets",
            "label": "Inconsistent bullet point characters",
            "count": len(unique_bullets),
            "examples": list(unique_bullets),
        })

    # â”€â”€ 4. Bullet points missing ending punctuation â”€â”€
    # Use PDF-line rejoining so we check *complete* bullets, not fragments.
    experience_text = _extract_experience_sections(text)
    bullets = _rejoin_pdf_lines(experience_text)
    real_bullets = [b for b in bullets if _is_experience_bullet(b)]
    bullets_no_period = [
        b for b in real_bullets if b and b.rstrip()[-1:] not in ".!?:;"
    ]
    if len(bullets_no_period) > 2:
        issues_list.append({
            "type": "missing_period",
            "label": "Bullet points missing ending punctuation",
            "count": len(bullets_no_period),
            "examples": [
                b[:80] + ("..." if len(b) > 80 else "")
                for b in bullets_no_period[:3]
            ],
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
    # remnants like "/envelâŒ¢pe" for envelope or "â™‚phone-alt" for phone icon.
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

    # â”€â”€ Phone number â”€â”€
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

    # â”€â”€ Email address â”€â”€
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", cleaned)
    if email_match:
        found.append({"type": "email", "label": "Email address", "value": email_match.group()})
    else:
        missing.append({
            "type": "email",
            "label": "Email address",
            "message": "No email address found. Include a professional email.",
        })

    # â”€â”€ LinkedIn â”€â”€
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

    # â”€â”€ GitHub â”€â”€
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

    # â”€â”€ Portfolio / Website â”€â”€
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

    # â”€â”€ Location / Address â”€â”€
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


def calculate_sections(cv_text: str) -> Tuple[int, Dict[str, Any]]:
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
            "file_format": {
                "is_supported_format": False,
                "is_pdf": False,
                "is_docx": False,
                "file_name": "",
                "file_size_kb": 0,
                "file_size_mb": 0,
                "size_ok": False,
            },
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

    # File format and size
    lower_name = file_name.lower() if file_name else ""
    is_pdf = lower_name.endswith(".pdf")
    is_docx = lower_name.endswith(".docx")
    is_supported_format = (is_pdf or is_docx) if file_name else True
    file_size_kb = round(file_size_bytes / 1024, 1) if file_size_bytes else 0
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2) if file_size_bytes else 0
    size_ok = file_size_bytes <= 2 * 1024 * 1024 if file_size_bytes else True  # <=2MB
    if not is_supported_format:
        issues.append("Unsupported file format (use PDF or DOCX)")
    file_format_info = {
        "is_supported_format": is_supported_format,
        "is_pdf": is_pdf,
        "is_docx": is_docx,
        "file_name": file_name,
        "file_size_kb": file_size_kb,
        "file_size_mb": file_size_mb,
        "size_ok": size_ok,
    }

    # Email address check
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

    # Header links (URLs in the header/top area)
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
        # Reflect actual formatting check result instead of always reporting True.
        "standard_formatting": has_headers and text_based and not issues,
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

    # â”€â”€ 1. Extract multi-word tech phrases from JD (e.g. "machine learning", "google cloud") â”€â”€
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

    # â”€â”€ 2. Extract single-word tech/skill keywords from JD â”€â”€
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

    # â”€â”€ 3. Match single keywords â”€â”€
    matched_single = jd_key & cv_words
    missing_single = jd_key - cv_words

    # â”€â”€ 4. Match multi-word phrases â”€â”€
    matched_phrases = set()
    missing_phrases = set()
    for phrase in tech_phrases:
        if phrase in cv_words_text:
            matched_phrases.add(phrase)
        else:
            missing_phrases.add(phrase)

    # â”€â”€ 5. Calculate scores â”€â”€
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


def calculate_final_score_breakdown(
    ats_parse_rate: int,
    quant_score: int,
    repetition_score: int,
    spelling_score: int,
    tailoring_score: int,
    sections_score: int,
    ats_essentials_score: int,
    contact_score: int,
    has_job_description: bool,
) -> Dict[str, Any]:
    """
    Compute a transparent final score with weighted component breakdown.

    Returns:
        Dict with:
            final_score: int (0-100)
            mode: str
            content_average: int
            components: list[{id,label,score,weight,weighted_points}]
            formula: human-readable formula string
    """
    content_average = normalize_score(
        int((ats_parse_rate + quant_score + repetition_score + spelling_score) / 4)
    )

    if has_job_description:
        components = [
            ("content_quality", "Content Quality", content_average, 0.30),
            ("jd_alignment", "JD Alignment", normalize_score(tailoring_score), 0.25),
            ("sections", "Sections", normalize_score(sections_score), 0.15),
            ("ats_essentials", "ATS Essentials", normalize_score(ats_essentials_score), 0.15),
            ("contact", "Contact Completeness", normalize_score(contact_score), 0.15),
        ]
        mode = "jd_aligned"
    else:
        components = [
            ("content_quality", "Content Quality", content_average, 0.35),
            ("sections", "Sections", normalize_score(sections_score), 0.25),
            ("ats_essentials", "ATS Essentials", normalize_score(ats_essentials_score), 0.25),
            ("contact", "Contact Completeness", normalize_score(contact_score), 0.15),
        ]
        mode = "no_jd"

    breakdown_rows: List[Dict[str, Any]] = []
    weighted_total = 0.0
    formula_parts: List[str] = []
    for comp_id, label, score, weight in components:
        weighted_points = round(score * weight, 2)
        weighted_total += weighted_points
        formula_parts.append(f"{weight:.2f}*{score}")
        breakdown_rows.append(
            {
                "id": comp_id,
                "label": label,
                "score": normalize_score(score),
                "weight": weight,
                "weighted_points": weighted_points,
            }
        )

    final_score = normalize_score(int(round(weighted_total)))
    return {
        "final_score": final_score,
        "mode": mode,
        "content_average": content_average,
        "components": breakdown_rows,
        "formula": " + ".join(formula_parts),
    }


def build_jd_skill_matrix(
    cv_text: str,
    job_desc: str,
    tailoring_details: Optional[Dict[str, Any]] = None,
    max_items: int = 24,
) -> List[Dict[str, str]]:
    """
    Build a JD-to-resume skill evidence matrix with Found/Partial/Missing status.
    """
    cv_raw = (cv_text or "").strip()
    jd_raw = (job_desc or "").strip()
    if not cv_raw or not jd_raw:
        return []

    details = tailoring_details or calculate_tailoring(cv_raw, jd_raw)[1]
    matched = list(details.get("matched_keywords", []))
    missing = list(details.get("missing_keywords", []))
    if not matched and not missing:
        return []

    skills = sorted(set([*matched, *missing]), key=lambda x: (len(str(x)), str(x)))[:max_items]
    cv_lower = cv_raw.lower()
    cv_lines = [ln.strip() for ln in cv_raw.splitlines() if ln.strip()]

    def _best_evidence_line(skill: str) -> str:
        skill_lower = skill.lower()
        # First pass: exact phrase match.
        for line in cv_lines:
            if skill_lower in line.lower():
                return line
        # Second pass: best token overlap.
        tokens = [t for t in re.findall(r"[a-z0-9\+\#\.]+", skill_lower) if len(t) >= 3]
        if not tokens:
            return ""
        best_line = ""
        best_hits = 0
        for line in cv_lines:
            line_lower = line.lower()
            hits = sum(1 for t in tokens if t in line_lower)
            if hits > best_hits:
                best_hits = hits
                best_line = line
        return best_line if best_hits > 0 else ""

    matrix: List[Dict[str, str]] = []
    for skill in skills:
        skill_str = str(skill).strip()
        if not skill_str:
            continue
        skill_lower = skill_str.lower()
        tokens = [t for t in re.findall(r"[a-z0-9\+\#\.]+", skill_lower) if len(t) >= 3]

        if skill_lower in cv_lower:
            status = "Found"
            confidence = "High"
        elif tokens and any(t in cv_lower for t in tokens):
            status = "Partial"
            confidence = "Medium"
        else:
            status = "Missing"
            confidence = "Low"

        evidence = _best_evidence_line(skill_str)
        if not evidence:
            evidence = "No direct evidence found in resume text."
        elif len(evidence) > 140:
            evidence = evidence[:137].rstrip() + "..."

        matrix.append(
            {
                "skill": skill_str,
                "status": status,
                "confidence": confidence,
                "evidence": evidence,
            }
        )

    return matrix


def generate_section_rewrite_recommendations(
    cv_text: str,
    quantifying_impact_data: Optional[Dict[str, Any]] = None,
    repetition_data: Optional[Dict[str, Any]] = None,
    max_items: int = 8,
) -> List[Dict[str, str]]:
    """
    Generate section-level before/after rewrite recommendations.

    Heuristic approach:
    - Prioritize non-quantified experience lines.
    - Replace repeated verbs where synonym suggestions exist.
    - Add measurable-impact placeholders for actionable rewrites.
    """
    quant_data = quantifying_impact_data or {}
    rep_data = repetition_data or {}

    repeated_map: Dict[str, List[str]] = {}
    for row in rep_data.get("repeated_words", []) or []:
        word = str(row.get("word", "")).strip().lower()
        suggestions = [str(s).strip() for s in row.get("suggestions", []) if str(s).strip()]
        if word and suggestions:
            repeated_map[word] = suggestions

    candidates: List[str] = []
    for line in quant_data.get("non_quantified_lines", []) or []:
        line_s = str(line).strip()
        if line_s and line_s not in candidates:
            candidates.append(line_s)

    if not candidates:
        # Fallback: use lines that contain repeated words.
        for raw_line in (cv_text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line_lower = line.lower()
            if any(re.search(rf"\b{re.escape(w)}\b", line_lower) for w in repeated_map):
                if line not in candidates:
                    candidates.append(line)
            if len(candidates) >= max_items:
                break

    def _rewrite_line(line: str) -> Tuple[str, str]:
        rewritten = line
        rationale_parts: List[str] = []

        # Improve repeated action verb, if present.
        for word, suggestions in repeated_map.items():
            if not suggestions:
                continue
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.I)
            if pattern.search(rewritten):
                replacement = suggestions[0]
                rewritten = pattern.sub(replacement, rewritten, count=1)
                rationale_parts.append(f"replaced repeated verb '{word}' with '{replacement}'")
                break

        # Add measurable outcome if no metric is present.
        if not _line_has_metric(rewritten):
            rewritten = rewritten.rstrip(". ")
            rewritten += " by [X%], improving [outcome] by [Y]."
            rationale_parts.append("added measurable impact placeholders")

        if not rewritten.endswith("."):
            rewritten += "."

        rationale = "; ".join(rationale_parts) if rationale_parts else "improved clarity and impact"
        return rewritten, rationale

    recommendations: List[Dict[str, str]] = []
    for line in candidates[:max_items]:
        after, rationale = _rewrite_line(line)
        if after.strip() == line.strip():
            continue
        recommendations.append(
            {
                "section": "Experience / Projects",
                "before": line,
                "after": after,
                "rationale": rationale,
            }
        )

    return recommendations

