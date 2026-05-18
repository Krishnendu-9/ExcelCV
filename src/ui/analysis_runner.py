"""Analysis execution: single CV, multi-resume comparison, and DB auto-save."""

import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st

from src.auth_utils import get_session_user
from src.config import MAX_FILE_BYTES, MAX_FILE_MB
from src.gemini_client import analyze_cv_with_gemini
from src.pdf_utils import extract_cv_text, parse_confidence_chip
from src.ui.app_utils import _coerce_score, _normalize_missing_skills, _sanitize_cv_filename
from src.ui.common import issue_count


def _is_quota_message(message: str) -> bool:
    """Detect Gemini rate-limit / quota signatures in an error string."""
    text = (message or "").lower()
    return (
        "429" in text
        or "rate limit" in text
        or "quota" in text
        or "resource exhausted" in text
    )


def _uploaded_file_sha256(uploaded_cv: Any) -> str:
    """Return a stable content hash for deduplication, or an empty string."""
    try:
        if hasattr(uploaded_cv, "getvalue"):
            raw_bytes = uploaded_cv.getvalue()
            if isinstance(raw_bytes, (bytes, bytearray)):
                return hashlib.sha256(bytes(raw_bytes)).hexdigest()

        if hasattr(uploaded_cv, "seek") and hasattr(uploaded_cv, "read"):
            uploaded_cv.seek(0)
            raw_bytes = uploaded_cv.read()
            uploaded_cv.seek(0)
            if isinstance(raw_bytes, (bytes, bytearray)):
                return hashlib.sha256(bytes(raw_bytes)).hexdigest()
    except Exception:
        return ""
    return ""


def run_single_analysis(
    job_description: str,
    uploaded_cv,
    status_container: Optional[Any] = None,
) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Process a single CV analysis workflow.

    Args:
        job_description: The job description text
        uploaded_cv: Streamlit uploaded file object

    Returns:
        (analysis_dict, cv_text) if successful, None otherwise. cv_text is returned
        so the caller can keep extracted content in session.

    All output (validation errors, parse chip, preview, spinner, model errors) is
    rendered into ``status_container`` when provided, so the caller can place it.
    """
    progress_area = status_container if status_container is not None else st.container()

    with progress_area:
        if not (job_description or "").strip():
            st.error("Please provide a job description.")
            return None
        if uploaded_cv is None:
            st.error("Please upload a PDF or DOCX CV.")
            return None
        if getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
            st.error(f"{uploaded_cv.name} is too large. Max {MAX_FILE_MB}MB.")
            return None

        cv_name = getattr(uploaded_cv, "name", "resume.pdf")
        try:
            cv_text = extract_cv_text(uploaded_cv, cv_name)
        except ValueError as exc:
            st.error(str(exc))
            return None

        # Parse confidence chip first — it's the at-a-glance signal.
        ext = Path(cv_name).suffix.lower()
        label, cls = parse_confidence_chip(cv_text, ext)
        st.markdown(f"<span class='{cls}'>{label}</span>", unsafe_allow_html=True)

        preview = cv_text[:900]
        if len(cv_text) > 900:
            preview += "..."
        with st.expander("Preview extracted resume text"):
            st.write(preview)

        with st.spinner(f"Analyzing {uploaded_cv.name} with Gemini..."):
            try:
                analysis = analyze_cv_with_gemini(
                    cv_text=cv_text,
                    job_desc=job_description,
                    file_name=cv_name,
                    file_size_bytes=getattr(uploaded_cv, "size", 0),
                )
                return (analysis, cv_text)
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
    return None


def _analyze_cv_payload(job_description: str, uploaded_cv) -> Tuple[Dict[str, Any], str]:
    """Extract CV text and run model analysis for one file."""
    if not job_description.strip():
        raise ValueError("Please provide a job description.")
    if uploaded_cv is None:
        raise ValueError("Please upload a PDF or DOCX CV.")
    if getattr(uploaded_cv, "size", 0) > MAX_FILE_BYTES:
        raise ValueError(f"{uploaded_cv.name} is too large. Max {MAX_FILE_MB}MB.")

    cv_name = getattr(uploaded_cv, "name", "resume.pdf")
    cv_text = extract_cv_text(uploaded_cv, cv_name)
    analysis = analyze_cv_with_gemini(
        cv_text=cv_text,
        job_desc=job_description,
        file_name=cv_name,
        file_size_bytes=getattr(uploaded_cv, "size", 0),
    )
    return analysis, cv_text


def _short_error_message(exc: Exception, max_len: int = 220) -> str:
    """Trim noisy tracebacks/JSON-blob errors down to one human-readable line."""
    text = str(exc).strip()
    if not text:
        text = type(exc).__name__
    # Collapse newlines so the warning list doesn't break formatting.
    text = " ".join(text.split())
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


# Callback signature: (file_name, idx_1_based, total, status)
# status ∈ {"running", "done", "error", "skipped"}
ProgressCallback = Callable[[str, int, int, str], None]


def run_multi_resume_comparison(
    job_description: str,
    uploaded_cvs: List[Any],
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """Run analysis for multiple resumes and return comparison rows + errors.

    ``progress_callback`` (optional) receives ``(file_name, idx, total, status)``
    before/after each file so the caller can render per-file progress. Errors
    inside the callback are swallowed so a broken UI hook never breaks the run.
    """
    normalized_jd = (job_description or "").strip()
    if not normalized_jd:
        raise ValueError("Please provide a job description for comparison.")
    files = uploaded_cvs or []
    if len(files) < 2:
        raise ValueError("Please upload at least 2 resumes for comparison.")
    if len(files) > 5:
        raise ValueError("Please upload no more than 5 resumes at a time.")

    def _emit(file_name: str, idx: int, total: int, status: str) -> None:
        if progress_callback is None:
            return
        try:
            progress_callback(file_name, idx, total, status)
        except Exception:
            pass

    deduped_files: List[Any] = []
    seen_signatures: set[str] = set()
    skipped_duplicates: List[str] = []
    for uploaded_cv in files:
        file_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume"))
        file_size = int(getattr(uploaded_cv, "size", 0) or 0)
        file_hash = _uploaded_file_sha256(uploaded_cv)
        signature = f"{file_name.lower()}|{file_size}|{file_hash or 'nohash'}"
        if signature in seen_signatures:
            skipped_duplicates.append(file_name)
            continue
        seen_signatures.add(signature)
        deduped_files.append(uploaded_cv)

    if len(deduped_files) < 2:
        raise ValueError("Please upload at least 2 unique resumes for comparison.")

    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []
    quota_block_message: Optional[str] = None
    total = len(deduped_files)
    for idx, uploaded_cv in enumerate(deduped_files):
        file_name = _sanitize_cv_filename(getattr(uploaded_cv, "name", "resume"))
        # If a previous file in this run already hit the Gemini quota, every
        # further call would burn more of the same per-minute quota and fail
        # the same way. Short-circuit the remaining files so they all appear in
        # the user-visible error list with a clear, consistent reason.
        if quota_block_message is not None:
            errors.append(f"{file_name}: {quota_block_message}")
            _emit(file_name, idx + 1, total, "skipped")
            continue
        _emit(file_name, idx + 1, total, "running")
        try:
            analysis, _ = _analyze_cv_payload(normalized_jd, uploaded_cv)
            analysis = analysis if isinstance(analysis, dict) else {}
            tailoring_metrics = analysis.get("tailoring_metrics", {})
            content_metrics = analysis.get("content_metrics", {})
            sections_metrics = analysis.get("sections_metrics", {})
            if not isinstance(tailoring_metrics, dict):
                tailoring_metrics = {}
            if not isinstance(content_metrics, dict):
                content_metrics = {}
            if not isinstance(sections_metrics, dict):
                sections_metrics = {}

            missing_skills = _normalize_missing_skills(analysis.get("missing_skills", []))
            try:
                issues_total = int(issue_count(analysis))
            except Exception:
                issues_total = 0
            rows.append(
                {
                    "Resume": file_name,
                    "Final Score": _coerce_score(analysis.get("match_score", 0)),
                    "JD Alignment": _coerce_score(tailoring_metrics.get("score", 0)),
                    "ATS Parse": _coerce_score(content_metrics.get("ats_parse_rate", 0)),
                    "Sections": _coerce_score(sections_metrics.get("score", 0)),
                    "Issues": max(0, issues_total),
                    "Top Missing Skills": ", ".join(missing_skills) if missing_skills else "None",
                    # Stash the full analysis dict so the report page can render
                    # per-resume drill-down details without re-running Gemini.
                    # Prefixed with `_` so DataFrame/CSV consumers skip it.
                    "_analysis": analysis,
                }
            )
            _emit(file_name, idx + 1, total, "done")
        except Exception as exc:  # pragma: no cover - UI path
            short = _short_error_message(exc)
            errors.append(f"{file_name}: {short}")
            _emit(file_name, idx + 1, total, "error")
            if _is_quota_message(str(exc)) and idx < len(deduped_files) - 1:
                quota_block_message = short
                warnings.append(
                    "Gemini API rate limit hit during comparison. Remaining resumes were skipped to avoid burning more quota."
                )

    rows = sorted(
        rows,
        key=lambda row: (
            -int(row.get("Final Score", 0)),
            int(row.get("Issues", 0)),
            str(row.get("Resume", "")).lower(),
        ),
    )
    for idx, row in enumerate(rows, start=1):
        row["Rank"] = idx

    if skipped_duplicates:
        warnings.append(
            "Skipped duplicate file selections: " + ", ".join(skipped_duplicates)
        )
    return {"rows": rows, "errors": errors, "warnings": warnings}


def _autosave_analysis(cv_name: str, job_description: str, analysis: Dict[str, Any]) -> None:
    """Persist analysis result to DB for the currently logged-in user (silent)."""
    user = get_session_user()
    if not user:
        return
    try:
        from src.database import Analysis as AnalysisModel
        from src.database import get_db as _get_db
        match_score = float(analysis.get("match_score", 0))
        db = _get_db()
        try:
            record = AnalysisModel(
                user_id=user["id"],
                cv_name=cv_name,
                job_description=job_description,
                result=analysis,
                match_score=match_score,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
