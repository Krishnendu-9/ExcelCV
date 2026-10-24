"""Application configuration and environment helpers."""

import os
from typing import List, Optional

from dotenv import load_dotenv

# Load env from .env only. `override=False` keeps real environment variables as the
# source of truth. .env.example is documentation, never a config source: its values are
# public placeholders, and every optional setting already has a default in code.
load_dotenv(".env", override=False)

MAX_FILE_MB = 2
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

SESSION_SECRET_MIN_LENGTH = 32
SESSION_SECRET_GENERATOR = 'python -c "import secrets; print(secrets.token_hex(32))"'

# Published placeholder values, compared after lowercasing and dropping separators.
_PLACEHOLDER_SECRETS = {
    "changethistoarandomsecret",  # the exact value shipped in .env.example
    "changeme",
    "changethis",
    "changeit",
    "secret",
    "sessionsecret",
    "yoursessionsecret",
    "yoursecret",
    "yoursecretkey",
    "replaceme",
}
# Fragments that mark a value as a placeholder wherever they appear in it.
_PLACEHOLDER_FRAGMENTS = ("changethis", "changeme", "replaceme", "yoursecret")


def require_strong_secret(value: Optional[str], name: str = "SESSION_SECRET") -> str:
    """Return *value* stripped, or raise RuntimeError if it is missing, a placeholder or short."""
    secret = (value or "").strip()
    fix = (
        f"Generate one with: {SESSION_SECRET_GENERATOR} and set {name} in your environment or .env."
    )
    if not secret:
        raise RuntimeError(f"{name} is required for secure authentication. {fix}")
    folded = "".join(ch for ch in secret.lower() if ch.isalnum())
    if folded in _PLACEHOLDER_SECRETS or any(frag in folded for frag in _PLACEHOLDER_FRAGMENTS):
        raise RuntimeError(f"{name} is set to a published placeholder value. {fix}")
    if len(secret) < SESSION_SECRET_MIN_LENGTH:
        raise RuntimeError(
            f"{name} must be at least {SESSION_SECRET_MIN_LENGTH} characters "
            f"(got {len(secret)}). {fix}"
        )
    return secret


def get_api_key() -> Optional[str]:
    """Return Gemini API key from environment, if available."""
    return os.getenv("GOOGLE_API_KEY")


def preferred_models() -> List[Optional[str]]:
    """Return list of preferred model names, with user's choice first."""
    models = []
    user_model = os.getenv("GEMINI_MODEL")
    if user_model:
        models.append(user_model.strip())

    # Add fallback models (ordered: fast & cheap first, then more capable)
    models.extend(
        [
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
        ]
    )

    # Preserve order while removing duplicates and empty values.
    seen = set()
    unique_models: List[Optional[str]] = []
    for model in models:
        if not model or model in seen:
            continue
        seen.add(model)
        unique_models.append(model)
    return unique_models
