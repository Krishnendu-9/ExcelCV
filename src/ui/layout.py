"""Site-wide layout components: top nav header, footer, and theme toggle."""

import json
import threading
from datetime import datetime
from typing import List

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.email_utils import is_email_configured, send_acknowledgement_email, send_contact_email
from src.ui.app_utils import _build_page_href, _load_logo_data_uri

PROTECTED_HEADER_PAGES = {"resume-builder", "my-cvs", "my-analyses", "compare-cv"}
NAV_LABEL_TO_PAGE = {
    "Analyze CV": "upload-cv",
    "Compare Resumes": "compare-cv",
    "Cover Letter": "cover-letter",
    "Resume Builder": "resume-builder",
    "My CVs": "my-cvs",
    "My Analyses": "my-analyses",
    "My Comparisons": "my-comparisons",
}
NAV_ITEMS = [
    ("Analyze CV", "upload-cv"),
    ("Compare Resumes", "compare-anchor"),
    ("Resume Builder", "resume-builder"),
    ("Cover Letter", "cover-letter"),
    ("My CVs", "my-cvs"),
    ("My Analyses", "my-analyses"),
    ("My Comparisons", "my-comparisons"),
]
# Page keys that need a hidden bridge button so the user-dropdown <a> tags
# can route through Streamlit's in-app nav (preserving session_state)
# instead of triggering a full-page reload. These do NOT render as visible
# top-nav items — only their bridge buttons are emitted.
DROPDOWN_NAV_ITEMS = [
    "give-feedback",
    "support",
    "settings",
]


def _nav_action_button_key(action: str) -> str:
    """Return a stable widget key for JS-triggered nav action bridge buttons."""
    normalized = "".join(ch if ch.isalnum() else "_" for ch in str(action).strip().lower())
    return f"nav_action_{normalized}"


def _nav_action_css_class(action: str) -> str:
    """Return the CSS class used by Streamlit for a nav action button key."""
    normalized = "".join(ch if ch.isalnum() else "_" for ch in str(action).strip().lower())
    return f"st-key-nav_action_{normalized}"


def _queue_nav_action(action: str) -> None:
    """Persist the most recent nav action so header highlight can update immediately."""
    st.session_state["nav_action_pending"] = str(action)


def _open_feedback_dialog() -> None:
    """Mark the feedback modal as open and reset any prior submit state.

    Streamlit only allows one open dialog per script run, so opening Feedback
    must also tear down any stale Support flag (e.g. left True after the user
    X-dismissed the Support modal earlier).
    """
    st.session_state["support_dialog_open"] = False
    st.session_state["feedback_dialog_open"] = True
    st.session_state.pop("feedback_sent", None)


def _open_support_dialog() -> None:
    """Mark the support modal as open. Tears down any stale Feedback flag for
    the same mutual-exclusion reason as :func:`_open_feedback_dialog`."""
    st.session_state["feedback_dialog_open"] = False
    st.session_state.pop("feedback_sent", None)
    st.session_state["support_dialog_open"] = True


@st.dialog("Support")
def _support_dialog() -> None:
    """Lightweight support modal — shows the support email + an Open Mail App
    button. No form: routes the user to their own mail client so we never
    intercept what's meant for a direct reply. The 'always-visible copy button'
    rule lives in base_theme.css.tpl as a global override."""
    st.session_state["support_dialog_open"] = False
    st.write("We'll get back to you as soon as possible.")
    st.code("support@excelcv.app", language=None)
    st.link_button(
        "Open mail app",
        "mailto:support@excelcv.app?subject=ExcelCV%20Support%20Request",
        type="primary",
        width="stretch",
    )


@st.dialog("Send feedback")
def _feedback_dialog() -> None:
    """Lightweight feedback modal — single textarea, ships to support inbox."""
    if st.session_state.get("feedback_sent"):
        st.markdown("#### Thank you for your feedback")
        st.write(
            "We've received your message. Our team reviews every submission "
            "and will get back to you if a response is needed."
        )
        if st.button("Close", key="feedback_close_btn", type="primary", width="stretch"):
            st.session_state["feedback_dialog_open"] = False
            st.session_state.pop("feedback_sent", None)
            st.session_state.pop("feedback_message_input", None)
            st.rerun()
        return

    user = get_session_user() or {}
    st.write("Help us improve ExcelCV. We read every message.")
    message = st.text_area(
        "Your feedback",
        key="feedback_message_input",
        height=160,
        label_visibility="collapsed",
        placeholder="Share a feature idea, a bug, or any thought...",
    )

    if st.button("Send feedback", key="feedback_send_btn", type="primary", width="stretch"):
        text = (message or "").strip()
        if not text:
            st.warning("Please type a message before sending.")
        elif not is_email_configured():
            st.error(
                "We couldn't send your feedback right now. "
                "Please email support@excelcv.app directly."
            )
        else:
            user_name = str(user.get("full_name") or "ExcelCV user")
            user_email = str(user.get("email") or "")
            ok = send_contact_email(
                name=user_name,
                reply_to=user_email or "noreply@excelcv.app",
                inquiry="Feedback",
                subject="ExcelCV Feedback",
                message=text,
            )
            if ok:
                # Best-effort acknowledgement back to the submitter — fire it
                # off in a background daemon thread so the user doesn't wait
                # for a second SMTP roundtrip before seeing the thank-you
                # screen. The ack is a courtesy; the inbox notification (above)
                # is what actually matters.
                if user_email:
                    threading.Thread(
                        target=send_acknowledgement_email,
                        args=(user_email, user_name, "Feedback", text),
                        daemon=True,
                    ).start()
                # Flip to thank-you branch. st.rerun() closes the dialog, then
                # the top-level `if feedback_dialog_open: _feedback_dialog()`
                # immediately reopens it on the next render — this time with
                # feedback_sent=True, so the thank-you branch renders.
                st.session_state["feedback_sent"] = True
                st.rerun()
            else:
                st.error(
                    "We couldn't send your feedback right now. "
                    "Please email support@excelcv.app directly."
                )


def _render_html_block(html: str) -> None:
    """Render HTML reliably across Streamlit versions/runtimes."""
    st.markdown(html, unsafe_allow_html=True)


def render_theme_toggle(standalone: bool = True, key: str = "theme_toggle") -> None:
    """Render the theme switch button. If standalone=False, only the button (for use inside a column)."""
    if standalone:
        col_spacer, col_btn = st.columns([6, 1], gap="small")
        container = col_btn
    else:
        container = st.container()
    with container:
        current_theme = st.session_state.get("theme", "light")
        theme_icon = "\U0001f319" if current_theme == "light" else "\u2600\ufe0f"
        if st.button(
            theme_icon,
            key=key,
            width="stretch" if standalone else "content",
        ):
            new_theme = "dark" if current_theme == "light" else "light"
            st.session_state["theme"] = new_theme
            # The button click itself triggers a Streamlit rerun — no explicit st.rerun()
            # needed. Calling st.rerun() here stops execution before the form widgets
            # below are processed, causing typed values to be lost.


def render_site_header(show_theme_toggle: bool = True, current_page: str = "upload") -> str | None:
    """Render top branded header. Auth links are plain HTML — no nested st.columns."""
    _user = get_session_user()

    # Layout: brand | nav-left | user-right | theme
    if show_theme_toggle:
        col_brand, col_nav, col_user, col_theme = st.columns([1.1, 3.2, 1.2, 0.55], gap="small")
    else:
        col_brand, col_nav, col_user = st.columns([1.1, 3.2, 1.75], gap="small")
        col_theme = None

    # Render the theme toggle FIRST so its button click handler runs before we
    # read st.session_state["theme"] to build nav-link / logo / user-menu URLs.
    # Otherwise a same-render toggle (light→dark) would leave every URL on the
    # page baked with the OLD ?_t value, which the fallback navigation path
    # would carry through to the next session — flipping the theme back.
    if show_theme_toggle and col_theme is not None:
        with col_theme:
            _render_html_block('<div class="theme-toggle-gap" aria-hidden="true"></div>')
            render_theme_toggle(standalone=False, key="theme_toggle_header")

    logo_src = _load_logo_data_uri(st.session_state.get("theme", "light"))
    logo_content_html = (
        f'<img src="{logo_src}" alt="ExcelCV logo" class="site-logo-wordmark" />'
        if logo_src
        else '<div class="site-logo-badge">EC</div><div class="site-brand-copy"><div class="site-name">ExcelCV</div></div>'
    )
    _cur_theme = st.session_state.get("theme", "light")
    logo_target_url = f"/?page=home&_clear=1&_t={_cur_theme}"
    logo_html = (
        f'<a href="{logo_target_url}" target="_self" class="site-logo-link" aria-label="Go to homepage">'
        f'<div class="site-logo-shell">{logo_content_html}</div></a>'
    )

    with col_brand:
        _render_html_block(f'<div class="site-brand">{logo_html}</div>')

    nav_items = NAV_ITEMS
    pending_action = str(st.session_state.get("nav_action_pending", "")).strip()
    if current_page in ("upload", "home", "upload-cv"):
        active_page = "upload-cv"
    elif current_page == "report":
        active_page = "upload-cv"
    else:
        active_page = current_page
    if pending_action == "compare-anchor":
        active_page = "compare-cv"
    elif pending_action in {item[1] for item in nav_items}:
        active_page = pending_action

    nav_links: List[str] = []
    for label, page_key in nav_items:
        is_active = page_key == active_page or (
            page_key == "compare-anchor" and active_page == "compare-cv"
        )
        active_cls = " site-nav-item-active" if is_active else ""
        if page_key == "compare-anchor":
            href = _build_page_href("home") + "#compare-section-anchor"
        elif not _user and page_key in PROTECTED_HEADER_PAGES:
            href = _build_page_href("auth", next_page=page_key)
        else:
            href = _build_page_href(page_key)
        nav_links.append(
            f'<a href="{href}" target="_self" '
            f'onclick="try{{var w=window.parent&&window.parent!==window?window.parent:window;'
            f"var b=w.document.querySelector('.{_nav_action_css_class(page_key)} button');"
            f'if(b){{event.preventDefault();event.stopPropagation();b.click();return false;}}}}catch(_e){{}}" '
            f'class="site-nav-item{active_cls}" data-nav-action="{page_key}" style="text-decoration:none;">{label}</a>'
        )

    with col_nav:
        _render_html_block('<div class="site-nav site-nav-left">' + "".join(nav_links) + "</div>")

    # Normalize nav active classes on every render so stale client-side mutations
    # from other pages (e.g. home scroll-spy) cannot leak into this page.
    components.html(
        f"""<script>
(function() {{
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;
  var active = {json.dumps(active_page)};
  var homeLikeNav = active === 'upload-cv' || active === 'compare-cv';
  if (!homeLikeNav && w.__excelcv_compare_spy_observer__) {{
    try {{ w.__excelcv_compare_spy_observer__.disconnect(); }} catch (_e) {{}}
    w.__excelcv_compare_spy_observer__ = null;
  }}
  var items = doc.querySelectorAll('a.site-nav-item[data-nav-action]');
  if (!items || !items.length) return;
  for (var i = 0; i < items.length; i++) {{
    var el = items[i];
    var action = String(el.getAttribute('data-nav-action') || '');
    var isActive = (action === active) || (action === 'compare-anchor' && active === 'compare-cv');
    el.classList.toggle('site-nav-item-active', !!isActive);
  }}
}})();
</script>""",
        height=0,
    )

    # User section: FlowCV-style dropdown when logged in, Sign In button when not.
    _ICON_FEEDBACK = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" class="site-user-item-icon" aria-hidden="true">'
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
    )
    _ICON_SUPPORT = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" class="site-user-item-icon" aria-hidden="true">'
        '<rect x="2" y="4" width="20" height="16" rx="2"/>'
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>'
    )
    _ICON_SETTINGS = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" class="site-user-item-icon" aria-hidden="true">'
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08'
        "a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74"
        "l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25"
        "a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25"
        "a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08"
        "a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38"
        'a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/></svg>'
    )
    _ICON_LOGOUT = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" class="site-user-item-icon" aria-hidden="true">'
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" y1="12" x2="9" y2="12"/></svg>'
    )
    if _user:
        raw_full_name = str(_user.get("full_name", "")).strip()
        name_tokens = [token for token in raw_full_name.replace(",", " ").split() if token.strip()]
        first_name = (name_tokens[0] if name_tokens else "User")[:18]

        def _dropdown_link(page_key: str, icon: str, label: str, extra_class: str = "") -> str:
            """Build a dropdown <a> that routes through the global nav-action bridge."""
            # Modal-only items should never hard-navigate.
            if page_key == "give-feedback":
                href = "#"
            elif page_key == "support":
                href = "#"
            else:
                href = _build_page_href(page_key)
            # The bridge button can be missing from DOM for a noticeable
            # window after Streamlit tears down a dialog with st.rerun() — up
            # to a second in practice. Retry generously (20 × 100ms = 2s)
            # before falling back to URL nav, and trigger the click via a
            # full MouseEvent dispatch (more reliable than .click() for
            # React's synthetic event system, which sometimes ignores .click()
            # invocations on freshly remounted widgets).
            cls = f"site-user-item{(' ' + extra_class) if extra_class else ''}"
            return (
                f'<a href="{href}" target="_self" class="{cls}" '
                f'data-nav-action="{page_key}">{icon}{label}</a>'
            )

        user_section_html = (
            '<details class="site-user-dropdown">'
            f'<summary class="site-user-trigger">Hi, {first_name}<span class="site-user-caret">&#9662;</span></summary>'
            '<div class="site-user-panel">'
            + _dropdown_link("give-feedback", _ICON_FEEDBACK, "Give Feedback")
            + _dropdown_link("support", _ICON_SUPPORT, "Support")
            + _dropdown_link("settings", _ICON_SETTINGS, "Settings")
            # Logout intentionally keeps a hard nav: the ``?_logout=1`` query
            # param is handled in main() before any page render to clear the
            # session and cookie, so we want the new HTTP request that a real
            # navigation produces.
            + f'<a href="/?_logout=1&_t={_cur_theme}" target="_self" class="site-user-item site-user-item-logout">{_ICON_LOGOUT}Logout</a>'
            + "</div>"
            "</details>"
        )
    else:
        next_after_auth = (
            current_page
            if current_page
            in (
                "home",
                "upload",
                "upload-cv",
                "compare-cv",
                "resume-builder",
                "my-cvs",
                "my-analyses",
            )
            else "home"
        )
        user_section_html = (
            f'<a href="{_build_page_href("auth", next_page=next_after_auth)}" target="_self" '
            f'class="site-nav-item site-nav-item-signin" style="text-decoration:none;white-space:nowrap;">Sign In</a>'
        )

    with col_user:
        _render_html_block(f'<div class="site-user-section">{user_section_html}</div>')

    nav_action: str | None = None
    with st.container(key="site_nav_action_bridge"):
        for _, page_key in nav_items:
            if st.button(
                " ",
                key=_nav_action_button_key(page_key),
                help=f"Internal navigation trigger for {page_key}",
                on_click=_queue_nav_action,
                args=(page_key,),
            ):
                nav_action = page_key
        # Bridge buttons for the user-dropdown items. Same mechanism, just
        # not rendered as visible nav links — they exist so the dropdown
        # <a> tags' onclick handler can find a Streamlit button to click,
        # keeping the click in-app instead of triggering a hard reload.
        for page_key in DROPDOWN_NAV_ITEMS:
            # Modal-only items: bridge button fires a dedicated callback that
            # flips a session flag, instead of queuing a page navigation.
            if page_key == "give-feedback":
                st.button(
                    " ",
                    key=_nav_action_button_key(page_key),
                    help="Internal trigger for the feedback modal",
                    on_click=_open_feedback_dialog,
                )
                continue
            if page_key == "support":
                st.button(
                    " ",
                    key=_nav_action_button_key(page_key),
                    help="Internal trigger for the support modal",
                    on_click=_open_support_dialog,
                )
                continue
            if st.button(
                " ",
                key=_nav_action_button_key(page_key),
                help=f"Internal navigation trigger for {page_key}",
                on_click=_queue_nav_action,
                args=(page_key,),
            ):
                nav_action = page_key

    # Mutually exclusive — Streamlit can only render one dialog per script run.
    # `elif` is a safety net in case both flags somehow ended up True (e.g. a
    # callback path we didn't anticipate). Feedback takes precedence because it
    # might be mid-submission with thank-you state worth preserving.
    if st.session_state.get("feedback_dialog_open"):
        _feedback_dialog()
    elif st.session_state.get("support_dialog_open"):
        _support_dialog()

    _render_html_block('<div class="site-header-rule"></div>')
    return nav_action


def render_top_nav(active_page: str) -> str | None:
    """Render the shared global top navigation with the existing design."""
    normalized = NAV_LABEL_TO_PAGE.get(active_page, active_page)
    return render_site_header(show_theme_toggle=True, current_page=normalized)


def render_site_footer() -> None:
    """Render a full-width professional footer band for all pages."""
    year = datetime.now().year
    footer_theme_cls = (
        "footer-light" if st.session_state.get("theme", "light") == "light" else "footer-dark"
    )
    logo_src = _load_logo_data_uri(st.session_state.get("theme", "light"))
    footer_brand_heading = (
        f'<img src="{logo_src}" alt="ExcelCV logo" class="site-footer-brand-logo" />'
        if logo_src
        else '<div class="site-footer-brand-title">ExcelCV</div>'
    )
    is_guest = not get_session_user()
    # Product footer links act like deliberate deep-nav: route guests through
    # the auth gate (with a `next` hint so they bounce back) instead of letting
    # them land on the home/cover-letter page and see a guest shell.
    analyze_cv_href = (
        _build_page_href("auth", next_page="upload-cv") if is_guest else _build_page_href("home")
    )
    compare_resumes_href = (
        _build_page_href("auth", next_page="compare-cv")
        if is_guest
        else _build_page_href("home") + "#compare-section-anchor"
    )
    cover_letter_href = (
        _build_page_href("auth", next_page="cover-letter")
        if is_guest
        else _build_page_href("cover-letter")
    )
    footer_links = {
        "analyze_cv": analyze_cv_href,
        "compare_resumes": compare_resumes_href,
        "cover_letter": cover_letter_href,
        "resume_builder": _build_page_href("resume-builder"),
        "my_cvs": _build_page_href("my-cvs"),
        "my_analyses": _build_page_href("my-analyses"),
        "resume_tips": _build_page_href("resume-tips"),
        "cover_letter_guide": _build_page_href("cover-letter-guide"),
        "how_it_works": _build_page_href("how-it-works"),
        "privacy_policy": _build_page_href("privacy-policy"),
        "terms_of_service": _build_page_href("terms-of-service"),
        "contact": _build_page_href("contact"),
    }

    footer_html = f"""
    <footer class="site-footer-band {footer_theme_cls}" role="contentinfo" aria-label="Website footer">
        <div class="site-footer-inner">
            <div class="site-footer-grid">
                <div class="site-footer-brand-col">
                    {footer_brand_heading}
                    <p class="site-footer-brand-text">
                        AI-powered resume analysis and actionable feedback to help you land your target role faster.
                    </p>
                </div>
                <div class="site-footer-links-grid">
                    <div class="site-footer-link-col site-footer-link-col--wide">
                        <h4>Product</h4>
                        <div class="site-footer-link-grid-2col">
                            <a href="{footer_links["analyze_cv"]}" target="_self">Analyze CV</a>
                            <a href="{footer_links["resume_builder"]}" target="_self">Resume Builder</a>
                            <a href="{footer_links["compare_resumes"]}" target="_self">Compare Resumes</a>
                            <a href="{footer_links["my_cvs"]}" target="_self">My CVs</a>
                            <a href="{footer_links["cover_letter"]}" target="_self">Cover Letter</a>
                            <a href="{footer_links["my_analyses"]}" target="_self">My Analyses</a>
                        </div>
                    </div>
                    <div class="site-footer-link-col">
                        <h4>Resources</h4>
                        <a href="{footer_links["resume_tips"]}" target="_self">Resume Tips</a>
                        <a href="{footer_links["cover_letter_guide"]}" target="_self">Cover Letter Guide</a>
                        <a href="{footer_links["how_it_works"]}" target="_self">How It Works</a>
                    </div>
                    <div class="site-footer-link-col">
                        <h4>Legal</h4>
                        <a href="{footer_links["privacy_policy"]}" target="_self">Privacy Policy</a>
                        <a href="{footer_links["terms_of_service"]}" target="_self">Terms of Service</a>
                        <a href="{footer_links["contact"]}" target="_self">Contact Us</a>
                    </div>
                </div>
            </div>
            <div class="site-footer-bottom">
                <span>&copy; {year} ExcelCV. All rights reserved.</span>
                <span class="site-footer-sep">&bull;</span>
                <span>Built for educational and portfolio demonstration purposes.</span>
            </div>
        </div>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
