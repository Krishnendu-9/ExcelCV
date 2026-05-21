# ExcelCV â€” GenAI-Powered CV Reviewer, Comparator & Resume Builder

ExcelCV is a full-stack AI-powered career tool built with Streamlit and Google Gemini.
It analyzes resumes against job descriptions with explainable ATS scoring, ranks multiple
candidates side-by-side, generates tailored cover letters, and includes a FlowCV-inspired
resume builder with live preview, cloud save, and PDF export.

---

## Features

### CV Analyzer
- Upload a resume (`PDF` or `DOCX`, max 2 MB) and paste a job description
- Gemini 2.0 Flash generates a structured JSON analysis merged with deterministic scoring
- **Explainable weighted score (0â€“100)** across five components:
  - Content quality, JD alignment, section structure, ATS essentials, contact completeness
- **JD Skill Matrix** â€” each required skill mapped to resume evidence (`Found / Partial / Missing`)
- **Rewrite Assistant** â€” section-level `Before â†’ After â†’ Why` guidance for stronger bullets
- **Recruiter Snapshot** â€” one-card hiring summary with key strength and key risk
- **Priority Action Plan** â€” ranked fix list with impact/effort guidance
- **Interview Prep** â€” targeted questions generated from strengths and skill gaps
- **Learning Roadmap** â€” skill-gap closure plan with short practical targets
- **Portfolio Checklist** â€” readiness check for sections, links, and contact info
- Download report as **PDF** or **JSON**
- Analyses are auto-saved per user; reviewable from **My Analyses**

### Multi-Resume Comparison
- Compare 2â€“5 resumes against the same job description
- Dedicated **Comparison Results** page (route: `compare-report`) â€” not rendered inline
- Ranked table with inline meter bars: Final Score, JD Alignment, ATS Parse, Sections, Issues
- **8 sort options** (Final/JD/ATS/Sections/Issues highâ†”low + Name Aâ†’Z) that re-number the rank column and flow through to CSV/PDF exports
- **Top Match card** + identity-based â˜… winner pill that stays on the true top match across sorts
- **Drill-down expander** per resume with summary, suggestions, missing keywords, and an **"Open as full report â†’"** button
- **CSV** + **ReportLab PDF** export of the ranked shortlist
- Auto-saved per user; revisit from **My Comparisons**
- Gemini quota short-circuit: if file N hits a 429, files N+1..end are marked `skipped (rate limit)` instead of burning more quota

### Cover Letter Generator
- Upload a resume + paste a job description; optionally add company name, role, source, and tone
- Gemini generates a tailored cover letter
- View on-screen as Markdown; **download as DOCX**
- Auth-gated like the other compute-intensive flows

### Evaluation Toolkit
- Add a human reviewer score per resume
- Tracks MAE, RMSE, and correlation between AI and human scores
- Export benchmark JSON for model quality assessment

### Resume Builder
- **Three-panel workspace** â€” left sections/templates/style controls, middle editable cards, right zoomable preview
- **Real-time preview** â€” Personal Details (name, contact) update in the preview as you type each character (no Enter needed), via a postMessage JS bridge
- **Three CV templates: Classic, Creative, Modern** â€” each with a distinct layout in both the live preview and the downloaded PDF (defined in [src/ui/cv_builder_constants.py](src/ui/cv_builder_constants.py))
- Sections: Personal, Summary, Education, Experience, Skills, Projects, Languages, Certifications, Interests â€” all collapsible, reorderable, individually hideable
- **AI Bullet Suggestions** â€” Gemini generates achievement bullets from job title + company, using existing bullets as context to avoid duplication
- Accent color picker, font selector, font size / line height / entry spacing controls (persisted with each saved CV)
- Save CVs to your account; load any saved CV back into the editor
- **One-click PDF download** â€” generates and downloads the PDF directly
- Manage saved CVs from **My CVs**

### Authentication & Accounts
- Email/password registration and sign-in (bcrypt, HMAC-signed session cookie)
- Google OAuth 2.0 sign-in
- Optional persistent login via `excelcv_session` cookie (opt-in with `ENABLE_PERSISTENT_LOGIN=1`)
- Forgot password / email-based reset link
- Settings page: change email, change password, delete account
- Protected pages redirect to auth gate and bounce back after login

### UI / UX
- Light / dark theme toggle with `localStorage` persistence
- Theme switch preserves all typed form data (no data loss on toggle)
- Responsive site header with branded logo, navigation, and user dropdown
- Professional footer (product, resources, legal columns)
- Full dark mode support across all pages

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / Server | Streamlit |
| AI | Google Gemini 2.0 Flash (`google-generativeai`) |
| Database | SQLite via SQLAlchemy ORM |
| Auth | bcrypt + HMAC-SHA256 signed cookies + Google OAuth 2.0 |
| PDF parsing | pypdf / PyPDF2, python-docx |
| PDF export | ReportLab |
| DOCX export | python-docx |
| Email | SMTP (optional, for password reset) |

---

## Project Structure

```text
cv-review/
â”œâ”€â”€ app.py                            # Main entry point â€” routing, auth gating, theme
â”œâ”€â”€ README.md
â”œâ”€â”€ CLAUDE.md                         # Dev status notes for Claude AI sessions
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ requirements-dev.txt
â”œâ”€â”€ pyproject.toml
â”œâ”€â”€ .env.example
â”œâ”€â”€ .pre-commit-config.yaml
â”œâ”€â”€ .streamlit/
â”‚   â””â”€â”€ config.toml                   # Upload cap, polling watcher, theme defaults
â”œâ”€â”€ .github/                          # CI workflows
â”œâ”€â”€ assets/
â”‚   â”œâ”€â”€ images/
â”‚   â”‚   â”œâ”€â”€ ExcelCV.png               # Logo (color)
â”‚   â”‚   â””â”€â”€ ExcelCV_clean.png         # Logo (clean variant)
â”‚   â””â”€â”€ FireShot Capture ... .pdf     # Reference design captures
â”œâ”€â”€ data/
â”‚   â””â”€â”€ excelcv.db                    # SQLite database (auto-created on first run)
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ excelcv.md                    # Source-of-truth project snapshot
â”‚   â”œâ”€â”€ SETUP.md                      # Full setup walkthrough
â”‚   â”œâ”€â”€ compareCV.md                  # Compare-flow reference
â”‚   â”œâ”€â”€ report_page.md                # Report-page reference
â”‚   â”œâ”€â”€ resume_builder.md             # Resume Builder reference
â”‚   â”œâ”€â”€ METRICS_DOCUMENTATION.md
â”‚   â”œâ”€â”€ PROJECT_REPORT.md
â”‚   â””â”€â”€ PRD_CV.txt
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ config.py                     # Env var loading, file-size limits
â”‚   â”œâ”€â”€ database.py                   # SQLAlchemy models: User, PasswordResetToken, CV, Analysis, Comparison
â”‚   â”œâ”€â”€ auth_utils.py                 # Session, cookies, bcrypt login/register
â”‚   â”œâ”€â”€ oauth_utils.py                # Google OAuth token exchange
â”‚   â”œâ”€â”€ gemini_client.py              # Gemini API: CV analysis, bullet suggestions
â”‚   â”œâ”€â”€ pdf_utils.py                  # PDF/DOCX text extraction
â”‚   â”œâ”€â”€ email_utils.py                # SMTP password reset email
â”‚   â”œâ”€â”€ assets/
â”‚   â”‚   â””â”€â”€ ui/
â”‚   â”‚       â””â”€â”€ base_theme.css.tpl    # Global CSS template
â”‚   â”œâ”€â”€ cover_letter/
â”‚   â”‚   â”œâ”€â”€ page.py                   # Streamlit page renderer
â”‚   â”‚   â”œâ”€â”€ service.py                # End-to-end pipeline
â”‚   â”‚   â”œâ”€â”€ generator.py              # Prompt construction + Gemini call
â”‚   â”‚   â”œâ”€â”€ models.py                 # CoverLetterResult dataclass
â”‚   â”‚   â”œâ”€â”€ validators.py             # Input validation
â”‚   â”‚   â””â”€â”€ docx_builder.py           # DOCX export
â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ scoring.py                # Deterministic ATS / content / tailoring scoring
â”‚   â”‚   â”œâ”€â”€ scoring_constants.py      # Score thresholds, weights
â”‚   â”‚   â”œâ”€â”€ evaluation.py             # Human-vs-AI evaluation metrics
â”‚   â”‚   â”œâ”€â”€ reporting.py              # PDF / JSON report generation
â”‚   â”‚   â”œâ”€â”€ pdf_generator.py          # CV PDF export (ReportLab) â€” template-specific layouts
â”‚   â”‚   â”œâ”€â”€ comparison_pdf.py         # Comparison PDF (ReportLab)
â”‚   â”‚   â””â”€â”€ career_tools.py           # Supporting career utility functions
â”‚   â””â”€â”€ ui/
â”‚       â”œâ”€â”€ app_utils.py              # APP_PAGES registry, URL helpers, snapshot store
â”‚       â”œâ”€â”€ layout.py                 # Site header, footer, theme toggle
â”‚       â”œâ”€â”€ theme.py                  # Theme CSS variable injection
â”‚       â”œâ”€â”€ css_injection.py          # Global CSS/JS (top bar, compact header, etc.)
â”‚       â”œâ”€â”€ css_generators.py         # Theme-aware CSS builders
â”‚       â”œâ”€â”€ ui_components.py          # Shared UI primitives
â”‚       â”œâ”€â”€ ui_constants.py           # UI-wide constants
â”‚       â”œâ”€â”€ common.py                 # Shared helpers (issue_count, score color class, â€¦)
â”‚       â”œâ”€â”€ auth_page.py              # Sign In / Register / Forgot Password / Reset
â”‚       â”œâ”€â”€ upload.py                 # Home + Analyze CV + Compare form
â”‚       â”œâ”€â”€ analysis_runner.py        # CV analysis pipeline + multi-resume comparison
â”‚       â”œâ”€â”€ report.py                 # Single-resume analysis report
â”‚       â”œâ”€â”€ compare_report.py         # Dedicated comparison-results page
â”‚       â”œâ”€â”€ cv_builder_page.py        # Resume Builder entry (form + live preview)
â”‚       â”œâ”€â”€ cv_builder_constants.py   # Template configs, zoom, section order
â”‚       â”œâ”€â”€ cv_builder_pdf.py         # Resume Builder PDF export
â”‚       â”œâ”€â”€ cv_builder_preview_data.py# Preview-data assembly
â”‚       â”œâ”€â”€ cv_builder_value_utils.py # Value normalization helpers
â”‚       â”œâ”€â”€ my_cvs_page.py            # Saved CVs management
â”‚       â”œâ”€â”€ my_analyses_page.py       # Analysis history
â”‚       â”œâ”€â”€ my_comparisons_page.py    # Comparison history
â”‚       â”œâ”€â”€ settings_page.py          # Account settings
â”‚       â””â”€â”€ static_pages.py           # Info/legal pages + cover-letter dispatch
â””â”€â”€ tests/
    â”œâ”€â”€ test_analysis_runner.py
    â”œâ”€â”€ test_auth_utils.py
    â”œâ”€â”€ test_compare_report_helpers.py
    â”œâ”€â”€ test_cover_letter_pipeline.py
    â”œâ”€â”€ test_oauth_utils.py
    â”œâ”€â”€ test_scoring_core.py
    â”œâ”€â”€ test_scoring_sections_order.py
    â””â”€â”€ test_upload_helpers.py
```

---

## Database Schema

```
users
  id (UUID PK) | email | hashed_password | full_name | google_id | created_at

password_reset_tokens
  id (UUID PK) | user_id (FK) | token_hash | expires_at | created_at

cvs                â† Resume Builder saves
  id (UUID PK) | user_id (FK) | title | template | data (JSON) | created_at | updated_at

analyses           â† auto-saved on every single-resume upload
  id (UUID PK) | user_id (FK) | cv_name | job_description | result (JSON) | match_score | created_at

comparisons        â† auto-saved on every successful multi-resume run
  id (UUID PK) | user_id (FK) | job_description | rows (JSON) | errors (JSON) | warnings (JSON)
              | resume_count | top_score | top_resume_name | created_at
```

---

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` (copy from `.env.example` and edit):
```env
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_MODEL=models/gemini-2.0-flash

SESSION_SECRET=your-long-random-secret
ENABLE_PERSISTENT_LOGIN=0

# Optional — auth throttling safety defaults
AUTH_LOGIN_WINDOW_SECONDS=600
AUTH_LOGIN_MAX_ATTEMPTS=5
AUTH_LOGIN_LOCK_SECONDS=900
AUTH_RESET_WINDOW_SECONDS=1800
AUTH_RESET_MAX_ATTEMPTS=3

# Optional — Gemini API guardrails
GEMINI_RATE_WINDOW_SECONDS=60
GEMINI_MAX_REQUESTS_PER_WINDOW=20
GEMINI_MAX_CV_CHARS=120000
GEMINI_MAX_JD_CHARS=40000
GEMINI_MAX_FILE_SIZE_BYTES=5242880
GEMINI_ANALYSIS_MAX_OUTPUT_TOKENS=2400

# Optional â€” needed for password reset email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@gmail.com
SMTP_ENCRYPTION=tls

# Optional â€” for Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501
```

3. Run:
```bash
streamlit run app.py
```

The SQLite database is created automatically at `data/excelcv.db` on first run (all 5 tables).

See [docs/SETUP.md](docs/SETUP.md) for the full setup walkthrough including OAuth and SMTP configuration.

---

## Testing

Run all unit tests:
```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

Current automated coverage includes auth/session paths, scoring logic, analysis runner behavior, cover-letter pipeline validation, and compare/upload helper logic across:
`test_analysis_runner.py`, `test_auth_utils.py`, `test_compare_report_helpers.py`, `test_cover_letter_pipeline.py`, `test_oauth_utils.py`, `test_scoring_core.py`, `test_scoring_sections_order.py`, and `test_upload_helpers.py`.

CI runs lint (`ruff`), compile checks, and unit tests on push/PR via the workflows in `.github/`.

---

## Analysis Workflow

### Single Resume
1. Go to **Analyze CV** â€” paste a job description.
2. Upload one resume (`PDF` or `DOCX`, max 2 MB).
3. Click **Upload & Analyze**.
4. Review the scored report: ATS breakdown, JD skill matrix, rewrite tips, interview prep, action plan.
5. Download as PDF or JSON; the analysis is auto-saved to **My Analyses**.

### Multi-Resume Comparison
1. Click **Compare Resumes** in the navigation (sign-in required).
2. Paste one job description, upload 2â€“5 resumes.
3. Click **Run comparison**.
4. The dedicated **Comparison Results** page opens with the ranked table, Top Match card, and per-resume drill-downs. Re-sort, download CSV/PDF, or open any resume as a full report.
5. The run is auto-saved; revisit from **My Comparisons**.

### Cover Letter
1. Click **Cover Letter** in the navigation (sign-in required).
2. Upload your resume, paste the job description, optionally fill in company / role / tone.
3. Generate, then download as DOCX.

### Resume Builder
1. Click **Resume Builder** in the navigation (sign-in required).
2. Choose a template (**Classic / Creative / Modern**) from the top bar.
3. Fill in Personal Details â€” the preview updates as you type.
4. Expand sections (Education, Experience, Skills, etc.) to add entries; reorder or hide sections from the left rail.
5. Click **Save** to store in your account; **Download PDF** to download instantly.

---

## Troubleshooting

- **Missing GOOGLE_API_KEY** â€” add it to `.env`.
- **DOCX support not installed** â€” run `pip install python-docx`.
- **DOCX contained no extractable text** â€” the file may contain image-based text; open in Word and ensure selectable text exists.
- **PDF export fails** â€” requires ReportLab (`pip install reportlab`). No system libraries needed.
- **Google OAuth not working** â€” ensure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` match what is configured in Google Cloud Console.
- **Gemini 429 / quota** â€” during multi-resume runs, remaining files are marked `skipped (rate limit)` so you can retry only the unfinished ones.

---

## Notes

This project is structured as an MCA final-year capstone demo:
- Explainable deterministic + AI scoring logic
- Measurable human-vs-AI evaluation toolkit
- Full authentication (email + OAuth)
- Cloud-ready architecture (Streamlit Community Cloud + SQLite)

For deeper references, see:
- [docs/excelcv.md](docs/excelcv.md) â€” current repository snapshot
- [docs/SETUP.md](docs/SETUP.md) â€” setup walkthrough
- [docs/compareCV.md](docs/compareCV.md) â€” multi-resume comparison reference
- [docs/report_page.md](docs/report_page.md) â€” analysis report reference
- [docs/resume_builder.md](docs/resume_builder.md) â€” Resume Builder reference
- [docs/METRICS_DOCUMENTATION.md](docs/METRICS_DOCUMENTATION.md) â€” metric calculation details
