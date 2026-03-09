"""UI package exports."""

from src.ui.common import (
    _markdown_inline_to_html,
    get_category_icon,
    get_score_color_class,
    issue_count,
)
from src.ui.report import _build_sidebar_html, _build_sidebar_js, render_report_page
from src.ui.theme import inject_back_button_sync, inject_base_css
from src.ui.upload import render_upload_landing_sections, render_upload_preview_card

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
