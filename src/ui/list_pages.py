"""Shared primitives for collection list pages (My CVs / My Analyses / My Comparisons).

Centralises card layout, score badges, empty states and delete-confirmation UI
so all three pages stay visually consistent and share one stylesheet.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Callable, Iterable, Sequence

import streamlit as st


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%b %d, %Y · %H:%M") if dt else "—"


def score_badge_html(score: float, suffix: str = "%") -> str:
    """Return an HTML span styled by score tier (good / mid / low)."""
    try:
        value = float(score or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value >= 75:
        tier = "good"
    elif value >= 50:
        tier = "mid"
    else:
        tier = "low"
    label = f"{value:.0f}{suffix}"
    return (
        f'<span class="lp-score lp-score--{tier}">'
        f'<span class="lp-score-dot"></span>{label}</span>'
    )


def inject_list_page_css() -> None:
    """Inject the unified collection-page stylesheet.

    Must be called on every rerun — Streamlit re-renders the whole script per
    interaction, so a session-state gate would cause the ``<style>`` block to
    disappear from the DOM after the first render and the cards would revert
    to raw Streamlit defaults.

    Tokens come from the global theme so light/dark switching is automatic.
    """
    st.markdown(
        """
        <style>
        /* ── Page shell ──────────────────────────────────────────── */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_shell_"] {
            margin-top: -72px !important;
        }
        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] [class*="st-key-lp_shell_"] {
                margin-top: -38px !important;
            }
        }

        /* ── Header ─────────────────────────────────────────────── */
        .lp-head {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin: 0 0 1.25rem;
            flex-wrap: wrap;
        }
        .lp-head-left h2 {
            margin: 0 0 0.25rem;
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: var(--text-primary);
        }
        .lp-head-left p {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.92rem;
        }
        .lp-head-count {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.32rem 0.85rem;
            border-radius: 999px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            font-size: 0.82rem;
            font-weight: 700;
            box-shadow: 0 1px 2px var(--shadow);
        }
        .lp-head-count-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #6366f1);
        }

        /* ── Card ───────────────────────────────────────────────── */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"] {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.05rem 1.25rem 0.9rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px var(--shadow);
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
            position: relative;
            overflow: hidden;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"]:hover {
            border-color: rgba(99, 102, 241, 0.45);
            box-shadow: 0 8px 22px var(--shadow);
            transform: translateY(-1px);
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"]::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            background: linear-gradient(180deg, #3b82f6, #6366f1);
            opacity: 0;
            transition: opacity 0.18s ease;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"]:hover::before {
            opacity: 1;
        }

        .lp-card-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.3rem;
        }
        .lp-card-title {
            margin: 0;
            font-size: 1.02rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.35;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .lp-card-meta {
            margin: 0.2rem 0 0;
            font-size: 0.78rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.55rem;
            flex-wrap: wrap;
        }
        .lp-card-meta-sep {
            color: var(--border-color);
        }
        .lp-card-jd {
            margin: 0.55rem 0 0;
            padding: 0.55rem 0.75rem;
            border-left: 2px solid rgba(99, 102, 241, 0.35);
            background: linear-gradient(90deg, rgba(99,102,241,0.06), transparent);
            border-radius: 0 6px 6px 0;
            font-size: 0.84rem;
            color: var(--text-secondary);
            line-height: 1.45;
        }

        /* ── Chips ──────────────────────────────────────────────── */
        .lp-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            line-height: 1.4;
        }
        .lp-chip--brand {
            background: rgba(99, 102, 241, 0.12);
            color: #4f46e5;
            border: 1px solid rgba(99, 102, 241, 0.22);
        }
        body.theme-dark .lp-chip--brand {
            background: rgba(129, 140, 248, 0.16);
            color: #a5b4fc;
            border-color: rgba(129, 140, 248, 0.3);
        }
        .lp-chip--neutral {
            background: rgba(148, 163, 184, 0.16);
            color: var(--text-secondary);
            border: 1px solid rgba(148, 163, 184, 0.22);
        }

        /* ── Score badge ────────────────────────────────────────── */
        .lp-score {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            white-space: nowrap;
            border: 1px solid transparent;
        }
        .lp-score-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
        }
        .lp-score--good {
            background: rgba(34, 197, 94, 0.14);
            color: #15803d;
            border-color: rgba(34, 197, 94, 0.28);
        }
        body.theme-dark .lp-score--good {
            color: #4ade80;
            background: rgba(34, 197, 94, 0.18);
        }
        .lp-score--good .lp-score-dot { background: #22c55e; }
        .lp-score--mid {
            background: rgba(245, 158, 11, 0.14);
            color: #b45309;
            border-color: rgba(245, 158, 11, 0.28);
        }
        body.theme-dark .lp-score--mid {
            color: #fbbf24;
            background: rgba(245, 158, 11, 0.18);
        }
        .lp-score--mid .lp-score-dot { background: #f59e0b; }
        .lp-score--low {
            background: rgba(239, 68, 68, 0.14);
            color: #b91c1c;
            border-color: rgba(239, 68, 68, 0.28);
        }
        body.theme-dark .lp-score--low {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.18);
        }
        .lp-score--low .lp-score-dot { background: #ef4444; }

        /* ── Action row buttons: tighter, secondary-styled ────── */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"] [data-testid="stHorizontalBlock"] {
            margin-top: 0.55rem !important;
            gap: 0.5rem !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"] .stButton button {
            min-height: 38px !important;
            padding: 0.45rem 0.9rem !important;
            font-size: 0.86rem !important;
            border-radius: 10px !important;
        }
        /* Delete button: outline-only, no inner shading.
           Specificity is doubled with the chained attribute selector so we
           outrank the global `.stButton button:hover *` rule that would
           otherwise paint a filled `--button-hover-bg` inside the button. */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:hover,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:focus-visible,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] [data-baseweb="button"],
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] [data-baseweb="button"]:hover {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            filter: none !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:hover *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:focus *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] [data-baseweb="button"] * {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
            color: #ef4444 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button {
            color: #ef4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.32) !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:hover {
            background: rgba(239, 68, 68, 0.10) !important;
            background-color: rgba(239, 68, 68, 0.10) !important;
            border-color: rgba(239, 68, 68, 0.55) !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] [class*="st-key-lp_action_delete_"][class*="st-key-lp_action_delete_"] button:hover {
            background: rgba(239, 68, 68, 0.16) !important;
            background-color: rgba(239, 68, 68, 0.16) !important;
        }

        /* ── Inline delete-confirm panel ──────────────────────────
           Key is ``lp_confirm_panel_<...>`` specifically (not
           ``lp_confirm_<...>``) so this rule doesn't also paint the
           inner button containers (``lp_confirm_yes_<...>`` /
           ``lp_confirm_no_<...>``), which would otherwise inherit the
           pink wash and create a "box inside a box" effect. */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_panel_"] {
            background: linear-gradient(180deg, rgba(239,68,68,0.06), rgba(239,68,68,0.02));
            border: 1px solid rgba(239, 68, 68, 0.32);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            margin-top: 0.6rem;
        }
        /* ── Confirm-panel buttons: outlined w/ destructive vs. safe hover ──
           "Yes, delete" → red ink + red wash on hover (destructive).
           "Cancel"      → neutral ink + green wash on hover (safe).
           Specificity is doubled to outrank the global button rules in
           base_theme.css.tpl (which would otherwise flatten both to the
           default theme button look). */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            color: #ef4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.45) !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] button p {
            background: transparent !important;
            color: #ef4444 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_yes_"][class*="st-key-lp_confirm_yes_"] button:hover {
            background: rgba(239, 68, 68, 0.12) !important;
            background-color: rgba(239, 68, 68, 0.12) !important;
            border-color: rgba(239, 68, 68, 0.65) !important;
        }

        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:focus,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] [data-baseweb="button"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button p {
            background: transparent !important;
            color: var(--text-primary) !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover {
            background: rgba(34, 197, 94, 0.12) !important;
            background-color: rgba(34, 197, 94, 0.12) !important;
            border-color: rgba(34, 197, 94, 0.55) !important;
            color: #15803d !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover p {
            color: #15803d !important;
        }
        body.theme-dark [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover,
        body.theme-dark [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover *,
        body.theme-dark [data-testid="stAppViewContainer"] [class*="st-key-lp_confirm_no_"][class*="st-key-lp_confirm_no_"] button:hover p {
            color: #4ade80 !important;
        }
        .lp-confirm-text {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin: 0 0 0.6rem;
            color: var(--text-primary);
            font-size: 0.9rem;
            font-weight: 600;
        }
        .lp-confirm-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 999px;
            background: rgba(239, 68, 68, 0.18);
            color: #dc2626;
            font-size: 0.85rem;
            font-weight: 800;
            flex-shrink: 0;
        }
        .lp-confirm-sub {
            color: var(--text-secondary);
            font-size: 0.82rem;
            font-weight: 500;
        }

        /* ── Toolbar (search + sort + select-mode toggle) ──────── */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 0.55rem 0.75rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px var(--shadow);
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] [data-testid="stHorizontalBlock"] {
            align-items: end !important;
            gap: 0.65rem !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] .stTextInput,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] .stSelectbox {
            margin: 0 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] .stTextInput input,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] .stSelectbox [data-baseweb="select"] {
            min-height: 38px !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] [data-testid="stWidgetLabel"] {
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary) !important;
            margin-bottom: 0.2rem !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_toolbar_"] .stButton button {
            min-height: 38px !important;
            padding: 0 0.85rem !important;
            font-size: 0.84rem !important;
            border-radius: 10px !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_bulk_bar_"] {
            background: linear-gradient(135deg, rgba(99,102,241,0.10), rgba(59,130,246,0.06));
            border: 1px solid rgba(99,102,241,0.32);
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            margin-bottom: 0.85rem;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_bulk_bar_"] [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        .lp-bulk-count {
            font-weight: 700;
            color: var(--text-primary);
            font-size: 0.92rem;
        }

        /* ── Card action row: compact Open + icon Delete ────────── */
        .lp-card-actions {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            margin-left: auto;
            flex-shrink: 0;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_open_"] button {
            min-height: 34px !important;
            padding: 0 0.85rem !important;
            font-size: 0.82rem !important;
            border-radius: 9px !important;
            font-weight: 600 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_icon_delete_"][class*="st-key-lp_action_icon_delete_"] button,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_icon_delete_"][class*="st-key-lp_action_icon_delete_"] [data-baseweb="button"] {
            min-height: 34px !important;
            min-width: 34px !important;
            width: 34px !important;
            height: 34px !important;
            padding: 0 !important;
            border-radius: 9px !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: 1px solid rgba(239, 68, 68, 0.32) !important;
            color: #ef4444 !important;
            box-shadow: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_icon_delete_"][class*="st-key-lp_action_icon_delete_"] button *,
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_icon_delete_"][class*="st-key-lp_action_icon_delete_"] button p {
            background: transparent !important;
            background-color: transparent !important;
            color: #ef4444 !important;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_action_icon_delete_"][class*="st-key-lp_action_icon_delete_"] button:hover {
            background: rgba(239, 68, 68, 0.12) !important;
            background-color: rgba(239, 68, 68, 0.12) !important;
            border-color: rgba(239, 68, 68, 0.55) !important;
        }

        /* ── Group card (collapsed/expanded repeated runs) ──────── */
        .lp-group-summary {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            color: var(--text-secondary);
            font-size: 0.82rem;
            flex-wrap: wrap;
        }
        .lp-group-summary-sep {
            color: var(--border-color);
        }
        .lp-sparkline {
            vertical-align: middle;
            opacity: 0.92;
        }
        [data-testid="stAppViewContainer"] [class*="st-key-lp_subrun_"] {
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.4rem 0.7rem 0.4rem 0.85rem;
            margin: 0.35rem 0 0;
        }
        .lp-subrun-line {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            color: var(--text-secondary);
            font-size: 0.82rem;
        }
        .lp-subrun-time {
            color: var(--text-primary);
            font-weight: 600;
        }

        /* ── Select-mode checkbox spacing ───────────────────────── */
        [data-testid="stAppViewContainer"] [class*="st-key-lp_card_"] [class*="st-key-lp_select_"] {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            min-height: 38px;
        }

        /* ── Empty state ────────────────────────────────────────── */
        .lp-empty {
            text-align: center;
            padding: 3rem 1.5rem;
            border: 1.5px dashed var(--border-color);
            border-radius: 18px;
            background: linear-gradient(180deg, var(--bg-card), transparent);
            margin: 1rem 0 1.5rem;
        }
        .lp-empty-icon {
            font-size: 2.4rem;
            line-height: 1;
            margin-bottom: 0.7rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(59,130,246,0.10));
            border: 1px solid rgba(99,102,241,0.22);
        }
        .lp-empty-title {
            margin: 0 0 0.4rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        .lp-empty-body {
            margin: 0 auto 1.2rem;
            max-width: 460px;
            color: var(--text-secondary);
            font-size: 0.92rem;
            line-height: 1.55;
        }
        [data-testid="stAppViewContainer"] .lp-empty-cta-wrap [data-testid="stButton"] {
            display: flex;
            justify-content: center;
        }
        [data-testid="stAppViewContainer"] .lp-empty-cta-wrap [data-testid="stButton"] button {
            min-width: 220px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    *,
    title: str,
    subtitle: str,
    count: int | None,
    count_label_singular: str,
    count_label_plural: str | None = None,
) -> None:
    """Render the unified page header with title, subtitle and pill counter."""
    plural = count_label_plural or (count_label_singular + "s")
    if count is None:
        count_html = ""
    else:
        word = count_label_singular if count == 1 else plural
        count_html = (
            f'<span class="lp-head-count">'
            f'<span class="lp-head-count-dot"></span>{count} {word}'
            f"</span>"
        )
    st.markdown(
        f"""
        <div class="lp-head">
            <div class="lp-head-left">
                <h2>{html.escape(title)}</h2>
                <p>{html.escape(subtitle)}</p>
            </div>
            {count_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(
    *,
    icon: str,
    title: str,
    body: str,
    cta_label: str,
    cta_key: str,
    on_cta: Callable[[], None],
) -> None:
    """Render a friendly empty state with a centred CTA."""
    st.markdown(
        f"""
        <div class="lp-empty">
            <div class="lp-empty-icon">{icon}</div>
            <p class="lp-empty-title">{html.escape(title)}</p>
            <p class="lp-empty-body">{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="lp-empty-cta-wrap">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(cta_label, key=cta_key, type="primary", width="stretch"):
                on_cta()
        st.markdown("</div>", unsafe_allow_html=True)


def render_card_shell(card_key: str, body_html: str) -> None:
    """Open a list card with the unified shell and inject the card body HTML.

    The card itself is a Streamlit container so action buttons can be placed
    inside the same surface (consistent hover/border state).
    """
    st.markdown(body_html, unsafe_allow_html=True)


def render_meta_line(parts: Iterable[str]) -> str:
    """Compose a meta line ('Created · Updated · …') with separators."""
    bits: list[str] = []
    items = [p for p in parts if p]
    for i, p in enumerate(items):
        bits.append(html.escape(p))
        if i < len(items) - 1:
            bits.append('<span class="lp-card-meta-sep">·</span>')
    return " ".join(bits)


def render_delete_confirm(
    *,
    key: str,
    message: str,
    sub_message: str = "This action cannot be undone.",
    confirm_label: str = "Yes, delete",
    on_confirm: Callable[[], None],
) -> None:
    """Render an inline destructive-action confirmation panel.

    Caller is responsible for guarding the call with the corresponding session
    flag (so the panel only appears after the user clicks the trigger).
    """
    with st.container(key=f"lp_confirm_panel_{key}"):
        st.markdown(
            f"""
            <div class="lp-confirm-text">
                <span class="lp-confirm-icon">!</span>
                <span>
                    {html.escape(message)}
                    <span class="lp-confirm-sub">— {html.escape(sub_message)}</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, _ = st.columns([1.3, 1, 2])
        with c1:
            if st.button(confirm_label, key=f"lp_confirm_yes_{key}", type="primary", width="stretch"):
                on_confirm()
        with c2:
            if st.button("Cancel", key=f"lp_confirm_no_{key}", width="stretch"):
                st.session_state.pop(f"confirm_delete_{key}", None)
                st.rerun()


def sparkline_svg(
    values: Sequence[float],
    *,
    width: int = 96,
    height: int = 26,
    color: str = "#6366f1",
) -> str:
    """Tiny inline SVG sparkline for a sequence of score values.

    Returns an empty string when fewer than two points are available — caller
    should render a flat hyphen or omit the sparkline in that case.
    """
    pts = [float(v) for v in values if v is not None]
    if len(pts) < 2:
        return ""
    vmin = min(pts)
    vmax = max(pts)
    rng = max(vmax - vmin, 1.0)
    n = len(pts) - 1
    coords: list[str] = []
    for i, v in enumerate(pts):
        x = 1 + (i / n) * (width - 2)
        y = (height - 2) - ((v - vmin) / rng) * (height - 4) + 1
        coords.append(f"{x:.1f},{y:.1f}")
    last_x, last_y = coords[-1].split(",")
    poly = " ".join(coords)
    return (
        f'<svg class="lp-sparkline" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" aria-hidden="true">'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" points="{poly}" />'
        f'<circle cx="{last_x}" cy="{last_y}" r="2" fill="{color}" />'
        f"</svg>"
    )


def render_toolbar(
    *,
    key: str,
    search_key: str,
    sort_key: str,
    sort_options: Sequence[str],
    select_mode: bool,
    select_toggle_key: str,
    search_placeholder: str = "Search…",
) -> tuple[str, str, bool]:
    """Render the search + sort + select-mode toolbar.

    Returns ``(search_value, sort_value, select_mode_after_click)``. The caller
    persists ``select_mode`` in session state — the returned bool is the new
    desired state (already toggled if the user clicked the button).
    """
    new_select_mode = select_mode
    with st.container(key=f"lp_toolbar_{key}"):
        c_search, c_sort, c_btn = st.columns([3, 2, 1.2], gap="small")
        with c_search:
            search_value = st.text_input(
                "Search",
                key=search_key,
                placeholder=search_placeholder,
                label_visibility="collapsed",
            )
        with c_sort:
            sort_value = st.selectbox(
                "Sort",
                options=list(sort_options),
                key=sort_key,
                label_visibility="collapsed",
            )
        with c_btn:
            label = "Done" if select_mode else "Select"
            if st.button(label, key=select_toggle_key, width="stretch"):
                new_select_mode = not select_mode
    return search_value, sort_value, new_select_mode


def render_bulk_action_bar(
    *,
    key: str,
    selected_count: int,
    confirm_label: str,
    on_confirm: Callable[[], None],
    on_cancel: Callable[[], None] | None = None,
) -> None:
    """Floating bar shown above the list while in select mode."""
    with st.container(key=f"lp_bulk_bar_{key}"):
        c_label, c_confirm, c_cancel = st.columns([4, 2, 1.2], gap="small")
        with c_label:
            word = "item" if selected_count == 1 else "items"
            st.markdown(
                f'<div class="lp-bulk-count">{selected_count} {word} selected</div>',
                unsafe_allow_html=True,
            )
        with c_confirm:
            disabled = selected_count == 0
            if st.button(
                confirm_label,
                key=f"lp_bulk_confirm_{key}",
                type="primary",
                width="stretch",
                disabled=disabled,
            ):
                on_confirm()
        with c_cancel:
            if st.button("Cancel", key=f"lp_bulk_cancel_{key}", width="stretch"):
                if on_cancel:
                    on_cancel()


def reset_css_marker() -> None:
    """No-op kept for backwards compatibility; CSS is now always re-emitted."""
    st.session_state.pop("_lp_css_injected", None)


# Re-exported helpers used by the three pages.
fmt_dt = _fmt_dt

__all__ = [
    "fmt_dt",
    "score_badge_html",
    "sparkline_svg",
    "inject_list_page_css",
    "render_page_header",
    "render_empty_state",
    "render_card_shell",
    "render_delete_confirm",
    "render_meta_line",
    "render_toolbar",
    "render_bulk_action_bar",
    "reset_css_marker",
]
