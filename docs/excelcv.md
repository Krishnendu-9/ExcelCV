# ExcelCV Project Guide (Current Repository Snapshot)

Last verified against the repository on **2026-05-18**.

This file is the source-of-truth summary of the project as it exists right now in this repo (folders, files, features, and known gaps).

---

## 1) What This Project Is

ExcelCV is a Streamlit application for:

1. Resume analysis against a job description (AI + deterministic ATS-style checks).
2. Multi-resume comparison (2 to 5 files) with a dedicated ranked-results page and per-user history.
3. Cover-letter generation tailored to a resume + job description.
4. Account system (email/password + optional Google OAuth).
5. Resume builder with live preview, PDF export, and saved CVs.
6. Saved analysis / comparison history and a benchmark/evaluation toolkit.

---

## 2) Current Runtime Entry and Architecture

- App entrypoint: `app.py`
- Main package: `src/`
- UI rendering modules: `src/ui/`
- Cover-letter feature package: `src/cover_letter/`
- Core services/business logic: `src/services/`
- Database layer: `src/database.py` (SQLite + SQLAlchemy)
- Local DB file path: `data/excelcv.db`

`app.py` is a routing/session orchestration layer. Most UI and feature logic lives in `src/ui/*`, `src/services/*`, and `src/cover_letter/*`.

---

## 3) Current Route/Page Map

### Main user flows
- `home` / `upload` / `upload-cv` → Analyze CV landing/upload page.
- `report` → single-resume analysis result page.
- `compare-cv` → multi-resume comparison form (anchored inside the upload page).
- `compare-report` → dedicated ranked-comparison results page (auth-gated).
- `cover-letter` → AI cover-letter generator page.
- `resume-builder` → resume builder.
- `my-cvs` → saved resumes.
- `my-analyses` → saved analysis history.
- `my-comparisons` → saved comparison history.
- `settings` → account settings.
- `auth` → sign in / register / forgot password / reset.

### Static/informational pages (rendered via `src/ui/static_pages.py`)
- `career-blog`
- `ats-insights`
- `instant-report`
- `evaluation-toolkit`
- `explainable-scoring`
- `project-notes`
- `how-it-works`
- `interview-prep`
- `resume-tips`
- `cover-letter-guide`
- `privacy-policy`
- `terms-of-service`
- `contact`

(`cover-letter` is also routed through `static_pages.py` but delegates to `render_cover_letter_page()` in [src/cover_letter/page.py](../src/cover_letter/page.py).)

Protected pages in current code (`PROTECTED_PAGES` in [app.py:53](../app.py)):
- `resume-builder`, `my-cvs`, `my-analyses`, `my-comparisons`, `compare-report`, `settings`

---

## 4) Feature Status (Implemented Now)

## 4.1 Single Resume Analysis
- Input: job description + one `.pdf` or `.docx` file.
- File size limit: 2 MB (`src/config.py` + `.streamlit/config.toml`).
- Flow: text extraction → Gemini response → deterministic scoring merge → report page.
- Auto-saved per user to the `analyses` table; reviewable from **My Analyses**.

Core files:
- `src/ui/upload.py`
- `src/ui/analysis_runner.py`
- `src/pdf_utils.py`
- `src/gemini_client.py`
- `src/services/scoring.py`

## 4.2 Multi-Resume Comparison
- Compare 2 to 5 resumes against one JD.
- Output columns: Final Score, JD Alignment, ATS Parse, Sections, Issues, Top Missing Skills.
- Dedicated `compare-report` page (not rendered inline below the form). Page features:
  - 8 sort options (Final/JD/ATS/Sections/Issues high↔low + Name A→Z); rank column re-numbers on sort.
  - Two-column outer card: Comparison Results table (left) + Top Match card (right).
  - Per-resume drill-down expanders with summary, suggestions, missing keywords, and an **Open as full report** button that snapshots into the single-CV report flow.
  - CSV and ReportLab PDF export of the ranked results.
  - Identity-based ★ winner pill that stays glued to the true top match across re-sorts.
- Auto-saved per user to the `comparisons` table after a successful run; reviewable from **My Comparisons**.
- Gemini quota short-circuit: if file N hits a 429, files N+1..end are marked `skipped (rate limit)`.

Core files:
- `src/ui/upload.py` (form + autosave hook)
- `src/ui/compare_report.py` (dedicated results page)
- `src/ui/my_comparisons_page.py` (history list)
- `src/ui/analysis_runner.py` (`run_multi_resume_comparison`)
- `src/services/comparison_pdf.py` (ReportLab compare PDF)

See [docs/compareCV.md](compareCV.md) for the full compare-flow reference.

## 4.3 Cover Letter Generator
- Inputs: a resume (PDF/DOCX, same 2 MB cap), the target job description, plus optional fields (company name, role, source of the opening, tone).
- Calls Gemini to produce a tailored cover letter; renders the result on-screen with a Markdown view and a Word/DOCX download.
- Auth-gated like the other compute-intensive flows.

Core files:
- `src/cover_letter/page.py` — Streamlit page renderer.
- `src/cover_letter/service.py` — orchestration (resume parse → prompt build → Gemini → result wrap).
- `src/cover_letter/generator.py` — prompt construction + Gemini call.
- `src/cover_letter/models.py` — `CoverLetterResult` dataclass.
- `src/cover_letter/validators.py` — input validation (file type/size, required fields).
- `src/cover_letter/docx_builder.py` — DOCX export.

## 4.4 Report Page
- Two-column report UI (sticky left score sidebar + right detail groups).
- Categories: Content, Sections, ATS Essentials, Insights.
- Score display: horizontal animated bar (was a circular ring earlier); colour tier green ≥ 80, amber ≥ 60, red < 60. Shared animation engine (`@keyframes hv-sweep` + `@property --hv-p`) with the homepage hero panel.
- Includes score breakdown card and a collapsed Model Evaluation Toolkit expander (MAE / RMSE / correlation vs human reviewer scores).
- Download options: PDF and JSON.

Core file: `src/ui/report.py`. See [docs/report_page.md](report_page.md) for the full reference.

## 4.5 Resume Builder
- Active page entry: `render_cv_builder_page()` in `src/ui/cv_builder_page.py`.
- 3-panel workspace: left sections/templates/style controls, middle editor cards, right preview with zoom.
- Save/load CVs to DB, import/export JSON, PDF download.
- Templates currently shipped (defined in `src/ui/cv_builder_constants.py` — `TEMPLATE_CONFIGS`): `classic`, `creative`, `modern`.
- Real-time preview for Personal Details fields via a postMessage JS bridge; other sections re-render on Streamlit's normal rerun.
- Backed by a recent refactor that split the original monolith into focused modules:
  - `cv_builder_page.py` — page composition + rendering.
  - `cv_builder_constants.py` — template configs, zoom levels, section ordering.
  - `cv_builder_pdf.py` — PDF export pipeline.
  - `cv_builder_preview_data.py` — preview-data assembly.
  - `cv_builder_value_utils.py` — value normalization helpers.

See [docs/resume_builder.md](resume_builder.md) for the full reference.

## 4.6 Auth and Accounts
- Email/password auth with bcrypt.
- HMAC signed session cookie (`excelcv_session`), restore-on-load logic (opt-in via `ENABLE_PERSISTENT_LOGIN`).
- Optional Google OAuth.
- Forgot/reset password token flow (requires SMTP env vars).
- Settings page supports email/password update and account deletion.

Core files:
- `src/auth_utils.py`
- `src/oauth_utils.py`
- `src/email_utils.py`
- `src/ui/auth_page.py`
- `src/ui/settings_page.py`

---

## 5) Current Scoring Model (As Implemented)

Deterministic metrics include:
- ATS Parse Rate
- Quantifying Impact
- Repetition
- Spelling & Grammar
- Bullets Consistency
- Sections completeness
- Sections order
- Contact completeness
- ATS essentials checks
- File-name quality
- Tailoring/JD alignment

Final weighted score logic (`calculate_final_score_breakdown` in `src/services/scoring.py`):

With JD (`mode="jd_aligned"`):
- Content Quality: 0.30
- JD Alignment: 0.25
- Sections: 0.15
- ATS Essentials: 0.15
- Contact Completeness: 0.15

Without JD (`mode="no_jd"`):
- Content Quality: 0.35
- Sections: 0.25
- ATS Essentials: 0.25
- Contact Completeness: 0.15

Content Quality is itself the unweighted mean of `[ats_parse_rate, quantifying_impact, repetition, spelling_grammar]`, plus `bullets_consistency` when present (4- or 5-way average).

---

## 6) Database Models (Current)

Defined in `src/database.py`:
- `User`
- `PasswordResetToken`
- `CV`
- `Analysis`
- `Comparison` *(persisted multi-resume comparison runs; full `rows` list including each row's stashed `_analysis` dict; survives logout, per-user)*

Engine:
- SQLite (`data/excelcv.db`)

Also includes:
- `_migrate()` for additive schema update (`google_id` column handling).

---

## 7) Current Repository Structure (Actual)

```text
cv-review/
  app.py
  README.md
  CLAUDE.md
  pyproject.toml
  requirements.txt
  requirements-dev.txt
  .env.example
  .pre-commit-config.yaml
  .streamlit/
    config.toml
  .github/
    (CI workflows)
  assets/
    images/
      ExcelCV.png
      ExcelCV_clean.png
    FireShot Capture 020 ... .pdf
    FireShot Capture 021 ... .pdf
  data/
    .gitkeep
    excelcv.db
  docs/
    excelcv.md
    SETUP.md
    resume_builder.md
    report_page.md
    compareCV.md
    METRICS_DOCUMENTATION.md
    PROJECT_REPORT.md
    PRD_CV.txt
    BRD/
      CV Reviewer BRD.xlsx
      CV Reviewer BRD (1).xlsx
      CV Reviewer BRD (2).xlsx
  src/
    __init__.py
    auth_utils.py
    config.py
    database.py
    email_utils.py
    gemini_client.py
    oauth_utils.py
    pdf_utils.py
    assets/
      ui/
        base_theme.css.tpl
    cover_letter/
      __init__.py
      docx_builder.py
      generator.py
      models.py
      page.py
      service.py
      validators.py
    services/
      __init__.py
      career_tools.py
      comparison_pdf.py
      evaluation.py
      pdf_generator.py
      reporting.py
      scoring.py
      scoring_constants.py
    ui/
      __init__.py
      analysis_runner.py
      app_utils.py
      auth_page.py
      common.py
      compare_report.py
      css_generators.py
      css_injection.py
      cv_builder_constants.py
      cv_builder_page.py
      cv_builder_pdf.py
      cv_builder_preview_data.py
      cv_builder_value_utils.py
      layout.py
      my_analyses_page.py
      my_comparisons_page.py
      my_cvs_page.py
      report.py
      settings_page.py
      static_pages.py
      theme.py
      ui_components.py
      ui_constants.py
      upload.py
  tests/
    __init__.py
    test_analysis_runner.py
    test_auth_utils.py
    test_compare_report_helpers.py
    test_cover_letter_pipeline.py
    test_oauth_utils.py
    test_scoring_core.py
    test_scoring_sections_order.py
    test_upload_helpers.py
```

---

## 8) Known Current-State Gaps / Cleanup Candidates

1. Test coverage improved (auth/session helpers, scoring core, analysis runner, cover-letter pipeline, compare/upload helper logic), but end-to-end UI coverage is still thin; many Streamlit flows are exercised manually.
2. Some static-page text (for example privacy wording) may not be fully aligned with the actual persisted account/data model.
3. `src/ui/cv_builder_page.py` is still large (~6.2k lines) even after the recent split into `cv_builder_constants.py` / `cv_builder_pdf.py` / `cv_builder_preview_data.py` / `cv_builder_value_utils.py`. Further extraction (preview HTML, per-section renderers) is possible.
4. Report-page snapshots are in-memory (`@st.cache_resource` dict in `app_utils.py`) — shareable `?rid=` links survive Streamlit reruns but **not** a server restart. Production would want DB-backed snapshots.
5. Comparison records are listed per-user on **My Comparisons** but have no shareable permalink yet.

---

## 9) Run and Setup (Current)

Install:
```bash
py -3 -m pip install -r requirements.txt
```

Run:
```bash
py -3 -m streamlit run app.py
```

Required env:
- `GOOGLE_API_KEY`

Optional env:
- `SESSION_SECRET`, `ENABLE_PERSISTENT_LOGIN`, `GEMINI_MODEL`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_ENCRYPTION`

See [docs/SETUP.md](SETUP.md) for the full setup walkthrough.

---

## 10) Key File Pointers

- Routing/session orchestration: `app.py`
- Page list / URL helpers: `src/ui/app_utils.py` (`APP_PAGES`, `_build_page_href`, snapshot store)
- Upload + compare form UX: `src/ui/upload.py`
- Comparison results page: `src/ui/compare_report.py`
- Saved comparisons list: `src/ui/my_comparisons_page.py`
- Single/multi analysis runners: `src/ui/analysis_runner.py`
- Gemini orchestration + merge: `src/gemini_client.py`
- Scoring engine: `src/services/scoring.py`
- Report rendering: `src/ui/report.py`
- Resume builder (entry): `src/ui/cv_builder_page.py`
- Cover-letter page: `src/cover_letter/page.py`
- Cover-letter pipeline: `src/cover_letter/service.py`, `generator.py`, `docx_builder.py`
- Auth/session/cookies: `src/auth_utils.py`
- ORM models/DB init: `src/database.py`
- Shared theme/style injection: `src/ui/theme.py`, `src/ui/css_injection.py`, `src/assets/ui/base_theme.css.tpl`

---

If you want, the next update can be a second pass that also aligns `README.md` and `docs/SETUP.md` with this same current-state snapshot.
