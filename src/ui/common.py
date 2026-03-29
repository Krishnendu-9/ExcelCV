"""
Common UI helper functions shared across upload/report rendering.
"""

import re
from typing import Any, Dict


def _markdown_inline_to_html(text: str) -> str:
    """Convert inline Markdown (**bold**, *italic*) to HTML so it renders correctly in unsafe_allow_html blocks."""
    if not text:
        return text
    # Escape HTML to avoid breaking tags or XSS
    s = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **bold** -> <strong>bold</strong> (do before single *)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    # *italic* -> <em>italic</em>
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def get_score_color_class(score) -> str:
    """Get CSS class for score color."""
    try:
        score = int(score)
    except (TypeError, ValueError):
        return "score-low"
    if score >= 80:
        return "score-good"
    if score >= 60:
        return "score-medium"
    return "score-low"


def get_category_icon(score: int) -> str:
    """Get icon for category based on score."""
    if score >= 80:
        return "&#10003;"
    if score >= 60:
        return "&#9888;"
    return "&#10005;"


def issue_count(analysis: Dict[str, Any]) -> int:
    """Count total issues found in analysis."""
    count = 0
    count += len(analysis.get("missing_keywords", []))
    count += len(analysis.get("missing_skills", []))
    count += len([s for s in analysis.get("suggestions", []) if s.strip()])
    if analysis.get("match_score", 0) < 70:
        count += 1
    return max(count, 0)
