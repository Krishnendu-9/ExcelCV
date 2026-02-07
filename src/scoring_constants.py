"""
Scoring Constants - Centralized configuration for scoring thresholds and status values.

This module contains all constants used for score calculations, status thresholds,
and metric-specific configurations to maintain consistency across the application.
"""

from typing import Dict, Tuple

# Status Thresholds for Different Metrics
# Format: (ok_min, warn_min) - scores >= ok_min = "ok", >= warn_min = "warn", else "error"
ATS_PARSE_RATE_THRESHOLDS: Tuple[int, int] = (80, 60)
QUANTIFYING_IMPACT_THRESHOLDS: Tuple[int, int] = (70, 50)
REPETITION_THRESHOLDS: Tuple[int, int] = (80, 60)
SPELLING_GRAMMAR_THRESHOLDS: Tuple[int, int] = (90, 70)

# ATS Parse Rate - Text Length Thresholds
ATS_PARSE_TEXT_LENGTH_GOOD = 800  # characters
ATS_PARSE_TEXT_LENGTH_MODERATE = 400
ATS_PARSE_TEXT_LENGTH_POOR = 100
ATS_PARSE_BASE_SCORE_GOOD = 85
ATS_PARSE_BASE_SCORE_MODERATE = 70
ATS_PARSE_BASE_SCORE_POOR = 50
ATS_PARSE_BASE_SCORE_VERY_POOR = 20
ATS_PARSE_SECTION_BONUS = 10  # Bonus for having standard sections

# Quantifying Impact - Scoring Parameters
QUANTIFY_MIN_LINE_LENGTH = 10  # Minimum line length to consider
QUANTIFY_BASE_SCORE = 40  # Base score (minimum)
QUANTIFY_SCORE_MULTIPLIER = 0.6  # Multiplier for percentage

# Repetition - Scoring Parameters
REPETITION_MIN_WORDS = 5  # Minimum words to assess
REPETITION_BASE_SCORE = 50  # Base score
REPETITION_UNIQUE_RATIO_MULTIPLIER = 50  # Multiplier for unique ratio
REPETITION_MAX_PENALTY = 40  # Maximum penalty for heavy repetition
REPETITION_PENALTY_THRESHOLD = 2  # Words repeated more than this get penalty
REPETITION_TOP_WORDS_TO_CHECK = 20  # Check top N most common words
REPETITION_TOP_WORDS_TO_SUGGEST = 5  # Suggest top N repeated words
REPETITION_SUGGEST_THRESHOLD = 2  # Only suggest words repeated more than this

# Spelling & Grammar - Penalty Values
SPELLING_BASE_SCORE = 100
SPELLING_DOUBLE_SPACE_PENALTY_PER_INSTANCE = 2
SPELLING_DOUBLE_SPACE_MAX_PENALTY = 15
SPELLING_PUNCTUATION_PENALTY_PER_INSTANCE = 2
SPELLING_PUNCTUATION_MAX_PENALTY = 10
SPELLING_ALL_CAPS_THRESHOLD = 3  # More than this many all-caps words
SPELLING_ALL_CAPS_MIN_LENGTH = 4  # Minimum length for all-caps penalty
SPELLING_ALL_CAPS_MAX_PENALTY = 10
SPELLING_GOOD_SCORE_THRESHOLD = 85

# Sections - Scoring Parameters
SECTIONS_SCORE_PER_SECTION = 20  # Points per section found
SECTIONS_MAX_SCORE = 100  # Maximum score (all 5 sections)

# ATS Essentials - Scoring Parameters
ATS_ESSENTIALS_BASE_SCORE = 60
ATS_ESSENTIALS_HEADERS_BONUS = 25
ATS_ESSENTIALS_TEXT_BASED_BONUS = 10
ATS_ESSENTIALS_WORD_COUNT_BONUS_THRESHOLD = 200
ATS_ESSENTIALS_WORD_COUNT_BONUS = 5
ATS_ESSENTIALS_KEYWORD_DENSITY_DIVISOR = 5  # word_count / this = density score

# Tailoring - Scoring Parameters
TAILORING_MIN_WORD_LENGTH = 3  # Minimum word length to consider
TAILORING_DEFAULT_SCORE_NO_JD = 80  # Default when no job description
TAILORING_DEFAULT_SCORE_NO_CV = 0  # Default when no CV
TAILORING_DEFAULT_SCORE_NO_KEYWORDS = 70  # Default when no keywords extracted

# Stop words to exclude from keyword matching
STOP_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "have", "has", "are",
    "was", "were", "been", "being", "will", "your", "you", "their", "they",
    "would", "could", "should", "about", "when", "which", "what", "where",
    "into", "through", "during", "before", "after", "above", "below"
}

# Section Keywords for Detection
SECTION_KEYWORDS: Dict[str, list] = {
    "contact": ["contact", "email", "phone", "mobile", "address", "@", "linkedin"],
    "experience": ["experience", "work history", "employment", "professional experience", "career"],
    "education": ["education", "academic", "degree", "university", "college", "bachelor", "master", "phd"],
    "skills": ["skills", "technical skills", "competencies", "expertise"],
    "summary": ["summary", "objective", "profile", "about me", "professional summary"],
}

# Metric Status Values
STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_ERROR = "error"
STATUS_LOCK = "lock"

# Score Bounds
MIN_SCORE = 0
MAX_SCORE = 100

# Synonym suggestions for repeated words (common resume action verbs)
WORD_SYNONYMS: Dict[str, list] = {
    "designed": ["planned", "created", "developed"],
    "developed": ["enhanced", "expanded", "improved"],
    "managed": ["directed", "led", "coordinated"],
    "implemented": ["executed", "deployed", "launched"],
    "created": ["built", "produced", "designed"],
    "improved": ["enhanced", "optimized", "refined"],
    "built": ["constructed", "created", "assembled"],
    "worked": ["collaborated", "contributed", "operated"],
    "used": ["utilized", "leveraged", "applied"],
    "made": ["produced", "created", "constructed"],
    "helped": ["assisted", "supported", "facilitated"],
    "responsible": ["accountable", "tasked with", "oversaw"],
    "led": ["directed", "guided", "spearheaded"],
    "handled": ["managed", "oversaw", "addressed"],
    "supported": ["assisted", "aided", "facilitated"],
    "maintained": ["preserved", "sustained", "managed"],
    "performed": ["executed", "conducted", "carried out"],
    "provided": ["delivered", "supplied", "offered"],
    "conducted": ["performed", "executed", "carried out"],
    "assisted": ["supported", "helped", "contributed to"],
    "established": ["founded", "initiated", "set up"],
    "analyzed": ["evaluated", "examined", "assessed"],
    "prepared": ["compiled", "organized", "assembled"],
    "ensured": ["guaranteed", "verified", "confirmed"],
    "collaborated": ["partnered", "cooperated", "teamed up"],
    "contributed": ["supported", "aided", "participated"],
    "integrated": ["combined", "merged", "incorporated"],
    "deployed": ["launched", "released", "rolled out"],
    "optimized": ["improved", "enhanced", "streamlined"],
}


def get_metric_thresholds(metric_name: str) -> Tuple[int, int]:
    """
    Get status thresholds for a specific metric.
    
    Args:
        metric_name: Name of the metric (e.g., "ats_parse_rate", "quantifying_impact")
    
    Returns:
        Tuple of (ok_min, warn_min) thresholds
    """
    thresholds_map = {
        "ats_parse_rate": ATS_PARSE_RATE_THRESHOLDS,
        "quantifying_impact": QUANTIFYING_IMPACT_THRESHOLDS,
        "repetition": REPETITION_THRESHOLDS,
        "spelling_grammar": SPELLING_GRAMMAR_THRESHOLDS,
    }
    return thresholds_map.get(metric_name.lower(), (80, 60))
