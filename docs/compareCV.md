# Compare Resumes Page (`compare-cv`) Documentation

## 1) Purpose

The **Compare Multiple Resumes (2-5 files)** section lets a signed-in user:

- paste one job description,
- upload multiple resumes,
- run the same analysis pipeline for each file,
- view ranked side-by-side results.

This is used for candidate shortlisting and quick ATS/JD-fit comparison.

---

## 2) Where It Lives

Primary implementation files:

- `app.py`
- `src/ui/upload.py`
- `src/ui/analysis_runner.py`
- `src/ui/layout.py`
- `src/ui/app_utils.py`
- `src/auth_utils.py`
- `src/ui/css_injection.py`

Core route key:

- `compare-cv`

---

## 3) Routing + Navigation Behavior

### Route ownership

- `app.py` treats `compare-cv` as a protected page.
- If unauthenticated, user is routed to auth and returned after login.

### Navbar integration

- Top nav label: **Compare Resumes**
- Nav action maps to home page + compare anchor for smooth in-page landing.
- Active highlight is synchronized with compare focus state.

### Anchor behavior

- Anchor ID: `compare-section-anchor`
- Compare mode now scrolls once per entry context (not on every rerun), reducing jumpiness.

---

## 4) UI Structure in `src/ui/upload.py`

Inside `render_upload_page(compare_mode: bool = False)`:

1. Hero/upload area (single CV flow) renders first.
2. Compare section anchor and shell render next.
3. Compare form is inside `st.container(key="compare_form_box")`.
4. Results table + summary metrics render below form.
5. "What happens next?" helper card renders below results.

Main compare heading:

- `Compare Multiple Resumes (2-5 files)`

---

## 5) Auth States

### Signed-in user

Shows form:

- `compare_jd` (text area)
- `compare_cvs` (multi file uploader)
- submit button (`Run comparison`)

### Guest user

Shows locked CTA card:

- "Sign in to compare resumes"
- link to auth route with `next_page="compare-cv"`

No comparison computation executes for guests.

---

## 6) Input Validation Rules

Validation is handled in `run_multi_resume_comparison()`:

- Job description is required (non-empty trimmed text).
- Minimum files: 2
- Maximum files: 5
- Duplicate uploaded files are deduplicated primarily by `(sanitized_filename_lower, file_size, sha256(file_bytes))`, with filename+size fallback when hashing is unavailable.
- If deduplication leaves fewer than 2 unique files, request is rejected.
- Each file is still validated by shared payload analyzer (`_analyze_cv_payload`), including size and extraction checks.

Max file size per file:

- controlled by `MAX_FILE_BYTES` / `MAX_FILE_MB` from `src/config.py`.

---

## 7) Comparison Processing Pipeline

Per file:

1. Extract text (`extract_cv_text`)
2. Run LLM analysis (`analyze_cv_with_gemini`)
3. Normalize/scalar values:
   - final score
   - JD alignment
   - ATS parse
   - sections score
   - issue count
   - top missing skills

Output row fields:

- `Rank`
- `Resume`
- `Final Score`
- `JD Alignment`
- `ATS Parse`
- `Sections`
- `Issues`
- `Top Missing Skills`

Sorting:

1. Final Score descending
2. Issues ascending
3. Resume name ascending

---

## 8) Session State Keys (Compare Flow)

Primary keys:

- `comparison_results`
- `comparison_errors`
- `comparison_warnings`
- `comparison_signature`
- `compare_jd`
- `compare_cvs`

Support keys:

- `scroll_to_compare_anchor`
- `_compare_mode_anchor_scrolled`

### Signature-based stale-result protection

- Current input signature = normalized JD + sorted `(file_name, file_size)` tokens.
- If signature changes after previous run, old results are cleared and user is prompted to rerun.

---

## 9) Result Rendering

When results exist:

- metrics row:
  - Resumes Compared
  - Top Score
  - Average Score
- comparison dataframe with stable column order
- `Download comparison CSV` button exports the visible table
- success banner for top match
- `Clear comparison results` button to reset compare session state

When issues occur:

- `comparison_errors` shown as warning list
- `comparison_warnings` shown as info list (e.g., skipped duplicates)

---

## 10) Clear/Reset Behavior

Comparison state is cleared in:

- local compare clear button in `upload.py`
- `_clear_analysis_state(clear_comparison=True)` in `app_utils.py`
- `logout_user()` in `auth_utils.py`

This prevents stale comparison artifacts across logout/reset/navigation paths.

---

## 11) Styling Hooks (CSS)

Key selectors:

- `.st-key-compare_section_shell`
- `.st-key-compare_form_box`
- `.compare-mode-badge`
- `.compare-results-title`
- `.compare-next-shell`
- `.compare-next-title`
- `.compare-next-list`

Most compare styling is centralized in `src/ui/css_injection.py`.

---

## 12) Known Constraints

- Streamlit reruns the script on interactions; navigation is optimized but not true SPA behavior.
- Comparison rows are not currently persisted as first-class DB entities (single-CV report persistence is separate).

---

## 13) QA Checklist (Recommended)

Functional:

- Signed-in compare run with 2 files works.
- Signed-in compare run with 5 files works.
- 1 file shows validation error.
- 6 files shows validation error.
- Empty JD shows validation error.
- Duplicate file upload triggers warning and skips duplicates.
- Results reorder correctly by score.
- CSV download contains the same rows and column order as the table.

State/rerun:

- Changing JD after run clears stale results prompt.
- Changing file set after run clears stale results prompt.
- Clear button removes table + banners.
- Logout clears compare state.

Auth:

- Guest sees sign-in CTA.
- Guest cannot run comparison.
- Post-login returns to compare route when requested from compare CTA.

---

## 14) Quick Improvement Backlog

- Persist comparison sessions/history per user.
- Add expandable per-resume "why this score" details under table.
