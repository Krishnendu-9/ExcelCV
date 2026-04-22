"""
UI Constants - Centralized configuration for styling and theming.

This module contains all constants used for CSS styling, JavaScript,
and theme configuration to maintain consistency and ease of maintenance.
"""

from typing import Dict

# Theme Colors
LIGHT_BG_PRIMARY = "#ffffff"
LIGHT_TEXT_PRIMARY = "#111827"
DARK_BG_PRIMARY = "#0b0f17"
DARK_TEXT_PRIMARY = "#e5e7eb"

# Component Colors
LIGHT_BG_SECONDARY = "#f9fafb"
LIGHT_BG_CARD = "#ffffff"
LIGHT_BG_SIDEBAR = "#f3f4f6"
LIGHT_BG_HERO = "rgba(249, 250, 251, 0.95)"
LIGHT_TEXT_SECONDARY = "#6b7280"
LIGHT_BORDER = "rgba(0, 0, 0, 0.1)"
LIGHT_BORDER_LIGHT = "rgba(0, 0, 0, 0.05)"

DARK_BG_SECONDARY = "#111827"
DARK_BG_CARD = "#1f2937"
DARK_BG_SIDEBAR = "#0f172a"
DARK_BG_HERO = "rgba(15, 23, 42, 0.92)"
DARK_TEXT_SECONDARY = "#cbd5e1"
DARK_BORDER = "rgba(255, 255, 255, 0.1)"
DARK_BORDER_LIGHT = "rgba(255, 255, 255, 0.06)"

# Accent Colors
ACCENT_GREEN = "#10b981"
ACCENT_PURPLE = "#7c6bff"
TEXT_MUTED = "#9ca3af"

# Hover Effect Colors (Warm Sun)
WARM_HOVER_BORDER = "#f5e6a8"
WARM_GLOW_OUTER = "0 0 20px rgba(250, 246, 219, 0.6)"
WARM_GLOW_INNER = "0 0 40px rgba(250, 246, 219, 0.4)"
WARM_HOVER_GLOW = f"{WARM_GLOW_OUTER}, {WARM_GLOW_INNER}"

# Button Colors
LIGHT_BUTTON_BG = "#ffffff"
LIGHT_BUTTON_TEXT = "#111827"
LIGHT_BUTTON_BORDER = "rgba(0, 0, 0, 0.15)"
LIGHT_BUTTON_HOVER_BG = "#e5e7eb"
LIGHT_BUTTON_HOVER_BORDER = "rgba(0, 0, 0, 0.2)"
LIGHT_BUTTON_SHADOW = "0 1px 3px rgba(0, 0, 0, 0.1)"
LIGHT_BUTTON_HOVER_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.15)"

DARK_BUTTON_BG = "#1f2937"
DARK_BUTTON_TEXT = "#e5e7eb"
DARK_BUTTON_BORDER = "rgba(255, 255, 255, 0.1)"
DARK_BUTTON_HOVER_BG = "#374151"
DARK_BUTTON_HOVER_BORDER = "rgba(255, 255, 255, 0.2)"
DARK_BUTTON_SHADOW = "none"
DARK_BUTTON_HOVER_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.4)"

# Shadows
LIGHT_SHADOW = "rgba(0, 0, 0, 0.1)"
LIGHT_SHADOW_LG = "rgba(0, 0, 0, 0.15)"
DARK_SHADOW = "rgba(0, 0, 0, 0.3)"
DARK_SHADOW_LG = "rgba(0, 0, 0, 0.45)"

# Placeholder Colors
LIGHT_PLACEHOLDER = "#6b7280"
DARK_PLACEHOLDER = "#9ca3af"

# CSS Selectors
THEME_BUTTON_SELECTORS = [
    'button[key="theme_toggle"]',
    '.theme-toggle',
    '[data-testid="stAppViewContainer"] button[key="theme_toggle"]',
    '.stButton button[key="theme_toggle"]',
    'button[data-baseweb="button"][key="theme_toggle"]',
    '[data-testid="baseButton-secondary"][key="theme_toggle"]',
    'button:has([data-testid="baseButton-secondary"])[key="theme_toggle"]',
]

def get_theme_colors(is_light: bool) -> Dict[str, str]:
    """Get theme-specific color dictionary."""
    if is_light:
        return {
            "bg_primary": LIGHT_BG_PRIMARY,
            "text_primary": LIGHT_TEXT_PRIMARY,
            "bg_secondary": LIGHT_BG_SECONDARY,
            "bg_card": LIGHT_BG_CARD,
            "bg_sidebar": LIGHT_BG_SIDEBAR,
            "bg_hero": LIGHT_BG_HERO,
            "text_secondary": LIGHT_TEXT_SECONDARY,
            "border": LIGHT_BORDER,
            "border_light": LIGHT_BORDER_LIGHT,
            "shadow": LIGHT_SHADOW,
            "shadow_lg": LIGHT_SHADOW_LG,
            "button_bg": LIGHT_BUTTON_BG,
            "button_text": LIGHT_BUTTON_TEXT,
            "button_border": LIGHT_BUTTON_BORDER,
            "button_hover_bg": LIGHT_BUTTON_HOVER_BG,
            "button_hover_border": LIGHT_BUTTON_HOVER_BORDER,
            "button_shadow": LIGHT_BUTTON_SHADOW,
            "button_hover_shadow": LIGHT_BUTTON_HOVER_SHADOW,
            "placeholder": LIGHT_PLACEHOLDER,
        }
    else:
        return {
            "bg_primary": DARK_BG_PRIMARY,
            "text_primary": DARK_TEXT_PRIMARY,
            "bg_secondary": DARK_BG_SECONDARY,
            "bg_card": DARK_BG_CARD,
            "bg_sidebar": DARK_BG_SIDEBAR,
            "bg_hero": DARK_BG_HERO,
            "text_secondary": DARK_TEXT_SECONDARY,
            "border": DARK_BORDER,
            "border_light": DARK_BORDER_LIGHT,
            "shadow": DARK_SHADOW,
            "shadow_lg": DARK_SHADOW_LG,
            "button_bg": DARK_BUTTON_BG,
            "button_text": DARK_BUTTON_TEXT,
            "button_border": DARK_BUTTON_BORDER,
            "button_hover_bg": DARK_BUTTON_HOVER_BG,
            "button_hover_border": DARK_BUTTON_HOVER_BORDER,
            "button_shadow": DARK_BUTTON_SHADOW,
            "button_hover_shadow": DARK_BUTTON_HOVER_SHADOW,
            "placeholder": DARK_PLACEHOLDER,
        }
