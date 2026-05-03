"""App-level utilities: page-routing helpers, state management, and report snapshots."""

import base64
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from uuid import uuid4

import streamlit as st

from src.ui.common import issue_count

APP_PAGES: Dict[str, str] = {
    "home": "Home",
    "auth": "Sign In",
    "upload-cv": "Upload CV",
    "compare-cv": "Compare Multiple CV",
    "career-blog": "Career Blog",
    "motivation-letter": "Motivation Letter",
    "resume-builder": "Resume Builder",
    "cv-builder": "Resume Builder",
    "my-cvs": "My CVs",
    "my-analyses": "My Analyses",
    "settings": "Settings",
    "upload": "Resume Checker",
    "report": "Report",
    "ats-insights": "ATS Insights",
    "instant-report": "Instant Report",
    "evaluation-toolkit": "Evaluation Toolkit",
    "explainable-scoring": "Explainable Scoring",
    "project-notes": "Project Notes",
    "how-it-works": "How It Works",
    "interview-prep": "Interview Prep",
    "privacy-policy": "Privacy Policy",
    "terms-of-service": "Terms of Service",
    "contact": "Contact",
}


def _build_page_href(page: str, include_rid: bool = False, next_page: str | None = None) -> str:
    """Build app-internal page URL. _t carries theme across session resets; Python strips it immediately."""
    theme = st.session_state.get("theme", "light")
    params: Dict[str, str] = {"page": page, "_t": theme}
    if next_page:
        params["next"] = str(next_page)
    if include_rid:
        rid = st.session_state.get("report_snapshot_id") or st.query_params.get("rid")
        if rid:
            params["rid"] = str(rid)
    return f"/?{urlencode(params)}"

def _sanitize_cv_filename(raw_name: str) -> str:
    """Return a safe single-segment filename for display and downloads."""
    safe_name = str(raw_name or "CV.pdf").strip()
    safe_name = safe_name.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[\r\n\t]+", " ", safe_name)
    safe_name = re.sub(r'[<>:"/\\|?*]+', "-", safe_name).strip(" .")
    return safe_name or "CV.pdf"


def _coerce_score(value: Any, default: int = 0) -> int:
    """Convert score-like input to a bounded integer (0-100)."""
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, parsed))


def _normalize_missing_skills(value: Any, limit: int = 3) -> List[str]:
    """Return a de-duplicated list of display-ready missing skills."""
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        raw_items = [value]
    else:
        return []

    normalized: List[str] = []
    for item in raw_items:
        skill = str(item).strip()
        if not skill or skill in normalized:
            continue
        normalized.append(skill)
        if len(normalized) >= limit:
            break
    return normalized


def _clear_analysis_state(clear_comparison: bool = True) -> None:
    """Clear analysis/report-related session state keys."""
    for key in (
        "analysis",
        "cv_text",
        "job_description",
        "cv_name",
        "cv_file_size",
        "issues",
        "report_snapshot_id",
        "jd",
        "cvs",
    ):
        st.session_state.pop(key, None)
    if clear_comparison:
        st.session_state.pop("comparison_results", None)
        st.session_state.pop("comparison_errors", None)


@lru_cache(maxsize=4)
def _load_logo_data_uri(theme: str = "light") -> str:
    """Return theme-oriented logo as a data URI for stable HTML rendering."""
    base_dir = Path(__file__).resolve().parents[2] / "assets" / "images"
    normalized_theme = "dark" if str(theme).lower() == "dark" else "light"

    if normalized_theme == "dark":
        preferred = ["ExcelCV_clean.png", "ExcelCV.png"]
    else:
        # Use transparent logo in light theme to avoid visible white-box canvas artifacts.
        preferred = ["ExcelCV_clean.png", "ExcelCV.png"]

    logo_path: Path | None = None
    for candidate in preferred:
        path = base_dir / candidate
        if path.exists():
            logo_path = path
            break

    if logo_path is None:
        return ""

    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:image/png;base64,{encoded}"


@st.cache_resource
def _report_snapshot_store() -> Dict[str, Dict[str, Any]]:
    """Process-wide in-memory store for recent report snapshots."""
    return {}


def _build_report_snapshot() -> Dict[str, Any]:
    """Capture the minimum session fields required to restore a report page."""
    return {
        "analysis": st.session_state.get("analysis"),
        "cv_text": st.session_state.get("cv_text"),
        "job_description": st.session_state.get("job_description") or st.session_state.get("jd", ""),
        "cv_name": st.session_state.get("cv_name", "CV"),
        "cv_file_size": st.session_state.get("cv_file_size", 0),
        "issues": st.session_state.get("issues"),
    }


def _save_report_snapshot(snapshot_id: Optional[str] = None) -> str:
    """Save current report state and return a shareable snapshot id."""
    store = _report_snapshot_store()
    sid = snapshot_id or uuid4().hex
    store[sid] = _build_report_snapshot()

    # Keep memory bounded.
    while len(store) > 200:
        oldest_key = next(iter(store))
        del store[oldest_key]
    return sid


def _restore_report_snapshot(snapshot_id: str) -> bool:
    """Restore report state from snapshot id. Returns True on success."""
    store = _report_snapshot_store()
    snapshot = store.get(snapshot_id)
    if not snapshot or not snapshot.get("analysis"):
        return False

    st.session_state["analysis"] = snapshot.get("analysis")
    st.session_state["cv_text"] = snapshot.get("cv_text", "")
    st.session_state["job_description"] = snapshot.get("job_description", "")
    st.session_state["jd"] = snapshot.get("job_description", "")
    st.session_state["cv_name"] = snapshot.get("cv_name", "CV")
    st.session_state["cv_file_size"] = snapshot.get("cv_file_size", 0)
    st.session_state["issues"] = snapshot.get("issues", issue_count(snapshot["analysis"]))
    st.session_state["page"] = "report"
    st.session_state["report_snapshot_id"] = snapshot_id
    return True
