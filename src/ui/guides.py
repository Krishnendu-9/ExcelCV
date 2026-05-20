"""Resume Tips pillar page and sub-guide article renderers.

Architecture
------------
- Each sub-guide is a separate app route (slug starts with ``guide-``) registered
  in ``APP_PAGES``. Routing in ``app.py`` dispatches any ``guide-*`` page to
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

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from src.ui.app_utils import _build_page_href

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

GUIDES_DIR = Path(__file__).resolve().parents[2] / "docs" / "guides"

EDITORIAL_BYLINE = "ExcelCV Editorial Team"

GUIDES_META: Dict[str, Dict[str, Any]] = {
    "guide-why-75-rejected": {
        "title": "Why 75% of Resumes Are Rejected Before a Human Sees Them",
        "tag": "Resume Help",
        "date": "May 18, 2026",
        "read_time": "7 min read",
        "summary": (
            "Three out of four resumes never reach a recruiter. Here's where the "
            "75% number comes from, why it happens, and what to fix first."
        ),
        "related": [
            "guide-pass-ats-scanner-2026",
            "guide-pdf-vs-docx",
            "guide-keywords-software-engineers",
        ],
        "tags": ["ATS rejection", "applicant tracking", "resume statistics", "job search"],
    },
    "guide-pass-ats-scanner-2026": {
        "title": "How to Pass an ATS Scanner in 2026: Step-by-Step Guide",
        "tag": "Resume Help",
        "date": "May 12, 2026",
        "read_time": "9 min read",
        "summary": (
            "The complete 9-step playbook — parsing, keywords, formatting, file "
            "naming, and testing — for any ATS in 2026."
        ),
        "related": [
            "guide-why-75-rejected",
            "guide-ats-friendly-templates",
            "guide-keywords-software-engineers",
        ],
        "tags": ["ATS", "resume optimization", "applicant tracking", "resume tips"],
    },
    "guide-pdf-vs-docx": {
        "title": "PDF vs DOCX Resume: Which Format Passes ATS Better in 2026?",
        "tag": "Resume Help",
        "date": "April 28, 2026",
        "read_time": "6 min read",
        "summary": (
            "The PDF-vs-DOCX debate finally settled with data — tested across the "
            "major ATS platforms in production today."
        ),
        "related": [
            "guide-ats-friendly-templates",
            "guide-pass-ats-scanner-2026",
            "guide-why-75-rejected",
        ],
        "tags": ["PDF vs DOCX", "resume format", "ATS", "resume tips"],
    },
    "guide-ats-friendly-templates": {
        "title": "ATS-Friendly Resume Templates and Formats",
        "tag": "Resume Help",
        "date": "April 14, 2026",
        "read_time": "5 min read",
        "summary": (
            "Optimized structure and formatting rules that keep parsers happy "
            "across every major ATS platform."
        ),
        "related": [
            "guide-pdf-vs-docx",
            "guide-pass-ats-scanner-2026",
            "guide-keywords-software-engineers",
        ],
        "tags": ["resume templates", "ATS", "resume format", "job search"],
    },
    "guide-keywords-software-engineers": {
        "title": "ATS Resume Keywords for Software Engineers in 2026",
        "tag": "Resume Help",
        "date": "April 6, 2026",
        "read_time": "9 min read",
        "summary": (
            "High-signal keywords ATS platforms scan for in software engineering "
            "resumes — broken down by backend, frontend, DevOps, and ML."
        ),
        "related": [
            "guide-pass-ats-scanner-2026",
            "guide-ai-hiring-tools-2026",
            "guide-why-75-rejected",
        ],
        "tags": ["software engineer resume", "ATS keywords", "tech resume", "developer job search"],
    },
    "guide-resume-no-experience": {
        "title": "How to Write a Resume with No Experience That Passes ATS",
        "tag": "Career Advice",
        "date": "March 22, 2026",
        "read_time": "8 min read",
        "summary": (
            "Students, new grads, and career switchers — build a resume that "
            "beats the ATS without traditional work history."
        ),
        "related": [
            "guide-pass-ats-scanner-2026",
            "guide-ats-friendly-templates",
            "guide-keywords-software-engineers",
        ],
        "tags": ["no experience resume", "student resume", "new grad", "first job"],
    },
    "guide-ai-hiring-tools-2026": {
        "title": "How AI Hiring Tools Are Changing Resume Screening in 2026",
        "tag": "Career Advice",
        "date": "March 10, 2026",
        "read_time": "9 min read",
        "summary": (
            "AI now reads, ranks, and rejects most resumes before recruiters see "
            "them. What's actually happening — and how to stay ahead."
        ),
        "related": [
            "guide-pass-ats-scanner-2026",
            "guide-keywords-software-engineers",
            "guide-why-75-rejected",
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
        "guides": ["guide-why-75-rejected", "guide-pass-ats-scanner-2026"],
    },
    {
        "id": "format-layout",
        "icon": "📄",
        "label": "File format and layout choices",
        "intro": (
            "Most parsing failures are caused by layout, not language. Get "
            "these two questions right before you write a single bullet."
        ),
        "guides": ["guide-pdf-vs-docx", "guide-ats-friendly-templates"],
    },
    {
        "id": "keywords",
        "icon": "🔑",
        "label": "Keywords by role and industry",
        "intro": (
            "ATS scoring lives and dies on the right keywords. Generic lists "
            "are useless — pick the guide that matches your role."
        ),
        "guides": ["guide-keywords-software-engineers"],
    },
    {
        "id": "starters-changers",
        "icon": "🎓",
        "label": "Students, new grads, and career changers",
        "intro": (
            "ATS-friendly doesn't mean traditional experience required. If "
            "your background is non-linear, this guide is for you."
        ),
        "guides": ["guide-resume-no-experience"],
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
        "guides": ["guide-ai-hiring-tools-2026"],
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
        [data-testid="stElementContainer"]:has(> .excelcv-guide-continue),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-tags),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-byline-card),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-placeholder) {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        /* Pull the FIRST content block on a guide page up to close the natural
           band below the site header rule. Applied to the wrapping
           stElementContainer (not the inner element) so it actually offsets
           Streamlit's vertical-block gap above it. */
        [data-testid="stElementContainer"]:has(> .excelcv-guide-pillar-hero),
        [data-testid="stElementContainer"]:has(> .excelcv-guide-breadcrumb) {{
            margin-top: -60px !important;
        }}
        .excelcv-guide-pillar-hero {{
            padding: 12px 0 8px;
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
            margin: 0 0 14px;
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-pillar-lede {{
            color: {p["text_secondary"]} !important;
            font-size: 1.06rem;
            line-height: 1.6;
            max-width: 64ch;
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
            margin: 18px 0 28px;
        }}
        .excelcv-guide-toc h3 {{
            margin: 0 0 12px;
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
            margin: 28px 0 8px;
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
            max-width: 72ch;
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
            text-decoration: none;
            color: {p["text_primary"]} !important;
            transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }}
        .excelcv-guide-card:hover {{
            border-color: {p["card_hover_border"]} !important;
            background: {p["card_hover_bg"]} !important;
            transform: translateY(-1px);
            box-shadow: {p["shadow"]};
            text-decoration: none;
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
            margin: 14px 0 10px;
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
        .excelcv-guide-article-body {{
            color: {p["text_body"]} !important;
            line-height: 1.7;
            font-size: 1.0rem;
            max-width: 78ch;
        }}
        .excelcv-guide-article-body h1,
        .excelcv-guide-article-body h2,
        .excelcv-guide-article-body h3,
        .excelcv-guide-article-body h4,
        .excelcv-guide-article-body strong {{
            color: {p["text_primary"]} !important;
        }}
        .excelcv-guide-article-body h2 {{
            font-size: 1.45rem;
            margin: 28px 0 10px;
        }}
        .excelcv-guide-article-body h3 {{
            font-size: 1.15rem;
            margin: 22px 0 8px;
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


# ---------------------------------------------------------------------------
# Pillar page
# ---------------------------------------------------------------------------


def render_resume_tips_pillar() -> None:
    """Render the redesigned Resume Tips pillar page."""
    inject_guides_css()

    pillar_title = "Resume Tips: The Complete ATS Guide"
    pillar_lede = (
        "Roughly <strong>75% of resumes</strong> get filtered out by Applicant "
        "Tracking Systems before a human ever sees them. This guide is the "
        "complete playbook — covering format, keywords, AI-based ranking, "
        "and the layout fixes that match what modern ATS platforms actually "
        "look for. Seven in-depth guides, organized so you can read just the "
        "sections that apply to you."
    )

    st.markdown(
        f"""
        <div class="excelcv-guide-pillar-hero">
            <span class="excelcv-guide-pillar-badge">Pillar Guide · Updated May 2026</span>
            <h1 class="excelcv-guide-pillar-title">{pillar_title}</h1>
            <p class="excelcv-guide-pillar-lede">{pillar_lede}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Table of contents
    toc_links = "".join(
        f'<a href="#section-{section["id"]}">{section["label"]}</a>' for section in SECTIONS
    )
    toc_links += '<a href="#faq">Frequently asked questions</a>'
    st.markdown(
        f"""
        <div class="excelcv-guide-toc">
            <h3>What this guide covers</h3>
            <div class="excelcv-guide-toc-grid">{toc_links}</div>
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
                f'<a class="excelcv-guide-card" href="{href}" target="_self">'
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
    home_href = _build_page_href("home")

    # Breadcrumb + back link
    st.markdown(
        f"""
        <div class="excelcv-guide-breadcrumb">
            <a href="{home_href}" target="_self">Home</a>
            <span class="excelcv-guide-breadcrumb-sep">›</span>
            <a href="{pillar_href}" target="_self">Resume Tips</a>
            <span class="excelcv-guide-breadcrumb-sep">›</span>
            <span>{meta["title"]}</span>
        </div>
        <a class="excelcv-guide-back-link" href="{pillar_href}" target="_self">← Back to Resume Tips</a>
        <span class="excelcv-guide-tag-chip">{meta["tag"]}</span>
        <h1 class="excelcv-guide-article-title">{meta["title"]}</h1>
        <p class="excelcv-guide-byline">By <strong>{EDITORIAL_BYLINE}</strong></p>
        <div class="excelcv-guide-article-meta">
            <span>{meta["date"]}</span>
            <span class="dot">·</span>
            <span>{meta["read_time"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Body
    if body_md:
        st.markdown(
            f'<div class="excelcv-guide-article-body">\n\n{body_md}\n\n</div>',
            unsafe_allow_html=True,
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
                f'<li><a href="{href}" target="_self">{rel["title"]}</a>'
                f'<span class="excelcv-guide-continue-blurb"> — {rel["summary"]}</span></li>'
            )
        st.markdown(
            f"""
            <div class="excelcv-guide-continue">
                <h3>Continue learning: more ATS guides</h3>
                <p class="excelcv-guide-continue-sub">
                    Part of the <a href="{pillar_href}" target="_self">complete ATS resume guide</a>.
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
