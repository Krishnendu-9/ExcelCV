"""
UI Components Module

This module contains all UI-related functions for the CV Reviewer application,
including CSS injection, theme management, and report rendering.
"""

import json
import re
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from src.reporting import build_report_md
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
from src.js_generators import (
    generate_theme_force_js,
    generate_hover_effects_js,
    generate_scroll_to_section_js,
)


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
            /* Catch-all: every button in the app (e.g. Download Reports) – download buttons may sit outside .report-main in DOM */
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
                max-width: 1400px;
                background: transparent !important;
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
                margin-bottom: 8px;
            }}
            .brand-mark {{
                width: 38px;
                height: 38px;
                border-radius: 10px;
                background: linear-gradient(135deg, #10b981, #7c6bff);
                display: grid;
                place-items: center;
                font-weight: 800;
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
                color: var(--text-muted); 
                font-size: 0.85rem; 
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
                font-weight: 600;
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
                font-size: 1.35rem !important;
                margin-bottom: 12px !important;
                margin-top: 6px !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.6 !important;
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
                font-size: 1.35rem !important;
                margin-bottom: 12px !important;
                margin-top: 6px !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.6 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stTextArea label,
            body.theme-light .stTextArea > label,
            body.theme-light [data-testid="stTextArea"] label,
            body.theme-light .stForm .stTextArea label {{
                color: #1f2937 !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.25) !important;
                padding-bottom: 10px !important;
                margin-bottom: 18px !important;
            }}
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stTextArea label,
            body.theme-dark .stTextArea > label,
            body.theme-dark [data-testid="stTextArea"] label,
            body.theme-dark .stForm .stTextArea label {{
                color: #f9fafb !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.35) !important;
                padding-bottom: 10px !important;
                margin-bottom: 18px !important;
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
                border: 2px solid rgba(0, 0, 0, 0.1) !important;
                border-radius: 12px;
                padding: 24px;
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
                font-size: 1.35rem !important;
                margin-bottom: 12px !important;
                margin-top: 6px !important;
                display: block !important;
                letter-spacing: 0.03em !important;
                line-height: 1.6 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
                text-transform: none !important;
            }}
            /* Additional specificity for light mode - Professional styling with accent line */
            body.theme-light .stFileUploader label,
            body.theme-light .stFileUploader > label,
            body.theme-light [data-testid="stFileUploader"] label,
            body.theme-light .stForm .stFileUploader label {{
                color: #1f2937 !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.25) !important;
                padding-bottom: 10px !important;
                margin-bottom: 18px !important;
            }}
            
            /* Style file uploader - DARK MODE */
            body.theme-dark .stFileUploader {{
                border: 2px solid rgba(255, 255, 255, 0.1) !important;
                background: #111827 !important;
            }}
            /* Removed .stFileUploader:hover - only dropzone should glow, not the container */
            /* Additional specificity for dark mode - Professional styling with accent line */
            body.theme-dark .stFileUploader label,
            body.theme-dark .stFileUploader > label,
            body.theme-dark [data-testid="stFileUploader"] label,
            body.theme-dark .stForm .stFileUploader label {{
                color: #f9fafb !important;
                border-bottom: 2px solid rgba(124, 107, 255, 0.35) !important;
                padding-bottom: 10px !important;
                margin-bottom: 18px !important;
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
                margin: 0 0 10px;
                font-weight: 800;
                color: var(--text-primary);
            }}
            .hero-title span {{ 
                color: var(--accent); 
            }}
            .hero-subtitle {{
                color: var(--text-secondary);
                font-size: 1.1rem;
                margin-bottom: 16px;
                line-height: 1.6;
            }}
            .privacy-note {{
                color: var(--text-muted);
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
                padding: 24px;
                box-shadow: inset 0 1px 0 var(--border-light);
            }}
            .preview-card {{
                background: var(--bg-card) !important;
                border-radius: 18px;
                padding: 24px 24px 16px;
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
                margin-bottom: 14px;
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
                color: var(--text-muted); 
            }}
            .pill-row {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin: 6px 0 14px;
            }}
            .pill {{
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 6px 10px;
                border-radius: 10px;
                font-size: 0.82rem;
                font-weight: 600;
            }}
            .progress-shell {{
                margin: 16px 0 8px;
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
                padding: 10px 0;
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

            /* Report page – center theme + Upload buttons with PDF section */
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
            /* Make the columns container fill viewport height */
            [data-testid="stHorizontalBlock"] {{
                align-items: flex-start !important;
            }}
            /* Sidebar column: sticky */
            [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {{
                position: sticky !important;
                top: 0 !important;
                align-self: flex-start !important;
                max-height: 100vh !important;
                overflow-y: auto !important;
            }}
            .report-sidebar {{
                background: var(--bg-sidebar);
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 20px;
                box-shadow: 0 14px 50px var(--shadow);
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
                font-weight: 800; 
                color: #fcd34d; 
            }}
            .score-number span {{ 
                font-size: 1rem; 
                color: var(--text-muted); 
            }}
            .issues-text {{ 
                color: var(--text-muted); 
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
                margin-bottom: 8px;
                color: var(--text-primary);
                font-weight: 700;
                letter-spacing: 0.03em;
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
                color: var(--text-muted);
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
                border-radius: 10px;
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
                gap: 10px;
                color: var(--text-muted);
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
                background: var(--bg-card);
                border: 1px solid var(--border-light);
                border-radius: 18px;
                padding: 20px;
                box-shadow: 0 14px 50px var(--shadow);
            }}
            .detail-card {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-light);
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 14px;
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
            /* Shared body area for all report sections (Quantifying Impact, Spelling & Grammar, Strengths, etc.) – same as Suggestions */
            .section-body {{
                padding: 0 0 4px 0;
                margin: 0;
            }}
            .section-body-item {{
                margin-bottom: 8px;
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
            .list-tag {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 10px;
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
                color: var(--text-muted); 
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
            
            /* Report area buttons (Download Reports, etc.) use theme colors – light in light mode */
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
            .report-main {{
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
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.35rem !important; margin-bottom: 12px !important; margin-top: 6px !important; display: block !important; letter-spacing: 0.03em !important; line-height: 1.6 !important; border-bottom: 2px solid ' + borderColor + ' !important; padding-bottom: 10px !important; margin-bottom: 18px !important;';
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
                                label.style.cssText += 'color: ' + labelColor + ' !important; font-weight: 700 !important; font-size: 1.35rem !important; margin-bottom: 12px !important; margin-top: 6px !important; display: block !important; letter-spacing: 0.03em !important; line-height: 1.6 !important; border-bottom: 2px solid ' + borderColor + ' !important; padding-bottom: 10px !important; margin-bottom: 18px !important;';
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
                                uploader.style.cssText += 'background-color: ' + (bgColor === '#ffffff' ? '#f9fafb' : '#111827') + ' !important; border-color: ' + (bgColor === '#ffffff' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)') + ' !important;';
                                
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
                        
                        // Run continuously to prevent background glow - AGGRESSIVE
                        fixThemeButtonGlow();
                        setTimeout(fixThemeButtonGlow, 10);
                        setTimeout(fixThemeButtonGlow, 50);
                        setTimeout(fixThemeButtonGlow, 100);
                        setTimeout(fixThemeButtonGlow, 200);
                        setInterval(fixThemeButtonGlow, 50);
                        
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
                        
                        // Run immediately and continuously to prevent any default glow
                        fixDropzoneGlow();
                        setInterval(fixDropzoneGlow, 50);
                        
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
                        
                        // Run continuously to prevent background glow
                        fixUploadButtonGlow();
                        setInterval(fixUploadButtonGlow, 50);
                        
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
                
                // Run continuously every 10ms to aggressively override Streamlit
                window.themeInterval = setInterval(forceTheme, 10);
                
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
        return "✓"
    if score >= 60:
        return "⚠"
    return "✗"


def issue_count(analysis: Dict[str, Any]) -> int:
    """Count total issues found in analysis."""
    count = 0
    count += len(analysis.get("missing_keywords", []))
    count += len(analysis.get("missing_skills", []))
    count += len([s for s in analysis.get("suggestions", []) if s.strip()])
    if analysis.get("match_score", 0) < 70:
        count += 1
    return max(count, 0)


def render_upload_preview_card() -> None:
    """Static preview card on the upload screen."""
    st.markdown(
        """
        <div class="upload-preview">
            <div class="preview-card">
                <div class="preview-header">
                    <div>
                        <div style="font-weight:700;" class="text-primary">ATS Resume Score</div>
                        <div class="text-muted" style="font-size:0.9rem;">Sample preview</div>
                    </div>
                    <div class="preview-badge">LIVE</div>
                </div>
                <div class="preview-score"><span class="num">92</span><span class="den">/100</span></div>
                <div class="pill-row">
                    <span class="pill">ATS Parse</span>
                    <span class="pill">Quantified Impact</span>
                    <span class="pill">Sections</span>
                    <span class="pill">Skills</span>
                </div>
                <div class="progress-shell">
                    <div class="progress-track">
                        <div class="progress-fill" style="width:90%;"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-top:6px;" class="text-secondary">
                        <span>Parse rate</span><span>90%</span>
                    </div>
                </div>
                <div class="list-row"><span>ATS Parse Rate</span><span>✓</span></div>
                <div class="list-row"><span>Quantifying Impact</span><span>✓</span></div>
                <div class="list-row"><span>Repetition</span><span>⚠</span></div>
                <div class="list-row"><span>Spelling & Grammar</span><span>✕</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_sidebar_html(score: int, issues: int, categories: list) -> str:
    """Build the entire sidebar as one complete HTML string."""
    issues_cls = 'clickable' if issues > 0 else ''
    issues_attr = 'data-section-id="suggestions"' if issues > 0 else ''

    html = f"""
    <div class="report-sidebar">
        <div class="score-card">
            <div class="score-title text-muted" style="font-size:0.95rem;">Your Score</div>
            <div class="score-number">{score}<span>/100</span></div>
            <div class="issues-text {issues_cls}" {issues_attr}>{issues} issues</div>
        </div>"""

    for title, cat_score, items in categories:
        safe_score = int(cat_score) if cat_score is not None else 0
        badge_cls = get_score_color_class(safe_score)
        category_id = title.lower().replace(" ", "-")
        has_items = len(items) > 0
        cursor = 'cursor:pointer;' if has_items else ''
        chevron = '<span class="category-chevron">&#9660;</span>' if has_items else ''

        html += f"""
        <div class="category">
            <div class="category-head" id="cat-head-{category_id}" style="{cursor}">
                <span class="category-title">
                    <span>{title}</span>
                    {chevron}
                </span>
                <span class="category-score {badge_cls}">{safe_score}%</span>
            </div>"""

        if has_items:
            html += f'<div class="category-items collapsed" id="cat-items-{category_id}">'
            for item in items:
                item_label, status = item[0], item[1]
                score_val = item[2] if len(item) > 2 else None
                badge_class = {"ok": "badge badge-ok", "warn": "badge badge-warn",
                               "error": "badge badge-warn", "lock": "badge badge-lock"
                               }.get(status, "badge badge-warn")

                if status in ("warn", "error"):
                    if score_val is not None and isinstance(score_val, (int, float)) and score_val <= 100:
                        badge_text = f"{int(score_val)}%"
                    elif score_val is not None:
                        badge_text = f"{score_val} {'issue' if score_val == 1 else 'issues'}"
                    else:
                        badge_text = "Review"
                else:
                    badge_text = {"ok": "No issues", "lock": "Locked"}.get(status, "Review")

                section_id = item_label.lower().replace(" & ", "-").replace(" ", "-").replace("--", "-").strip("-")
                icon_cls = "icon-ok" if status == "ok" else "icon-warn"
                icon = "&#10003;" if status == "ok" else "&#10005;"
                clickable = "clickable" if status != "lock" else ""
                data = f'data-section-id="{section_id}"' if status != "lock" else ""

                html += f"""
                <div class="subitem {clickable}" {data}>
                    <span class="subitem-label-wrap">
                        <span class="subitem-icon {icon_cls}">{icon}</span>
                        <span>{item_label}</span>
                    </span>
                    <span class="{badge_class}">{badge_text}</span>
                </div>"""
            html += '</div>'  # close category-items

        html += '</div>'  # close category

    html += '</div>'  # close report-sidebar
    return html


def _build_sidebar_js() -> str:
    """Build JavaScript for sidebar interactions. Runs in components.html iframe."""
    return """
    <script>
    (function() {
        var doc = window.parent.document;

        // Toggle expand/collapse for a category
        function toggleCategory(categoryId) {
            var head = doc.getElementById('cat-head-' + categoryId);
            var items = doc.getElementById('cat-items-' + categoryId);
            if (!head || !items) return;

            if (head.classList.contains('expanded')) {
                head.classList.remove('expanded');
                items.classList.remove('expanded');
                items.classList.add('collapsed');
            } else {
                head.classList.add('expanded');
                items.classList.remove('collapsed');
                items.classList.add('expanded');
            }
        }

        // Scroll to a section in the main (right) column
        function scrollToSection(sectionId) {
            var el = doc.getElementById(sectionId);
            if (!el) return;

            // Simple and reliable: scrollIntoView on the parent window
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Brief highlight effect
            el.style.transition = 'background-color 0.3s ease';
            var origBg = el.style.backgroundColor;
            el.style.backgroundColor = 'rgba(16,185,129,0.15)';
            setTimeout(function() { el.style.backgroundColor = origBg; }, 1200);
        }

        // Event delegation on parent document
        function handleClick(e) {
            var t = e.target;
            if (!t || !t.closest) return;

            // Category header click -> toggle
            var head = t.closest('.category-head');
            if (head && head.id && head.id.indexOf('cat-head-') === 0) {
                var catId = head.id.replace('cat-head-', '');
                toggleCategory(catId);
                e.stopPropagation();
                e.preventDefault();
                return;
            }
            // Sub-item click -> scroll
            var subitem = t.closest('.subitem');
            if (subitem) {
                var sid = subitem.getAttribute('data-section-id');
                if (sid) {
                    scrollToSection(sid);
                    e.stopPropagation();
                    e.preventDefault();
                    return;
                }
            }
            // Issues text click -> scroll
            var issueEl = t.closest('.issues-text');
            if (issueEl) {
                var isid = issueEl.getAttribute('data-section-id');
                if (isid) {
                    scrollToSection(isid);
                    e.stopPropagation();
                    e.preventDefault();
                    return;
                }
            }
        }

        // Remove previous listener if any, then attach new one
        if (window.parent.__sidebarClickHandler) {
            doc.removeEventListener('click', window.parent.__sidebarClickHandler, true);
        }
        window.parent.__sidebarClickHandler = handleClick;
        doc.addEventListener('click', handleClick, true);

        // Also attach direct click handlers to all subitems as backup
        function attachDirectHandlers() {
            var subitems = doc.querySelectorAll('.subitem[data-section-id]');
            subitems.forEach(function(item) {
                if (item.getAttribute('data-direct-bound')) return;
                item.setAttribute('data-direct-bound', '1');
                item.style.cursor = 'pointer';
                item.addEventListener('click', function(ev) {
                    var secId = item.getAttribute('data-section-id');
                    if (secId) scrollToSection(secId);
                    ev.stopPropagation();
                    ev.preventDefault();
                });
            });
            var issues = doc.querySelectorAll('.issues-text[data-section-id]');
            issues.forEach(function(item) {
                if (item.getAttribute('data-direct-bound')) return;
                item.setAttribute('data-direct-bound', '1');
                item.style.cursor = 'pointer';
                item.addEventListener('click', function(ev) {
                    var secId = item.getAttribute('data-section-id');
                    if (secId) scrollToSection(secId);
                    ev.stopPropagation();
                    ev.preventDefault();
                });
            });
        }
        // Run direct attachment with retries
        attachDirectHandlers();
        setTimeout(attachDirectHandlers, 500);
        setTimeout(attachDirectHandlers, 1000);
        setTimeout(attachDirectHandlers, 2000);

        // Auto-expand Content on load
        function initContent() {
            var head = doc.getElementById('cat-head-content');
            var items = doc.getElementById('cat-items-content');
            if (head && items && !head.classList.contains('expanded')) {
                head.classList.add('expanded');
                items.classList.remove('collapsed');
                items.classList.add('expanded');
            }
        }
        // Retry until elements exist
        var attempts = 0;
        var initTimer = setInterval(function() {
            initContent();
            attempts++;
            if (attempts > 20 || doc.getElementById('cat-head-content')) {
                clearInterval(initTimer);
            }
        }, 200);
    })();
    </script>
    """


def render_report_page(analysis: Dict[str, Any], name: str = "CV") -> None:
    """Render the two-column report view inspired by the HTML mock."""
    score = analysis.get("match_score", 0)
    subs = analysis.get("subscores", {}) or {}
    issues = issue_count(analysis)

    # Extract content metrics
    content_metrics = analysis.get("content_metrics", {}) or {}
    ats_parse_rate = content_metrics.get("ats_parse_rate", 0)
    quant_impact = content_metrics.get("quantifying_impact", {}) or {}
    repetition = content_metrics.get("repetition", {}) or {}
    spelling_grammar = content_metrics.get("spelling_grammar", {}) or {}
    
    # Calculate Content category score as average of content metrics
    content_items = [
        ats_parse_rate,
        quant_impact.get("score", 0),
        repetition.get("score", 0),
        spelling_grammar.get("score", 0)
    ]
    content_score = int(sum(content_items) / len(content_items)) if content_items else subs.get("ats_readiness", score)
    
    # Build Content category items: (label, status, score) so sidebar can show number instead of "Review"
    content_items_list = [
        ("ATS Parse Rate", "ok" if ats_parse_rate >= 80 else "warn" if ats_parse_rate >= 60 else "error", ats_parse_rate),
        ("Quantifying Impact", quant_impact.get("status", "ok"), quant_impact.get("score", 0)),
        ("Repetition", repetition.get("status", "ok"), repetition.get("score", 0)),
        ("Spelling & Grammar", spelling_grammar.get("status", "ok"), spelling_grammar.get("score", 0)),
    ]
    
    # Extract other category metrics
    sections_metrics = analysis.get("sections_metrics", {}) or {}
    sections_score = sections_metrics.get("score", subs.get("experience_alignment", score)) or 0
    sections_details = sections_metrics.get("details", {}) or {}
    
    # Build Sections category items
    sections_items_list = []
    missing_sections = sections_details.get("missing_sections", [])
    if missing_sections:
        sections_items_list.append(("Essential Sections", "error", len(missing_sections)))
    if not sections_details.get("has_contact", True):
        sections_items_list.append(("Contact Information", "error", 1))
    
    ats_essentials_metrics = analysis.get("ats_essentials_metrics", {}) or {}
    ats_essentials_score = ats_essentials_metrics.get("score", subs.get("ats_readiness", score)) or 0
    ats_essentials_details = ats_essentials_metrics.get("details", {}) or {}
    
    # Build ATS Essentials category items
    ats_items_list = []
    ats_issues = ats_essentials_details.get("issues", [])
    if ats_essentials_details.get("standard_formatting", True):
        ats_items_list.append(("File Format & Size", "ok", None))
    else:
        ats_items_list.append(("File Format & Size", "warn", 1))
    if ats_issues:
        ats_items_list.append(("Design", "warn" if len(ats_issues) > 0 else "ok", len(ats_issues)))
    if ats_essentials_details.get("section_headers_present", False):
        ats_items_list.append(("Email Address", "ok", None))
        ats_items_list.append(("Hyperlink in Header", "ok", None))
    
    categories = [
        ("Content", content_score, content_items_list),
        ("Sections", sections_score, sections_items_list),
        ("ATS Essentials", ats_essentials_score, ats_items_list),
    ]

    # No report-shell wrapper (it was rendering as a bar); columns put Your Score and ATS Parse Rate side by side
    sidebar, main = st.columns([1, 1.6], gap="large")

    with sidebar:
        # Build the ENTIRE sidebar as ONE HTML string
        sidebar_html = _build_sidebar_html(score, issues, categories)
        st.markdown(sidebar_html, unsafe_allow_html=True)

        # Inject JavaScript via components.html (guaranteed execution)
        components.html(_build_sidebar_js(), height=0)

        # Download buttons
        st.download_button(
            "📄 Download report (Markdown)",
            data=build_report_md(name, analysis),
            file_name=f"{name}-analysis.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_md_sidebar",
        )
        st.download_button(
            "💾 Download JSON",
            data=json.dumps(analysis, indent=2),
            file_name=f"{name}-analysis.json",
            mime="application/json",
            use_container_width=True,
            key="download_json_sidebar",
        )

    with main:
        # Full ATS card in one markdown with report-main wrapper to avoid empty bar above ATS Parse Rate
        ats_parse_rate_value = content_metrics.get("ats_parse_rate", 0)
        ats_badge_class = "badge-ok" if ats_parse_rate_value >= 80 else "badge-warn" if ats_parse_rate_value >= 60 else "badge-warn"
        ats_badge_text = "Excellent" if ats_parse_rate_value >= 80 else "Good" if ats_parse_rate_value >= 60 else "Needs Improvement"
        st.markdown(
            f"""
            <div class="report-main">
            <div class="detail-card section-anchor" id="ats-parse-rate">
            <div class="detail-head">
                <h3>ATS Parse Rate</h3>
                <span class="badge {ats_badge_class}">{ats_badge_text}</span>
            </div>
            <div class="section-body">
            <p class="section-body-item text-description">A high parse rate ensures the ATS can read your resume, experience, and skills.</p>
            <div class="progress-track dark">
                <div class="progress-fill dark" style="width:{ats_parse_rate_value}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                <span>Score</span><span>{ats_parse_rate_value}%</span>
            </div>
            </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Content metric cards (scores and status from backend programmatic + optional AI logic)
        quant_score = quant_impact.get("score", 0)
        quant_status = quant_impact.get("status", "ok")
        quant_details = quant_impact.get("details", "")
        quant_badge = "ok" if quant_status == "ok" else "warn"
        quant_label = "No issues" if quant_status == "ok" else f"{quant_score}%"
        st.markdown(
            f"""
            <div class="detail-card section-anchor" id="quantifying-impact">
            <div class="detail-head">
                <h3>Quantifying Impact</h3>
                <span class="badge badge-{quant_badge}">{quant_label}</span>
            </div>
            <div class="section-body">
            <p class="section-body-item text-description">Your resume should include quantifiable achievements with numbers, metrics, and measurable results.</p>
            <div class="progress-track dark">
                <div class="progress-fill dark" style="width:{quant_score}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                <span>Score</span><span>{quant_score}%</span>
            </div>
            {f'<p class="section-body-item text-description" style="margin-top:8px;font-size:0.9rem;">{quant_details}</p>' if quant_details else ''}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rep_score = repetition.get("score", 0)
        rep_status = repetition.get("status", "ok")
        rep_details = repetition.get("details", "")
        rep_badge = "ok" if rep_status == "ok" else "warn"
        rep_label = "No issues" if rep_status == "ok" else f"{rep_score}%"
        st.markdown(
            f"""
            <div class="detail-card section-anchor" id="repetition">
            <div class="detail-head">
                <h3>Repetition</h3>
                <span class="badge badge-{rep_badge}">{rep_label}</span>
            </div>
            <div class="section-body">
            <p class="section-body-item text-description">Avoid excessive repetition of words and phrases to improve readability and professionalism.</p>
            <div class="progress-track dark">
                <div class="progress-fill dark" style="width:{rep_score}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                <span>Score (higher = less repetition)</span><span>{rep_score}%</span>
            </div>
            {f'<p class="section-body-item text-description" style="margin-top:8px;font-size:0.9rem;">{rep_details}</p>' if rep_details else ''}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        spell_score = spelling_grammar.get("score", 0)
        spell_status = spelling_grammar.get("status", "ok")
        spell_details = spelling_grammar.get("details", "")
        spell_badge = "ok" if spell_status == "ok" else "warn"
        spell_label = "No issues" if spell_status == "ok" else f"{spell_score}%"
        st.markdown(
            f"""
            <div class="detail-card section-anchor" id="spelling-grammar">
            <div class="detail-head">
                <h3>Spelling & Grammar</h3>
                <span class="badge badge-{spell_badge}">{spell_label}</span>
            </div>
            <div class="section-body">
            <p class="section-body-item text-description">Ensure your resume is free of spelling and grammatical errors for a professional appearance.</p>
            <div class="progress-track dark">
                <div class="progress-fill dark" style="width:{spell_score}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;" class="text-muted">
                <span>Score</span><span>{spell_score}%</span>
            </div>
            {f'<p class="section-body-item text-description" style="margin-top:8px;font-size:0.9rem;">{spell_details}</p>' if spell_details else ''}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Strengths and gaps
        def render_list_block(title: str, items: List[str], badge: str, section_id: str = None) -> None:
            if section_id:
                st.markdown(f'<div class="detail-card section-anchor" id="{section_id}">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="detail-card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="detail-head">
                    <h3>{title}</h3>
                    <span class="badge {badge}">{len(items) or '0'} items</span>
                </div>
                <div class="section-body">
                """,
                unsafe_allow_html=True,
            )
            if items:
                for idx, item in enumerate(items, 1):
                    item_html = _markdown_inline_to_html(item)
                    st.markdown(
                        f'<p class="section-body-item text-primary"><strong>{idx}.</strong> {item_html}</p>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<p class="section-body-item text-muted">Nothing noted here yet.</p>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div></div>", unsafe_allow_html=True)

        render_list_block("Strengths", analysis.get("strengths", []), "badge-ok")
        render_list_block("Missing skills", analysis.get("missing_skills", []), "badge-warn", "missing-skills")
        render_list_block("Missing keywords (ATS)", analysis.get("missing_keywords", []), "badge-warn", "missing-keywords")

        # Suggestions (same section-body layout as other sections)
        suggestions = analysis.get("suggestions", [])
        st.markdown('<div class="detail-card section-anchor" id="suggestions">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="detail-head">
                <h3>Suggestions</h3>
                <span class="badge badge-ok">{len(suggestions) or '0'} tips</span>
            </div>
            <div class="section-body">
            """,
            unsafe_allow_html=True,
        )
        if suggestions:
            for idx, suggestion in enumerate(suggestions, 1):
                suggestion_html = _markdown_inline_to_html(suggestion)
                st.markdown(
                    f'<p class="section-body-item text-primary"><strong>{idx}.</strong> {suggestion_html}</p>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<p class="section-body-item text-muted">No suggestions provided.</p>', unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        # Download buttons in main content area for better visibility
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Download Reports", unsafe_allow_html=False)
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.download_button(
                "📄 Download Markdown Report",
                data=build_report_md(name, analysis),
                file_name=f"{name}-analysis.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_md_main",
            )
        with col2:
            st.download_button(
                "💾 Download JSON Export",
                data=json.dumps(analysis, indent=2),
                file_name=f"{name}-analysis.json",
                mime="application/json",
                use_container_width=True,
                key="download_json_main",
            )
        st.markdown("</div>", unsafe_allow_html=True)

