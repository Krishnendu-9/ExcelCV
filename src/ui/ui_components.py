"""
Backward-compatible facade for UI component functions.

All implementations are split into smaller modules under src/ui.
"""

from src.ui import (
    _build_sidebar_html,
    _build_sidebar_js,
    _markdown_inline_to_html,
    get_category_icon,
    get_score_color_class,
    inject_back_button_sync,
    inject_base_css,
    issue_count,
    render_report_page,
    render_upload_landing_sections,
    render_upload_preview_card,
)

__all__ = [
    "_markdown_inline_to_html",
    "inject_back_button_sync",
    "inject_base_css",
    "get_score_color_class",
    "get_category_icon",
    "issue_count",
    "render_upload_landing_sections",
    "render_upload_preview_card",
    "_build_sidebar_html",
    "_build_sidebar_js",
    "render_report_page",
]
