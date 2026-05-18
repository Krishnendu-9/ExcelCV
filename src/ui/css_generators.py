"""
CSS Generation Helpers

This module contains functions to generate CSS sections for the UI components.
All CSS is generated programmatically to maintain consistency and ease of maintenance.
"""

from src.ui.ui_constants import (
    ACCENT_GREEN,
    ACCENT_PURPLE,
    THEME_BUTTON_SELECTORS,
    WARM_HOVER_BORDER,
    WARM_HOVER_GLOW,
    get_theme_colors,
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
                --landing-panel-bg: {"linear-gradient(140deg, #f8fafc, #eef2ff)" if is_light else "linear-gradient(140deg, #0f172a, #111827)"};
                --landing-panel-border: {"rgba(148, 163, 184, 0.34)" if is_light else "rgba(148, 163, 184, 0.24)"};
                --landing-panel-shadow: {"0 14px 34px rgba(15, 23, 42, 0.08)" if is_light else "0 16px 44px rgba(2, 6, 23, 0.36)"};
                --landing-spectrum-bg: {"linear-gradient(135deg, #eef2ff, #e0e7ff)" if is_light else "linear-gradient(130deg, rgba(15, 23, 42, 0.96), rgba(59, 38, 116, 0.72))"};
                --landing-walk-bg: {"linear-gradient(135deg, #f8fafc, #e2e8f0)" if is_light else "linear-gradient(145deg, #0f172a, #172554)"};
                --landing-proof-bg: {"linear-gradient(135deg, #f8fafc, #f1f5f9)" if is_light else "linear-gradient(130deg, rgba(17, 24, 39, 0.95), rgba(30, 41, 59, 0.86))"};
                --landing-faq-bg: {"linear-gradient(140deg, #f8fafc, #e2e8f0)" if is_light else "linear-gradient(150deg, #0f172a, #1e293b)"};
                --landing-card-bg: {"linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95))" if is_light else "linear-gradient(160deg, rgba(15, 23, 42, 0.62), rgba(30, 41, 59, 0.44))"};
                --landing-card-border: {"rgba(148, 163, 184, 0.34)" if is_light else "rgba(148, 163, 184, 0.24)"};
                --landing-heading-text: {"#0f172a" if is_light else "#e2e8f0"};
                --landing-body-text: {"#334155" if is_light else "rgba(226, 232, 240, 0.82)"};
                --landing-muted-text: {"#475569" if is_light else "#94a3b8"};
                --landing-story-visual-bg: {"linear-gradient(150deg, #e2e8f0, #f1f5f9)" if is_light else "linear-gradient(150deg, rgba(15, 23, 42, 0.72), rgba(30, 41, 59, 0.55))"};
                --landing-story-card-bg: {"rgba(255, 255, 255, 0.94)" if is_light else "rgba(15, 23, 42, 0.84)"};
                --landing-story-card-border: {"rgba(148, 163, 184, 0.34)" if is_light else "rgba(148, 163, 184, 0.30)"};
                --landing-chip-bg: {"rgba(255, 255, 255, 0.86)" if is_light else "rgba(15, 23, 42, 0.48)"};
                --landing-chip-border: {"rgba(148, 163, 184, 0.34)" if is_light else "rgba(148, 163, 184, 0.28)"};
                --landing-chip-text: {"#334155" if is_light else "#e2e8f0"};
                --preview-shell-bg: {"linear-gradient(155deg, rgba(241, 245, 249, 0.96), rgba(226, 232, 240, 0.92))" if is_light else "linear-gradient(155deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.88))"};
                --preview-shell-border: {"rgba(148, 163, 184, 0.36)" if is_light else "rgba(148, 163, 184, 0.22)"};
                --preview-card-bg: {"linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.95))" if is_light else "linear-gradient(160deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.76))"};
                --preview-card-border: {"rgba(148, 163, 184, 0.36)" if is_light else "rgba(148, 163, 184, 0.30)"};
                --preview-text: {"#0f172a" if is_light else "#e2e8f0"};
                --preview-muted: {"#475569" if is_light else "#94a3b8"};
                --report-pill-bg: {"rgba(203, 213, 225, 0.84)" if is_light else "rgba(17, 24, 39, 0.45)"};
                --report-pill-border: {"rgba(100, 116, 139, 0.40)" if is_light else "rgba(148, 163, 184, 0.28)"};
                --report-pill-text: {"#1f2937" if is_light else "#cbd5e1"};
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
    return """
            .stTextArea label,
            .stTextArea > label,
            .stTextArea label p,
            .stTextArea label span,
            [data-testid="stTextArea"] label,
            [data-testid="stTextArea"] > label,
            .stForm .stTextArea label,
            .stForm .stTextArea > label,
            form .stTextArea label,
            form .stTextArea > label,
            .stFileUploader label,
            .stFileUploader > label,
            [data-testid="stFileUploader"] label,
            [data-testid="stFileUploader"] > label {
                color: var(--text-primary) !important;
                font-weight: 700 !important;
                font-size: 1.35rem !important;
                margin-top: 0 !important;
                margin-bottom: 8px !important;
                padding-bottom: 0 !important;
                border-bottom: none !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.3 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }
            body.theme-light .stTextArea label,
            body.theme-light [data-testid="stTextArea"] label,
            body.theme-light .stForm .stTextArea label,
            body.theme-light .stFileUploader label,
            body.theme-light [data-testid="stFileUploader"] label {
                color: #1f2937 !important;
            }
            body.theme-dark .stTextArea label,
            body.theme-dark [data-testid="stTextArea"] label,
            body.theme-dark .stForm .stTextArea label,
            body.theme-dark .stFileUploader label,
            body.theme-dark [data-testid="stFileUploader"] label {
                color: #f9fafb !important;
            }
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
            {selectors}:hover,
            {selectors}:focus,
            {selectors}:active {{
                box-shadow: none !important;
                border-color: var(--button-border) !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                background-image: none !important;
            }}
            {selectors}:hover *,
            {selectors}:focus *,
            {selectors}:active * {{
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
