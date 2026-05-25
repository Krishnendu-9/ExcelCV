"""CSS/JS injection helpers: header bar, form spacing, fixed top-bar, logo behaviour."""

import streamlit as st
import streamlit.components.v1 as components


def inject_file_uploader_spacing_css() -> None:
    """Matching outer-box treatment for the "Job description" textarea and the file uploader.

    Both render as a card: 1px border, soft fill, 14px radius, the section label pinned at
    the top of the card, then the input below it.  Scoped via the parent container keys
    (hero card / compare card), which reliably carry st-key-* classes.
    """
    st.markdown(
        """
        <style>
        /* Card box — Job description textarea (light) */
        body .st-key-hero_wrapper .stTextArea,
        body .st-key-hero_wrapper [data-testid="stTextArea"],
        body .st-key-compare_form_box .stTextArea,
        body .st-key-compare_form_box [data-testid="stTextArea"],
        body .st-key-compare_section_shell .stTextArea,
        body .st-key-compare_section_shell [data-testid="stTextArea"] {
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            background: #f9fafb !important;
        }
        body.theme-dark .st-key-hero_wrapper .stTextArea,
        body.theme-dark .st-key-hero_wrapper [data-testid="stTextArea"],
        body.theme-dark .st-key-compare_form_box .stTextArea,
        body.theme-dark .st-key-compare_form_box [data-testid="stTextArea"],
        body.theme-dark .st-key-compare_section_shell .stTextArea,
        body.theme-dark .st-key-compare_section_shell [data-testid="stTextArea"] {
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: #111827 !important;
        }
        /* Shared card layout for BOTH the textarea box and the file-uploader box.
           Scopes: hero_wrapper (analyze CV), compare_form_box (logged-in compare),
           and compare_section_shell (guest compare — JD textarea sits outside the
           logged-in form_box wrapper). */
        body .st-key-hero_wrapper .stTextArea,
        body .st-key-hero_wrapper [data-testid="stTextArea"],
        body .st-key-hero_wrapper .stFileUploader,
        body .st-key-hero_wrapper [data-testid="stFileUploader"],
        body .st-key-compare_form_box .stTextArea,
        body .st-key-compare_form_box [data-testid="stTextArea"],
        body .st-key-compare_form_box .stFileUploader,
        body .st-key-compare_form_box [data-testid="stFileUploader"],
        body .st-key-compare_section_shell .stTextArea,
        body .st-key-compare_section_shell [data-testid="stTextArea"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            justify-content: flex-start !important;
            gap: 8px !important;
            border-radius: 14px !important;
            padding: 16px 18px 18px 18px !important;
            box-sizing: border-box !important;
            overflow: visible !important;
        }
        /* Section labels — pinned to the top of the card, never straddling the border. */
        body .st-key-hero_wrapper .stTextArea > label,
        body .st-key-hero_wrapper .stTextArea label,
        body .st-key-hero_wrapper .stTextArea > div:first-child,
        body .st-key-hero_wrapper .stFileUploader > label,
        body .st-key-hero_wrapper .stFileUploader label,
        body .st-key-hero_wrapper .stFileUploader > div:first-child,
        body .st-key-compare_form_box .stTextArea > label,
        body .st-key-compare_form_box .stTextArea label,
        body .st-key-compare_form_box .stTextArea > div:first-child,
        body .st-key-compare_form_box .stFileUploader > label,
        body .st-key-compare_form_box .stFileUploader label,
        body .st-key-compare_form_box .stFileUploader > div:first-child,
        body .st-key-compare_section_shell .stTextArea > label,
        body .st-key-compare_section_shell .stTextArea label,
        body .st-key-compare_section_shell .stTextArea > div:first-child {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            transform: none !important;
            position: static !important;
            top: auto !important;
            order: -1 !important;
            align-self: stretch !important;
            line-height: 1.25 !important;
            border-bottom: none !important;
        }
        body .st-key-hero_wrapper .stTextArea label p,
        body .st-key-hero_wrapper .stFileUploader label p,
        body .st-key-compare_form_box .stTextArea label p,
        body .st-key-compare_form_box .stFileUploader label p,
        body .st-key-compare_section_shell .stTextArea label p {
            margin: 0 !important;
        }
        /* Even rhythm between the form's stacked widgets (textarea → uploader → button). */
        .st-key-hero_wrapper [data-testid="stForm"] [data-testid="stVerticalBlock"] > div,
        .st-key-compare_form_box [data-testid="stForm"] [data-testid="stVerticalBlock"] > div {
            margin-bottom: 6px !important;
        }
        /* Dropzone sits flush inside its card. */
        .st-key-hero_wrapper [data-testid="stFileUploaderDropzone"],
        .st-key-compare_form_box [data-testid="stFileUploaderDropzone"] {
            margin: 0 !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
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
        "blur(12px) saturate(120%)" if is_dark else "blur(12px) saturate(108%) brightness(1.04)"
    )
    header_shadow = "0 4px 16px rgba(2, 6, 23, 0.20)" if is_dark else "none"
    compare_box_border = "rgba(56, 189, 248, 0.24)" if is_dark else "rgba(148, 163, 184, 0.42)"
    compare_box_bg = (
        "radial-gradient(200px 130px at 78% 10%, rgba(45, 212, 191, 0.09), transparent 70%), "
        "linear-gradient(170deg, rgba(7, 16, 36, 0.82), rgba(2, 8, 24, 0.8))"
        if is_dark
        else "linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.98))"
    )
    compare_box_shadow = (
        "0 12px 24px rgba(2, 6, 23, 0.32)" if is_dark else "0 10px 20px rgba(15, 23, 42, 0.12)"
    )
    compare_label_color = "#e2e8f0" if is_dark else "#1e293b"
    compare_textarea_bg = "rgba(30, 41, 59, 0.62)" if is_dark else "rgba(255, 255, 255, 0.98)"
    compare_textarea_border = (
        "rgba(100, 116, 139, 0.55)" if is_dark else "rgba(148, 163, 184, 0.62)"
    )
    compare_textarea_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_placeholder = "#94a3b8" if is_dark else "#64748b"
    compare_dropzone_bg = "rgba(30, 41, 59, 0.56)" if is_dark else "rgba(248, 250, 252, 0.98)"
    compare_button_bg = "rgba(30, 41, 59, 0.88)" if is_dark else "rgba(226, 232, 240, 0.95)"
    compare_button_text = "#e2e8f0" if is_dark else "#0f172a"
    compare_button_border = "rgba(71, 85, 105, 0.7)" if is_dark else "rgba(148, 163, 184, 0.7)"
    compare_hover_bg = "rgba(37, 99, 235, 0.16)" if is_dark else "rgba(239, 246, 255, 0.98)"
    compare_hover_border = "rgba(56, 189, 248, 0.65)" if is_dark else "rgba(37, 99, 235, 0.62)"
    compare_hover_shadow = (
        "0 0 0 3px rgba(56, 189, 248, 0.14)" if is_dark else "0 0 0 3px rgba(37, 99, 235, 0.14)"
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
            padding: 0 16px 0 0 !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
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
        /* The header bar is position:fixed via JS, so the stElementContainer that
           wraps it should not reserve any space in normal flow. Collapsing this
           wrapper removes the visible gap between the fixed-header spacer and the
           first page content. */
        [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"].header-bar),
        [data-testid="stElementContainer"]:has([data-testid="stHorizontalBlock"].header-bar) {
            margin: 0 !important;
            padding: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            overflow: visible !important;
        }
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) > div:has(.site-brand),
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) [data-testid="stColumn"]:has(.site-brand),
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) [data-testid="column"]:has(.site-brand),
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) [data-testid="stVerticalBlock"]:has(.site-brand),
        [data-testid="stHorizontalBlock"].header-bar:has(.site-brand) [data-testid="stElementContainer"]:has(.site-brand) {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            height: 48px !important;
            min-height: 48px !important;
        }
        .site-brand {
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            overflow: hidden !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            flex-direction: row !important;
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
            height: 48px !important;
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
        .compare-drilldown-title {
            margin-top: 20px !important;
            margin-bottom: 6px !important;
            font-size: 1.02rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }
        .compare-table-wrap {
            margin: 8px 0 18px 0 !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 14px !important;
            overflow: hidden !important;
            background: var(--bg-card) !important;
            box-shadow: 0 6px 14px var(--shadow) !important;
        }
        .compare-table {
            width: 100% !important;
            border-collapse: collapse !important;
            font-size: 0.94rem !important;
        }
        .compare-table thead tr {
            background: var(--bg-secondary) !important;
        }
        .compare-table .compare-th {
            padding: 12px 16px !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            color: var(--text-secondary) !important;
            border-bottom: 1px solid var(--border-color) !important;
            text-align: left !important;
            white-space: nowrap !important;
        }
        .compare-table .compare-th--num {
            text-align: right !important;
        }
        .compare-table .compare-td {
            padding: 13px 16px !important;
            color: var(--text-primary) !important;
            border-bottom: 1px solid var(--border-light) !important;
            vertical-align: middle !important;
        }
        .compare-table tbody tr:last-child .compare-td {
            border-bottom: none !important;
        }
        .compare-table .compare-td--rank {
            font-variant-numeric: tabular-nums !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            width: 78px !important;
        }
        .compare-table .compare-td--name {
            font-weight: 600 !important;
            max-width: 320px !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }
        .compare-table .compare-td--num {
            text-align: right !important;
            font-variant-numeric: tabular-nums !important;
            font-weight: 600 !important;
            min-width: 76px !important;
        }
        /* Score tier colors (match single-report convention) */
        .compare-table .compare-td--score-good { color: #15803d !important; }
        .compare-table .compare-td--score-medium { color: #b45309 !important; }
        .compare-table .compare-td--score-low { color: #dc2626 !important; }
        /* Issues are inverted — fewer is better */
        .compare-table .compare-td--issue-good { color: #15803d !important; }
        .compare-table .compare-td--issue-medium { color: #b45309 !important; }
        .compare-table .compare-td--issue-high { color: #dc2626 !important; }
        body.theme-dark .compare-table .compare-td--score-good,
        body.theme-dark .compare-table .compare-td--issue-good {
            color: #4ade80 !important;
        }
        body.theme-dark .compare-table .compare-td--score-medium,
        body.theme-dark .compare-table .compare-td--issue-medium {
            color: #fbbf24 !important;
        }
        body.theme-dark .compare-table .compare-td--score-low,
        body.theme-dark .compare-table .compare-td--issue-high {
            color: #f87171 !important;
        }
        /* Winner row highlight */
        .compare-table tbody tr.compare-row--winner .compare-td {
            background: linear-gradient(90deg, rgba(34, 197, 94, 0.10), rgba(34, 197, 94, 0.0) 70%) !important;
        }
        .compare-table tbody tr.compare-row--winner .compare-td:first-child {
            box-shadow: inset 3px 0 0 #22c55e !important;
        }
        body.theme-dark .compare-table tbody tr.compare-row--winner .compare-td {
            background: linear-gradient(90deg, rgba(74, 222, 128, 0.14), rgba(74, 222, 128, 0.0) 70%) !important;
        }
        .compare-winner-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 4px !important;
            padding: 3px 10px !important;
            border-radius: 999px !important;
            background: rgba(245, 158, 11, 0.16) !important;
            color: #92400e !important;
            font-weight: 700 !important;
            font-size: 0.84rem !important;
            line-height: 1 !important;
        }
        body.theme-dark .compare-winner-pill {
            background: rgba(245, 158, 11, 0.22) !important;
            color: #fcd34d !important;
        }
        /* Inline mini-bar inside each score cell. ``currentColor`` on the
           fill inherits the tier color (.compare-td--score-good etc.) so
           the bar tints to match the number. */
        .compare-meter {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 10px !important;
            width: 100% !important;
        }
        .compare-meter__track {
            flex: 0 1 64px !important;
            min-width: 36px !important;
            height: 5px !important;
            border-radius: 999px !important;
            background: rgba(148, 163, 184, 0.22) !important;
            overflow: hidden !important;
        }
        body.theme-dark .compare-meter__track {
            background: rgba(148, 163, 184, 0.18) !important;
        }
        .compare-meter__fill {
            height: 100% !important;
            border-radius: 999px !important;
            background: currentColor !important;
            transition: width 0.4s ease !important;
        }
        .compare-meter__val {
            min-width: 24px !important;
            text-align: right !important;
            font-variant-numeric: tabular-nums !important;
            font-weight: 600 !important;
        }
        /* "Open as full report" button inside each drill-down expander —
           keep it visually distinct as a secondary "deep-dive" action. */
        [class*="st-key-compare_open_report_box_"] {
            margin-top: 10px !important;
            display: flex !important;
            justify-content: flex-end !important;
        }
        [class*="st-key-compare_open_report_box_"] [data-testid="stButton"] button {
            min-height: 38px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
        }
        /* Action row: tighten Streamlit's default vertical spacing so the
           Clear / Download buttons read as a single row beside the table. */
        .st-key-compare_report_actions {
            margin: 8px 0 8px 0 !important;
        }
        .st-key-compare_report_actions [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        .st-key-compare_report_actions [data-testid="stDownloadButton"] button,
        .st-key-compare_report_actions [data-testid="stButton"] button {
            min-height: 40px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        /* Sort selector — stacked label-above-select layout (works inside a
           half-width parent column, where nested columns would be both ugly
           and forbidden by Streamlit's max-1-level nesting rule). */
        .st-key-compare_sort_row {
            margin: 6px 0 8px 0 !important;
        }
        .st-key-compare_sort_row .compare-sort-label {
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            color: var(--text-secondary) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 4px !important;
            line-height: 1.2 !important;
        }
        .st-key-compare_sort_row [data-baseweb="select"] {
            min-height: 38px !important;
        }
        /* Primary section: tighten gaps so the LEFT/RIGHT columns read as one
           paired unit, and tame the top-match card's outer margin inside the
           right column (it was sized for full-width historically).
           Outer-card treatment mirrors the .st-key-hero_wrapper card on the
           Analyze CV home page so the two pages feel like siblings. */
        .st-key-compare_primary_section {
            position: relative !important;
            overflow: hidden !important;
            margin: 14px 0 18px 0 !important;
            padding: 26px 40px 24px !important;
            background:
                radial-gradient(120% 70% at 100% 0%, rgba(20, 184, 166, 0.08), transparent 55%),
                linear-gradient(135deg, var(--bg-hero), var(--bg-secondary)) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 22px !important;
            box-shadow: 0 8px 40px var(--shadow-lg) !important;
        }
        @media (max-width: 900px) {
            .st-key-compare_primary_section {
                padding: 18px 18px 16px !important;
                border-radius: 16px !important;
            }
        }
        .st-key-compare_primary_section .compare-top-card {
            margin-top: 0 !important;
        }
        .st-key-compare_primary_section .compare-results-title {
            margin: 0 0 6px 0 !important;
        }
        /* Chip strip (left half of the chips/sort sub-row, beside the
           selectbox). Aligned vertically with the selectbox below the
           "SORT BY" label that gets pulled up above it. */
        .st-key-compare_primary_section .compare-results-chips {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            align-items: center !important;
            margin: 0 !important;
            padding-top: 20px !important;
        }
        .st-key-compare_primary_section .compare-results-chips .hero-chip {
            padding: 5px 11px !important;
            font-size: 0.84rem !important;
            white-space: nowrap !important;
        }
        /* Lift only the SORT BY label up so it sits on the same baseline as
           the "Comparison Results" title in the row above. The selectbox
           stays in its current position — only the label moves. The
           negative margin equals roughly (title-height + title-margin-bottom
           + Streamlit vertical gap) so the label visually replaces what
           would otherwise be empty space to the right of the title. */
        .st-key-compare_primary_section .st-key-compare_sort_row .compare-sort-label {
            margin-top: -34px !important;
        }
        /* Sort row inside the primary section: drop its own outer margin
           so it doesn't compound with the chip-row padding. */
        .st-key-compare_primary_section .st-key-compare_sort_row {
            margin: 0 !important;
        }
        /* Pull the comparison table flush against the chips/sort row above
           it. The table-wrap defaults to 8px margin-top; inside the primary
           card we want it tighter so the section reads as one block. */
        .st-key-compare_primary_section .compare-table-wrap {
            margin-top: 4px !important;
        }
        /* Tame Streamlit's default vertical-block gap inside the left column
           so the title → (chips/sort) → table stack doesn't get extra dead
           space at every element boundary. */
        .st-key-compare_primary_section [data-testid="stVerticalBlock"] {
            gap: 0.4rem !important;
        }
        /* Narrower columns: relax the table's per-cell min-widths so the
           meters don't push the table beyond the column boundary. */
        .st-key-compare_primary_section .compare-table .compare-td--num {
            min-width: 64px !important;
        }
        .st-key-compare_primary_section .compare-table .compare-meter__track {
            flex: 0 1 48px !important;
            min-width: 28px !important;
        }
        .st-key-compare_primary_section .compare-table .compare-td--name {
            max-width: 220px !important;
        }
        .st-key-compare_primary_section .compare-table .compare-th,
        .st-key-compare_primary_section .compare-table .compare-td {
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        /* Hide the text caret inside the sort selectbox. BaseWeb's Select
           renders a real <input> for keyboard accessibility (visible blinking
           caret next to the selected option text on focus). Streamlit ships
           several CSS-in-JS rules with !important that can set caret-color
           on inner elements, so the safe play is to hide the caret on EVERY
           descendant of the sort row — there are no real text inputs in this
           sub-tree, so the blanket rule has no false positives. The first
           rule is the broad catch-all; the explicit selectors below it raise
           specificity for any element that gets a higher-specificity rule
           from Streamlit's stylesheet. */
        .st-key-compare_sort_row,
        .st-key-compare_sort_row * {
            caret-color: transparent !important;
        }
        body .st-key-compare_sort_row [data-testid="stSelectbox"] input,
        body .st-key-compare_sort_row [data-baseweb="select"] input,
        body .st-key-compare_sort_row [data-baseweb="select-control"] input,
        body .st-key-compare_sort_row [role="combobox"],
        body .st-key-compare_sort_row [role="combobox"] input,
        body .st-key-compare_sort_row [contenteditable] {
            caret-color: transparent !important;
            cursor: pointer !important;
        }
        .compare-progress-shell {
            margin: 12px 0 4px 0 !important;
            padding: 12px 14px !important;
            border-radius: 12px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
        }
        .compare-progress-header {
            font-size: 0.92rem !important;
            color: var(--text-secondary) !important;
            margin-bottom: 8px !important;
        }
        .compare-progress-list {
            list-style: none !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
        }
        .compare-progress-item {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            font-size: 0.92rem !important;
            color: var(--text-primary) !important;
        }
        .compare-progress-icon {
            width: 18px;
            text-align: center;
        }
        .compare-progress-name {
            font-weight: 600 !important;
            flex: 1 1 auto;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .compare-progress-status {
            color: var(--text-secondary) !important;
            font-size: 0.86rem !important;
        }
        .compare-progress-item--error .compare-progress-status,
        .compare-progress-item--error .compare-progress-name {
            color: #dc2626 !important;
        }
        .compare-progress-item--skipped .compare-progress-status {
            color: #b45309 !important;
        }
        .compare-progress-item--done .compare-progress-status {
            color: #15803d !important;
        }
        .compare-report-head {
            margin: 14px 0 18px 0 !important;
            padding: 24px 26px 22px 26px !important;
            border-radius: 18px !important;
            border: 1px solid var(--border-color) !important;
            background: linear-gradient(140deg, var(--bg-card), var(--bg-secondary)) !important;
            box-shadow: 0 14px 28px var(--shadow) !important;
        }
        .compare-report-back {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-bottom: 12px !important;
            padding: 5px 12px !important;
            border-radius: 999px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
            color: var(--text-secondary) !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            text-decoration: none !important;
            transition: transform 0.15s ease, color 0.15s ease !important;
        }
        .compare-report-back:hover,
        .compare-report-back:focus-visible {
            transform: translateX(-2px) !important;
            color: var(--text-primary) !important;
        }
        .compare-report-title {
            margin: 8px 0 6px 0 !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
            line-height: 1.1 !important;
        }
        .compare-report-subtitle {
            margin: 0 !important;
            font-size: 1rem !important;
            color: var(--text-secondary) !important;
            line-height: 1.5 !important;
            max-width: 760px !important;
        }
        .compare-report-empty {
            margin: 24px 0 32px 0 !important;
            padding: 36px 28px !important;
            border-radius: 18px !important;
            border: 1px dashed var(--border-color) !important;
            background: var(--bg-card) !important;
            text-align: center !important;
        }
        .compare-report-empty__icon {
            font-size: 2.4rem !important;
            line-height: 1 !important;
            margin-bottom: 10px !important;
        }
        .compare-report-empty__title {
            margin: 0 0 8px 0 !important;
            font-size: 1.45rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
        }
        .compare-report-empty__copy {
            margin: 0 auto 18px auto !important;
            max-width: 520px !important;
            font-size: 0.98rem !important;
            color: var(--text-secondary) !important;
            line-height: 1.5 !important;
        }
        .compare-view-results-row {
            display: flex !important;
            justify-content: flex-end !important;
            margin: 10px 0 8px 0 !important;
        }
        .compare-view-results-link {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 8px 14px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(37, 99, 235, 0.32) !important;
            background: rgba(37, 99, 235, 0.08) !important;
            color: #1d4ed8 !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            text-decoration: none !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }
        .compare-view-results-link:hover,
        .compare-view-results-link:focus-visible {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18) !important;
        }
        body.theme-dark .compare-view-results-link {
            background: rgba(96, 165, 250, 0.18) !important;
            border-color: rgba(96, 165, 250, 0.45) !important;
            color: #bfdbfe !important;
        }
        .compare-report-hero {
            /* Match the negative top margin trick used by my_analyses_page and
               my_comparisons_page so the hero sits flush under the fixed
               header instead of leaving a blank band above it. */
            margin: -72px 0 14px 0 !important;
            padding: 0 !important;
        }
        @media (max-width: 900px) {
            .compare-report-hero {
                margin-top: -38px !important;
            }
        }
        .compare-report-hero__title {
            margin: 8px 0 6px 0 !important;
            font-size: clamp(2rem, 3vw, 2.6rem) !important;
            font-weight: 900 !important;
            line-height: 1.08 !important;
            letter-spacing: -0.02em !important;
            color: var(--text-primary) !important;
        }
        .compare-report-hero__title span {
            background: linear-gradient(118deg, #0f6ac9 8%, #14b8a6 92%) !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
        }
        .compare-report-hero__subtitle {
            margin: 0 0 12px 0 !important;
            /* No max-width: subtitle is a single sentence and should sit on
               one line on desktop. Browser wraps naturally at narrow widths. */
            font-size: 1rem !important;
            line-height: 1.5 !important;
            color: var(--text-secondary) !important;
        }
        .compare-report-hero__chips {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            margin: 4px 0 0 0 !important;
        }
        .compare-top-card {
            position: relative !important;
            margin: 14px 0 10px 0 !important;
            padding: 18px 20px 16px 20px !important;
            border-radius: 16px !important;
            border: 1px solid rgba(37, 99, 235, 0.28) !important;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(14, 165, 183, 0.06)) !important;
            box-shadow: 0 10px 22px var(--shadow) !important;
        }
        body.theme-dark .compare-top-card {
            border-color: rgba(96, 165, 250, 0.35) !important;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(14, 165, 183, 0.12)) !important;
        }
        .compare-top-card__tag {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 4px 10px !important;
            border-radius: 999px !important;
            background: rgba(37, 99, 235, 0.14) !important;
            color: #1d4ed8 !important;
            font-size: 0.74rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
        }
        body.theme-dark .compare-top-card__tag {
            background: rgba(96, 165, 250, 0.22) !important;
            color: #bfdbfe !important;
        }
        .compare-top-card__head {
            display: flex !important;
            align-items: flex-start !important;
            justify-content: space-between !important;
            gap: 16px !important;
            margin-top: 8px !important;
            flex-wrap: wrap !important;
        }
        .compare-top-card__name {
            margin: 0 !important;
            font-size: 1.35rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
            word-break: break-word !important;
            line-height: 1.2 !important;
        }
        .compare-top-card__score {
            display: flex !important;
            align-items: baseline !important;
            gap: 4px !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
            line-height: 1 !important;
        }
        .compare-top-card__score-value {
            font-size: 2.1rem !important;
        }
        .compare-top-card__score-total {
            font-size: 0.95rem !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
        }
        .compare-top-card__bar {
            position: relative !important;
            width: 100% !important;
            height: 8px !important;
            margin-top: 12px !important;
            border-radius: 999px !important;
            background: rgba(148, 163, 184, 0.25) !important;
            overflow: hidden !important;
        }
        .compare-top-card__bar-fill {
            position: absolute !important;
            inset: 0 auto 0 0 !important;
            border-radius: 999px !important;
            background: linear-gradient(90deg, #2563eb, #0ea5b7) !important;
        }
        .compare-top-card__metrics {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
            margin-top: 14px !important;
        }
        .compare-top-card__metric {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 5px 10px !important;
            border-radius: 8px !important;
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            font-size: 0.85rem !important;
            color: var(--text-secondary) !important;
        }
        .compare-top-card__metric strong {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
        }
        .compare-top-card__skills {
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            gap: 6px !important;
            margin-top: 12px !important;
        }
        .compare-top-card__skills-label {
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            color: var(--text-secondary) !important;
            margin-right: 4px !important;
        }
        .compare-top-card__chip {
            display: inline-flex !important;
            align-items: center !important;
            padding: 3px 9px !important;
            border-radius: 999px !important;
            background: rgba(239, 68, 68, 0.10) !important;
            border: 1px solid rgba(239, 68, 68, 0.32) !important;
            color: #b91c1c !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
        }
        body.theme-dark .compare-top-card__chip {
            background: rgba(248, 113, 113, 0.16) !important;
            border-color: rgba(248, 113, 113, 0.42) !important;
            color: #fecaca !important;
        }
        .compare-top-card__chip--ok {
            background: rgba(16, 185, 129, 0.10) !important;
            border-color: rgba(16, 185, 129, 0.32) !important;
            color: #047857 !important;
        }
        body.theme-dark .compare-top-card__chip--ok {
            background: rgba(52, 211, 153, 0.16) !important;
            border-color: rgba(52, 211, 153, 0.42) !important;
            color: #bbf7d0 !important;
        }
        .st-key-compare_form_box {
            margin-top: 10px !important;
            margin-bottom: 4px !important;
            padding: 16px 16px 14px 16px !important;
            border-radius: 14px !important;
            border: 1px solid __COMPARE_BOX_BORDER__ !important;
            background: __COMPARE_BOX_BG__ !important;
            box-shadow: __COMPARE_BOX_SHADOW__ !important;
        }
        /* Sign-in CTA card (hero + compare guest views): distinct accent look
           so it visually differs from the clean white JD textarea card. */
        .st-key-upload_guest_box,
        .st-key-compare_guest_box {
            margin-top: 14px !important;
            margin-bottom: 4px !important;
            padding: 22px 18px 20px !important;
            border-radius: 14px !important;
            border: 1px solid rgba(15, 106, 201, 0.22) !important;
            background: linear-gradient(160deg, rgba(15, 106, 201, 0.07), rgba(20, 184, 166, 0.07)) !important;
            box-shadow: 0 8px 22px rgba(15, 106, 201, 0.10) !important;
        }
        body.theme-dark .st-key-upload_guest_box,
        body.theme-dark .st-key-compare_guest_box {
            background: linear-gradient(160deg, rgba(15, 106, 201, 0.18), rgba(20, 184, 166, 0.14)) !important;
            border-color: rgba(125, 211, 252, 0.30) !important;
            box-shadow: 0 12px 28px rgba(2, 8, 23, 0.40) !important;
        }
        .guest-auth-shell {
            text-align: center !important;
            padding: 0.5rem 0.75rem 0.35rem !important;
        }
        .guest-auth-icon {
            width: 46px !important;
            height: 46px !important;
            margin: 0 auto 0.6rem auto !important;
            border-radius: 999px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1.25rem !important;
            background: __GUEST_ICON_BG__ !important;
            color: __GUEST_ICON_COLOR__ !important;
            border: 1px solid rgba(59, 130, 246, 0.22) !important;
        }
        .guest-auth-title {
            margin: 0 0 0.4rem 0 !important;
            font-size: 1.45rem !important;
            line-height: 1.15 !important;
            font-weight: 800 !important;
            color: __GUEST_TITLE_COLOR__ !important;
        }
        .guest-auth-copy {
            margin: 0 auto 0.95rem auto !important;
            max-width: 640px !important;
            font-size: 0.94rem !important;
            line-height: 1.45 !important;
            color: __GUEST_BODY_COLOR__ !important;
        }
        .guest-auth-cta {
            display: inline-block !important;
            padding: 0.6rem 1.85rem !important;
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
        /* Analysis progress panel (renders under the hero scorecard while a CV is analyzed).
           Guarded with :has() so the empty container leaves no ghost card on the page. */
        .st-key-analysis_status_box:has([data-testid="stElementContainer"]) {
            margin-top: 16px !important;
            padding: 14px 16px 12px 16px !important;
            border: 1px solid __COMPARE_BOX_BORDER__ !important;
            border-radius: 14px !important;
            background: __COMPARE_BOX_BG__ !important;
            box-shadow: __COMPARE_BOX_SHADOW__ !important;
        }
        .st-key-analysis_status_box [data-testid="stVerticalBlock"] {
            gap: 0.6rem !important;
        }
        .st-key-analysis_status_box [data-testid="stExpander"] {
            margin: 0 !important;
        }
        .st-key-analysis_status_box [data-testid="stExpander"] summary {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            min-height: 0 !important;
        }
        .st-key-analysis_status_box [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
            flex: 0 0 1.25rem !important;
            width: 1.25rem !important;
            max-width: 1.25rem !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        }
        .st-key-analysis_status_box [data-testid="stExpander"] summary p,
        .st-key-analysis_status_box [data-testid="stExpander"] summary span:not([data-testid="stIconMaterial"]) {
            min-width: 0 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }
        .st-key-analysis_status_box [data-testid="stStatusWidget"],
        .st-key-analysis_status_box [data-testid="stSpinner"] {
            margin-top: 2px !important;
        }
        .st-key-analysis_status_box .chip {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 4px 11px !important;
            border-radius: 999px !important;
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            color: #0e7490 !important;
            background: rgba(20, 184, 166, 0.12) !important;
            border: 1px solid rgba(20, 184, 166, 0.28) !important;
        }
        .st-key-analysis_status_box .chip.chip-warn {
            color: #b45309 !important;
            background: rgba(245, 158, 11, 0.12) !important;
            border-color: rgba(245, 158, 11, 0.30) !important;
        }
        body.theme-dark .st-key-analysis_status_box .chip {
            color: #5eead4 !important;
            background: rgba(20, 184, 166, 0.18) !important;
        }
        body.theme-dark .st-key-analysis_status_box .chip.chip-warn {
            color: #fcd34d !important;
            background: rgba(245, 158, 11, 0.18) !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] {
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-compare_form_box [data-testid="stForm"] [data-testid="stVerticalBlock"] > div {
            margin-bottom: 6px !important;
        }
        .st-key-compare_form_box .stTextArea label,
        .st-key-compare_form_box .stFileUploader label {
            color: __COMPARE_LABEL_COLOR__ !important;
            font-weight: 700 !important;
        }
        /* The comparison "Job description" field uses the same textarea styling as the
           main "Job description" field — no compare-specific colours. */
        .stForm .stTextArea textarea:hover,
        .stForm .stTextArea textarea:focus,
        .stForm .stTextArea > div:hover textarea,
        .stForm .stTextArea > div:focus-within textarea {
            background: var(--excelcv-uniform-hover-bg) !important;
            border-color: var(--excelcv-uniform-hover-border) !important;
            box-shadow: var(--excelcv-uniform-hover-shadow) !important;
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
        /* ── Alternating section backgrounds for visual rhythm ─────────── */
        [data-testid="stAppViewContainer"] .landing-extended > section.landing-clean-section:nth-of-type(even) {
            background: linear-gradient(200deg, rgba(20, 184, 166, 0.06), rgba(15, 106, 201, 0.04)) !important;
            border-color: rgba(20, 184, 166, 0.18) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-extended > section.landing-clean-section:nth-of-type(even) {
            background: linear-gradient(200deg, rgba(20, 184, 166, 0.10), rgba(15, 106, 201, 0.08)) !important;
            border-color: rgba(20, 184, 166, 0.22) !important;
        }
        /* ── Comparison table (Why ExcelCV vs Generic ATS scanners) ────── */
        [data-testid="stAppViewContainer"] .landing-compare-wrap {
            overflow-x: auto !important;
            margin-top: 8px !important;
            border-radius: 14px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table {
            width: 100% !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 0.97rem !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table thead th {
            text-align: left !important;
            padding: 16px 18px !important;
            font-size: 0.95rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
            background: var(--bg-secondary) !important;
            border-bottom: 2px solid var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-th-us {
            color: #ffffff !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
            border-bottom-color: transparent !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-th-other {
            color: var(--text-muted) !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table tbody td {
            padding: 14px 18px !important;
            border-bottom: 1px solid var(--border-color) !important;
            vertical-align: top !important;
            line-height: 1.5 !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table tbody tr:last-child td {
            border-bottom: none !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-feature {
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            width: 24% !important;
            min-width: 160px !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-other {
            color: var(--text-muted) !important;
            width: 34% !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-us {
            color: var(--text-primary) !important;
            width: 42% !important;
            background: linear-gradient(135deg, rgba(15, 106, 201, 0.05), rgba(20, 184, 166, 0.05)) !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-other::before {
            content: "✕  " !important;
            color: #ef4444 !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .landing-compare-table .lc-us::before {
            content: "✓  " !important;
            color: #10b981 !important;
            font-weight: 800 !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-compare-table .lc-us {
            background: linear-gradient(135deg, rgba(15, 106, 201, 0.16), rgba(20, 184, 166, 0.14)) !important;
        }
        @media (max-width: 768px) {
            [data-testid="stAppViewContainer"] .landing-compare-table {
                font-size: 0.88rem !important;
            }
            [data-testid="stAppViewContainer"] .landing-compare-table thead th,
            [data-testid="stAppViewContainer"] .landing-compare-table tbody td {
                padding: 10px 12px !important;
            }
            [data-testid="stAppViewContainer"] .landing-compare-table .lc-feature {
                min-width: 120px !important;
            }
        }
        /* ── Comparison table lead-in pill ────────────────────────────── */
        [data-testid="stAppViewContainer"] .landing-compare-lead {
            display: inline-block !important;
            margin: 0 0 8px 0 !important;
            padding: 6px 14px !important;
            border-radius: 999px !important;
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em !important;
            text-transform: uppercase !important;
            color: #0f6ac9 !important;
            background: rgba(15, 106, 201, 0.10) !important;
            border: 1px solid rgba(15, 106, 201, 0.22) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .landing-compare-lead {
            color: #7dd3fc !important;
            background: rgba(15, 106, 201, 0.20) !important;
            border-color: rgba(125, 211, 252, 0.30) !important;
        }
        /* ── Hover animations on landing-clean-cards ──────────────────── */
        [data-testid="stAppViewContainer"] .landing-clean-card {
            transition: transform 220ms cubic-bezier(.22, 1, .36, 1),
                        box-shadow 220ms cubic-bezier(.22, 1, .36, 1),
                        border-color 220ms ease !important;
        }
        [data-testid="stAppViewContainer"] .landing-clean-card:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 14px 28px var(--shadow-lg) !important;
            border-color: rgba(20, 184, 166, 0.40) !important;
        }
        /* ── Feature showcase section ─────────────────────────────────── */
        [data-testid="stAppViewContainer"] .landing-showcase-grid {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 16px !important;
        }
        [data-testid="stAppViewContainer"] .landing-showcase-card {
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            background: var(--bg-card) !important;
            padding: 18px 18px 16px !important;
            box-shadow: 0 8px 18px var(--shadow) !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
            transition: transform 220ms cubic-bezier(.22, 1, .36, 1),
                        box-shadow 220ms cubic-bezier(.22, 1, .36, 1),
                        border-color 220ms ease !important;
        }
        [data-testid="stAppViewContainer"] .landing-showcase-card:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 14px 28px var(--shadow-lg) !important;
            border-color: rgba(20, 184, 166, 0.40) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-emoji {
            font-size: 1.5rem !important;
            line-height: 1 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-title {
            margin: 0 !important;
            font-size: 1.08rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-desc {
            margin: 0 !important;
            font-size: 0.86rem !important;
            line-height: 1.45 !important;
            color: var(--text-secondary) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mock {
            position: relative !important;
            height: 130px !important;
            border-radius: 10px !important;
            border: 1px solid var(--border-color) !important;
            background: linear-gradient(160deg, var(--bg-secondary), var(--bg-card)) !important;
            padding: 10px !important;
            overflow: hidden !important;
        }
        /* Mockup: Resume Builder (3-panel mini) */
        [data-testid="stAppViewContainer"] .lsc-mock-builder {
            display: grid !important;
            grid-template-columns: 22px 1fr 1.1fr !important;
            gap: 6px !important;
            padding: 8px !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-rail {
            display: flex !important;
            flex-direction: column !important;
            gap: 5px !important;
            padding: 4px 2px !important;
            background: var(--bg-card) !important;
            border-radius: 6px !important;
            border: 1px solid var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-section {
            display: block !important;
            height: 6px !important;
            border-radius: 3px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-section.active {
            background: linear-gradient(90deg, #0f6ac9, #14b8a6) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-editor,
        [data-testid="stAppViewContainer"] .lsc-mb-preview {
            background: var(--bg-card) !important;
            border-radius: 6px !important;
            border: 1px solid var(--border-color) !important;
            padding: 7px 6px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 5px !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-line {
            display: block !important;
            height: 5px !important;
            border-radius: 3px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-h {
            height: 7px !important;
            width: 70% !important;
            background: linear-gradient(90deg, #0f6ac9, #14b8a6) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-l1 { width: 95% !important; }
        [data-testid="stAppViewContainer"] .lsc-mb-l2 { width: 80% !important; }
        [data-testid="stAppViewContainer"] .lsc-mb-l3 { width: 60% !important; }
        [data-testid="stAppViewContainer"] .lsc-mb-pname {
            display: block !important;
            height: 8px !important;
            width: 60% !important;
            border-radius: 3px !important;
            background: var(--text-primary) !important;
            opacity: 0.45 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-pmeta {
            display: block !important;
            height: 4px !important;
            width: 80% !important;
            border-radius: 2px !important;
            background: var(--text-muted) !important;
            opacity: 0.5 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-prule {
            display: block !important;
            height: 1px !important;
            width: 100% !important;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-pline {
            display: block !important;
            height: 4px !important;
            width: 100% !important;
            border-radius: 2px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-mb-pline-short { width: 70% !important; }
        /* Mockup: Compare table */
        [data-testid="stAppViewContainer"] .lsc-mock-compare {
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
            padding: 8px !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-row {
            display: grid !important;
            grid-template-columns: 28px 1fr 32px !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 5px 7px !important;
            border-radius: 6px !important;
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            font-size: 0.7rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-winner {
            border-color: rgba(16, 185, 129, 0.40) !important;
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.10), var(--bg-card)) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-rank {
            color: var(--text-secondary) !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-winner .lsc-cmp-rank {
            color: #f59e0b !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-name {
            display: block !important;
            height: 6px !important;
            border-radius: 3px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cmp-score {
            text-align: right !important;
            font-weight: 800 !important;
            font-variant-numeric: tabular-nums !important;
        }
        [data-testid="stAppViewContainer"] .lsc-good { color: #10b981 !important; }
        [data-testid="stAppViewContainer"] .lsc-mid { color: #f59e0b !important; }
        [data-testid="stAppViewContainer"] .lsc-low { color: #ef4444 !important; }
        /* Mockup: Cover Letter */
        [data-testid="stAppViewContainer"] .lsc-mock-letter {
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
            padding: 10px !important;
            background: var(--bg-card) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-head {
            display: flex !important;
            justify-content: space-between !important;
            margin-bottom: 4px !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-name {
            display: block !important;
            height: 7px !important;
            width: 38% !important;
            border-radius: 3px !important;
            background: var(--text-primary) !important;
            opacity: 0.55 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-date {
            display: block !important;
            height: 7px !important;
            width: 22% !important;
            border-radius: 3px !important;
            background: var(--text-muted) !important;
            opacity: 0.5 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-line {
            display: block !important;
            height: 4px !important;
            width: 100% !important;
            border-radius: 2px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-line-short { width: 70% !important; }
        [data-testid="stAppViewContainer"] .lsc-cl-foot {
            display: flex !important;
            justify-content: flex-end !important;
            margin-top: auto !important;
        }
        [data-testid="stAppViewContainer"] .lsc-cl-pill {
            font-size: 0.6rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.06em !important;
            padding: 3px 8px !important;
            border-radius: 999px !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
            color: #ffffff !important;
        }
        /* Mockup: History list */
        [data-testid="stAppViewContainer"] .lsc-mock-history {
            display: flex !important;
            flex-direction: column !important;
            gap: 5px !important;
            padding: 8px !important;
        }
        [data-testid="stAppViewContainer"] .lsc-hi-row {
            display: grid !important;
            grid-template-columns: 12px 1fr 30px !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 5px 7px !important;
            border-radius: 6px !important;
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            font-size: 0.7rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stAppViewContainer"] .lsc-hi-dot {
            display: block !important;
            width: 8px !important;
            height: 8px !important;
            border-radius: 999px !important;
            background: linear-gradient(135deg, #0f6ac9, #14b8a6) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-hi-name {
            display: block !important;
            height: 6px !important;
            border-radius: 3px !important;
            background: var(--border-color) !important;
        }
        [data-testid="stAppViewContainer"] .lsc-hi-score {
            text-align: right !important;
            font-variant-numeric: tabular-nums !important;
        }
        @media (max-width: 1100px) {
            [data-testid="stAppViewContainer"] .landing-showcase-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }
        @media (max-width: 600px) {
            [data-testid="stAppViewContainer"] .landing-showcase-grid {
                grid-template-columns: 1fr !important;
            }
        }
        /* ── Compare Multiple Resumes — preview card on the right ─────── */
        [data-testid="stAppViewContainer"] .compare-preview-card {
            border: 1px solid var(--border-color) !important;
            border-radius: 18px !important;
            background:
                radial-gradient(120% 80% at 0% 0%, rgba(15, 106, 201, 0.10), transparent 60%),
                radial-gradient(130% 90% at 100% 100%, rgba(20, 184, 166, 0.13), transparent 55%),
                var(--bg-card) !important;
            box-shadow: 0 18px 36px var(--shadow-lg) !important;
            padding: 18px 18px 14px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 14px !important;
            height: 100% !important;
        }
        [data-testid="stAppViewContainer"] .cpc-top-match {
            border: 1px solid var(--border-color) !important;
            border-radius: 14px !important;
            background: var(--bg-card) !important;
            padding: 12px 14px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-tag {
            display: inline-flex !important;
            align-items: center !important;
            align-self: flex-start !important;
            padding: 3px 10px !important;
            border-radius: 999px !important;
            font-size: 0.7rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.06em !important;
            color: #0f6ac9 !important;
            background: rgba(15, 106, 201, 0.10) !important;
            border: 1px solid rgba(15, 106, 201, 0.22) !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-row {
            display: flex !important;
            align-items: baseline !important;
            justify-content: space-between !important;
            gap: 10px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-name {
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-score {
            font-size: 1.5rem !important;
            font-weight: 900 !important;
            color: #10b981 !important;
            font-variant-numeric: tabular-nums !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-out {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            color: var(--text-muted) !important;
            margin-left: 2px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-bar {
            position: relative !important;
            height: 8px !important;
            border-radius: 999px !important;
            background: var(--bg-secondary) !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-bar-fill {
            position: absolute !important;
            inset: 0 !important;
            width: 91% !important;
            background: linear-gradient(90deg, #0f6ac9, #10b981) !important;
            border-radius: 999px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-metrics {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 6px !important;
            margin-top: 2px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-metric {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            padding: 4px 2px !important;
            border-radius: 8px !important;
            background: var(--bg-secondary) !important;
            min-width: 0 !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-mlabel {
            font-size: 0.62rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            color: var(--text-muted) !important;
        }
        [data-testid="stAppViewContainer"] .cpc-tm-mval {
            font-size: 0.95rem !important;
            font-weight: 800 !important;
            font-variant-numeric: tabular-nums !important;
            margin-top: 1px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-table {
            display: flex !important;
            flex-direction: column !important;
            gap: 5px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-row {
            display: grid !important;
            grid-template-columns: 36px 1fr 110px 40px !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 8px 10px !important;
            border-radius: 10px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
            font-size: 0.85rem !important;
        }
        [data-testid="stAppViewContainer"] .cpc-row-winner {
            border-color: rgba(16, 185, 129, 0.40) !important;
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.10), var(--bg-card)) !important;
        }
        [data-testid="stAppViewContainer"] .cpc-rank {
            font-weight: 800 !important;
            color: var(--text-secondary) !important;
            font-size: 0.85rem !important;
        }
        [data-testid="stAppViewContainer"] .cpc-row-winner .cpc-rank {
            color: #f59e0b !important;
        }
        [data-testid="stAppViewContainer"] .cpc-name {
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        [data-testid="stAppViewContainer"] .cpc-bar {
            position: relative !important;
            height: 6px !important;
            border-radius: 999px !important;
            background: var(--bg-secondary) !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewContainer"] .cpc-bar-fill {
            display: block !important;
            height: 100% !important;
            width: var(--cw, 80%) !important;
            border-radius: 999px !important;
        }
        [data-testid="stAppViewContainer"] .cpc-good-bg { background: #10b981 !important; }
        [data-testid="stAppViewContainer"] .cpc-mid-bg { background: #f59e0b !important; }
        [data-testid="stAppViewContainer"] .cpc-low-bg { background: #ef4444 !important; }
        [data-testid="stAppViewContainer"] .cpc-score {
            text-align: right !important;
            font-weight: 800 !important;
            font-variant-numeric: tabular-nums !important;
        }
        [data-testid="stAppViewContainer"] .cpc-good { color: #10b981 !important; }
        [data-testid="stAppViewContainer"] .cpc-mid { color: #f59e0b !important; }
        [data-testid="stAppViewContainer"] .cpc-low { color: #ef4444 !important; }
        [data-testid="stAppViewContainer"] .cpc-foot {
            text-align: center !important;
            font-size: 0.7rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            color: var(--text-muted) !important;
            margin-top: 2px !important;
        }
        /* ── Compare section feature chips (replaces "What happens next?") */
        [data-testid="stAppViewContainer"] .compare-feature-chips {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 12px !important;
            margin-top: 18px !important;
        }
        [data-testid="stAppViewContainer"] .cfc-chip {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 12px 14px !important;
            border-radius: 12px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--bg-card) !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06) !important;
            transition: transform 200ms cubic-bezier(.22, 1, .36, 1),
                        box-shadow 200ms cubic-bezier(.22, 1, .36, 1) !important;
        }
        [data-testid="stAppViewContainer"] .cfc-chip:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.10) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] .cfc-chip {
            box-shadow: 0 4px 12px rgba(2, 8, 23, 0.30) !important;
        }
        [data-testid="stAppViewContainer"] .cfc-icon {
            font-size: 1.1rem !important;
            flex: none !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: linear-gradient(135deg, rgba(15, 106, 201, 0.10), rgba(20, 184, 166, 0.12)) !important;
        }
        [data-testid="stAppViewContainer"] .cfc-text {
            font-size: 0.84rem !important;
            line-height: 1.35 !important;
            color: var(--text-secondary) !important;
        }
        [data-testid="stAppViewContainer"] .cfc-text strong {
            color: var(--text-primary) !important;
            font-weight: 800 !important;
        }
        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] .compare-feature-chips {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }
        @media (max-width: 520px) {
            [data-testid="stAppViewContainer"] .compare-feature-chips {
                grid-template-columns: 1fr !important;
            }
            [data-testid="stAppViewContainer"] .cpc-row {
                grid-template-columns: 32px 1fr 36px !important;
            }
            [data-testid="stAppViewContainer"] .cpc-bar {
                display: none !important;
            }
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
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }
        /* CV Builder rail safety: prevent style controls from being clipped by global overrides. */
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-left-scroll-native {
            height: var(--cvb-workspace-h) !important;
            max-height: var(--cvb-workspace-h) !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            scrollbar-gutter: auto !important;
        }
        /* CV Builder: keep toolbar-to-workspace transition flush. */
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-toolbar-native) + [data-testid="stElementContainer"]:has(.st-key-cvb-main-native) {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            row-gap: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        [data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"] {
            min-height: 0 !important;
            height: auto !important;
            max-height: none !important;
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
                padding: 0 10px 0 0 !important;
            }
            .site-logo-wordmark {
                height: 44px !important;
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
                height: 38px !important;
                transform: scale(1.0) !important;
            }
            #excelcv-fixed-header-spacer {
                min-height: 48px;
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
  max-height:48px !important; overflow:hidden !important;
}
[data-testid="stAppViewContainer"] .site-brand img{
  height:48px !important; max-height:48px !important; width:auto !important;
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
                    48,
                    Math.ceil(header.getBoundingClientRect().height || header.offsetHeight || 78)
                );
                spacer.style.display = 'block';
                spacer.style.width = '100%';
                spacer.style.height = (top + headerHeight) + 'px';
                spacer.style.margin = '0';
                spacer.style.padding = '0';
                spacer.style.pointerEvents = 'none';

                try {
                    var fixedSpace = (top + headerHeight) + 'px';
                    doc.documentElement.style.setProperty('--excelcv-fixed-header-space', fixedSpace);
                    doc.body.style.setProperty('--excelcv-fixed-header-space', fixedSpace);
                } catch (e) {}
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
