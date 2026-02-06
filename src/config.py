import os
from typing import List, Optional

from dotenv import load_dotenv


# Load env from .env first, then .env.example as fallback for local dev.
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    load_dotenv(".env.example")

MAX_FILE_MB = 2
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024


def get_api_key() -> Optional[str]:
    return os.getenv("GOOGLE_API_KEY")


def preferred_models() -> List[Optional[str]]:
    """Return list of preferred model names, with user's choice first."""
    models = []
    user_model = os.getenv("GEMINI_MODEL")
    if user_model:
        models.append(user_model.strip())
    
    # Add fallback models
    models.extend([
        "models/gemini-2.0-flash-exp",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-flash-8b",
        "models/gemini-1.5-flash-001",
        "models/gemini-1.5-pro",
        "models/gemini-pro",
    ])
    return models

