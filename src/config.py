"""Application configuration and environment helpers."""

import os
from typing import List, Optional

from dotenv import load_dotenv


# Load env from .env first, then .env.example as fallback for any missing keys.
# `override=False` keeps explicit .env values as the source of truth.
load_dotenv(".env", override=False)
load_dotenv(".env.example", override=False)

MAX_FILE_MB = 2
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024


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

