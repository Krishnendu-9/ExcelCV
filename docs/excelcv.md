# ExcelCV Project Guide (Current Repository Snapshot)

Last verified against the repository on **2026-05-11**.

This file is the source-of-truth summary of the project as it exists right now in this repo (folders, files, features, and known gaps).

---

## 1) What This Project Is

ExcelCV is a Streamlit application for:

1. Resume analysis against a job description (AI + deterministic ATS-style checks).
2. Multi-resume comparison (2 to 5 files).
3. Account system (email/password + optional Google OAuth).
4. Resume builder with live preview, PDF export, and saved CVs.
5. Saved analysis history and a benchmark/evaluation toolkit.

---

## 2) Current Runtime Entry and Architecture

- App entrypoint: `app.py`
- Main package: `src/`
- UI rendering modules: `src/ui/`
- Core services/business logic: `src/services/`
- Database layer: `src/database.py` (SQLite + SQLAlchemy)
- Local DB file path: `data/excelcv.db`

`app.py` is a routing/session orchestration layer. Most UI and feature logic lives in `src/ui/*` and `src/services/*`.

---

## 3) Current Route/Page Map

### Main user flows
- `home` / `upload` / `upload-cv` -> Analyze CV landing/upload page.
- `report` -> analysis result page.
- `cv-builder` (alias `resume-builder`) -> resume builder.
- `my-cvs` -> saved resumes.
- `my-analyses` -> saved analysis history.
- `compare-cv` -> comparison mode (auth-gated).
- `settings` -> account settings.
- `auth` -> sign in/register/forgot/reset.

### Static/informational pages (rendered via `src/ui/static_pages.py`)
- `career-blog`
- `motivation-letter`
- `ats-insights`
- `instant-report`
- `evaluation-toolkit`
- `explainable-scoring`
- `project-notes`
- `how-it-works`
- `interview-prep`
- `privacy-policy`
- `terms-of-service`
- `contact`

Protected pages in current code:
- `cv-builder`, `resume-builder`, `my-cvs`, `my-analyses`, `compare-cv`, `settings`

---

## 4) Feature Status (Implemented Now)

## 4.1 Single Resume Analysis
- Input: job description + one `.pdf` or `.docx` file.
- File size limit: 2 MB (`src/config.py` + `.streamlit/config.toml`).
- Flow: text extraction -> Gemini response -> deterministic scoring merge -> report page.

Core files:
- `src/ui/upload.py`
- `src/ui/analysis_runner.py`
- `src/pdf_utils.py`
- `src/gemini_client.py`
- `src/services/scoring.py`

## 4.2 Multi-Resume Comparison
- Compare 2 to 5 resumes against one JD.
- Output includes: Final Score, JD Alignment, ATS Parse, Sections, Issues, Top Missing Skills.
- Sorted by final score descending.

Core file:
- `src/ui/analysis_runner.py` (`run_multi_resume_comparison`)

## 4.3 Report Page
- Two-column report UI (sticky left score sidebar + right detail groups).
- Categories: Content, Sections, ATS Essentials, Insights.
- Includes score breakdown card and model evaluation toolkit expander.
- Download options: PDF and JSON.

Core file:
- `src/ui/report.py`

## 4.4 Resume Builder
- Active page entry: `render_cv_builder_page()` in `src/ui/cv_builder_page.py`.
- 3-panel workspace: left controls, middle editor, right preview.
- Save/load CVs to DB, import/export JSON, PDF download.
- Templates currently normalized/used in code: `classic`, `creative`, `modern`.

Important current-state note:
- `src/ui/cv_builder_page.py` is very large and contains repeated/legacy duplicate function definitions.
- Python uses the last definition at runtime. This is functional but technical debt.

## 4.5 Auth and Accounts
- Email/password auth with bcrypt.
- HMAC signed session cookie (`excelcv_session`), restore-on-load logic.
- Optional Google OAuth.
- Forgot/reset password token flow.
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

With JD:
- Content Quality: 0.30
- JD Alignment: 0.25
- Sections: 0.15
- ATS Essentials: 0.15
- Contact Completeness: 0.15

Without JD:
- Content Quality: 0.35
- Sections: 0.25
- ATS Essentials: 0.25
- Contact Completeness: 0.15

---

## 6) Database Models (Current)

Defined in `src/database.py`:
- `User`
- `PasswordResetToken`
- `CV`
- `Analysis`

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
  .streamlit/
    config.toml
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
    tmp_write_test_agent2.txt
    assets/
      ui/
        base_theme.css.tpl
        base_theme.js.tpl
    services/
      __init__.py
      career_tools.py
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
      css_generators.py
      css_injection.py
      cv_builder_page.py
      layout.py
      my_analyses_page.py
      my_cvs_page.py
      report.py
      settings_page.py
      static_pages.py
      theme.py
      ui_components.py
      ui_constants.py
      upload.py
  tmp/
    fireshot008_extract/
      p000_000.jpg
      p000_001.jpg
      p000_002.jpg
      p000_003.jpg
  tmp_write_check.txt
```

---

## 8) Known Current-State Gaps / Cleanup Candidates

1. No `tests/` directory is present right now, while some docs still mention test commands.
2. `README.md` and some docs still reference older structure/behavior not fully aligned with current files.
3. Temporary artifacts currently exist in repo/workspace:
   - `tmp_write_check.txt`
   - `src/tmp_write_test_agent2.txt`
4. `src/ui/cv_builder_page.py` is monolithic and contains legacy duplicate definitions.
5. Some static-page text (for example privacy wording) is not fully aligned with the actual persisted account/data model.

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
- `SESSION_SECRET`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_ENCRYPTION`

---

## 10) Key File Pointers

- Routing/session orchestration: `app.py`
- Upload + compare UX: `src/ui/upload.py`
- Single/multi analysis runners: `src/ui/analysis_runner.py`
- Gemini orchestration + merge: `src/gemini_client.py`
- Scoring engine: `src/services/scoring.py`
- Report rendering: `src/ui/report.py`
- Resume builder: `src/ui/cv_builder_page.py`
- Auth/session/cookies: `src/auth_utils.py`
- ORM models/DB init: `src/database.py`
- Shared theme/style injection: `src/ui/theme.py`, `src/ui/css_injection.py`, `src/assets/ui/base_theme.css.tpl`

---

If you want, the next update can be a second pass that also aligns `README.md` and `docs/SETUP.md` with this same current-state snapshot.
