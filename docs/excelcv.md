# ExcelCV Project Guide

A snapshot of the repository at commit `7010703`, checked against the code on **2026-11-07**.
It describes the project as it stood then and is not updated automatically. Statements marked
*not re-checked* were carried over without verification.

[tests/test_project_guide.py](../tests/test_project_guide.py) re-checks part of this file on
every test run: every path it names exists, the layout in section 7 lists every directory and
the files it says it lists in full, the route map and protected pages match the code, the
final-score weights match `calculate_final_score_breakdown()`, the database models match
`src/database.py`, the required settings match `docs/SETUP.md`, and every function and
constant it names exists. The feature descriptions in section 4 and the gaps in section 8 are
prose and nothing checks them.

---

## 1) What This Project Is

ExcelCV is a Streamlit application for:

1. Resume analysis against a job description. Every score is computed in code; Google Gemini
   supplies three subscores for the downloadable reports and sets no score on the report page.
2. Multi-resume comparison (2 to 5 files) with a dedicated ranked-results page and per-user history.
3. Cover-letter generation tailored to a resume and a target role.
4. An account system (email/password, plus optional Google OAuth).
5. A resume builder with live preview, PDF export and saved CVs.
6. Saved analysis and comparison history, and a benchmark/evaluation toolkit.

---

## 2) Runtime Entry and Architecture

- App entry point: `app.py`
- Main package: `src/`
- UI rendering modules: `src/ui/`
- Cover-letter feature package: `src/cover_letter/`
- Core services and business logic: `src/services/`
- Database layer: `src/database.py` (SQLite + SQLAlchemy)
- Local database file: `data/excelcv.db`

`app.py` is a routing and session orchestration layer. Most UI and feature logic lives in
`src/ui/`, `src/services/` and `src/cover_letter/`.

---

## 3) Route Map

Every page key is registered in `APP_PAGES` in `src/ui/app_utils.py`. `app.py` dispatches the
main flows and the guide articles itself and hands every other key to `render_static_page()`
in `src/ui/static_pages.py`.

### Main user flows
- `home` / `upload` / `upload-cv` → Analyze CV landing and upload page.
- `report` → single-resume analysis result page.
- `compare-cv` → redirects to `home` and scrolls to the comparison form on that page.
- `compare-report` → dedicated ranked-comparison results page.
- `cover-letter` → cover-letter generator. Routed through `src/ui/static_pages.py`, which
  calls `render_cover_letter_page()` in `src/cover_letter/page.py`.
- `resume-builder` → resume builder.
- `my-cvs` → saved resumes.
- `my-analyses` → saved analysis history.
- `my-comparisons` → saved comparison history.
- `settings` → account settings.
- `auth` → sign in / register / forgot password / reset.

### Informational pages (`src/ui/static_pages.py`)
- `career-blog`
- `ats-insights`
- `instant-report`
- `evaluation-toolkit`
- `explainable-scoring`
- `project-notes`
- `how-it-works`
- `interview-prep`
- `contact`
- `resume-tips`, `cover-letter-guide`, `privacy-policy`, `terms-of-service`: the same module
  passes these to `render_resume_tips_pillar()`, `render_cover_letter_guide()`,
  `render_privacy_policy()` and `render_terms_of_service()` in `src/ui/guides.py`.

### Guide articles (`src/ui/guides.py`)
Each key of `GUIDES_META` is a page, rendered by `render_guide_article()` from the Markdown
file of the same name in `docs/guides/`.
- `why-75-rejected`
- `pass-ats-scanner-2026`
- `pdf-vs-docx`
- `ats-friendly-templates`
- `keywords-software-engineers`
- `resume-no-experience`
- `ai-hiring-tools-2026`

### Protected pages
Guests who open one of these are sent to sign in. The set is `PROTECTED_PAGES`, defined near
the top of `app.py` (search for `PROTECTED_PAGES =`):
- `resume-builder`, `my-cvs`, `my-analyses`, `my-comparisons`, `compare-report`, `settings`

Analyze CV, Compare Resumes and Cover Letter are not in that set. Each of those pages shows
guests a sign-in prompt in place of its form instead; see
[KNOWN_ISSUES.md §4](KNOWN_ISSUES.md#4-sign-in-checks-for-ai-features-live-in-the-ui-layer).

---

## 4) Feature Status

## 4.1 Single Resume Analysis
- Requires sign-in. Input: a job description (required) and one `.pdf` or `.docx` file.
- File size limit: 2 MB (`MAX_FILE_MB` in `src/config.py`, and `maxUploadSize` in
  `.streamlit/config.toml`).
- Flow: text extraction → Gemini call (only its three subscores are kept; untrusted CV and
  job-description text is fenced by `src/prompt_fence.py`) → every score computed in code →
  report page.
- Auto-saved per user to the `analyses` table; reviewable from **My Analyses**.

Core files:
- `src/ui/upload.py`
- `src/ui/analysis_runner.py`
- `src/pdf_utils.py`
- `src/gemini_client.py`
- `src/services/scoring.py`

## 4.2 Multi-Resume Comparison
- Requires sign-in. Compares 2 to 5 resumes against one job description.
- On-page results table: Rank, Resume, Final, JD Align, ATS Parse, Sections, Issues. Top
  Missing Skills is left out of the table on purpose (it truncated mid-word); it appears in
  the Top Match card, the drill-downs and the CSV export.
- Dedicated `compare-report` page (not rendered inline below the form). Page features:
  - 8 sort options: Final Score high→low and low→high, JD Alignment / ATS Parse / Sections
    high→low, Issues low→high and high→low, Resume name A→Z. The rank column re-numbers on sort.
  - Two-column outer card: Comparison Results table (left) and Top Match card (right).
  - Per-resume drill-down expanders with summary, suggestions, missing keywords, and an
    **Open as full report** button that snapshots into the single-CV report flow.
  - CSV and ReportLab PDF export of the ranked results.
  - A ★ winner marker that stays on the true top match across re-sorts.
- Auto-saved per user to the `comparisons` table after a successful run; reviewable from
  **My Comparisons**.
- Gemini quota short-circuit: if file N hits a rate limit, files N+1..end are shown as
  `skipped (rate limit)`.

Core files:
- `src/ui/upload.py` (form and autosave hook)
- `src/ui/compare_report.py` (dedicated results page)
- `src/ui/my_comparisons_page.py` (history list)
- `src/ui/analysis_runner.py` (`run_multi_resume_comparison()`)
- `src/services/comparison_pdf.py` (ReportLab comparison PDF)

See [docs/compareCV.md](compareCV.md) for the full compare-flow reference.

## 4.3 Cover Letter Generator
- Requires sign-in. Required: a resume (upload a PDF/DOCX under the same 2 MB cap, or pick a
  saved CV), the job title and the company name.
- Optional: the job description, how the opening was found, and free-text additional
  information (achievements, projects or tone notes). There is no separate tone control.
- Calls Gemini to draft the letter; shows it as a read-only plain-text preview with a
  Word/DOCX download.

Core files:
- `src/cover_letter/page.py` — Streamlit page renderer.
- `src/cover_letter/service.py` — orchestration (resume parse → prompt build → Gemini → result).
- `src/cover_letter/generator.py` — prompt construction and the Gemini call.
- `src/cover_letter/models.py` — `CoverLetterResult` dataclass.
- `src/cover_letter/validators.py` — input validation (required fields, file type, length caps).
- `src/cover_letter/docx_builder.py` — DOCX export.

## 4.4 Report Page
- Two-column report UI: sticky score sidebar on the left, detail groups on the right.
- Categories: Content, Sections, ATS Essentials, Insights.
- Score display: horizontal animated bar; colour tier green ≥ 80, amber ≥ 60, red < 60. The
  animation (`@keyframes hv-sweep` and `@property --hv-p`) is shared with the homepage hero panel.
- Includes a "How this score is calculated" breakdown card and a collapsed
  "Benchmark against human reviewers" expander (MAE / RMSE / correlation between the
  computed score and human reviewer scores; records last for the session, with a JSON
  download and no import).
- Download options: PDF, Markdown and JSON.

Core file: `src/ui/report.py`. See [docs/report_page.md](report_page.md) for the full reference.

## 4.5 Resume Builder
- Page entry: `render_cv_builder_page()` in `src/ui/cv_builder_page.py`.
- 3-panel workspace: sections, templates and style controls on the left, editor cards in the
  middle, preview with zoom on the right.
- Save/load CVs to the database, import/export JSON, PDF download (headless Chromium via
  Playwright).
- Templates shipped (`TEMPLATE_CONFIGS` in `src/ui/cv_builder_constants.py`): `classic`,
  `modern`, `creative`.
- Real-time preview via a postMessage JS bridge: the name, title and contact details update
  in the template as you type. Every other field, the summary included, shows as a plain
  "Label: value" line while you type, and the formatted sections return on Streamlit's
  normal rerun.
- Split across focused modules:
  - `src/ui/cv_builder_page.py` — page composition and rendering.
  - `src/ui/cv_builder_constants.py` — template configs, zoom levels, section ordering.
  - `src/ui/cv_builder_pdf.py` — PDF export pipeline.
  - `src/ui/cv_builder_preview_data.py` — preview-data assembly.
  - `src/ui/cv_builder_value_utils.py` — value normalisation helpers.

See [docs/resume_builder.md](resume_builder.md) for the full reference.

## 4.6 Auth and Accounts
- Email/password auth with bcrypt.
- HMAC-signed session cookie (`excelcv_session`); restore-on-load is opt-in via
  `ENABLE_PERSISTENT_LOGIN`.
- Optional Google OAuth.
- Forgot/reset password token flow (requires the SMTP settings).
- Settings page supports email and password changes and account deletion.

Core files:
- `src/auth_utils.py`
- `src/oauth_utils.py`
- `src/email_utils.py`
- `src/ui/auth_page.py`
- `src/ui/settings_page.py`

---

## 5) Scoring Model

Eleven metrics, each computed in `src/services/scoring.py`:
- ATS Parse Rate — `calculate_ats_parse_rate()`
- Quantifying Impact — `calculate_quantifying_impact()`
- Repetition — `calculate_repetition()`
- Spelling & Grammar — `calculate_spelling_grammar()`
- Bullets Consistency — `calculate_bullets_consistency()`
- Sections completeness — `calculate_sections()`
- Sections order — `calculate_sections_order()`
- Contact completeness — `calculate_contact_info()`
- ATS Essentials checks — `calculate_ats_essentials()`
- File-name quality — `calculate_file_name_quality()`
- Tailoring / JD alignment — `calculate_tailoring()`

Final weighted score (`calculate_final_score_breakdown()` in `src/services/scoring.py`):

With a job description (`mode="jd_aligned"`):
- Content Quality: 0.30
- JD Alignment: 0.25
- Sections: 0.15
- ATS Essentials: 0.15
- Contact Completeness: 0.15

Without a job description (`mode="no_jd"`):
- Content Quality: 0.35
- Sections: 0.25
- ATS Essentials: 0.25
- Contact Completeness: 0.15

Content Quality is the unweighted mean of ATS Parse Rate, Quantifying Impact, Repetition and
Spelling & Grammar, plus Bullets Consistency when present (a 4- or 5-way average). See
[docs/METRICS_DOCUMENTATION.md](METRICS_DOCUMENTATION.md) for every metric's rules.

---

## 6) Database Models

Defined in `src/database.py`:
- `User`
- `PasswordResetToken`
- `CV`
- `Analysis`
- `Comparison` — a persisted multi-resume comparison run: the full `rows` list, including each
  row's stashed `_analysis` dict, plus its errors and warnings.

Engine: SQLite at `data/excelcv.db`, created on first run (the file is gitignored).

`_migrate()` applies the one additive schema change `create_all` cannot: adding the
`google_id` column to existing `users` tables.

---

## 7) Repository Layout

An orientation, not a file listing: run `git ls-files` for every file. Each line names a
directory and what lives there. Where a line says it lists a directory's files in full, it
does, and the guard test fails when a file is added there without a line here. Elsewhere only
the main files are named.

### Root (all files)
- `app.py` — entry point: page routing, session handling, the sign-in gate, theme.
- `README.md` — project overview.
- `requirements.txt` / `requirements-dev.txt` — runtime and development dependencies.
- `pyproject.toml` — ruff and mypy configuration.
- `.env.example` — documents the settings; the app never reads it (see `docs/SETUP.md`).
- `.pre-commit-config.yaml` — pre-commit hooks (whitespace fixers, ruff, ruff-format).
- `.gitattributes`, `.gitignore`.

### Directories
- `.github/` — `.github/workflows/ci.yml` (ruff, mypy, pip-audit, compile check, unit tests)
  and `.github/pip-audit-ignore.txt` (reviewed advisory ignores, read in CI by
  `scripts/pip_audit_ignores.py`). The `.github/workflows/` directory holds only that workflow.
- `.streamlit/` — `.streamlit/config.toml` (upload cap, theme, server settings).
- `assets/` — `assets/images/` holds the logo PNGs used by the header and sign-in page; the
  two FireShot PDFs at the top of `assets/` are saved captures of a third-party resume
  checker's page.
- `data/` — the SQLite database `data/excelcv.db` (created on first run, gitignored) and
  `data/.gitkeep`.
- `docs/` — this guide, `docs/SETUP.md`, `docs/KNOWN_ISSUES.md`,
  `docs/METRICS_DOCUMENTATION.md`, the feature references (`docs/report_page.md`,
  `docs/compareCV.md`, `docs/resume_builder.md`), the original build plan
  `docs/PRD_CV.txt`, a requirements spreadsheet in `docs/BRD/`, and `docs/guides/`, which
  holds one Markdown file per guide article (section 3).
- `scripts/` (all files) — `scripts/generate_minor_report.py` and
  `scripts/generate_changes_report.py` write the project reports as `.docx` into
  `docs/submission/`; `scripts/pip_audit_ignores.py` parses the pip-audit ignore list for CI.
- `src/` (all top-level modules):
  - `src/config.py` — `.env` loading, settings, the `SESSION_SECRET` guard, `MAX_FILE_MB`.
  - `src/auth_utils.py` — password hashing, login/logout, session cookies.
  - `src/oauth_utils.py` — Google OAuth state and token exchange.
  - `src/email_utils.py` — password-reset and contact-form email (SMTP).
  - `src/database.py` — SQLAlchemy engine and models.
  - `src/gemini_client.py` — Gemini calls, response parsing, and assembly of the `analysis` dict.
  - `src/prompt_fence.py` — fences untrusted CV and job-description text inside prompts.
  - `src/pdf_utils.py` — PDF (pypdf) and DOCX text extraction.
- `src/services/` (all files) — business logic:
  - `src/services/scoring.py` and `src/services/scoring_constants.py` — every metric and the
    final score.
  - `src/services/reporting.py` — the downloadable PDF and Markdown analysis reports.
  - `src/services/comparison_pdf.py` — the comparison PDF.
  - `src/services/pdf_generator.py` — saved-CV PDF export (ReportLab).
  - `src/services/evaluation.py` — MAE / RMSE / correlation for the evaluation toolkit.
  - `src/services/career_tools.py` — the report enrichments (most are dormant; see
    [KNOWN_ISSUES.md §6](KNOWN_ISSUES.md#6-dormant-report-enrichments-that-are-built-but-not-shown)).
- `src/cover_letter/` (all files) — the cover-letter feature; section 4.3 describes each module.
- `src/ui/` — every page renderer and its styling. Main modules: `src/ui/upload.py`,
  `src/ui/report.py`, `src/ui/compare_report.py`, `src/ui/cv_builder_page.py`,
  `src/ui/guides.py`, `src/ui/static_pages.py`, `src/ui/auth_page.py`,
  `src/ui/settings_page.py`, `src/ui/analysis_runner.py` and `src/ui/app_utils.py`. The
  My CVs / My Analyses / My Comparisons pages share `src/ui/list_pages.py`; theming is in
  `src/ui/theme.py`, `src/ui/css_injection.py` and `src/ui/css_generators.py`.
- `src/assets/` — `src/assets/ui/base_theme.css.tpl` (the theme stylesheet template),
  `src/assets/images/` (the cover-letter page image) and `src/assets/icons/` (SVG contact
  icons that no Python module currently reads).
- `tests/` — the `unittest` suite, plus `tests/repo_files.py`, a helper for tests that check
  committed files. Several tests guard documentation against the code, this file included.

---

## 8) Known Gaps and Cleanup Candidates

Tracked defects and dormant features are recorded in [docs/KNOWN_ISSUES.md](KNOWN_ISSUES.md),
and test-coverage gaps in [docs/SETUP.md §8](SETUP.md#8-whats-not-set-up-yet). Not recorded
elsewhere:

1. `src/ui/cv_builder_page.py` is the largest module in the repository by far, even after the
   split listed in section 4.5. Further extraction (preview HTML, per-section renderers) is
   possible.
2. Report-page snapshots live in memory (`_report_snapshot_store()` in `src/ui/app_utils.py`, an
   `@st.cache_resource` dict). Shareable `?rid=` links survive Streamlit reruns but not a server
   restart. Production would want database-backed snapshots.
3. Saved comparisons are listed per user on **My Comparisons**, but opening one loads it into
   the session; there is no shareable permalink.
4. *Not re-checked:* some static-page text (for example the privacy wording) may not be fully
   aligned with the data the app actually stores.

---

## 9) Run and Setup

```bash
py -3 -m pip install -r requirements.txt
py -3 -m playwright install chromium
py -3 -m streamlit run app.py
```

Required settings (in `.env`):
- `GOOGLE_API_KEY`
- `SESSION_SECRET`

The app refuses to start without a valid `SESSION_SECRET`. Every optional setting (OAuth,
SMTP, persistent login, Gemini limits, login throttling) is documented in
[docs/SETUP.md](SETUP.md), which is the reference for setup.

---

## 10) Key File Pointers

- Routing and session orchestration: `app.py`
- Page list and URL helpers: `src/ui/app_utils.py` (`APP_PAGES`, `_build_page_href()`, the
  report snapshot store)
- Upload and compare form: `src/ui/upload.py`
- Comparison results page: `src/ui/compare_report.py`
- Saved comparisons list: `src/ui/my_comparisons_page.py`
- Single and multi analysis runners: `src/ui/analysis_runner.py`
- Gemini orchestration and analysis assembly: `src/gemini_client.py`
- Prompt-injection fencing: `src/prompt_fence.py`
- Scoring engine: `src/services/scoring.py`
- Report rendering: `src/ui/report.py`
- Resume builder (entry): `src/ui/cv_builder_page.py`
- Guide articles, Resume Tips, privacy and terms pages: `src/ui/guides.py`
- Cover-letter page: `src/cover_letter/page.py`
- Cover-letter pipeline: `src/cover_letter/service.py`, `src/cover_letter/generator.py`,
  `src/cover_letter/docx_builder.py`
- Auth, sessions and cookies: `src/auth_utils.py`
- ORM models and database init: `src/database.py`
- Theme and style injection: `src/ui/theme.py`, `src/ui/css_injection.py`,
  `src/assets/ui/base_theme.css.tpl`
