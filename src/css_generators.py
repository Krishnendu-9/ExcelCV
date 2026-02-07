"""
CSS Generation Helpers

This module contains functions to generate CSS sections for the UI components.
All CSS is generated programmatically to maintain consistency and ease of maintenance.
"""

from typing import Dict
from src.ui_constants import (
    get_theme_colors,
    WARM_HOVER_GLOW,
    WARM_HOVER_BORDER,
    ACCENT_GREEN,
    ACCENT_PURPLE,
    get_js_colors,
    THEME_BUTTON_SELECTORS,
)


def generate_theme_base_css(is_light: bool, bg_color: str, text_color: str) -> str:
    """Generate base theme CSS for body, html, and containers."""
    return f"""
            /* FORCE THEME - APPLY TO EVERYTHING IMMEDIATELY */
            html,
            body,
            body > div,
            .stApp,
            .stApp > div,
            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > div,
            [data-testid="stAppViewContainer"] > div > div {{
                background-color: {bg_color} !important;
                background: {bg_color} !important;
                color: {text_color} !important;
            }}
            
            .main,
            .block-container {{
                background-color: transparent !important;
                background: transparent !important;
            }}
            
            body.theme-light,
            body.theme-light .stApp,
            .stApp.theme-light,
            body.theme-light [data-testid="stAppViewContainer"],
            body.theme-light [data-testid="stAppViewContainer"] > div,
            body.theme-light .stApp > div {{
                background-color: #ffffff !important;
                background: #ffffff !important;
                color: #111827 !important;
            }}
            
            body.theme-dark,
            body.theme-dark .stApp,
            .stApp.theme-dark,
            body.theme-dark [data-testid="stAppViewContainer"],
            body.theme-dark [data-testid="stAppViewContainer"] > div,
            body.theme-dark .stApp > div {{
                background-color: #0b0f17 !important;
                background: #0b0f17 !important;
                color: #e5e7eb !important;
            }}
    """


def generate_css_variables(is_light: bool, bg_color: str, text_color: str) -> str:
    """Generate CSS custom properties (variables)."""
    colors = get_theme_colors(is_light)
    return f"""
            :root {{
                --bg-primary: {bg_color};
                --text-primary: {text_color};
                --bg-secondary: {colors['bg_secondary']};
                --bg-card: {colors['bg_card']};
                --bg-sidebar: {colors['bg_sidebar']};
                --bg-hero: {colors['bg_hero']};
                --text-secondary: {colors['text_secondary']};
                --text-muted: #9ca3af;
                --border-color: {colors['border']};
                --border-light: {colors['border_light']};
                --shadow: {colors['shadow']};
                --shadow-lg: {colors['shadow_lg']};
                --accent: {ACCENT_GREEN};
                --accent-2: {ACCENT_PURPLE};
                --warm-hover-bg: #faf6db;
                --warm-hover-border: {WARM_HOVER_BORDER};
                --warm-hover-glow: {WARM_HOVER_GLOW};
                --button-bg: {colors['button_bg']};
                --button-text: {colors['button_text']};
                --button-border: {colors['button_border']};
                --button-hover-bg: {colors['button_hover_bg']};
                --button-hover-border: {colors['button_hover_border']};
                --button-shadow: {colors['button_shadow']};
                --button-hover-shadow: {colors['button_hover_shadow']};
                --placeholder-color: {colors['placeholder']};
            }}
    """


def generate_textarea_css() -> str:
    """Generate CSS for textarea (Job description input)."""
    return f"""
            .stTextArea textarea {{
                background: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                color: var(--text-primary) !important;
                padding: 12px 16px !important;
                font-size: 0.95rem !important;
                transition: all 0.2s ease !important;
                box-shadow: none !important;
            }}
            .stTextArea textarea:hover {{
                box-shadow: {WARM_HOVER_GLOW} !important;
                border-color: {WARM_HOVER_BORDER} !important;
                background: var(--bg-card) !important;
                background-color: var(--bg-card) !important;
            }}
            .stTextArea textarea:focus {{
                border-color: {WARM_HOVER_BORDER} !important;
                box-shadow: {WARM_HOVER_GLOW} !important;
            }}
    """


def generate_dropzone_css(is_light: bool) -> str:
    """Generate CSS for file uploader dropzone."""
    light_mode_text_color = '.stFileUploader [data-testid="stFileUploaderDropzone"], .stFileUploader [data-testid="stFileUploaderDropzone"] * { color: #374151 !important; }' if is_light else ''
    
    return f"""
            .stFileUploader [data-testid="stFileUploaderDropzone"],
            .stFileUploader [data-testid="stFileUploaderDropzone"] *,
            .stFileUploader [data-testid="stFileUploaderDropzone"] p,
            .stFileUploader [data-testid="stFileUploaderDropzone"] span,
            .stFileUploader [data-testid="stFileUploaderDropzone"] small {{
                color: var(--text-primary) !important;
            }}
            .stFileUploader [data-testid="stFileUploaderDropzone"],
            [data-testid="stFileUploaderDropzone"] {{
                box-shadow: none !important;
            }}
            {light_mode_text_color}
            
            .stFileUploader [data-testid="stFileUploaderDropzone"] {{
                background: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 12px !important;
                color: var(--text-primary) !important;
                padding: 12px 16px !important;
                font-size: 0.95rem !important;
                transition: all 0.2s ease !important;
                box-shadow: none !important;
            }}
            .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {{
                box-shadow: {WARM_HOVER_GLOW} !important;
                border-color: {WARM_HOVER_BORDER} !important;
                background: var(--bg-card) !important;
                background-color: var(--bg-card) !important;
            }}
    """


def generate_label_css() -> str:
    """Generate CSS for form labels (Job description, Upload resume)."""
    return f"""
            .stTextArea label,
            .stTextArea > label,
            .stTextArea label p,
            .stTextArea label span,
            [data-testid="stTextArea"] label,
            [data-testid="stTextArea"] > label,
            .stForm .stTextArea label,
            .stForm .stTextArea > label,
            form .stTextArea label,
            form .stTextArea > label {{
                color: var(--text-primary) !important;
                font-weight: 700 !important;
                font-size: 1.35rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.6 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            body.theme-light .stTextArea label,
            body.theme-light .stTextArea > label,
            body.theme-light [data-testid="stTextArea"] label,
            body.theme-light .stForm .stTextArea label {{
                color: #1f2937 !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.25) !important;
                padding-bottom: 6px !important;
                margin-bottom: 4px !important;
            }}
            body.theme-dark .stTextArea label,
            body.theme-dark .stTextArea > label,
            body.theme-dark [data-testid="stTextArea"] label,
            body.theme-dark .stForm .stTextArea label {{
                color: #f9fafb !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.35) !important;
                padding-bottom: 6px !important;
                margin-bottom: 4px !important;
            }}
            
            .stFileUploader label,
            .stFileUploader > label,
            [data-testid="stFileUploader"] label,
            [data-testid="stFileUploader"] > label {{
                color: var(--text-primary) !important;
                font-weight: 700 !important;
                font-size: 1.35rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.6 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            body.theme-light [data-testid="stFileUploader"] label,
            body.theme-light .stFileUploader label {{
                color: #1f2937 !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.25) !important;
                padding-bottom: 6px !important;
                margin-bottom: 4px !important;
            }}
            body.theme-dark [data-testid="stFileUploader"] label,
            body.theme-dark .stFileUploader label {{
                color: #f9fafb !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.35) !important;
                padding-bottom: 6px !important;
                margin-bottom: 4px !important;
            }}
    """


def generate_theme_button_css() -> str:
    """Generate CSS for theme toggle button."""
    selectors = ", ".join(THEME_BUTTON_SELECTORS)
    return f"""
            .theme-toggle {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 6px 12px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 0.85rem;
                color: var(--text-primary);
                transition: all 0.2s ease;
            }}
            {selectors}:hover {{
                box-shadow: {WARM_HOVER_GLOW} !important;
                border-color: {WARM_HOVER_BORDER} !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                background-image: none !important;
            }}
            {selectors}:hover * {{
                background-color: transparent !important;
                background: transparent !important;
                background-image: none !important;
            }}
    """


def generate_button_hover_css() -> str:
    """Generate CSS for button hover effects (boundary-only glow)."""
    return f"""
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button[data-testid]:hover {{
                box-shadow: {WARM_HOVER_GLOW} !important;
                border-color: {WARM_HOVER_BORDER} !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                background-image: none !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover *,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover *,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button[data-testid]:hover * {{
                background-color: transparent !important;
                background: transparent !important;
            }}
            
            .report-main .stButton > button:hover,
            .report-main .stButton button:hover,
            .report-main button:hover,
            .report-sidebar .stButton > button:hover,
            .report-sidebar .stButton button:hover,
            .report-sidebar button:hover {{
                box-shadow: {WARM_HOVER_GLOW} !important;
                border-color: {WARM_HOVER_BORDER} !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
            }}
    """
