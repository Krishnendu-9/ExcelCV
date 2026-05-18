# ExcelCV — Development Status for Claude

This file is for Claude to read at the start of a new session so it can immediately understand
what has been built, what is working, and what still needs to be done.

Last updated: **2026-05-18**

---

## Project Overview

**ExcelCV** — AI-powered CV reviewer, multi-resume comparator, cover-letter generator, and
resume builder built with Streamlit + Google Gemini.
- Run: `streamlit run app.py --server.port 8501`
- Database: SQLite (SQLAlchemy ORM) — `src/database.py`
- Auth: email/password + Google OAuth (cookies for session persistence)
- AI: Google Gemini via `src/gemini_client.py` (default `models/gemini-2.0-flash`)

For the canonical project snapshot, see [docs/excelcv.md](docs/excelcv.md). For setup,
see [docs/SETUP.md](docs/SETUP.md).

---

## Architecture

```
app.py                                ← Main router (page dispatch, theme, auth gating)
src/
  auth_utils.py                       ← Session, cookies, password hashing, login/logout
  config.py                           ← Env loading, MAX_FILE_BYTES / MAX_FILE_MB
  database.py                         ← SQLAlchemy models: User, PasswordResetToken,
                                         CV, Analysis, Comparison
  gemini_client.py                    ← Gemini API calls (CV analysis, bullet suggestions)
  email_utils.py                      ← Password reset email
  oauth_utils.py                      ← Google OAuth token exchange
  pdf_utils.py                        ← PDF/DOCX text extraction
  assets/ui/base_theme.css.tpl        ← Global CSS template
  cover_letter/
    page.py                           ← Cover-letter page renderer
    service.py                        ← Orchestration (parse → prompt → Gemini → result)
    generator.py                      ← Prompt construction + Gemini call
    models.py                         ← CoverLetterResult dataclass
    validators.py                     ← Input validation
    docx_builder.py                   ← DOCX export
  services/
    scoring.py                        ← Deterministic scoring engine
    scoring_constants.py              ← Score weights, thresholds
    evaluation.py                     ← Human-vs-AI evaluation metrics
    reporting.py                      ← PDF / JSON report builder
    pdf_generator.py                  ← CV PDF export (ReportLab, template-aware)
    comparison_pdf.py                 ← Multi-resume comparison PDF
    career_tools.py                   ← Supporting career utility functions
  ui/
    app_utils.py                      ← APP_PAGES registry, URL helpers, snapshot store
    layout.py                         ← Header (nav + user dropdown), footer
    theme.py                          ← Theme CSS variable injection
    css_injection.py                  ← Global CSS helpers
    css_generators.py                 ← Theme-aware CSS builders
    ui_components.py                  ← Shared UI primitives
    ui_constants.py                   ← UI-wide constants
    common.py                         ← Shared helpers (issue_count, score color, etc.)
    auth_page.py                      ← Sign In / Sign Up / Google OAuth page
    upload.py                         ← Home / Analyze CV + Compare form
    analysis_runner.py                ← Analysis + comparison orchestration
    report.py                         ← Single-resume report
    compare_report.py                 ← Dedicated comparison results page
    cv_builder_page.py                ← Resume Builder entry
    cv_builder_constants.py           ← Template configs, zoom, section order
    cv_builder_pdf.py                 ← Resume Builder PDF export
    cv_builder_preview_data.py        ← Preview-data assembly
    cv_builder_value_utils.py         ← Value normalization helpers
    my_cvs_page.py                    ← Saved CVs list
    my_analyses_page.py               ← Saved analyses list
    my_comparisons_page.py            ← Saved comparisons list
    settings_page.py                  ← Account settings
    static_pages.py                   ← Info/legal pages + cover-letter dispatch
```

---

## COMPLETED FEATURES

### Core Application
- [x] Full page routing via `app.py` (home, upload, report, compare-report, cover-letter,
      resume-builder, my-cvs, my-analyses, my-comparisons, settings, auth, static pages)
- [x] Theme toggle (light/dark) with localStorage persistence across sessions
- [x] Google OAuth sign-in flow (exchange code → create user → set session cookie)
- [x] Email/password sign-in, sign-up, forgot password (email reset link)
- [x] Session cookie restore (persistent login across page reloads, opt-in)
- [x] Protected pages redirect to auth gate, then bounce back to intended page
- [x] Logout clears cookie and session

### Header & Footer
- [x] Site header with logo, nav links, user dropdown
- [x] User dropdown: My Comparisons, Settings, Logout (plus feedback/support)
- [x] Full-width professional footer with product/resource/legal columns
- [x] Active nav item highlighting per page (including compare-return state)

### Home / Analyze CV Page
- [x] File upload (PDF/DOCX, ≤ 2 MB), job description textarea
- [x] Gemini AI analysis with score, issues, skill gaps
- [x] Animated hero illustration with horizontal score bar + category bars
- [x] Compare mode (multiple CVs) — form anchored inside this page

### Multi-Resume Comparison (full reference: docs/compareCV.md)
- [x] Dedicated `compare-report` page (not inline)
- [x] 2-5 file upload with form-stage + runner-stage dedup
- [x] Ranked table with inline meter bars, color-coded score tiers
- [x] 8 sort options; rank column re-numbers on sort
- [x] Top Match card (right column) + identity-based ★ winner pill
- [x] Per-resume drill-down expanders → "Open as full report"
- [x] CSV export + ReportLab PDF export
- [x] Autosaved per user to `comparisons` table
- [x] My Comparisons history page (route: `my-comparisons`)
- [x] Gemini 429 / quota short-circuit (remaining files marked `skipped`)
- [x] One-shot scroll-to-top on entry; return-to-compare hints for browser back

### Cover Letter Generator
- [x] Resume + JD inputs (+ optional company / role / source / tone)
- [x] Gemini-generated cover letter
- [x] Markdown view + DOCX download
- [x] Auth-gated

### Report Page (full reference: docs/report_page.md)
- [x] Full analysis report rendering (4 group cards + sticky sidebar)
- [x] Shareable snapshot via `?rid=` query param (in-memory store)
- [x] **Horizontal animated score bar** (was a circular ring; restyled this session)
      shared engine with hero panel via `@property --hv-p` + `@keyframes hv-sweep`
- [x] PDF + JSON download
- [x] Model evaluation toolkit (MAE / RMSE / correlation) inside collapsed expander

### My CVs / My Analyses / My Comparisons
- [x] List view, open / re-load, delete (with confirm)
- [x] Per-user persistence survives logout

### Settings Page
- [x] Change email (with password verification)
- [x] Change password
- [x] Delete account (with confirmation dialog)
- [x] Card-styled UI matching homepage design

### Resume Builder Page (full reference: docs/resume_builder.md)
- [x] 3-panel workspace (left rail, middle editor, right preview)
- [x] Three templates: **Classic, Creative, Modern** (defined in `cv_builder_constants.py`
      → `TEMPLATE_CONFIGS`). Each has distinct layout in both live preview and PDF.
- [x] Canonical sections: personal, summary, experience, education, skills, projects,
      languages, certifications, interests
- [x] Section reorder, hide/show (eye icon), collapse/expand (chevron)
- [x] AI bullet suggestion via Gemini (uses existing bullets as context)
- [x] Customize controls: accent color, font, font size, line height, entry spacing
      — all persisted with the saved CV
- [x] Save / Load to DB; import / export JSON; one-click PDF download
- [x] Cached PDF generation (`_cached_generate_cv_pdf` — only rebuilds on data change)
- [x] Real-time preview for Personal Details fields via postMessage JS bridge
- [x] Widget-state protection across reruns (`_protect_builder_widget_state`)

---

## KNOWN ISSUES / NOT YET DONE

### Resume Builder
- [ ] Real-time preview only covers Personal Details fields. Experience / Education / Skills /
      Projects / Certifications still re-render on Streamlit's normal rerun.
- [ ] Blank preview on first load (no skeleton / sample data).
- [ ] `cv_builder_page.py` is still ~6.2k lines after the split into
      `cv_builder_constants.py / cv_builder_pdf.py / cv_builder_preview_data.py /
      cv_builder_value_utils.py`. Further extraction is possible.

### Comparison
- [ ] No shareable permalink for saved comparisons (per-user only — by design for v1).
- [ ] Sequential per-file Gemini calls (intentional, see compareCV.md §7 — quota contract).
      Bounded parallelism is a backlog item.

### Analysis / Report Page
- [ ] Snapshot store is in-memory (`@st.cache_resource` dict) — shareable `?rid=` links
      survive Streamlit reruns but NOT a server restart. Production: move to DB-backed.

### Static Pages
- [ ] Many static pages (ATS Insights, Evaluation Toolkit, Project Notes, How It Works,
      Interview Prep, Privacy Policy, Terms of Service) still need real content.

### Contact Page
- [ ] Contact form is wired but only works if SMTP env vars are set. No visual feedback
      when email is not configured.

### General / Infrastructure
- [ ] No production deployment config. Currently runs locally on port 8501.
- [ ] Thin test coverage — only `test_oauth_utils.py` and `test_scoring_sections_order.py`
      under `tests/`. The CV-builder JS bridge has no automated coverage.

---

## KEY FILES TO KNOW

| File | Why it matters |
|------|---------------|
| `app.py` | All page routing, auth gating, theme sync |
| `src/ui/app_utils.py` | `APP_PAGES`, URL helpers, in-memory snapshot store |
| `src/ui/upload.py` | Analyze CV + Compare form (one page, two modes) |
| `src/ui/compare_report.py` | Dedicated comparison-results page |
| `src/ui/report.py` | Single-resume analysis report |
| `src/ui/cv_builder_page.py` | Resume Builder — most recently worked on |
| `src/cover_letter/page.py` | Cover-letter page renderer |
| `src/cover_letter/service.py` | Cover-letter pipeline |
| `src/ui/layout.py` | Header + footer for every page |
| `src/ui/css_injection.py` | Global CSS overrides (compact header, etc.) |
| `src/assets/ui/base_theme.css.tpl` | Global CSS template (theme tokens, hero bar, report bar) |
| `src/auth_utils.py` | Session, cookies — touch with care |
| `src/database.py` | SQLAlchemy models: User, PasswordResetToken, CV, Analysis, Comparison |
| `src/gemini_client.py` | AI calls — `analyze_cv_with_gemini()`, `suggest_cv_bullets()` |
| `src/services/scoring.py` | Deterministic scoring + `calculate_final_score_breakdown` |
| `src/services/comparison_pdf.py` | ReportLab comparison PDF |
| `src/services/pdf_generator.py` | CV PDF export |

---

## RECENT SESSION WORK (2026-05-18)

### Score display restyled — circle → horizontal bar
- Both score visualizations switched from a 148×148 (hero) / 140×140 (report) circular
  conic-gradient ring to a 12px-tall horizontal linear-gradient bar.
- Same animation engine retained: `@property --hv-p` (registered as `<percentage>`) +
  `@keyframes hv-sweep` — `--hv-p` now drives a hard linear-gradient stop instead of a
  conic-gradient stop, so the bar fills 0 → score% with the same easing.
- Hero card (`src/ui/upload.py` → `render_upload_preview_card`):
  - Made `.hero-visual` a `display: flex; flex-direction: column; height: 100%` container.
  - `.hv-bars` gets `margin-top: auto` so the score block stays at the top and the
    Content/Sections/ATS Essentials/Insights bars + tips push down to fill the column
    height (Streamlit columns stretch — the card no longer has dead space below the tips).
- Report sidebar (`src/ui/report.py` score card):
  - `.report-score-ring-wrap` is now flex column auto-height (`max-width: 300px`),
    `.report-score-ring` is the horizontal bar, `.report-score-ring-label` is `flex-row`
    with `flex-wrap: wrap` so `.rsr-issues` flows onto its own line below `.rsr-num` /
    `.rsr-den`.
- All class names kept (`.report-score-ring*`, `.hv-ring*`) for compatibility, even though
  the markup is no longer a ring — see docs/report_page.md §11 note.

### Earlier (2026-04-30) — Resume Builder backend
1. Customization (accent_color, font, font_size, line_height, entry_spacing) persisted in
   DB under `data["customization"]` and restored on load.
2. Font Size / Line Height / Entry Spacing controls added inside the Customize expander
   and wired end-to-end to both `generate_cv_html()` and `generate_cv_pdf()`.
3. PDF generation cached via `_cached_generate_cv_pdf()` (`@st.cache_data`).
4. `_save_cv` rolls back on DB error.
5. Bullet removal cleans up orphan session-state keys.
6. AI bullet suggestions pass existing bullets as `context` to avoid duplication.
7. PDF generator XML-escapes user text (fixes `<` / `&` crashes in `Paragraph` markup).

### Earlier (2026-04-29) — Real-time preview
1. Real-time preview for Personal Details fields via postMessage JS bridge
   (`inject_cv_builder_realtime_js()` — 0-height iframe capture-phase listener).
2. Removed "Press Enter to apply" tooltip
   (`[data-testid="InputInstructions"] { display: none !important; }`).

---

## HOW TO START NEXT SESSION

1. Read this file + skim [docs/excelcv.md](docs/excelcv.md) for the current snapshot.
2. For the area you're touching, also read:
   - Comparison work → [docs/compareCV.md](docs/compareCV.md)
   - Report-page work → [docs/report_page.md](docs/report_page.md)
   - Resume Builder work → [docs/resume_builder.md](docs/resume_builder.md)
3. Ask the user what they want to work on next.

Good next steps to suggest if the user doesn't have a specific request:
- Extend real-time preview to Experience/Education/Skills sections
- Skeleton/sample data for the blank-preview-on-first-load case
- Move report snapshots to DB-backed persistence (survive server restarts)
- Add shareable permalink for saved comparisons
- Fill in content for the placeholder static pages
- Add E2E test coverage (Playwright) for the CV-builder JS bridge
