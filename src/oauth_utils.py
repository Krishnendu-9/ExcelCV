"""Google OAuth 2.0 helpers — URL building and authorization-code exchange."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
import urllib.parse
from typing import Optional

import requests

from src import config as _app_config  # Also ensures .env is loaded.

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_STATE_TTL_SECONDS = 10 * 60

# Nonce digests of states that were already accepted, mapped to the state's expiry.
# In-process only: it stops replay within one server process. The state's own expiry
# and Google's single-use authorization codes bound replay beyond that.
_CONSUMED_LOCK = threading.Lock()
_CONSUMED_STATE_NONCES: dict[str, int] = {}


def _google_client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "")


def _google_client_secret() -> str:
    return os.environ.get("GOOGLE_CLIENT_SECRET", "")


def _google_redirect_uri() -> str:
    return os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501")


def _state_secret() -> str:
    """Return the OAuth state signing secret, rejecting missing, placeholder or short values."""
    return _app_config.require_strong_secret(os.environ.get("SESSION_SECRET"), "SESSION_SECRET")


# Backward-compatible module exports used by older imports (for example auth_page).
GOOGLE_CLIENT_ID = _google_client_id()
GOOGLE_CLIENT_SECRET = _google_client_secret()
GOOGLE_REDIRECT_URI = _google_redirect_uri()


def is_google_oauth_configured() -> bool:
    return bool(_google_client_id() and _google_client_secret())


def _normalize_next_page(next_page: str | None) -> str:
    value = str(next_page or "").strip()
    if not value:
        return ""
    if value == "auth":
        return ""
    return value


def new_oauth_nonce() -> str:
    """Return a fresh random nonce that binds an OAuth flow to the browser that starts it."""
    return secrets.token_urlsafe(32)


def _nonce_digest(nonce: str) -> str:
    return hashlib.sha256(nonce.encode("utf-8")).hexdigest()


def _consume_nonce_digest(digest: str, exp: int) -> bool:
    """Mark a state's nonce as used. Return False if it was already used."""
    now = int(time.time())
    with _CONSUMED_LOCK:
        for key, key_exp in list(_CONSUMED_STATE_NONCES.items()):
            if key_exp < now:
                _CONSUMED_STATE_NONCES.pop(key, None)
        if digest in _CONSUMED_STATE_NONCES:
            return False
        _CONSUMED_STATE_NONCES[digest] = exp
        return True


def create_oauth_state_token(next_page: str | None = None, *, nonce: str) -> str:
    """Create a signed short-lived OAuth state token bound to *nonce*.

    The caller keeps *nonce* in the starting browser. Only its SHA-256 goes into the
    state, so the state URL alone never reveals the value needed to redeem it.
    """
    if not nonce:
        raise ValueError("An OAuth nonce is required to create a state token.")
    state_secret = _state_secret()
    now = int(time.time())
    payload_obj = {
        "iat": now,
        "exp": now + _STATE_TTL_SECONDS,
        "nonce_sha256": _nonce_digest(nonce),
    }
    next_value = _normalize_next_page(next_page)
    if next_value:
        payload_obj["next"] = next_value
    raw = json.dumps(payload_obj, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(
        state_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{sig}"


def parse_oauth_state_token(state: str, nonce: str | None) -> Optional[dict]:
    """Return the decoded OAuth state payload if it is valid for this browser, else None.

    Valid means: correctly signed, unexpired, carrying the SHA-256 of *nonce* (the value
    held by the browser that started the flow), and not used before. A successful call
    consumes the state, so the same state is rejected the second time.
    """
    try:
        state_secret = _state_secret()
    except RuntimeError:
        return None
    if not state or "." not in state or not nonce:
        return None
    try:
        payload, sig = state.rsplit(".", 1)
        expected = hmac.new(
            state_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        if not isinstance(data, dict):
            return None
        exp = int(data.get("exp", 0))
        if exp < int(time.time()):
            return None
        bound_digest = data.get("nonce_sha256")
        if not isinstance(bound_digest, str) or not hmac.compare_digest(
            bound_digest, _nonce_digest(nonce)
        ):
            return None
        if not _consume_nonce_digest(bound_digest, exp):
            return None
        next_value = _normalize_next_page(data.get("next"))
        if next_value:
            data["next"] = next_value
        elif "next" in data:
            data.pop("next", None)
        return data
    except Exception:
        return None


def validate_oauth_state_token(state: str, nonce: str | None) -> bool:
    """Return True when the state is valid for this browser. Consumes the state like parse."""
    return parse_oauth_state_token(state, nonce) is not None


def build_google_auth_url(state: str = "") -> str:
    params = {
        "client_id": _google_client_id(),
        "redirect_uri": _google_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    if state:
        params["state"] = state
    return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_userinfo(code: str) -> Optional[dict]:
    """Exchange an authorization code for Google userinfo.

    Returns a dict with at least: sub, email, name, and email_verified set to True.
    Returns None on any failure, including when Google does not report the email
    as verified.
    """
    try:
        token_resp = requests.post(
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": _google_client_id(),
                "client_secret": _google_client_secret(),
                "redirect_uri": _google_redirect_uri(),
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if token_resp.status_code != 200:
            return None
        access_token = token_resp.json().get("access_token")
        if not access_token:
            return None
        info_resp = requests.get(
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if info_resp.status_code != 200:
            return None
        info = info_resp.json()
        if not isinstance(info, dict) or info.get("email_verified") is not True:
            return None
        return info
    except Exception:
        return None
