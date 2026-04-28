"""Login / Register / Forgot-Password page for the Streamlit app."""

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import (
    _COOKIE_NAME,
    _SESSION_SECONDS,
    authenticate_user,
    create_password_reset_token,
    create_session_token,
    create_user,
    login_user,
    use_password_reset_token,
)
from src.email_utils import is_email_configured, send_password_reset_email
from src.oauth_utils import GOOGLE_REDIRECT_URI as _APP_URL
from src.oauth_utils import build_google_auth_url, is_google_oauth_configured


def _logo_data_uri() -> str:
    base_dir = Path(__file__).resolve().parent.parent.parent / "templates"
    for name in ("ExcelCV_clean.png", "ExcelCV.png"):
        p = base_dir / name
        if p.exists():
            return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
    return ""


def _set_session_cookie(user_dict: dict) -> None:
    token = create_session_token(user_dict)
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}={token}; max-age={_SESSION_SECONDS}; path=/; SameSite=Lax";</script>',
        height=0,
    )


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
    return f"""
    <style>
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    .stMainBlockContainer {{
        background: {t["bg"]} !important;
    }}

    [data-testid="stAppViewContainer"] .main .block-container {{
        max-width: 1240px !important;
        height: 100dvh !important;
        min-height: 0 !important;
        box-sizing: border-box !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        overflow: hidden !important;
    }}

    .st-key-auth_shell {{
        width: 100% !important;
        max-width: 100% !important;
        height: calc(100dvh - 12px) !important;
        min-height: 0 !important;
        margin: 0 auto !important;
        border-radius: 18px !important;
        border: 1px solid {t["hero_panel_border"]} !important;
        background: {t["hero_panel_bg"]} !important;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12) !important;
        padding: 0.44rem 0.9rem 0.38rem 0.9rem !important;
        box-sizing: border-box !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }}

    .st-key-auth_shell_top {{
        margin-bottom: 0.1rem !important;
    }}
    .st-key-auth_shell_top [data-testid="stVerticalBlock"] {{
        gap: 0 !important;
    }}
    .auth-top-header {{
        position: relative;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        min-height: 48px;
        padding-top: 0.02rem;
    }}
    .auth-top-logo {{
        position: absolute;
        left: 0;
        top: 0;
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }}
    .auth-top-logo img {{
        height: 44px;
        object-fit: contain;
    }}
    .auth-top-title {{
        margin: 0.12rem 0 0 0;
        color: {t["title"]};
        font-size: clamp(1.24rem, 2.2vw, 1.95rem);
        line-height: 1.08;
        font-weight: 800;
        text-align: center;
    }}

    .auth-hero-panel {{
        margin: 0 auto 0.16rem auto;
        max-width: 100%;
        border-radius: 20px;
        border: none;
        background: transparent;
        box-shadow: none;
        padding: 0.16rem 0.4rem 0.08rem;
        text-align: center;
    }}
    .auth-hero-title {{
        margin: 0.12rem 0 0.1rem 0;
        color: {t["title"]};
        font-size: clamp(1.2rem, 2.1vw, 1.85rem);
        line-height: 1.08;
        font-weight: 800;
    }}
    .auth-hero-subtitle {{
        margin: 0 auto;
        max-width: 740px;
        color: {t["subtitle"]};
        font-size: 0.82rem;
        line-height: 1.2;
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
        min-height: 31.5rem !important;
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
    div[data-testid="stTextInput"] input {{
        background: {t["input_bg"]} !important;
        color: {t["input_text"]} !important;
        caret-color: {t["input_text"]} !important;
        border: none !important;
        outline: none !important;
        font-size: 0.9rem !important;
        line-height: 1.2 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: {t["input_placeholder"]} !important;
        opacity: 1 !important;
    }}
    label, .stTextInput label {{
        color: {t["label"]} !important;
        font-weight: 700 !important;
    }}

    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] {{
        margin-right: 0.38rem !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] button,
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] [role="button"] {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: auto !important;
        height: auto !important;
        min-height: 0 !important;
        padding: 0.06rem !important;
        border: none !important;
        border-radius: 0 !important;
        color: {t["subtitle"]} !important;
        background: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        appearance: none !important;
        cursor: pointer !important;
        transition: color 0.15s !important;
    }}
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] button:hover,
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] [role="button"]:hover {{
        color: {t["tab_active_text"]} !important;
        background: transparent !important;
    }}
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] button:focus-visible,
    div[data-testid="stTextInput"] [data-baseweb="input-icon-container"] [role="button"]:focus-visible {{
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.22) !important;
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
    div[data-testid="stFormSubmitButton"] button,
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 800 !important;
        min-height: 2.08rem !important;
    }}
    /* Match non-submit auth actions to the Sign In submit button style */
    div.st-key-forgot_btn_inline button,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button,
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
    div.st-key-forgot_btn_inline button:hover,
    div.st-key-forgot_btn_inline button:focus-visible,
    div.st-key-forgot_btn_inline button:focus,
    div.st-key-forgot_btn_inline button:active,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button:hover,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button:focus-visible,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button:focus,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button:active,
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
    div.st-key-forgot_btn_inline button:hover *,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button:hover *,
    div.st-key-back_from_sent button:hover *,
    div[data-testid="stButton"].st-key-back_from_sent > button:hover *,
    div.st-key-back_to_login button:hover *,
    div[data-testid="stButton"].st-key-back_to_login > button:hover *,
    div.st-key-go_signin button:hover *,
    div[data-testid="stButton"].st-key-go_signin > button:hover * {{
        color: var(--button-text) !important;
    }}

    .google-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: {t["google_bg"]};
        color: {t["google_text"]};
        border: 1px solid {t["google_border"]};
        border-radius: 10px;
        padding: 0.36rem 0.72rem;
        font-size: 0.84rem;
        font-weight: 700;
        text-decoration: none;
        width: 100%;
        box-sizing: border-box;
        transition: box-shadow 0.15s, border-color 0.15s;
    }}
    .google-btn:hover {{
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.16);
        border-color: {t["tab_active_border"]};
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

    .auth-inline-actions {{
        margin-top: 0.12rem;
        display: flex;
        justify-content: flex-end;
    }}
    .st-key-auth-inline-actions {{
        display: flex !important;
        justify-content: flex-end !important;
    }}
    div.st-key-forgot_btn_inline button,
    div[data-testid="stButton"].st-key-forgot_btn_inline > button {{
        white-space: nowrap !important;
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
        .auth-hero-panel {{
            margin-top: 0;
            padding: 0.7rem 0.45rem 0.62rem;
            border-radius: 14px;
        }}
        .auth-hero-subtitle {{
            font-size: 0.98rem;
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


def render_auth_page(theme: str = "light") -> None:
    t = _DARK if theme == "dark" else _LIGHT
    st.markdown(_base_css(t), unsafe_allow_html=True)

    if st.query_params.get("auth_view") == "forgot_password":
        st.session_state["auth_view"] = "forgot_password"

    logo_uri = _logo_data_uri()
    logo_html = (
        f'<img src="{logo_uri}" alt="ExcelCV" />'
        if logo_uri
        else '<span style="color:#2563eb;font-size:2rem;font-weight:800;">ExcelCV</span>'
    )

    with st.container(key="auth_shell"):
        with st.container(key="auth_shell_top"):
            st.markdown(
                f"""
                <div class="auth-top-header">
                    <div class="auth-top-logo">{logo_html}</div>
                    <h1 class="auth-top-title">Secure access to your resume workspace</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col_center = st.columns([0.75, 1.7, 0.75])[1]

        if st.session_state.get("oauth_error"):
            with col_center:
                st.error(st.session_state.pop("oauth_error"))

        reset_token = st.session_state.get("reset_token")
        if reset_token:
            _render_reset_password_form(col_center, reset_token, t)
        elif st.session_state.get("auth_view") == "forgot_password":
            _render_forgot_password_form(col_center, t)
        else:
            _render_sign_in_register(col_center, t)
        _render_footer(t)


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
                google_url = build_google_auth_url()
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
                    submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                with st.container(key="auth-inline-actions"):
                    forgot_cols = st.columns([0.6, 0.4])
                    with forgot_cols[1]:
                        if st.button(
                            "Forgot your password?",
                            key="forgot_btn_inline",
                            use_container_width=False,
                            type="primary",
                        ):
                            st.session_state["auth_view"] = "forgot_password"
                            st.query_params["auth_view"] = "forgot_password"
                            st.rerun()

                if submitted:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        user = authenticate_user(email, password)
                        if user:
                            login_user(user)
                            _set_session_cookie(user)
                            st.session_state["ui_toast"] = {
                                "message": "Signed in successfully.",
                                "icon": "✅",
                            }
                            redirect_to = st.session_state.pop("auth_redirect", "home")
                            st.session_state["page"] = redirect_to
                            st.query_params["page"] = redirect_to
                            st.rerun()
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
                        use_container_width=True,
                        type="primary",
                    )

                if submitted_reg:
                    if not full_name or not reg_email or not reg_pass:
                        st.error("Please fill in all fields.")
                    else:
                        user, err = create_user(full_name, reg_email, reg_pass)
                        if err:
                            st.error(err)
                        else:
                            login_user(user)
                            _set_session_cookie(user)
                            st.session_state["ui_toast"] = {
                                "message": "Account created successfully.",
                                "icon": "🎉",
                            }
                            redirect_to = st.session_state.pop("auth_redirect", "home")
                            st.session_state["page"] = redirect_to
                            st.query_params["page"] = redirect_to
                            st.rerun()


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
                send_btn = st.form_submit_button("Send reset link", use_container_width=True, type="primary")

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
                reset_btn = st.form_submit_button("Set new password", use_container_width=True, type="primary")

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


def _render_footer(t: dict) -> None:
    st.markdown(
        f'<p class="auth-footer">Your data is stored locally on this device. Nothing is shared externally.</p>',
        unsafe_allow_html=True,
    )
