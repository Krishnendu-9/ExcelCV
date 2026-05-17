"""
Theme and base style injection utilities.
"""

import json
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.ui.css_generators import (
    generate_button_hover_css,
    generate_css_variables,
    generate_dropzone_css,
    generate_label_css,
    generate_textarea_css,
    generate_theme_base_css,
    generate_theme_button_css,
)
from src.ui.ui_constants import (
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
    """Cleanup legacy global listeners/observers that caused forced reloads on Back/Forward.

    Note: the previous ``target.themeInterval`` cleanup was removed. It was a
    vestigial reference to a poller that no longer exists. Theme-class
    application is now owned by the permanent watcher installed by
    ``_inject_theme_persistence`` in ``app.py``.
    """
    components.html(
        """
<script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            try {
                if (target.__excelcvBackSyncHandler) {
                    target.removeEventListener('popstate', target.__excelcvBackSyncHandler);
                    target.__excelcvBackSyncHandler = null;
                }
            } catch (e) {}

            try {
                if (target.__excelcvFixedHeaderObserver) {
                    target.__excelcvFixedHeaderObserver.disconnect();
                    target.__excelcvFixedHeaderObserver = null;
                }
            } catch (e) {}

            try {
                if (target.__excelcvLogoHomeObserver) {
                    target.__excelcvLogoHomeObserver.disconnect();
                    target.__excelcvLogoHomeObserver = null;
                }
            } catch (e) {}
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

    Note: the ``body.theme-light`` / ``body.theme-dark`` class on the shell
    elements (body / html / .stApp / viewContainer) is applied by
    ``_inject_theme_persistence`` in ``app.py``, which runs on every render
    unguarded. Doing it here too would silently miss class re-application on
    same-theme rerenders (e.g. clicking a nav link), because the textContent
    guard below correctly skips re-injecting an unchanged style block — but
    inline scripts injected via that guard would also fail to re-execute,
    which is what caused the cross-navigation theme flip bug.
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

    # Inject CSS via JS into the parent document's <head>.
    # json.dumps safely escapes the CSS string for use as a JS string literal,
    # avoiding any issues with Streamlit's markdown renderer treating <style>
    # blocks as visible text.
    css_json = json.dumps(css_markup)
    components.html(
        f"""<script>
(function() {{
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;

    var styleId = 'excelcv-base-theme';
    var existing = doc.getElementById(styleId);
    if (existing) {{
        if (existing.textContent !== {css_json}) {{
            existing.textContent = {css_json};
        }}
    }} else {{
        var style = doc.createElement('style');
        style.id = styleId;
        style.textContent = {css_json};
        (doc.head || doc.documentElement).appendChild(style);
    }}
}})();
</script>""",
        height=0,
    )


