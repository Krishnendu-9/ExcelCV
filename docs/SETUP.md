# ExcelCV — Setup Guide

ExcelCV is a Streamlit application: an AI-powered CV reviewer + multi-resume comparator + resume builder + cover-letter generator, backed by SQLite for per-user persistence.

---

## 1) Prerequisites

- **Python 3.11+** (the codebase uses `match` statements, `dict | None` PEP 604 unions, etc.)
- A **Google Gemini API key** — sign up at [aistudio.google.com](https://aistudio.google.com/app/apikey). Free tier is sufficient for development.

OS notes:
- **Windows**: use `py -3` (the launcher) in the commands below.
- **macOS / Linux**: replace `py -3` with `python3`.

---

## 2) Install Dependencies

```bash
# Windows
py -3 -m pip install -r requirements.txt

# macOS / Linux
python3 -m pip install -r requirements.txt
```

If you prefer a virtual environment (recommended):

```bash
# Windows
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3) Configure Environment

Copy `.env.example` to `.env` in the repo root and fill in the keys:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### Required

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key. Without it, the Analyze CV / Compare Resumes / Cover Letter features won't work. |

### Recommended (defaults work but should be overridden)

| Variable | Purpose | Default |
|---|---|---|
| `SESSION_SECRET` | HMAC key used to sign session cookies. **Change this in any non-local deployment.** Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. | `excelcv-session-key-change-in-prod` |
| `GEMINI_MODEL` | Override the default Gemini model preference order. | `models/gemini-2.0-flash` |

### Optional — Google OAuth ("Continue with Google" button)

Skip this entire group if you only want email/password sign-in.

| Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `GOOGLE_REDIRECT_URI` | Must match a URI authorized in the Console. Default: `http://localhost:8501` |

To set up OAuth:
1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (Application type: **Web application**).
3. Add `http://localhost:8501` (and any other host you'll run from) under **Authorized redirect URIs**.
4. Paste the generated Client ID / Secret into `.env`.

### Optional — SMTP (password reset emails)

Skip if you don't need the "Forgot password?" flow.

| Variable | Purpose | Default |
|---|---|---|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username (often the sender email) | *(empty — disabled)* |
| `SMTP_PASSWORD` | SMTP password. For Gmail, use an **[App Password](https://myaccount.google.com/apppasswords)**, not your account password. | *(empty)* |
| `SMTP_FROM` | "From" address. Falls back to `SMTP_USER` if blank. | *(empty)* |
| `SMTP_ENCRYPTION` | `tls`, `ssl`, or empty for plain. | `tls` |

If `SMTP_USER` is empty, the reset-password flow silently no-ops (the UI still says "if that email is registered, a link has been sent" so users don't learn which addresses exist).

---

## 4) Run the App

```bash
# Windows
py -3 -m streamlit run app.py

# macOS / Linux
python3 -m streamlit run app.py
```

The console will print:

```
Local URL:    http://localhost:8501
Network URL:  http://<your-LAN-ip>:8501
```

Open the Local URL in your browser. On first run the SQLite database is auto-created at [`data/excelcv.db`](../data/excelcv.db) with all 5 tables (`users`, `cvs`, `analyses`, `comparisons`, `password_reset_tokens`).

### Useful runtime knobs

These live in [`.streamlit/config.toml`](../.streamlit/config.toml) — don't delete the file:

- **Upload cap = 2 MB per file** (`maxUploadSize = 2`). Enforced at the network layer before the Python validation in [src/ui/upload.py](../src/ui/upload.py) runs.
- **Hot-reload via polling** (`fileWatcherType = "poll"`) — reliable on Windows where the default inotify-style watcher is flaky.
- **Auto-rerun on file save** (`runOnSave = true`).
- **Folder watch blacklist** prevents spurious reruns when the SQLite DB or git refs are written.

---

## 5) Data & Storage

- **Database**: a single SQLite file at `data/excelcv.db`. Auto-created on first app startup by [`src/database.py`](../src/database.py) `init_db()`. Per-user data (saved resumes, analyses, comparisons) survives logout.
- **Gitignored**: `data/*.db` is in `.gitignore` so your local DB is never committed.
- **Backup**: the file isn't in version control. If the data matters to you, copy it periodically:
  ```bash
  # Windows
  copy data\excelcv.db data\excelcv.db.bak

  # macOS / Linux
  cp data/excelcv.db data/excelcv.db.bak
  ```
- **Reset to a clean DB**: stop the app, delete `data/excelcv.db`, restart. `init_db()` will recreate empty tables. (Warning: this wipes all accounts + saved data.)

---

## 6) Project Layout

```
app.py                        — Main router, page dispatch, auth gating, theme
src/
  auth_utils.py               — Session cookies, password hashing, login/logout
  database.py                 — SQLAlchemy models (User, CV, Analysis, Comparison, ...)
  gemini_client.py            — Gemini API calls (CV analysis)
  oauth_utils.py              — Google OAuth token exchange
  email_utils.py              — Password reset email (SMTP)
  config.py                   — Env helpers, MAX_FILE_MB
  cover_letter/               — Cover letter page + service
  services/
    pdf_generator.py          — Resume PDF export (ReportLab)
    comparison_pdf.py         — Compare-resumes PDF export
  ui/
    upload.py                 — Analyze CV / Compare form (home page)
    report.py                 — Single-CV analysis report view
    compare_report.py         — Ranked comparison results page
    cv_builder_page.py        — Resume Builder workspace
    my_cvs_page.py            — Saved resumes list
    my_analyses_page.py       — Saved analyses list
    my_comparisons_page.py    — Saved comparisons list
    settings_page.py          — Email / password / delete account
    auth_page.py              — Sign in / sign up / forgot password
    layout.py                 — Top nav, footer, theme toggle
    theme.py, css_injection.py, css_generators.py
                              — Theme + CSS injection helpers
docs/
  excelcv.md                  — Architecture overview
  compareCV.md                — Compare Resumes feature reference
  resume_builder.md           — Resume Builder behavior reference
  SETUP.md                    — (this file)
```

---

## 7) Troubleshooting

**"Python was not found"** on Windows — install Python from [python.org](https://www.python.org/downloads/) (don't use the Microsoft Store stub), or replace `py -3` with the full path to `python.exe`.

**Streamlit hot-reload not picking up edits** — make sure the file watcher type is set to polling in `.streamlit/config.toml`. This is already set; don't change it.

**`ImportError: No module named ...`** — re-run `pip install -r requirements.txt`. If you used a venv, make sure it's activated.

**Gemini calls fail with quota / 429** — the free tier has rate limits (~15 requests/min on `gemini-2.0-flash`). The Compare Resumes flow detects this mid-run and short-circuits remaining files; see [docs/compareCV.md §12](compareCV.md) for details.

**Google OAuth redirect mismatch** — `GOOGLE_REDIRECT_URI` must exactly match a value registered in Google Cloud Console **including trailing slash, port, and scheme**. The default `http://localhost:8501` (no trailing slash) is what Streamlit serves locally.

**Upload says "could not read these files (try re-selecting)" on the first try** — known Streamlit hydration race. The app retries up to 2 times silently before surfacing the warning. If you still see it after retries, the file is genuinely unreadable.

**SQLite file locked** — only one process can write to a SQLite file at a time. Close any other Streamlit instance / DB browser before running the app.

---

## 8) What's Not Set Up Yet

- **No automated tests** — there's no `tests/` directory in this branch. The earlier SETUP guide referenced `py -3 -m unittest discover -s tests` and a Streamlit smoke test; both were aspirational, not real. If you add tests later, the convention would be `tests/` at the repo root with `test_*.py` files.
- **No production deployment config** — the app runs locally on port 8501. For deployment you'd need to set `SESSION_SECRET` to a strong random value, harden the SMTP / OAuth secrets handling, and put SQLite behind a proper backup story (or migrate to Postgres via SQLAlchemy's connection string).
