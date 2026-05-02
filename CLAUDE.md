# ExcelCV — Development Status for Claude

This file is for Claude to read at the start of a new session so it can immediately understand
what has been built, what is working, and what still needs to be done.

---

## Project Overview

**ExcelCV** — AI-powered CV reviewer and resume builder built with Streamlit + Google Gemini.
- Run: `streamlit run app.py --server.port 8501`
- Database: SQLite (SQLAlchemy ORM) — `src/database.py`
- Auth: email/password + Google OAuth (cookies for session persistence)
- AI: Google Gemini via `src/gemini_client.py`

---

## Architecture

```
app.py                      ← Main router (page dispatch, theme, auth gating)
src/
  auth_utils.py             ← Session, cookies, password hashing, login/logout
  database.py               ← SQLAlchemy models: User, CV, Analysis
  gemini_client.py          ← Gemini API calls (CV analysis, bullet suggestions)
  email_utils.py            ← Password reset email
  oauth_utils.py            ← Google OAuth token exchange
  services/pdf_generator.py ← CV PDF export (WeasyPrint / fallback)
  ui/
    app_utils.py            ← Page routing helpers, snapshot store, logo loader
    layout.py               ← Header (nav + user dropdown), footer
    css_injection.py        ← Global CSS helpers (compact header, top bar, etc.)
    theme.py                ← Theme CSS variables injection
    auth_page.py            ← Sign In / Sign Up / Google OAuth page
    upload.py               ← Home / Analyze CV page (file upload + JD input)
    report.py               ← Analysis report view
    cv_builder_page.py      ← Resume Builder page (main focus of recent work)
    my_cvs_page.py          ← My CVs page (saved CVs list)
    my_analyses_page.py     ← My Analyses page (saved analyses list)
    settings_page.py        ← Settings page (email, password, delete account)
    static_pages.py         ← Info/legal pages (career blog, privacy, contact…)
    analysis_runner.py      ← Analysis orchestration helpers
    common.py               ← Shared UI helpers (issue_count, etc.)
```

---

## COMPLETED FEATURES

### Core Application
- [x] Full page routing via `app.py` (home, upload, report, cv-builder, my-cvs, my-analyses, settings, auth, static pages)
- [x] Theme toggle (light/dark) with localStorage persistence across sessions
- [x] Google OAuth sign-in flow (exchange code → create user → set session cookie)
- [x] Email/password sign-in, sign-up, forgot password (email reset link)
- [x] Session cookie restore (persistent login across page reloads)
- [x] Protected pages redirect to auth gate, then bounce back to intended page
- [x] Logout clears cookie and session

### Header & Footer
- [x] Site header with logo, nav links, user dropdown ("Hi, Krishnendu ▾")
- [x] User dropdown: Give Feedback, Support, Settings, Logout
- [x] Full-width professional footer with product/resource/legal columns
- [x] Active nav item highlighting per page

### Home / Analyze CV Page
- [x] File upload (PDF/DOCX), job description textarea
- [x] Gemini AI analysis with score, issues, skill gaps
- [x] Upload preview card (static)
- [x] Compare mode (multiple CVs)

### Report Page
- [x] Full analysis report rendering
- [x] Shareable snapshot via `?rid=` query param

### My CVs Page
- [x] List saved CVs, open in builder, delete

### My Analyses Page
- [x] List past analyses, view reports

### Settings Page
- [x] Change email (with password verification)
- [x] Change password
- [x] Delete account (with confirmation dialog)
- [x] Card-styled UI matching homepage design

### Resume Builder Page (`src/ui/cv_builder_page.py`)
This is the most recently worked-on page. Current state:

- [x] FlowCV-inspired two-column layout (left: form, right: live preview)
- [x] Hero section + Overview/Content/Customize/AI Tools pill nav (cosmetic)
- [x] Top controls: Resume Title, Template selector, Save button, Prepare PDF button
- [x] Personal Details card (Full Name, Email, Phone, Location, Website, LinkedIn, GitHub)
- [x] Collapsible sections: Summary, Education, Professional Experience, Skills, Certificates, Projects
- [x] Each section supports adding/removing multiple entries
- [x] Experience: multi-bullet support, AI bullet suggestion via Gemini
- [x] Customize section (Accent Color picker + Font selector) in expander
- [x] "Add Content" CTA button (styled like FlowCV's pink gradient button)
- [x] Save CV to database, Load saved CV into builder
- [x] PDF export via `generate_cv_pdf()`
- [x] Three HTML templates: Classic, Modern, Minimal (in `generate_cv_html()`)
- [x] Dark mode preview support (`preview_dark` param)
- [x] **REAL-TIME PREVIEW** — as user types in Personal Details fields, the preview updates
      instantly (no Enter/Submit needed). Implemented via postMessage JS bridge:
      - `inject_cv_builder_realtime_js()` — injected 0-height iframe listens to `input` events
        in the parent document using capture phase, scoped to `.st-key-cvb-personal-card`
      - Broadcasts `{type:'cv-rt-update', field, value}` to all iframes
      - `generate_cv_html()` preview has a `message` event listener that updates
        `#cv-name` and `#cv-contact` DOM elements directly
      - Contact row always rendered (with `display:none` when empty) so the handler
        can always find `#cv-contact`
- [x] **"Press Enter to apply" tooltip hidden** — `[data-testid="InputInstructions"]` set to
      `display: none !important` in `_inject_cv_builder_css()`

---

## KNOWN ISSUES / NOT YET DONE

### Resume Builder — High Priority
- [ ] **Real-time preview only works for Personal Details fields** (Full Name + contact row).
      Fields in Experience, Education, Skills, Projects, Certifications do NOT update in real-time.
      They update when the user presses Enter or tabs away, causing a full Streamlit rerun.
      To extend real-time to other sections: add more postMessage handlers for each section,
      or do a full-page snapshot diff approach.

- [ ] **Preview is blank/white when the page first loads** (screenshot shows blank right panel).
      This happens because session state fields are empty on first load. The preview shows
      "Your Name" placeholder but no content. Consider showing a sample/skeleton CV on first load.

- [ ] **"Add Content" button** (the pink gradient button at the bottom) currently just shows
      an info message. It should instead scroll to the relevant section or open a modal
      similar to FlowCV's "+ Add Content" flow.

- [ ] **Overview / Customize / AI Tools pills** in the hero are cosmetic only — they have no
      routing behavior. "AI Tools" should eventually open an AI-powered panel.

- [ ] **PDF export quality** — `generate_cv_pdf()` in `src/services/pdf_generator.py` may fall
      back to a simple text dump if WeasyPrint is not installed. Needs testing on the target
      deployment environment.

### Analysis / Report Page
- [ ] The report page shares a snapshot via `?rid=` but the snapshot is in-memory
      (`@st.cache_resource` dict). It does not persist across server restarts.
      For production, consider database-backed snapshots.

### Static Pages
- [ ] Many static pages (ATS Insights, Evaluation Toolkit, Project Notes, How It Works,
      Interview Prep, Privacy Policy, Terms of Service) have placeholder content.
      These need real content written for them.

### Contact Page
- [ ] Contact form is wired to `send_contact_email()` but only works if SMTP env vars
      are set. Currently no visual feedback if email is not configured.

### General / Infrastructure
- [ ] No production deployment config. Currently runs locally on port 8501.
- [ ] No test coverage for the new CV builder real-time JS bridge (JS-side logic is not
      Python-testable; would need Playwright or Selenium for E2E tests).
- [ ] `tests/test_app_helpers.py` and `tests/test_ui_smoke.py` are modified but may be
      out of sync with the current page structure.

---

## KEY FILES TO KNOW

| File | Why it matters |
|------|---------------|
| `app.py` | All page routing, auth gating, theme sync |
| `src/ui/cv_builder_page.py` | Resume Builder — most recently worked on |
| `src/ui/layout.py` | Header + footer for every page |
| `src/ui/css_injection.py` | Global CSS overrides (compact header, etc.) |
| `src/auth_utils.py` | Session, cookies — touch with care |
| `src/database.py` | SQLAlchemy models (User, CV, Analysis) |
| `src/gemini_client.py` | AI calls — `suggest_cv_bullets()`, `analyze_cv()` |
| `src/services/pdf_generator.py` | CV PDF export |

---

## RECENT SESSION WORK (last session: 2026-04-30)

### Backend fixes & upgrades for Resume Builder

1. **Customization persisted in DB and restored on load** — DONE
   - `collect_cv_data()` now includes a `"customization"` key with `accent_color`,
     `font`, `font_size`, `line_height`, `entry_spacing`
   - `load_cv_into_builder()` restores all five from the saved `data["customization"]`
   - Previously these were lost every time a CV was loaded from My CVs

2. **Font Size / Line Height / Entry Spacing wired up end-to-end** — DONE
   - `render_cv_builder_page()` reads `cvb_font_size`, `cvb_line_height`, `cvb_entry_spacing`
     from session state and passes them to both `generate_cv_html()` and `generate_cv_pdf()`
   - Three new number inputs added inside the **Customize** expander so users can
     actually control these values

3. **PDF generation cached** — DONE
   - Added `@st.cache_data` wrapper `_cached_generate_cv_pdf()` — PDF bytes are only
     rebuilt when the CV data actually changes, not on every Streamlit rerun

4. **`_save_cv` rollback on DB error** — DONE
   - Added `except Exception: db.rollback(); return False` so failed commits don't
     leave the session in a dirty state

5. **Bullet removal orphan key cleanup** — DONE
   - "Remove Bullet" now pops the last bullet's session-state key before decrementing
     the counter, so old values don't linger and ghost-populate bullets after re-adds

6. **AI bullet suggestions use existing bullets as context** — DONE
   - "AI Suggest" now builds a `context` string from all filled bullet fields and passes
     it to `suggest_cv_bullets(role, company, context)` so Gemini avoids duplicating
     bullets the user already wrote

7. **PDF generator XML escaping** — DONE (`src/services/pdf_generator.py`)
   - All user-supplied text now goes through `xml.sax.saxutils.escape` before being
     embedded in ReportLab `Paragraph` markup — previously a `<` or `&` in a job title
     or company name would crash PDF generation with an XML parse error

### Previous session work (2026-04-29)

1. **Real-time preview for Personal Details** — DONE
   - Added `id="cv-name"` and `id="cv-contact"` to all three templates in `generate_cv_html()`
   - Added `postMessage` listener inside the preview HTML
   - Created `inject_cv_builder_realtime_js()` function
   - Called it inside `render_cv_builder_page()` after `components.html(html, ...)`
   - Confirmed working: user saw "Krishnendu Ghosh" appear live in preview

2. **Removed "Press Enter to apply" tooltip** — DONE
   - Added `[data-testid="InputInstructions"] { display: none !important; }` to
     `_inject_cv_builder_css()` at the end of the style block

---

## HOW TO START NEXT SESSION

1. Read this file.
2. Read `src/ui/cv_builder_page.py` (it is long, ~1310 lines — focus on `render_cv_builder_page()`,
   `generate_cv_html()`, `_inject_cv_builder_css()`, and `inject_cv_builder_realtime_js()`).
3. Ask the user what they want to work on next.

Good next steps to suggest to the user if they don't have a specific request:
- Extend real-time preview to Experience/Education/Skills sections
- Improve the blank-preview-on-first-load UX (skeleton or sample data)
- Wire up the "AI Tools" pill with an actual AI panel
- Fill in content for static pages
- PDF export testing and improvement
