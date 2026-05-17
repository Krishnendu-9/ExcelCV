# Compare Resumes Page (`compare-cv`) Documentation

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
- `src/ui/upload.py`              (compare form + run dispatcher)
- `src/ui/compare_report.py`      (dedicated ranked results page + drill-down)
- `src/ui/analysis_runner.py`     (`run_multi_resume_comparison` orchestration)
- `src/ui/app_utils.py`           (`_clear_comparison_run_artifacts`, snapshot store)
- `src/auth_utils.py`             (logout cleanup)
- `src/ui/css_injection.py`       (compare-specific styling)

Route keys:

- `compare-cv`     — form page (currently anchored inside the main upload page)
- `compare-report` — dedicated ranked results page (protected)

---

## 3) Routing + Navigation Behavior

### Route ownership

- `app.py` treats `compare-report` as a protected page. `compare-cv` redirects to the upload page anchored at the compare section.
- If unauthenticated, user is routed to auth and returned after login.

### Navbar integration

- Top nav label: **Compare Resumes**
- Nav action maps to the upload page + compare anchor for smooth in-page landing.
- Active highlight is synchronized with compare focus state via an `IntersectionObserver` scroll-spy.

### Anchor behavior

- Anchor ID: `compare-section-anchor`
- Compare mode scrolls once per entry context (not on every rerun) to reduce jumpiness.

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

Support keys:

- `scroll_to_compare_anchor`

### Signature-based stale-result protection

- Current input signature = normalized JD + sorted `(file_name, file_size)` tokens.
- If signature changes after the previous run, `_clear_comparison_run_artifacts()` is called and the user is prompted to rerun. Because the unified helper also clears `comparison_attempted`, the report page's empty state correctly reads as "no comparison yet" instead of "your last run produced 0 rows".

---

## 9) Result Rendering

All result rendering lives on the dedicated `compare-report` page (`src/ui/compare_report.py`).

When results exist:

- hero with hero chips (resumes compared, top score, average score)
- top-match card with score, bar, per-metric strip, and top missing skills chips
- comparison dataframe with stable column order (`_analysis` is hidden)
- **per-resume drill-down expanders** under the table, each with: per-metric tiles, summary, top missing skills chips, suggestions list, missing keywords
- `Download CSV` button exports the visible columns only
- `Clear results` button resets compare run artifacts and navigates back to the form

When the run was attempted but no rows were produced:

- empty state copy reflects the attempt and the per-file error list explains why (rate limit, unreadable PDF, empty file, etc.)

When issues occur:

- `comparison_errors` shown as warning list
- `comparison_warnings` shown as info list (e.g. skipped duplicates, quota short-circuit)

---

## 10) Clear/Reset Behavior

Two helpers handle compare cleanup; the lifecycle ownership lives in `app_utils.py`:

- `_clear_comparison_run_artifacts()` (app_utils) — pops `comparison_results`, `comparison_errors`, `comparison_warnings`, `comparison_signature`, `comparison_attempted`. Leaves form inputs alone. Used by both the form (on input change) and the report page (`Clear results`).
- `_clear_comparison_session_state()` (upload.py) — full reset: calls the helper above AND clears `compare_upload_warnings`, `compare_jd`, `compare_selected_files`, `compare_cvs_rev`, and any `compare_cvs_input_*` widget keys.
- `_clear_analysis_state(clear_comparison=True)` (app_utils) — uses the unified helper internally so the lifecycle stays consistent across analyze/compare flows.
- `logout_user()` (auth_utils) — clears every comparison key, including `comparison_attempted` and `compare_upload_warnings`.

---

## 11) Styling Hooks (CSS)

Key selectors:

- `.st-key-compare_section_shell`
- `.st-key-compare_form_box`
- `.compare-mode-badge`
- `.compare-results-title`
- `.compare-drilldown-title`
- `.compare-progress-shell`, `.compare-progress-list`, `.compare-progress-item--{running,done,error,skipped}`
- `.compare-next-shell`, `.compare-next-title`, `.compare-next-list`
- `.compare-top-card__*`

All compare styling is centralized in `src/ui/css_injection.py`.

---

## 12) Known Constraints

- Streamlit reruns the script on interactions; navigation is optimized but not true SPA behavior.
- Comparison rows are not currently persisted as first-class DB entities (single-CV report persistence is separate).
- Sequential model calls — see § 7 for the quota-driven rationale.

### Gemini rate-limit (quota) short-circuit

If `analyze_cv_with_gemini` raises a 429 / quota / "resource exhausted" error mid-run, every remaining file is short-circuited as `skipped` rather than burning more quota. Both the per-file error list and a top-level warning explain what happened, and the progress UI shows the affected files as `skipped (rate limit)`.

---

## 13) QA Checklist (Recommended)

Functional:

- Signed-in compare run with 2 files works and lands on the dedicated report page.
- Signed-in compare run with 5 files works.
- 1 file shows validation error on the form, no navigation.
- 6 files attempted via uploader: warning shows that extras were skipped; run with the first 5 still works.
- Empty JD shows validation error.
- Duplicate file upload triggers warning and skips duplicates at the form stage.
- Per-file progress card updates live during the run (running → done/error/skipped).
- Results reorder correctly by score.
- CSV download contains the same rows and column order as the table (no `_analysis` column leakage).
- Drill-down expanders render summary, suggestions, and missing keywords from the stored analysis dict.

State/rerun:

- Changing JD after a run clears stale results AND `comparison_attempted` — re-entering report shows "no comparison yet", not the attempted-empty copy.
- Changing file set after a run clears stale results prompt.
- `Clear results` on the report page removes table + banners and bounces to the form.
- Logout clears every compare key (including `comparison_attempted` and `compare_upload_warnings`).

Auth:

- Guest sees sign-in CTA.
- Guest cannot run comparison.
- Post-login returns to compare route when requested from compare CTA.

Quota:

- Simulated 429 on file 2 of 4 leaves files 3 and 4 marked as `skipped (rate limit)` in both the progress UI and the report's per-file error list.

---

## 14) Quick Improvement Backlog

- Persist comparison sessions/history per user (database table + my-comparisons page).
- Optional bounded parallelism (e.g. 2 workers) with quota-aware batching to cut wall-clock time without losing the short-circuit guarantee.
- "Open as single report" action from each drill-down so users can jump into the full single-CV report flow for any compared resume.
