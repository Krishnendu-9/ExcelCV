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
REPETITION_MIN_WORDS = 20  # Minimum words to assess
REPETITION_VERB_REPEAT_THRESHOLD = 3  # Flag verbs repeated >= this many times
REPETITION_PENALTY_PER_EXTRA = 12  # Score penalty per extra repeat beyond threshold-1
REPETITION_MAX_FLAGGED_DISPLAY = 8  # Max repeated words to show in UI

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

# Technical acronyms & common CV terms that are legitimately all-caps.
# These are excluded from the "excessive all-caps" check.
TECH_ACRONYMS: set = {
    # ── AI / ML ──
    "BERT", "BART", "CLIP", "DALL", "LSTM", "YOLO", "RCNN", "CUDA", "RLHF",
    "LLAMA", "LLMS", "GPTS", "GGUF", "GGML", "LORA", "ONNX", "MLIR",
    "NLTK", "DLIB", "ADAM",
    # ── Programming / Frameworks ──
    "HTML", "SCSS", "SASS", "LESS", "JSON", "YAML", "TOML", "AJAX", "CORS",
    "REST", "SOAP", "GRPC", "WASM", "MERN", "MEAN", "LAMP",
    "FAST", "NUXT", "NEXT",
    # ── Cloud / DevOps / Infra ──
    "AZURE", "NGINX", "KAFKA", "REDIS", "MQTT", "HELM", "KUBE", "ISTIO",
    "CICD", "JIRA", "ASANA", "TRELLO", "LINUX", "UNIX", "BASH",
    # ── Databases ──
    "MYSQL", "MSSQL", "PSQL", "NOSQL", "SQLITE", "MONGO",
    # ── Protocols / Networking ──
    "HTTP", "HTTPS", "SMTP", "IMAP", "SFTP", "AMQP", "LDAP",
    # ── Methodologies ──
    "AGILE", "SCRUM", "SDLC", "ITIL", "LEAN", "SAFE",
    # ── File Formats ──
    "JPEG", "TIFF", "XLSX", "DOCX", "PPTX", "AVRO",
    # ── Architecture / Patterns ──
    "CRUD", "MVVM", "SAAS", "PAAS", "IAAS", "FAAS",
    # ── Common CV section headers (intentionally uppercase) ──
    "EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "SUMMARY",
    "CERTIFICATIONS", "ACHIEVEMENTS", "AWARDS", "PUBLICATIONS",
    "CONTACT", "OBJECTIVE", "INTERESTS", "ACTIVITIES",
    "PROFESSIONAL", "TECHNICAL", "VOLUNTEER", "REFERENCES",
}

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

# Synonym suggestions for repeated words (resume action verbs & descriptive words).
# Only words in this dictionary are flagged for repetition – this keeps the
# analysis focused on actionable feedback (words the user CAN replace).
WORD_SYNONYMS: Dict[str, list] = {
    # ── Past-tense action verbs (bullet-point starters) ──
    "achieved": ["accomplished", "attained", "earned"],
    "administered": ["managed", "directed", "supervised"],
    "analyzed": ["evaluated", "examined", "assessed"],
    "analysed": ["evaluated", "examined", "assessed"],
    "applied": ["utilized", "employed", "leveraged"],
    "architected": ["designed", "structured", "engineered"],
    "assembled": ["compiled", "gathered", "organized"],
    "assisted": ["supported", "helped", "contributed to"],
    "automated": ["streamlined", "mechanized", "systematized"],
    "built": ["constructed", "developed", "created"],
    "collaborated": ["partnered", "cooperated", "teamed up"],
    "communicated": ["conveyed", "presented", "articulated"],
    "compiled": ["assembled", "gathered", "collected"],
    "completed": ["finished", "accomplished", "finalized"],
    "conducted": ["performed", "executed", "carried out"],
    "configured": ["set up", "customized", "arranged"],
    "contributed": ["supported", "aided", "participated"],
    "coordinated": ["organized", "managed", "arranged"],
    "created": ["designed", "produced", "built"],
    "customized": ["tailored", "adapted", "modified"],
    "delivered": ["provided", "produced", "supplied"],
    "deployed": ["launched", "released", "rolled out"],
    "designed": ["planned", "created", "architected"],
    "developed": ["built", "created", "engineered"],
    "directed": ["led", "managed", "guided"],
    "documented": ["recorded", "cataloged", "detailed"],
    "drove": ["led", "spearheaded", "championed"],
    "enabled": ["empowered", "facilitated", "allowed"],
    "engineered": ["designed", "built", "developed"],
    "enhanced": ["improved", "upgraded", "strengthened"],
    "ensured": ["guaranteed", "verified", "confirmed"],
    "established": ["founded", "initiated", "set up"],
    "evaluated": ["assessed", "analyzed", "reviewed"],
    "executed": ["implemented", "performed", "carried out"],
    "expanded": ["grew", "extended", "broadened"],
    "facilitated": ["enabled", "supported", "coordinated"],
    "formulated": ["devised", "designed", "developed"],
    "generated": ["produced", "created", "yielded"],
    "guided": ["mentored", "directed", "advised"],
    "handled": ["managed", "oversaw", "addressed"],
    "headed": ["led", "directed", "managed"],
    "helped": ["assisted", "supported", "facilitated"],
    "identified": ["discovered", "recognized", "pinpointed"],
    "implemented": ["executed", "deployed", "launched"],
    "improved": ["enhanced", "optimized", "refined"],
    "increased": ["boosted", "raised", "expanded"],
    "initiated": ["started", "launched", "introduced"],
    "integrated": ["combined", "merged", "incorporated"],
    "investigated": ["researched", "examined", "explored"],
    "launched": ["introduced", "released", "deployed"],
    "led": ["directed", "guided", "spearheaded"],
    "leveraged": ["utilized", "harnessed", "capitalized on"],
    "maintained": ["preserved", "sustained", "managed"],
    "managed": ["directed", "led", "coordinated"],
    "mentored": ["guided", "coached", "trained"],
    "migrated": ["transitioned", "transferred", "moved"],
    "modernized": ["updated", "upgraded", "revamped"],
    "monitored": ["tracked", "observed", "supervised"],
    "negotiated": ["brokered", "mediated", "arranged"],
    "operated": ["ran", "managed", "administered"],
    "optimized": ["improved", "enhanced", "streamlined"],
    "organized": ["arranged", "coordinated", "structured"],
    "oversaw": ["supervised", "managed", "directed"],
    "partnered": ["collaborated", "cooperated", "allied"],
    "performed": ["executed", "conducted", "carried out"],
    "pioneered": ["introduced", "innovated", "initiated"],
    "planned": ["organized", "arranged", "strategized"],
    "prepared": ["compiled", "organized", "assembled"],
    "presented": ["demonstrated", "showcased", "exhibited"],
    "processed": ["handled", "managed", "dealt with"],
    "produced": ["created", "generated", "delivered"],
    "programmed": ["coded", "developed", "scripted"],
    "provided": ["delivered", "supplied", "offered"],
    "published": ["released", "issued", "distributed"],
    "reduced": ["decreased", "minimized", "cut"],
    "researched": ["investigated", "studied", "explored"],
    "resolved": ["fixed", "addressed", "rectified"],
    "restructured": ["reorganized", "revamped", "transformed"],
    "reviewed": ["assessed", "evaluated", "examined"],
    "secured": ["obtained", "acquired", "protected"],
    "simplified": ["streamlined", "clarified", "condensed"],
    "spearheaded": ["led", "championed", "drove"],
    "standardized": ["normalized", "unified", "formalized"],
    "streamlined": ["simplified", "optimized", "improved"],
    "strengthened": ["reinforced", "enhanced", "fortified"],
    "supervised": ["oversaw", "directed", "managed"],
    "supported": ["assisted", "aided", "facilitated"],
    "trained": ["coached", "mentored", "instructed"],
    "transformed": ["converted", "revamped", "modernized"],
    "updated": ["revised", "upgraded", "modernized"],
    "upgraded": ["enhanced", "improved", "modernized"],
    "utilized": ["leveraged", "employed", "applied"],
    "validated": ["verified", "confirmed", "authenticated"],
    "worked": ["collaborated", "contributed", "operated"],
    "wrote": ["authored", "composed", "drafted"],
    "made": ["produced", "created", "constructed"],
    "used": ["utilized", "leveraged", "applied"],
    "responsible": ["accountable", "tasked with", "oversaw"],
    # ── Present-participle forms (appear in bullet continuations) ──
    "ensuring": ["guaranteeing", "maintaining", "securing"],
    "handling": ["managing", "processing", "dealing with"],
    "processing": ["handling", "analyzing", "computing"],
    "implementing": ["deploying", "executing", "applying"],
    "enhancing": ["improving", "boosting", "strengthening"],
    "increasing": ["boosting", "raising", "expanding"],
    "reducing": ["minimizing", "decreasing", "cutting"],
    "improving": ["enhancing", "refining", "advancing"],
    "supporting": ["facilitating", "enabling", "assisting"],
    "using": ["utilizing", "leveraging", "employing"],
    "achieving": ["attaining", "accomplishing", "reaching"],
    "managing": ["directing", "overseeing", "coordinating"],
    "developing": ["building", "creating", "engineering"],
    "building": ["constructing", "developing", "creating"],
    "designing": ["planning", "creating", "architecting"],
    "integrating": ["combining", "merging", "incorporating"],
    "deploying": ["launching", "releasing", "rolling out"],
    "optimizing": ["improving", "enhancing", "streamlining"],
    "leading": ["directing", "guiding", "spearheading"],
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
