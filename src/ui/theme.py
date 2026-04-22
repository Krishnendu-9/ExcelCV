"""
Theme and base style injection utilities.
"""

from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.css_generators import (
    generate_button_hover_css,
    generate_css_variables,
    generate_dropzone_css,
    generate_label_css,
    generate_textarea_css,
    generate_theme_base_css,
    generate_theme_button_css,
)
from src.ui_constants import (
    DARK_BG_PRIMARY,
    DARK_TEXT_PRIMARY,
    LIGHT_BG_PRIMARY,
    LIGHT_TEXT_PRIMARY,
)

@lru_cache(maxsize=32)
def _read_ui_markup_template(path: str, mtime_ns: int) -> str:
    """Read template file text with cache key tied to file path + mtime."""
    _ = mtime_ns
    return Path(path).read_text(encoding="utf-8")


def _load_ui_markup_template(name: str) -> str:
    """Load UI markup template and auto-refresh cache when file changes on disk."""
    base_dir = Path(__file__).resolve().parents[1] / "assets" / "ui"
    template_path = base_dir / name
    return _read_ui_markup_template(
        str(template_path),
        template_path.stat().st_mtime_ns,
    )




def _render_ui_markup_template(name: str, replacements: dict[str, str]) -> str:
    """Render a markup template with placeholders and normalize escaped braces."""
    rendered = _load_ui_markup_template(name)
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered.replace("{{", "{").replace("}}", "}")


def inject_back_button_sync() -> None:
    """Inject script so browser back/forward reload the page and sync with query_params."""
    components.html(
        """
<script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            if (target.__excelcvBackSyncHandler) {
                target.removeEventListener('popstate', target.__excelcvBackSyncHandler);
            }
            target.__excelcvBackSyncHandler = function() {
                target.location.reload();
            };
            target.addEventListener('popstate', target.__excelcvBackSyncHandler);
        })();
</script>
        """,
        height=0,
    )



def inject_base_css(theme: str = "light") -> None:
    """
    Inject custom CSS for the refreshed dual-page experience with manual theme support.
    
    Args:
        theme: Theme mode ("light" or "dark")
    """
    is_light = theme == "light"
    # Use constants for theme colors
    bg_color = LIGHT_BG_PRIMARY if is_light else DARK_BG_PRIMARY
    text_color = LIGHT_TEXT_PRIMARY if is_light else DARK_TEXT_PRIMARY
    
    # Generate CSS using helper functions
    theme_base_css = generate_theme_base_css(is_light, bg_color, text_color)
    css_variables = generate_css_variables(is_light, bg_color, text_color)
    textarea_css = generate_textarea_css()
    dropzone_css = generate_dropzone_css(is_light)
    label_css = generate_label_css()
    theme_button_css = generate_theme_button_css()
    button_hover_css = generate_button_hover_css()
    label_text_color = "#1f2937" if is_light else "#f9fafb"
    
    replacements = {
        "theme_base_css": theme_base_css,
        "css_variables": css_variables,
        "textarea_css": textarea_css,
        "dropzone_css": dropzone_css,
        "label_css": label_css,
        "theme_button_css": theme_button_css,
        "button_hover_css": button_hover_css,
        "label_text_color": label_text_color,
        "bg_color": bg_color,
    }
    css_markup = _render_ui_markup_template("base_theme.css.tpl", replacements)
    js_markup = _render_ui_markup_template("base_theme.js.tpl", replacements)
    html = (
        "<style>\n"
        f"{css_markup}"
        "</style>\n"
        "<!-- Sidebar interactions handled by components.html in render_report_page -->\n"
        "<script>\n"
        f"{js_markup}"
        "</script>"
    )
    st.markdown(html, unsafe_allow_html=True)


