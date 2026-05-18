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
    "compare-report": "Comparison Results",
    "career-blog": "Career Blog",
    "cover-letter": "Cover Letter",
    "resume-builder": "Resume Builder",
    "my-cvs": "My CVs",
    "my-analyses": "My Analyses",
    "my-comparisons": "My Comparisons",
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
    "resume-tips": "Resume Tips",
    "cover-letter-guide": "Cover Letter Guide",
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


def _clear_comparison_run_artifacts() -> None:
    """Clear computed comparison outputs and run signatures.

    Run artifacts are everything produced by a `Run comparison` click:
    ranked rows, per-file errors, run-stage warnings, the input signature,
    and the attempted flag. The form's own staged-files / JD state is left
    untouched so the user can re-run after edits without re-selecting files.
    """
    for key in (
        "comparison_results",
        "comparison_errors",
        "comparison_warnings",
        "comparison_signature",
        "comparison_attempted",
    ):
        st.session_state.pop(key, None)


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
        _clear_comparison_run_artifacts()
        st.session_state.pop("compare_upload_warnings", None)
        st.session_state.pop("compare_upload_hydration_retries", None)
        st.session_state.pop("compare_jd", None)
        st.session_state.pop("compare_selected_files", None)
        st.session_state.pop("compare_cvs_rev", None)
        for key in list(st.session_state.keys()):
            if str(key).startswith("compare_cvs_input_"):
                st.session_state.pop(key, None)


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


def _snapshot_scope() -> tuple[str | None, str]:
    """Return (user_id, guest_session_id) used to scope report snapshots."""
    user_id: str | None = None
    try:
        from src.auth_utils import get_session_user

        user = get_session_user()
        if isinstance(user, dict):
            raw_uid = user.get("id")
            if raw_uid:
                user_id = str(raw_uid)
    except Exception:
        user_id = None

    guest_session_id = str(st.session_state.get("guest_session_id", "") or "").strip()
    if not guest_session_id:
        guest_session_id = uuid4().hex
        st.session_state["guest_session_id"] = guest_session_id
    return user_id, guest_session_id


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
    owner_user_id, guest_session_id = _snapshot_scope()
    payload = _build_report_snapshot()
    payload["_owner_user_id"] = owner_user_id
    payload["_guest_session_id"] = guest_session_id
    store[sid] = payload

    # Keep memory bounded.
    while len(store) > 200:
        oldest_key = next(iter(store))
        del store[oldest_key]
    return sid


def _save_report_snapshot_from_data(
    analysis: Dict[str, Any],
    cv_name: str,
    job_description: str,
    cv_file_size: int = 0,
    cv_text: str = "",
) -> str:
    """Save a report snapshot from an arbitrary analysis dict (not session state).

    Used by the compare-report drill-down to let users open any compared
    resume's full single-CV report — the analysis dict is stashed on each
    comparison row, but ``_save_report_snapshot`` only knows how to read the
    *current* session state. This helper takes the data directly so we can
    spin up a report-page snapshot without clobbering the user's main session.
    """
    store = _report_snapshot_store()
    sid = uuid4().hex
    owner_user_id, guest_session_id = _snapshot_scope()
    store[sid] = {
        "analysis": analysis,
        "cv_text": cv_text,
        "job_description": job_description or "",
        "cv_name": cv_name or "CV",
        "cv_file_size": int(cv_file_size or 0),
        "issues": issue_count(analysis) if isinstance(analysis, dict) else 0,
        "_owner_user_id": owner_user_id,
        "_guest_session_id": guest_session_id,
    }
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
    owner_user_id, guest_session_id = _snapshot_scope()
    snapshot_owner = snapshot.get("_owner_user_id")
    snapshot_guest = str(snapshot.get("_guest_session_id", "") or "")
    # Never restore another authenticated user's snapshot. For guests,
    # scope to the originating guest session only.
    if snapshot_owner:
        if owner_user_id != str(snapshot_owner):
            return False
    elif snapshot_guest and snapshot_guest != guest_session_id:
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
