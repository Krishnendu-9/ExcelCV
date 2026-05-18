"""Authentication utilities for session-based auth in the Streamlit app."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import streamlit as st
import streamlit.components.v1 as components

from src import config as _app_config  # noqa: F401  # Ensures .env/.env.example are loaded.
from src.database import PasswordResetToken, User, get_db

_SESSION_SECONDS = 3 * 24 * 3600  # 3 days
_COOKIE_NAME = "excelcv_session"


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
    """Return configured session secret or raise a clear startup/runtime error."""
    secret = _session_secret()
    if not secret:
        raise RuntimeError(
            "SESSION_SECRET is required for secure authentication. "
            "Set SESSION_SECRET in your environment or .env file."
        )
    return secret


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
        token = ""

        # Primary path: Streamlit exposes parsed cookies here on current runtimes.
        try:
            context_cookies = getattr(st.context, "cookies", None)
            if context_cookies:
                token = str(context_cookies.get(_COOKIE_NAME, "")).strip()
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
                morsel = parsed.get(_COOKIE_NAME)
                if morsel:
                    token = morsel.value.strip()

        # Some environments encode cookie values; normalize before validation.
        token = unquote(token)
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
    cookie = build_session_cookie_header(token, _SESSION_SECONDS)
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

    for key in list(st.session_state.keys()):
        if str(key).startswith("compare_cvs_input_"):
            st.session_state.pop(key, None)

    # Remove all resume-builder keys in one pass (covers old/new naming variants).
    for key in list(st.session_state.keys()):
        if str(key).startswith("cvb_"):
            st.session_state.pop(key, None)

    # Legacy key kept for backwards compatibility with older sessions.
    st.session_state.pop("cvb_skill_ids", None)
    st.session_state["page"] = "home"


# ── Google OAuth ──────────────────────────────────────────────────────────────

def get_or_create_google_user(google_info: dict) -> Optional[dict]:
    """Find or create a user from Google userinfo payload.

    If the email already exists (password account), links the Google ID to it.
    Returns a user dict on success, None on failure.
    """
    google_id = google_info.get("sub", "").strip()
    email = google_info.get("email", "").lower().strip()
    name = google_info.get("name", "") or email.split("@")[0]
    if not google_id or not email:
        return None

    db = get_db()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
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
        record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
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
