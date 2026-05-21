"""
ExcelCV: GenAI-Powered CV Reviewer — Main Streamlit Application

Thin routing and session-orchestration layer.
All rendering logic lives in src/ui/*.
"""

import json
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import (
    assert_session_secret_configured,
    build_session_cookie_header,
    get_or_create_google_user,
    get_session_user,
    login_user,
    logout_user,
    restore_session_from_cookie,
    set_session_cookie,
)
from src.database import init_db
from src.ui.app_utils import APP_PAGES, _clear_analysis_state, _restore_report_snapshot
from src.ui.auth_page import render_auth_page
from src.ui.css_injection import (
    inject_compact_header_css,
    inject_file_uploader_spacing_css,
    inject_fixed_top_bar,
    inject_footer_full_width,
)

try:
    from src.ui.css_injection import inject_dropdown_outside_click, inject_header_layout_override
except ImportError:

    def inject_header_layout_override() -> None:
        return None

    def inject_dropdown_outside_click() -> None:
        return None


from src.ui.compare_report import render_compare_report_page
from src.ui.cv_builder_page import render_cv_builder_page
from src.ui.layout import render_site_footer, render_top_nav
from src.ui.my_analyses_page import render_my_analyses_page
from src.ui.my_comparisons_page import render_my_comparisons_page
from src.ui.my_cvs_page import render_my_cvs_page
from src.ui.report import render_report_view
from src.ui.settings_page import render_settings_page
from src.ui.static_pages import render_static_page
from src.ui.ui_components import inject_back_button_sync, inject_base_css
from src.ui.upload import render_upload_page

PROTECTED_PAGES = {
    "resume-builder",
    "my-cvs",
    "my-analyses",
    "my-comparisons",
    "compare-report",
    "settings",
}
NAV_ACTIVE_LABELS = {
    "home": "Analyze CV",
    "upload": "Analyze CV",
    "upload-cv": "Analyze CV",
    "report": "Analyze CV",
    "cover-letter": "Cover Letter",
    "resume-builder": "Resume Builder",
    "my-cvs": "My CVs",
    "my-analyses": "My Analyses",
    "my-comparisons": "My Comparisons",
    "compare-report": "Compare Resumes",
}
NAV_ACTION_TO_PAGE = {
    "upload-cv": "upload-cv",
    "compare-anchor": "home",
    "cover-letter": "cover-letter",
    "resume-builder": "resume-builder",
    "my-cvs": "my-cvs",
    "my-analyses": "my-analyses",
    # User-dropdown destinations (bridge buttons live in layout.py).
    "my-comparisons": "my-comparisons",
    "settings": "settings",
    "contact": "contact",
}
HOME_COMPARE_FOCUS_KEY = "home_nav_focus_compare"


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
    target = str(intended_page or "home")
    if target not in APP_PAGES or target == "auth":
        target = "home"
    st.session_state["auth_redirect"] = target
    st.session_state["page"] = "auth"
    _set_query_params_atomic({"page": "auth", "next": target})
    _theme = st.session_state.get("theme", "light")
    inject_base_css(_theme)
    render_auth_page(theme=_theme)
    _inject_theme_persistence(_theme)
    st.stop()


def _resolve_post_auth_target(default: str = "home") -> str:
    """Return safe post-auth destination from session/query context."""
    for raw in (
        st.session_state.get("auth_redirect"),
        st.query_params.get("next"),
        st.query_params.get("page"),
    ):
        page = str(raw or "").strip()
        if page and page in APP_PAGES and page != "auth":
            return page
    return default


def _inject_theme_persistence(theme: str) -> None:
    """Sync theme to localStorage, install a permanent theme watcher, and
    install a one-time click interceptor that carries the current theme across
    navigations.

    Theme persistence is split into three layers, each guarding the previous:

      1. Write the current theme to localStorage every render \u2014 durable mirror
         of ``st.session_state["theme"]`` for cross-session reseeding.

      2. Install (once per browser window) a permanent ``setInterval`` watcher
         that polls localStorage and re-applies ``theme-light`` / ``theme-dark``
         to body / html / .stApp / [data-testid="stAppViewContainer"] if any of
         them is missing the correct class. THIS is what survives Streamlit
         re-mounting inner shells across page navigations \u2014 and it works even
         if our render-time iframe is cached by Streamlit and doesn't
         re-execute (a real concern: ``components.html`` with identical content
         across reruns reuses the same iframe and the inline script never
         re-runs, which is why the previous "apply on every render" fix
         silently broke on same-theme navigation).

      3. Apply the class immediately on every render too (defensive belt with
         the watcher's suspenders) \u2014 and embed a per-render nonce in the
         script content so Streamlit is forced to re-mount the iframe and
         re-execute the script every render, not just when the theme changes.

    Also installs (once) a click interceptor that:
      - routes nav-link clicks through the hidden Streamlit bridge button
        (preserves Streamlit session_state \u2014 including theme \u2014 across navs)
      - for the fallback path, appends ?_t=<theme> from localStorage to any
        internal link so the next fresh Streamlit session can re-seed
        session_state["theme"]. Reads from localStorage (NOT the embedded
        Python theme value) so the link gets the *currently active* theme,
        not a stale value baked at render time.
    """
    safe_theme = "dark" if theme == "dark" else "light"
    # Per-render nonce forces Streamlit to treat each call as a fresh iframe
    # (otherwise identical content across reruns would reuse the same iframe
    # and the script would never re-execute). Cheap insurance even though the
    # permanent watcher below is the real fix.
    nonce = uuid4().hex
    components.html(
        f"""<script>
/* nonce: {nonce} */
(function() {{
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;
    w.localStorage.setItem('excelcv_theme', '{safe_theme}');

    function _shellTargets() {{
        return [
            doc.body,
            doc.documentElement,
            doc.querySelector('.stApp'),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
        ];
    }}
    function _syncThemeClass(themeClass) {{
        var targets = _shellTargets();
        for (var i = 0; i < targets.length; i++) {{
            var el = targets[i];
            if (!el || !el.classList) continue;
            if (el.classList.contains(themeClass)) continue;
            el.classList.remove('theme-light', 'theme-dark');
            el.classList.add(themeClass);
        }}
    }}
    // Immediate apply with this render's value (in case the watcher hasn't
    // ticked yet between this render and the user's next interaction).
    _syncThemeClass('{safe_theme}' === 'dark' ? 'theme-dark' : 'theme-light');

    // Permanent watcher: install once per browser window. Polls localStorage
    // every 250ms and re-applies the correct class to any re-mounted shell.
    // This is the layer that makes navigation rock-solid \u2014 even if Streamlit
    // reuses our iframe or re-mounts inner shells, the watcher keeps the
    // theme class glued to the DOM.
    if (!w._ecvThemeWatcherInstalled) {{
        w._ecvThemeWatcherInstalled = true;
        w._ecvThemeWatcherId = setInterval(function() {{
            var stored = w.localStorage.getItem('excelcv_theme');
            _syncThemeClass(stored === 'dark' ? 'theme-dark' : 'theme-light');
        }}, 250);
    }}

    var url = new URL(w.location.href);
    if (url.searchParams.has('_t')) {{
        url.searchParams.delete('_t');
        w.history.replaceState(null, '', url.toString());
    }}
    function _navButtonClass(action) {{
        var normalized = String(action || "").toLowerCase().replace(/[^a-z0-9]/g, "_");
        return ".st-key-nav_action_" + normalized + " button";
    }}
    function _modalFallbackHref(action, currentHref) {{
        try {{
            var u = new URL(currentHref, w.location.origin);
            var a = String(action || "").toLowerCase();
            if (a === "give-feedback") {{
                u.searchParams.set("open_feedback", "1");
            }} else if (a === "support") {{
                u.searchParams.set("open_support", "1");
            }}
            return u.toString();
        }} catch (_e) {{
            return currentHref;
        }}
    }}
    var NAV_HANDLER_KEY = "__excelcv_nav_action_click__";
    function handleNavActionClick(e) {{
        if (typeof e.button === "number" && e.button !== 0) return;
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
        if (!a) return;
        try {{
            var navAction = a.getAttribute("data-nav-action");
            if (navAction) {{
                e.preventDefault();
                e.stopPropagation();
                var navActionNorm = String(navAction || "").toLowerCase();
                var isModalAction = navActionNorm === "give-feedback" || navActionNorm === "support";
                var fallbackHref = _modalFallbackHref(navAction, a.href);
                var tryBridge = function(remaining) {{
                    var btn = doc.querySelector(_navButtonClass(navAction));
                    if (btn) {{
                        try {{
                            var evt = new w.MouseEvent('click', {{
                                bubbles: true,
                                cancelable: true,
                                view: w,
                                button: 0
                            }});
                            btn.dispatchEvent(evt);
                        }} catch (_evtErr) {{}}
                        try {{ btn.click(); }} catch (_clickErr) {{}}
                        return;
                    }}
                    if (remaining > 0) {{
                        setTimeout(function() {{ tryBridge(remaining - 1); }}, 80);
                        return;
                    }}
                    if (isModalAction) {{
                        // Never hard-navigate for modal-only actions.
                        return;
                    }}
                    w.location.href = fallbackHref;
                }};
                tryBridge(25);
                return;
            }}
            if (e.defaultPrevented) return;
            var u = new URL(a.href, w.location.origin);
            if (u.hostname !== w.location.hostname) return;
            // Always read theme from localStorage (the live mirror) \u2014 the
            // link's existing ?_t (baked at navbar-render-time) may be stale
            // if the user toggled theme after the navbar was built.
            var t = w.localStorage.getItem('excelcv_theme');
            if (t) {{ u.searchParams.set('_t', t); a.href = u.toString(); }}
        }} catch(ex) {{}}
    }}
    if (doc[NAV_HANDLER_KEY]) {{
        doc.removeEventListener('click', doc[NAV_HANDLER_KEY], true);
    }}
    doc[NAV_HANDLER_KEY] = handleNavActionClick;
    doc.addEventListener('click', handleNavActionClick, true);
}})();
</script>""",
        height=0,
    )


def _inject_url_and_anchor_cleanup(
    current_page: str = "home", report_snapshot_id: str | None = None
) -> None:
    """Keep URL clean, prevent hash-based reload jumps, and collapse invisible injection wrappers."""
    desired_page_js = json.dumps(str(current_page or "home"))
    desired_rid_js = json.dumps(str(report_snapshot_id or ""))
    run_token_js = json.dumps(uuid4().hex)
    script = """<script>
(function () {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;
    var desiredPage = __DESIRED_PAGE__;
    var desiredRid = __DESIRED_RID__;
    var runToken = __RUN_TOKEN__;

    w.__excelcvUrlSyncRunToken = runToken;
    function _isCurrentRun() {
        return w.__excelcvUrlSyncRunToken === runToken;
    }

    // Track what Python has just rendered so the popstate handler (bound
    // below) knows what to compare the URL against after the user hits
    // Back/Forward. Updating this on EVERY render is the whole point of
    // putting this logic here — the runToken guarantees the iframe content
    // changes each render and re-executes, which static scripts in
    // components.html do NOT do.
    w.__excelcvRenderedPage = desiredPage;

    // Bind the popstate listener — handle browser Back/Forward so the URL
    // and the rendered page don't desync. Strategy: store the handler as a
    // window-scoped FUNCTION REFERENCE (not a closure stuck inside this
    // iframe's scope) and re-install it every render. That way, even if a
    // previous render's iframe was torn down and its closure became
    // invalid, the latest iframe's handler is always live on the parent
    // window. The old listener (if any) is explicitly removed first so we
    // don't accumulate duplicates.
    if (w.__excelcvPopstateHandler) {
        try { w.removeEventListener("popstate", w.__excelcvPopstateHandler); } catch (_re) {}
    }
    w.__excelcvPopstateHandler = function () {
        try {
            console.log("[excelcv-popstate] fired", "url=", w.location.href, "rendered=", w.__excelcvRenderedPage);
            var u = new URL(w.location.href);
            var urlPage = (u.searchParams.get("page") || "home").toLowerCase();
            var renderedPage = String(w.__excelcvRenderedPage || "home").toLowerCase();
            var homeLike = new Set(["home", "upload", "upload-cv", ""]);
            if (homeLike.has(urlPage) && homeLike.has(renderedPage)) {
                console.log("[excelcv-popstate] both home-like, skipping");
                return;
            }
            if (urlPage !== renderedPage) {
                console.log("[excelcv-popstate] mismatch -> setting __bnav and reloading");
                u.searchParams.set("__bnav", "1");
                w.history.replaceState(null, "", u.toString());
                w.location.reload();
            } else {
                console.log("[excelcv-popstate] URL matches rendered, no reload");
            }
        } catch (pe) {
            console.error("[excelcv-popstate] handler threw:", pe);
        }
    };
    w.addEventListener("popstate", w.__excelcvPopstateHandler);
    w.__excelcvPopstateBound = true;

    if (!_isCurrentRun()) return;

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
        if (!_isCurrentRun()) return;
        var u = new URL(w.location.href);
        var page = (u.searchParams.get("page") || "").toLowerCase();
        var isHome = page === "home" || (page === "" && !u.searchParams.has("next"));
        var hadHash = !!u.hash;
        var keepCompareHash = isHome && u.hash === "#compare-section-anchor";
        var changed = false;

        if (isHome && hadHash && !keepCompareHash) {
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
            var canonical = u.pathname + (u.search || "") + (keepCompareHash ? u.hash : "");
            w.history.replaceState(null, "", canonical);
        }

        if (isHome && hadHash && !keepCompareHash) {
            try { w.scrollTo({ top: 0, left: 0, behavior: "instant" }); } catch (_e) { w.scrollTo(0, 0); }
            var main = doc.querySelector("[data-testid='stAppViewContainer']");
            if (main) {
                try { main.scrollTo({ top: 0, left: 0, behavior: "instant" }); } catch (_e2) { main.scrollTop = 0; }
            }
        } else if (keepCompareHash) {
            var scrollToCompare = function() {
                var anchor = doc.getElementById("compare-section-anchor");
                if (anchor && anchor.scrollIntoView) {
                    try { anchor.scrollIntoView({ behavior: "smooth", block: "start" }); } catch (_e3) { anchor.scrollIntoView(true); }
                }
            };
            [60, 220, 600].forEach(function(ms) { setTimeout(scrollToCompare, ms); });
        }
    } catch (e) {}

    // Sync URL to the current in-app route without triggering an extra Streamlit rerun.
    try {
        if (!_isCurrentRun()) return;
        var target = new URL(w.location.href);
        var normalizedDesired = String(desiredPage || "home").toLowerCase();
        var homeLike = new Set(["home", "upload", "upload-cv"]);
        var pageInUrl = (target.searchParams.get("page") || "").toLowerCase();
        var changedUrl = false;

        if (homeLike.has(normalizedDesired)) {
            if (target.searchParams.has("page")) { target.searchParams.delete("page"); changedUrl = true; }
            if (target.searchParams.has("rid")) { target.searchParams.delete("rid"); changedUrl = true; }
            if (target.searchParams.has("next")) { target.searchParams.delete("next"); changedUrl = true; }
        } else {
            if (pageInUrl !== normalizedDesired) {
                target.searchParams.set("page", normalizedDesired);
                changedUrl = true;
            }
            if (normalizedDesired === "report" && desiredRid) {
                if ((target.searchParams.get("rid") || "") !== desiredRid) {
                    target.searchParams.set("rid", desiredRid);
                    changedUrl = true;
                }
            } else if (target.searchParams.has("rid")) {
                target.searchParams.delete("rid");
                changedUrl = true;
            }
            if (normalizedDesired !== "auth" && target.searchParams.has("next")) {
                target.searchParams.delete("next");
                changedUrl = true;
            }
        }

        if (changedUrl) {
            var nextUrl = target.pathname + target.search + target.hash;
            var currentUrl = w.location.pathname + w.location.search + w.location.hash;
            if (nextUrl !== currentUrl) {
                w.history.pushState({ excelcv: true, page: normalizedDesired }, "", nextUrl);
            }
        }
    } catch (_urlSyncErr) {}

    // Collapse invisible injection wrappers so their flex-gap contribution is removed.
    // Runs after a short delay to ensure all sibling injection iframes have already
    // loaded and executed their scripts before we hide their containers.
    setTimeout(function () {
        if (!_isCurrentRun()) return;
        try {
            // Hide style-only wrappers (st.markdown('<style>...')) — <style> still applies.
            var styleEls = doc.querySelectorAll('[data-testid="stElementContainer"]:has(style)');
            for (var i = 0; i < styleEls.length; i++) {
                styleEls[i].style.setProperty('display', 'none', 'important');
            }
            // Hide zero-height custom component wrappers (components.html(height=0)).
            // offsetHeight <= 1 guards against hiding positive-height iframes (e.g. CV builder preview).
            var ccEls = doc.querySelectorAll('[data-testid="stCustomComponentV1"]');
            for (var j = 0; j < ccEls.length; j++) {
                var cc = ccEls[j];
                if ((cc.offsetHeight || 0) <= 1) {
                    var parent = cc.closest('[data-testid="stElementContainer"]');
                    if (parent) parent.style.setProperty('display', 'none', 'important');
                }
            }
        } catch (e) {}
    }, 150);

})();
</script>"""
    script = (
        script.replace("__DESIRED_PAGE__", desired_page_js)
        .replace("__DESIRED_RID__", desired_rid_js)
        .replace("__RUN_TOKEN__", run_token_js)
    )
    components.html(script, height=0)


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

    Google redirects to our redirect_uri with ?code=... plus assorted callback
    noise (iss, scope, authuser, prompt, …). We detect this early in main()
    before any page routing so the login completes transparently AND the URL
    bar is rewritten to the canonical post-login route in the same script
    run — otherwise unknown callback params (e.g. `iss`, which Google sends
    per OIDC) would linger until the user clicks something.
    """
    code = st.query_params.get("code")
    returned_state = str(st.query_params.get("state") or "").strip()
    if not code or st.session_state.get("user"):
        return
    from src.oauth_utils import parse_oauth_state_token

    state_payload = parse_oauth_state_token(returned_state)
    if not state_payload:
        st.session_state["oauth_error"] = "Google sign-in failed (invalid state). Please try again."
        st.session_state["page"] = "auth"
        _set_query_params_atomic({"page": "auth"})
        return
    next_from_state = str(state_payload.get("next") or "").strip()
    if next_from_state in APP_PAGES and next_from_state != "auth":
        st.session_state["auth_redirect"] = next_from_state

    from src.oauth_utils import exchange_code_for_userinfo

    user_info = exchange_code_for_userinfo(code)
    if not user_info:
        st.session_state["oauth_error"] = "Google sign-in failed. Please try again."
        st.session_state["page"] = "auth"
        _set_query_params_atomic({"page": "auth"})
        return

    user = get_or_create_google_user(user_info)
    if not user:
        st.session_state["oauth_error"] = "Could not create your account. Please try again."
        st.session_state["page"] = "auth"
        _set_query_params_atomic({"page": "auth"})
        return

    login_user(user)
    set_session_cookie(user)
    target_page = _resolve_post_auth_target("home")
    st.session_state.pop("auth_redirect", None)
    st.session_state["page"] = target_page
    # Atomically replace EVERY query param so OAuth callback noise (iss,
    # code, state, scope, authuser, prompt, anything Google adds later)
    # drops out in one shot. The end-of-render JS cleanup further trims
    # `?page=home` to a bare path for the home route.
    _set_query_params_atomic({"page": target_page})


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
    assert_session_secret_configured()
    _init_database()

    if st.query_params.get("_logout"):
        logout_user()
        st.session_state["ui_toast"] = {"message": "Signed out successfully.", "icon": "👋"}
        st.session_state["_skip_cookie_restore_once"] = True
        if "_logout" in st.query_params:
            del st.query_params["_logout"]
        _set_query_params_atomic({"page": "home"})
        expired = build_session_cookie_header("", 0) + "; expires=Thu, 01 Jan 1970 00:00:00 GMT"
        components.html(
            f"<script>\n(function() {{\n  var expire = {json.dumps(expired)};\n  try {{ document.cookie = expire; }} catch(e) {{}}\n  try {{\n    var w = window.parent && window.parent !== window ? window.parent : window;\n    w.document.cookie = expire;\n  }} catch(e) {{}}\n}})();\n</script>",
            height=0,
        )

    if not st.session_state.pop("_skip_cookie_restore_once", False):
        restore_session_from_cookie()

    _handle_oauth_callback()
    _handle_reset_token()

    if "theme" not in st.session_state:
        raw_theme = st.query_params.get("_t") or st.query_params.get("theme")
        st.session_state["theme"] = raw_theme if raw_theme in ("light", "dark") else "light"

    _show_queued_toast()
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if st.session_state.get("page") not in APP_PAGES:
        st.session_state["page"] = "home"
    if "report_snapshot_id" not in st.session_state:
        st.session_state["report_snapshot_id"] = None

    next_page = st.query_params.get("next")
    if st.query_params.get("page") == "auth" and next_page in APP_PAGES and next_page != "auth":
        st.session_state["auth_redirect"] = str(next_page)

    url_page = st.query_params.get("page")
    url_rid = st.query_params.get("rid")
    open_feedback = str(st.query_params.get("open_feedback") or "").strip().lower()
    open_support = str(st.query_params.get("open_support") or "").strip().lower()
    # Browser-nav marker. ``_inject_url_and_anchor_cleanup`` adds ``__bnav=1``
    # to the URL just before reloading in response to a popstate (browser
    # Back/Forward). When we see it, we force URL-driven routing — bypassing
    # the ``_last_applied_url_page`` guard below — and then strip the marker
    # so it doesn't survive subsequent renders.
    is_browser_nav = bool(st.query_params.get("__bnav"))
    if is_browser_nav:
        try:
            del st.query_params["__bnav"]
        except Exception:
            pass
    is_unauth_protected = url_page in PROTECTED_PAGES and not get_session_user()
    if is_unauth_protected:
        intended = str(url_page)
        _render_auth_gate(intended)
    # Apply URL-driven routing when either:
    #   - the URL page value actually changed since we last applied it
    #     (normal in-app rerun / refresh), OR
    #   - this rerun was triggered by a browser-nav reload (``__bnav=1``),
    #     even if the URL value matches what was last applied. Without the
    #     browser-nav override, hitting Back after a forward bridge-button
    #     nav would leave ``session_state['page']`` stuck on the previous
    #     slug because ``_last_applied_url_page`` would equal the URL.
    last_applied_url_page = st.session_state.get("_last_applied_url_page")
    if url_page in APP_PAGES and not is_unauth_protected:
        if is_browser_nav or str(url_page) != str(last_applied_url_page):
            st.session_state["page"] = str(url_page)
            st.session_state["_last_applied_url_page"] = str(url_page)
    elif url_page not in APP_PAGES:
        st.session_state["_last_applied_url_page"] = None
    if url_rid:
        st.session_state["report_snapshot_id"] = str(url_rid)
    if open_feedback in {"1", "true", "yes"}:
        st.session_state["support_dialog_open"] = False
        st.session_state["feedback_dialog_open"] = True
        st.session_state.pop("feedback_sent", None)
        try:
            del st.query_params["open_feedback"]
        except Exception:
            pass
        try:
            del st.query_params["open_support"]
        except Exception:
            pass
    elif open_support in {"1", "true", "yes"}:
        st.session_state["feedback_dialog_open"] = False
        st.session_state.pop("feedback_sent", None)
        st.session_state["support_dialog_open"] = True
        try:
            del st.query_params["open_support"]
        except Exception:
            pass

    if st.session_state.get("page") == "auth" or st.query_params.get("page") == "auth":
        if get_session_user():
            target_page = _resolve_post_auth_target("home")
            st.session_state.pop("auth_redirect", None)
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
            st.session_state["page"] = "auth"
            _theme = st.session_state.get("theme", "light")
            inject_base_css(_theme)
            render_auth_page(theme=_theme)
            _inject_theme_persistence(_theme)
            return

    if st.query_params.get("_clear"):
        _clear_analysis_state(clear_comparison=True)
        st.session_state["page"] = "home"
        _set_query_params_atomic({"page": "home"})

    if (
        st.session_state.get("page") == "report"
        and not st.session_state.get("analysis")
        and st.session_state.get("report_snapshot_id")
    ):
        _restore_report_snapshot(str(st.session_state["report_snapshot_id"]))

    if st.session_state.get("page") == "report" and not st.session_state.get("analysis"):
        st.session_state["page"] = "home"
        _set_query_params_atomic({"page": "home"})

    if st.session_state.get("cvb_load_id"):
        st.session_state["page"] = "resume-builder"

    current_page = str(st.session_state.get("page", "upload"))
    if current_page == "compare-cv":
        st.session_state["page"] = "home"
        st.session_state["scroll_to_compare_anchor"] = True
        st.session_state[HOME_COMPARE_FOCUS_KEY] = True
        current_page = "home"

    # Defensive cleanup: stale compare-focus/nav-action state from a previous
    # page can leak into the first Resume Builder paint and briefly mark
    # "Compare Resumes" as active.
    if current_page == "resume-builder":
        st.session_state[HOME_COMPARE_FOCUS_KEY] = False
        st.session_state.pop("scroll_to_compare_anchor", None)
        if str(st.session_state.get("nav_action_pending", "")).strip() == "compare-anchor":
            st.session_state.pop("nav_action_pending", None)
    active_nav_label = NAV_ACTIVE_LABELS.get(current_page, "Analyze CV")
    if current_page in ("home", "upload", "upload-cv") and st.session_state.get(
        HOME_COMPARE_FOCUS_KEY
    ):
        active_nav_label = "Compare Resumes"
    # Resume Tips pillar, any sub-guide article, and the Cover Letter Guide
    # are NOT part of the top nav — none of the top-nav items should be
    # highlighted when the reader is in one of those pages. An empty label
    # normalizes to a non-matching page key in render_top_nav, so no nav item
    # gets the .site-nav-item-active class.
    from src.ui.guides import GUIDES_META as _GUIDES_META

    if (
        current_page == "resume-tips"
        or current_page == "cover-letter-guide"
        or current_page == "privacy-policy"
        or current_page == "terms-of-service"
        or current_page in _GUIDES_META
    ):
        active_nav_label = ""

    # Inject layout-critical CSS BEFORE the header and page content render.
    # Streamlit streams its response to the browser top-to-bottom; if these
    # `<style>` blocks come after the header markup (as they used to), the
    # browser shows the unstyled header for the duration of the rerun, then
    # snaps into shape once the styles arrive. Putting them first eliminates
    # the FOUC. The DOM-dependent JS injections (header layout override,
    # fixed top bar, footer full width) still run at the bottom — they need
    # the elements they target to exist before they execute.
    inject_base_css(st.session_state["theme"])
    inject_compact_header_css()
    inject_file_uploader_spacing_css()

    nav_action = render_top_nav(active_nav_label)
    if nav_action:
        target_page = NAV_ACTION_TO_PAGE.get(nav_action, "home")
        if nav_action == "compare-anchor":
            st.session_state["scroll_to_compare_anchor"] = True
            st.session_state[HOME_COMPARE_FOCUS_KEY] = True
        elif nav_action == "upload-cv":
            # Explicit "Analyze CV" click — also drop the
            # return-to-compare scroll hint set by the compare-report page so
            # a deliberate nav choice isn't silently overridden by a stale
            # auto-scroll from the previous compare session.
            st.session_state[HOME_COMPARE_FOCUS_KEY] = False
            st.session_state.pop("scroll_to_compare_anchor", None)
            # If the user is already on home, scrolling to the top IS the nav
            # action (the Analyze CV section sits at the top of the page).
            # Without this, clicking Analyze CV from a scrolled-down position
            # is a visible no-op.
            if current_page in ("home", "upload", "upload-cv"):
                st.session_state["scroll_to_analyze_top"] = True
        elif target_page not in ("home", "upload", "upload-cv"):
            st.session_state[HOME_COMPARE_FOCUS_KEY] = False
        if not get_session_user() and target_page in PROTECTED_PAGES:
            st.session_state.pop("nav_action_pending", None)
            _render_auth_gate(target_page)
        st.session_state["page"] = target_page
        st.session_state.pop("nav_action_pending", None)
        current_page = str(st.session_state.get("page", "home"))
    else:
        if current_page not in ("home", "upload", "upload-cv"):
            st.session_state[HOME_COMPARE_FOCUS_KEY] = False
        st.session_state.pop("nav_action_pending", None)
        current_page = str(st.session_state.get("page", "upload"))

    if current_page in ("home", "upload", "upload-cv"):
        render_upload_page(compare_mode=False)
    elif current_page == "compare-report":
        _require_auth("compare-report")
        render_compare_report_page()
    elif current_page == "report":
        render_report_view()
    elif current_page == "resume-builder":
        _require_auth("resume-builder")
        render_cv_builder_page()
    elif current_page == "my-cvs":
        _require_auth("my-cvs")
        render_my_cvs_page()
    elif current_page == "my-analyses":
        _require_auth("my-analyses")
        render_my_analyses_page()
    elif current_page == "my-comparisons":
        _require_auth("my-comparisons")
        render_my_comparisons_page()
    elif current_page == "settings":
        _require_auth("settings")
        render_settings_page()
    elif current_page in _GUIDES_META:
        # Resume Tips sub-guide articles (see src/ui/guides.py). Each guide
        # slug is registered in APP_PAGES; dispatch here by checking
        # membership in the canonical GUIDES_META dict rather than relying
        # on a slug prefix (slugs no longer carry a "guide-" prefix so they
        # render shorter in the URL bar).
        from src.ui.guides import render_guide_article

        render_guide_article(current_page)
    else:
        render_static_page(current_page)

    _inject_theme_persistence(st.session_state["theme"])
    # Layout-critical CSS (inject_base_css, inject_compact_header_css,
    # inject_file_uploader_spacing_css) is now injected BEFORE render_top_nav
    # to eliminate FOUC during cross-page navigation. The injections below are
    # JS-based and must run AFTER the DOM they target exists.
    inject_header_layout_override()
    inject_fixed_top_bar()
    inject_dropdown_outside_click()
    inject_footer_full_width()
    inject_back_button_sync()
    _inject_url_and_anchor_cleanup(
        current_page=current_page,
        report_snapshot_id=(
            str(st.session_state.get("report_snapshot_id") or "")
            if current_page == "report"
            else ""
        ),
    )

    if current_page != "resume-builder":
        render_site_footer()


if __name__ == "__main__":
    main()
