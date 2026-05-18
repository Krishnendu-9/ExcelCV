"""Google OAuth 2.0 helpers — URL building and authorization-code exchange."""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
from typing import Optional

import requests

from src import config as _app_config  # noqa: F401  # Ensures .env/.env.example are loaded.

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_STATE_TTL_SECONDS = 10 * 60


def _google_client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "")


def _google_client_secret() -> str:
    return os.environ.get("GOOGLE_CLIENT_SECRET", "")


def _google_redirect_uri() -> str:
    return os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501")


def _state_secret() -> str:
    return (os.environ.get("SESSION_SECRET") or "").strip()


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


def create_oauth_state_token(next_page: str | None = None) -> str:
    """Create a signed short-lived OAuth state token."""
    state_secret = _state_secret()
    if not state_secret:
        raise RuntimeError("SESSION_SECRET is required for OAuth state generation.")
    payload_obj = {
        "iat": int(time.time()),
        "exp": int(time.time()) + _STATE_TTL_SECONDS,
    }
    next_value = _normalize_next_page(next_page)
    if next_value:
        payload_obj["next"] = next_value
    raw = json.dumps(payload_obj, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(state_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def parse_oauth_state_token(state: str) -> Optional[dict]:
    """Return decoded OAuth state payload when valid and unexpired, else None."""
    state_secret = _state_secret()
    if not state_secret or not state or "." not in state:
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
        exp = int(data.get("exp", 0))
        if exp < int(time.time()):
            return None
        if not isinstance(data, dict):
            return None
        next_value = _normalize_next_page(data.get("next"))
        if next_value:
            data["next"] = next_value
        elif "next" in data:
            data.pop("next", None)
        return data
    except Exception:
        return None


def validate_oauth_state_token(state: str) -> bool:
    """Return True when OAuth state token is structurally valid and unexpired."""
    return parse_oauth_state_token(state) is not None


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

    Returns a dict with at least: sub, email, name.
    Returns None on any failure.
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
        return info_resp.json() if info_resp.status_code == 200 else None
    except Exception:
        return None
