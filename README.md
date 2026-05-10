# ExcelCV — GenAI-Powered CV Reviewer & Resume Builder

ExcelCV is a full-stack AI-powered career tool built with Streamlit and Google Gemini.
It analyzes resumes against job descriptions with explainable ATS scoring, and includes
a FlowCV-inspired resume builder with live preview, cloud save, and PDF export.

---

## Features

### CV Analyzer
- Upload a resume (`PDF` or `DOCX`, max 2 MB) and paste a job description
- Gemini 2.0 Flash generates a structured JSON analysis merged with deterministic scoring
- **Explainable weighted score (0–100)** across five components:
  - Content quality, JD alignment, section structure, ATS essentials, contact completeness
- **JD Skill Matrix** — each required skill mapped to resume evidence (`Found / Partial / Missing`)
- **Rewrite Assistant** — section-level `Before → After → Why` guidance for stronger bullets
- **Recruiter Snapshot** — one-card hiring summary with key strength and key risk
- **Priority Action Plan** — ranked fix list with impact/effort guidance
- **Interview Prep** — targeted questions generated from strengths and skill gaps
- **Learning Roadmap** — skill-gap closure plan with short practical targets
- **Portfolio Checklist** — readiness check for sections, links, and contact info
- Download report as Markdown or JSON
- Analyses are auto-saved per user; reviewable from **My Analyses**

### Multi-Resume Comparison
- Compare 2–5 resumes against the same job description
- Ranked table: final score, ATS parse rate, section score, issue count, top missing skills

### Evaluation Toolkit
- Add a human reviewer score per resume
- Tracks MAE, RMSE, and correlation between AI and human scores
- Export benchmark JSON for model quality assessment

### Resume Builder
- **FlowCV-inspired two-column layout** — edit on the left, live preview on the right
- **Real-time preview** — Personal Details (name, contact) update in the preview as you type each character (no Enter needed), using a postMessage JS bridge
- Three CV templates: **Classic**, **Modern**, **Minimal** — each with a distinct layout in both the live preview and the downloaded PDF
- Sections: Personal Details, Summary, Education, Professional Experience, Skills, Certificates, Projects — all collapsible
- **AI Bullet Suggestions** — Gemini generates achievement bullets from job title + company
- Accent color picker and font selector
- Save CVs to your account; load any saved CV back into the editor
- **One-click PDF download** — "Download PDF" button generates and downloads the PDF directly, no two-step flow
- PDF layout matches the selected template:
  - **Classic** — centered name in dark navy, centered contact row, thick horizontal rule
  - **Modern** — filled blue banner header with white name and light-blue contact text
  - **Minimal** — centered name in dark gray, centered contact row, light gray rule
- Manage saved CVs from **My CVs**

### Authentication & Accounts
- Email/password registration and sign-in (bcrypt, HMAC-signed session cookie)
- Google OAuth 2.0 sign-in
- Persistent login via `excelcv_session` cookie (3-day expiry)
- Forgot password / email-based reset link
- Settings page: change email, change password, delete account
- Protected pages redirect to auth gate and bounce back after login

### UI / UX
- Light / dark theme toggle with `localStorage` persistence
- Theme switch preserves all typed form data (no data loss on toggle)
- Responsive site header with branded logo, navigation, and user dropdown
- Professional footer (product, resources, legal columns)
- Full dark mode support across all CV builder inputs, preview, and section cards

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / Server | Streamlit |
| AI | Google Gemini 2.0 Flash (`google-generativeai`) |
| Database | SQLite via SQLAlchemy ORM |
| Auth | bcrypt + HMAC-SHA256 signed cookies + Google OAuth 2.0 |
| PDF parsing | PyPDF2, python-docx |
| PDF export | ReportLab |
| Email | SMTP (optional, for password reset) |

---

## Project Structure

```text
cv-review/
|-- app.py                         # Main entry point - routing, auth gating, theme
|-- requirements.txt
|-- CLAUDE.md                      # Dev status notes for Claude AI sessions
|-- docs/
|   `-- pages/
|       |-- README.md              # Static mockup index and page folder conventions
|       |-- auth/
|       |-- compare-cv/
|       |-- home-upload/
|       |-- my-analyses/
|       |-- my-cvs/
|       |-- resume-builder/
|       |-- resume-checker/
|       |   `-- resume_checker.html
|       |-- resume-report/
|       |   `-- resume_report_page.html
|       |-- settings/
|       `-- static-pages/
|-- data/
|   `-- excelcv.db                 # SQLite database (auto-created)
|-- templates/
|   `-- ExcelCV_clean.png          # Logo asset
|-- src/
|   |-- config.py                  # Env var loading
|   |-- database.py                # SQLAlchemy models: User, CV, Analysis, PasswordResetToken
|   |-- auth_utils.py              # Session, cookies, bcrypt login/register
|   |-- oauth_utils.py             # Google OAuth token exchange
|   |-- gemini_client.py           # Gemini API: CV analysis, bullet suggestions
|   |-- scoring.py                 # Deterministic ATS / content / tailoring scoring
|   |-- evaluation.py              # Human vs AI evaluation metrics
|   |-- pdf_utils.py               # PDF/DOCX text extraction
|   |-- reporting.py               # Markdown/JSON/PDF report generation
|   |-- email_utils.py             # SMTP password reset email
|   |-- career_tools.py            # Supporting career utility functions
|   |-- services/
|   |   `-- pdf_generator.py       # CV PDF export (ReportLab) - template-specific layouts
|   `-- ui/
|       |-- app_utils.py           # Page URL helpers, snapshot store, logo loader
|       |-- layout.py              # Site header, footer, theme toggle
|       |-- css_injection.py       # Global CSS/JS (top bar, compact header, etc.)
|       |-- theme.py               # Theme CSS variable injection
|       |-- auth_page.py           # Sign In / Register / Forgot Password / Reset
|       |-- upload.py              # Home + Analyze CV page
|       |-- analysis_runner.py     # CV analysis pipeline, multi-resume comparison
|       |-- report.py              # Full analysis report rendering
|       |-- cv_builder_page.py     # Resume Builder (form + live preview + PDF export)
|       |-- my_cvs_page.py         # Saved CVs management
|       |-- my_analyses_page.py    # Analysis history
|       |-- settings_page.py       # Account settings
|       |-- static_pages.py        # Info/legal pages
|       `-- common.py              # Shared UI helpers
`-- tests/
    |-- test_scoring.py
    |-- test_evaluation.py
    |-- test_reporting.py
    |-- test_career_tools.py
    |-- test_gemini_client_helpers.py
    |-- test_pdf_utils.py
    |-- test_app_helpers.py
    |-- test_ui_smoke.py
    `-- test_ui_common.py
```

---

## Database Schema

```
users
  id (UUID PK) | email | hashed_password | full_name | google_id | created_at

password_reset_tokens
  id (UUID PK) | user_id (FK) | token_hash | expires_at | created_at

cvs  ← Resume Builder saves
  id (UUID PK) | user_id (FK) | title | template | data (JSON) | created_at | updated_at

analyses  ← auto-saved on every upload
  id (UUID PK) | user_id (FK) | cv_name | job_description | result (JSON) | match_score | created_at
```

---

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env`:
```env
GOOGLE_API_KEY=your-gemini-api-key

# Optional — needed for password reset email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=you@gmail.com

# Optional — for signed session cookies (auto-generated if not set)
SESSION_SECRET=any-random-secret-string

# Optional — for Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501/
```

3. Run:
```bash
streamlit run app.py
```

The SQLite database is created automatically at `data/excelcv.db` on first run.

---

## Testing

Run all unit tests:
```bash
py -3 -m unittest discover -s tests -p "test_*.py" -q
```

Optional Streamlit smoke test:
```bash
$env:RUN_STREAMLIT_SMOKE = "1"
py -3 -m unittest tests.test_streamlit_runtime_smoke -q
```

---

## Analysis Workflow

### Single Resume
1. Go to **Analyze CV** — paste a job description.
2. Upload one resume (`PDF` or `DOCX`).
3. Click **Upload & Analyze**.
4. Review the scored report: ATS breakdown, JD skill matrix, rewrite tips, interview prep, action plan.

### Multi-Resume Comparison
1. Click **Compare** in the navigation.
2. Paste one job description, upload 2–5 resumes.
3. Click **Run Comparison** to see the ranked table.

### Resume Builder
1. Click **Resume Builder** in the navigation (sign-in required).
2. Choose a template (Classic / Modern / Minimal) from the top bar.
3. Fill in Personal Details — the preview updates as you type.
4. Expand sections (Education, Experience, Skills, etc.) to add entries.
5. Click **Save** to store in your account; **Download PDF** to download instantly.

---

## Troubleshooting

- **Missing GOOGLE_API_KEY** — add it to `.env`.
- **DOCX support not installed** — run `pip install python-docx`.
- **DOCX contained no extractable text** — the file may contain image-based text; open in Word and ensure selectable text exists.
- **PDF export fails** — requires ReportLab (`pip install reportlab`). No system libraries needed.
- **Google OAuth not working** — ensure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` match what is configured in Google Cloud Console.

---

## Notes

This project is structured as an MCA final-year capstone demo:
- Explainable deterministic + AI scoring logic
- Measurable human-vs-AI evaluation toolkit
- Full authentication (email + OAuth)
- Cloud-ready architecture (Streamlit Community Cloud + SQLite)