"""Authentication utilities for session-based auth in the Streamlit app."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from typing import Optional
from urllib.parse import unquote

import bcrypt
import streamlit as st
import streamlit.components.v1 as components

from src import config as _app_config  # Also ensures .env is loaded.
from src.database import PasswordResetToken, User, get_db
from src.oauth_utils import build_google_auth_url, create_oauth_state_token, new_oauth_nonce

_SESSION_SECONDS = 3 * 24 * 3600  # 3 days
_COOKIE_NAME = "excelcv_session"


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        value = int(str(os.environ.get(name, str(default))).strip() or str(default))
    except Exception:
        value = default
    return max(minimum, value)


_LOGIN_WINDOW_SECONDS = _env_int("AUTH_LOGIN_WINDOW_SECONDS", 600, 60)
_LOGIN_MAX_ATTEMPTS = _env_int("AUTH_LOGIN_MAX_ATTEMPTS", 5, 1)
_LOGIN_LOCK_SECONDS = _env_int("AUTH_LOGIN_LOCK_SECONDS", 900, 60)
_RESET_WINDOW_SECONDS = _env_int("AUTH_RESET_WINDOW_SECONDS", 1800, 60)
_RESET_MAX_ATTEMPTS = _env_int("AUTH_RESET_MAX_ATTEMPTS", 3, 1)

_THROTTLE_LOCK = threading.Lock()
_LOGIN_FAILURES: dict[str, list[float]] = {}
_LOGIN_LOCK_UNTIL: dict[str, float] = {}
_RESET_REQUESTS: dict[str, list[float]] = {}


def _normalized_email(email: str) -> str:
    return (email or "").strip().lower()


def _client_fingerprint() -> str:
    """Best-effort client fingerprint for per-client throttling."""
    try:
        headers = getattr(st.context, "headers", {}) or {}
        for header in ("CF-Connecting-IP", "True-Client-IP", "X-Real-IP"):
            value = str(headers.get(header, "")).strip()
            if value:
                return value
        forwarded = str(headers.get("X-Forwarded-For", "")).strip()
        if forwarded:
            return forwarded.split(",")[0].strip()
    except Exception:
        pass
    try:
        guest_id = str(st.session_state.get("guest_session_id", "")).strip()
        if guest_id:
            return f"guest:{guest_id}"
    except Exception:
        pass
    return "unknown-client"


def _login_throttle_keys(email: str) -> list[str]:
    email_key = _normalized_email(email)
    client_key = _client_fingerprint()
    keys: list[str] = [f"client:{client_key}"]
    if email_key:
        keys.append(f"email:{email_key}")
        keys.append(f"email+client:{email_key}|{client_key}")
    return keys


def _reset_throttle_keys(email: str) -> list[str]:
    email_key = _normalized_email(email)
    client_key = _client_fingerprint()
    keys: list[str] = [f"client:{client_key}"]
    if email_key:
        keys.append(f"email:{email_key}")
    return keys


def _prune_window(values: list[float], window_seconds: int, now_ts: float) -> list[float]:
    return [ts for ts in values if now_ts - ts < window_seconds]


def check_login_throttle(email: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds) for login attempts."""
    now_ts = time.time()
    retry_after = 0
    with _THROTTLE_LOCK:
        for key in _login_throttle_keys(email):
            lock_until = _LOGIN_LOCK_UNTIL.get(key, 0.0)
            if lock_until > now_ts:
                retry_after = max(retry_after, int(lock_until - now_ts))
    return retry_after <= 0, max(0, retry_after)


def record_login_failure(email: str) -> None:
    """Record failed login and apply temporary lockout when threshold is exceeded."""
    now_ts = time.time()
    with _THROTTLE_LOCK:
        for key in _login_throttle_keys(email):
            attempts = _prune_window(_LOGIN_FAILURES.get(key, []), _LOGIN_WINDOW_SECONDS, now_ts)
            attempts.append(now_ts)
            _LOGIN_FAILURES[key] = attempts
            if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
                _LOGIN_LOCK_UNTIL[key] = now_ts + _LOGIN_LOCK_SECONDS
                _LOGIN_FAILURES[key] = []


def clear_login_failures(email: str) -> None:
    """Clear login failure counters for the supplied principal/client after successful login."""
    with _THROTTLE_LOCK:
        for key in _login_throttle_keys(email):
            _LOGIN_FAILURES.pop(key, None)
            _LOGIN_LOCK_UNTIL.pop(key, None)


def check_password_reset_throttle(email: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds) for forgot-password requests."""
    now_ts = time.time()
    retry_after = 0
    with _THROTTLE_LOCK:
        for key in _reset_throttle_keys(email):
            attempts = _prune_window(_RESET_REQUESTS.get(key, []), _RESET_WINDOW_SECONDS, now_ts)
            _RESET_REQUESTS[key] = attempts
            if len(attempts) >= _RESET_MAX_ATTEMPTS:
                earliest = min(attempts) if attempts else now_ts
                retry_after = max(
                    retry_after,
                    int(max(0.0, _RESET_WINDOW_SECONDS - (now_ts - earliest))),
                )
    return retry_after <= 0, max(0, retry_after)


def record_password_reset_attempt(email: str) -> None:
    """Record a forgot-password request attempt for throttling."""
    now_ts = time.time()
    with _THROTTLE_LOCK:
        for key in _reset_throttle_keys(email):
            attempts = _prune_window(_RESET_REQUESTS.get(key, []), _RESET_WINDOW_SECONDS, now_ts)
            attempts.append(now_ts)
            _RESET_REQUESTS[key] = attempts


def _session_secret() -> str:
    return (os.environ.get("SESSION_SECRET") or "").strip()


def _persistent_login_enabled() -> bool:
    return str(os.environ.get("ENABLE_PERSISTENT_LOGIN", "0")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _ensure_session_secret() -> str:
    """Return configured session secret or raise a clear startup/runtime error.

    Rejects a missing value, known published placeholders and anything too short.
    """
    return _app_config.require_strong_secret(_session_secret(), "SESSION_SECRET")


def assert_session_secret_configured() -> None:
    """Public startup guard for auth configuration."""
    _ensure_session_secret()


def is_persistent_login_enabled() -> bool:
    """Return whether browser cookie-based persistent login is enabled."""
    return _persistent_login_enabled()


def _is_request_secure() -> bool:
    """Best-effort detection of HTTPS requests behind direct/proxy deployments."""
    try:
        proto = str(st.context.headers.get("X-Forwarded-Proto", "")).lower()
        if proto:
            return proto == "https"
        proto = str(st.context.headers.get("X-Forwarded-Protocol", "")).lower()
        if proto:
            return proto == "https"
        url = str(getattr(st.context, "url", "") or "").lower()
        if url.startswith("https://"):
            return True
    except Exception:
        return False
    return False


def build_session_cookie_header(token: str, max_age: int = _SESSION_SECONDS) -> str:
    """Build hardened session-cookie attributes for JS cookie writes."""
    parts = [
        f"{_COOKIE_NAME}={token}",
        f"max-age={int(max_age)}",
        "path=/",
        "SameSite=Strict",
    ]
    if _is_request_secure():
        parts.append("Secure")
    return "; ".join(parts)


def _write_browser_cookie(cookie: str) -> None:
    """Write a cookie string from both the component iframe and the parent window."""
    components.html(
        f"""<script>
(function() {{
  var cookie = {json.dumps(cookie)};
  try {{ document.cookie = cookie; }} catch(e) {{}}
  try {{
    var w = window.parent && window.parent !== window ? window.parent : window;
    w.document.cookie = cookie;
  }} catch(e) {{}}
}})();
</script>""",
        height=0,
    )


def _read_request_cookie(name: str) -> str:
    """Return a cookie value from the current request, or "" if absent."""
    token = ""

    # Primary path: Streamlit exposes parsed cookies here on current runtimes.
    try:
        context_cookies = getattr(st.context, "cookies", None)
        if context_cookies:
            token = str(context_cookies.get(name, "")).strip()
    except Exception:
        token = ""

    # Fallback path: parse raw Cookie header if context cookies are unavailable.
    if not token:
        headers = st.context.headers
        cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
        if not cookie_header:
            for key, value in dict(headers).items():
                if str(key).lower() == "cookie":
                    cookie_header = str(value)
                    break
        if cookie_header:
            parsed = SimpleCookie()
            parsed.load(cookie_header)
            morsel = parsed.get(name)
            if morsel:
                token = morsel.value.strip()

    # Some environments encode cookie values; normalize before validation.
    return unquote(token)


# ── OAuth browser binding ─────────────────────────────────────────────────────
#
# The Google button is a full-page navigation, so the callback arrives in a NEW
# Streamlit session whose st.session_state is empty. The nonce therefore travels in
# a browser cookie. SameSite=Lax is the usual setting for OAuth state cookies, so the
# cross-site return from Google cannot drop it. No max-age: the signed state expires.
#
# Known race, accepted: the cookie is written by a components.html script, which runs
# after its iframe loads and has no ordering guarantee against the link becoming
# clickable. A click inside that window reaches the callback with no cookie and fails
# closed; app.py then tells the user to click Continue with Google again. Making the
# link inert until the script runs was rejected: it would tie the login button to
# Streamlit DOM and iframe-sandbox details and break theming.

_OAUTH_NONCE_COOKIE = "excelcv_oauth_nonce"
_OAUTH_NONCE_SESSION_KEY = "oauth_nonce"


def _oauth_nonce_cookie_header(nonce: str, *, expire: bool = False) -> str:
    parts = [f"{_OAUTH_NONCE_COOKIE}={nonce}", "path=/", "SameSite=Lax"]
    if expire:
        parts.append("max-age=0")
    if _is_request_secure():
        parts.append("Secure")
    return "; ".join(parts)


def begin_google_oauth(next_page: Optional[str] = None) -> str:
    """Return a Google sign-in URL whose state only this browser can redeem.

    Keeps one nonce per Streamlit session so reruns of the auth page reuse it, and
    stores it in a browser cookie that the callback session reads back.
    """
    nonce = str(st.session_state.get(_OAUTH_NONCE_SESSION_KEY) or "")
    if not nonce:
        nonce = new_oauth_nonce()
        st.session_state[_OAUTH_NONCE_SESSION_KEY] = nonce
    _write_browser_cookie(_oauth_nonce_cookie_header(nonce))
    state = create_oauth_state_token(next_page=next_page, nonce=nonce)
    return build_google_auth_url(state=state)


def take_oauth_nonce() -> str:
    """Return this browser's OAuth nonce for the callback and clear it so it is used once."""
    try:
        nonce = _read_request_cookie(_OAUTH_NONCE_COOKIE)
    except Exception:
        nonce = ""
    st.session_state.pop(_OAUTH_NONCE_SESSION_KEY, None)
    if nonce:
        _write_browser_cookie(_oauth_nonce_cookie_header("", expire=True))
    return nonce


def create_session_token(user_dict: dict) -> str:
    """Return a signed token encoding user_dict with a 3-day expiry."""
    secret = _ensure_session_secret()
    expiry = int(time.time()) + _SESSION_SECONDS
    raw = json.dumps({"user": user_dict, "exp": expiry}, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def validate_session_token(token: str) -> Optional[dict]:
    """Return the user dict if the token is valid and unexpired, else None."""
    try:
        secret = _ensure_session_secret()
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        if data["exp"] < int(time.time()):
            return None
        return data["user"]
    except Exception:
        return None


def restore_session_from_cookie() -> bool:
    """Read the session cookie from request headers and restore login if valid.

    Must be called once at the top of main() before any auth checks.
    Returns True if a session was restored.
    """
    if st.session_state.get("user"):
        return True
    if not _persistent_login_enabled():
        return False
    try:
        token = _read_request_cookie(_COOKIE_NAME)
        if not token:
            return False
        user = validate_session_token(token)
        if user:
            st.session_state["user"] = user
            return True
    except Exception:
        pass
    return False


def _to_bytes(password: str) -> bytes:
    """Encode and truncate to bcrypt's 72-byte limit."""
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def create_user(full_name: str, email: str, password: str) -> tuple[Optional[dict], Optional[str]]:
    """Register a new user. Returns (user_dict, None) or (None, error_message)."""
    db = get_db()
    try:
        if db.query(User).filter(User.email == email.lower().strip()).first():
            return None, "Email is already registered."
        if len(password) < 8:
            return None, "Password must be at least 8 characters."
        user = User(
            full_name=full_name.strip(),
            email=email.lower().strip(),
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "email": user.email, "full_name": user.full_name}, None
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Verify credentials. Returns user dict on success, None on failure."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return {"id": user.id, "email": user.email, "full_name": user.full_name}
    finally:
        db.close()


def get_session_user() -> Optional[dict]:
    return st.session_state.get("user")


def login_user(user_dict: dict) -> None:
    st.session_state["user"] = user_dict


def set_session_cookie(user_dict: dict) -> None:
    """Persist session auth as a browser cookie from both iframe and parent window contexts."""
    if not _persistent_login_enabled():
        return
    token = create_session_token(user_dict)
    _write_browser_cookie(build_session_cookie_header(token, _SESSION_SECONDS))


def logout_user() -> None:
    for key in [
        "user",
        "cv_builder_data",
        "analysis",
        "cv_text",
        "job_description",
        "jd",
        "cv_name",
        "cv_file_size",
        "issues",
        "report_snapshot_id",
        "comparison_results",
        "comparison_errors",
        "comparison_warnings",
        "comparison_signature",
        "comparison_attempted",
        "compare_upload_warnings",
        "compare_upload_hydration_retries",
        "compare_jd",
        "compare_selected_files",
        "compare_cvs_rev",
        "guest_session_id",
    ]:
        st.session_state.pop(key, None)

    for state_key in list(st.session_state.keys()):
        if str(state_key).startswith("compare_cvs_input_"):
            st.session_state.pop(state_key, None)

    # Remove all resume-builder keys in one pass (covers old/new naming variants).
    for state_key in list(st.session_state.keys()):
        if str(state_key).startswith("cvb_"):
            st.session_state.pop(state_key, None)

    # Legacy key kept for backwards compatibility with older sessions.
    st.session_state.pop("cvb_skill_ids", None)
    st.session_state["page"] = "home"


# ── Google OAuth ──────────────────────────────────────────────────────────────


def get_or_create_google_user(google_info: dict) -> Optional[dict]:
    """Find or create a user from Google userinfo payload.

    If the email already exists (password account), links the Google ID to it, but only
    when Google reports the email as verified. Any match or account creation by email
    requires email_verified to be True; a Google ID that is already linked does not.
    Returns a user dict on success, None on failure.
    """
    google_id = google_info.get("sub", "").strip()
    email = google_info.get("email", "").lower().strip()
    name = google_info.get("name", "") or email.split("@")[0]
    email_verified = google_info.get("email_verified") is True
    if not google_id or not email:
        return None

    db = get_db()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            if not email_verified:
                return None
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.google_id = google_id
                db.commit()
            else:
                user = User(
                    full_name=name,
                    email=email,
                    hashed_password="GOOGLE_OAUTH",
                    google_id=google_id,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        return {"id": user.id, "email": user.email, "full_name": user.full_name}
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


# ── Password Reset ────────────────────────────────────────────────────────────


def create_password_reset_token(email: str) -> Optional[str]:
    """Generate a password-reset token for *email* and persist its hash.

    Returns the raw (unhashed) token to be e-mailed to the user.
    Returns None if the email is not registered (do not reveal this to the UI).
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            return None
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
        db.commit()
        return raw
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def use_password_reset_token(raw_token: str, new_password: str) -> tuple[bool, str]:
    """Verify token, update password, and invalidate the token.

    Returns (True, "") on success or (False, error_message) on failure.
    """
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters."

    db = get_db()
    try:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = (
            db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
        )
        if not record:
            return False, "Invalid or expired reset link. Please request a new one."
        exp = record.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            db.delete(record)
            db.commit()
            return False, "This reset link has expired. Please request a new one."
        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            return False, "Account not found."
        user.hashed_password = hash_password(new_password)
        db.delete(record)
        db.commit()
        return True, ""
    except Exception:
        db.rollback()
        return False, "An error occurred. Please try again."
    finally:
        db.close()
