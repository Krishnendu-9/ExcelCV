"""My Analyses page — search / sort / group / bulk-delete view of saved runs.

Layout rules
------------
- Runs that share the same ``(cv_name, job_description)`` are merged into a
  single "group card" with an expandable sub-list and a score sparkline.
- A run that has no peers renders as a flat card.
- Toolbar adds search-by-CV-name, sort-order, and a Select mode toggle.
- Select mode shows a checkbox column and a floating action bar so the user
  can delete many rows in one go instead of one-by-one confirms.
"""

from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime
from typing import Iterable, Sequence

import streamlit as st

from src.auth_utils import get_session_user
from src.database import Analysis, get_db
from src.ui.list_pages import (
    fmt_dt,
    inject_list_page_css,
    render_bulk_action_bar,
    render_delete_confirm,
    render_empty_state,
    render_meta_line,
    render_page_header,
    render_toolbar,
    score_badge_html,
    sparkline_svg,
)


_SORT_OPTIONS: dict[str, tuple[str, bool]] = {
    "Newest first": ("created_at", True),
    "Oldest first": ("created_at", False),
    "Highest score": ("score", True),
    "Lowest score": ("score", False),
    "CV name (A–Z)": ("name", False),
}

_SS_SELECT_MODE = "myanalyses_select_mode"
_SS_SELECTED = "myanalyses_selected_ids"
_SS_EXPANDED = "myanalyses_expanded_groups"
_SS_SEARCH = "myanalyses_search"
_SS_SORT = "myanalyses_sort"
_SS_CONFIRM_BULK = "myanalyses_confirm_bulk"


def _go_to_home() -> None:
    st.session_state["page"] = "home"
    st.rerun()


def _open_report(analysis: Analysis) -> None:
    st.session_state["analysis"] = analysis.result
    st.session_state["cv_name"] = analysis.cv_name
    st.session_state["jd"] = analysis.job_description
    st.session_state["report_snapshot_id"] = analysis.id
    st.session_state["page"] = "report"
    st.rerun()


def _delete_ids(ids: Iterable[str]) -> int:
    id_list = [str(i) for i in ids if i]
    if not id_list:
        return 0
    db = get_db()
    try:
        deleted = (
            db.query(Analysis)
            .filter(Analysis.id.in_(id_list))
            .delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    finally:
        db.close()


def _matches_search(analysis: Analysis, needle: str) -> bool:
    if not needle:
        return True
    needle = needle.lower().strip()
    haystack = " ".join(
        str(getattr(analysis, attr, "") or "")
        for attr in ("cv_name", "job_description")
    ).lower()
    return needle in haystack


def _sort_value(analysis: Analysis, field: str):
    if field == "score":
        return float(getattr(analysis, "match_score", 0) or 0)
    if field == "name":
        return str(getattr(analysis, "cv_name", "") or "").lower()
    return getattr(analysis, "created_at", datetime.min)


def _group_key(analysis: Analysis) -> tuple[str, str]:
    cv = str(getattr(analysis, "cv_name", "") or "").strip().lower()
    jd = str(getattr(analysis, "job_description", "") or "").strip().lower()
    return cv, jd


def _ensure_state() -> None:
    st.session_state.setdefault(_SS_SELECT_MODE, False)
    if not isinstance(st.session_state.get(_SS_SELECTED), set):
        st.session_state[_SS_SELECTED] = set()
    if not isinstance(st.session_state.get(_SS_EXPANDED), set):
        st.session_state[_SS_EXPANDED] = set()


def _render_select_checkbox(analysis_id: str) -> None:
    """Render a checkbox in select mode and reflect its state into the set."""
    selected: set = st.session_state[_SS_SELECTED]
    key = f"myanalyses_select_{analysis_id}"
    checked = st.checkbox(
        "Select",
        key=key,
        value=analysis_id in selected,
        label_visibility="collapsed",
    )
    if checked:
        selected.add(analysis_id)
    else:
        selected.discard(analysis_id)


def _render_flat_card(analysis: Analysis, *, select_mode: bool) -> None:
    """A standalone (un-grouped) analysis row."""
    score = float(getattr(analysis, "match_score", 0) or 0)
    jd_raw = analysis.job_description or ""
    jd_short = jd_raw[:80] + ("…" if len(jd_raw) > 80 else "")
    safe_cv = html.escape(str(analysis.cv_name or "(untitled)"))
    safe_jd = html.escape(jd_short) if jd_short else ""
    jd_chip = (
        f'<span class="lp-chip lp-chip--neutral" title="{html.escape(jd_raw)}">'
        f"JD · {safe_jd}</span>"
        if safe_jd
        else ""
    )

    with st.container(key=f"lp_card_analysis_{analysis.id}"):
        if select_mode:
            col_check, col_body = st.columns([0.07, 0.93], gap="small")
            with col_check:
                with st.container(key=f"lp_select_analysis_{analysis.id}"):
                    _render_select_checkbox(analysis.id)
        else:
            col_body = st.container()

        with col_body:
            st.markdown(
                f"""
                <div class="lp-card-row">
                    <p class="lp-card-title">
                        {safe_cv}
                        {jd_chip}
                    </p>
                    {score_badge_html(score, suffix="")}
                </div>
                <p class="lp-card-meta">{render_meta_line([fmt_dt(analysis.created_at)])}</p>
                """,
                unsafe_allow_html=True,
            )

            if not select_mode:
                _render_card_actions(analysis)


def _render_card_actions(analysis: Analysis) -> None:
    """Open + icon-delete pair shown when not in select mode."""
    col_spacer, col_open, col_del = st.columns([5, 1.4, 0.55], gap="small")
    with col_open:
        with st.container(key=f"lp_action_open_analysis_{analysis.id}"):
            if st.button("Open", key=f"myanalyses_open_{analysis.id}", width="stretch"):
                _open_report(analysis)
    with col_del:
        with st.container(key=f"lp_action_icon_delete_analysis_{analysis.id}"):
            if st.button(
                ":material/delete:",
                key=f"myanalyses_del_{analysis.id}",
                type="tertiary",
            ):
                st.session_state[f"confirm_delete_analysis_{analysis.id}"] = True

    if st.session_state.get(f"confirm_delete_analysis_{analysis.id}"):
        def _do_delete(target_id=str(analysis.id)):
            _delete_ids([target_id])
            st.session_state.pop(f"confirm_delete_analysis_{target_id}", None)
            st.session_state["ui_toast"] = {"message": "Analysis deleted.", "icon": "🗑️"}
            st.rerun()

        render_delete_confirm(
            key=f"analysis_{analysis.id}",
            message="Delete this analysis?",
            on_confirm=_do_delete,
        )


def _render_group_card(
    group_id: str,
    runs: Sequence[Analysis],
    *,
    select_mode: bool,
) -> None:
    """Collapsed/expanded card for multiple runs of the same (CV, JD)."""
    latest = runs[0]  # runs come in pre-sorted newest-first
    scores = [float(getattr(r, "match_score", 0) or 0) for r in runs]
    latest_score = scores[0]
    s_min, s_max = min(scores), max(scores)
    jd_raw = latest.job_description or ""
    jd_short = jd_raw[:80] + ("…" if len(jd_raw) > 80 else "")
    safe_cv = html.escape(str(latest.cv_name or "(untitled)"))
    safe_jd = html.escape(jd_short) if jd_short else ""
    jd_chip = (
        f'<span class="lp-chip lp-chip--neutral" title="{html.escape(jd_raw)}">'
        f"JD · {safe_jd}</span>"
        if safe_jd
        else ""
    )
    # Sparkline reads oldest→latest left-to-right.
    spark = sparkline_svg(list(reversed(scores)))
    range_label = f"{int(s_min)}–{int(s_max)}" if s_min != s_max else f"{int(s_min)}"
    summary = render_meta_line(
        [
            f"{len(runs)} runs",
            f"scores {range_label}",
            f"latest {fmt_dt(latest.created_at)}",
        ]
    )

    expanded_set: set = st.session_state[_SS_EXPANDED]
    is_expanded = group_id in expanded_set

    with st.container(key=f"lp_card_group_{group_id}"):
        if select_mode:
            col_check, col_body = st.columns([0.07, 0.93], gap="small")
            with col_check:
                # Group select toggles ALL underlying ids — convenient bulk.
                _render_group_select(group_id, runs)
        else:
            col_body = st.container()

        with col_body:
            st.markdown(
                f"""
                <div class="lp-card-row">
                    <p class="lp-card-title">
                        {safe_cv}
                        <span class="lp-chip lp-chip--brand">{len(runs)} runs</span>
                        {jd_chip}
                    </p>
                    <div class="lp-card-actions">
                        {spark}
                        {score_badge_html(latest_score, suffix="")}
                    </div>
                </div>
                <p class="lp-card-meta lp-group-summary">{summary}</p>
                """,
                unsafe_allow_html=True,
            )

            if not select_mode:
                col_spacer, col_expand, col_open, col_del = st.columns(
                    [4, 1.7, 1.4, 0.55], gap="small"
                )
                with col_expand:
                    label = "Hide runs" if is_expanded else f"Show {len(runs)} runs"
                    if st.button(label, key=f"myanalyses_toggle_{group_id}", width="stretch"):
                        if is_expanded:
                            expanded_set.discard(group_id)
                        else:
                            expanded_set.add(group_id)
                        st.rerun()
                with col_open:
                    with st.container(key=f"lp_action_open_group_{group_id}"):
                        if st.button(
                            "Open latest",
                            key=f"myanalyses_openlatest_{group_id}",
                            width="stretch",
                        ):
                            _open_report(latest)
                with col_del:
                    with st.container(key=f"lp_action_icon_delete_group_{group_id}"):
                        if st.button(
                            ":material/delete:",
                            key=f"myanalyses_groupdel_{group_id}",
                            type="tertiary",
                        ):
                            st.session_state[f"confirm_delete_group_{group_id}"] = True

                if st.session_state.get(f"confirm_delete_group_{group_id}"):
                    def _do_group_delete(target_ids=tuple(str(r.id) for r in runs), gid=group_id):
                        n = _delete_ids(target_ids)
                        st.session_state.pop(f"confirm_delete_group_{gid}", None)
                        st.session_state["ui_toast"] = {
                            "message": f"Deleted {n} run{'s' if n != 1 else ''}.",
                            "icon": "🗑️",
                        }
                        st.rerun()

                    render_delete_confirm(
                        key=f"group_{group_id}",
                        message=f"Delete all {len(runs)} runs in this group?",
                        on_confirm=_do_group_delete,
                    )

            if is_expanded:
                _render_group_expansion(runs, select_mode=select_mode)


def _render_group_select(group_id: str, runs: Sequence[Analysis]) -> None:
    """One checkbox at the group level that toggles every run in the group."""
    selected: set = st.session_state[_SS_SELECTED]
    run_ids = [str(r.id) for r in runs]
    all_selected = bool(run_ids) and all(rid in selected for rid in run_ids)
    with st.container(key=f"lp_select_group_{group_id}"):
        new_state = st.checkbox(
            "Select group",
            key=f"myanalyses_groupselect_{group_id}",
            value=all_selected,
            label_visibility="collapsed",
        )
    if new_state and not all_selected:
        selected.update(run_ids)
    elif not new_state and all_selected:
        for rid in run_ids:
            selected.discard(rid)


def _render_group_expansion(runs: Sequence[Analysis], *, select_mode: bool) -> None:
    """Sub-list of individual runs inside an expanded group card."""
    for run in runs:
        score = float(getattr(run, "match_score", 0) or 0)
        safe_time = html.escape(fmt_dt(run.created_at))
        with st.container(key=f"lp_subrun_{run.id}"):
            cols = st.columns([0.08, 4, 1, 1.2, 0.55], gap="small") if not select_mode \
                else st.columns([0.08, 4, 1, 1.2, 0.55], gap="small")
            with cols[0]:
                if select_mode:
                    _render_select_checkbox(str(run.id))
            with cols[1]:
                st.markdown(
                    f'<div class="lp-subrun-line"><span class="lp-subrun-time">{safe_time}</span></div>',
                    unsafe_allow_html=True,
                )
            with cols[2]:
                st.markdown(score_badge_html(score, suffix=""), unsafe_allow_html=True)
            if not select_mode:
                with cols[3]:
                    with st.container(key=f"lp_action_open_sub_{run.id}"):
                        if st.button(
                            "Open",
                            key=f"myanalyses_openrun_{run.id}",
                            width="stretch",
                        ):
                            _open_report(run)
                with cols[4]:
                    with st.container(key=f"lp_action_icon_delete_sub_{run.id}"):
                        if st.button(
                            ":material/delete:",
                            key=f"myanalyses_delrun_{run.id}",
                            type="tertiary",
                        ):
                            st.session_state[f"confirm_delete_analysis_{run.id}"] = True

        if st.session_state.get(f"confirm_delete_analysis_{run.id}"):
            def _do_delete(target_id=str(run.id)):
                _delete_ids([target_id])
                st.session_state.pop(f"confirm_delete_analysis_{target_id}", None)
                st.session_state["ui_toast"] = {"message": "Run deleted.", "icon": "🗑️"}
                st.rerun()

            render_delete_confirm(
                key=f"analysis_{run.id}",
                message="Delete this run?",
                on_confirm=_do_delete,
            )


def render_my_analyses_page() -> None:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to view your analysis history.")
        return

    inject_list_page_css()
    _ensure_state()

    with st.container(key="lp_shell_myanalyses"):
        db = get_db()
        try:
            analyses: list[Analysis] = (
                db.query(Analysis)
                .filter(Analysis.user_id == user["id"])
                .order_by(Analysis.created_at.desc())
                .all()
            )
        finally:
            db.close()

        render_page_header(
            title="My Analyses",
            subtitle="Every CV vs job-description run you've saved. Search, sort, group, or clear them out in bulk.",
            count=len(analyses),
            count_label_singular="analysis",
            count_label_plural="analyses",
        )

        if not analyses:
            render_empty_state(
                icon="🔍",
                title="No analyses saved yet",
                body="Upload your CV with a job description on the home page to get an ATS score, missing-keyword report and quick fixes.",
                cta_label="Analyse a CV",
                cta_key="myanalyses_empty_cta",
                on_cta=_go_to_home,
            )
            return

        # ── Toolbar ────────────────────────────────────────────────
        search, sort_label, new_select_mode = render_toolbar(
            key="myanalyses",
            search_key=_SS_SEARCH,
            sort_key=_SS_SORT,
            sort_options=list(_SORT_OPTIONS.keys()),
            select_mode=bool(st.session_state.get(_SS_SELECT_MODE, False)),
            select_toggle_key="myanalyses_toggle_select",
            search_placeholder="Search by CV name or JD…",
        )
        if new_select_mode != st.session_state.get(_SS_SELECT_MODE):
            st.session_state[_SS_SELECT_MODE] = new_select_mode
            if not new_select_mode:
                # Leaving select mode wipes the pending selection.
                st.session_state[_SS_SELECTED] = set()
                st.session_state.pop(_SS_CONFIRM_BULK, None)
            st.rerun()

        select_mode = bool(st.session_state.get(_SS_SELECT_MODE, False))

        # ── Filter + sort ─────────────────────────────────────────
        filtered = [a for a in analyses if _matches_search(a, search)]
        sort_field, sort_desc = _SORT_OPTIONS.get(str(sort_label), ("created_at", True))
        filtered.sort(key=lambda a: _sort_value(a, sort_field), reverse=sort_desc)

        if not filtered:
            st.info("No analyses match your filter. Try a different search term or clear it.")
            return

        # ── Group runs that share the same (CV, JD) ───────────────
        groups: dict[tuple[str, str], list[Analysis]] = defaultdict(list)
        order: list[tuple[str, str]] = []
        for a in filtered:
            k = _group_key(a)
            if k not in groups:
                order.append(k)
            groups[k].append(a)

        # ── Bulk action bar (only when in select mode) ────────────
        if select_mode:
            selected: set = st.session_state[_SS_SELECTED]
            confirm_pending = bool(st.session_state.get(_SS_CONFIRM_BULK))

            def _request_bulk_confirm():
                st.session_state[_SS_CONFIRM_BULK] = True
                st.rerun()

            def _exit_select_mode():
                st.session_state[_SS_SELECT_MODE] = False
                st.session_state[_SS_SELECTED] = set()
                st.session_state.pop(_SS_CONFIRM_BULK, None)
                st.rerun()

            render_bulk_action_bar(
                key="myanalyses",
                selected_count=len(selected),
                confirm_label=f"Delete selected ({len(selected)})",
                on_confirm=_request_bulk_confirm,
                on_cancel=_exit_select_mode,
            )

            if confirm_pending:
                def _do_bulk_delete():
                    ids = list(st.session_state.get(_SS_SELECTED) or [])
                    n = _delete_ids(ids)
                    st.session_state[_SS_SELECTED] = set()
                    st.session_state[_SS_SELECT_MODE] = False
                    st.session_state.pop(_SS_CONFIRM_BULK, None)
                    st.session_state["ui_toast"] = {
                        "message": f"Deleted {n} analys{'is' if n == 1 else 'es'}.",
                        "icon": "🗑️",
                    }
                    st.rerun()

                render_delete_confirm(
                    key="bulk_myanalyses",
                    message=f"Delete {len(selected)} selected analyses?",
                    on_confirm=_do_bulk_delete,
                )

        # ── Render groups (flat card when N==1, grouped card otherwise) ──
        for key in order:
            runs = groups[key]
            if len(runs) == 1:
                _render_flat_card(runs[0], select_mode=select_mode)
            else:
                group_id = f"{abs(hash(key))}"
                _render_group_card(group_id, runs, select_mode=select_mode)
