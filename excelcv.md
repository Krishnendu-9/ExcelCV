# ExcelCV Complete Project Guide

This file explains the full project in two ways:
- very simple language first (so anyone can understand),
- then detailed technical explanation (for developers and AI agents).

---

## 1) Super Simple Explanation (Kid-Friendly)

Imagine ExcelCV is a smart teacher for resumes.

- You give it:
  - a **job description** (what company wants),
  - and a **resume** (what candidate has done).
- It checks:
  - Is the resume easy for ATS software to read?
  - Does it have numbers and impact?
  - Is it missing important sections?
  - Does it match the job needs?
- Then it gives:
  - a score,
  - problems to fix,
  - suggestions to improve,
  - and downloadable report.

It also has:
- login/signup,
- resume builder,
- saved resumes,
- saved past analyses,
- compare multiple resumes side-by-side.

Theme button (light/dark) changes colors, but user data should stay safe in session and DB.

---

## 2) Product Purpose

ExcelCV is a Streamlit-based web app that combines:
- deterministic ATS-style scoring logic,
- Gemini-assisted qualitative analysis,
- explainable scoring breakdown,
- user account + persistence.

Main goal: help users improve resumes quickly with transparent and actionable feedback.

---

## 3) Main Working Features

## 3.1 Resume Analysis (Single File)
- Input: one JD + one resume (`.pdf` or `.docx`, max `2MB`).
- Output:
  - final match score,
  - category-level and metric-level analysis,
  - issue count,
  - missing skills,
  - rewrite guidance,
  - recruiter-style summary.

## 3.2 Multi-Resume Comparison
- Input: one JD + `2-5` resumes.
- Output table:
  - Resume name,
  - Final Score,
  - JD Alignment,
  - ATS Parse,
  - Sections,
  - Issues,
  - Top Missing Skills.
- Sorted by Final Score descending.

## 3.3 Explainable Scoring
- Score is not magic.
- App returns weighted components and formula.
- Modes:
  - `jd_aligned` when JD exists,
  - `no_jd` when JD is missing.

## 3.4 CV/Resume Builder
- Build resume from structured form sections.
- Save resume template/data in DB.
- Load old resume back into builder.
- Export generated PDF.

## 3.5 Account Features
- Sign in / Create account.
- Google OAuth support (if configured).
- Password reset via email (if SMTP configured).
- My CVs page (saved resumes).
- My Analyses page (analysis history).

## 3.6 Reports and Downloads
- Report rendering with section cards.
- Download report as PDF and JSON/markdown-style content.
- Evaluation toolkit for human-vs-model benchmark metrics.

---

## 4) Frontend UX, Styling, Positioning, Theme

## 4.1 UI Stack
- Streamlit widgets + custom HTML/CSS + injected JS.
- Heavy styling customization in:
  - `src/ui/theme.py`
  - `src/ui/css_injection.py`
  - `src/assets/ui/base_theme.css.tpl`
  - `src/assets/ui/base_theme.js.tpl`

## 4.2 Header and Navigation
- Header built in `src/ui/layout.py`.
- Shows:
  - logo,
  - nav links (`Analyze CV`, `Resume Builder`, `My CVs`, `My Analyses`, `Compare`),
  - auth area (Sign In OR user dropdown),
  - theme toggle.
- Protected pages auto-route logged-out users to auth.

## 4.3 Fixed Top Bar Behavior
- `inject_fixed_top_bar()` pins header near top with dynamic spacer.
- Prevents content overlap while scrolling.
- `inject_header_layout_override()` forces nav to avoid internal scrolling boxes.

## 4.4 Theme System
- Theme values: `light` / `dark`.
- Stored in `st.session_state["theme"]`.
- Synced to browser `localStorage` by `_inject_theme_persistence()`.
- `_t` query param temporarily carries theme across hard reload/session resets.
- CSS variables and major color tokens generated in `src/css_generators.py`.

## 4.5 URL and Scroll Cleanup
- `_inject_url_and_anchor_cleanup()` removes stale hash/query noise and home-anchor jump side effects.
- `inject_back_button_sync()` removes legacy listeners that previously caused forced reload loops on browser back.
- `_inject_chunk_load_recovery()` tries one safe reload for chunk import failures.

---

## 5) Backend and Core Logic

## 5.1 Routing Orchestrator (`app.py`)
- Initializes Streamlit config and DB.
- Handles:
  - cookie/session restore,
  - logout,
  - OAuth callback,
  - password reset token,
  - page routing,
  - protected page auth gate,
  - theme + style injections.

## 5.2 Analysis Pipeline
- Main execution module: `src/ui/analysis_runner.py`.
- Steps:
  1. Validate inputs.
  2. Extract resume text (`src/pdf_utils.py`).
  3. Run Gemini + deterministic scoring (`src/gemini_client.py`, `src/scoring.py`).
  4. Save to session + snapshot.
  5. Optionally autosave analysis to DB for logged-in users.

## 5.3 Deterministic Scoring (`src/scoring.py`)
- Metrics include:
  - ATS parse rate,
  - quantifying impact,
  - repetition (action-verb variety),
  - spelling/grammar heuristics,
  - section completeness,
  - ATS essentials,
  - contact completeness,
  - tailoring/JD alignment.
- Final score breakdown:
  - With JD:
    - Content Quality `0.30`
    - JD Alignment `0.25`
    - Sections `0.15`
    - ATS Essentials `0.15`
    - Contact `0.15`
  - Without JD:
    - Content Quality `0.35`
    - Sections `0.25`
    - ATS Essentials `0.25`
    - Contact `0.15`

## 5.4 AI Layer (`src/gemini_client.py`)
- Picks preferred model from config fallback list.
- Handles retryable errors and quota failures.
- Sanitizes prompts and extracts JSON safely from model output.
- Merges AI-generated insights with deterministic analysis fields.

## 5.5 Resume Text Extraction (`src/pdf_utils.py`)
- Supports PDF and DOCX extraction.
- Validates text presence.
- Computes parse confidence chip labels for UX.

## 5.6 Career Helper Outputs (`src/career_tools.py`)
- Generates:
  - recruiter snapshot,
  - priority action plan,
  - interview prep questions,
  - learning roadmap,
  - portfolio checklist.

## 5.7 Reporting (`src/reporting.py`, `src/ui/report.py`)
- `src/reporting.py` builds downloadable report outputs.
- `src/ui/report.py` builds rich HTML cards and sidebar navigation.
- Includes explainable scoring, skill matrix, rewrite assistant, and category drill-down.

---

## 6) Authentication and Security Logic

Main files:
- `src/auth_utils.py`
- `src/oauth_utils.py`
- `src/email_utils.py`

Features:
- bcrypt password hashing and verification.
- HMAC-signed session token cookie.
- Restore session from cookie on app start.
- Google OAuth sign-in (optional env setup).
- Password reset token generation/use.
- Contact/reset emails through SMTP config.

Protected pages:
- `cv-builder` / `resume-builder`
- `my-cvs`
- `my-analyses`
- `compare-cv`

If not logged in, user is redirected to `auth` with intended destination preserved.

---

## 7) Database Design

File: `src/database.py`

Engine:
- SQLite via SQLAlchemy.
- DB path: `data/excelcv.db`.

Models:
- `User`
  - account identity and auth fields.
- `PasswordResetToken`
  - one-time reset token with expiration/usage flags.
- `CV`
  - saved resume builder JSON data + template metadata.
- `Analysis`
  - saved analysis results + score + JD + cv name.

Also includes lightweight migration helper (`_migrate`) for additive schema updates.

---

## 8) Page-by-Page Frontend Logic

## 8.1 Home/Upload (`src/ui/upload.py`)
- Hero + chips + JD textarea.
- Logged-in:
  - upload form and analyze button.
- Logged-out:
  - upload locked card and sign-in CTA.
- Compare section rendered below and can work in compare mode.

## 8.2 Auth (`src/ui/auth_page.py`)
- Unified auth workspace:
  - sign in,
  - create account,
  - forgot password,
  - reset password.
- Theme-aware surfaces, form styling, and logo branding.

## 8.3 Resume Builder (`src/ui/cv_builder_page.py`)
- Session-state-driven dynamic form sections:
  - personal info,
  - summary,
  - experience,
  - education,
  - skills categories,
  - projects,
  - certifications.
- Generate HTML preview and export PDF.
- Save/update user CV record.

## 8.4 My CVs (`src/ui/my_cvs_page.py`)
- Lists saved CVs.
- Actions:
  - open in builder,
  - download PDF,
  - delete with confirmation.

## 8.5 My Analyses (`src/ui/my_analyses_page.py`)
- Lists historical analysis results.
- Actions:
  - view full report,
  - delete record.

## 8.6 Report (`src/ui/report.py`)
- Sidebar score summary + expandable categories.
- Detailed cards for all metrics and recommendations.
- Download buttons and evaluation toolkit integration.

## 8.7 Static Pages (`src/ui/static_pages.py`)
- Project notes, ATS insights, how-it-works, legal pages, contact, etc.
- Includes contact email form handling.

---

## 9) State Management and URL Logic

Main state patterns:
- `st.session_state["page"]` controls route.
- query params (`page`, `rid`, `next`, `_t`) support deep-linking and persistence.
- report snapshots saved in in-memory store (`_report_snapshot_store`) for recoverable report routing.
- `_set_query_params_atomic()` avoids noisy multi-history updates.

This is critical for browser-back behavior and avoiding repeated back presses.

---

## 10) File Structure (What Each Important File Does)

```text
cv-review/
  app.py                          -> app entrypoint, routing, auth gating, injections
  README.md                       -> user/dev quick overview
  SETUP.md                        -> setup and environment guide
  PRD_CV.txt                      -> product requirement notes
  requirements.txt                -> runtime dependencies
  requirements-dev.txt            -> development/test dependencies
  data/
    excelcv.db                    -> sqlite database file
  docs/
    architecture.md               -> high-level architecture notes
    mockups/                      -> html visual mockups
  src/
    __init__.py
    config.py                     -> env/config constants and model preferences
    database.py                   -> ORM models + DB init/migration
    auth_utils.py                 -> login/session/cookie/password reset primitives
    oauth_utils.py                -> Google OAuth URL + token exchange
    email_utils.py                -> SMTP email sending helpers
    pdf_utils.py                  -> PDF/DOCX text extraction and parse confidence
    gemini_client.py              -> Gemini calls, retries, output cleanup
    scoring_constants.py          -> scoring thresholds/constants/word maps
    scoring.py                    -> deterministic scoring + explainable breakdown
    career_tools.py               -> action plan/interview/roadmap/checklists
    reporting.py                  -> report text/pdf builders
    evaluation.py                 -> MAE/RMSE/correlation calculations
    css_generators.py             -> theme CSS string generation helpers
    ui_constants.py               -> fixed UI token constants
    ui_components.py              -> compatibility exports for UI helpers
    services/
      __init__.py
      pdf_generator.py            -> resume-builder PDF generation
    assets/
      ui/
        base_theme.css.tpl        -> base CSS template
        base_theme.js.tpl         -> base JS template
    ui/
      __init__.py
      app_utils.py                -> routing links, state clear, snapshot logic
      common.py                   -> shared UI helper functions
      css_injection.py            -> injected CSS/JS for layout and behavior overrides
      theme.py                    -> base theme injection + listener cleanup
      layout.py                   -> site header/footer/theme toggle
      upload.py                   -> home upload + compare page content
      report.py                   -> report and evaluation rendering
      analysis_runner.py          -> single/multi analysis execution
      auth_page.py                -> auth UI and flows
      cv_builder_page.py          -> resume builder full UI + save/export
      my_cvs_page.py              -> saved resume list page
      my_analyses_page.py         -> saved analysis list page
      static_pages.py             -> informational pages and contact page
  tests/
    test_app_helpers.py
    test_career_tools.py
    test_evaluation.py
    test_gemini_client_helpers.py
    test_pdf_utils.py
    test_reporting.py
    test_report_builders.py
    test_scoring.py
    test_streamlit_runtime_smoke.py
    test_ui_common.py
    test_ui_smoke.py
    test_upload_landing.py
```

---

## 11) Important UX/Behavior Rules Implemented

- Protected nav targets should send logged-out users to auth.
- Post-login should return user to intended page.
- Theme should persist through route changes/logout/login.
- Header should stay visually fixed and not require internal nav scrolling.
- URL cleanup should reduce ugly query/hash noise and avoid jumpy reload positions.
- Home logo click should reliably return to homepage and clear volatile state.

---

## 12) Environment and Run Commands

Minimum `.env`:
- `GOOGLE_API_KEY=...`

Optional:
- OAuth credentials,
- SMTP credentials,
- session secret overrides.

Run:
```bash
py -m streamlit run app.py
```

Tests:
```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

---

## 13) Where to Edit for Future Changes

- Change menu links/order: `src/ui/layout.py`
- Change fixed header behavior: `src/ui/css_injection.py`
- Change theme palette/base styling: `src/css_generators.py`, `src/assets/ui/base_theme.css.tpl`
- Change auth gating/routing: `app.py`
- Change scoring logic: `src/scoring.py`, `src/scoring_constants.py`
- Change Gemini prompt/model behavior: `src/gemini_client.py`
- Change report cards: `src/ui/report.py`
- Change resume builder fields/layout: `src/ui/cv_builder_page.py`
- Change DB schema/models: `src/database.py`

---

## 14) Mental Model Summary (One Paragraph)

ExcelCV is a Streamlit app where `app.py` orchestrates routing/session/auth, UI modules render pages, analysis modules compute deterministic + AI-enhanced resume insights, and SQLAlchemy persists user/CV/analysis data. Styling is heavily customized through template-driven theme CSS plus JS/CSS injection for fixed header, URL cleanup, and cross-rerun behavior stability. The system is designed to keep resume analysis explainable, page navigation predictable, and account-based workflows (builder/history/reporting) practical for real use and demo presentation.

