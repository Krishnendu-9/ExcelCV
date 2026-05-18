# Compare Resumes Page (`compare-cv`) Documentation

Last verified against the repository on **2026-05-18**.

## 1) Purpose

The **Compare Multiple Resumes (2-5 files)** section lets a signed-in user:

- paste one job description,
- upload multiple resumes,
- run the same analysis pipeline for each file,
- view ranked side-by-side results on a dedicated report page.

This is used for candidate shortlisting and quick ATS/JD-fit comparison.

---

## 2) Where It Lives

Primary implementation files:

- `app.py`
- `src/ui/upload.py`              (compare form + run dispatcher + autosave hook)
- `src/ui/compare_report.py`      (dedicated ranked results page + drill-down + persistence helpers)
- `src/ui/my_comparisons_page.py` (list / view / delete saved comparisons)
- `src/ui/analysis_runner.py`     (`run_multi_resume_comparison` orchestration)
- `src/services/comparison_pdf.py` (ReportLab PDF export)
- `src/database.py`               (`Comparison` SQLAlchemy model — persistence)
- `src/ui/app_utils.py`           (`_clear_comparison_run_artifacts`, `_save_report_snapshot_from_data`, snapshot store)
- `src/auth_utils.py`             (logout cleanup)
- `src/ui/css_injection.py`       (compare-specific styling)

Route keys:

- `compare-cv`      — form page (currently anchored inside the main upload page)
- `compare-report`  — dedicated ranked results page (protected)
- `my-comparisons`  — saved comparisons list (protected; reached via user dropdown)

---

## 3) Routing + Navigation Behavior

### Route ownership

- `app.py` treats `compare-report` and `my-comparisons` as protected pages.
- `compare-cv` redirects to the upload page anchored at the compare section.
- `my-comparisons` is reached from the user dropdown ("My Comparisons"), not the main nav, to avoid crowding the navbar.
- If unauthenticated, user is routed to auth and returned after login.

### Navbar integration

- Top nav label: **Compare Resumes**
- Nav action maps to the upload page + compare anchor for smooth in-page landing.
- Active highlight is synchronized with compare focus state via an `IntersectionObserver` scroll-spy.

### Anchor behavior

- Anchor ID: `compare-section-anchor`
- Compare mode scrolls once per entry context (not on every rerun) to reduce jumpiness.

### Return-to-compare (from the report page)

The dedicated report page (`render_compare_report_page`) sets two session-state hints on every render:

- `scroll_to_compare_anchor = True` — consumed by `render_upload_page` to scroll to the compare section.
- `home_nav_focus_compare = True` — read by the nav highlighter so "Compare Resumes" stays active.

Combined effect: pressing **browser Back** from the report lands the user back on the home page **at the compare section**, with the correct nav tab highlighted — no "Back to Compare" button needed (it was removed). An explicit click on the **Analyze CV** nav clears both flags so a deliberate nav choice isn't overridden by stale return-to-compare state.

### One-shot scroll-to-top on report entry

`scroll_compare_report_to_top` is set right before navigating into `compare-report` (from `_run_comparison_with_progress` and from the **My Comparisons → View** action). The report page pops it on first render and injects a one-shot scroll-to-top JS; subsequent reruns on the same page (sort change, expander toggle, etc.) do **not** re-scroll, so the user's scroll position is preserved during interactions.

---

## 4) UI Structure in `src/ui/upload.py`

Inside `render_upload_page(compare_mode: bool = False)`:

1. Hero/upload area (single CV flow) renders first.
2. Compare section anchor and shell render next.
3. Compare form is inside `st.container(key="compare_form_box")`.
4. Upload-stage warnings render inline below the staged-files list.
5. A "View latest comparison results →" deep link appears when prior results exist.
6. "What happens next?" helper card renders below the form.

Ranked results, the top-match card, the drill-down expanders, and the CSV/clear actions live on the **dedicated `compare-report` page** (`src/ui/compare_report.py`) — they are no longer rendered inline below the form.

Main compare heading:

- `Compare Multiple Resumes (2-5 files)`

---

## 5) Auth States

### Signed-in user

Shows form:

- `compare_jd` (text area)
- `compare_cvs_input_<rev>` (multi file uploader; reset by bumping `compare_cvs_rev`)
- staged-file list with per-row delete buttons
- submit button (`Run comparison`)

### Guest user

Shows locked CTA card:

- "Sign in to compare resumes"
- link to auth route with `next_page="compare-cv"`

No comparison computation executes for guests.

---

## 6) Input Validation Rules

Two layers of deduplication exist by design:

- **Form-stage** (`src/ui/upload.py`) — every newly uploaded file is hashed (SHA256) against already-staged files; duplicates are rejected with an upload-stage warning before the user can submit.
- **Runner-stage** (`run_multi_resume_comparison`) — defensive dedup using `(sanitized_filename_lower, file_size, sha256)` so direct callers (tests, future API entry points) are protected too. Duplicates here surface as run-stage warnings.

Other rules (validated in `run_multi_resume_comparison`):

- Job description is required (non-empty trimmed text).
- Minimum files: 2
- Maximum files: 5
- If deduplication leaves fewer than 2 unique files, request is rejected.
- Each file is still validated by `_analyze_cv_payload`, including size and extraction checks.

Max file size per file:

- controlled by `MAX_FILE_BYTES` / `MAX_FILE_MB` from `src/config.py`. The uploader's help text is rendered dynamically from `MAX_FILE_MB` so it stays in sync.

### First-interaction hydration race

Streamlit's `UploadedFile.getvalue()` can return empty bytes on the very first file-uploader interaction in a session, before the upload finishes hydrating server-side. To avoid surfacing a phantom "could not read these files" error on every first upload:

- `_read_uploaded_cv_bytes` (in `upload.py`) is defensive — tries `getvalue()`, then `seek(0)` + `read()`.
- If a batch comes back fully unreadable AND no other progress was made, the form silently reruns up to `MAX_HYDRATION_RETRIES = 2` times (counter held in `compare_upload_hydration_retries`) so the second pass can re-read the now-hydrated files.
- The widget rev is NOT bumped during retries, so the uploader keeps its state and re-delivers the same files.
- Only after retries are exhausted does the unreadable warning surface.

---

## 7) Comparison Processing Pipeline

`run_multi_resume_comparison(job_description, uploaded_cvs, progress_callback=None)`:

Per file (sequential, in order):

1. Extract text (`extract_cv_text`)
2. Run LLM analysis (`analyze_cv_with_gemini`)
3. Normalize/scalar values:
   - final score
   - JD alignment
   - ATS parse
   - sections score
   - issue count
   - top missing skills
4. Stash the full analysis dict under the row's `_analysis` key so the report page can render drill-down details without re-running Gemini.

Output row fields (display):

- `Rank`
- `Resume`
- `Final Score`
- `JD Alignment`
- `ATS Parse`
- `Sections`
- `Issues`
- `Top Missing Skills`

Hidden/internal row fields:

- `_analysis` — full analysis dict (omitted from the dataframe via `column_order` and from the CSV export via `extrasaction="ignore"`).

Sorting:

1. Final Score descending
2. Issues ascending
3. Resume name ascending

### Why sequential, not parallel

Parallelizing the per-file Gemini calls would shave wall-clock time but would also defeat the quota short-circuit (§ 12) — if file N hits a 429, files N+1..end can only be skipped *if* they haven't been submitted yet. Sequential keeps that contract simple.

### Progress callback contract

`progress_callback(file_name, idx_1_based, total, status)` is invoked before each file (`"running"`), after success (`"done"`), after failure (`"error"`), and for any files skipped due to a prior quota error (`"skipped"`). Errors inside the callback are swallowed so a UI bug never breaks the run. The upload page uses this to stream per-file status into a live progress card while the run is in flight.

---

## 8) Session State Keys (Compare Flow)

Run artifacts (lifecycle = until next run / inputs change / clear / logout):

- `comparison_results`
- `comparison_errors`
- `comparison_warnings`
- `comparison_signature`
- `comparison_attempted`

Form state (lifecycle = until full reset / logout):

- `compare_jd`
- `compare_selected_files` (list of staged file records: `name`, `size`, `bytes`, `signature`)
- `compare_cvs_rev` (monotonic counter that re-keys the uploader widget after each successful add)
- `compare_cvs_input_<rev>` (Streamlit uploader widget state, transient)
- `compare_upload_warnings` (upload-stage warnings only; replaced per upload batch, cleared on successful run)
- `compare_upload_hydration_retries` (first-interaction hydration race counter; see § 6)

Report-page state:

- `compare_report_sort_choice` (selected sort label; persists per session so re-entering the page keeps the user's last sort)
- `scroll_compare_report_to_top` (one-shot; set just before navigating into the report so the page lands at top of viewport, popped on first render)

Navigation / return hints (set by the report page, consumed by the home page):

- `scroll_to_compare_anchor` (scrolls the home page to the compare section on next render)
- `home_nav_focus_compare` (keeps "Compare Resumes" highlighted in the top nav when on the home page)

### Signature-based stale-result protection

- Current input signature = normalized JD + sorted `(file_name, file_size)` tokens.
- If signature changes after the previous run, `_clear_comparison_run_artifacts()` is called and the user is prompted to rerun. Because the unified helper also clears `comparison_attempted`, the report page's empty state correctly reads as "no comparison yet" instead of "your last run produced 0 rows".

---

## 9) Result Rendering

All result rendering lives on the dedicated `compare-report` page (`src/ui/compare_report.py`).

### Page structure (when results exist)

1. **Hero** (full-width) — title + subtitle only. Chips have moved into the primary section.
2. **JD context expander** (full-width) — collapsed by default; preview shows the first 140 chars of the JD so the user has context without having to expand.
3. **Primary section** — outer card mirroring the Analyze CV home-page hero (radial+linear gradient background, 22px rounded corners, soft shadow). Two columns:
   - **LEFT (1.4)** — Comparison Results
     - Section title `Comparison Results` (top-left)
     - Sort by selector (top-right of the same row as the title)
     - Chip strip: `✓ N resumes compared`, `✓ Top score X`, `✓ Average Y`
     - Custom HTML comparison table (see below)
   - **RIGHT (1.0)** — Top Match card
     - `★ TOP MATCH · RANK #1` pill
     - Resume name + score `XX / 100`
     - Progress bar
     - Per-metric chips (JD Alignment, ATS Parse, Sections, Issues)
     - Top missing skills chips
4. **Per-resume drill-down expanders** (full-width below the primary section) — each row gets one, in current sort order. Each contains:
   - Per-metric tiles (JD Alignment, ATS Parse, Sections, Issues)
   - Summary text (from the stashed `_analysis` dict)
   - Top missing skills chips
   - Suggestions list (top 6)
   - Missing keywords (top 12)
   - **"Open as full report →"** primary button — saves a snapshot via `_save_report_snapshot_from_data` and navigates to the single-CV `report` page so the user can dig into the full scoring breakdown without re-uploading.
5. **Actions row** (full-width, right-aligned) — `Clear results` · `Download CSV` · **`Download PDF`** (primary).

### Comparison table

Custom HTML (`_render_comparison_table_html`), not `st.dataframe` — needed for per-row tinting, color-coded score cells, and inline meters that `st.dataframe` can't produce.

Columns: `Rank · Resume · Final · JD Align · ATS Parse · Sections · Issues` (Top Missing Skills was dropped from the table to keep it readable at column width; it survives in CSV export and in the drill-down expanders).

Per-cell behavior:

- **Score cells** (Final / JD Align / ATS Parse / Sections): inline meter (fixed-width track + tier-colored fill) + numeric value. Color tiers: green ≥ 80, amber 60–79, red < 60. `currentColor` on the fill auto-matches the number color.
- **Issues**: inverse coloring (low is good) — green ≤ 5, amber 6–15, red > 15. No meter (not a 0–100 scale).
- **Winner row**: identity-based ★ pill in the rank cell + green left border + faint green row tint. **Decoupled from the user's sort choice** — the star always belongs to the *true* top match (resume at index 0 of the unsorted comparison rows, which the Top Match card on the right is showing). If the user re-sorts to "Final Score (low → high)" and the true top match drops to row 3, it still shows `★ 3` with the green tint there.

### Sort selector

`_SORT_OPTIONS` in `compare_report.py` exposes 8 sort variants (Final / JD / ATS / Sections / Issues in both directions, plus name A → Z). `_apply_sort` re-orders the rows **and re-numbers the `Rank` column** so the displayed rank reflects the current sort position. The sorted rows flow through to the table, the drill-down expanders, the CSV export, and the PDF export — single source of truth.

### CSV export

`_comparison_rows_to_csv` uses `extrasaction="ignore"` so the hidden `_analysis` key never leaks into the CSV. Column order is stable (`Rank · Resume · Final Score · JD Alignment · ATS Parse · Sections · Issues · Top Missing Skills`). The export reflects the **current sort**, not the original ranking.

### PDF export

`generate_comparison_pdf` (in `src/services/comparison_pdf.py`, ReportLab) renders an A4 portrait artifact:

- Title + meta strip (resumes compared, top match, top score, average, generation timestamp)
- JD block (truncated to 1200 chars for layout — full JD lives in DB / session)
- Ranked table — same color-coded tiers as the HTML version, winner row tinted with a green left border, header repeated on page break
- Per-resume summary blocks (rank · name · score → summary text + top missing skills + top 4 suggestions)
- Optional Notes appendix when `errors` / `warnings` are present

`_build_comparison_pdf_bytes` is wrapped with `@st.cache_data(max_entries=20)` so re-runs (sort changes, expander toggles) reuse the same bytes unless the args actually change.

### Persistence (autosave + my-comparisons)

After a successful run (`rows` non-empty), `_run_comparison_with_progress` calls `_autosave_comparison(rows, jd, errors, warnings)`. This writes a `Comparison` record (table `comparisons` in SQLite) with the full `rows` list (including each row's stashed `_analysis` dict), `errors`, `warnings`, denormalized `top_score` / `top_resume_name` / `resume_count` for fast list rendering, and `created_at`. Failure is silent — autosave is convenience, not a critical path.

The **My Comparisons** page (`src/ui/my_comparisons_page.py`, route `my-comparisons`) lists the signed-in user's saved comparisons (mirrors the My Analyses card layout). Per-row actions:

- **View Comparison** → calls `_load_saved_comparison_into_session(id)` which re-hydrates `comparison_results`, `comparison_errors`, `comparison_warnings`, `compare_jd`, sets `scroll_compare_report_to_top`, then navigates to `compare-report`.
- **Delete** → confirm dialog → row removed from `comparisons` table.

### Empty / failure states

When the run was attempted but no rows were produced:

- Empty state copy reflects the attempt and the per-file error list explains why (rate limit, unreadable PDF, empty file, etc.)

When issues occur:

- `comparison_errors` shown as warning list below the actions row
- `comparison_warnings` shown as info list (e.g. skipped duplicates, quota short-circuit)

---

## 10) Clear/Reset Behavior

Two helpers handle compare cleanup; the lifecycle ownership lives in `app_utils.py`:

- `_clear_comparison_run_artifacts()` (app_utils) — pops `comparison_results`, `comparison_errors`, `comparison_warnings`, `comparison_signature`, `comparison_attempted`. Leaves form inputs alone. Used by both the form (on input change) and the report page (`Clear results`).
- `_clear_comparison_session_state()` (upload.py) — full reset: calls the helper above AND clears `compare_upload_warnings`, `compare_upload_hydration_retries`, `compare_jd`, `compare_selected_files`, `compare_cvs_rev`, and any `compare_cvs_input_*` widget keys.
- `_clear_analysis_state(clear_comparison=True)` (app_utils) — uses the unified helper internally so the lifecycle stays consistent across analyze/compare flows.
- `logout_user()` (auth_utils) — clears every transient compare key including `comparison_attempted`, `compare_upload_warnings`, and `compare_upload_hydration_retries`. **Persisted records in the `comparisons` table survive logout** — they're per-user, so on next sign-in the same user sees their full history on the My Comparisons page.

Note: `compare_report_sort_choice`, `scroll_compare_report_to_top`, and `home_nav_focus_compare` are not in any of the explicit clear paths — `compare_report_sort_choice` is treated as a session preference (no harm in keeping); the other two are one-shot flags that get popped on consumption.

---

## 11) Styling Hooks (CSS)

Form / upload-page side:

- `.st-key-compare_section_shell`
- `.st-key-compare_form_box`
- `.st-key-compare_selected_list_box`, `.st-key-compare_file_row_<idx>`, `.st-key-compare_file_delete_btn_<idx>`
- `.compare-mode-badge`
- `.compare-progress-shell`, `.compare-progress-list`, `.compare-progress-item--{running,done,error,skipped}`
- `.compare-next-shell`, `.compare-next-title`, `.compare-next-list`

Report page — outer + sort:

- `.compare-report-hero`, `.compare-report-hero__title`, `.compare-report-hero__subtitle`
- `.st-key-compare_primary_section` — outer card (gradient bg, rounded, shadow)
- `.compare-results-title`
- `.compare-results-chips`, `.hero-chip` (chip strip inside the primary card)
- `.st-key-compare_sort_row`, `.compare-sort-label` (label is lifted via negative margin to align with the title)

Report page — table:

- `.compare-table-wrap`, `.compare-table`
- `.compare-th`, `.compare-th--rank`, `.compare-th--name`, `.compare-th--num`
- `.compare-td`, `.compare-td--rank`, `.compare-td--name`, `.compare-td--num`
- `.compare-td--score-good`, `.compare-td--score-medium`, `.compare-td--score-low`
- `.compare-td--issue-good`, `.compare-td--issue-medium`, `.compare-td--issue-high`
- `.compare-row`, `.compare-row--winner` (identity-based, not position-based)
- `.compare-winner-pill` (the ★ in the rank cell)
- `.compare-meter`, `.compare-meter__track`, `.compare-meter__fill`, `.compare-meter__val`

Report page — drill-down + actions:

- `.compare-drilldown-title`
- `[class*="st-key-compare_open_report_box_"]` (per-resume "Open as full report" button)
- `.st-key-compare_report_actions`

Empty state:

- `.compare-report-empty`, `.compare-report-empty__icon`, `.compare-report-empty__title`, `.compare-report-empty__copy`

Top-match card (right column):

- `.compare-top-card`, `.compare-top-card--hero`
- `.compare-top-card__tag`, `.compare-top-card__head`, `.compare-top-card__name`
- `.compare-top-card__score`, `.compare-top-card__score-value`, `.compare-top-card__score-total`
- `.compare-top-card__bar`, `.compare-top-card__bar-fill`
- `.compare-top-card__metrics`, `.compare-top-card__metric`
- `.compare-top-card__skills`, `.compare-top-card__skills-label`, `.compare-top-card__chip`, `.compare-top-card__chip--ok`

My Comparisons page:

- `.st-key-mycomparisons-root`, `.comparison-card`, `.comparison-top-name`, `.comparison-meta`, `.comparison-score-badge`, `.comparison-count-chip`, `.comparison-jd-preview`

All compare styling is centralized in `src/ui/css_injection.py` except the My Comparisons card styles, which live inline in `src/ui/my_comparisons_page.py` (mirrors the My Analyses page pattern).

---

## 12) Known Constraints

- Streamlit reruns the script on interactions; navigation is optimized but not true SPA behavior.
- Sequential model calls — see § 7 for the quota-driven rationale.
- Saved comparisons are per-user and listed on the My Comparisons page, but there is no shareable permalink yet (a saved record can only be opened by its owner, not via a URL).

### Gemini rate-limit (quota) short-circuit

If `analyze_cv_with_gemini` raises a 429 / quota / "resource exhausted" error mid-run, every remaining file is short-circuited as `skipped` rather than burning more quota. Both the per-file error list and a top-level warning explain what happened, and the progress UI shows the affected files as `skipped (rate limit)`.

---

## 13) QA Checklist (Recommended)

Functional:

- Signed-in compare run with 2 files works and lands on the dedicated report page **scrolled to top** (not stuck at the form's mid-page scroll offset).
- Signed-in compare run with 5 files works.
- 1 file shows validation error on the form, no navigation.
- 6 files attempted via uploader: warning shows that extras were skipped; run with the first 5 still works.
- Empty JD shows validation error.
- Duplicate file upload triggers warning and skips duplicates at the form stage.
- Per-file progress card updates live during the run (running → done/error/skipped).
- Results reorder correctly by score.
- Sort selector — picking a different sort re-orders both the table and the drill-down expanders; CSV and PDF exports reflect the current sort.
- ★ winner pill stays glued to the **true** top match across every sort option (e.g. sorting Final low → high still shows the ★ next to the highest-scoring resume, even if it's no longer at row 1).
- CSV download contains the same rows and column order as the spec (no `_analysis` column leakage).
- PDF download produces a valid file with color-coded scores, winner-row tint, JD block, and per-resume summaries.
- Drill-down expanders render summary, suggestions, and missing keywords from the stored analysis dict.
- **"Open as full report →"** from each drill-down navigates to the single-CV report page with the correct analysis loaded.

Navigation / scroll:

- Browser back from `compare-report` lands on the home page at the compare section with **Compare Resumes** highlighted in the nav.
- Clicking **Analyze CV** in the nav while on `compare-report` lands on the home page at the **top** (not the compare section) — the return-to-compare hints are cleared.
- Expander toggle / sort change on the report page does **not** yank the scroll position back to the top.

Persistence (my-comparisons):

- Running a comparison while signed in auto-saves a record visible on **My Comparisons** (reachable from the user dropdown).
- Clicking **View Comparison** re-hydrates `comparison_results` + JD + warnings and renders the report page exactly as it looked after the original run.
- **Delete** removes the row from the `comparisons` table and refreshes the list.
- Logout → log back in: saved comparisons are still listed (per-user persistence survives logout).

State/rerun:

- Changing JD after a run clears stale results AND `comparison_attempted` — re-entering report shows "no comparison yet", not the attempted-empty copy.
- Changing file set after a run clears stale results prompt.
- `Clear results` on the report page removes table + banners and bounces to the form.
- Logout clears every transient compare key (including `comparison_attempted` and `compare_upload_warnings`) but **leaves persisted DB rows intact**.

Auth:

- Guest sees sign-in CTA.
- Guest cannot run comparison.
- Post-login returns to compare route when requested from compare CTA.
- Guest accessing `?page=my-comparisons` directly is bounced to the auth gate.

Quota:

- Simulated 429 on file 2 of 4 leaves files 3 and 4 marked as `skipped (rate limit)` in both the progress UI and the report's per-file error list.

---

## 14) Improvement Backlog

Shipped:

- ✅ Persisted comparisons per user — new `comparisons` table in [src/database.py](../src/database.py), autosave hook in [src/ui/upload.py](../src/ui/upload.py) → `_autosave_comparison`, dedicated `my-comparisons` page at [src/ui/my_comparisons_page.py](../src/ui/my_comparisons_page.py), reachable from the user dropdown.
- ✅ "Open as full report" from each drill-down — uses `_save_report_snapshot_from_data` so any compared resume can be inspected via the full single-CV report flow without re-uploading.
- ✅ Sort selector above the table — re-orders rows + re-numbers ranks + flows through to drill-downs and CSV/PDF exports.
- ✅ PDF export — [src/services/comparison_pdf.py](../src/services/comparison_pdf.py) (ReportLab) produces a shareable shortlist artifact with color-coded scores, winner-row highlight, and per-resume summaries.
- ✅ Two-column outer-card primary section (Comparison Results left, Top Match right) mirroring the Analyze CV home-page hero.
- ✅ Identity-based ★ winner — the star and green row tint stay on the true top match regardless of the user's sort choice.
- ✅ JD context expander, inline meter bars in score cells, color-coded score tiers, winner-row highlight.
- ✅ One-shot scroll-to-top on report entry + return-to-compare flags so browser back lands on the compare section with the right nav highlight.

Open / future:

- Optional bounded parallelism (e.g. 2 workers) with quota-aware batching to cut wall-clock time without losing the short-circuit guarantee.
- Permalink/share for saved comparisons (currently they're listed per-user but not shareable; would need a snapshot-style URL).
- Browser-side print stylesheet as a lighter alternative to the ReportLab PDF.
