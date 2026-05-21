"""Resume Tips pillar page and sub-guide article renderers.

Architecture
------------
- Each sub-guide is a separate app route registered in ``APP_PAGES`` and
  recorded as a key in :data:`GUIDES_META`. Routing in ``app.py`` dispatches
  any ``current_page`` that's a member of ``GUIDES_META`` to
  :func:`render_guide_article` here.
- Metadata for every guide (title, byline, date, related slugs, …) lives in
  :data:`GUIDES_META` below — single source of truth used by the pillar's
  section cards, the article shell, and the "Continue learning" footer block.
- Prose lives in ``docs/guides/{slug}.md`` so long-form content stays out of
  Python triple-quoted strings.
- Pillar sections (``SECTIONS``) declare the hub-and-spoke ordering: which
  guides appear in which section of the pillar page.
- Site-wide FAQ (``FAQ_ITEMS``) renders at the bottom of the pillar.

All articles use the byline "ExcelCV Editorial Team". Adding/reordering guides
only requires editing ``GUIDES_META`` and ``SECTIONS`` — no code changes.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from src.ui.app_utils import _build_page_href

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

GUIDES_DIR = Path(__file__).resolve().parents[2] / "docs" / "guides"

EDITORIAL_BYLINE = "ExcelCV Editorial Team"

GUIDES_META: Dict[str, Dict[str, Any]] = {
    "why-75-rejected": {
        "title": "Why 75% of Resumes Are Rejected Before a Human Sees Them",
        "tag": "Resume Help",
        "date": "May 20, 2026",
        "read_time": "7 min read",
        "summary": (
            "Three out of four resumes never reach a recruiter. Here's where the "
            "75% number comes from, why it happens, and what to fix first."
        ),
        "related": [
            "pass-ats-scanner-2026",
            "pdf-vs-docx",
            "keywords-software-engineers",
        ],
        "tags": ["ATS rejection", "applicant tracking", "resume statistics", "job search"],
    },
    "pass-ats-scanner-2026": {
        "title": "How to Pass an ATS Scanner in 2026: Step-by-Step Guide",
        "tag": "Resume Help",
        "date": "May 20, 2026",
        "read_time": "9 min read",
        "summary": (
            "The complete 9-step playbook — parsing, keywords, formatting, file "
            "naming, and testing — for any ATS in 2026."
        ),
        "related": [
            "why-75-rejected",
            "ats-friendly-templates",
            "keywords-software-engineers",
        ],
        "tags": ["ATS", "resume optimization", "applicant tracking", "resume tips"],
    },
    "pdf-vs-docx": {
        "title": "PDF vs DOCX Resume: Which Format Passes ATS Better in 2026?",
        "tag": "Resume Help",
        "date": "May 20, 2026",
        "read_time": "6 min read",
        "summary": (
            "The PDF-vs-DOCX debate finally settled with data — tested across the "
            "major ATS platforms in production today."
        ),
        "related": [
            "ats-friendly-templates",
            "pass-ats-scanner-2026",
            "why-75-rejected",
        ],
        "tags": ["PDF vs DOCX", "resume format", "ATS", "resume tips"],
    },
    "ats-friendly-templates": {
        "title": "ATS-Friendly Resume Templates and Formats",
        "tag": "Resume Help",
        "date": "May 20, 2026",
        "read_time": "5 min read",
        "summary": (
            "Optimized structure and formatting rules that keep parsers happy "
            "across every major ATS platform."
        ),
        "related": [
            "pdf-vs-docx",
            "pass-ats-scanner-2026",
            "keywords-software-engineers",
        ],
        "tags": ["resume templates", "ATS", "resume format", "job search"],
    },
    "keywords-software-engineers": {
        "title": "ATS Resume Keywords for Software Engineers in 2026",
        "tag": "Resume Help",
        "date": "May 20, 2026",
        "read_time": "9 min read",
        "summary": (
            "High-signal keywords ATS platforms scan for in software engineering "
            "resumes — broken down by backend, frontend, DevOps, and ML."
        ),
        "related": [
            "pass-ats-scanner-2026",
            "ai-hiring-tools-2026",
            "why-75-rejected",
        ],
        "tags": ["software engineer resume", "ATS keywords", "tech resume", "developer job search"],
    },
    "resume-no-experience": {
        "title": "How to Write a Resume with No Experience That Passes ATS",
        "tag": "Career Advice",
        "date": "May 20, 2026",
        "read_time": "8 min read",
        "summary": (
            "Students, new grads, and career switchers — build a resume that "
            "beats the ATS without traditional work history."
        ),
        "related": [
            "pass-ats-scanner-2026",
            "ats-friendly-templates",
            "keywords-software-engineers",
        ],
        "tags": ["no experience resume", "student resume", "new grad", "first job"],
    },
    "ai-hiring-tools-2026": {
        "title": "How AI Hiring Tools Are Changing Resume Screening in 2026",
        "tag": "Career Advice",
        "date": "May 20, 2026",
        "read_time": "9 min read",
        "summary": (
            "AI now reads, ranks, and rejects most resumes before recruiters see "
            "them. What's actually happening — and how to stay ahead."
        ),
        "related": [
            "pass-ats-scanner-2026",
            "keywords-software-engineers",
            "why-75-rejected",
        ],
        "tags": ["AI hiring", "AI recruiting", "future of work", "resume screening"],
    },
}

# Pillar page sections — order matters; this is what users see on the pillar.
SECTIONS: List[Dict[str, Any]] = [
    {
        "id": "foundations",
        "icon": "📘",
        "label": "Foundations: how ATS works and what gets rejected",
        "intro": (
            "Start here if you've never thought about ATS before. These guides "
            "explain what the software actually does and the step-by-step "
            "process that gets your resume through."
        ),
        "guides": ["why-75-rejected", "pass-ats-scanner-2026"],
    },
    {
        "id": "format-layout",
        "icon": "📄",
        "label": "File format and layout choices",
        "intro": (
            "Most parsing failures are caused by layout, not language. Get "
            "these two questions right before you write a single bullet."
        ),
        "guides": ["pdf-vs-docx", "ats-friendly-templates"],
    },
    {
        "id": "keywords",
        "icon": "🔑",
        "label": "Keywords by role and industry",
        "intro": (
            "ATS scoring lives and dies on the right keywords. Generic lists "
            "are useless — pick the guide that matches your role."
        ),
        "guides": ["keywords-software-engineers"],
    },
    {
        "id": "starters-changers",
        "icon": "🎓",
        "label": "Students, new grads, and career changers",
        "intro": (
            "ATS-friendly doesn't mean traditional experience required. If "
            "your background is non-linear, this guide is for you."
        ),
        "guides": ["resume-no-experience"],
    },
    {
        "id": "whats-changing",
        "icon": "🤖",
        "label": "What's changing in 2026",
        "intro": (
            "The ATS landscape is shifting from keyword counting to AI-driven "
            "semantic ranking. Understand what's new so you optimize for the "
            "right system."
        ),
        "guides": ["ai-hiring-tools-2026"],
    },
]

FAQ_ITEMS: List[Dict[str, str]] = [
    {
        "q": "What is an ATS and why does it matter?",
        "a": (
            "An Applicant Tracking System (ATS) is software that intakes, parses, "
            "and ranks resumes before any human sees them. By 2026 the large "
            "majority of mid-size and enterprise employers use one, which makes "
            "the ATS the first real gatekeeper in your job search."
        ),
    },
    {
        "q": "What's the single most important change to make right now?",
        "a": (
            "Switch to a clean, single-column layout with standard section "
            "headings — Work Experience, Skills, Education. Multi-column "
            '"designer" resumes are the biggest cause of ATS parsing errors. '
            "Tune wording afterward; structure first."
        ),
    },
    {
        "q": "PDF or DOCX — which is safer in 2026?",
        "a": (
            "Both work in nearly every modern ATS. DOCX is the marginally safer "
            "default because legacy enterprise systems still mis-parse some "
            "PDFs. If the job posting names a format, use it. Otherwise default "
            "to DOCX unless the employer explicitly requests PDF."
        ),
    },
    {
        "q": "How do I know which ATS a company uses?",
        "a": (
            "The application URL almost always gives it away. "
            "myworkdayjobs.com → Workday, greenhouse.io → Greenhouse, "
            "lever.co → Lever, icims.com → iCIMS, taleo.net → Taleo, "
            "bamboohr.com → BambooHR. Tailor accordingly when you can identify "
            "the platform."
        ),
    },
    {
        "q": "Is a free ATS checker as good as a paid one?",
        "a": (
            "In 2026, yes — parsing tech has commoditized. A free tool that runs "
            "your resume against the actual job description (not a generic "
            '"ATS-friendly" check) will catch the same issues a paid product '
            "would for the vast majority of applications."
        ),
    },
    {
        "q": "How often should I update my resume?",
        "a": (
            "Tailor it for every application — at minimum update the summary "
            "and skills section to mirror the new job description's keywords. "
            "Even very similar roles at different companies often demand "
            "different terms. A 10-minute tailoring pass dramatically improves "
            "callback rates."
        ),
    },
]


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


def _resolve_theme() -> str:
    """Return the current theme ('light' or 'dark') from session state.

    Reading session_state synchronously (instead of relying on the JS-applied
    ``body.theme-light`` / ``body.theme-dark`` class) lets us bake the right
    colors into the page on the very first paint — no race against the theme
    watcher in app.py, no FOUC, no half-themed cards.
    """
    raw = st.session_state.get("theme", "light")
    return "dark" if raw == "dark" else "light"


def _guide_palette(theme: str) -> Dict[str, str]:
    """Return the full palette for the guide pages for a given theme.

    All values are hard-coded (not ``var(--…)``) so the page renders
    correctly even when the global CSS variable block has not yet been
    applied to the parent document by the time the browser paints.
    """
    if theme == "dark":
        return {
            "page_bg": "transparent",
            "text_primary": "#f1f5f9",
            "text_secondary": "#cbd5e1",
            "text_muted": "#94a3b8",
            "text_body": "#e2e8f0",
            "card_bg": "#1e293b",
            "card_border": "rgba(148, 163, 184, 0.22)",
            "card_hover_bg": "#243449",
            "card_hover_border": "#7dd3fc",
            "accent": "#7dd3fc",
            "accent_strong": "#38bdf8",
            "chip_bg": "rgba(15, 23, 42, 0.55)",
            "chip_border": "rgba(148, 163, 184, 0.25)",
            "chip_text": "#cbd5e1",
            "badge_bg": "rgba(56, 189, 248, 0.16)",
            "badge_border": "rgba(56, 189, 248, 0.38)",
            "badge_text": "#7dd3fc",
            "code_bg": "rgba(15, 23, 42, 0.65)",
            "code_text": "#f1f5f9",
            "shadow": "0 8px 22px rgba(2, 6, 23, 0.45)",
        }
    return {
        "page_bg": "transparent",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "text_body": "#334155",
        "card_bg": "#ffffff",
        "card_border": "rgba(148, 163, 184, 0.40)",
        "card_hover_bg": "#f8fafc",
        "card_hover_border": "#1667d9",
        "accent": "#1667d9",
        "accent_strong": "#0369a1",
        "chip_bg": "#f1f5f9",
        "chip_border": "rgba(148, 163, 184, 0.36)",
        "chip_text": "#475569",
        "badge_bg": "rgba(14, 165, 233, 0.10)",
        "badge_border": "rgba(14, 165, 233, 0.32)",
        "badge_text": "#0369a1",
        "code_bg": "#f1f5f9",
        "code_text": "#0f172a",
        "shadow": "0 8px 22px rgba(15, 23, 42, 0.08)",
    }


def inject_guides_css() -> None:
    """Render the CSS used by the pillar page and the sub-guide article shell.

    Colors are baked in per-render based on ``st.session_state['theme']`` so
    there is no race against the JS-applied ``body.theme-…`` class. All rules
    are scoped under ``.excelcv-guide-*`` so they cannot leak into other
    pages, and every color/background rule uses ``!important`` so a stale
    CSS-variable resolution from earlier renders cannot win on cascade.
    """
    theme = _resolve_theme()
    p = _guide_palette(theme)
    st.markdown(
        f"""
        <style>
        /* Collapse the inter-block gap between sequential stElementContainers
           on guide pages so multiple st.markdown calls don't pile up vertical
           rhythm. Scoped to elements that contain our guide-* class names so
           it can't leak to other pages. */
        [data-testid="stElementContainer"]:has(> .excelcv-guide-pillar-top),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-pillar-hero),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-toc),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-section),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-faq),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-breadcrumb),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-back-link),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-tag-chip),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-article-title),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-byline),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-article-meta),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-article-body),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-article-layout),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-continue),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-tags),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-byline-card),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-placeholder) {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        /* Pull the FIRST content block on a guide page up to close the natural
           band below the site header rule. The selector uses ``:has(X)`` (any
           descendant) rather than ``:has(> X)`` (direct child) because
           Streamlit wraps st.markdown content in extra
           ``stMarkdown`` / ``stMarkdownContainer`` divs — the guide class is
           not a direct child of stElementContainer.
           On the pillar page the first block is ``.excelcv-guide-pillar-top``;
           on an article page (breadcrumb removed) the first block is the
           ``.excelcv-guide-article-meta-row``. */
        [data-testid="stElementContainer"]:has(.excelcv-guide-pillar-top),
        [data-testid="stElementContainer"]:has(.excelcv-guide-article-meta-row) {{
            margin-top: -90px !important;
        }}
        /* Bridge-button container collapse. ``st.container(key="…")`` wraps
           its children in a ``.st-key-<key>`` div AND, in recent Streamlit
           versions, ALSO in a sibling ``data-testid="stLayoutWrapper"`` div
           used for internal layout. Hiding the ``.st-key-…`` element alone
           leaves the stLayoutWrapper reserving ~60px above the article meta
           row. We have to ``display: none`` ALL three: the layout wrapper,
           the ``.st-key-…`` element, and the wrapping ``stElementContainer``.
           Streamlit buttons inside remain in the DOM and findable by the JS
           click handler — ``.click()`` fires on display:none elements too —
           so the bridge mechanism keeps working. */
        [data-testid="stLayoutWrapper"]:has(.st-key-guide_nav_action_bridge),
        [data-testid="stElementContainer"]:has(.st-key-guide_nav_action_bridge),
        .st-key-guide_nav_action_bridge {{
            display: none !important;
        }}
        /* 2-column hero + TOC row at the top of the pillar page. Hero takes
           the left column, TOC card sits on the right filling the empty band
           that used to be there. Same 50/50 ratio (``repeat(2, 1fr)``) as the
           article-card grid in each pillar section, so the page reads as one
           consistent column system top-to-bottom. Collapses to a single
           column below 900px. */
        .excelcv-guide-pillar-top {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 40px;
            align-items: start;
            margin-bottom: 0;
        }}
        @media (max-width: 900px) {{
            .excelcv-guide-pillar-top {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
        }}
        .excelcv-guide-pillar-hero {{
            /* No top padding — the parent grid is align-items: start, so the
               hero title needs to sit flush with the column top to align with
               the TOC card's top edge on the right. */
            padding: 0 0 8px;
        }}
        .excelcv-guide-pillar-badge {{
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 600;
            color: {p["badge_text"]} !important;
            background: {p["badge_bg"]} !important;
            border: 1px solid {p["badge_border"]} !important;
            padding: 4px 10px;
            border-radius: 999px;
            letter-spacing: 0.02em;
            margin-bottom: 14px;
        }}
        .excelcv-guide-pillar-title {{
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1.15;
            /* !important on margin-top so the browser/Streamlit default
               h1 margin (0.67em) doesn't push the title down,
               which leaves the TOC card on the right looking taller. */
            margin: 0 0 14px !important;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-pillar-lede {{
            color: {p["text_secondary"]} !important;
            font-size: 1.06rem;
            line-height: 1.6;
            /* No max-width — the lede now lives in a 50% grid column, so the
               column itself constrains the line length. The 64ch cap from
               when the lede was full-width is what was making it look narrow
               inside its own column. */
            margin: 0 0 18px;
        }}
        .excelcv-guide-pillar-lede strong {{
            color: {p["text_primary"]} !important;
        }}

        .excelcv-guide-toc {{
            background: {p["card_bg"]} !important;
            border: 1px solid {p["card_border"]} !important;
            border-radius: 14px;
            padding: 18px 22px;
            /* No outer margin — the parent .excelcv-guide-pillar-top grid
               controls spacing on wide screens; on narrow screens (where the
               grid collapses to 1 column) the parent's gap handles it. */
            margin: 0;
        }}
        .excelcv-guide-toc-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .excelcv-guide-toc-header .excelcv-guide-pillar-badge {{
            /* In the TOC corner the badge is a label, not a hero element —
               drop the bottom margin it had when it sat above the title. */
            margin-bottom: 0;
        }}
        .excelcv-guide-toc h3 {{
            margin: 0;
            font-size: 1.0rem;
            font-weight: 700;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-toc-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px 22px;
        }}
        .excelcv-guide-toc-grid a {{
            color: {p["accent"]} !important;
            text-decoration: none;
            font-size: 0.94rem;
        }}
        .excelcv-guide-toc-grid a:hover {{
            text-decoration: underline;
        }}

        .excelcv-guide-section {{
            margin: 12px 0 8px;
            /* When the TOC scrolls a section into view, leave room for the
               site header bar above it. */
            scroll-margin-top: 110px;
        }}
        .excelcv-guide-section-head {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
        }}
        .excelcv-guide-section-icon {{
            font-size: 1.25rem;
        }}
        .excelcv-guide-section-title {{
            font-size: 1.4rem;
            font-weight: 800;
            color: {p["text_primary"]} !important;
            margin: 0;
        }}
        .excelcv-guide-section-intro {{
            color: {p["text_secondary"]} !important;
            font-size: 0.98rem;
            line-height: 1.6;
            margin: 6px 0 14px;
        }}

        .excelcv-guide-card-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
        }}
        @media (max-width: 900px) {{
            .excelcv-guide-card-grid {{
                grid-template-columns: 1fr;
            }}
            .excelcv-guide-toc-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .excelcv-guide-card {{
            display: block;
            background: {p["card_bg"]} !important;
            border: 1px solid {p["card_border"]} !important;
            border-radius: 14px;
            padding: 16px 18px;
            text-decoration: none !important;
            color: {p["text_primary"]} !important;
            transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }}
        /* Some Streamlit-injected global link rules add underline back on
           hover or visited states; force-strip it on every state for cards. */
        .excelcv-guide-card,
        .excelcv-guide-card:hover,
        .excelcv-guide-card:focus,
        .excelcv-guide-card:active,
        .excelcv-guide-card:visited,
        .excelcv-guide-card * {{
            text-decoration: none !important;
        }}
        .excelcv-guide-card:hover {{
            border-color: {p["card_hover_border"]} !important;
            background: {p["card_hover_bg"]} !important;
            transform: translateY(-1px);
            box-shadow: {p["shadow"]};
        }}
        .excelcv-guide-card-title {{
            font-size: 1.02rem;
            font-weight: 700;
            color: {p["text_primary"]} !important;
            margin: 0 0 6px;
            line-height: 1.35;
        }}
        .excelcv-guide-card-summary {{
            color: {p["text_secondary"]} !important;
            font-size: 0.92rem;
            line-height: 1.5;
            margin: 0 0 10px;
        }}
        .excelcv-guide-card-meta {{
            font-size: 0.82rem;
            color: {p["text_muted"]} !important;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .excelcv-guide-card-meta .dot {{
            opacity: 0.5;
        }}
        .excelcv-guide-card-cta {{
            color: {p["accent"]} !important;
            font-weight: 600;
        }}

        /* FAQ */
        .excelcv-guide-faq {{
            margin: 36px 0 0;
            /* TOC anchor scroll target — keep clear of the site header. */
            scroll-margin-top: 110px;
        }}
        .excelcv-guide-faq h2 {{
            font-size: 1.6rem;
            font-weight: 800;
            margin: 0 0 12px;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-faq details {{
            background: {p["card_bg"]} !important;
            border: 1px solid {p["card_border"]} !important;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }}
        .excelcv-guide-faq summary {{
            font-weight: 700;
            color: {p["text_primary"]} !important;
            cursor: pointer;
            list-style: none;
            outline: none;
        }}
        .excelcv-guide-faq summary::-webkit-details-marker {{ display: none; }}
        .excelcv-guide-faq summary::after {{
            content: "+";
            float: right;
            color: {p["text_muted"]} !important;
            font-weight: 700;
            margin-left: 12px;
            transition: transform 0.2s ease;
        }}
        .excelcv-guide-faq details[open] summary::after {{
            content: "−";
        }}
        .excelcv-guide-faq details p {{
            color: {p["text_secondary"]} !important;
            line-height: 1.6;
            margin: 10px 0 0;
        }}

        /* Article shell */
        .excelcv-guide-breadcrumb {{
            color: {p["text_muted"]} !important;
            font-size: 0.88rem;
            margin: 6px 0 14px;
        }}
        .excelcv-guide-breadcrumb a {{
            color: {p["text_muted"]} !important;
            text-decoration: none;
        }}
        .excelcv-guide-breadcrumb a:hover {{
            color: {p["accent"]} !important;
            text-decoration: underline;
        }}
        .excelcv-guide-breadcrumb-sep {{
            margin: 0 6px;
            opacity: 0.6;
        }}
        .excelcv-guide-back-link {{
            color: {p["accent"]} !important;
            text-decoration: none;
            font-size: 0.92rem;
            font-weight: 600;
        }}
        .excelcv-guide-back-link:hover {{
            text-decoration: underline;
        }}
        .excelcv-guide-tag-chip {{
            display: inline-block;
            font-size: 0.74rem;
            font-weight: 600;
            color: {p["badge_text"]} !important;
            background: {p["badge_bg"]} !important;
            border: 1px solid {p["badge_border"]} !important;
            padding: 3px 10px;
            border-radius: 999px;
            margin: 0;
        }}
        /* Inline meta row: tag chip + date with calendar icon + read time
           with clock icon. Sits at the top of the article (above the title)
           now that the breadcrumb has been removed. Top margin is 0 because
           the wrapping ``stElementContainer`` already gets a negative
           margin-top to close the gap below the site header rule. */
        .excelcv-guide-article-meta-row {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 14px;
            margin: 0 0 10px;
        }}
        .excelcv-guide-meta-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: {p["text_muted"]} !important;
            font-size: 0.86rem;
        }}
        .excelcv-guide-meta-icon {{
            width: 14px;
            height: 14px;
            flex-shrink: 0;
        }}
        .excelcv-guide-article-title {{
            font-size: 2.0rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 8px;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-byline {{
            color: {p["text_secondary"]} !important;
            font-size: 0.92rem;
            margin: 0 0 4px;
        }}
        .excelcv-guide-byline strong {{
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-article-meta {{
            color: {p["text_muted"]} !important;
            font-size: 0.84rem;
            margin: 0 0 22px;
            display: flex;
            gap: 12px;
        }}
        .excelcv-guide-article-meta .dot {{
            opacity: 0.5;
        }}
        /* Two-column article layout: main body on the left, sticky TOC rail
           on the right. The body retains a comfortable max-width for reading
           (~70ch) while the rail takes its own fixed column on wide screens
           and collapses entirely below 1100px. */
        .excelcv-guide-article-layout {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) 260px;
            gap: 56px;
            align-items: start;
            margin-top: 6px;
        }}
        .excelcv-guide-article-main {{
            min-width: 0;
        }}
        @media (max-width: 1100px) {{
            .excelcv-guide-article-layout {{
                grid-template-columns: 1fr;
                gap: 0;
            }}
            .excelcv-guide-toc-rail {{ display: none !important; }}
        }}
        /* Outer aside must stretch to the full grid-row height (= article
           body height) so the inner sticky element has a tall containing
           block to stick within. With ``align-self: start`` the outer would
           collapse to ~280px (TOC content height) and sticky would detach
           the moment the reader scrolled past that, leaving the right column
           blank for the rest of the article. */
        .excelcv-guide-toc-rail {{
            align-self: stretch;
            min-height: 0;
        }}
        .excelcv-guide-toc-rail-inner {{
            position: sticky;
            top: 96px;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
            border-left: 2px solid {p["card_border"]};
            padding: 4px 0 4px 18px;
        }}
        .excelcv-guide-toc-rail-label {{
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {p["text_muted"]} !important;
            margin-bottom: 12px;
        }}
        .excelcv-guide-toc-rail-list {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .excelcv-guide-toc-rail-list li {{
            margin: 8px 0;
        }}
        .excelcv-guide-toc-rail-list a {{
            display: block;
            color: {p["text_muted"]} !important;
            text-decoration: none;
            font-size: 0.92rem;
            line-height: 1.45;
            padding: 4px 0;
            border-left: 2px solid transparent;
            margin-left: -20px;
            padding-left: 18px;
            transition: color 0.15s ease, border-color 0.15s ease;
        }}
        .excelcv-guide-toc-rail-list a:hover {{
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-toc-rail-list a.excelcv-guide-toc-active {{
            color: {p["accent"]} !important;
            border-left-color: {p["accent"]};
            font-weight: 600;
        }}

        .excelcv-guide-article-body {{
            color: {p["text_body"]} !important;
            line-height: 1.75;
            font-size: 1.125rem;
            max-width: 70ch;
        }}
        .excelcv-guide-article-body p {{
            margin: 0 0 16px;
        }}
        .excelcv-guide-article-body h1,
        .excelcv-guide-article-body h2,
        .excelcv-guide-article-body h3,
        .excelcv-guide-article-body h4,
        .excelcv-guide-article-body strong {{
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-article-body h2 {{
            font-size: 1.65rem;
            font-weight: 800;
            margin: 36px 0 12px;
            scroll-margin-top: 110px;
        }}
        .excelcv-guide-article-body h3 {{
            font-size: 1.25rem;
            font-weight: 700;
            margin: 26px 0 8px;
            scroll-margin-top: 110px;
        }}
        .excelcv-guide-article-body ul,
        .excelcv-guide-article-body ol {{
            padding-left: 1.4em;
        }}
        .excelcv-guide-article-body li {{
            margin: 4px 0;
        }}
        .excelcv-guide-article-body a {{
            color: {p["accent"]} !important;
            text-decoration: underline;
        }}
        .excelcv-guide-article-body code {{
            background: {p["code_bg"]} !important;
            color: {p["code_text"]} !important;
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.92em;
        }}
        .excelcv-guide-article-body blockquote {{
            margin: 16px 0;
            padding: 8px 14px;
            border-left: 3px solid {p["accent"]};
            background: {p["chip_bg"]};
            color: {p["text_secondary"]} !important;
            border-radius: 0 8px 8px 0;
        }}
        .excelcv-guide-continue {{
            margin: 32px 0 12px;
            padding: 18px 22px;
            background: {p["card_bg"]} !important;
            border: 1px solid {p["card_border"]} !important;
            border-radius: 14px;
        }}
        .excelcv-guide-continue h3 {{
            margin: 0 0 4px;
            font-size: 1.05rem;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-continue-sub {{
            color: {p["text_muted"]} !important;
            font-size: 0.88rem;
            margin: 0 0 12px;
        }}
        .excelcv-guide-continue-sub a {{
            color: {p["accent"]} !important;
        }}
        .excelcv-guide-continue-list {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .excelcv-guide-continue-list li {{
            margin: 8px 0;
            color: {p["text_secondary"]} !important;
        }}
        .excelcv-guide-continue-list a {{
            color: {p["accent"]} !important;
            text-decoration: none;
            font-weight: 600;
        }}
        .excelcv-guide-continue-list a:hover {{
            text-decoration: underline;
        }}
        .excelcv-guide-continue-blurb {{
            color: {p["text_secondary"]} !important;
            font-size: 0.9rem;
            font-weight: 400;
            margin-left: 6px;
        }}
        .excelcv-guide-tags {{
            margin: 22px 0 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .excelcv-guide-tags .chip {{
            font-size: 0.78rem;
            color: {p["chip_text"]} !important;
            background: {p["chip_bg"]} !important;
            border: 1px solid {p["chip_border"]} !important;
            border-radius: 999px;
            padding: 3px 10px;
        }}
        .excelcv-guide-byline-card {{
            margin: 22px 0 0;
            padding: 14px 18px;
            background: {p["card_bg"]} !important;
            border: 1px solid {p["card_border"]} !important;
            border-radius: 12px;
        }}
        .excelcv-guide-byline-card .name {{
            font-weight: 700;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-byline-card .role {{
            color: {p["text_muted"]} !important;
            font-size: 0.88rem;
            margin-bottom: 6px;
        }}
        .excelcv-guide-byline-card .bio {{
            color: {p["text_secondary"]} !important;
            font-size: 0.92rem;
            line-height: 1.55;
            margin: 0;
        }}

        .excelcv-guide-placeholder {{
            padding: 28px;
            background: {p["card_bg"]} !important;
            border: 1px dashed {p["card_border"]} !important;
            border-radius: 14px;
            text-align: center;
            color: {p["text_secondary"]} !important;
        }}
        .excelcv-guide-placeholder strong {{
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-placeholder a {{
            color: {p["accent"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guide_href(slug: str) -> str:
    """Build an in-app URL for a guide article."""
    return _build_page_href(slug)


def _guide_nav_button_key(slug: str) -> str:
    """Key for the hidden bridge button that swaps the page to ``slug``."""
    normalized = "".join(ch if ch.isalnum() else "_" for ch in str(slug).strip().lower())
    return f"nav_action_{normalized}"


def _navigate_to_guide_page(slug: str) -> None:
    """Bridge-button callback: swap st.session_state['page'] to ``slug``.

    Also writes the new page to ``st.query_params['page']`` so the URL
    updates atomically with the state change. Without this, the address bar
    can stay stuck on the previous page's URL even though the new page is
    rendered (the JS-based URL sync in app.py can lose its race with the
    rerun). Pops nav_action_pending so any stale top-nav focus from the
    previous page doesn't leak into the new render.
    """
    st.session_state["page"] = str(slug)
    st.session_state.pop("nav_action_pending", None)
    try:
        st.query_params["page"] = str(slug)
    except Exception:
        # Older Streamlit versions don't expose dict-style writes — silently
        # fall back to the JS-based URL sync if so.
        pass


def _emit_guide_nav_bridges() -> None:
    """Emit hidden Streamlit buttons — one per guide slug + the pillar.

    The reasoning: ``<a href="?page=guide-…">`` does a real HTTP navigation
    which forces a full page reload (slow, visible flash). Clicking a
    hidden Streamlit button instead sends a WebSocket message that
    triggers a normal in-app rerun — much faster, no white flash.

    Guide-card and continue-learning links get ``data-guide-nav="<slug>"``
    and a small JS handler (injected by :func:`render_guide_article` and
    :func:`render_resume_tips_pillar`) clicks the matching bridge on the
    user's behalf. The bridge buttons themselves are invisible thanks to
    the existing ``st-key-nav_action_*`` CSS rules in ``base_theme.css.tpl``.
    """
    targets = list(GUIDES_META.keys()) + ["resume-tips"]
    with st.container(key="guide_nav_action_bridge"):
        for slug in targets:
            st.button(
                " ",
                key=_guide_nav_button_key(slug),
                help=f"Internal navigation trigger for {slug}",
                on_click=_navigate_to_guide_page,
                args=(slug,),
            )


_GUIDE_NAV_DELEGATED_JS = """
<script>
(function() {
    var w = window.parent && window.parent !== window ? window.parent : window;
    var doc = w.document;
    if (doc.__excelcv_guide_nav_bound__) return;
    doc.__excelcv_guide_nav_bound__ = true;
    doc.addEventListener('click', function(ev) {
        var el = ev.target;
        while (el && el !== doc && !(el.getAttribute && el.getAttribute('data-guide-nav'))) {
            el = el.parentNode;
        }
        if (!el || el === doc) return;
        var slug = String(el.getAttribute('data-guide-nav') || '').trim();
        if (!slug) return;
        var normalized = '';
        for (var i = 0; i < slug.length; i++) {
            var c = slug.charAt(i);
            normalized += /[a-zA-Z0-9]/.test(c) ? c.toLowerCase() : '_';
        }
        var btnClass = 'st-key-nav_action_' + normalized;
        var btn = doc.querySelector('.' + btnClass + ' button');
        if (!btn) return;
        ev.preventDefault();
        ev.stopPropagation();
        try { w.scrollTo({ top: 0, left: 0, behavior: 'instant' }); } catch (_e1) { w.scrollTo(0, 0); }
        btn.click();
    }, true);
})();
</script>
"""


def _load_guide_markdown(slug: str) -> str | None:
    """Return the markdown body for a guide, or None if the file is missing."""
    path = GUIDES_DIR / f"{slug}.md"
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _section_for_guide(slug: str) -> Dict[str, Any] | None:
    """Look up which pillar section a guide belongs to (for breadcrumb)."""
    for section in SECTIONS:
        if slug in section["guides"]:
            return section
    return None


_H2_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")
# Strip apostrophes (straight and curly) BEFORE the non-alphanumeric pass so
# that "Don't" becomes "dont" rather than "don-t" — the awkward ``-t-``
# artifact was breaking clicks on the "Don't Be in the 75%" TOC link.
_SLUG_STRIP_CHARS = str.maketrans("", "", "'’‘“”")


def _slugify(text: str) -> str:
    """Lower-kebab-case a heading for use as an in-page anchor id."""
    cleaned = text.lower().translate(_SLUG_STRIP_CHARS)
    slug = _SLUG_NON_ALNUM.sub("-", cleaned).strip("-")
    return slug or "section"


def _extract_toc_and_anchor_headings(md: str) -> Tuple[str, List[Dict[str, str]]]:
    """Inject explicit ``id`` attributes onto each ``## H2`` in the markdown
    and return the modified markdown alongside the TOC entries.

    Streamlit's markdown renderer doesn't honor the Kramdown ``{#id}`` extension,
    so the only reliable way to get stable in-page anchors is to convert the
    ``## Heading`` lines to raw HTML headings ourselves and render the result
    with ``unsafe_allow_html=True``. The rest of the markdown still renders
    normally — Streamlit happily mixes markdown blocks and inline HTML blocks.

    Duplicate slugs are disambiguated with a ``-2``, ``-3`` suffix so repeated
    section names (e.g. two "Common Mistakes" sections) get unique anchors.
    """
    toc: List[Dict[str, str]] = []
    used_slugs: Dict[str, int] = {}

    def _replace(match: re.Match) -> str:
        text = match.group(1).strip()
        base = _slugify(text)
        count = used_slugs.get(base, 0) + 1
        used_slugs[base] = count
        slug = base if count == 1 else f"{base}-{count}"
        toc.append({"id": slug, "text": text})
        # Blank lines around the raw HTML keep Streamlit's markdown parser from
        # gluing it into surrounding paragraphs.
        return f'\n\n<h2 id="{slug}">{text}</h2>\n\n'

    new_md = _H2_PATTERN.sub(_replace, md)
    return new_md, toc


# ---------------------------------------------------------------------------
# Pillar page
# ---------------------------------------------------------------------------


def render_resume_tips_pillar() -> None:
    """Render the redesigned Resume Tips pillar page."""
    inject_guides_css()
    _emit_guide_nav_bridges()
    components.html(_GUIDE_NAV_DELEGATED_JS, height=0)

    pillar_title = "Resume Tips: The Complete ATS Guide"
    pillar_lede = (
        "Roughly <strong>75% of resumes</strong> get filtered out by Applicant "
        "Tracking Systems before a human ever sees them. This guide is the "
        "complete playbook — covering format, keywords, AI-based ranking, "
        "and the layout fixes that match what modern ATS platforms actually "
        "look for. Seven in-depth guides, organized so you can read just the "
        "sections that apply to you."
    )

    # Table of contents links (built first so we can render hero + TOC as a
    # single 2-column row instead of stacking them vertically). Each link
    # carries ``data-smooth-scroll`` so the delegated click handler in
    # ``render_site_footer`` intercepts the click and smooth-scrolls + updates
    # the URL via replaceState. Without the attribute the plain hash link
    # triggers a Streamlit rerun on the URL change, which resets the scroll
    # position and makes clicking the TOC feel like a page reload.
    toc_links = "".join(
        f'<a href="#section-{section["id"]}" data-smooth-scroll="#section-{section["id"]}">{section["label"]}</a>'
        for section in SECTIONS
    )
    toc_links += '<a href="#faq" data-smooth-scroll="#faq">Frequently asked questions</a>'

    st.markdown(
        f"""
        <div class="excelcv-guide-pillar-top">
            <div class="excelcv-guide-pillar-hero">
                <h1 class="excelcv-guide-pillar-title">{pillar_title}</h1>
                <p class="excelcv-guide-pillar-lede">{pillar_lede}</p>
            </div>
            <div class="excelcv-guide-toc">
                <div class="excelcv-guide-toc-header">
                    <h3>What this guide covers</h3>
                    <span class="excelcv-guide-pillar-badge">Pillar Guide · Updated May 2026</span>
                </div>
                <div class="excelcv-guide-toc-grid">{toc_links}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section blocks with article cards
    for section in SECTIONS:
        cards_html = ""
        for slug in section["guides"]:
            meta = GUIDES_META.get(slug)
            if not meta:
                continue
            href = _guide_href(slug)
            cards_html += (
                f'<a class="excelcv-guide-card" href="{href}" target="_self" data-guide-nav="{slug}">'
                f'<div class="excelcv-guide-card-title">{meta["title"]}</div>'
                f'<div class="excelcv-guide-card-summary">{meta["summary"]}</div>'
                f'<div class="excelcv-guide-card-meta">'
                f'<span>{meta["read_time"]}</span>'
                f'<span class="dot">·</span>'
                f'<span class="excelcv-guide-card-cta">Read guide →</span>'
                f"</div></a>"
            )
        st.markdown(
            f"""
            <div class="excelcv-guide-section" id="section-{section["id"]}">
                <div class="excelcv-guide-section-head">
                    <span class="excelcv-guide-section-icon">{section["icon"]}</span>
                    <h2 class="excelcv-guide-section-title">{section["label"]}</h2>
                </div>
                <p class="excelcv-guide-section-intro">{section["intro"]}</p>
                <div class="excelcv-guide-card-grid">{cards_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # FAQ
    faq_html = "".join(
        f"<details><summary>{item['q']}</summary><p>{item['a']}</p></details>" for item in FAQ_ITEMS
    )
    st.markdown(
        f"""
        <div class="excelcv-guide-faq" id="faq">
            <h2>Frequently asked questions</h2>
            {faq_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sub-guide article page
# ---------------------------------------------------------------------------


def render_guide_article(slug: str) -> None:
    """Render a single sub-guide article identified by its slug."""
    inject_guides_css()
    _emit_guide_nav_bridges()
    components.html(_GUIDE_NAV_DELEGATED_JS, height=0)

    meta = GUIDES_META.get(slug)
    if not meta:
        st.markdown(
            f"""
            <div class="excelcv-guide-placeholder">
                <strong>Guide not found.</strong>
                <p>The slug <code>{slug}</code> isn't registered. "
                "<a href="{_build_page_href("resume-tips")}" target="_self">Return to the guide hub →</a></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    body_md = _load_guide_markdown(slug)

    pillar_href = _build_page_href("resume-tips")

    # Breadcrumb + inline meta row (tag chip · date · read time). The
    # "← Back to Resume Tips" link is intentionally not rendered — the
    # breadcrumb above already provides the way back and the meta row reads
    # cleaner without a second back affordance underneath.
    cal_icon = (
        '<svg class="excelcv-guide-meta-icon" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/></svg>'
    )
    clock_icon = (
        '<svg class="excelcv-guide-meta-icon" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/></svg>'
    )
    st.markdown(
        f"""
        <div class="excelcv-guide-article-meta-row">
            <span class="excelcv-guide-tag-chip">{meta["tag"]}</span>
            <span class="excelcv-guide-meta-item">{cal_icon}{meta["date"]}</span>
            <span class="excelcv-guide-meta-item">{clock_icon}{meta["read_time"]}</span>
        </div>
        <h1 class="excelcv-guide-article-title">{meta["title"]}</h1>
        <p class="excelcv-guide-byline">By <strong>{EDITORIAL_BYLINE}</strong></p>
        """,
        unsafe_allow_html=True,
    )

    # Body + sticky TOC rail
    if body_md:
        anchored_md, toc_entries = _extract_toc_and_anchor_headings(body_md)
        if toc_entries:
            toc_items = "".join(
                f'<li><a href="#{entry["id"]}" data-smooth-scroll="#{entry["id"]}" data-toc-target="{entry["id"]}">{entry["text"]}</a></li>'
                for entry in toc_entries
            )
            toc_html = (
                '<aside class="excelcv-guide-toc-rail">'
                '<div class="excelcv-guide-toc-rail-inner">'
                '<div class="excelcv-guide-toc-rail-label">On this page</div>'
                f'<ul class="excelcv-guide-toc-rail-list">{toc_items}</ul>'
                "</div></aside>"
            )
        else:
            toc_html = ""
        # Two-column layout: main body on the left, sticky TOC on the right.
        # ``anchored_md`` has its H2 headings rewritten as raw <h2 id="…">
        # blocks; Streamlit mixes markdown and HTML when unsafe_allow_html=True,
        # so the anchor ids survive and the TOC links land on them.
        st.markdown(
            (
                '<div class="excelcv-guide-article-layout">'
                '<div class="excelcv-guide-article-main">'
                f'<div class="excelcv-guide-article-body">\n\n{anchored_md}\n\n</div>'
                "</div>"
                f"{toc_html}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        # Scroll-spy: highlight the current section in the TOC rail as the
        # reader scrolls. Replaces any previously bound observer so navigating
        # between guide articles doesn't leave stale listeners attached to
        # the wrong DOM.
        if toc_entries:
            components.html(
                """
                <script>
                (function() {
                    var w = window.parent && window.parent !== window ? window.parent : window;
                    var doc = w.document;
                    var attempts = 0;
                    var attach = function() {
                        var rail = doc.querySelector('.excelcv-guide-toc-rail');
                        var body = doc.querySelector('.excelcv-guide-article-body');
                        if (!rail || !body) {
                            if (attempts++ < 30) setTimeout(attach, 200);
                            return;
                        }
                        if (w.__excelcv_toc_observer__) {
                            try { w.__excelcv_toc_observer__.disconnect(); } catch (_e) {}
                            w.__excelcv_toc_observer__ = null;
                        }
                        var links = Array.prototype.slice.call(
                            rail.querySelectorAll('a[data-toc-target]')
                        );
                        var headings = links
                            .map(function(a) { return doc.getElementById(a.getAttribute('data-toc-target')); })
                            .filter(function(h) { return !!h; });
                        if (!headings.length) return;
                        var setActive = function(id) {
                            links.forEach(function(a) {
                                a.classList.toggle(
                                    'excelcv-guide-toc-active',
                                    a.getAttribute('data-toc-target') === id
                                );
                            });
                        };
                        // Scroll-position scan rather than pure IntersectionObserver
                        // — IO doesn't cleanly resolve "which section am I in
                        // RIGHT now" for long sections that span the entire
                        // viewport, leaving the highlight stuck on a stale link.
                        var REF_OFFSET = 160;
                        var update = function() {
                            // Edge case: when the user has scrolled to (or past)
                            // the bottom of the document, the last heading
                            // physically cannot reach the REF_OFFSET line —
                            // the page is at max scroll. Force-activate the
                            // last heading so the TOC reflects what the reader
                            // is actually reading.
                            var docEl = doc.documentElement;
                            var scrollY = w.scrollY || w.pageYOffset || docEl.scrollTop || 0;
                            var maxScroll = (docEl.scrollHeight || 0) - (w.innerHeight || 0);
                            if (maxScroll > 0 && scrollY >= maxScroll - 4) {
                                setActive(headings[headings.length - 1].id);
                                return;
                            }
                            var current = headings[0].id;
                            for (var i = 0; i < headings.length; i++) {
                                var top = headings[i].getBoundingClientRect().top;
                                if (top - REF_OFFSET <= 0) {
                                    current = headings[i].id;
                                } else {
                                    break;
                                }
                            }
                            setActive(current);
                        };
                        var onScroll = function() {
                            if (w.__excelcv_toc_raf__) return;
                            w.__excelcv_toc_raf__ = w.requestAnimationFrame(function() {
                                w.__excelcv_toc_raf__ = 0;
                                update();
                            });
                        };
                        w.addEventListener('scroll', onScroll, true);
                        w.addEventListener('resize', onScroll, true);
                        w.__excelcv_toc_observer__ = { disconnect: function() {
                            try { w.removeEventListener('scroll', onScroll, true); } catch (_e) {}
                            try { w.removeEventListener('resize', onScroll, true); } catch (_e) {}
                        }};
                        update();
                    };
                    attach();
                })();
                </script>
                """,
                height=0,
            )
    else:
        st.markdown(
            """
            <div class="excelcv-guide-placeholder">
                <strong>This guide is being written.</strong>
                <p>The content for this article hasn't been added yet. Check
                back soon — or return to the
                <a href=\""""
            + pillar_href
            + """\" target="_self">Resume Tips hub</a>
                to read other guides in the meantime.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Continue learning
    related = [s for s in meta.get("related", []) if s in GUIDES_META]
    if related:
        items_html = ""
        for rel_slug in related:
            rel = GUIDES_META[rel_slug]
            href = _guide_href(rel_slug)
            items_html += (
                f'<li><a href="{href}" target="_self" data-guide-nav="{rel_slug}">{rel["title"]}</a>'
                f'<span class="excelcv-guide-continue-blurb"> — {rel["summary"]}</span></li>'
            )
        st.markdown(
            f"""
            <div class="excelcv-guide-continue">
                <h3>Continue learning: more ATS guides</h3>
                <p class="excelcv-guide-continue-sub">
                    Part of the <a href="{pillar_href}" target="_self" data-guide-nav="resume-tips">complete ATS resume guide</a>.
                    Recommended next reads:
                </p>
                <ul class="excelcv-guide-continue-list">{items_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tag chips
    tags = meta.get("tags") or []
    if tags:
        chips_html = "".join(f'<span class="chip">#{t}</span>' for t in tags)
        st.markdown(
            f'<div class="excelcv-guide-tags">{chips_html}</div>',
            unsafe_allow_html=True,
        )

    # Editorial byline card
    st.markdown(
        f"""
        <div class="excelcv-guide-byline-card">
            <div class="name">{EDITORIAL_BYLINE}</div>
            <div class="role">Resume & ATS research at ExcelCV</div>
            <p class="bio">
                The ExcelCV Editorial Team researches resume parsing, ATS
                behavior, and 2026 hiring trends to help job seekers land
                interviews faster. We update these guides as ATS platforms
                evolve.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
