"""
ExcelCV: GenAI-Powered CV Reviewer — Main Streamlit Application

Thin routing and session-orchestration layer.
All rendering logic lives in src/ui/*.
"""

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import (
    get_session_user,
    get_or_create_google_user,
    login_user,
    logout_user,
    set_session_cookie,
    restore_session_from_cookie,
    _COOKIE_NAME,
)
from src.database import init_db
from src.ui.app_utils import APP_PAGES, _clear_analysis_state, _restore_report_snapshot
from src.ui.auth_page import render_auth_page
from src.ui.css_injection import (
    inject_compact_header_css,
    inject_fixed_top_bar,
    inject_file_uploader_spacing_css,
    inject_footer_full_width,
)
try:
    from src.ui.css_injection import inject_header_layout_override, inject_dropdown_outside_click
except ImportError:
    def inject_header_layout_override() -> None:
        return None
    def inject_dropdown_outside_click() -> None:
        return None
from src.ui.layout import render_top_nav, render_site_footer
from src.ui.upload import render_upload_page
from src.ui.report import render_report_view
from src.ui.static_pages import render_static_page
from src.ui.cv_builder_page import render_cv_builder_page
from src.ui.my_cvs_page import render_my_cvs_page
from src.ui.my_analyses_page import render_my_analyses_page
from src.ui.settings_page import render_settings_page
from src.ui.ui_components import inject_back_button_sync, inject_base_css

PROTECTED_PAGES = {"cv-builder", "resume-builder", "my-cvs", "my-analyses", "compare-cv", "settings"}
NAV_ACTIVE_LABELS = {
    "home": "Analyze CV",
    "upload": "Analyze CV",
    "upload-cv": "Analyze CV",
    "report": "Analyze CV",
    "cv-builder": "Resume Builder",
    "resume-builder": "Resume Builder",
    "my-cvs": "My CVs",
    "my-analyses": "My Analyses",
    "compare-cv": "Compare",
}


def _query_params_dict() -> dict[str, str]:
    try:
        return dict(st.query_params.to_dict())
    except Exception:
        return {str(k): str(v) for k, v in st.query_params.items()}


def _set_query_params_atomic(params: dict[str, str]) -> None:
    """Set query params in one URL history operation when possible."""
    current = _query_params_dict()
    target = {str(k): str(v) for k, v in params.items()}
    if current == target:
        return
    try:
        st.query_params.from_dict(target)
    except Exception:
        st.query_params.clear()
        for key, value in target.items():
            st.query_params[key] = value


def _render_auth_gate(intended_page: str) -> None:
    """Render auth page immediately for protected routes when user is logged out."""
    st.session_state["auth_redirect"] = intended_page
    st.session_state["page"] = "auth"
    _theme = st.session_state.get("theme", "light")
    inject_base_css(_theme)
    render_auth_page(theme=_theme)
    _inject_theme_persistence(_theme)
    st.stop()


def _inject_theme_persistence(theme: str) -> None:
    """Sync theme to localStorage and install a click interceptor that carries it across navigations.

    On every page load this:
      1. Writes the current theme to localStorage so it survives session resets.
      2. Adds a one-time click listener on the parent window that appends ?_t=<theme>
         to every internal link click \u2014 Python reads _t on the next fresh session and
         cleans it immediately, so URLs stay tidy at rest.
      3. Strips any stale ?_t param from the current URL via history.replaceState.
    """
    safe_theme = "dark" if theme == "dark" else "light"
    components.html(
        f"""<script>
(function() {{
    var w = window.parent && window.parent !== window ? window.parent : window;
    w.localStorage.setItem('excelcv_theme', '{safe_theme}');
    var url = new URL(w.location.href);
    if (url.searchParams.has('_t')) {{
        url.searchParams.delete('_t');
        w.history.replaceState(null, '', url.toString());
    }}
    if (w._ecvThemeHooked) return;
    w._ecvThemeHooked = true;
    w.document.addEventListener('click', function(e) {{
        var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
        if (!a) return;
        try {{
            var u = new URL(a.href, w.location.origin);
            if (u.hostname !== w.location.hostname) return;
            var t = w.localStorage.getItem('excelcv_theme');
            if (t) {{ u.searchParams.set('_t', t); a.href = u.toString(); }}
        }} catch(ex) {{}}
    }}, true);
}})();
</script>""",
        height=0,
    )


def _inject_url_and_anchor_cleanup() -> None:
    """Keep URL clean and prevent hash-based mid-page reload jumps on home."""
    components.html(
        """<script>
(function () {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;

    try {
        var styleId = "excelcv-hide-heading-anchors";
        if (!doc.getElementById(styleId)) {
            var style = doc.createElement("style");
            style.id = styleId;
            style.textContent = "[data-testid='stHeaderActionElements']{display:none!important;}";
            (doc.head || doc.documentElement).appendChild(style);
        }
    } catch (e) {}

    try {
        var u = new URL(w.location.href);
        var page = (u.searchParams.get("page") || "").toLowerCase();
        var isHome = page === "home" || (page === "" && !u.searchParams.has("next"));
        var hadHash = !!u.hash;
        var changed = false;

        if (isHome && hadHash) {
            u.hash = "";
            changed = true;
        }

        // Canonical home URL: drop routing/theme transient params on home.
        if (isHome) {
            var keys = Array.from(u.searchParams.keys());
            var ignorable = new Set(["page", "_t", "theme", "_asset_reload"]);
            var onlyIgnorable = keys.length > 0 && keys.every(function (k) { return ignorable.has(k); });
            if (onlyIgnorable) {
                u.search = "";
                changed = true;
            }
        }

        if (changed) {
            var canonical = u.pathname + (u.search || "");
            w.history.replaceState(null, "", canonical);
        }

        if (isHome && hadHash) {
            try { w.scrollTo({ top: 0, left: 0, behavior: "instant" }); } catch (_e) { w.scrollTo(0, 0); }
            var main = doc.querySelector("[data-testid='stAppViewContainer']");
            if (main) {
                try { main.scrollTo({ top: 0, left: 0, behavior: "instant" }); } catch (_e2) { main.scrollTop = 0; }
            }
        }
    } catch (e) {}

})();
</script>""",
        height=0,
    )


def _inject_chunk_load_recovery() -> None:
    """Auto-recover once when browser fails to load Streamlit dynamic chunks."""
    components.html(
        """<script>
(function () {
    var w = window.parent && window.parent !== window ? window.parent : window;
    if (w.__excelcvChunkRecoveryInstalled) return;
    w.__excelcvChunkRecoveryInstalled = true;

    var RETRY_KEY = "excelcv_chunk_retry_ts";
    var RETRY_WINDOW_MS = 15000;

    function shouldRecover(msg) {
        if (!msg) return false;
        var text = String(msg);
        return (
            text.indexOf("Failed to fetch dynamically imported module") !== -1 ||
            text.indexOf("Importing a module script failed") !== -1 ||
            text.indexOf("ChunkLoadError") !== -1
        );
    }

    function recentlyRetried() {
        try {
            var prev = Number(w.sessionStorage.getItem(RETRY_KEY) || "0");
            return Number.isFinite(prev) && (Date.now() - prev) < RETRY_WINDOW_MS;
        } catch (e) {
            return false;
        }
    }

    function markRetried() {
        try {
            w.sessionStorage.setItem(RETRY_KEY, String(Date.now()));
        } catch (e) {}
    }

    function recover() {
        if (recentlyRetried()) return;
        markRetried();
        try {
            var u = new URL(w.location.href);
            u.searchParams.set("_asset_reload", String(Date.now()));
            w.location.replace(u.toString());
        } catch (e) {
            try { w.location.reload(); } catch (_e) {}
        }
    }

    w.addEventListener("error", function (evt) {
        var message = (evt && evt.message) || (evt && evt.error && evt.error.message) || "";
        if (shouldRecover(message)) recover();
    }, true);

    w.addEventListener("unhandledrejection", function (evt) {
        var reason = evt && evt.reason;
        var message = (reason && reason.message) || String(reason || "");
        if (shouldRecover(message)) recover();
    });
})();
</script>""",
        height=0,
    )


def _show_queued_toast() -> None:
    """Render a one-time toast queued in session state."""
    payload = st.session_state.pop("ui_toast", None)
    if not payload:
        return
    if isinstance(payload, dict):
        message = str(payload.get("message", "")).strip()
        icon = payload.get("icon")
    else:
        message = str(payload).strip()
        icon = None
    if not message:
        return
    try:
        st.toast(message, icon=icon)
    except Exception:
        st.success(message)



@st.cache_resource
def _init_database() -> None:
    init_db()


def _handle_oauth_callback() -> None:
    """Process a Google OAuth authorization-code callback.

    Google redirects to our redirect_uri with ?code=...  We detect this early
    in main() before any page routing so the login completes transparently.
    """
    code = st.query_params.get("code")
    if not code or st.session_state.get("user"):
        return

    # Consume all OAuth-related query params immediately so they don't linger.
    for _p in ["code", "state", "scope", "authuser", "prompt"]:
        if _p in st.query_params:
            del st.query_params[_p]

    from src.oauth_utils import exchange_code_for_userinfo
    user_info = exchange_code_for_userinfo(code)
    if not user_info:
        st.session_state["oauth_error"] = "Google sign-in failed. Please try again."
        st.session_state["page"] = "auth"
        return

    user = get_or_create_google_user(user_info)
    if not user:
        st.session_state["oauth_error"] = "Could not create your account. Please try again."
        st.session_state["page"] = "auth"
        return

    login_user(user)
    set_session_cookie(user)
    st.session_state["page"] = st.session_state.pop("auth_redirect", "home")


def _handle_reset_token() -> None:
    """Detect a password-reset link (?reset_token=...) and route to the auth page."""
    token = st.query_params.get("reset_token")
    if not token:
        return
    del st.query_params["reset_token"]
    st.session_state["reset_token"] = token
    st.session_state["page"] = "auth"


def _require_auth(intended_page: str = "home") -> None:
    """Redirect to auth page if the user is not signed in.

    Stores the intended destination so the auth page can redirect back after login.
    st.rerun() stops execution, so code after this call only runs when authenticated.
    """
    if not get_session_user():
        _render_auth_gate(intended_page)



def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="ExcelCV",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_chunk_load_recovery()
    _init_database()

    if st.query_params.get('_logout'):
        logout_user()
        st.session_state["ui_toast"] = {"message": "Signed out successfully.", "icon": "👋"}
        st.session_state["_skip_cookie_restore_once"] = True
        if '_logout' in st.query_params:
            del st.query_params['_logout']
        _set_query_params_atomic({"page": "home"})
        components.html(
            f'<script>\n(function() {{\n  var expire = "{_COOKIE_NAME}=; Max-Age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax";\n  try {{ document.cookie = expire; }} catch(e) {{}}\n  try {{\n    var w = window.parent && window.parent !== window ? window.parent : window;\n    w.document.cookie = expire;\n  }} catch(e) {{}}\n}})();\n</script>',
            height=0,
        )

    if not st.session_state.pop('_skip_cookie_restore_once', False):
        restore_session_from_cookie()

    _handle_oauth_callback()
    _handle_reset_token()

    if 'theme' not in st.session_state:
        raw_theme = st.query_params.get('_t') or st.query_params.get('theme')
        st.session_state['theme'] = raw_theme if raw_theme in ('light', 'dark') else 'light'

    _show_queued_toast()
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    if st.session_state.get('page') not in APP_PAGES:
        st.session_state['page'] = 'home'
    if 'report_snapshot_id' not in st.session_state:
        st.session_state['report_snapshot_id'] = None

    next_page = st.query_params.get("next")
    if (
        st.query_params.get("page") == "auth"
        and next_page in APP_PAGES
        and next_page != "auth"
    ):
        st.session_state["auth_redirect"] = str(next_page)

    url_page = st.query_params.get("page")
    url_rid = st.query_params.get("rid")
    is_unauth_protected = url_page in PROTECTED_PAGES and not get_session_user()
    if is_unauth_protected:
        intended = "cv-builder" if str(url_page) in ("cv-builder", "resume-builder") else str(url_page)
        _render_auth_gate(intended)
    if url_page in APP_PAGES and not is_unauth_protected:
        st.session_state["page"] = str(url_page)
    if url_rid:
        st.session_state["report_snapshot_id"] = str(url_rid)

    if st.session_state.get('page') == 'auth' or st.query_params.get('page') == 'auth':
        if get_session_user():
            target_page = st.query_params.get("page")
            if target_page == "auth" or target_page not in APP_PAGES:
                target_page = st.session_state.pop("auth_redirect", "home")
            if target_page == "auth" or target_page not in APP_PAGES:
                target_page = "home"
            st.session_state["page"] = str(target_page)
            desired_params = {"page": str(target_page)}
            if target_page == "report":
                rid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
                if rid:
                    desired_params["rid"] = str(rid)
            if _query_params_dict() != desired_params:
                _set_query_params_atomic(desired_params)
                st.rerun()
        else:
            st.session_state['page'] = 'auth'
            _theme = st.session_state.get('theme', 'light')
            inject_base_css(_theme)
            render_auth_page(theme=_theme)
            _inject_theme_persistence(_theme)
            return

    if st.query_params.get('_clear'):
        _clear_analysis_state(clear_comparison=True)
        st.session_state['page'] = 'home'
        _set_query_params_atomic({"page": "home"})

    if (
        st.session_state.get('page') == 'report'
        and not st.session_state.get('analysis')
        and st.session_state.get('report_snapshot_id')
    ):
        _restore_report_snapshot(str(st.session_state['report_snapshot_id']))

    if st.session_state.get('page') == 'report' and not st.session_state.get('analysis'):
        st.session_state['page'] = 'home'
        _set_query_params_atomic({"page": "home"})

    if st.session_state.get('cvb_load_id'):
        st.session_state['page'] = 'cv-builder'

    current_page = str(st.session_state.get('page', 'upload'))
    render_top_nav(NAV_ACTIVE_LABELS.get(current_page, "Analyze CV"))

    if current_page in ('home', 'upload', 'upload-cv'):
        render_upload_page(compare_mode=False)
    elif current_page == 'compare-cv':
        _require_auth('compare-cv')
        render_upload_page(compare_mode=True)
    elif current_page == 'report':
        render_report_view()
    elif current_page in ('cv-builder', 'resume-builder'):
        _require_auth('cv-builder')
        render_cv_builder_page()
    elif current_page == 'my-cvs':
        _require_auth('my-cvs')
        render_my_cvs_page()
    elif current_page == 'my-analyses':
        _require_auth('my-analyses')
        render_my_analyses_page()
    elif current_page == 'settings':
        _require_auth('settings')
        render_settings_page()
    else:
        render_static_page(current_page)

    _inject_theme_persistence(st.session_state['theme'])
    inject_base_css(st.session_state['theme'])
    inject_file_uploader_spacing_css()
    inject_compact_header_css()
    inject_header_layout_override()
    inject_fixed_top_bar()
    inject_dropdown_outside_click()
    inject_footer_full_width()
    inject_back_button_sync()
    _inject_url_and_anchor_cleanup()

    if current_page not in ("cv-builder", "resume-builder"):
        render_site_footer()


if __name__ == "__main__":
    main()
