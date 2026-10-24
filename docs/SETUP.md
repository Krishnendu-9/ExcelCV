# ExcelCV — Setup Guide

ExcelCV is a Streamlit application: an AI-powered CV reviewer + multi-resume comparator + resume builder + cover-letter generator, backed by SQLite for per-user persistence.

> **Deploying anywhere other than your own machine? Read [KNOWN_ISSUES.md](KNOWN_ISSUES.md) first.** It lists problems left unfixed because the right fix depends on your deployment: login throttling that trusts client-supplied IP headers and lets anyone lock any account, an AI rate limit that counts actions rather than API calls, and unlimited free sign-ups.

---

## 1) Prerequisites

- **Python 3.13** — the version CI tests and `pyproject.toml` targets.
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

Then install the headless Chromium browser that the **resume builder's PDF export** launches at runtime (through Playwright, which `requirements.txt` already installs):

```bash
# Windows
py -3 -m playwright install chromium

# macOS / Linux
python3 -m playwright install chromium
```

Everything else works without it, but the resume builder's **Download PDF** button will fail until Chromium is installed.

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
| `SESSION_SECRET` | Signs session cookies and Google OAuth state. **The app refuses to start without it.** It must be at least 32 characters and must not be a published placeholder: the value in `.env.example`, `changeme`, `change-this` and similar are all rejected. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. |

`.env.example` is documentation only; the app never reads it. Copying it unchanged leaves `SESSION_SECRET` at its placeholder, which is rejected on purpose.

### Optional

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_MODEL` | Override the default Gemini model preference order. | `models/gemini-2.0-flash` |
| `ENABLE_PERSISTENT_LOGIN` | `1` keeps users signed in across browser restarts with a signed cookie. | `0` |

### Optional - Production Safety Guardrails

These env vars are optional. If unset, the app uses safe defaults.

#### Auth throttling (login + forgot password)

| Variable | Purpose | Default |
|---|---|---|
| `AUTH_LOGIN_WINDOW_SECONDS` | Time window for failed-login counting. | `600` |
| `AUTH_LOGIN_MAX_ATTEMPTS` | Max failed logins in the window before temporary lockout. | `5` |
| `AUTH_LOGIN_LOCK_SECONDS` | Temporary lockout duration after exceeding login limit. | `900` |
| `AUTH_RESET_WINDOW_SECONDS` | Time window for forgot-password request counting. | `1800` |
| `AUTH_RESET_MAX_ATTEMPTS` | Max reset requests in the window. | `3` |

#### Gemini API usage guardrails

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_RATE_WINDOW_SECONDS` | Rate-limit window for AI requests per user/session. | `60` |
| `GEMINI_MAX_REQUESTS_PER_WINDOW` | Max AI requests allowed in the window. | `20` |
| `GEMINI_MAX_CV_CHARS` | Longest CV text accepted. Longer CVs are rejected with a message; anything accepted is sent to the model whole. The default is four A4 pages of text packed edge to edge at 10 pt, beyond any real resume (derivation in `src/gemini_client.py`). | `26624` |
| `GEMINI_MAX_JD_CHARS` | Longest job description accepted, for both analysis and cover letters. Same rule: rejected if longer, never silently cut. | `40000` |
| `GEMINI_MAX_FILE_SIZE_BYTES` | File-size guardrail for analysis. Can only **lower** the 2 MB upload cap; a larger value has no effect. | `2097152` |
| `GEMINI_ANALYSIS_MAX_OUTPUT_TOKENS` | Max output tokens requested for analysis response. | `2400` |

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

- **Upload cap = 2 MB per file** (`maxUploadSize = 2`). Enforced at the network layer before the Python validation in [src/ui/upload.py](../src/ui/upload.py) runs. It must match `MAX_FILE_MB` in [src/config.py](../src/config.py); a test checks that they agree.
- **Hot-reload via polling** (`fileWatcherType = "poll"`) — reliable on Windows where the default inotify-style watcher is flaky.
- **Folder watch blacklist** prevents spurious reruns when the SQLite DB or git refs are written.

Auto-rerun on save is a development setting and is not committed. Turn it on for a local session with `streamlit run app.py --server.runOnSave true`.

---

## 5) Data & Storage

- **Database**: a single SQLite file at `data/excelcv.db`. Auto-created on first app startup by [`src/database.py`](../src/database.py) `init_db()`. Per-user data (saved resumes, analyses, comparisons) survives logout.
- **WAL mode**: connections use SQLite's write-ahead log (`journal_mode=WAL`, `busy_timeout` 15 s), so concurrent sessions do not block each other on reads. This creates `excelcv.db-wal` and `excelcv.db-shm` next to the database while the app runs.
- **Gitignored**: `data/*.db` and the `-wal` / `-shm` / `-journal` side files are in `.gitignore`, so your local data is never committed.
- **Backup**: the file isn't in version control. **Stop the app first**: while it runs, recent writes may still sit in `excelcv.db-wal`, and copying only `excelcv.db` would miss them. Then copy it:
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
  prompt_fence.py             — Delimiter fencing for untrusted prompt input
  pdf_utils.py                — PDF (pypdf) and DOCX text extraction
  oauth_utils.py              — Google OAuth state and token exchange
  email_utils.py              — Password reset email (SMTP)
  config.py                   — .env loading, SESSION_SECRET guard, MAX_FILE_MB
  cover_letter/               — Cover letter page + service
  services/
    pdf_generator.py          — Saved-CV PDF export (ReportLab)
    comparison_pdf.py         — Compare-resumes PDF export
    reporting.py              — Analysis report PDF / Markdown
  ui/
    cv_builder_pdf.py         — Resume builder PDF export (headless Chromium via Playwright)
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

**App refuses to start, complaining about `SESSION_SECRET`** — it is missing, shorter than 32 characters, or a placeholder. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` and put it in `.env`.

**Resume builder "Download PDF" fails with "PDF engine unavailable"** — run `py -3 -m playwright install chromium` (see step 2).

**Google sign-in says the browser did not send back the sign-in cookie** — click Continue with Google again. If it keeps happening, the browser is blocking cookies for this site.

**SQLite "database is locked"** — WAL mode lets reads and writes overlap, and writers wait up to 15 s for each other. A lock error now usually means another program (a DB browser, a second app instance) is holding a write transaction open. Close it.

---

## 8) What's Not Set Up Yet

- **Coverage is growing but still not complete** — `tests/` covers auth/session helpers, the session-secret guard, OAuth state binding, prompt fencing, scoring core, analysis runner paths, the cover-letter pipeline, compare/upload helpers, SQLite settings and committed configuration. Run with `py -3 -m unittest discover -s tests -p "test_*.py" -q`. CI also runs ruff, mypy (UI pages excluded) and pip-audit. Large UI flows are still mostly manual: Playwright is installed for the resume builder's PDF export, but no browser-driven end-to-end tests exist yet.
- **No production deployment config** — the app runs locally on port 8501. `SESSION_SECRET` is already enforced at startup. For deployment you would still need to harden the SMTP / OAuth secrets handling, fix login throttling for your proxy setup (see [KNOWN_ISSUES.md §1](KNOWN_ISSUES.md#1-login-and-password-reset-throttling-trusts-spoofable-headers-and-can-lock-out-any-account)), and put SQLite behind a proper backup story (or migrate to Postgres via SQLAlchemy's connection string).
