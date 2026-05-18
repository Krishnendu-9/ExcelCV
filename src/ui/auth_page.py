"""Login / Register / Forgot-Password page for the Streamlit app."""

import base64
import json
import textwrap
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import (
    authenticate_user,
    build_session_cookie_header,
    create_session_token,
    create_password_reset_token,
    create_user,
    is_persistent_login_enabled,
    login_user,
    use_password_reset_token,
)
from src.email_utils import is_email_configured, send_password_reset_email
from src.oauth_utils import GOOGLE_REDIRECT_URI as _APP_URL
from src.oauth_utils import (
    build_google_auth_url,
    create_oauth_state_token,
    is_google_oauth_configured,
)
from src.ui.app_utils import APP_PAGES, _build_page_href


def _logo_data_uri() -> str:
    base_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "images"
    for name in ("ExcelCV_clean.png", "ExcelCV.png"):
        p = base_dir / name
        if p.exists():
            return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
    return ""


def _redirect_after_login(user_dict: dict, redirect_to: str) -> None:
    """Set session cookie client-side and hard-navigate so auth persists across page reloads."""
    login_user(user_dict)
    target_url = _build_page_href(redirect_to or "home")
    cookie_value = ""
    if is_persistent_login_enabled():
        token = create_session_token(user_dict)
        cookie_value = build_session_cookie_header(token)
    components.html(
        f"""<script>
(function() {{
  var cookie = {json.dumps(cookie_value)};
  var target = {json.dumps(target_url)};
  function forceNavigate(win) {{
    try {{ win.location.href = target; }} catch(e) {{}}
    try {{ win.location.assign(target); }} catch(e) {{}}
  }}
  if (cookie) {{
    try {{ document.cookie = cookie; }} catch(e) {{}}
  }}
  try {{
    var w = window.parent && window.parent !== window ? window.parent : window;
    if (cookie) {{
      w.document.cookie = cookie;
    }}
    forceNavigate(w);
    return;
  }} catch(e) {{}}
  forceNavigate(window);
}})();
</script>""",
        height=0,
    )
    st.stop()


def _resolve_post_login_target() -> str:
    """Resolve where auth should redirect after successful login."""
    candidate = st.session_state.get("auth_redirect") or st.query_params.get("next") or "home"
    page = str(candidate or "").strip()
    if page in APP_PAGES and page != "auth":
        return page
    return "home"


_DARK = {
    "bg": "#0b0f17",
    "hero_panel_bg": "linear-gradient(165deg, rgba(8, 21, 44, 0.86), rgba(7, 28, 56, 0.74))",
    "hero_panel_border": "rgba(56, 189, 248, 0.22)",
    "hero_panel_shadow": "0 20px 45px rgba(2, 8, 23, 0.45)",
    "surface_bg": "linear-gradient(175deg, rgba(15, 23, 42, 0.94), rgba(2, 14, 34, 0.92))",
    "surface_border": "rgba(148, 163, 184, 0.26)",
    "surface_shadow": "0 22px 48px rgba(2, 8, 23, 0.42)",
    "title": "#e2e8f0",
    "subtitle": "#94a3b8",
    "label": "#cbd5e1",
    "input_bg": "rgba(30, 41, 59, 0.78)",
    "input_text": "#f1f5f9",
    "input_border": "rgba(148, 163, 184, 0.4)",
    "input_placeholder": "#94a3b8",
    "badge_bg": "rgba(37, 99, 235, 0.22)",
    "badge_border": "rgba(125, 211, 252, 0.35)",
    "badge_text": "#7dd3fc",
    "tab_text": "#9ca3af",
    "tab_active_text": "#38bdf8",
    "tab_active_border": "#38bdf8",
    "tab_hover_text": "#7dd3fc",
    "google_bg": "rgba(15, 23, 42, 0.65)",
    "google_border": "rgba(148, 163, 184, 0.35)",
    "google_text": "#e2e8f0",
    "divider": "rgba(148, 163, 184, 0.3)",
    "divider_text": "#94a3b8",
    "link": "#60a5fa",
    "link_hover": "#93c5fd",
    "back_border": "rgba(148, 163, 184, 0.34)",
    "back_text": "#cbd5e1",
    "back_bg": "rgba(15, 23, 42, 0.58)",
    "footer": "#64748b",
}

_LIGHT = {
    "bg": "#f1f5f9",
    "hero_panel_bg": "linear-gradient(165deg, rgba(248, 250, 252, 0.96), rgba(226, 232, 240, 0.92))",
    "hero_panel_border": "rgba(148, 163, 184, 0.36)",
    "hero_panel_shadow": "0 16px 36px rgba(15, 23, 42, 0.11)",
    "surface_bg": "linear-gradient(175deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96))",
    "surface_border": "rgba(148, 163, 184, 0.36)",
    "surface_shadow": "0 20px 36px rgba(15, 23, 42, 0.12)",
    "title": "#0f172a",
    "subtitle": "#64748b",
    "label": "#1e293b",
    "input_bg": "#f8fafc",
    "input_text": "#0f172a",
    "input_border": "rgba(148, 163, 184, 0.58)",
    "input_placeholder": "#64748b",
    "badge_bg": "rgba(37, 99, 235, 0.1)",
    "badge_border": "rgba(37, 99, 235, 0.32)",
    "badge_text": "#1d4ed8",
    "tab_text": "#64748b",
    "tab_active_text": "#1d4ed8",
    "tab_active_border": "#2563eb",
    "tab_hover_text": "#1e40af",
    "google_bg": "#ffffff",
    "google_border": "rgba(148, 163, 184, 0.52)",
    "google_text": "#1f2937",
    "divider": "rgba(148, 163, 184, 0.42)",
    "divider_text": "#64748b",
    "link": "#2563eb",
    "link_hover": "#1d4ed8",
    "back_border": "rgba(148, 163, 184, 0.48)",
    "back_text": "#334155",
    "back_bg": "rgba(255, 255, 255, 0.8)",
    "footer": "#64748b",
}

_GOOGLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18" style="flex-shrink:0">
  <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
  <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
  <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
  <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
</svg>"""


def _base_css(t: dict) -> str:
    return textwrap.dedent(
        f"""
    <style>
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    .stMainBlockContainer {{
        background: {t["bg"]} !important;
    }}

    /* Suppress the always-on html scrollbar placeholder injected by the
       global base theme so the auth page renders without any scroll UI.
       Use both overflow and scrollbar-gutter resets so neither the body
       scrollbar nor the reserved gutter strip shows. */
    html, body {{
        overflow: hidden !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
        scrollbar-gutter: auto !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
    }}
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section.main,
    [data-testid="stMain"] {{
        height: 100dvh !important;
        max-height: 100dvh !important;
        overflow: hidden !important;
    }}

    [data-testid="stAppViewContainer"] .main .block-container {{
        max-width: 1240px !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        box-sizing: border-box !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* Outer auth card — ~88vh tall, vertically centered in the viewport so a
       small breathing margin shows above and below. */
    .st-key-auth_shell {{
        width: 100% !important;
        max-width: 100% !important;
        height: 88dvh !important;
        max-height: 88dvh !important;
        margin: 0 auto !important;
        border-radius: 22px !important;
        border: 1px solid {t["hero_panel_border"]} !important;
        background: {t["hero_panel_bg"]} !important;
        box-shadow: 0 18px 38px rgba(15, 23, 42, 0.14) !important;
        padding: 1.2rem 1.8rem !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }}

    /* Two-column flex centering inside the shell. */
    .st-key-auth_shell > [data-testid="stVerticalBlock"] {{
        width: 100% !important;
        height: 100% !important;
        justify-content: center !important;
    }}
    .st-key-auth_shell [data-testid="stHorizontalBlock"] {{
        width: 100% !important;
        align-items: center !important;
    }}

    /* Left value-prop panel — logo, eyebrow, title, feature list, and
       "how it works" strip stacked tightly so all content fits in the
       fixed 88dvh card without scrolling. Subtitle was removed because
       the title + feature bullets already say the same thing. */
    .auth-brand-panel {{
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        padding: 0.2rem 1.6rem 0.2rem 0.2rem;
    }}
    .auth-brand-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.1rem;
    }}
    .auth-brand-logo {{
        height: 34px;
        width: auto;
        object-fit: contain;
    }}
    .auth-brand-wordmark {{
        color: #2563eb;
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.005em;
    }}
    .auth-brand-eyebrow {{
        display: inline-flex;
        align-items: center;
        align-self: flex-start;
        gap: 8px;
        color: {t["badge_text"]};
        background: {t["badge_bg"]};
        border: 1px solid {t["badge_border"]};
        border-radius: 999px;
        padding: 0.16rem 0.6rem;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }}
    .auth-brand-title {{
        margin: 0;
        color: {t["title"]};
        font-size: clamp(1.35rem, 2.05vw, 1.85rem);
        line-height: 1.12;
        font-weight: 800;
        letter-spacing: -0.01em;
    }}
    /* Suppress Streamlit's auto-generated heading anchor link icon that
       leaks next to the headline period in the brand panel. */
    .auth-brand-title a,
    .auth-brand-title .anchor-link,
    .auth-brand-panel a[href^="#"] {{
        display: none !important;
    }}
    .auth-brand-subtitle {{
        margin: 0;
        color: {t["subtitle"]};
        font-size: 0.98rem;
        line-height: 1.5;
        max-width: 42ch;
    }}
    .auth-brand-features {{
        margin: 0.1rem 0 0 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 0.38rem;
    }}
    .auth-brand-features li {{
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
    }}
    .auth-feature-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 999px;
        background: {t["badge_bg"]};
        color: {t["badge_text"]};
        font-size: 0.74rem;
        font-weight: 800;
        flex-shrink: 0;
        margin-top: 0.08rem;
    }}
    .auth-brand-features li > div {{
        display: flex;
        flex-direction: column;
        gap: 0.04rem;
    }}
    .auth-brand-features li strong {{
        color: {t["title"]};
        font-size: 0.88rem;
        font-weight: 700;
        line-height: 1.25;
    }}
    .auth-brand-features li span {{
        color: {t["subtitle"]};
        font-size: 0.78rem;
        line-height: 1.35;
    }}

    /* "How it works" 3-step strip below the feature bullets. Compact
       single-column band, badge-colored to tie back to the eyebrow at
       the top of the panel. */
    .auth-howitworks {{
        margin: 0.25rem 0 0 0;
        padding: 0.55rem 0.75rem;
        border-radius: 12px;
        background: {t["badge_bg"]};
        border: 1px solid {t["badge_border"]};
        display: flex;
        flex-direction: column;
        gap: 0.32rem;
    }}
    .auth-howitworks-label {{
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {t["badge_text"]};
    }}
    .auth-howitworks-steps {{
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.26rem;
    }}
    .auth-howitworks-steps li {{
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
    }}
    .auth-step-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 999px;
        background: {t["badge_text"]};
        color: {t["bg"]};
        font-size: 0.68rem;
        font-weight: 800;
        flex-shrink: 0;
        margin-top: 0.04rem;
    }}
    .auth-step-text {{
        color: {t["title"]};
        font-size: 0.78rem;
        line-height: 1.35;
        font-weight: 500;
    }}

    .st-key-auth_surface,
    .st-key-auth_surface_forgot,
    .st-key-auth_surface_reset {{
        border-radius: 22px !important;
        border: 1px solid {t["surface_border"]} !important;
        background: {t["surface_bg"]} !important;
        box-shadow: {t["surface_shadow"]} !important;
        padding: 0.5rem 0.72rem 0.72rem 0.72rem !important;
        margin: 0.02rem auto 0 auto !important;
    }}
    .st-key-auth_surface {{
        min-height: 0 !important;
    }}
    .st-key-auth_surface [data-testid="stVerticalBlock"],
    .st-key-auth_surface_forgot [data-testid="stVerticalBlock"],
    .st-key-auth_surface_reset [data-testid="stVerticalBlock"] {{
        gap: 0.42rem !important;
    }}

    .auth-surface-head {{
        margin-bottom: 0.15rem;
        text-align: left;
    }}
    .auth-surface-title {{
        margin: 0 0 0.12rem 0;
        color: {t["title"]};
        font-size: 1.06rem;
        font-weight: 800;
        line-height: 1.2;
    }}
    .auth-surface-subtitle {{
        margin: 0;
        color: {t["subtitle"]};
        font-size: 0.82rem;
        line-height: 1.3;
    }}

    div[data-testid="stTabs"] > div:first-child,
    div[data-testid="stTabs"] [data-testid="stTabsListContainer"],
    div[data-testid="stTabs"] [role="tablist"] {{
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin-bottom: 0.12rem !important;
    }}
    div[data-testid="stTabs"] button {{
        color: {t["tab_text"]} !important;
        font-size: 0.9rem;
        font-weight: 700;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: {t["tab_active_text"]} !important;
        border-bottom-color: {t["tab_active_border"]} !important;
    }}
    div[data-testid="stTabs"] button:hover {{
        color: {t["tab_hover_text"]} !important;
        background: transparent !important;
    }}

    div[data-testid="stTextInput"] [data-baseweb="input"] {{
        background: {t["input_bg"]} !important;
        border: 1px solid {t["input_border"]} !important;
        border-radius: 12px !important;
        min-height: 2rem !important;
        transition: border-color 0.15s, box-shadow 0.15s !important;
    }}
    div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {{
        border-color: {t["tab_active_border"]} !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }}
    /* Higher specificity than the global `body.theme-light/dark
       [data-testid="stTextInput"] input` rules in base_theme.css.tpl which
       paint a white background + 1px border + drop shadow on the <input>
       element itself, creating a nested inner box inside our frame.
       Vertical centering trick: setting `height` == `line-height` removes
       the dependence on font baseline / character set. Asterisks in the
       password placeholder and letters in the email placeholder otherwise
       baseline differently — asterisks sit higher in the line, descenders
       sit lower — and padding-based centering becomes visibly uneven. */
    body div[data-testid="stTextInput"] input,
    body.theme-light div[data-testid="stTextInput"] input,
    body.theme-light .stTextInput input,
    body.theme-light [data-testid="stTextInput"] input,
    body.theme-light div[data-baseweb="input"] input,
    body.theme-dark div[data-testid="stTextInput"] input,
    body.theme-dark .stTextInput input,
    body.theme-dark [data-testid="stTextInput"] input,
    body.theme-dark div[data-baseweb="input"] input {{
        background: transparent !important;
        background-color: transparent !important;
        color: {t["input_text"]} !important;
        caret-color: {t["input_text"]} !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-appearance: none !important;
        -moz-appearance: none !important;
        appearance: none !important;
        font-size: 0.9rem !important;
        height: 2.4rem !important;
        min-height: 2.4rem !important;
        line-height: 2.4rem !important;
        padding: 0 0.85rem !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }}
    /* Placeholder pseudo-element: match the same line-height so the
       placeholder text aligns vertically the same way the typed text
       would, regardless of which characters are in it. */
    body div[data-testid="stTextInput"] input::placeholder,
    body.theme-light div[data-testid="stTextInput"] input::placeholder,
    body.theme-dark div[data-testid="stTextInput"] input::placeholder {{
        line-height: 2.4rem !important;
        vertical-align: middle !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: {t["input_placeholder"]} !important;
        opacity: 1 !important;
    }}
    label, .stTextInput label {{
        color: {t["label"]} !important;
        font-weight: 700 !important;
    }}

    /* Password reveal eye button — matches the cv_builder .eye-btn style
       (flat icon, 2px padding, no chrome, tinted hover background).
       Streamlit's global `.stForm button` rules in base_theme.css.tpl
       paint every form button with a 44px-tall pill shape with a border,
       background, and shadow — that's why the eye renders as a "creepy"
       detached boxed widget. We override here with stAppViewContainer +
       !important specificity and target every flavor of clickable element
       Streamlit/BaseWeb might use for the reveal (button, [role=button],
       [tabindex], and the textPasswordReveal baseweb wrapper). */

    /* The input frame: the single bordered, rounded box. All children
       inside it (regardless of BaseWeb version / wrapper name / type)
       get their backgrounds, borders, radii, and shadows nuked, so the
       frame reads as ONE rounded field — not a nested "box on a box". */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stAppViewContainer"] .stTextInput [data-baseweb="input"] {{
        background: {t["input_bg"]} !important;
        border: 1px solid {t["input_border"]} !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}
    /* Universal-descendant reset — every wrapper inside the frame is
       made visually transparent. The `:not(input):not(svg):not(path)`
       guard preserves the input element's typography and the eye
       button's SVG; everything else (BaseWeb wrappers, InputContainer,
       BaseInput, base-input, passwordReveal sub-divs, etc.) becomes
       invisible chrome. */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"] *:not(input):not(svg):not(path):not(button):not([role="button"]) {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    /* First inline wrapper grows to fill the row (so the password eye
       reveal lands on the right edge). Doesn't change layout for plain
       inputs because there's only one wrapper anyway. */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"] > div:first-child {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
        display: flex !important;
        align-items: center !important;
    }}
    /* The <input> element itself fills its wrapper. */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"] input {{
        width: 100% !important;
        flex: 1 1 auto !important;
    }}
    /* Reveal-container wrappers stay transparent but don't take row space. */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"] [class*="input-icon"],
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="textPasswordReveal"] {{
        flex: 0 0 auto !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* The eye reveal itself. Cover every shape Streamlit might use. */
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] button,
    [data-testid="stAppViewContainer"] .stTextInput button,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"] button,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [role="button"],
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="textPasswordReveal"] > *,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [aria-label*="ass" i] {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 28px !important;
        height: 28px !important;
        min-height: 0 !important;
        min-width: 0 !important;
        max-height: 28px !important;
        margin: 0 !important;
        padding: 2px !important;
        border: none !important;
        border-radius: 6px !important;
        color: {t["subtitle"]} !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        appearance: none !important;
        cursor: pointer !important;
        flex-shrink: 0 !important;
        transition: color 0.12s ease, background-color 0.12s ease !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] button *,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [role="button"] * {{
        background: transparent !important;
        background-color: transparent !important;
        color: inherit !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] button:hover,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] button:focus-visible,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [role="button"]:hover,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [role="button"]:focus-visible {{
        color: {t["tab_active_text"]} !important;
        background: rgba(37, 99, 235, 0.12) !important;
        background-color: rgba(37, 99, 235, 0.12) !important;
        outline: none !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] button svg,
    [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [role="button"] svg {{
        width: 16px !important;
        height: 16px !important;
        fill: currentColor !important;
        stroke: currentColor !important;
    }}
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {{
        display: none !important;
    }}

    div[data-testid="stForm"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}

    /* Inline "Forgot your password?" text link — sits between password
       input and Sign In submit, right-aligned, no button chrome. */
    .auth-forgot-row {{
        display: flex;
        justify-content: flex-end;
        margin: 0.1rem 0 0.45rem 0;
    }}
    [data-testid="stAppViewContainer"] a.auth-forgot-link {{
        color: {t["link"]} !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        line-height: 1.2 !important;
        padding: 0.12rem 0.18rem !important;
        border-radius: 6px !important;
        transition: color 0.15s ease, background-color 0.15s ease !important;
    }}
    [data-testid="stAppViewContainer"] a.auth-forgot-link:hover,
    [data-testid="stAppViewContainer"] a.auth-forgot-link:focus-visible {{
        color: {t["link_hover"]} !important;
        text-decoration: underline !important;
        text-underline-offset: 3px !important;
        outline: none !important;
    }}
    div[data-testid="stFormSubmitButton"] button,
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 800 !important;
        min-height: 2.08rem !important;
    }}

    /* Strong primary CTA for the Sign In / Create Account submit buttons.
       The base theme applies `var(--button-bg)` (white) to `.stForm button`
       AND its children via `[data-testid="stAppViewContainer"] .stForm
       button *` — that's why a naive `background: linear-gradient(...)` on
       the button alone showed up as a thin border with white interior. We
       have to match that specificity (`stAppViewContainer` prefix) AND make
       all children transparent so the button's gradient shows through. */
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button,
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button[kind],
    [data-testid="stAppViewContainer"] .stForm div[data-testid="stFormSubmitButton"] button {{
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 55%, #38bdf8 100%) !important;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid rgba(37, 99, 235, 0.78) !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        min-height: 2.4rem !important;
        padding: 0.45rem 1rem !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
        transition: transform 0.12s ease, box-shadow 0.16s ease, filter 0.16s ease !important;
    }}
    /* Children get transparent backgrounds and white text so the button's
       gradient is visible behind the label markdown wrapper. */
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button *,
    [data-testid="stAppViewContainer"] .stForm div[data-testid="stFormSubmitButton"] button * {{
        background: transparent !important;
        background-color: transparent !important;
        color: #ffffff !important;
        border-color: transparent !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stAppViewContainer"] .stForm div[data-testid="stFormSubmitButton"] button:hover {{
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 55%, #38bdf8 100%) !important;
        background-color: #1d4ed8 !important;
        border-color: rgba(29, 78, 216, 0.85) !important;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
        transform: translateY(-1px) !important;
        outline: none !important;
        color: #ffffff !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button:hover *,
    [data-testid="stAppViewContainer"] .stForm div[data-testid="stFormSubmitButton"] button:hover * {{
        background: transparent !important;
        background-color: transparent !important;
        color: #ffffff !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button:active {{
        transform: translateY(0) !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    }}
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button:disabled,
    [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] button[disabled] {{
        filter: grayscale(0.4) brightness(0.92) !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }}
    /* Secondary auth-action buttons (back to login, go to sign-in,
       resend reset). The forgot-password button was removed in favour of an
       inline text link; remaining selectors style the back/return actions. */
    div.st-key-back_from_sent button,
    div[data-testid="stButton"].st-key-back_from_sent > button,
    div.st-key-back_to_login button,
    div[data-testid="stButton"].st-key-back_to_login > button,
    div.st-key-go_signin button,
    div[data-testid="stButton"].st-key-go_signin > button {{
        background-color: var(--button-bg) !important;
        background: var(--button-bg) !important;
        color: var(--button-text) !important;
        border: 1px solid var(--button-border) !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        min-height: 2.08rem !important;
        transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
        box-shadow: var(--button-shadow) !important;
    }}
    div.st-key-back_from_sent button:hover,
    div.st-key-back_from_sent button:focus-visible,
    div.st-key-back_from_sent button:focus,
    div.st-key-back_from_sent button:active,
    div[data-testid="stButton"].st-key-back_from_sent > button:hover,
    div[data-testid="stButton"].st-key-back_from_sent > button:focus-visible,
    div[data-testid="stButton"].st-key-back_from_sent > button:focus,
    div[data-testid="stButton"].st-key-back_from_sent > button:active,
    div.st-key-back_to_login button:hover,
    div.st-key-back_to_login button:focus-visible,
    div.st-key-back_to_login button:focus,
    div.st-key-back_to_login button:active,
    div[data-testid="stButton"].st-key-back_to_login > button:hover,
    div[data-testid="stButton"].st-key-back_to_login > button:focus-visible,
    div[data-testid="stButton"].st-key-back_to_login > button:focus,
    div[data-testid="stButton"].st-key-back_to_login > button:active,
    div.st-key-go_signin button:hover,
    div.st-key-go_signin button:focus-visible,
    div.st-key-go_signin button:focus,
    div.st-key-go_signin button:active,
    div[data-testid="stButton"].st-key-go_signin > button:hover,
    div[data-testid="stButton"].st-key-go_signin > button:focus-visible,
    div[data-testid="stButton"].st-key-go_signin > button:focus,
    div[data-testid="stButton"].st-key-go_signin > button:active {{
        background-color: var(--button-hover-bg) !important;
        background: var(--button-hover-bg) !important;
        border-color: var(--button-hover-border) !important;
        box-shadow: var(--button-hover-shadow) !important;
        color: var(--button-text) !important;
        outline: none !important;
    }}
    div.st-key-back_from_sent button:hover *,
    div[data-testid="stButton"].st-key-back_from_sent > button:hover *,
    div.st-key-back_to_login button:hover *,
    div[data-testid="stButton"].st-key-back_to_login > button:hover *,
    div.st-key-go_signin button:hover *,
    div[data-testid="stButton"].st-key-go_signin > button:hover * {{
        color: var(--button-text) !important;
    }}

    /* Google OAuth button — rendered as an <a class="google-btn"> inside
       st.markdown. The default Streamlit markdown link styles win over a
       plain `.google-btn { ... }` rule (higher specificity on
       `[data-testid="stMarkdown"] a`), so we use the stAppViewContainer
       prefix and !important to anchor the styling. */
    [data-testid="stAppViewContainer"] a.google-btn,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdown"] a.google-btn {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 12px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        background: {t["google_bg"]} !important;
        color: {t["google_text"]} !important;
        border: 1px solid {t["google_border"]} !important;
        border-radius: 12px !important;
        padding: 0.62rem 1rem !important;
        min-height: 2.4rem !important;
        font-size: 0.94rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        letter-spacing: 0.005em !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06) !important;
        transition: background-color 0.15s ease, border-color 0.15s ease,
                    box-shadow 0.15s ease, transform 0.12s ease !important;
        cursor: pointer !important;
    }}
    [data-testid="stAppViewContainer"] a.google-btn:hover,
    [data-testid="stAppViewContainer"] a.google-btn:focus-visible,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdown"] a.google-btn:hover,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdown"] a.google-btn:focus-visible {{
        background: {t["google_bg"]} !important;
        color: {t["google_text"]} !important;
        border-color: {t["tab_active_border"]} !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.10),
                    0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-1px) !important;
        outline: none !important;
        text-decoration: none !important;
    }}
    [data-testid="stAppViewContainer"] a.google-btn:active {{
        transform: translateY(0) !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
    }}
    [data-testid="stAppViewContainer"] a.google-btn svg {{
        flex-shrink: 0 !important;
        width: 18px !important;
        height: 18px !important;
    }}
    /* Streamlit may wrap the anchor's text in a child <p>; keep it inline
       and inheriting the button's typography. */
    [data-testid="stAppViewContainer"] a.google-btn > *,
    [data-testid="stAppViewContainer"] a.google-btn p {{
        margin: 0 !important;
        padding: 0 !important;
        color: inherit !important;
        font: inherit !important;
        text-decoration: none !important;
        background: transparent !important;
    }}
    .or-divider {{
        display: flex;
        align-items: center;
        gap: 10px;
        color: {t["divider_text"]};
        font-size: 0.86rem;
        font-weight: 600;
        margin: 0.14rem 0;
    }}
    .or-divider::before, .or-divider::after {{
        content: "";
        flex: 1;
        height: 1px;
        background: {t["divider"]};
    }}

    .auth-footer {{
        text-align: center;
        color: {t["footer"]};
        font-size: 0.74rem;
        margin-top: 0.02rem;
    }}

    @media (max-width: 900px) {{
        .st-key-auth_shell {{
            margin-top: 0.75rem !important;
            border-radius: 18px !important;
            padding: 0.78rem 0.72rem 0.95rem 0.72rem !important;
        }}
        /* Hide the value-prop panel on narrow screens — form takes the full
           width so it remains usable without scrolling. */
        .auth-brand-panel {{
            display: none !important;
        }}
        .st-key-auth_shell [data-testid="stHorizontalBlock"] > div:first-child {{
            display: none !important;
        }}
        .st-key-auth_shell [data-testid="stHorizontalBlock"] > div:last-child {{
            width: 100% !important;
            flex: 1 1 100% !important;
        }}
        .st-key-auth_surface,
        .st-key-auth_surface_forgot,
        .st-key-auth_surface_reset {{
            padding: 1.05rem 0.9rem 0.95rem 0.9rem !important;
            border-radius: 16px !important;
        }}
        .st-key-auth_surface {{
            min-height: auto !important;
        }}
    }}
    </style>
    """
    ).strip()


def render_auth_page(theme: str = "light") -> None:
    t = _DARK if theme == "dark" else _LIGHT
    st.markdown(_base_css(t), unsafe_allow_html=True)

    if st.query_params.get("auth_view") == "forgot_password":
        st.session_state["auth_view"] = "forgot_password"

    logo_uri = _logo_data_uri()
    logo_html = (
        f'<img src="{logo_uri}" alt="ExcelCV" class="auth-brand-logo" />'
        if logo_uri
        else '<span class="auth-brand-wordmark">ExcelCV</span>'
    )

    with st.container(key="auth_shell"):
        cols = st.columns([1, 1], gap="large")

        with cols[0]:
            st.markdown(
                f"""
                <div class="auth-brand-panel">
                    <div class="auth-brand-header">{logo_html}</div>
                    <span class="auth-brand-eyebrow">Welcome to ExcelCV</span>
                    <h1 class="auth-brand-title">Build a resume that gets you hired.</h1>
                    <ul class="auth-brand-features">
                        <li>
                            <span class="auth-feature-icon">&#10003;</span>
                            <div>
                                <strong>AI-powered scoring</strong>
                                <span>Explainable, ATS-aware feedback on every resume in seconds.</span>
                            </div>
                        </li>
                        <li>
                            <span class="auth-feature-icon">&#10003;</span>
                            <div>
                                <strong>Compare side-by-side</strong>
                                <span>Rank multiple resumes against the same job description.</span>
                            </div>
                        </li>
                        <li>
                            <span class="auth-feature-icon">&#10003;</span>
                            <div>
                                <strong>Resume Builder</strong>
                                <span>Build, preview, and export polished CVs in three templates.</span>
                            </div>
                        </li>
                        <li>
                            <span class="auth-feature-icon">&#10003;</span>
                            <div>
                                <strong>Cover Letter Generator</strong>
                                <span>Draft tailored cover letters grounded in your resume.</span>
                            </div>
                        </li>
                        <li>
                            <span class="auth-feature-icon">&#10003;</span>
                            <div>
                                <strong>Save your progress</strong>
                                <span>Build, save, and revisit your CVs and analyses anytime.</span>
                            </div>
                        </li>
                    </ul>
                    <div class="auth-howitworks">
                        <span class="auth-howitworks-label">How it works</span>
                        <ol class="auth-howitworks-steps">
                            <li>
                                <span class="auth-step-num">1</span>
                                <span class="auth-step-text">Upload your resume and paste the job description.</span>
                            </li>
                            <li>
                                <span class="auth-step-num">2</span>
                                <span class="auth-step-text">Get a scored report with keyword gaps and rewrites.</span>
                            </li>
                            <li>
                                <span class="auth-step-num">3</span>
                                <span class="auth-step-text">Build, refine, and export the final version.</span>
                            </li>
                        </ol>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col_form = cols[1]

        if st.session_state.get("oauth_error"):
            with col_form:
                st.error(st.session_state.pop("oauth_error"))

        reset_token = st.session_state.get("reset_token")
        if reset_token:
            _render_reset_password_form(col_form, reset_token, t)
        elif st.session_state.get("auth_view") == "forgot_password":
            _render_forgot_password_form(col_form, t)
        else:
            _render_sign_in_register(col_form, t)


def _render_sign_in_register(col, t: dict) -> None:
    with col:
        with st.container(key="auth_surface"):
            st.markdown(
                """
                <div class="auth-surface-head">
                    <h3 class="auth-surface-title">Sign in or create your account</h3>
                    <p class="auth-surface-subtitle">
                        Continue to upload resumes, compare analyses, and keep your progress organized.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if is_google_oauth_configured():
                oauth_state = create_oauth_state_token(next_page=_resolve_post_login_target())
                google_url = build_google_auth_url(state=oauth_state)
                st.markdown(
                    f'<a href="{google_url}" target="_self" class="google-btn">'
                    f"{_GOOGLE_SVG} Continue with Google</a>",
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="or-divider">or</div>', unsafe_allow_html=True)

            tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

            with tab_login:
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", placeholder="********")
                    # Inline forgot-password link: right-aligned, sits between
                    # the password field and the Sign In submit so users see
                    # it at the exact moment they realise they don't remember
                    # their password. URL flips auth_view via query param —
                    # already handled at the top of render_auth_page().
                    forgot_href = _build_page_href("auth", next_page=_resolve_post_login_target())
                    forgot_href = forgot_href + ("&" if "?" in forgot_href else "?") + "auth_view=forgot_password"
                    st.markdown(
                        f'<div class="auth-forgot-row">'
                        f'<a href="{forgot_href}" target="_self" class="auth-forgot-link">'
                        f'Forgot your password?</a></div>',
                        unsafe_allow_html=True,
                    )
                    submitted = st.form_submit_button("Sign In", width="stretch", type="primary")

                if submitted:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state["ui_toast"] = {
                                "message": "Signed in successfully.",
                                "icon": "✅",
                            }
                            redirect_to = _resolve_post_login_target()
                            _redirect_after_login(user, redirect_to)
                        else:
                            st.error("Invalid email or password.")

            with tab_register:
                with st.form("register_form"):
                    full_name = st.text_input("Full Name", placeholder="Your Name")
                    reg_email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
                    reg_pass = st.text_input(
                        "Password (min. 8 chars)",
                        type="password",
                        placeholder="********",
                        key="reg_pass",
                    )
                    submitted_reg = st.form_submit_button(
                        "Create Account",
                        width="stretch",
                        type="primary",
                    )

                if submitted_reg:
                    if not full_name or not reg_email or not reg_pass:
                        st.error("Please fill in all fields.")
                    elif "@" not in reg_email or "." not in reg_email.split("@", 1)[-1]:
                        st.error("Enter a valid email address (e.g. you@example.com).")
                    else:
                        user, err = create_user(full_name, reg_email, reg_pass)
                        if err:
                            st.error(err)
                        else:
                            st.session_state["ui_toast"] = {
                                "message": "Account created successfully.",
                                "icon": "🎉",
                            }
                            redirect_to = _resolve_post_login_target()
                            _redirect_after_login(user, redirect_to)


def _render_forgot_password_form(col, t: dict) -> None:
    with col:
        with st.container(key="auth_surface_forgot"):
            st.markdown(
                """
                <div class="auth-surface-head">
                    <h3 class="auth-surface-title">Reset your password</h3>
                    <p class="auth-surface-subtitle">
                        Enter your account email and we will send you a secure reset link.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("reset_email_sent"):
                st.success(
                    "If that email is registered, a reset link has been sent. "
                    "Check your inbox and spam folder."
                )
                if st.button("Back to Sign In", key="back_from_sent", type="primary"):
                    st.session_state.pop("reset_email_sent", None)
                    st.session_state.pop("auth_view", None)
                    if "auth_view" in st.query_params:
                        del st.query_params["auth_view"]
                    st.rerun()
                return

            with st.form("forgot_form"):
                fp_email = st.text_input("Email", placeholder="you@example.com", key="fp_email")
                send_btn = st.form_submit_button("Send reset link", width="stretch", type="primary")

            if send_btn:
                if not fp_email:
                    st.error("Please enter your email address.")
                elif not is_email_configured():
                    st.warning(
                        "Email is not configured on this server. "
                        "Set SMTP_USER and SMTP_PASSWORD in .env (or .env.example for local fallback)."
                    )
                else:
                    raw_token = create_password_reset_token(fp_email.strip())
                    if raw_token:
                        send_password_reset_email(fp_email.strip(), raw_token, _APP_URL)
                    # Always show the same message to prevent email enumeration
                    st.session_state["ui_toast"] = {
                        "message": "If this email is registered, reset mail has been sent.",
                        "icon": "📨",
                    }
                    st.session_state["reset_email_sent"] = True
                    st.rerun()

            if st.button("Back to Sign In", key="back_to_login", type="primary"):
                st.session_state.pop("auth_view", None)
                if "auth_view" in st.query_params:
                    del st.query_params["auth_view"]
                st.rerun()


def _render_reset_password_form(col, reset_token: str, t: dict) -> None:
    with col:
        with st.container(key="auth_surface_reset"):
            st.markdown(
                """
                <div class="auth-surface-head">
                    <h3 class="auth-surface-title">Set a new password</h3>
                    <p class="auth-surface-subtitle">
                        Choose a strong password to secure your ExcelCV account.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("reset_form"):
                new_pass = st.text_input(
                    "New password (min. 8 chars)",
                    type="password",
                    placeholder="********",
                    key="rp_new",
                )
                confirm_pass = st.text_input(
                    "Confirm new password",
                    type="password",
                    placeholder="********",
                    key="rp_confirm",
                )
                reset_btn = st.form_submit_button("Set new password", width="stretch", type="primary")

            if reset_btn:
                if not new_pass or not confirm_pass:
                    st.error("Please fill in both fields.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    ok, err = use_password_reset_token(reset_token, new_pass)
                    if ok:
                        st.session_state.pop("reset_token", None)
                        st.success("Password updated. You can now sign in with your new password.")
                        if st.button("Go to Sign In", key="go_signin", type="primary"):
                            st.session_state["page"] = "auth"
                            st.rerun()
                    else:
                        st.error(err)
                        if "expired" in err.lower() or "invalid" in err.lower():
                            st.session_state.pop("reset_token", None)


