"""
Theme and base style injection utilities.
"""

import streamlit as st
import streamlit.components.v1 as components

from src.ui_constants import (
    LIGHT_BG_PRIMARY,
    LIGHT_TEXT_PRIMARY,
    DARK_BG_PRIMARY,
    DARK_TEXT_PRIMARY,
    get_theme_colors,
)
from src.css_generators import (
    generate_theme_base_css,
    generate_css_variables,
    generate_textarea_css,
    generate_dropzone_css,
    generate_label_css,
    generate_theme_button_css,
    generate_button_hover_css,
)

def inject_back_button_sync() -> None:
    """Inject script so browser back/forward reload the page and sync with query_params."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            target.addEventListener('popstate', function() {
                target.location.reload();
            });
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
    
    st.markdown(
        f"""
        <style>
            {theme_base_css}
            
            {css_variables}
            
            /* Placeholder visibility: explicit color so visible in light theme (no body class needed) */
            .stTextArea textarea::placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            .stTextArea textarea::-webkit-input-placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            .stTextArea textarea::-moz-placeholder {{
                color: var(--placeholder-color) !important;
                opacity: 1 !important;
            }}
            
            /* Textarea and Dropzone Styling */
            {textarea_css}
            {dropzone_css}
            
            /* Label Styling */
            {label_css}
            
            /* Theme Button Styling */
            {theme_button_css}
            
            /* Button Hover Effects */
            {button_hover_css}
            
            /* BUTTONS: variable-based so visible in light/dark without body class */
            .stButton > button,
            .stButton button,
            .stButton > button *,
            .stButton button *,
            form button[type="submit"],
            form button,
            form button *,
            .stForm button[type="submit"],
            .stForm button,
            .stForm button *,
            .stForm .stButton button,
            .stForm .stButton button *,
            button[data-testid="baseButton-primary"],
            button[data-testid="baseButton-primary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            .stButton > button,
            .stButton button,
            form button[type="submit"],
            form button,
            .stForm button[type="submit"],
            .stForm button,
            button[data-testid="baseButton-primary"] {{
                border: 1px solid var(--button-border) !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 0.75rem 1.5rem !important;
                min-height: 44px !important;
                box-shadow: var(--button-shadow) !important;
            }}
            .stButton > button:hover,
            .stButton button:hover,
            form button[type="submit"]:hover,
            form button:hover,
            .stForm button[type="submit"]:hover,
            .stForm button:hover,
            .stButton > button:hover *,
            .stButton button:hover *,
            form button:hover *,
            .stForm button:hover *,
            button[data-testid="baseButton-primary"]:hover,
            button[data-testid="baseButton-primary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            .stButton > button:hover,
            .stButton button:hover,
            form button[type="submit"]:hover,
            form button:hover,
            .stForm button[type="submit"]:hover,
            .stForm button:hover,
            button[data-testid="baseButton-primary"]:hover {{
                box-shadow: var(--button-hover-shadow) !important;
            }}
            [data-testid="stAppViewContainer"] .stForm button,
            [data-testid="stAppViewContainer"] .stForm button *,
            [data-testid="stAppViewContainer"] .stForm .stButton button,
            [data-testid="stAppViewContainer"] .stForm .stButton button * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] .stForm button:hover,
            [data-testid="stAppViewContainer"] .stForm button:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            /* Catch-all: every button in the app (e.g. Download Reports) - download buttons may sit outside .report-main in DOM */
            [data-testid="stAppViewContainer"] .stButton button,
            [data-testid="stAppViewContainer"] .stButton button *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"],
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"] *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"],
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] .stButton button:hover,
            [data-testid="stAppViewContainer"] .stButton button:hover *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"]:hover,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-primary"]:hover *,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"]:hover,
            [data-testid="stAppViewContainer"] button[data-testid="baseButton-secondary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            /* Nuclear: any button in the app (Streamlit download buttons may use different markup) */
            [data-testid="stAppViewContainer"] button {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
            }}
            [data-testid="stAppViewContainer"] button:hover {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            [data-testid="stAppViewContainer"] button * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            [data-testid="stAppViewContainer"] button:hover * {{
                color: var(--button-text) !important;
            }}
            .stFileUploader button,
            .stFileUploader button *,
            .stFileUploader [data-baseweb="button"],
            .stFileUploader [data-baseweb="button"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-border) !important;
            }}
            .stFileUploader button,
            .stFileUploader [data-baseweb="button"] {{
                border: 1px solid var(--button-border) !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                font-weight: 600 !important;
                min-height: 36px !important;
                box-shadow: var(--button-shadow) !important;
            }}
            .stFileUploader button:hover,
            .stFileUploader [data-baseweb="button"]:hover,
            .stFileUploader button:hover *,
            .stFileUploader [data-baseweb="button"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            button[data-testid="baseButton-secondary"],
            button[data-testid="baseButton-secondary"] * {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
            }}
            button[data-testid="baseButton-secondary"]:hover,
            button[data-testid="baseButton-secondary"]:hover * {{
                background-color: var(--button-hover-bg) !important;
                background: var(--button-hover-bg) !important;
                color: var(--button-text) !important;
                border-color: var(--button-hover-border) !important;
            }}
            
            /* Hide Streamlit's deploy button */
            #MainMenu {{
                visibility: hidden;
            }}
            .stDeployButton {{
                display: none !important;
            }}
            /* Remove top blank: collapse header so it takes no space */
            header[data-testid="stHeader"] {{
                display: none !important;
                height: 0 !important;
                min-height: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                overflow: hidden !important;
                border: none !important;
            }}
            /* Nudge the first controls row flush to top */
            [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(.stSelectbox):first-child {{
                margin-top: 10px !important;
                padding-top: 0 !important;
            }}
            
            /* Hide Streamlit's default file size limit text */
            .stFileUploader > div > div > small {{
                display: none !important;
            }}
            
            /* Remove ALL top and bottom blank: zero padding/margin on every container */
            [data-testid="stAppViewContainer"] {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"] section {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"] > section > div {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            .main {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            .main .block-container {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
                max-width: 1240px;
                background: transparent !important;
            }}
            /* Collapse invisible markdown/script injection containers so top controls start at page top */
            [data-testid="stMainBlockContainer"] {{
                padding-top: 0 !important;
                margin-top: 0 !important;
            }}
            [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"] > style),
            [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"] > script),
            [data-testid="stMainBlockContainer"] .element-container:has(style),
            [data-testid="stMainBlockContainer"] .element-container:has(script) {{
                margin: 0 !important;
                padding: 0 !important;
                min-height: 0 !important;
                height: 0 !important;
                overflow: hidden !important;
            }}
            .block-container {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Remove bottom blank: no margin/padding on last block */
            .main .block-container > div:last-child {{
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Tighten gaps between rows */
            [data-testid="stVerticalBlock"] {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {{
                margin-bottom: 0 !important;
            }}
            .topbar {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 0 8px;
                margin-bottom: 6px;
            }}
            .brand-mark {{
                width: 38px;
                height: 38px;
                border-radius: 14px;
                background: linear-gradient(135deg, #10b981, #7c6bff);
                display: grid;
                place-items: center;
                font-weight: 900;
                color: #ffffff;
                font-size: 1.2rem;
            }}
            .brand-copy {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}
            .brand-title {{ 
                font-weight: 700; 
                font-size: 1.1rem; 
                color: var(--text-primary); 
            }}
            .brand-subtitle {{ 
                color: var(--text-secondary); 
                font-size: 0.85rem; 
            }}
            .site-brand {{
                display: flex;
                align-items: center;
                gap: 12px;
                min-height: 56px;
                padding-top: 4px;
            }}
            .site-logo-shell {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                border-radius: 12px;
                padding: 4px 6px;
                line-height: 1;
            }}
            body.theme-dark .site-logo-shell {{
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(244, 249, 255, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.7);
                box-shadow: 0 8px 18px rgba(0, 0, 0, 0.28);
            }}
            .site-logo-wordmark {{
                height: 50px;
                width: auto;
                max-width: 100%;
                display: block;
                object-fit: contain;
                object-position: left center;
            }}
            .site-logo-badge {{
                width: 52px;
                height: 52px;
                border-radius: 14px;
                background: linear-gradient(135deg, #10b981, #22d3ee);
                color: #ffffff;
                font-weight: 900;
                font-size: 1rem;
                display: grid;
                place-items: center;
                letter-spacing: 0.03em;
                box-shadow: 0 10px 24px rgba(16, 185, 129, 0.25);
            }}
            .site-brand-copy {{
                display: flex;
                align-items: center;
            }}
            .site-name {{
                color: var(--text-primary);
                font-size: 1.95rem;
                font-weight: 900;
                letter-spacing: 0.012em;
                margin: 0;
                line-height: 1;
            }}
            .site-nav {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                flex-wrap: nowrap;
                padding-top: 4px;
            }}
            .site-nav-item {{
                display: inline-flex;
                align-items: center;
                padding: 10px 16px;
                border-radius: 999px;
                border: 1px solid var(--border-color);
                background: var(--bg-card);
                color: var(--text-secondary);
                font-size: 1.04rem;
                font-weight: 700;
                line-height: 1;
            }}
            .theme-toggle-gap {{
                height: 4px;
            }}
            .st-key-theme_toggle_header {{
                margin-top: 0 !important;
            }}
            .site-header-rule {{
                height: 1px;
                margin: 6px 0 6px;
                background: var(--border-light);
            }}
            @media (max-width: 1200px) {{
                .site-name {{
                    font-size: 1.75rem;
                }}
                .site-logo-shell {{
                    padding: 3px 5px;
                }}
                .site-logo-wordmark {{
                    height: 44px;
                }}
                .site-logo-badge {{
                    width: 52px;
                    height: 52px;
                    font-size: 1rem;
                }}
            }}
            @media (max-width: 980px) {{
                .site-nav {{
                    justify-content: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }}
                .site-nav-item {{
                    font-size: 0.82rem;
                    padding: 7px 10px;
                }}
                .site-name {{
                    font-size: 1.35rem;
                }}
                .site-logo-shell {{
                    padding: 2px 4px;
                }}
                .site-logo-wordmark {{
                    height: 38px;
                }}
                .site-logo-badge {{
                    width: 42px;
                    height: 42px;
                    font-size: 0.9rem;
                }}
                .theme-toggle-gap {{
                    height: 2px;
                }}
            }}
            /* Fix selectbox cursor issue and theme */
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] > div,
            .stSelectbox > div > div > div input {{
                cursor: pointer !important;
                caret-color: transparent !important;
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
            }}
            div[data-baseweb="select"] input:focus {{
                cursor: pointer !important;
                caret-color: transparent !important;
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Fix selectbox container and all nested elements */
            .stSelectbox > div > div {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
            }}
            .stSelectbox > div > div > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            .stSelectbox > div > div > div > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Force all baseweb select elements */
            [data-baseweb="select"] {{
                background-color: var(--bg-card) !important;
            }}
            [data-baseweb="select"] > div {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            [data-baseweb="select"] input {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            
            /* Style selectbox (Mode dropdown) to match theme */
            .stSelectbox label {{
                color: var(--text-primary) !important;
                font-size: 0.9rem;
                font-weight: 700;
            }}

            /* Style checkbox label (Debug mode) to ensure visibility in both themes */
            .stCheckbox label,
            .stCheckbox label p,
            .stCheckbox label span,
            [data-testid="stCheckbox"] label,
            [data-testid="stCheckbox"] label p,
            [data-testid="stCheckbox"] label span,
            [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: var(--text-primary) !important;
                opacity: 1 !important;
                font-size: 0.95rem !important;
                font-weight: 600 !important;
            }}
            body.theme-light .stCheckbox label,
            body.theme-light [data-testid="stCheckbox"] label,
            body.theme-light [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: #1f2937 !important;
            }}
            body.theme-dark .stCheckbox label,
            body.theme-dark [data-testid="stCheckbox"] label,
            body.theme-dark [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {{
                color: #f9fafb !important;
            }}
            
            /* Fix selectbox dropdown background and text */
            div[data-baseweb="select"] > div {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="select"] input {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="popover"] {{
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
            }}
            div[data-baseweb="popover"] li {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
            }}
            div[data-baseweb="popover"] li:hover {{
                background-color: var(--bg-secondary) !important;
            }}
            
            /* (Button styles above use CSS variables; no body.theme-* override) */
            
            /* Style text area */
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
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
                background: var(--bg-card) !important;
                background-color: var(--bg-card) !important;
            }}
            .stTextArea textarea:focus {{
                border-color: #f5e6a8 !important;
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
            }}
            /* Target the label container that comes before textarea */
            .stTextArea > div:first-child,
            .stTextArea > div:first-child label,
            .stTextArea > div:first-child > label {{
                color: {'#1f2937' if is_light else '#f9fafb'} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
            }}
            /* Style text area label - Professional and prominent styling - Multiple selectors for maximum coverage */
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
                color: {'#1f2937' if is_light else '#f9fafb'} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stTextArea label,
            body.theme-light .stTextArea > label,
            body.theme-light [data-testid="stTextArea"] label,
            body.theme-light .stForm .stTextArea label {{
                color: #1f2937 !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stTextArea label,
            body.theme-dark .stTextArea > label,
            body.theme-dark [data-testid="stTextArea"] label,
            body.theme-dark .stForm .stTextArea label {{
                color: #f9fafb !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Target label text content directly */
            .stTextArea label p,
            .stTextArea label span,
            .stTextArea label * {{
                color: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
            }}
            
            /* Style file uploader (Upload PDF/browse file) - LIGHT MODE */
            body.theme-light .stFileUploader {{
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                border-radius: 12px;
                padding: 0;
                background: #f9fafb !important;
                transition: all 0.2s ease;
            }}
            /* Removed .stFileUploader:hover - only dropzone should glow, not the container */
            /* Style file uploader label - Professional styling matching Job description - Multiple selectors */
            .stFileUploader label,
            .stFileUploader > label,
            .stFileUploader label p,
            .stFileUploader label span,
            [data-testid="stFileUploader"] label,
            [data-testid="stFileUploader"] > label,
            .stForm .stFileUploader label,
            .stForm .stFileUploader > label,
            form .stFileUploader label,
            form .stFileUploader > label {{
                color: {'#1f2937' if is_light else '#f9fafb'} !important;
                font-weight: 700 !important;
                font-size: 1.28rem !important;
                margin-bottom: 0 !important;
                margin-top: 0 !important;
                display: block !important;
                letter-spacing: 0.01em !important;
                line-height: 1.2 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stFileUploader label,
            body.theme-light .stFileUploader > label,
            body.theme-light [data-testid="stFileUploader"] label,
            body.theme-light .stForm .stFileUploader label {{
                color: #1f2937 !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            
            /* Style file uploader - DARK MODE */
            body.theme-dark .stFileUploader {{
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                background: #111827 !important;
            }}
            /* Removed .stFileUploader:hover - only dropzone should glow, not the container */
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stFileUploader label,
            body.theme-dark .stFileUploader > label,
            body.theme-dark [data-testid="stFileUploader"] label,
            body.theme-dark .stForm .stFileUploader label {{
                color: #f9fafb !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }}
            /* Target file uploader label text content directly */
            .stFileUploader label p,
            .stFileUploader label span,
            .stFileUploader label * {{
                color: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
            }}
            
            /* Fix file uploader inner elements and buttons */
            .stFileUploader > div {{
                background-color: transparent !important;
            }}
            
            /* Uploaded file display - theme-aware (light: white card, dark: dark card) */
            .stFileUploader .uploadedFile,
            .stFileUploader [data-testid="stFileUploaderFile"],
            .stFileUploader [data-testid="stFileUploaderFile"] > div,
            .stFileUploader [data-testid="stFileUploaderFile"] span,
            .stFileUploader [data-testid="stFileUploaderFile"] p,
            .stFileUploader [data-testid="stFileUploaderFile"] div,
            .stFileUploader .uploadedFile span,
            .stFileUploader .uploadedFile div,
            .stFileUploader .uploadedFile p,
            .stFileUploader .uploadedFile *,
            .stFileUploader [data-testid="stFileUploaderFile"] * {{
                background-color: var(--bg-card) !important;
                color: var(--text-primary) !important;
                border-color: var(--border-color) !important;
            }}
            .stFileUploader .uploadedFile,
            .stFileUploader [data-testid="stFileUploaderFile"] {{
                border: 1px solid var(--border-color) !important;
                padding: 8px 12px !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                font-size: 0.9rem !important;
            }}
            .stFileUploader .uploadedFile:hover,
            .stFileUploader [data-testid="stFileUploaderFile"]:hover {{
                background-color: var(--bg-secondary) !important;
                border-color: var(--accent-2) !important;
            }}
            .stFileUploader .uploadedFile:hover *,
            .stFileUploader [data-testid="stFileUploaderFile"]:hover * {{
                background-color: transparent !important;
                color: var(--text-primary) !important;
            }}
            
            /* (Browse Files uses variable-based button rules above) */
            
            /* Style form elements */
            .stForm {{
                border: none;
                background: transparent;
            }}

            /* Upload page */
            .hero-shell {{
                background: linear-gradient(135deg, var(--bg-hero), var(--bg-secondary));
                border: 1px solid var(--border-light);
                border-radius: 24px;
                padding: 40px 40px 32px;
                box-shadow: 0 30px 90px var(--shadow-lg);
                margin-top: 16px;
            }}
            .hero-copy {{
                padding-right: 12px;
                margin-top: 0 !important;
            }}
            .eyebrow {{
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.75rem;
                color: var(--accent-2);
                margin-bottom: 12px;
                font-weight: 700;
            }}
            .hero-title {{
                font-size: 3.5rem;
                line-height: 1.05;
                margin: 0 0 6px;
                font-weight: 900;
                color: var(--text-primary);
            }}
            .hero-title span {{ 
                color: var(--accent); 
            }}
            .hero-subtitle {{
                color: var(--text-secondary);
                font-size: 1.1rem;
                margin-bottom: 6px;
                line-height: 1.6;
            }}
            .hero-chip-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 6px 0 0;
            }}
            .hero-chip {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                border-radius: 999px;
                padding: 6px 11px;
                background: linear-gradient(145deg, var(--bg-card), var(--bg-secondary));
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.01em;
                margin: 0;
            }}
            .privacy-note {{
                color: var(--text-secondary);
                font-size: 0.85rem;
                margin-top: 8px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .upload-preview {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-light);
                border-radius: 20px;
                padding: 16px;
                margin-top: 0;
                box-shadow: inset 0 1px 0 var(--border-light);
            }}
            /* Keep hero text and scorecard aligned higher on first fold. */
            [data-testid="stHorizontalBlock"]:has(.hero-copy) {{
                margin-top: 0 !important;
                align-items: flex-start !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div {{
                margin-top: 0 !important;
                padding-top: 0 !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.hero-copy) > div:last-child [data-testid="stVerticalBlock"] > div {{
                margin-top: 0 !important;
                margin-bottom: 6px !important;
            }}
            .landing-extended {{
                margin-top: 28px;
                padding: 28px;
                border-radius: 24px;
                border: 1px solid var(--border-light);
                background: linear-gradient(140deg, var(--bg-card), var(--bg-secondary));
                box-shadow: 0 18px 48px var(--shadow);
            }}
            .landing-band {{
                max-width: 860px;
                margin-bottom: 18px;
            }}
            .landing-kicker {{
                margin: 0 0 8px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-size: 0.78rem;
                font-weight: 700;
                color: var(--accent-2);
            }}
            .landing-title {{
                margin: 0;
                font-size: clamp(1.7rem, 3vw, 2.4rem);
                line-height: 1.15;
                color: var(--text-primary);
            }}
            .landing-subtitle {{
                margin: 10px 0 0;
                font-size: 1rem;
                line-height: 1.6;
                color: var(--text-secondary);
            }}
            .landing-feature-grid {{
                margin-top: 22px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 14px;
            }}
            .landing-feature-card {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 16px;
                transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            }}
            .landing-feature-card:hover {{
                transform: translateY(-2px);
                border-color: rgba(16, 185, 129, 0.45);
                box-shadow: 0 12px 24px var(--shadow);
            }}
            .landing-feature-card h3 {{
                margin: 0 0 8px;
                font-size: 1.02rem;
                color: var(--text-primary);
            }}
            .landing-feature-card p {{
                margin: 0;
                color: var(--text-secondary);
                line-height: 1.5;
                font-size: 0.94rem;
            }}
            .landing-mode-shell {{
                margin-top: 16px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
            }}
            .landing-mode-card {{
                background: linear-gradient(160deg, var(--bg-sidebar), var(--bg-card));
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 14px;
            }}
            .mode-eyebrow {{
                margin: 0;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--accent);
                font-weight: 700;
            }}
            .landing-mode-card h4 {{
                margin: 8px 0 6px;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .landing-mode-card p {{
                margin: 0;
                color: var(--text-secondary);
                line-height: 1.5;
                font-size: 0.9rem;
            }}
            .landing-flow {{
                margin-top: 18px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
            }}
            .landing-step {{
                background: var(--bg-card);
                border: 1px dashed var(--border-color);
                border-radius: 14px;
                padding: 14px;
            }}
            .step-num {{
                display: inline-block;
                margin-bottom: 6px;
                padding: 4px 8px;
                border-radius: 999px;
                background: rgba(16, 185, 129, 0.12);
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
            }}
            .landing-step h4 {{
                margin: 0 0 6px;
                color: var(--text-primary);
                font-size: 1rem;
            }}
            .landing-step p {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.92rem;
                line-height: 1.5;
            }}
            .landing-proof-grid {{
                margin-top: 18px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                gap: 14px;
            }}
            .proof-tile {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 12px;
            }}
            .proof-label {{
                margin: 0;
                color: var(--text-secondary);
                font-size: 0.8rem;
            }}
            .proof-value {{
                margin: 6px 0 0;
                color: var(--text-primary);
                font-size: 1rem;
                font-weight: 700;
            }}
            .landing-faq {{
                margin-top: 20px;
                padding-top: 2px;
            }}
            .landing-faq h3 {{
                margin: 0 0 6px;
                color: var(--text-primary);
                font-size: 1.2rem;
            }}
            .landing-faq-item {{
                border: 1px solid var(--border-color);
                border-radius: 12px;
                background: var(--bg-card);
                padding: 12px 14px;
                margin-top: 8px;
            }}
            .landing-faq-item h4 {{
                margin: 0;
                color: var(--text-primary);
                font-weight: 700;
            }}
            .landing-faq-item p {{
                margin: 10px 0 0;
                color: var(--text-secondary);
                line-height: 1.55;
                font-size: 0.92rem;
            }}
            .landing-feature-card,
            .landing-mode-card,
            .landing-step,
            .proof-tile,
            .landing-faq-item {{
                opacity: 0;
                transform: translateY(10px);
                animation: landing-fade-up 0.45s ease forwards;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(1),
            .landing-mode-shell .landing-mode-card:nth-child(1),
            .landing-flow .landing-step:nth-child(1),
            .landing-proof-grid .proof-tile:nth-child(1),
            .landing-faq .landing-faq-item:nth-child(2) {{
                animation-delay: 0.04s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(2),
            .landing-mode-shell .landing-mode-card:nth-child(2),
            .landing-flow .landing-step:nth-child(2),
            .landing-proof-grid .proof-tile:nth-child(2),
            .landing-faq .landing-faq-item:nth-child(3) {{
                animation-delay: 0.08s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(3),
            .landing-mode-shell .landing-mode-card:nth-child(3),
            .landing-flow .landing-step:nth-child(3),
            .landing-proof-grid .proof-tile:nth-child(3),
            .landing-faq .landing-faq-item:nth-child(4) {{
                animation-delay: 0.12s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(4),
            .landing-proof-grid .proof-tile:nth-child(4),
            .landing-faq .landing-faq-item:nth-child(5) {{
                animation-delay: 0.16s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(5) {{
                animation-delay: 0.2s;
            }}
            .landing-feature-grid .landing-feature-card:nth-child(6) {{
                animation-delay: 0.24s;
            }}
            @keyframes landing-fade-up {{
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            @media (max-width: 1100px) {{
                .hero-title {{
                    font-size: 2.8rem;
                }}
                .upload-preview {{
                    padding: 18px;
                    margin-top: 10px;
                }}
                .landing-extended {{
                    padding: 22px;
                }}
            }}
            @media (max-width: 768px) {{
                .hero-title {{
                    font-size: 2.15rem;
                    line-height: 1.12;
                }}
                .hero-subtitle {{
                    font-size: 1rem;
                }}
                .hero-chip {{
                    font-size: 0.76rem;
                    padding: 6px 9px;
                }}
                .upload-preview {{
                    margin-top: 0;
                }}
                .landing-title {{
                    font-size: 1.6rem;
                }}
                .landing-subtitle {{
                    font-size: 0.95rem;
                }}
                .landing-feature-grid,
                .landing-mode-shell,
                .landing-flow {{
                    grid-template-columns: 1fr;
                    gap: 14px;
                }}
            }}
            @media (prefers-reduced-motion: reduce) {{
                .landing-feature-card,
                .landing-mode-card,
                .landing-step,
                .proof-tile,
                .landing-faq-item {{
                    opacity: 1;
                    transform: none;
                    animation: none;
                }}
            }}
            .preview-card {{
                background: var(--bg-card) !important;
                border-radius: 18px;
                padding: 18px 18px 12px;
                color: var(--text-primary) !important;
                box-shadow: 0 20px 60px var(--shadow);
                border: 1px solid var(--border-light);
            }}
            
            /* Ensure preview card text is visible in both themes */
            .preview-card * {{
                color: var(--text-primary) !important;
            }}
            .preview-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .preview-badge {{
                background: rgba(16, 185, 129, 0.15);
                color: var(--accent);
                padding: 6px 12px;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.75rem;
                letter-spacing: 0.5px;
            }}
            .theme-dark .preview-badge {{
                background: rgba(16, 185, 129, 0.25);
                color: #34d399;
            }}
            .preview-score {{
                display: flex;
                align-items: baseline;
                gap: 6px;
                font-weight: 700;
            }}
            .preview-score .num {{ 
                color: var(--accent); 
                font-size: 1.8rem; 
            }}
            .preview-score .den {{ 
                color: var(--text-secondary); 
            }}
            .pill-row {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin: 4px 0 10px;
            }}
            .pill {{
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 6px 10px;
                border-radius: 14px;
                font-size: 0.98rem;
                font-weight: 700;
            }}
            .progress-shell {{
                margin: 12px 0 6px;
            }}
            .progress-track {{
                width: 100%;
                height: 10px;
                background: var(--bg-secondary);
                border-radius: 12px;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, var(--accent), #22d3ee);
                border-radius: 12px;
            }}
            .list-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid var(--border-color);
                background-color: transparent !important;
            }}
            .list-row:last-child {{ 
                border-bottom: none; 
            }}
            .list-row span {{ 
                font-size: 0.95rem; 
                color: var(--text-primary) !important; 
            }}
            
            /* Fix preview card list items to match theme */
            .preview-card .list-row {{
                background-color: transparent !important;
                color: var(--text-primary) !important;
            }}
            .preview-card .list-row span {{
                color: var(--text-primary) !important;
            }}
            
            /* Ensure icons in list rows are visible and properly colored */
            .list-row span:last-child {{
                font-weight: 700;
                font-size: 1.1rem;
            }}
            
            /* Make sure all text in preview card is visible */
            .preview-card,
            .preview-card * {{
                background-color: var(--bg-card) !important;
            }}
            .preview-card .text-primary,
            .preview-card .text-secondary,
            .preview-card .text-muted {{
                color: var(--text-primary) !important;
            }}

            /* Report page - center theme + Upload buttons with PDF section */
            #report-pdf-row-marker {{
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child {{
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                gap: 8px !important;
            }}
            .report-hero {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
                border: 1px solid var(--border-color);
                padding: 18px 20px;
                border-radius: 16px;
                margin: 10px 0 20px;
            }}
            .report-title {{ 
                margin: 0; 
                font-size: 2rem; 
                color: var(--text-primary); 
            }}
            .score-pill {{
                background: rgba(16,185,129,0.15);
                color: var(--accent);
                padding: 10px 14px;
                border-radius: 12px;
                font-weight: 700;
                min-width: 110px;
                text-align: center;
            }}
            .theme-dark .score-pill {{
                color: #a7f3d0;
            }}
            .report-shell {{
                display: grid;
                grid-template-columns: 360px 1fr;
                gap: 20px;
            }}
            /* Report layout: two columns */
            [data-testid="stHorizontalBlock"] {{
                align-items: flex-start !important;
            }}
            .report-sidebar {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 10px 34px var(--shadow);
                position: sticky !important;
                top: 92px !important;
                max-height: calc(100vh - 112px) !important;
                overflow-y: auto !important;
            }}
            .score-card {{
                background: linear-gradient(145deg, var(--bg-card), var(--bg-sidebar));
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 18px;
                margin-bottom: 18px;
                text-align: center;
            }}
            .score-number {{ 
                font-size: 2.8rem; 
                font-weight: 900; 
                color: #fcd34d; 
            }}
            .score-number span {{ 
                font-size: 1rem; 
                color: var(--text-secondary); 
            }}
            .issues-text {{ 
                color: var(--text-secondary); 
                font-size: 0.95rem; 
            }}
            .issues-text.clickable {{
                cursor: pointer;
                color: #f87171;
                text-decoration: underline;
                transition: color 0.2s ease;
            }}
            .issues-text.clickable:hover {{
                color: #ef4444;
            }}
            .category {{
                border-top: 1px solid var(--border-light);
                padding: 12px 0;
            }}
            .category:first-of-type {{ 
                border-top: none; 
            }}
            .category-head {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
                color: var(--text-primary);
                font-weight: 700;
                letter-spacing: 0.02em;
                cursor: pointer;
                user-select: none;
                transition: color 0.2s ease;
                padding: 4px 0;
            }}
            .category-head:hover {{
                color: var(--accent);
            }}
            .category-head .category-title {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 1;
            }}
            .category-chevron {{
                display: inline-block;
                transition: transform 0.3s ease;
                font-size: 0.85rem;
                color: var(--text-secondary);
                margin-left: 4px;
            }}
            .category-head.expanded .category-chevron {{
                transform: rotate(180deg);
            }}
            .category-items {{
                overflow: hidden;
                transition: max-height 0.3s ease, opacity 0.2s ease;
            }}
            .category-items.collapsed {{
                max-height: 0;
                opacity: 0;
                margin: 0;
                padding: 0;
            }}
            .category-items.expanded {{
                max-height: 1000px;
                opacity: 1;
            }}
            .category-score {{
                padding: 6px 10px;
                border-radius: 14px;
                font-weight: 700;
                font-size: 0.95rem;
            }}
            .score-good {{ 
                background: rgba(16,185,129,0.12); 
                color: #34d399; 
            }}
            .score-medium {{ 
                background: rgba(234,179,8,0.15); 
                color: #fbbf24; 
            }}
            .score-low {{ 
                background: rgba(239,68,68,0.16); 
                color: #f87171; 
            }}
            .subitem {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                color: var(--text-secondary);
                padding: 8px 0;
                font-size: 0.92rem;
            }}
            .subitem .subitem-label-wrap {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 1;
                min-width: 0;
            }}
            .subitem .subitem-icon {{
                flex-shrink: 0;
                width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                font-size: 12px;
                font-weight: 700;
            }}
            .subitem .subitem-icon.icon-ok {{
                background: rgba(16,185,129,0.2);
                color: #34d399;
            }}
            .subitem .subitem-icon.icon-warn {{
                background: rgba(239,68,68,0.2);
                color: #f87171;
            }}
            .subitem.clickable {{
                cursor: pointer;
                transition: all 0.2s ease;
                border-radius: 6px;
                padding: 8px 10px;
                margin: 0 -10px;
            }}
            .subitem.clickable:hover {{
                background: var(--bg-secondary);
                color: var(--text-primary);
            }}
            .section-anchor {{
                scroll-margin-top: 100px;
            }}
            .badge {{
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
            }}
            .badge-ok {{ 
                background: rgba(16,185,129,0.18); 
                color: #34d399; 
            }}
            .badge-warn {{ 
                background: rgba(239,68,68,0.18); 
                color: #f87171; 
            }}
            .badge-lock {{ 
                background: rgba(148,163,184,0.15); 
                color: var(--text-secondary); 
            }}
            .theme-light .badge-lock {{
                color: #6b7280;
            }}

            .report-main {{
                display: flex;
                flex-direction: column;
                gap: 28px;
            }}
            .detail-card {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-light);
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 12px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            }}
            .report-group-wrap {{
                margin: 0;
            }}
            .report-group-wrap:last-of-type {{
                margin-bottom: 0;
            }}
            .report-group {{
                background: linear-gradient(140deg, var(--bg-card), var(--bg-sidebar));
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 12px 34px var(--shadow);
                margin: 0;
            }}
            .report-group-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 14px;
                padding: 4px 4px 2px;
            }}
            .report-group-head h3 {{
                margin: 0;
                font-size: 1.55rem;
                color: var(--text-primary);
                letter-spacing: 0.02em;
            }}
            .report-group-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 7px 14px;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 700;
                color: var(--text-secondary);
                background: rgba(17, 24, 39, 0.45);
                border: 1px solid var(--border-color);
                white-space: nowrap;
            }}
            .theme-light .report-group-pill {{
                background: rgba(255, 255, 255, 0.72);
                color: #4b5563;
            }}
            .report-group-body {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .detail-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .detail-head h3 {{ 
                margin: 0; 
            }}
            /* Shared body area for all report sections (Quantifying Impact, Spelling & Grammar, Strengths, etc.) - same as Suggestions */
            .section-body {{
                padding: 0 0 4px 0;
                margin: 0;
            }}
            .section-body-item {{
                margin-bottom: 6px;
                line-height: 1.45;
                color: var(--text-primary);
            }}
            .section-body-item:last-child {{
                margin-bottom: 0;
            }}
            .progress-track.dark {{
                background: var(--bg-secondary);
            }}
            .progress-fill.dark {{
                background: linear-gradient(90deg, var(--accent), #0ea5e9);
            }}
            /* Issue detail cards - for showing specific problems */
            .issue-card {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-light);
                border-radius: 12px;
                padding: 20px;
                margin-top: 14px;
                text-align: center;
            }}
            .issue-card .issue-icon {{
                font-size: 2rem;
                margin-bottom: 6px;
            }}
            .issue-card .issue-count {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #ef4444;
                color: #fff;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                font-size: 0.85rem;
                font-weight: 700;
                position: relative;
                top: -15px;
                left: -8px;
            }}
            .issue-card .issue-heading {{
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 6px;
            }}
            .issue-card .issue-desc {{
                color: var(--text-secondary);
                font-size: 0.95rem;
                margin-bottom: 12px;
            }}
            .issue-item {{
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 14px;
                padding: 12px 16px;
                margin-top: 8px;
                text-align: left;
                display: flex;
                align-items: flex-start;
                gap: 14px;
                color: var(--text-primary);
                font-size: 0.92rem;
                line-height: 1.5;
            }}
            .issue-item .issue-x {{
                color: #ef4444;
                font-weight: 700;
                font-size: 1rem;
                flex-shrink: 0;
                margin-top: 1px;
            }}
            .issue-item-ok {{
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            .issue-item-ok .issue-x {{
                color: #10b981;
            }}
            /* Contact Information rows */
            .contact-row {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 14px 18px;
                margin-top: 10px;
                border-radius: 14px;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
            }}
            .contact-icon {{
                font-size: 1.1rem;
                font-weight: 700;
                flex-shrink: 0;
                margin-top: 1px;
            }}
            .contact-icon.found {{
                color: #10b981;
            }}
            .contact-icon.missing {{
                color: #ef4444;
            }}
            .contact-label {{
                font-weight: 700;
                color: var(--text-primary);
                white-space: nowrap;
            }}
            .contact-sep {{
                color: var(--text-secondary);
                flex-shrink: 0;
            }}
            .contact-value {{
                color: var(--text-primary);
                word-break: break-all;
            }}
            .contact-msg {{
                color: var(--text-secondary);
                font-size: 0.9rem;
                word-break: normal;
            }}
            /* Repeated word tags */
            .repeat-group {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 14px;
                margin-top: 10px;
                margin-bottom: 6px;
                text-align: left;
            }}
            .repeat-word-tag {{
                display: inline-block;
                padding: 6px 14px;
                border-radius: 8px;
                background: #dc2626;
                color: #fff;
                font-weight: 700;
                font-size: 0.9rem;
            }}
            .repeat-suggestion {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 8px;
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 0.88rem;
            }}
            .repeat-label {{
                color: var(--text-secondary);
                font-size: 0.88rem;
                white-space: nowrap;
            }}
            /* Spelling issue tags */
            .spell-issue-row {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 8px;
                margin-top: 8px;
                text-align: left;
            }}
            .spell-tag {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 8px;
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: var(--text-primary);
                font-size: 0.88rem;
            }}
            .spell-tag-label {{
                font-weight: 700;
                color: #ef4444;
                margin-right: 4px;
            }}
            /* Good status card */
            .good-card {{
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.25);
            }}
            .good-card .issue-heading {{
                color: #10b981;
            }}
            .list-tag {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 14px;
                background: var(--bg-secondary);
                color: var(--text-primary);
                margin-right: 8px;
                margin-bottom: 6px;
                font-size: 0.9rem;
            }}
            .text-primary {{ 
                color: var(--text-primary); 
            }}
            .text-secondary {{ 
                color: var(--text-secondary); 
            }}
            .text-muted {{ 
                color: var(--text-secondary); 
            }}
            .text-description {{ 
                color: var(--text-secondary); 
            }}
            .download-row {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 12px;
                margin-top: 12px;
            }}
            
            /* Ensure download buttons are clickable */
            .report-sidebar button,
            .report-main button {{
                position: relative;
                z-index: 10;
                pointer-events: auto !important;
            }}
            
            /* Report area buttons (Download Reports, etc.) use theme colors - light in light mode */
            .report-main .stButton > button,
            .report-main .stButton button,
            .report-main button[data-testid="baseButton-primary"],
            .report-main button[data-testid="baseButton-secondary"],
            .report-sidebar .stButton > button,
            .report-sidebar .stButton button,
            .report-sidebar button[data-testid="baseButton-primary"],
            .report-sidebar button[data-testid="baseButton-secondary"],
            .report-main button,
            .report-sidebar button {{
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
                border: 1px solid var(--button-border) !important;
                box-shadow: var(--button-shadow) !important;
            }}
            /* Warm Sun hover for buttons in col_actions (Upload another resume, theme toggle) - Boundary-only glow, NO background */
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button[data-testid]:hover {{
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
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
            /* Ensure nested text elements remain visible */
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover div,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover span,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child button:hover p,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover div,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover span,
            [data-testid="stHorizontalBlock"]:has(.report-hero) > div:last-child .stButton > button:hover p {{
                background-color: transparent !important;
                background: transparent !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button *,
            .report-main .stButton button *,
            .report-main button *,
            .report-sidebar .stButton > button *,
            .report-sidebar .stButton button *,
            .report-sidebar button * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button:hover,
            .report-main .stButton button:hover,
            .report-main button:hover,
            .report-sidebar .stButton > button:hover,
            .report-sidebar .stButton button:hover,
            .report-sidebar button:hover {{
                box-shadow: 0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4) !important;
                border-color: #f5e6a8 !important;
                background-color: var(--button-bg) !important;
                background: var(--button-bg) !important;
                color: var(--button-text) !important;
            }}
            .report-main .stButton > button:hover *,
            .report-main .stButton button:hover *,
            .report-main button:hover *,
            .report-sidebar .stButton > button:hover *,
            .report-sidebar .stButton button:hover *,
            .report-sidebar button:hover * {{
                background-color: transparent !important;
                color: var(--button-text) !important;
            }}
            
            /* Ensure no overlay blocks buttons */
            .report-sidebar,
            .report-main,
            .report-group {{
                position: relative;
                z-index: 1;
            }}
        </style>
        <!-- Sidebar interactions handled by components.html in render_report_page -->
        <script>
            // SIMPLE THEME APPLICATION - WHITE FOR LIGHT, BLACK FOR DARK
            (function() {{
                // Clean up any existing intervals
                if (window.themeInterval) {{
                    clearInterval(window.themeInterval);
                }}
                
                const bgColor = '{bg_color}';
                const themeClass = bgColor === '#ffffff' ? 'theme-light' : 'theme-dark';
                
                function forceTheme() {{
                    try {{
                        // Apply theme class to body and html
                        if (document.body) {{
                            document.body.className = document.body.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            document.body.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        if (document.documentElement) {{
                            document.documentElement.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                        }}
                        
                        // Force .stApp and ALL its children - WHITE or BLACK
                        const stApp = document.querySelector('.stApp');
                        if (stApp) {{
                            stApp.className = stApp.className.replace(/theme-\\w+/g, '').trim() + ' ' + themeClass;
                            stApp.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                            
                            // Force ALL children recursively
                            const allChildren = stApp.querySelectorAll('*');
                            allChildren.forEach(child => {{
                                if (child && child.style && !child.classList.contains('hero-shell') && !child.classList.contains('preview-card')) {{
                                    // Only override container backgrounds, not content cards
                                    if (child === stApp.firstElementChild || child.parentElement === stApp) {{
                                        child.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                                    }}
                                }}
                            }});
                        }}
                        
                        // Force Streamlit view container and ALL children
                        const viewContainer = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (viewContainer) {{
                            viewContainer.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                            const allViewChildren = viewContainer.querySelectorAll('*');
                            allViewChildren.forEach(child => {{
                                if (child && child.style && child.parentElement === viewContainer) {{
                                    child.style.cssText += 'background-color: ' + bgColor + ' !important; background: ' + bgColor + ' !important;';
                                }}
                            }});
                        }}
                        
                        // Force main and block-container to be transparent
                        document.querySelectorAll('.main, .block-container').forEach(el => {{
                            if (el && el.style) {{
                                el.style.cssText += 'background-color: transparent !important;';
                            }}
                        }});
                        // Remove top and bottom blank: force zero padding/margin on all main containers
                        const view = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (view) {{
                            view.style.paddingTop = '0'; view.style.paddingBottom = '0';
                            view.style.marginTop = '0'; view.style.marginBottom = '0';
                            const section = view.querySelector('section');
                            if (section) {{
                                section.style.paddingTop = '0'; section.style.paddingBottom = '0';
                                section.style.marginTop = '0'; section.style.marginBottom = '0';
                                [].forEach.call(section.children, div => {{
                                    div.style.paddingTop = '0'; div.style.paddingBottom = '0';
                                }});
                            }}
                        }}
                        document.querySelectorAll('.main, .block-container').forEach(el => {{
                            if (el && el.style) {{
                                el.style.paddingTop = '0'; el.style.paddingBottom = '0';
                                el.style.marginTop = '0'; el.style.marginBottom = '0';
                            }}
                        }});
                        
                        // Fix selectbox (Mode dropdown) - force theme colors
                        document.querySelectorAll('div[data-baseweb="select"]').forEach(select => {{
                            if (select) {{
                                const selectDiv = select.querySelector('div');
                                if (selectDiv) {{
                                    selectDiv.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                                }}
                                const input = select.querySelector('input');
                                if (input) {{
                                    input.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important;';
                                }}
                            }}
                        }});
                        
                        // Fix text area labels - Professional styling with larger size
                        document.querySelectorAll('.stTextArea label, .stTextArea > label, [data-testid="stTextArea"] label').forEach(label => {{
                            if (label) {{
                                const labelColor = bgColor === '#ffffff' ? '#1f2937' : '#f9fafb';
                                const borderColor = bgColor === '#ffffff' ? 'rgba(124, 107, 255, 0.25)' : 'rgba(124, 107, 255, 0.35)';
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.28rem !important; margin-bottom: 0 !important; margin-top: 0 !important; display: block !important; letter-spacing: 0.01em !important; line-height: 1.2 !important; border-bottom: none !important; padding-bottom: 0 !important;';
                                // Also style any nested elements
                                const nestedElements = label.querySelectorAll('p, span, *');
                                nestedElements.forEach(el => {{
                                    if (el && el.tagName !== 'SVG' && el.tagName !== 'BUTTON') {{
                                        el.style.cssText += 'color: ' + labelColor + ' !important; font-size: inherit !important; font-weight: inherit !important;';
                                    }}
                                }});
                            }}
                        }});
                        
                        // Fix file uploader labels - Professional styling matching Job description
                        document.querySelectorAll('.stFileUploader label, .stFileUploader > label, [data-testid="stFileUploader"] label').forEach(label => {{
                            if (label) {{
                                const labelColor = bgColor === '#ffffff' ? '#1f2937' : '#f9fafb';
                                const borderColor = bgColor === '#ffffff' ? 'rgba(124, 107, 255, 0.25)' : 'rgba(124, 107, 255, 0.35)';
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.28rem !important; margin-bottom: 0 !important; margin-top: 0 !important; display: block !important; letter-spacing: 0.01em !important; line-height: 1.2 !important; border-bottom: none !important; padding-bottom: 0 !important;';
                                // Also style any nested elements
                                const nestedElements = label.querySelectorAll('p, span, *');
                                nestedElements.forEach(el => {{
                                    if (el && el.tagName !== 'SVG' && el.tagName !== 'BUTTON') {{
                                        el.style.cssText += 'color: ' + labelColor + ' !important; font-size: inherit !important; font-weight: inherit !important;';
                                    }}
                                }});
                            }}
                        }});
                        
                        // Fix file uploader - force theme colors
                        document.querySelectorAll('.stFileUploader').forEach(uploader => {{
                            if (uploader) {{
                                uploader.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#f9fafb' : '#111827') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important; padding: 0 !important;';
                                
                                // Fix Browse Files button inside uploader
                                const browseBtn = uploader.querySelector('button, [data-baseweb="button"]');
                                if (browseBtn) {{
                                    browseBtn.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                                }}
                            }}
                        }});
                        
                        // Fix Upload & Analyze button - SAME PATTERN AS THEME TOGGLE - FORCE VISIBLE IN LIGHT MODE
                        document.querySelectorAll('form button[type="submit"], .stForm button[type="submit"], .stButton > button, button[type="submit"], button[data-testid="baseButton-primary"]').forEach(btn => {{
                            if (btn && btn.getAttribute('key') !== 'theme_toggle') {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important; box-shadow: ' + (bgColor === '#ffffff' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none') + ' !important;';
                                
                                // Fix ALL nested elements (divs, spans, p tags)
                                const allNested = btn.querySelectorAll('div, span, p');
                                allNested.forEach(el => {{
                                    el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Fix Browse Files button - SAME PATTERN AS THEME TOGGLE - FORCE VISIBLE IN LIGHT MODE
                        document.querySelectorAll('.stFileUploader button, .stFileUploader [data-baseweb="button"], .stFileUploader [data-testid="baseButton-secondary"]').forEach(btn => {{
                            if (btn) {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important; box-shadow: ' + (bgColor === '#ffffff' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none') + ' !important;';
                                
                                // Fix ALL nested elements (divs, spans, p tags)
                                const allNested = btn.querySelectorAll('div, span, p');
                                allNested.forEach(el => {{
                                    el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Fix uploaded file visibility - ALWAYS VISIBLE - FORCE ALL TEXT
                        document.querySelectorAll('.stFileUploader .uploadedFile, .stFileUploader [data-testid="stFileUploaderFile"]').forEach(fileEl => {{
                            if (fileEl) {{
                                const fileBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const fileText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const fileBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.15)';
                                fileEl.style.cssText += 'background-color: ' + fileBg + ' !important; background: ' + fileBg + ' !important; color: ' + fileText + ' !important; border: 1px solid ' + fileBorder + ' !important;';
                                // Fix ALL nested elements - recursively
                                const allTextElements = fileEl.querySelectorAll('*');
                                allTextElements.forEach(textEl => {{
                                    if (textEl && textEl.tagName !== 'BUTTON' && textEl.tagName !== 'SVG') {{
                                        textEl.style.cssText += 'color: ' + fileText + ' !important; background-color: transparent !important;';
                                    }}
                                }});
                                // Also force direct children
                                Array.from(fileEl.children).forEach(child => {{
                                    child.style.cssText += 'color: ' + fileText + ' !important; background-color: ' + fileBg + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Middle theme + Upload buttons with respect to the Resume report (PDF) section
                        const pdfRow = document.querySelector('[data-testid="stHorizontalBlock"]:has(.report-hero)');
                        if (pdfRow && pdfRow.lastElementChild) {{
                            const actionsCol = pdfRow.lastElementChild;
                            actionsCol.style.display = 'flex';
                            actionsCol.style.flexDirection = 'column';
                            actionsCol.style.justifyContent = 'center';
                            actionsCol.style.gap = '8px';
                        }}
                        
                        // Fix theme toggle button - force theme colors and warm hover (APPLY TO ALL INSTANCES)
                        function fixThemeButtonGlow() {{
                            // Try multiple selectors to ensure we find it - MORE AGGRESSIVE
                            const themeBtnSelectors = [
                                'button[key="theme_toggle"]',
                                '.theme-toggle',
                                '[data-testid="stAppViewContainer"] button[key="theme_toggle"]',
                                '.stButton button[key="theme_toggle"]',
                                'button[data-baseweb="button"][key="theme_toggle"]',
                                '[data-testid="baseButton-secondary"][key="theme_toggle"]',
                                'button:has([data-testid="baseButton-secondary"])[key="theme_toggle"]'
                            ];
                            
                            themeBtnSelectors.forEach(selector => {{
                                document.querySelectorAll(selector).forEach(themeBtn => {{
                        if (themeBtn) {{
                                        const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                        const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                        const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)';
                                        
                                        // Continuously enforce no background glow
                                        if (!themeBtn.matches(':hover')) {{
                                            themeBtn.style.setProperty('background-color', btnBg, 'important');
                                            themeBtn.style.setProperty('background', btnBg, 'important');
                                            themeBtn.style.setProperty('background-image', 'none', 'important');
                                        }}
                                        
                                        if (!themeBtn.hasAttribute('data-theme-glow-applied')) {{
                                            themeBtn.setAttribute('data-theme-glow-applied', 'true');
                                            
                                            themeBtn.style.setProperty('background-color', btnBg, 'important');
                                            themeBtn.style.setProperty('background', btnBg, 'important');
                                            themeBtn.style.setProperty('color', btnText, 'important');
                                            themeBtn.style.setProperty('border-color', btnBorder, 'important');
                            
                            // Fix any nested divs
                                            const btnDivs = themeBtn.querySelectorAll('div, span, p');
                            btnDivs.forEach(div => {{
                                                div.style.setProperty('background-color', 'transparent', 'important');
                                                div.style.setProperty('background', 'transparent', 'important');
                                                div.style.setProperty('background-image', 'none', 'important');
                                                div.style.setProperty('color', btnText, 'important');
                                            }});
                                            
                                            // Add Warm Sun glow hover effect - boundary-only glow (matching textarea/dropzone)
                                            const warmHoverBorder = '#f5e6a8';
                                            const warmGlow = '0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4)';
                                            
                                            themeBtn.addEventListener('mouseenter', function(e) {{
                                                e.stopPropagation();
                                                this.style.setProperty('box-shadow', warmGlow, 'important');
                                                this.style.setProperty('border-color', warmHoverBorder, 'important');
                                                // Keep background unchanged - NO background glow
                                                this.style.setProperty('background-color', btnBg, 'important');
                                                this.style.setProperty('background', btnBg, 'important');
                                                this.style.setProperty('background-image', 'none', 'important');
                                                // Ensure nested elements remain transparent
                                                const allNested = this.querySelectorAll('*');
                                                allNested.forEach(el => {{
                                                    if (el && el.tagName !== 'SVG') {{
                                                        el.style.setProperty('background-color', 'transparent', 'important');
                                                        el.style.setProperty('background', 'transparent', 'important');
                                                        el.style.setProperty('background-image', 'none', 'important');
                                                    }}
                                                }});
                                            }}, true);
                                            
                                            // Also add mouseover as backup
                                            themeBtn.addEventListener('mouseover', function(e) {{
                                                e.stopPropagation();
                                                this.style.setProperty('box-shadow', warmGlow, 'important');
                                                this.style.setProperty('border-color', warmHoverBorder, 'important');
                                                this.style.setProperty('background-color', btnBg, 'important');
                                                this.style.setProperty('background', btnBg, 'important');
                                                this.style.setProperty('background-image', 'none', 'important');
                                            }}, true);
                                            
                                            themeBtn.addEventListener('mouseleave', function(e) {{
                                                e.stopPropagation();
                                                this.style.removeProperty('box-shadow');
                                                this.style.setProperty('border-color', btnBorder, 'important');
                                            }}, true);
                                            
                                            // Also add mouseout as backup
                                            themeBtn.addEventListener('mouseout', function(e) {{
                                                e.stopPropagation();
                                                this.style.removeProperty('box-shadow');
                                                this.style.setProperty('border-color', btnBorder, 'important');
                                            }}, true);
                                        }}
                                    }}
                                }});
                            }});
                        }}
                        
                        // Run continuously for a short warm-up period only.
                        fixThemeButtonGlow();
                        setTimeout(fixThemeButtonGlow, 10);
                        setTimeout(fixThemeButtonGlow, 50);
                        setTimeout(fixThemeButtonGlow, 100);
                        setTimeout(fixThemeButtonGlow, 200);
                        const themeBtnInterval = setInterval(fixThemeButtonGlow, 250);
                        setTimeout(() => clearInterval(themeBtnInterval), 12000);
                        
                        // Also run on DOM changes to catch dynamically added buttons
                        if (document.body) {{
                            new MutationObserver(() => {{
                                setTimeout(fixThemeButtonGlow, 5);
                            }}).observe(document.body, {{
                                childList: true,
                                subtree: true,
                                attributes: true,
                                attributeFilter: ['key', 'class', 'data-testid']
                            }});
                        }}
                        
                        // Run on all events
                        ['DOMContentLoaded', 'load', 'pageshow'].forEach(event => {{
                            window.addEventListener(event, fixThemeButtonGlow);
                        }});
                        
                        // Apply Warm Sun glow hover to textarea - boundary glow only (no background/inset)
                        document.querySelectorAll('.stTextArea textarea').forEach(textarea => {{
                            if (textarea) {{
                                const warmHoverBorder = '#f5e6a8';
                                const warmGlow = '0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4)';
                                textarea.addEventListener('mouseenter', function() {{
                                    this.style.cssText += 'box-shadow: ' + warmGlow + ' !important; border-color: ' + warmHoverBorder + ' !important; background: var(--bg-card) !important; background-color: var(--bg-card) !important;';
                                }});
                                textarea.addEventListener('mouseleave', function() {{
                                    if (!this.matches(':focus')) {{
                                        this.style.cssText = this.style.cssText.replace(/box-shadow:\\s*[^;]+/g, '').replace(/border-color:\\s*[^;]+/g, '');
                                    }}
                                }});
                            }}
                        }});
                        
                        /* Removed .stFileUploader hover - only dropzone should glow, matching textarea behavior */
                        
                        // Apply Warm Sun glow hover to dropzone - EXACTLY matching textarea hover style
                        function fixDropzoneGlow() {{
                            document.querySelectorAll('.stFileUploader [data-testid="stFileUploaderDropzone"]').forEach(dropzone => {{
                                if (dropzone) {{
                                    // Always remove box-shadow when not hovered (continuously enforce)
                                    if (!dropzone.matches(':hover')) {{
                                        dropzone.style.setProperty('box-shadow', 'none', 'important');
                                    }}
                                    // Always enforce background stays the same - NO background glow
                                    const dropzoneBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                    dropzone.style.setProperty('background', dropzoneBg, 'important');
                                    dropzone.style.setProperty('background-color', dropzoneBg, 'important');
                                    
                                    if (!dropzone.hasAttribute('data-glow-applied')) {{
                                        dropzone.setAttribute('data-glow-applied', 'true');
                                        
                                        // Explicitly remove any default box-shadow first (matching textarea behavior)
                                        dropzone.style.setProperty('box-shadow', 'none', 'important');
                                        
                                        // EXACT same values and approach as textarea - boundary glow only (no background/inset)
                                        const warmHoverBorder = '#f5e6a8';
                                        const warmGlow = '0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4)';
                                        
                                        const dropzoneBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                        dropzone.addEventListener('mouseenter', function() {{
                                            this.style.setProperty('box-shadow', warmGlow, 'important');
                                            this.style.setProperty('border-color', warmHoverBorder, 'important');
                                            // Explicitly prevent background color change - NO background glow
                                            this.style.setProperty('background', dropzoneBg, 'important');
                                            this.style.setProperty('background-color', dropzoneBg, 'important');
                                        }});
                                        
                                        dropzone.addEventListener('mouseleave', function() {{
                                            this.style.setProperty('box-shadow', 'none', 'important');
                                            this.style.removeProperty('border-color');
                                        }});
                                    }}
                                }}
                            }});
                        }}
                        
                        // Run immediately and keep polling briefly while Streamlit stabilizes.
                        fixDropzoneGlow();
                        const dropzoneInterval = setInterval(fixDropzoneGlow, 300);
                        setTimeout(() => clearInterval(dropzoneInterval), 12000);
                        
                        // Also run on DOM changes
                        if (document.body) {{
                            new MutationObserver(() => {{
                                setTimeout(fixDropzoneGlow, 5);
                            }}).observe(document.body, {{
                                childList: true,
                                subtree: true
                            }});
                        }}
                        
                        // Apply Warm Sun hover to "Upload another resume" button - boundary-only glow (matching textarea/dropzone)
                        function fixUploadButtonGlow() {{
                            document.querySelectorAll('button').forEach(btn => {{
                                if (btn && (btn.textContent && btn.textContent.includes('Upload another resume'))) {{
                                    const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                    
                                    // Continuously enforce no background glow
                                    if (!btn.matches(':hover')) {{
                                        btn.style.setProperty('background', btnBg, 'important');
                                        btn.style.setProperty('background-color', btnBg, 'important');
                                        btn.style.setProperty('background-image', 'none', 'important');
                                    }}
                                    
                                    if (!btn.hasAttribute('data-upload-glow-applied')) {{
                                        btn.setAttribute('data-upload-glow-applied', 'true');
                                        
                                        const warmHoverBorder = '#f5e6a8';
                                        const warmGlow = '0 0 20px rgba(250, 246, 219, 0.6), 0 0 40px rgba(250, 246, 219, 0.4)';
                                        
                                        btn.addEventListener('mouseenter', function() {{
                                            this.style.setProperty('box-shadow', warmGlow, 'important');
                                            this.style.setProperty('border-color', warmHoverBorder, 'important');
                                            // Keep background unchanged - NO background glow
                                            this.style.setProperty('background', btnBg, 'important');
                                            this.style.setProperty('background-color', btnBg, 'important');
                                            this.style.setProperty('background-image', 'none', 'important');
                                            // Ensure nested elements remain transparent
                                            const allNested = this.querySelectorAll('*');
                                            allNested.forEach(el => {{
                                                if (el && el.tagName !== 'SVG') {{
                                                    el.style.setProperty('background-color', 'transparent', 'important');
                                                    el.style.setProperty('background', 'transparent', 'important');
                                                    el.style.setProperty('background-image', 'none', 'important');
                                                }}
                                            }});
                                        }});
                                        
                                        btn.addEventListener('mouseleave', function() {{
                                            this.style.setProperty('box-shadow', 'none', 'important');
                                            this.style.removeProperty('border-color');
                                        }});
                                    }}
                                }}
                            }});
                        }}
                        
                        // Run continuously for a short warm-up period only.
                        fixUploadButtonGlow();
                        const uploadBtnInterval = setInterval(fixUploadButtonGlow, 300);
                        setTimeout(() => clearInterval(uploadBtnInterval), 12000);
                        
                        // Fix ALL secondary buttons
                        document.querySelectorAll('button[data-testid="baseButton-secondary"]').forEach(btn => {{
                            if (btn) {{
                                btn.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#ffffff' : '#1f2937') + ' !important; color: ' + (bgColor === '#ffffff' ? '#111827' : '#e5e7eb') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                            }}
                        }});
                        
                        // Fix Download Reports and any other buttons inside report area (override Streamlit dark defaults)
                        document.querySelectorAll('.report-main button, .report-sidebar button').forEach(btn => {{
                            if (btn) {{
                                const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                btn.style.cssText += 'background-color: ' + btnBg + ' !important; background: ' + btnBg + ' !important; color: ' + btnText + ' !important; border: 1px solid ' + btnBorder + ' !important;';
                                const nested = btn.querySelectorAll('*');
                                nested.forEach(el => {{
                                    if (el && el.style) el.style.cssText += 'background-color: transparent !important; color: ' + btnText + ' !important;';
                                }});
                            }}
                        }});
                        
                        // Catch-all: force theme on EVERY button in the app (download buttons may not be inside .report-main)
                        const viewContainer = document.querySelector('[data-testid="stAppViewContainer"]');
                        if (viewContainer) {{
                            viewContainer.querySelectorAll('button').forEach(btn => {{
                                if (btn) {{
                                    const btnBg = bgColor === '#ffffff' ? '#ffffff' : '#1f2937';
                                    const btnText = bgColor === '#ffffff' ? '#111827' : '#e5e7eb';
                                    const btnBorder = bgColor === '#ffffff' ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';
                                    btn.style.setProperty('background-color', btnBg, 'important');
                                    btn.style.setProperty('background', btnBg, 'important');
                                    btn.style.setProperty('color', btnText, 'important');
                                    btn.style.setProperty('border', '1px solid ' + btnBorder, 'important');
                                    btn.querySelectorAll('*').forEach(el => {{
                                        if (el && el.style) {{
                                            el.style.setProperty('background-color', 'transparent', 'important');
                                            el.style.setProperty('color', btnText, 'important');
                                        }}
                                    }});
                                }}
                            }});
                        }}
                    }} catch(e) {{
                        console.error('Theme error:', e);
                    }}
                }}
                
                // Run immediately multiple times
                forceTheme();
                setTimeout(forceTheme, 10);
                setTimeout(forceTheme, 50);
                setTimeout(forceTheme, 100);
                
                // Keep a moderate refresh interval and stop after warm-up.
                window.themeInterval = setInterval(forceTheme, 150);
                setTimeout(() => {{
                    if (window.themeInterval) {{
                        clearInterval(window.themeInterval);
                        window.themeInterval = null;
                    }}
                }}, 12000);
                
                // Also run on DOM changes
                if (document.body) {{
                    new MutationObserver(() => {{
                        setTimeout(forceTheme, 5);
                    }}).observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['style', 'class']
                    }});
                }}
                
                // Run on all events
                ['DOMContentLoaded', 'load'].forEach(event => {{
                    window.addEventListener(event, forceTheme);
                }});
            }})();
        </script>
        """,
        unsafe_allow_html=True,
    )




