"""CSS/JS injection helpers: header bar, form spacing, fixed top-bar, logo behaviour."""

import streamlit as st
import streamlit.components.v1 as components

def inject_file_uploader_spacing_css() -> None:
    """
    Inject custom CSS to position labels directly on top of their boxes
    for both 'Job description' and 'Upload resume (PDF or DOCX)'.
    """
    st.markdown(
        """
        <style>

        /* ── Position labels directly on top of boxes - Clean design ── */

        /* Textarea labels - scoped only to upload/comparison forms */
        .st-key-upload_form .stTextArea > label,
        .st-key-upload_form .stTextArea label,
        .st-key-upload_form [data-testid="stTextArea"] > label,
        .st-key-upload_form [data-testid="stTextArea"] label,
        .st-key-comparison_form .stTextArea > label,
        .st-key-comparison_form .stTextArea label,
        .st-key-comparison_form [data-testid="stTextArea"] > label,
        .st-key-comparison_form [data-testid="stTextArea"] label {
            margin-bottom: 2px !important;
            margin-top: 0 !important;
            padding-bottom: 2px !important;
        }

        /* File uploader labels - scoped only to upload/comparison forms */
        .st-key-upload_form .stFileUploader > label,
        .st-key-upload_form .stFileUploader label,
        .st-key-upload_form [data-testid="stFileUploader"] > label,
        .st-key-upload_form [data-testid="stFileUploader"] label,
        .st-key-comparison_form .stFileUploader > label,
        .st-key-comparison_form .stFileUploader label,
        .st-key-comparison_form [data-testid="stFileUploader"] > label,
        .st-key-comparison_form [data-testid="stFileUploader"] label {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Remove ALL gaps between label containers and input boxes */
        .st-key-upload_form .stTextArea > div:first-child,
        .st-key-upload_form .stTextArea > div:first-of-type,
        .st-key-upload_form .stTextArea > div,
        .st-key-comparison_form .stTextArea > div:first-child,
        .st-key-comparison_form .stTextArea > div:first-of-type,
        .st-key-comparison_form .stTextArea > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
        }

        .st-key-upload_form .stFileUploader > div:first-of-type,
        .st-key-upload_form .stFileUploader > div,
        .st-key-upload_form [data-testid="stFileUploader"] > div,
        .st-key-upload_form [data-testid="stFileUploader"] > div:first-child,
        .st-key-comparison_form .stFileUploader > div:first-of-type,
        .st-key-comparison_form .stFileUploader > div,
        .st-key-comparison_form [data-testid="stFileUploader"] > div,
        .st-key-comparison_form [data-testid="stFileUploader"] > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Ensure textarea sits directly below label with no gap */
        .st-key-upload_form .stTextArea textarea,
        .st-key-comparison_form .stTextArea textarea {
            margin-top: 0 !important;
            padding-top: 10px !important;
        }

        /* Ensure dropzone sits directly below label with no gap */
        .st-key-upload_form [data-testid="stFileUploaderDropzone"],
        .st-key-upload_form section[data-testid="stFileUploadDropzone"],
        .st-key-upload_form .stFileUploader [data-testid="stFileUploaderDropzone"],
        .st-key-comparison_form [data-testid="stFileUploaderDropzone"],
        .st-key-comparison_form section[data-testid="stFileUploadDropzone"],
        .st-key-comparison_form .stFileUploader [data-testid="stFileUploaderDropzone"] {
            margin-top: 0 !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }

        /* Remove any wrapper gaps completely */
        .st-key-upload_form .stTextArea,
        .st-key-comparison_form .stTextArea {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
        }

        .st-key-upload_form .stFileUploader,
        .st-key-comparison_form .stFileUploader {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Remove spacing from form containers */
        .st-key-upload_form .stTextArea,
        .st-key-upload_form .stFileUploader,
        .st-key-comparison_form .stTextArea,
        .st-key-comparison_form .stFileUploader {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Tighten top controls only inside upload/comparison forms (avoid leaking into CV Builder). */
        .st-key-upload_form .stSelectbox,
        .st-key-upload_form .stCheckbox,
        .st-key-upload_form .stSelectbox label,
        .st-key-upload_form .stCheckbox label,
        .st-key-comparison_form .stSelectbox,
        .st-key-comparison_form .stCheckbox,
        .st-key-comparison_form .stSelectbox label,
        .st-key-comparison_form .stCheckbox label {
            margin-top: 0 !important;
            margin-bottom: 2px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            line-height: 1.2 !important;
        }
        .st-key-upload_form [data-testid="stVerticalBlock"] > div,
        .st-key-comparison_form [data-testid="stVerticalBlock"] > div {
            margin-bottom: 6px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_compact_header_css() -> None:
    """Render a contained top bar visual style (geometry is fixed by JS sync)."""
    is_dark = st.session_state.get("theme", "light") == "dark"
    header_bg = "rgba(6, 12, 28, 0.66)" if is_dark else "rgba(255, 255, 255, 0.56)"
    toggle_btn_bg = "rgba(30, 41, 59, 0.52)" if is_dark else "rgba(226, 232, 240, 0.72)"
    toggle_btn_border = "rgba(148, 163, 184, 0.34)" if is_dark else "rgba(100, 116, 139, 0.34)"
    toggle_icon_color = "#f8fafc" if is_dark else "#0f172a"
    nav_active_color = "#38bdf8" if is_dark else "#1667d9"
    header_filter = (
        "blur(12px) saturate(120%)"
        if is_dark
        else "blur(12px) saturate(108%) brightness(1.04)"
    )
    header_shadow = (
        "0 4px 16px rgba(2, 6, 23, 0.20)"
        if is_dark
        else "none"
    )
    compare_box_border = "rgba(56, 189, 248, 0.24)" if is_dark else "rgba(148, 163, 184, 0.42)"
    compare_box_bg = (
        "radial-gradient(200px 130px at 78% 10%, rgba(45, 212, 191, 0.09), transparent 70%), "
        "linear-gradient(170deg, rgba(7, 16, 36, 0.82), rgba(2, 8, 24, 0.8))"
        if is_dark
        else "linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.98))"
    )
    compare_box_shadow = (
        "0 12px 24px rgba(2, 6, 23, 0.32)"
        if is_dark
        else "0 10px 20px rgba(15, 23, 42, 0.12)"
    )
    compare_label_color = "#e2e8f0" if is_dark else "#1e293b"
    compare_textarea_bg = "rgba(30, 41, 59, 0.62)" if is_dark else "rgba(255, 255, 255, 0.98)"
    compare_textarea_border = "rgba(100, 116, 139, 0.55)" if is_dark else "rgba(148, 163, 184, 0.62)"
    compare_textarea_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_placeholder = "#94a3b8" if is_dark else "#64748b"
    compare_dropzone_bg = "rgba(30, 41, 59, 0.56)" if is_dark else "rgba(248, 250, 252, 0.98)"
    compare_button_bg = "rgba(30, 41, 59, 0.88)" if is_dark else "rgba(226, 232, 240, 0.95)"
    compare_button_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_button_border = "rgba(71, 85, 105, 0.7)" if is_dark else "rgba(148, 163, 184, 0.7)"
    compare_hover_bg = "rgba(37, 99, 235, 0.16)" if is_dark else "rgba(239, 246, 255, 0.98)"
    compare_hover_border = "rgba(56, 189, 248, 0.65)" if is_dark else "rgba(37, 99, 235, 0.62)"
    compare_hover_shadow = (
        "0 0 0 3px rgba(56, 189, 248, 0.14)"
        if is_dark
        else "0 0 0 3px rgba(37, 99, 235, 0.14)"
    )
    guest_title_color = "#e2e8f0" if is_dark else "#0f172a"
    guest_body_color = "#94a3b8" if is_dark else "#64748b"
    guest_icon_bg = "rgba(37, 99, 235, 0.18)" if is_dark else "rgba(37, 99, 235, 0.10)"
    guest_icon_color = "#93c5fd" if is_dark else "#1d4ed8"
    guest_cta_bg = "linear-gradient(135deg, #2563eb, #3b82f6)"
    guest_cta_text = "#ffffff"
    guest_cta_border = "rgba(59, 130, 246, 0.55)"
    preview_shell_bg = (
        "linear-gradient(155deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.88))"
        if is_dark
        else "linear-gradient(155deg, rgba(241, 245, 249, 0.96), rgba(226, 232, 240, 0.92))"
    )
    preview_shell_border = "rgba(148, 163, 184, 0.22)" if is_dark else "rgba(148, 163, 184, 0.36)"
    preview_card_bg = (
        "linear-gradient(160deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.82))"
        if is_dark
        else "linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.95))"
    )
    preview_card_border = "rgba(148, 163, 184, 0.28)" if is_dark else "rgba(148, 163, 184, 0.36)"
    preview_text = "#e2e8f0" if is_dark else "#0f172a"
    preview_muted = "#94a3b8" if is_dark else "#475569"
    preview_chip_bg = "rgba(148, 163, 184, 0.18)" if is_dark else "rgba(148, 163, 184, 0.20)"
    preview_track_bg = "rgba(148, 163, 184, 0.20)" if is_dark else "rgba(148, 163, 184, 0.22)"
    css = """
        <style>
        :root {
            --excelcv-uniform-hover-bg: __COMPARE_HOVER_BG__;
            --excelcv-uniform-hover-border: __COMPARE_HOVER_BORDER__;
            --excelcv-uniform-hover-shadow: __COMPARE_HOVER_SHADOW__;
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            min-height: 0 !important;
        }
        /* Contained top bar (fixed geometry applied by inject_fixed_top_bar JS). */
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) {
            display: flex !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 8px !important;
            width: min(1800px, calc(100vw - 90px)) !important;
            margin: 0 auto !important;
            margin-bottom: 0 !important;
            padding: 0 16px !important;
            height: 60px !important;
            min-height: 60px !important;
            max-height: 60px !important;
            box-sizing: border-box !important;
            background: __HEADER_BG__ !important;
            border: none !important;
            outline: none !important;
            border-radius: 10px !important;
            -webkit-backdrop-filter: __HEADER_FILTER__ !important;
            backdrop-filter: __HEADER_FILTER__ !important;
            box-shadow: __HEADER_SHADOW__ !important;
        }
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) > div {
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) > div > div {
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) [data-testid="stElementContainer"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        .site-brand {
            min-height: 40px !important;
            max-height: 40px !important;
            overflow: hidden !important;
            padding-top: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
        }
        .site-logo-link {
            display: inline-flex !important;
            align-items: center !important;
            text-decoration: none !important;
            cursor: pointer !important;
            position: relative !important;
            z-index: 30 !important;
            pointer-events: auto !important;
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            outline: none !important;
            -webkit-appearance: none !important;
            appearance: none !important;
            user-select: none !important;
            -webkit-user-select: none !important;
        }
        .site-logo-link * {
            pointer-events: none !important;
        }
        .site-logo-shell {
            display: inline-flex !important;
            align-items: center !important;
            padding: 0 !important;
            border-radius: 0 !important;
            overflow: visible !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        body.theme-dark .site-logo-shell {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .site-logo-wordmark {
            height: 40px !important;
            width: auto !important;
            display: block !important;
            object-fit: contain !important;
            object-position: left center !important;
            transform: scale(1.0) !important;
            transform-origin: left center !important;
        }
        body.theme-dark .site-logo-wordmark {
            filter: brightness(1.48) saturate(1.18) contrast(1.08) drop-shadow(0 0 2px rgba(56,189,248,0.25)) !important;
        }
        .site-nav-shell {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 12px !important;
            width: 100% !important;
            min-width: 0 !important;
        }
        .site-nav-left {
            display: flex !important;
            align-items: center !important;
            min-width: 0 !important;
            flex-shrink: 0 !important;
            margin-right: auto !important;
        }
        .site-nav-right {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
        }
        .site-nav {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 18px !important;
            flex-wrap: nowrap !important;
            overflow: visible !important;
            white-space: nowrap !important;
            min-width: 0 !important;
        }
        .site-user-section {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            width: 100% !important;
            overflow: visible !important;
        }
        .site-nav-item {
            position: relative !important;
            display: inline-flex !important;
            align-items: center !important;
            padding: 6px 8px !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            color: var(--text-secondary) !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            text-decoration: none !important;
            transition: color 0.16s ease !important;
        }
        .site-nav-item:hover,
        .site-nav-item:focus-visible {
            color: __NAV_ACTIVE_COLOR__ !important;
        }
        .site-nav-item.site-nav-item-active {
            color: __NAV_ACTIVE_COLOR__ !important;
            font-weight: 600 !important;
        }
        .site-nav-item.site-nav-item-active::after {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            right: 0 !important;
            bottom: -8px !important;
            height: 2px !important;
            border-radius: 999px !important;
            background: __NAV_ACTIVE_COLOR__ !important;
        }
        .site-nav-item-signin {
            padding: 6px 12px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            line-height: 1.1 !important;
        }
        .site-user-dropdown {
            position: relative !important;
        }
        .site-user-dropdown summary {
            list-style: none !important;
        }
        .site-user-dropdown summary::-webkit-details-marker {
            display: none !important;
        }
        .site-user-trigger {
            display: inline-flex !important;
            align-items: center !important;
            gap: 8px !important;
            height: 38px !important;
            padding: 0 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.38) !important;
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.35) !important;
            color: var(--text-secondary) !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            max-width: 190px !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        body.theme-dark .site-user-trigger {
            background: rgba(15, 23, 42, 0.35) !important;
        }
        .site-user-caret {
            opacity: 0.75 !important;
            font-size: 0.9rem !important;
            line-height: 1 !important;
        }
        .site-user-dropdown[open] .site-user-caret {
            transform: rotate(180deg) !important;
        }
        .site-user-panel {
            position: absolute !important;
            top: calc(100% + 8px) !important;
            left: 0 !important;
            min-width: 190px !important;
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.16) !important;
            overflow: hidden !important;
            z-index: 1400 !important;
        }
        .site-user-item {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 10px 14px !important;
            color: var(--text-secondary) !important;
            text-decoration: none !important;
            font-size: 0.92rem !important;
            border-bottom: 1px solid var(--border-light) !important;
        }
        .site-user-item:last-child {
            border-bottom: none !important;
        }
        .site-user-item:hover,
        .site-user-item:focus-visible {
            background: rgba(148, 163, 184, 0.12) !important;
            color: var(--text-primary) !important;
        }
        .site-user-item-icon {
            flex-shrink: 0 !important;
            width: 15px !important;
            height: 15px !important;
            opacity: 0.75 !important;
        }
        .site-user-item:hover .site-user-item-icon,
        .site-user-item:focus-visible .site-user-item-icon {
            opacity: 1 !important;
        }
        .site-user-item-logout {
            color: #ef4444 !important;
            font-weight: 600 !important;
        }
        .site-user-item-logout .site-user-item-icon {
            opacity: 0.85 !important;
        }
        .theme-toggle-gap {
            display: none !important;
        }
        .st-key-theme_toggle_header {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
        }
        .st-key-theme_toggle_header button,
        .st-key-theme_toggle_header button[data-testid="baseButton-secondary"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            min-height: 38px !important;
            height: 38px !important;
            min-width: 128px !important;
            width: 128px !important;
            padding: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid __TOGGLE_BTN_BORDER__ !important;
            border-color: __TOGGLE_BTN_BORDER__ !important;
            outline: none !important;
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
            border-radius: 10px !important;
            cursor: pointer !important;
            transition: background 0.18s ease, border-color 0.18s ease !important;
            color: __TOGGLE_ICON_COLOR__ !important;
            font-size: 1.22rem !important;
            line-height: 1 !important;
        }
        .st-key-theme_toggle_header button:hover,
        .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:hover {
            background: __TOGGLE_BTN_BG__ !important;
            background-color: __TOGGLE_BTN_BG__ !important;
            border-color: __TOGGLE_BTN_BORDER__ !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            min-width: 0 !important;
            min-height: 0 !important;
            width: auto !important;
            height: auto !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"] *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div > div * {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            transition: none !important;
            display: inline !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active *,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover > div > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus > div > div,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active > div > div {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: inherit !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button::before,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button::after,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]::before,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]::after {
            content: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button:active,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header button[data-testid="baseButton-secondary"]:active {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid __TOGGLE_BTN_BORDER__ !important;
            border-color: __TOGGLE_BTN_BORDER__ !important;
            outline: none !important;
            box-shadow: none !important;
            background: __TOGGLE_BTN_BG__ !important;
            background-color: __TOGGLE_BTN_BG__ !important;
            background-image: none !important;
            color: __TOGGLE_ICON_COLOR__ !important;
            border-radius: 10px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:hover,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:focus,
        [data-testid="stAppViewContainer"] .st-key-theme_toggle_header [data-baseweb="button"]:active {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .compare-section-shell {
            position: relative !important;
            margin-top: 32px !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stAppViewContainer"] .st-key-compare_section_shell {
            margin-top: 0 !important;
            padding: 28px 26px !important;
            border-radius: 18px !important;
            border: 1px solid var(--border-color) !important;
            background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
            box-shadow: 0 12px 24px var(--shadow) !important;
        }
        .compare-section-title {
            margin: 0 0 8px 0 !important;
            font-size: 3rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            text-align: center !important;
            line-height: 1.05 !important;
        }
        .compare-section-subtitle {
            margin: 0 auto 20px auto !important;
            color: var(--text-secondary) !important;
            font-size: 1.05rem !important;
            line-height: 1.45 !important;
            text-align: center !important;
            max-width: none !important;
            white-space: nowrap !important;
        }
        .compare-mode-badge {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-bottom: 10px !important;
            padding: 6px 10px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(37, 99, 235, 0.35) !important;
            background: rgba(37, 99, 235, 0.1) !important;
            color: #1d4ed8 !important;
            font-size: 0.83rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
        }
        .compare-results-title {
            margin-top: 14px !important;
            margin-bottom: 8px !important;
            font-size: 1.02rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }
        .st-key-compare_form_box,
        .st-key-upload_guest_box {
            margin-top: 14px !important;
            margin-bottom: 12px !important;
            padding: 20px 18px 16px 18px !important;
            border-radius: 14px !important;
            border: 1px solid __COMPARE_BOX_BORDER__ !important;
            background: __COMPARE_BOX_BG__ !important;
            box-shadow: __COMPARE_BOX_SHADOW__ !important;
        }
        .guest-auth-shell {
            text-align: center !important;
            padding: 1.25rem 0.75rem !important;
        }
        .guest-auth-icon {
            width: 62px !important;
            height: 62px !important;
            margin: 0 auto 0.85rem auto !important;
            border-radius: 999px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1.6rem !important;
            background: __GUEST_ICON_BG__ !important;
            color: __GUEST_ICON_COLOR__ !important;
            border: 1px solid rgba(59, 130, 246, 0.22) !important;
        }
        .guest-auth-title {
            margin: 0 0 0.5rem 0 !important;
            font-size: 1.9rem !important;
            line-height: 1.12 !important;
            font-weight: 800 !important;
            color: __GUEST_TITLE_COLOR__ !important;
        }
        .guest-auth-copy {
            margin: 0 auto 1.25rem auto !important;
            max-width: 720px !important;
            font-size: 1.02rem !important;
            line-height: 1.5 !important;
            color: __GUEST_BODY_COLOR__ !important;
        }
        .guest-auth-cta {
            display: inline-block !important;
            padding: 0.65rem 2rem !important;
            border-radius: 0.65rem !important;
            text-decoration: none !important;
            font-weight: 800 !important;
            font-size: 1.04rem !important;
            background: __GUEST_CTA_BG__ !important;
            color: __GUEST_CTA_TEXT__ !important;
            border: 1px solid __GUEST_CTA_BORDER__ !important;
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.20) !important;
            transition: transform 0.16s ease, box-shadow 0.16s ease !important;
        }
        .guest-auth-cta:hover,
        .guest-auth-cta:focus-visible {
            transform: translateY(-1px) !important;
            box-shadow: 0 14px 24px rgba(37, 99, 235, 0.28) !important;
            color: __GUEST_CTA_TEXT__ !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] {
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] [data-testid="stVerticalBlock"] > div {
            margin-bottom: 12px !important;
        }
        .st-key-compare_form_box .stTextArea label,
        .st-key-compare_form_box .stFileUploader label {
            color: __COMPARE_LABEL_COLOR__ !important;
            font-weight: 700 !important;
        }
        .st-key-compare_form_box .stTextArea textarea {
            background: __COMPARE_TEXTAREA_BG__ !important;
            border: 1px solid __COMPARE_TEXTAREA_BORDER__ !important;
            color: __COMPARE_TEXTAREA_TEXT__ !important;
            border-radius: 10px !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stTextArea textarea:hover,
        .stForm .stTextArea textarea:focus,
        .stForm .stTextArea > div:hover textarea,
        .stForm .stTextArea > div:focus-within textarea {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box .stTextArea textarea::placeholder {
            color: __COMPARE_PLACEHOLDER__ !important;
        }
        .st-key-compare_form_box .stTextArea > div:hover textarea,
        .st-key-compare_form_box .stTextArea > div:focus-within textarea,
        .st-key-compare_form_box .stTextArea textarea:hover,
        .st-key-compare_form_box .stTextArea textarea:focus {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"] {
            border-radius: 10px !important;
            border: 1px solid __COMPARE_TEXTAREA_BORDER__ !important;
            background: __COMPARE_DROPZONE_BG__ !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stFileUploader [data-testid="stFileUploaderDropzone"]:hover,
        .stForm .stFileUploader [data-testid="stFileUploaderDropzone"]:focus-within {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"]:hover,
        .st-key-compare_form_box .stFileUploader [data-testid="stFileUploaderDropzone"]:focus-within {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box .stFileUploader button,
        .st-key-compare_form_box .stFileUploader [data-baseweb="button"] {
            min-width: 170px !important;
            border-radius: 10px !important;
            border: 1px solid __COMPARE_BUTTON_BORDER__ !important;
            background: __COMPARE_BUTTON_BG__ !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        }
        .stForm .stFileUploader button:hover,
        .stForm .stFileUploader [data-baseweb="button"]:hover {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button {
            min-height: 46px !important;
            border-radius: 10px !important;
            border: 1px solid __COMPARE_BUTTON_BORDER__ !important;
            background: __COMPARE_BUTTON_BG__ !important;
            background-image: none !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
            font-weight: 700 !important;
            transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
            outline: none !important;
            box-shadow: none !important;
            filter: none !important;
            transform: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button:hover,
        .stForm [data-testid="stFormSubmitButton"] button:focus-visible,
        .stForm [data-testid="stFormSubmitButton"] button:focus,
        .stForm [data-testid="stFormSubmitButton"] button:active {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            outline: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"],
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:hover,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus-visible,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]:active {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button *,
        .stForm [data-testid="stFormSubmitButton"] button > div,
        .stForm [data-testid="stFormSubmitButton"] button > div > p,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] *,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"],
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:focus-within,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:focus-within,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:focus-within {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button *,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button > div > p,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] *,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"] > div > div {
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            border: none !important;
        }
        .st-key-compare_form_box .stFileUploader button:hover,
        .st-key-compare_form_box .stFileUploader [data-baseweb="button"]:hover {
            background: __COMPARE_HOVER_BG__ !important;
            border-color: __COMPARE_HOVER_BORDER__ !important;
            box-shadow: __COMPARE_HOVER_SHADOW__ !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:active {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            outline: none !important;
            filter: none !important;
            transform: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"],
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:focus-visible,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]:active {
            background: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"]:has(button:active),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div:has(button:active),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:hover),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:focus-visible),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:focus),
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] > div > div:has(button:active) {
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button::before,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button::after,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]::before,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] [data-baseweb="button"]::after {
            content: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        /* Keep upload/compare submit buttons identical to uploader button hover and remove inner hover blocks. */
        .stForm [data-testid="stFormSubmitButton"] button,
        .st-key-upload_form [data-testid="stFormSubmitButton"] button,
        .st-key-comparison_form [data-testid="stFormSubmitButton"] button,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button {
            background: __COMPARE_BUTTON_BG__ !important;
            background-color: __COMPARE_BUTTON_BG__ !important;
            border: 1px solid __COMPARE_BUTTON_BORDER__ !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
            box-shadow: none !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button:hover,
        .stForm [data-testid="stFormSubmitButton"] button:focus,
        .stForm [data-testid="stFormSubmitButton"] button:focus-visible,
        .stForm [data-testid="stFormSubmitButton"] button:active,
        .st-key-upload_form [data-testid="stFormSubmitButton"] button:hover,
        .st-key-upload_form [data-testid="stFormSubmitButton"] button:focus,
        .st-key-upload_form [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-upload_form [data-testid="stFormSubmitButton"] button:active,
        .st-key-comparison_form [data-testid="stFormSubmitButton"] button:hover,
        .st-key-comparison_form [data-testid="stFormSubmitButton"] button:focus,
        .st-key-comparison_form [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-comparison_form [data-testid="stFormSubmitButton"] button:active,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:hover,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-compare_form_box [data-testid="stFormSubmitButton"] button:active {
            background: var(--excelcv-uniform-hover-bg) !important;
            background-color: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
            color: __COMPARE_BUTTON_TEXT__ !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button *,
        .stForm [data-testid="stFormSubmitButton"] button > div,
        .stForm [data-testid="stFormSubmitButton"] button > div > div,
        .stForm [data-testid="stFormSubmitButton"] button > div > p,
        .stForm [data-testid="stFormSubmitButton"] button span,
        .stForm [data-testid="stFormSubmitButton"] button p,
        .stForm [data-testid="stFormSubmitButton"] button:hover *,
        .stForm [data-testid="stFormSubmitButton"] button:hover > div,
        .stForm [data-testid="stFormSubmitButton"] button:hover > div > div,
        .stForm [data-testid="stFormSubmitButton"] button:hover > div > p,
        .stForm [data-testid="stFormSubmitButton"] button:focus *,
        .stForm [data-testid="stFormSubmitButton"] button:focus-visible *,
        .stForm [data-testid="stFormSubmitButton"] button:active * {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            color: inherit !important;
        }
        .stForm [data-testid="stFormSubmitButton"] button::before,
        .stForm [data-testid="stFormSubmitButton"] button::after,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]::before,
        .stForm [data-testid="stFormSubmitButton"] [data-baseweb="button"]::after {
            content: none !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .compare-upload-icon {
            width: 74px !important;
            height: 74px !important;
            margin: 0 auto 12px auto !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 2rem !important;
            color: #ffffff !important;
            background: linear-gradient(135deg, #0f6ac9, #13c0b0) !important;
        }
        .compare-upload-title {
            text-align: center !important;
            margin: 0 0 6px 0 !important;
            font-size: 1.8rem !important;
            line-height: 1.08 !important;
            color: __COMPARE_LABEL_COLOR__ !important;
            font-weight: 800 !important;
        }
        .compare-upload-copy {
            text-align: center !important;
            margin: 0 0 16px 0 !important;
            color: __COMPARE_PLACEHOLDER__ !important;
            font-size: 1.0rem !important;
        }
        .compare-next-shell {
            max-width: none !important;
            margin: 14px 0 0 0 !important;
            padding: 18px 18px 14px 18px !important;
            border-radius: 14px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
            box-shadow: 0 8px 18px var(--shadow) !important;
        }
        .compare-next-title {
            margin: 0 0 12px 0 !important;
            font-size: 2rem !important;
            color: var(--text-primary) !important;
            font-weight: 800 !important;
            text-align: center !important;
        }
        .compare-next-list {
            margin: 0 !important;
            padding-left: 0 !important;
            list-style: none !important;
        }
        .compare-next-list li {
            position: relative !important;
            padding-left: 30px !important;
            margin-bottom: 10px !important;
            color: var(--text-secondary) !important;
            font-size: 1.01rem !important;
            line-height: 1.45 !important;
        }
        .compare-next-list li::before {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            top: 0.58em !important;
            width: 12px !important;
            height: 12px !important;
            border-radius: 999px !important;
            border: 3px solid #0ea5b7 !important;
            transform: translateY(-50%) !important;
            box-sizing: border-box !important;
        }
        [data-testid="stAppViewContainer"] .landing-extended {
            margin-top: 50px !important;
            margin-bottom: 50px !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 50px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-section {
            background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary)) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 18px !important;
            padding: 28px 26px !important;
            box-shadow: 0 12px 24px var(--shadow) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-head {
            text-align: center !important;
            margin-bottom: 16px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-tag {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 6px 14px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(37, 99, 235, 0.25) !important;
            background: rgba(37, 99, 235, 0.08) !important;
            color: #1d4ed8 !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.01em !important;
            text-transform: none !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-title {
            margin: 10px 0 8px 0 !important;
            color: var(--text-primary) !important;
            font-size: clamp(1.55rem, 3vw, 2.6rem) !important;
            line-height: 1.18 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-subtitle {
            margin: 0 auto !important;
            max-width: 760px !important;
            color: var(--text-secondary) !important;
            font-size: 1.03rem !important;
            line-height: 1.55 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-grid {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 14px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card {
            border: 1px solid var(--border-color) !important;
            border-radius: 14px !important;
            background: var(--bg-card) !important;
            padding: 18px !important;
            box-shadow: 0 8px 18px var(--shadow) !important;
            text-align: left !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card h4 {
            margin: 0 0 8px 0 !important;
            color: var(--text-primary) !important;
            font-size: 1.14rem !important;
            line-height: 1.28 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card p {
            margin: 0 !important;
            color: var(--text-secondary) !important;
            font-size: 0.99rem !important;
            line-height: 1.55 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-icon {
            width: 42px !important;
            height: 42px !important;
            border-radius: 999px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-bottom: 10px !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta {
            border-radius: 20px !important;
            border: 1px solid rgba(14, 116, 144, 0.25) !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
            padding: 34px 20px !important;
            text-align: center !important;
            box-shadow: 0 14px 28px rgba(15, 106, 201, 0.24) !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta h3 {
            margin: 0 0 8px 0 !important;
            color: #ffffff !important;
            font-size: clamp(1.45rem, 2.4vw, 2.2rem) !important;
            line-height: 1.2 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta p {
            margin: 0 auto 14px auto !important;
            max-width: 760px !important;
            color: rgba(255, 255, 255, 0.94) !important;
            font-size: 1.05rem !important;
            line-height: 1.5 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta-pills {
            display: flex !important;
            justify-content: center !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-cta-pills span {
            display: inline-flex !important;
            align-items: center !important;
            padding: 7px 12px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(255, 255, 255, 0.32) !important;
            background: rgba(255, 255, 255, 0.12) !important;
            color: #ffffff !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card .story-tag {
            display: inline-flex !important;
            align-items: center !important;
            margin: 0 0 10px 0 !important;
            padding: 4px 9px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(16, 185, 129, 0.25) !important;
            background: rgba(16, 185, 129, 0.12) !important;
            color: #0f766e !important;
            font-size: 0.83rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card h5 {
            margin: 12px 0 2px 0 !important;
            color: var(--text-primary) !important;
            font-size: 1.06rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card span {
            color: var(--text-secondary) !important;
            font-size: 0.92rem !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-footnote {
            text-align: center !important;
            color: var(--text-secondary) !important;
            font-size: 0.94rem !important;
            padding: 2px 0 10px 0 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-tag {
            color: #7dd3fc !important;
            border-color: rgba(125, 211, 252, 0.28) !important;
            background: rgba(14, 116, 144, 0.22) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-card .story-tag {
            color: #86efac !important;
            border-color: rgba(134, 239, 172, 0.3) !important;
            background: rgba(22, 163, 74, 0.18) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-clean-cta {
            background: linear-gradient(135deg, rgba(15, 106, 201, 0.72), rgba(20, 184, 166, 0.66)) !important;
            box-shadow: 0 18px 32px rgba(2, 8, 23, 0.36) !important;
        }
        /* Stable preview card contrast for both theme modes */
        [data-testid="stAppViewContainer"] .upload-preview {
            background: __PREVIEW_SHELL_BG__ !important;
            border-color: __PREVIEW_SHELL_BORDER__ !important;
        }
        [data-testid="stAppViewContainer"] .upload-preview .preview-card {
            background: __PREVIEW_CARD_BG__ !important;
            border-color: __PREVIEW_CARD_BORDER__ !important;
        }
        [data-testid="stAppViewContainer"] .upload-preview .preview-card,
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .text-primary,
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .text-secondary,
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .list-row span {
            color: __PREVIEW_TEXT__ !important;
            opacity: 1 !important;
        }
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .text-muted {
            color: __PREVIEW_MUTED__ !important;
            opacity: 1 !important;
        }
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .pill {
            background: __PREVIEW_CHIP_BG__ !important;
        }
        [data-testid="stAppViewContainer"] .upload-preview .preview-card .progress-track {
            background: __PREVIEW_TRACK_BG__ !important;
        }
        .site-header-rule {
            display: none !important;
        }
        #excelcv-fixed-header-spacer {
            display: block !important;
            width: 100% !important;
            height: 66px !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }
        /* CV Builder rail safety: prevent style controls from being clipped by global overrides. */
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-left-scroll-native {
            height: var(--cvb-native-panel-h) !important;
            max-height: var(--cvb-native-panel-h) !important;
            overflow-y: scroll !important;
            overflow-x: hidden !important;
            scrollbar-gutter: auto !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"],
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-row-native > div > [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            column-gap: 0 !important;
            row-gap: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"],
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-row-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"] {
            min-height: 0 !important;
            overflow: visible !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-style-native .cvb-style-label,
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-style-native .cvb-label {
            margin-top: 14px !important;
            margin-bottom: 10px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-style-native .cvb-style-label-accent {
            margin-bottom: 12px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-style-native .stSlider {
            margin-bottom: 18px !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-style-native .stToggle {
            margin-top: 12px !important;
        }

        @media (max-width: 1100px) {
            [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) {
                width: calc(100vw - 34px) !important;
                padding: 0 10px !important;
            }
            .site-logo-wordmark {
                height: 36px !important;
                transform: scale(1.0) !important;
            }
            .site-nav-item {
                font-size: 14px !important;
            }
            .site-nav {
                gap: 12px !important;
            }
            .site-user-trigger {
                max-width: 132px !important;
                font-size: 0.86rem !important;
            }
            .site-nav-shell {
                gap: 6px !important;
            }
            .site-nav-item {
                font-size: 13.5px !important;
            }
            .compare-section-subtitle {
                white-space: normal !important;
            }
            .compare-section-title {
                font-size: 2.3rem !important;
            }
            .compare-next-title {
                font-size: 1.45rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }

        @media (max-width: 820px) {
            [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) {
                width: calc(100vw - 20px) !important;
                border-radius: 12px !important;
            }
            .site-nav,
            .site-nav-left {
                display: none !important;
            }
            .site-logo-wordmark {
                height: 32px !important;
                transform: scale(1.0) !important;
            }
            #excelcv-fixed-header-spacer {
                height: 60px !important;
            }
            .compare-section-shell {
                margin-top: 16px !important;
                padding: 0 !important;
            }
            [data-testid="stAppViewContainer"] .st-key-compare_section_shell {
                margin-top: 0 !important;
                padding: 18px 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-extended {
                margin-top: 30px !important;
                margin-bottom: 30px !important;
                gap: 30px !important;
            }
            .compare-section-title {
                font-size: 1.9rem !important;
            }
            .compare-upload-title {
                font-size: 1.4rem !important;
            }
            .compare-next-title {
                font-size: 1.28rem !important;
            }
            .st-key-compare_form_box,
            .st-key-upload_guest_box {
                padding: 14px 12px 12px 12px !important;
            }
            .compare-next-shell {
                padding: 16px 14px 12px 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-section {
                padding: 18px 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-grid {
                grid-template-columns: 1fr !important;
                gap: 10px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-title {
                font-size: 1.42rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-subtitle {
                font-size: 0.96rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-card {
                padding: 14px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-cta {
                padding: 24px 12px !important;
            }
            [data-testid="stAppViewContainer"] .landing-clean-cta p {
                font-size: 0.96rem !important;
            }
        }
        </style>
        """
    css = (
        css.replace("__HEADER_BG__", header_bg)
        .replace("__TOGGLE_BTN_BG__", toggle_btn_bg)
        .replace("__TOGGLE_BTN_BORDER__", toggle_btn_border)
        .replace("__TOGGLE_ICON_COLOR__", toggle_icon_color)
        .replace("__NAV_ACTIVE_COLOR__", nav_active_color)
        .replace("__HEADER_FILTER__", header_filter)
        .replace("__HEADER_SHADOW__", header_shadow)
        .replace("__COMPARE_BOX_BORDER__", compare_box_border)
        .replace("__COMPARE_BOX_BG__", compare_box_bg)
        .replace("__COMPARE_BOX_SHADOW__", compare_box_shadow)
        .replace("__COMPARE_LABEL_COLOR__", compare_label_color)
        .replace("__COMPARE_TEXTAREA_BG__", compare_textarea_bg)
        .replace("__COMPARE_TEXTAREA_BORDER__", compare_textarea_border)
        .replace("__COMPARE_TEXTAREA_TEXT__", compare_textarea_text)
        .replace("__COMPARE_PLACEHOLDER__", compare_placeholder)
        .replace("__COMPARE_DROPZONE_BG__", compare_dropzone_bg)
        .replace("__COMPARE_BUTTON_BG__", compare_button_bg)
        .replace("__COMPARE_BUTTON_TEXT__", compare_button_text)
        .replace("__COMPARE_BUTTON_BORDER__", compare_button_border)
        .replace("__COMPARE_HOVER_BG__", compare_hover_bg)
        .replace("__COMPARE_HOVER_BORDER__", compare_hover_border)
        .replace("__COMPARE_HOVER_SHADOW__", compare_hover_shadow)
        .replace("__GUEST_TITLE_COLOR__", guest_title_color)
        .replace("__GUEST_BODY_COLOR__", guest_body_color)
        .replace("__GUEST_ICON_BG__", guest_icon_bg)
        .replace("__GUEST_ICON_COLOR__", guest_icon_color)
        .replace("__GUEST_CTA_BG__", guest_cta_bg)
        .replace("__GUEST_CTA_TEXT__", guest_cta_text)
        .replace("__GUEST_CTA_BORDER__", guest_cta_border)
        .replace("__PREVIEW_SHELL_BG__", preview_shell_bg)
        .replace("__PREVIEW_SHELL_BORDER__", preview_shell_border)
        .replace("__PREVIEW_CARD_BG__", preview_card_bg)
        .replace("__PREVIEW_CARD_BORDER__", preview_card_border)
        .replace("__PREVIEW_TEXT__", preview_text)
        .replace("__PREVIEW_MUTED__", preview_muted)
        .replace("__PREVIEW_CHIP_BG__", preview_chip_bg)
        .replace("__PREVIEW_TRACK_BG__", preview_track_bg)
    )
    st.markdown(css, unsafe_allow_html=True)


def inject_header_layout_override() -> None:
    """Apply final-pass header layout overrides to prevent internal nav scrolling."""
    components.html(
        """
        <script>
        (function() {
            var w = window.parent && window.parent !== window ? window.parent : window;
            var doc = w.document;
            var styleId = "excelcv-header-layout-override";
            var css = `
[data-testid="stAppViewContainer"] .site-brand{
  max-height:40px !important; overflow:hidden !important;
}
[data-testid="stAppViewContainer"] .site-brand img{
  height:40px !important; max-height:40px !important; width:auto !important;
}
[data-testid="stAppViewContainer"] .site-nav-shell{
  display:flex !important; align-items:center !important; justify-content:flex-end !important;
  width:100% !important; min-width:0 !important; gap:10px !important;
}
[data-testid="stAppViewContainer"] .site-nav-left{
  margin-right:auto !important; flex-shrink:0 !important; min-width:0 !important;
}
[data-testid="stAppViewContainer"] .site-nav-right{
  display:flex !important; justify-content:flex-end !important; align-items:center !important;
  flex:1 1 auto !important; min-width:0 !important; overflow:visible !important;
}
[data-testid="stAppViewContainer"] .site-nav{
  display:flex !important; justify-content:flex-start !important; align-items:center !important;
  gap:18px !important; flex-wrap:nowrap !important; overflow:visible !important;
  white-space:nowrap !important; min-width:0 !important; max-width:none !important;
  scrollbar-width:none !important; -ms-overflow-style:none !important;
}
[data-testid="stAppViewContainer"] .site-nav::-webkit-scrollbar{display:none !important;}
[data-testid="stAppViewContainer"] .site-nav-item{
  flex:0 0 auto !important;
  font-size:15px !important;
  padding:6px 8px !important;
}
[data-testid="stAppViewContainer"] .site-user-section{
  display:flex !important; align-items:center !important; justify-content:flex-end !important;
  width:100% !important; overflow:visible !important;
}
[data-testid="stAppViewContainer"] .site-user-trigger{
  display:inline-flex !important; align-items:center !important; gap:8px !important;
  height:38px !important; padding:0 10px !important; border-radius:10px !important;
  max-width:170px !important; overflow:hidden !important; text-overflow:ellipsis !important;
}
[data-testid="stAppViewContainer"] .site-user-panel{
  right:0 !important; left:auto !important; z-index:1500 !important;
}
[data-testid="stAppViewContainer"] .site-nav-item-signin{
  padding:6px 12px !important; border-radius:10px !important; font-weight:600 !important;
  background:#3b82f6 !important; color:#fff !important; border-color:#3b82f6 !important;
}
@media (max-width: 1100px){
  [data-testid="stAppViewContainer"] .site-nav{gap:12px !important;}
  [data-testid="stAppViewContainer"] .site-nav-item{font-size:13.5px !important;}
  [data-testid="stAppViewContainer"] .site-user-trigger{max-width:130px !important;}
}
@media (max-width: 820px){
  [data-testid="stAppViewContainer"] .site-nav{display:none !important;}
}
`;
            var existing = doc.getElementById(styleId);
            if (existing) {
                existing.textContent = css;
            } else {
                var s = doc.createElement("style");
                s.id = styleId;
                s.textContent = css;
                (doc.head || doc.documentElement).appendChild(s);
            }
        })();
        </script>
        """,
        height=0,
    )


def inject_dropdown_outside_click() -> None:
    """Close the user dropdown panel when the user clicks anywhere outside it."""
    components.html(
        """
        <script>
        (function() {
            var w = window.parent && window.parent !== window ? window.parent : window;
            var doc = w.document;
            var HANDLER_KEY = "__excelcv_dropdown_outside_click__";
            if (doc[HANDLER_KEY]) {
                doc.removeEventListener("click", doc[HANDLER_KEY], true);
            }
            function handleOutsideClick(e) {
                var dropdown = doc.querySelector(".site-user-dropdown");
                if (!dropdown || !dropdown.hasAttribute("open")) return;
                if (!dropdown.contains(e.target)) {
                    dropdown.removeAttribute("open");
                }
            }
            doc[HANDLER_KEY] = handleOutsideClick;
            doc.addEventListener("click", handleOutsideClick, true);
        })();
        </script>
        """,
        height=0,
    )


def inject_fixed_top_bar() -> None:
    """Fix the contained top bar to viewport with a dynamic spacer."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;
            var HEADER_SELECTOR = '[data-testid="stHorizontalBlock"].header-bar:has(.site-brand), [data-testid="stHorizontalBlock"]:has(.site-brand)';
            var SPACER_ID = 'excelcv-fixed-header-spacer';
            var MAX_WIDTH = 1800;

            function getHeader() {
                var header = doc.querySelector(HEADER_SELECTOR);
                if (!header) return null;
                var rect = header.getBoundingClientRect();
                if (!rect || rect.width < 40 || rect.height < 24) return null;
                return header;
            }

            function viewportWidth() {
                return Math.max(
                    320,
                    (doc.documentElement && doc.documentElement.clientWidth) || target.innerWidth || 1200
                );
            }

            function computeTop(vw) {
                // Keep the top bar flush to the top edge (no visible upper gap).
                return 0;
            }

            function computeSidePad(vw) {
                if (vw <= 820) return 20;
                if (vw <= 1100) return 34;
                return 90;
            }

            function ensureSpacer(header) {
                var spacer = doc.getElementById(SPACER_ID);
                if (!spacer) {
                    spacer = doc.createElement('div');
                    spacer.id = SPACER_ID;
                }
                if (header.parentNode && spacer.nextSibling !== header) {
                    header.parentNode.insertBefore(spacer, header);
                }
                return spacer;
            }

            function applyFixedBar() {
                var header = getHeader();
                if (!header) return;
                header.classList.add('header-bar');

                var vw = viewportWidth();
                var top = computeTop(vw);
                var sidePad = computeSidePad(vw);
                var width = Math.max(320, Math.min(MAX_WIDTH, vw - sidePad));
                var spacer = ensureSpacer(header);

                header.style.position = 'fixed';
                header.style.top = top + 'px';
                header.style.left = '50%';
                header.style.transform = 'translateX(-50%)';
                header.style.width = width + 'px';
                header.style.zIndex = '1300';
                header.style.margin = '0';
                header.style.border = 'none';
                header.style.outline = 'none';

                var headerHeight = Math.max(
                    60,
                    Math.ceil(header.getBoundingClientRect().height || header.offsetHeight || 78)
                );
                spacer.style.display = 'block';
                spacer.style.width = '100%';
                spacer.style.height = (top + headerHeight) + 'px';
                spacer.style.margin = '0';
                spacer.style.padding = '0';
                spacer.style.pointerEvents = 'none';
            }

            function scheduleApply() {
                applyFixedBar();
                target.requestAnimationFrame(applyFixedBar);
                setTimeout(applyFixedBar, 60);
                setTimeout(applyFixedBar, 220);
            }

            scheduleApply();

            if (!target.__excelcvFixedHeaderResizeBound) {
                target.__excelcvFixedHeaderResizeBound = true;
                target.addEventListener('resize', scheduleApply);
            }

            if (target.__excelcvFixedHeaderObserver) {
                target.__excelcvFixedHeaderObserver.disconnect();
            }
            target.__excelcvFixedHeaderObserver = new MutationObserver(function() {
                scheduleApply();
            });
            target.__excelcvFixedHeaderObserver.observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
    )


def inject_footer_full_width() -> None:
    """Force the site footer band to span the full viewport width.

    Streamlit's stAppViewContainer has overflow-x:hidden which clips CSS
    translateX breakouts. This JS walks up from the footer element and
    sets overflow:visible on each ancestor so the 100vw width is visible.
    """
    components.html(
        """
        <script>
        (function() {
            var w = window.parent && window.parent !== window ? window.parent : window;
            var doc = w.document;

            function applyFullWidth() {
                var footer = doc.querySelector('.site-footer-band');
                if (!footer) return;

                // Walk up and unlock overflow on every ancestor up to body
                var el = footer.parentElement;
                while (el && el !== doc.body) {
                    var cs = w.getComputedStyle(el);
                    if (cs.overflowX === 'hidden' || cs.overflow === 'hidden') {
                        el.style.setProperty('overflow-x', 'visible', 'important');
                    }
                    el.style.setProperty('overflow', 'visible', 'important');
                    el = el.parentElement;
                }

                // Apply full-width to the stElementContainer holding the footer
                var container = footer.closest('[data-testid="stElementContainer"]');
                if (container) {
                    container.style.setProperty('width', '100vw', 'important');
                    container.style.setProperty('position', 'relative', 'important');
                    container.style.setProperty('left', '50%', 'important');
                    container.style.setProperty('transform', 'translateX(-50%)', 'important');
                    container.style.setProperty('overflow', 'visible', 'important');
                }
            }

            // Run immediately, after paint, and watch for DOM changes
            applyFullWidth();
            w.requestAnimationFrame(applyFullWidth);
            setTimeout(applyFullWidth, 150);

            if (!w.__excelcvFooterObserver) {
                w.__excelcvFooterObserver = new MutationObserver(applyFullWidth);
                w.__excelcvFooterObserver.observe(doc.body, { childList: true, subtree: true });
            }
        })();
        </script>
        """,
        height=0,
    )


def inject_logo_home_click_behavior() -> None:
    """Keep logo home navigation reliable across Streamlit reruns/reloads."""
    components.html(
        """
        <script>
        (function() {
            var target = window.parent && window.parent !== window ? window.parent : window;
            var doc = target.document;

            function buildHomeHref() {
                var current;
                try {
                    current = new URL(target.location.href);
                } catch (e) {
                    return '/?page=upload&_clear=1&_home=' + Date.now() + '&_reload=' + Date.now();
                }
                current.searchParams.set('page', 'upload');
                current.searchParams.set('_home', String(Date.now()));
                current.searchParams.set('_reload', String(Date.now()));
                current.searchParams.set('_clear', '1');
                current.searchParams.delete('rid');
                return current.pathname + '?' + current.searchParams.toString();
            }

            function bindLogos() {
                var logos = doc.querySelectorAll('.site-logo-link');
                logos.forEach(function(logo) {
                    if (logo.getAttribute('data-logo-home-bound') === '1') {
                        var cleanLogo = logo.cloneNode(true);
                        logo.parentNode.replaceChild(cleanLogo, logo);
                        logo = cleanLogo;
                    }
                    logo.setAttribute('data-logo-home-bound', '2');
                    logo.setAttribute('target', '_self');
                    logo.setAttribute('href', buildHomeHref());
                });
            }

            bindLogos();

            if (target.__excelcvLogoHomeObserver) {
                target.__excelcvLogoHomeObserver.disconnect();
            }
            target.__excelcvLogoHomeObserver = new MutationObserver(function() {
                bindLogos();
            });
            target.__excelcvLogoHomeObserver.observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
    )
