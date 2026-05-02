# ExcelCV — System Architecture

## High-Level Flow

```
Browser (User)
    │
    │  HTTP  (Streamlit WebSocket)
    ▼
┌─────────────────────────────────────────────────────────┐
│                    app.py  (Entry Point)                 │
│   • Page routing  • Session management  • Auth guards   │
│   • OAuth callback handling  • Cookie-based login       │
└───────────┬───────────────────────────────┬─────────────┘
            │                               │
     ┌──────▼──────┐                 ┌──────▼──────┐
     │  src/ui/*   │                 │  src/*.py   │
     │  (Rendering)│                 │  (Services) │
     └──────┬──────┘                 └──────┬──────┘
            │                               │
  ┌─────────┼──────────┐         ┌──────────┼───────────┐
  │         │          │         │          │           │
  ▼         ▼          ▼         ▼          ▼           ▼
layout   upload     report   gemini_   scoring.py  auth_utils
.py      .py        .py      client.py             .py
  │         │          │         │                    │
  │         │          │         │                    │
  ▼         ▼          ▼         ▼                    ▼
css_      analysis_  static_ pdf_utils           database.py
injection runner.py  pages.py .py                (SQLAlchemy)
.py                                                   │
                                                      ▼
                                               data/excelcv.db
                                               (SQLite)
```

## Module Responsibilities

| Module | Lines | Responsibility |
|---|---|---|
| `app.py` | ~350 | Routing, session orchestration, OAuth/cookie handling |
| `src/ui/layout.py` | ~180 | Site header, footer, theme toggle |
| `src/ui/upload.py` | ~460 | Upload page, compare page, file handling UI |
| `src/ui/report.py` | ~1800 | Full report rendering, evaluation toolkit |
| `src/ui/css_injection.py` | ~1380 | All CSS/JS injection (header bar, form spacing, top-bar) |
| `src/ui/analysis_runner.py` | ~175 | CV analysis pipeline, multi-resume comparison, DB auto-save |
| `src/ui/app_utils.py` | ~170 | Page URL helpers, state helpers, report snapshot store |
| `src/ui/static_pages.py` | ~290 | Info pages (blog, privacy, contact, how-it-works) |
| `src/ui/auth_page.py` | ~770 | Sign in, create account, forgot password, reset password |
| `src/ui/cv_builder_page.py` | — | Resume builder form and PDF export |
| `src/ui/my_cvs_page.py` | — | Saved CVs list with load/delete |
| `src/ui/my_analyses_page.py` | — | Analysis history with scores |
| `src/gemini_client.py` | — | Gemini API orchestration + JSON response parsing |
| `src/scoring.py` | — | Deterministic ATS/content/tailoring scoring |
| `src/auth_utils.py` | — | bcrypt login, HMAC session tokens, cookie restore |
| `src/database.py` | — | SQLAlchemy ORM (User, CV, Analysis, PasswordResetToken) |
| `src/email_utils.py` | — | SMTP password reset email |
| `src/oauth_utils.py` | — | Google OAuth 2.0 token exchange |
| `src/reporting.py` | — | Markdown/JSON/PDF report export |

## Authentication Flow

```
User submits form
       │
       ├─► Sign In ──► authenticate_user() ──► bcrypt verify
       │                       │
       ├─► Register ──► create_user() ──► bcrypt hash + DB insert
       │                       │
       └─► Google OAuth ──► exchange_code_for_userinfo()
                                │
                    ┌───────────▼────────────┐
                    │  create_session_token() │
                    │  HMAC-SHA256 signed     │
                    │  3-day expiry           │
                    └───────────┬────────────┘
                                │
                    Set cookie: excelcv_session
                    (via injected <script>)
                                │
                    On next load: restore_session_from_cookie()
                    reads Cookie header → validate_session_token()
```

## Analysis Pipeline

```
User uploads PDF/DOCX + pastes Job Description
            │
            ▼
    extract_cv_text()          ← src/pdf_utils.py
    (PyPDF2 / python-docx)
            │
            ▼
    analyze_cv_with_gemini()   ← src/gemini_client.py
    ┌───────┴────────────────────────────────────┐
    │  Gemini 2.0 Flash (JSON-mode response)     │
    │  + Deterministic scoring merge             │
    │    ├─ scoring.py  (ATS, content, tailoring)│
    │    └─ Weighted final score (0-100)         │
    └───────┬────────────────────────────────────┘
            │
            ▼
    Analysis dict stored in st.session_state
    + saved to Analysis table (logged-in users)
            │
            ▼
    render_report_view()       ← src/ui/report.py
    (Score breakdown, JD matrix, rewrite tips,
     interview prep, learning roadmap, downloads)
```

## Database Schema

```
users
  id (UUID PK) | email | hashed_password | full_name | google_id | created_at

password_reset_tokens
  id (UUID PK) | user_id (FK) | token_hash | expires_at | created_at

cvs  (CV Builder saves)
  id (UUID PK) | user_id (FK) | title | template | data (JSON) | created_at | updated_at

analyses  (auto-saved on every upload)
  id (UUID PK) | user_id (FK) | cv_name | job_description | result (JSON) | match_score | created_at
```

## Deployment

- **Local:** `streamlit run app.py`
- **Cloud:** Streamlit Community Cloud — connect GitHub repo, set `GOOGLE_API_KEY` in Secrets
- **Database:** SQLite (`data/excelcv.db`) — auto-created on first run
- **Secrets needed:** `GOOGLE_API_KEY` (required), `SESSION_SECRET`, `SMTP_*` (optional)
