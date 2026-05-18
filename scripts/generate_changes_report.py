"""Generate Report_Changes_Summary.docx — a side-by-side change log between
the old PDF and the new Minor_Project_Report.docx.

Run:
    py -3 scripts/generate_changes_report.py

Output:
    docs/submission/Report_Changes_Summary.docx
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OUT_DIR = _REPO_ROOT / "docs" / "submission"
_OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = _OUT_DIR / "Report_Changes_Summary.docx"

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    for tag, content in [("begin", None), ("instr", "PAGE"), ("end", None)]:
        if tag == "instr":
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = content
        else:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tag)
        run._r.append(e)


footer = doc.sections[0].footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
fp.add_run("Page | ").font.size = Pt(9)
add_page_number(fp)


def add_heading(text: str, level: int = 1, color: str = "1F4E79"):
    sizes = {1: 22, 2: 16, 3: 13, 4: 12}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level > 1 else 4)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(sizes.get(level, 11))
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor.from_string(color)
    return p


def add_para(text: str, bold: bool = False, italic: bool = False,
             size: int = 11, align=WD_ALIGN_PARAGRAPH.LEFT, space_after: int = 6,
             indent: float = 0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    return p


def add_bullet(text: str):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(2)
    for run in p.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(11)
    return p


def add_compare_table(rows: list[list[str]], headers: list[str] | None = None,
                       col_widths: list[float] | None = None,
                       header_color: str = "1F4E79"):
    if headers is None:
        headers = ["Old PDF", "New DOCX"]
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.name = "Calibri"
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), header_color)
        cell._tc.get_or_add_tcPr().append(shading)

    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = t.rows[r].cells[c]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.size = Pt(10)
            run.font.name = "Calibri"
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            # Alternate row shading
            if r % 2 == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "F2F2F2")
                cell._tc.get_or_add_tcPr().append(shading)

    if col_widths:
        for row in t.rows:
            for cell, w in zip(row.cells, col_widths):
                cell.width = Inches(w)
    return t


def page_break():
    doc.add_page_break()


# ════════════════════════════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════════════════════════════
add_para("ExcelCV — Project Report", bold=True, size=16,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
add_para("Detailed Change Log: Old PDF → New DOCX", bold=True, size=20,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
add_para("Generated 2026-05-18", italic=True, size=11,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)

add_para(
    "This document summarises every change made between the previous version of the "
    "project report (PDF) and the regenerated version (Minor_Project_Report.docx) "
    "produced on 2026-05-18. Sections are organised in the same order as the report "
    "itself so you can verify each change against the original PDF page by page.",
    space_after=12,
)

# ════════════════════════════════════════════════════════════════════
# TITLE PAGE & FRONT MATTER
# ════════════════════════════════════════════════════════════════════
add_heading("1. Title Page & Front Matter", 2)

add_compare_table(
    rows=[
        ["Subtitle: \"An Intelligent Resume Evaluation and Optimization System\"",
         "Updated subtitle: \"An Intelligent Resume Evaluation, Comparison, and "
         "Authoring Platform\" — reflects all 5 modules, not just analysis."],
        ["Title page, recommendation letter, certificate of approval, acknowledgement",
         "Kept verbatim — same student names, roll numbers, registration numbers, "
         "supervisor (Dr. Manas Ghosh), institution."],
        ["Page footer — inconsistent / cut off after Page 17",
         "Auto-numbered footer \"Page | N\" on every page."],
    ],
    col_widths=[3.4, 3.4],
)

# ════════════════════════════════════════════════════════════════════
# ABSTRACT
# ════════════════════════════════════════════════════════════════════
add_heading("2. Abstract", 2)
add_para(
    "The Abstract was completely rewritten. The old version described only the "
    "single-CV reviewer with dual-mode (General Review / ATS Scan). The new version "
    "covers:",
    space_after=6,
)
for s in [
    "Five integrated modules (Analyze, Compare, Cover Letter, Builder, History) — not "
    "just one.",
    "Eleven scoring metrics (was \"8 metrics\").",
    "Weighted scoring formula: Content 30%, JD Alignment 25%, Sections 15%, ATS "
    "Essentials 15%, Contact 15% — was just \"hybrid scoring\".",
    "PDF + DOCX input support (was \"PDF only\").",
    "PDF / JSON / DOCX / CSV outputs (was \"Markdown / JSON\").",
    "Human-vs-AI evaluation toolkit (MAE / RMSE / Pearson correlation).",
    "Authentication + persistence: SQLite, 5 tables, Google OAuth, session cookies.",
]:
    add_bullet(s)

# ════════════════════════════════════════════════════════════════════
# LIST OF SYMBOLS / ABBREVIATIONS
# ════════════════════════════════════════════════════════════════════
add_heading("3. List of Symbols & Abbreviations", 2)

add_para("List of Symbols", bold=True, space_after=4)
add_para("Same 18 symbols — kept as-is.", space_after=8)

add_para("List of Abbreviations", bold=True, space_after=4)
add_compare_table(
    rows=[
        ["CDN, AWS, R&D (unused in new report)",
         "Added: DOCX, CSV, ORM, OAuth, HMAC, SMTP, MAE / RMSE"],
    ],
    headers=["Removed", "Added"],
    col_widths=[3.0, 3.8],
    header_color="C00000",
)

# ════════════════════════════════════════════════════════════════════
# LIST OF FIGURES / TABLES
# ════════════════════════════════════════════════════════════════════
add_heading("4. List of Figures & Tables", 2)

add_para("Figures: 4 → 8", bold=True, space_after=4)
add_compare_table(
    rows=[
        ["2.1 DFD", "2.1 DFD (content updated to include auth, DB, multi-resume flow)"],
        ["3.2.1 Upload screen", "3.2.1 Home / Analyze CV"],
        ["3.2.2 Valid CV input", "3.2.2 Comparison Results — NEW"],
        ["3.2.3 Analysis Dashboard", "3.2.3 Single-Resume Report — NEW caption"],
        ["—", "3.2.4 Resume Builder workspace — NEW"],
        ["—", "3.2.5 Cover Letter page — NEW"],
        ["—", "3.2.6 My Comparisons history — NEW"],
        ["—", "2.2 Modular Architecture — NEW"],
    ],
    col_widths=[3.0, 3.8],
)

add_para("", space_after=4)
add_para("Tables: 9 → 17", bold=True, space_after=4)
add_compare_table(
    rows=[
        ["1.1 Literature Review",
         "1.1 Literature Review (added a row for ExcelCV)"],
        ["3.1.1–3.1.6 Test Cases (27 total)",
         "3.1.1–3.1.9 Test Cases (68 total) — see Chapter 3 section"],
        ["3.8 Response Time", "3.3.1 Response Time"],
        ["3.9 Bottleneck", "3.3.2 Bottleneck"],
        ["—", "2.1 Eleven Programmatic Scoring Metrics — NEW"],
        ["—", "2.2 Weighted Final-Score Formula — NEW"],
        ["—", "2.3 Database Schema (5 SQLite Tables) — NEW"],
        ["—", "3.3.3 Throughput Capacity (added paid-tier + parallelism rows)"],
        ["—", "3.3.4 Comparative ATS Analysis — NEW"],
    ],
    col_widths=[3.0, 3.8],
)

# ════════════════════════════════════════════════════════════════════
# CHAPTER 1
# ════════════════════════════════════════════════════════════════════
page_break()
add_heading("5. Chapter 1 — Introduction & Literature Review", 2)

add_heading("§1.1 Introduction", 3)
add_compare_table(
    rows=[
        ["4 paragraphs (~300 words) describing only single-CV reviewer + dual-mode",
         "5 paragraphs (~600 words) describing all 5 modules with concrete feature names"],
        ["\"8 key metrics\"",
         "\"Eleven metrics\" — each named explicitly"],
        ["\"PyPDF2\" only", "\"PyPDF2 / pypdf and python-docx\""],
        ["No mention of auth, persistence, comparison, cover letter, builder",
         "All explicitly covered"],
        ["\"Markdown / JSON export\"",
         "\"PDF (ReportLab) or JSON; cover letters as DOCX; comparison results as CSV "
         "or PDF\""],
        ["No scoring formula", "Weighted formula laid out inline"],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("§1.2 Literature Review", 3)
for s in [
    "Original 4 papers (Devlin 2018, Chandra & Kaur 2022, Kumar & Gupta 2022, "
    "Miller & Bhattacharya 2024) kept exactly.",
    "Added a 5th row: \"This work (ExcelCV) 2026\" with contribution + limitation, "
    "to position the project against prior art.",
]:
    add_bullet(s)

# ════════════════════════════════════════════════════════════════════
# CHAPTER 2
# ════════════════════════════════════════════════════════════════════
page_break()
add_heading("6. Chapter 2 — Workflow & Methodology", 2)

add_heading("§2.1 Workflow", 3)
add_para(
    "Completely restructured. Old version was one long bullet list describing the "
    "single-CV flow with dual-mode. New version has 5 sub-flows + a DFD:",
    space_after=6,
)
for s in [
    "§2.1.1 Sign-In / Registration Flow (NEW) — 6 steps covering Google OAuth and "
    "email/password.",
    "§2.1.2 Single-CV Analyze Flow (rewritten) — 7 steps, references actual modules.",
    "§2.1.3 Multi-Resume Comparison Flow (NEW) — 7 steps with quota short-circuit.",
    "§2.1.4 Cover Letter Flow (NEW) — 5 steps.",
    "§2.1.5 Resume Builder Flow (NEW) — 8 steps.",
    "§2.1.6 Level 0 DFD (NEW format) — tabular DFD with 7 data flows; old DFD was "
    "image-only and did not show auth, DB, or multi-resume flow.",
]:
    add_bullet(s)

add_heading("§2.2 Methodologies", 3)
add_para("Old version had 11 sub-sections; new version has 14:", space_after=6)
add_compare_table(
    rows=[
        ["2.2.1 Architecture (4 layers)",
         "2.2.1 Architecture (6 layers) — added AI/Feature Packages, Data Layer, "
         "Auth & Session Layer"],
        ["—", "2.2.2 Authentication and Session Management (NEW)"],
        ["2.2.2 Input Validation",
         "2.2.3 Input Validation (mentions hydration retry)"],
        ["2.2.3 Resume Text Extraction (PyPDF2 only)",
         "2.2.4 Resume Text Extraction (PDF + DOCX; parse-confidence indicator)"],
        ["2.2.4 AI Analysis",
         "2.2.5 AI Analysis (model name, fallback chain, truncation limits)"],
        ["2.5 Programmatic Metrics (8 metrics)",
         "2.2.9 Scoring Engine — Eleven Metrics (full table with function names)"],
        ["2.2.6 Hybrid Scoring (simple (AI+Rule)/2)",
         "2.2.9 Weighted Final-Score Formula (full table, JD-aligned vs no-JD modes)"],
        ["2.2.7 Report Generation",
         "2.2.11 Report Generation (PDF + JSON + DOCX + CSV outputs across modules)"],
        ["2.2.8 Error Handling",
         "2.2.12 Error Handling (added quota short-circuit, cookie validation, DB "
         "rollback)"],
        ["2.2.9 UI / UX",
         "2.2.13 UI / UX (added dark-theme guard, sticky sidebar, animated bar)"],
        ["2.2.10 System Constraints",
         "2.2.14 System Constraints"],
        ["2.2.11 Use Cases", "Removed — replaced by Workflow chapter (§2.1)"],
        ["—", "2.2.6 Multi-Resume Comparison Pipeline (NEW)"],
        ["—", "2.2.7 Cover Letter Generation (NEW)"],
        ["—", "2.2.8 Resume Builder (NEW)"],
        ["—", "2.2.10 Persistence and Data Model (NEW — full 5-table schema)"],
    ],
    col_widths=[3.0, 3.8],
)

add_heading("§2.3 Software & Hardware Requirements", 3)
add_compare_table(
    rows=[
        ["Python 3.8+",
         "Python 3.11+ (codebase uses match statements and PEP 604 union syntax)"],
        ["4 dependencies (Streamlit, PyPDF2, google-generativeai, python-dotenv)",
         "11 dependencies from actual requirements.txt: streamlit, pypdf, PyPDF2, "
         "python-docx, google-generativeai, sqlalchemy, bcrypt, reportlab, "
         "python-dotenv, requests, streamlit-sortables, playwright"],
        ["External services: Gemini only",
         "Gemini + Google OAuth + SMTP"],
        ["Config: .env, .env.example",
         "+ .streamlit/config.toml (upload cap, file watcher, theme tokens)"],
        ["Hardware specs (minimum / recommended / server)",
         "Kept similar with updated storage figures"],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("§2.4 Proposed Work", 3)
add_compare_table(
    rows=[
        ["10 completed features", "26 completed features"],
        ["\"Dual-mode\" listed as feature", "REMOVED (no longer exists)"],
        ["\"Markdown / JSON export\"", "\"PDF / JSON export\""],
        ["—", "Multi-resume comparison + ranking + Top Match + CSV/PDF export (NEW)"],
        ["—", "Cover Letter Generator + DOCX download (NEW)"],
        ["—", "Resume Builder + 3 templates + AI bullets + live preview (NEW)"],
        ["—", "Authentication + Google OAuth + session cookies (NEW)"],
        ["—", "Per-user persistence + My CVs / Analyses / Comparisons (NEW)"],
        ["—", "Human-vs-AI evaluation toolkit (NEW)"],
        ["—", "Gemini 429 quota short-circuit (NEW)"],
        ["Future enhancements: long list",
         "Trimmed — moved shipped items out; kept actual backlog (real-time preview "
         "extension, DB-backed snapshots, OCR, bounded parallelism, industry-specific "
         "weighting)"],
    ],
    col_widths=[3.0, 3.8],
)

# ════════════════════════════════════════════════════════════════════
# CHAPTER 3
# ════════════════════════════════════════════════════════════════════
page_break()
add_heading("7. Chapter 3 — Tests, Output & Performance", 2)

add_heading("§3.1 Test Cases — Biggest Expansion", 3)
add_para(
    "Old: 27 tests across 6 tables (all Pass). New: 68 tests across 9 tables "
    "(all Pass).",
    space_after=6,
)
add_compare_table(
    rows=[
        ["3.1.1 Input Validation (5 tests)",
         "3.1.1 Input Validation (6 tests) — added hydration retry test"],
        ["3.1.2 PDF Processing (5 tests)",
         "3.1.2 File Processing — PDF + DOCX (6 tests) — added DOCX, mixed content, "
         "empty file"],
        ["3.1.3 AI Integration (5 tests)",
         "3.1.3 AI Integration (6 tests) — added partial-JSON fail-soft test"],
        ["3.1.4 Scoring (5 tests)",
         "3.1.4 Scoring (8 tests) — added Bullets Consistency, Weighted Final Score, "
         "No-JD Mode"],
        ["3.1.5 Mode-switch tests (3 tests)",
         "REMOVED — feature no longer exists"],
        ["3.1.6 Edge Cases (4 tests; one had typo)",
         "3.1.9 Edge Cases (6 tests) — fixed the duplicate Input/Expected typo, added "
         "concurrent saves + theme switch"],
        ["—", "3.1.5 Auth & Persistence (10 tests) — NEW: register, sign-in, OAuth, "
         "persistent login, logout, protected page gate, forgot password, history "
         "survives logout, delete account"],
        ["—", "3.1.6 Multi-Resume Comparison (12 tests) — NEW: 2-file, 5-file, 1-file "
         "rejection, dedup, sort change, ★ winner glued, CSV, PDF, 429 mid-run, "
         "open-as-full-report, autosave, browser back"],
        ["—", "3.1.7 Resume Builder (9 tests) — NEW: template switch, reorder, hide, "
         "AI bullet, save/load, PDF, live preview, customisation persist"],
        ["—", "3.1.8 Cover Letter (5 tests) — NEW: basic, optional fields, DOCX "
         "download, missing JD, auth gate"],
    ],
    col_widths=[3.0, 3.8],
)

add_para("Fixes to original test tables:", bold=True, space_after=4)
for s in [
    "TC-04 \"Upload restricted to PDF\" → \"PDF / DOCX\".",
    "TC-24 had the same text for Input Description and Expected Outcome (both said "
    "\">10,000 characters\") → fixed: Expected now says \"Text truncated to 6,000 for "
    "Gemini\".",
    "Tables 3.1.4 and 3.1.5 in the old PDF were both titled \"Scoring System "
    "Validation\" (duplicate) → fixed: 3.1.5 is now \"Authentication & Persistence\".",
]:
    add_bullet(s)

add_heading("§3.2 Observed Output", 3)
add_compare_table(
    rows=[
        ["3 screenshots (old UI, circular score, dual-mode visible)",
         "6 figure placeholders with descriptive captions of what to capture: Home, "
         "Compare Results, Single Report, Resume Builder, Cover Letter, My "
         "Comparisons. User inserts the actual screenshots."],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("§3.3 Performance Analysis", 3)
add_compare_table(
    rows=[
        ["§3.3.1 Response Time table",
         "Kept with same figures (5.4 s average) but renamed components — \"PDF\" → "
         "\"PDF / DOCX Extraction\", added \"Programmatic Scoring (11 metrics)\""],
        ["§3.3.2 Bottleneck (3 rows)",
         "4 rows — added \"Scoring + JSON + everything else (~2%)\" so percentages "
         "add up cleanly"],
        ["§3.3.3 Scalability constraints",
         "Updated — added SQLite single-writer note"],
        ["§3.3.3 Throughput Capacity (3 rows)",
         "4 rows — added bounded-parallelism scenario"],
        ["§3.3.4 Memory Usage (inconsistent in original — ~15/min = 50 MB but "
         "~60/min = 10-20 MB, which is backwards)",
         "Fixed: idle (~80 MB), single-CV analysis (~110 MB), 5-resume compare "
         "(~150 MB), builder with cached PDF (~120 MB)"],
        ["§3.3.5 Comparative Analysis (6 parameters)",
         "9 parameters — added Output Artifacts, Multi-Resume Shortlisting, "
         "Persistent History rows"],
        ["§3.3.6 Optimizations",
         "Expanded — added cached PDF builders (CV + comparison), session-state "
         "reuse, model fallback explicit"],
        ["§3.3.7 Validation Summary",
         "Updated wording to reflect new module set"],
    ],
    col_widths=[3.4, 3.4],
)

# ════════════════════════════════════════════════════════════════════
# CHAPTER 4
# ════════════════════════════════════════════════════════════════════
page_break()
add_heading("8. Chapter 4 — Conclusion, Challenges, Future Scope, References", 2)

add_heading("§4.1 Conclusion", 3)
add_compare_table(
    rows=[
        ["6 paragraphs talking only about single-CV analysis + dual-mode",
         "6 paragraphs rewritten — covers all 5 modules, hybrid scoring, weighted "
         "formula, multi-resume shortlisting, cover letter + builder closing the loop, "
         "modular architecture, evaluation toolkit"],
        ["\"Average analysis time ~5.4 s\"",
         "Kept the figure, attributed properly to Gemini latency"],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("§4.2 Challenges", 3)
add_compare_table(
    rows=[
        ["Technical (4): PDF extraction, AI consistency, rate limits, score stability",
         "Same 4 + added Multi-Feature Integration challenge"],
        ["Design (3): Information density, mobile, theme consistency",
         "Same 3 + added Real-Time Preview vs Streamlit Rerun Model"],
        ["Operational (1): API costs", "Same + added Data Privacy"],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("§4.3 Future Scope", 3)
add_compare_table(
    rows=[
        ["Listed \"multi-resume comparison\" as future", "REMOVED (shipped)"],
        ["Listed \"PDF export\" as future", "REMOVED (shipped)"],
        ["Listed \"user history\" as future", "REMOVED (shipped)"],
        ["Listed \"cover letter generation\" as long-term", "REMOVED (shipped)"],
        ["Listed \"resume templates\" as future",
         "REMOVED (shipped — 3 templates: Classic, Creative, Modern)"],
        ["ML integration, OCR, multilingual, video resume, blockchain, mobile apps, "
         "enterprise", "KEPT (still backlog)"],
        ["—",
         "Added: DB-backed snapshots, shareable comparison permalinks, real-time "
         "preview extension, bounded parallelism, E2E tests, static-page content"],
    ],
    col_widths=[3.4, 3.4],
)

add_heading("References", 3)
add_compare_table(
    rows=[
        ["5 entries (4 library URLs + spaCy)",
         "12 entries in proper IEEE format"],
        ["Academic papers cited in §1.2 missing from References",
         "Added the 4 academic papers (Devlin BERT, Chandra & Kaur, Kumar & Gupta, "
         "Miller & Bhattacharya)"],
        ["—",
         "Added: pypdf docs, python-docx docs, ReportLab guide, SQLAlchemy 2.0 docs, "
         "Python Cookbook (Beazley & Jones)"],
        ["Streamlit, Gemini, PyPDF2, Python — kept",
         "Kept all with proper IEEE formatting"],
    ],
    col_widths=[3.4, 3.4],
)

# ════════════════════════════════════════════════════════════════════
# COSMETIC FIXES
# ════════════════════════════════════════════════════════════════════
page_break()
add_heading("9. Cosmetic Fixes Throughout", 2)

for s in [
    "\"Stream lit\" (two words) → \"Streamlit\" (correct spelling) — was wrong in "
    "~15 places.",
    "\"google-generative ai\" (with space) → \"google-generativeai\" (correct).",
    "\"python-dot env\" (with space) → \"python-dotenv\" (correct).",
    "Page numbers cut off / inconsistent in old PDF → auto-numbered \"Page | N\" "
    "footer on every page of new DOCX.",
]:
    add_bullet(s)

# ════════════════════════════════════════════════════════════════════
# SUMMARY IN NUMBERS
# ════════════════════════════════════════════════════════════════════
add_heading("10. Summary in Numbers", 2)
add_compare_table(
    rows=[
        ["Total test cases", "27", "68"],
        ["Tables (excluding TOC)", "~9", "17"],
        ["Figures referenced", "4", "8"],
        ["Documented features", "~10", "26"],
        ["Dependencies listed", "4", "11"],
        ["Reference entries", "5", "12"],
        ["Scoring metrics covered", "8", "11"],
        ["Hybrid formula", "(AI + Rule) / 2",
         "5-component weighted breakdown"],
        ["Approximate page count", "~36", "~40"],
    ],
    headers=["Metric", "Old PDF", "New DOCX"],
    col_widths=[2.4, 1.8, 2.6],
)

# ════════════════════════════════════════════════════════════════════
# WHAT YOU STILL NEED TO DO
# ════════════════════════════════════════════════════════════════════
add_heading("11. What You Still Need to Do Before Submitting", 2)

for n, item in [
    (1, "Open Minor_Project_Report.docx in MS Word to verify formatting (page breaks, "
        "table widths, font rendering)."),
    (2, "Insert the 6 screenshots at Figure 3.2.1–3.2.6 (each currently has a "
        "placeholder with a caption explaining what to capture)."),
    (3, "Add a proper DFD diagram image at §2.1.6 if your college prefers visual over "
        "tabular DFD (the new report includes a tabular DFD as a substitute)."),
    (4, "Sign / get supervisor signature on the Recommendation page."),
    (5, "Examiner signature page (§Certificate of Approval) has 4 numbered blank lines "
        "for signatures — leave blank for examiners to sign at viva."),
    (6, "Convert to PDF when ready: in Word, File → Save As → PDF."),
    (7, "Optional: re-run the generator at any time via "
        "`py -3 tmp/generate_minor_report.py` — the script overwrites the DOCX so "
        "tweaks can be regenerated easily."),
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.25)
    run = p.add_run(f"{n}. ")
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = "Calibri"
    run = p.add_run(item)
    run.font.size = Pt(11)
    run.font.name = "Calibri"

doc.save(OUT)
print(f"Generated: {OUT}")
print(f"Size: {OUT.stat().st_size:,} bytes")
