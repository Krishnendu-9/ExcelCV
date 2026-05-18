# ExcelCV — Report Page (Resume Analysis Results) — Complete Reference

This document explains the **Report page** (`?page=report`) end to end: what it shows, how it
is built, the data it consumes, the JavaScript that drives it, the CSS hooks it relies on, the
edge cases, and where to edit things. It is the page a user lands on after uploading a resume
for analysis.

File: **`src/ui/report.py`** (≈1660 lines).

---

## 1) Simple explanation

After you upload a resume + job description and the analysis runs, you land on the **report
page**. On the left there is a sticky **score card** — your resume's file name, an animated
**horizontal score bar** (0–100, coloured green / amber / red) with the score number above the
bar and the issue count below it, a collapsible
"How this score is calculated" breakdown, and an accordion of four categories
(**Content**, **Sections**, **ATS Essentials**, **Insights**) with per-check status badges.
On the right are four matching **group cards**, each holding collapsible **detail cards** for
every check (ATS Parse Rate, Quantifying Impact, …). Clicking a check in the sidebar scrolls
to and expands its detail card. At the bottom of the report: **download** the report as PDF or
JSON, an **"↻ Upload another resume"** button, and a collapsed **"Model evaluation
(project benchmark)"** tool (human-vs-model MAE / RMSE / correlation — for the project write-up).

---

## 2) Where it lives in the app

- Routed from `app.py`: when `st.session_state["page"] == "report"`, `app.py` calls
  `render_report_view()` (imported from `src.ui.report`).
- The page is reachable via `?page=report&rid=<snapshot_id>`. On a fresh session, `app.py`
  restores the analysis from the in-memory snapshot store (`_restore_report_snapshot`); if no
  analysis can be restored, it redirects to `home`.
- It is **not** an auth-protected page in itself, but a report only renders if there is an
  `analysis` in session (or a restorable snapshot). The snapshot is written/refreshed on every
  report render so a browser refresh keeps you on the report.
- `__init__.py` re-exports `render_report_page`, `_build_sidebar_html`, `_build_sidebar_js`
  from this module; `ui_components.py` re-exports `render_report_page` for back-compat.

---

## 3) Public functions (the two entry points)

### `render_report_view() -> None`  (page-level)
1. Reads `analysis = st.session_state.get("analysis")` and `name = st.session_state.get("cv_name", "CV")`.
2. If there is no analysis → `st.info(...)`, set `page = "home"`, drop the `rid` query param, `return`.
3. Refreshes the report snapshot (`_save_report_snapshot(...)`), sets `?page=report&rid=<sid>`
   so a refresh preserves the report.
4. Calls **`render_report_page(analysis, name=name)`** (the actual report UI).
5. Renders the end-of-report actions in a `st.columns([1, 1.6])` row (aligned under the main
   report lane): an **"↻ Upload another resume"** button + a collapsed
   `st.expander("Model evaluation (project benchmark)")` wrapping `render_evaluation_toolkit(analysis, name)`.
6. If "Upload another resume" was clicked → `_clear_analysis_state(clear_comparison=True)`,
   `page = "upload-cv"`, drop `rid`, `st.rerun()`. (The rerun is fired at the function's top
   level, after the layout `with` blocks have closed.)

### `render_report_page(analysis, name="CV") -> None`  (the report body)
Builds and renders the two-column report. Steps below.

---

## 4) Data contract — what the page reads out of `analysis`

`analysis` is the dict produced by `analyze_cv_with_gemini()` in `src/gemini_client.py`
(deterministic scoring from `src/services/scoring.py` merged with Gemini's qualitative output).
The report page consumes:

| Key | Shape | Used for |
|---|---|---|
| `match_score` | int 0–100 | the score ring + "Your Score" |
| `subscores` | `{skills_alignment, experience_alignment, ats_readiness}` | fallback category scores |
| `score_breakdown` | `{final_score, mode, content_average, components:[{id,label,score,weight,weighted_points}], formula}` | the "How this score is calculated" card |
| `content_metrics` | `{ats_parse_rate:int, quantifying_impact:{...}, repetition:{...}, spelling_grammar:{...}, bullets_consistency:{...}}` | the **Content** group + sidebar items |
| `sections_metrics` | `{score:int, details:{has_contact, has_experience, has_education, has_skills, has_summary, missing_sections:[...]}, section_order:{score, status, message, level, detected_order:[...]}}` | the **Sections** group |
| `contact_info` | `{found:[{type,label,value}], missing:[{label,message}], score:int}` | the "Contact Information" card |
| `ats_essentials_metrics` | `{score:int, details:{file_format:{...}, email_check:{...}, header_links:{...}, issues:[...], file_name_check:{score,status,file_name,issues:[...],suggested,name_token_count}}}` | the **ATS Essentials** group |
| `strengths`, `missing_skills`, `missing_keywords`, `suggestions` | `list[str]` | the **Insights** group + sidebar items |

`recruiter_snapshot`, `priority_action_plan`, `interview_prep`, `learning_roadmap`,
`portfolio_checklist`, `jd_skill_matrix`, `rewrite_recommendations` are still produced by
`gemini_client.py` and live in `analysis` (and are used by the downloadable PDF/JSON export
via `src/services/reporting.py`), but **they are no longer rendered on the report page** — the
Insights category was trimmed to just Strengths / Missing Skills / Missing Keywords /
Suggestions.

### Sub-metric dict shapes used by the detail cards

- `quantifying_impact`: `{score, status, details, total_lines, quantified_count, non_quantified_lines:[...]}`
- `repetition`: `{score, status, details, repeated_words:[{word,count,suggestions:[...]}]}`
- `spelling_grammar`: `{score, status, details, issues_list:[{label,count,examples:[...]}]}`
- `bullets_consistency`: `{score, status, details, total_bullets, out_of_range:[{line,words,issue}], min_words, max_words}` (the 15–45-word check; `status="ok"` + neutral message when too few bullets detected)
- `section_order`: `{score, status, message, level("entry"|"experienced"|"unknown"), detected_order:[...]}`
- `file_format` (under `ats_essentials_metrics.details`): `{is_pdf, is_docx, is_supported_format, size_ok, file_name, file_size_kb}`
- `email_check`: `{found, email, is_professional}`
- `header_links`: `{has_links, links:[...], has_full_url}`
- `file_name_check`: `{score, status, file_name, issues:[...], suggested, name_token_count}`

If a key is absent (e.g. an old saved analysis pre-dating a feature), the matching card
renders a graceful "Not assessed" state and the sidebar sub-item is omitted.

---

## 5) Layout

`render_report_page` renders `sidebar, main = st.columns([1, 1.6], gap="large")`.

```
┌─ report page ──────────────────────────────────────────────────────────┐
│ ┌─ sidebar (sticky) ──────┐  ┌─ main (the four group cards) ─────────┐ │
│ │ score-card              │  │ Content       (5 detail cards)        │ │
│ │  · file name            │  │ Sections      (3 detail cards)        │ │
│ │  · animated score ring  │  │ ATS Essentials(5 detail cards)        │ │
│ │  · "N issues"           │  │ Insights      (4 detail cards)        │ │
│ │ "How this score is      │  │ Download Reports (PDF / JSON)         │ │
│ │  calculated" (collapsed)│  │ ↻ Upload another resume               │ │
│ │ category accordion ×4   │  │ "Model evaluation" (collapsed)        │ │
│ └─────────────────────────┘  └───────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

There is **no separate header row** above the report (it used to show a "RESUME REPORT —
STANDARD SCORING" label + the big file name + a score pill + an Upload button) — that was
removed so the score card is visible at first glance; the file name moved into the score card
and the score pill was dropped (the ring already shows the score).

### 5.1 Sidebar  (`_build_sidebar_html(score, issues, categories, score_breakdown=None, cv_name="")`)

Returns **one HTML string** that is then collapsed to a continuous block
(`"\n".join(line.lstrip() for line in html.splitlines() if line.strip())`) before being passed
to `st.markdown(..., unsafe_allow_html=True)` — this matters: if any line is blank or
indented ≥4 spaces, Streamlit's markdown can misread it as an indented code block and dump the
raw HTML on screen, so the sidebar is emitted as a single uninterrupted HTML block.

Structure:
- `<div class="report-sidebar">` — sticky (`position: sticky; top: var(--excelcv-report-top, 96px)`), `overflow-y: auto`, `max-height: calc(100vh - top - 12px)`. Goes static below 1100px (`@media (max-width: 1099px)`).
  - `<div class="score-card">`:
    - `<div class="score-file">` — the resume file name (`cv_name`), HTML-escaped, ellipsis-truncated; omitted if empty.
    - `<div class="score-title">Your Score</div>`.
    - `<div class="report-score-ring-wrap" style="--rsr-c:<colour>;">` — `--rsr-c` is the score colour: **green `#10b981`** if score ≥ 80, **amber `#f59e0b`** if ≥ 60, **red `#ef4444`** otherwise. The wrap is a `flex-direction: column` container (`max-width: 300px`, auto height) — no fixed square box.
      - `<div class="report-score-ring" style="--hv-p:<score>%;">` — a 12px-tall **horizontal progress bar** (`border-radius: 999px`). The fill is driven by a single linear gradient with a hard stop at `--hv-p`: `linear-gradient(90deg, var(--rsr-c) 0%, var(--rsr-c) var(--hv-p), var(--bg-secondary) var(--hv-p))`. Animated 0→`score`% via `@keyframes hv-sweep` + `@property --hv-p` (registered as `<percentage>` so the custom-property interpolation is smooth) — same engine as the homepage hero panel's bar; respects `prefers-reduced-motion`. CSS `order: 2` so it sits visually below the label.
      - `<div class="report-score-ring-label">` — `flex-direction: row` with `flex-wrap: wrap`. `.rsr-num` (the score) and `.rsr-den` ("/ 100") sit on one row above the bar; `.issues-text.rsr-issues` ("N issues") has `flex-basis: 100%` so it wraps onto its own line below them. The issues span has class `clickable` + `data-section-id="suggestions"` when `issues > 0`, so clicking it scrolls to the Suggestions card.
  - the **"How this score is calculated"** card — `_build_score_breakdown_html(score_breakdown)`: a `<div class="detail-card section-anchor score-breakdown-card collapsed" id="score-breakdown">` with a `<h3>` (+ a `▼` chevron in the markup) and a `{final_score}%` badge; body is a one-line explanation (mode: `jd_aligned` / `no_jd`, content average %) plus a "Weighted score breakdown" box with one `.contact-row` per component (`{label} — {score}% × {weight} = {weighted_points}`). **Collapsed by default** (the `collapsed` class is in the markup, not just applied by JS).
  - one `<div class="category">` per category. Each has:
    - `<div class="category-head" id="cat-head-<id>">` — `<span class="category-title">` (title + a `▼` `.category-chevron` when there are sub-items) and `<span class="category-score <class>">{pct}%</span>` where `<class>` = `get_score_color_class(pct)` → `score-good` / `score-medium` / `score-low`.
    - `<div class="category-items collapsed" id="cat-items-<id>">` — one `.subitem` per check: `<span class="subitem-icon">` (`✓` for `ok`, `✗` otherwise) + the label + a `.badge`. Sub-items have class `clickable` + `data-section-id="<anchor>"` (unless status is `lock`) so clicking scrolls to the matching detail card.
    - Sub-item badge text rules: for **Content-style metrics** (label in `{"ATS Parse Rate","Quantifying Impact","Repetition","Spelling & Grammar","Bullets Consistency"}`) the badge is always `"{score}%"`; otherwise — `warn`/`error` → `"N issue"`/`"N issues"` (or `"Review"`), `ok` → `"No issues"`, `lock` → `"Locked"`.

`categories` is `[("Content", content_score, content_items_list), ("Sections", sections_score, sections_items_list), ("ATS Essentials", ats_essentials_score, ats_items_list), ("Insights", insights_score, insights_items_list)]`. Each `*_items_list` entry is a `(label, status, value_or_None)` tuple.

### 5.2 Main lane  (the four group cards)

`render_report_page` builds:
- `content_score` = mean of `[ats_parse_rate, quantifying_impact.score, repetition.score, spelling_grammar.score]`, plus `bullets_consistency.score` when present (so Content is a 4- or 5-way average). This mirrors the "Content Quality" component in `score_breakdown` (`calculate_final_score_breakdown` does the same).
- `sections_score` = `sections_metrics.score`. `ats_essentials_score` = `ats_essentials_metrics.score`.
- `insights_score` = `round(100 × clean_areas / 4)` where `clean_areas` = `(1 if strengths) + (1 if no missing skills) + (1 if no missing keywords) + 1` (Suggestions is informational, never an issue).
- Per-group issue counts: `content_issue_count` (ATS parse < 80 → +1; each of quant/repetition/spelling/bullets that isn't `ok` → `+max(1, len(its issue list))`), `sections_issue_count` (`len(missing_sections) + len(contact_missing) + (1 if section_order is "warn")`), `ats_issue_count` (file-format not OK → +1; `+len(design issues)`; bad email → +1; no header links → +1; `+len(file_name_check.issues)` when flagged), `insights_issue_count` (`len(missing_skills) + len(missing_keywords)`).
- Four `_build_group_card(title, group_id, issues_found, body_html)` cards. `_build_group_card` returns `<div class="report-group">` with `<div class="report-group-head" id="group-head-<id>">` (`<h3>{title}</h3>` + a `.report-group-pill` reading `"N issues found"` / `"No issues found"`) and `<div class="report-group-body">{body}</div>`. The body HTML is whitespace-normalised first (each line stripped, blanks dropped).
- The cards, in order:
  - **Content** (`group-content`): `_build_ats_parse_rate_html` → `_build_quantifying_impact_html` → `_build_repetition_html` → `_build_spelling_grammar_html` → `_build_bullets_consistency_html`.
  - **Sections** (`group-sections`): `_build_essential_sections_html` → `_build_contact_information_html` → `_build_sections_order_html`.
  - **ATS Essentials** (`group-ats-essentials`): `_build_file_format_size_html` → `_build_design_html` → `_build_email_address_html` → `_build_header_links_html` → `_build_file_name_check_html`.
  - **Insights** (`group-insights`): `strengths_html` → `missing_skills_html` → `missing_kw_html` → `suggestions_html` (all four built with `_build_list_card`).
- These four are wrapped: `report_main_html = '<div class="report-main">' + '<div class="report-group-wrap">{content}</div>' + ...sections... + ...ats... + ...insights... + '</div>'`, then `st.markdown(report_main_html, unsafe_allow_html=True)`.
- Then `_render_download_buttons(name, analysis)`.

---

## 6) Detail-card builders

Every detail card is a `<div class="detail-card section-anchor" id="<anchor>"><div class="detail-head"><h3>Title</h3><span class="badge badge-...">…</span></div><div class="section-body">…</div></div>`. They're collapsible — `_build_sidebar_js` adds a `▼` `.detail-chevron` to each `<h3>` and collapses them; the sidebar sub-items / the "N issues" line scroll to a card's `id` and expand it.

| Builder | Card title (`id`) | What it shows |
|---|---|---|
| `_build_score_breakdown_html(score_breakdown)` | **How this score is calculated** (`score-breakdown`) | weighted-component breakdown — *rendered in the sidebar*, collapsed by default |
| `_build_ats_parse_rate_html(ats_val)` | **ATS Parse Rate** (`ats-parse-rate`) | progress bar + "Great! We parsed X%…" / "improve formatting" |
| `_build_quantifying_impact_html(quant_impact)` | **Quantifying Impact** (`quantifying-impact`) | progress bar + list of non-quantified bullets, or "well quantified" |
| `_build_repetition_html(repetition)` | **Repetition** (`repetition`) | progress bar + repeated words with suggested synonyms, or "good variety" |
| `_build_spelling_grammar_html(spelling_grammar)` | **Spelling & Grammar** (`spelling-grammar`) | progress bar + issue list with examples, or "no significant errors" |
| `_build_bullets_consistency_html(bullets_consistency)` | **Bullets Consistency** (`bullets-consistency`) | progress bar + bullets outside 15–45 words ("too short"/"too long"), "all within range", or "Not assessed"; carries a "(based on detected bullet lines)" disclaimer |
| `_build_essential_sections_html(sections_details)` | **Essential Sections** (`essential-sections`) | Contact / Experience / Education / Skills / Summary present-or-missing checklist |
| `_build_contact_information_html(found, missing)` | **Contact Information** (`contact-information`) | found contact items + any missing ones with a hint |
| `_build_sections_order_html(section_order)` | **Sections Order** (`sections-order`) | "Detected order: Summary → … "; the experience-level-aware advice ("lead with Education" for entry-level + Experience-first / "put Experience above Education" for experienced + Education-first); "looks well-suited"; or "Not assessed". Carries a "(based on detected section headers)" disclaimer |
| `_build_file_format_size_html(file_format_info)` | **File Format & Size** (`file-format-size`) | file name, size in KB, PDF/DOCX support, "good job" / "use PDF" |
| `_build_email_address_html(email_check_info)` | **Email Address** (`email-address`) | email found?, is it professional?, advice |
| `_build_header_links_html(header_links_info)` | **Header Links** (`header-links`) | LinkedIn / GitHub / portfolio links in the header; "full link detected" / "partial" / "none found" |
| `_build_file_name_check_html(file_name_check)` | **File Name Check** (`file-name-check`) | current file name; "looks clean", or the issues (numbers/dates, extra periods, spaces/special chars, generic words, incomplete name) + a suggested `FirstNameLastName.pdf`; or "Not assessed" |
| `_build_list_card(title, items, section_id, badge_type, badge_label, icon, empty_msg)` | generic | a titled list of strings with an icon per row, or `empty_msg` — used for **Strengths**, **Missing Skills**, **Missing Keywords (ATS)**, **Suggestions** |

---

## 7) The sidebar JavaScript  (`_build_sidebar_js()`)

Rendered via `components.html(_build_sidebar_js(), height=0)` from inside the sidebar column.
It runs in the parent document (`var win = window.parent; var doc = win.document;`) and:

- **Category accordion** — `toggleCategory(id)` opens one category at a time (`closeOtherCategories`); all start collapsed. Clicks on `.category-head[id^="cat-head-"]` toggle.
- **Detail-card collapse** — `prepareDetailCards()` finds every `.detail-card`, appends a `.detail-chevron` to its `<h3>` (unless already present), makes the `.detail-head` keyboard-activatable (`role="button"`, `tabindex="0"`), and collapses all of them. `toggleDetailCard` / `expandDetailCard` / `collapseDetailCard` flip the `collapsed`/`expanded` classes (CSS animates `max-height`/`opacity`). Clicks on `.detail-card .detail-head` toggle; Enter/Space on a focused head toggles too.
- **Scroll-to** — `scrollToSection(sectionId)`: finds `#sectionId`, expands its containing `.detail-card`, `scrollIntoView({behavior:'smooth'})`, and briefly flashes the background. Triggered by clicks on `.subitem[data-section-id]` and `.issues-text[data-section-id]`.
- **Sticky-top sync** — `computeStickyTop()` measures the site header (`[data-testid="stHorizontalBlock"]:has(.site-brand)`) and sets `--excelcv-report-top` on `<html>`, so `.report-sidebar { top: var(--excelcv-report-top, 96px) }` parks the sidebar just below the header. `syncStickyTop()` runs on scroll/resize (rAF/debounced); on desktop it may `pinSidebar`/`unpinSidebar` (a `position: fixed` fallback) and clamps the bottom against the footer. Below 1100px the sidebar is left static.
- **Lifecycle** — installs a single capture-phase `click` (and `keydown`) listener on `doc`; a `MutationObserver` on `doc.body` re-runs init when Streamlit re-renders; `win.__excelcvSidebarCleanup` tears down listeners/observers/timers on the next run so nothing leaks across reruns. `initContent()` runs once (guarded by `initDone`), with retries at 40/220/700 ms.

---

## 8) `_render_download_buttons(name, analysis)`

Renders `### Download Reports` then a `st.columns(2)` row:
- **Download PDF Report** — `st.download_button(data=build_report_pdf_bytes(name, analysis), file_name="...-report.pdf", mime="application/pdf")` (`build_report_pdf_bytes` lives in `src/services/reporting.py`; falls back to a text dump if WeasyPrint isn't installed).
- **Download JSON Export** — `st.download_button(data=json.dumps(analysis, indent=2), file_name="...-analysis.json", mime="application/json")`.

---

## 9) `render_evaluation_toolkit(analysis, resume_name)`  (the project benchmark)

Now rendered **inside a collapsed `st.expander("Model evaluation (project benchmark)")`** at
the bottom of `render_report_view`. It is a model-validation tool for the final-project write-up:

- A caption explaining it adds human-review scores to validate the model (MAE / RMSE / correlation).
- A `st.form("evaluation_form", clear_on_submit=True)`: **Human reviewer score (0–100)** number input + an optional **Reviewer notes** text input + an **Add benchmark record** submit.
- On submit: appends `build_evaluation_record(resume_name, model_score=analysis["match_score"], human_score, notes)` to `st.session_state["evaluation_records"]`.
- If there are records: a `st.columns(4)` of metrics (**Records**, **MAE**, **RMSE**, **Correlation**) from `summarize_evaluation(records)`, a `st.dataframe(records)`, and a **Download benchmark JSON** button.

`build_evaluation_record` / `summarize_evaluation` come from `src/services/evaluation.py`.
The records live only in session state (not persisted).

---

## 10) Helpers & imports used by this module

- From `src/ui/common.py`: `issue_count(analysis)` (total issue count for the score card),
  `get_score_color_class(score)` (`score-good`/`score-medium`/`score-low`),
  `_markdown_inline_to_html` (used by `_build_list_card` to render inline markdown in list items).
- Local: `_escape_html(value)` — a minimal `& < >` escaper for embedding user text in the
  hand-built HTML.
- From `src/services/reporting.py`: `build_report_pdf_bytes`.
- From `src/services/evaluation.py`: `build_evaluation_record`, `summarize_evaluation`.
- From `src/ui/app_utils.py`: `_clear_analysis_state`, `_save_report_snapshot`.

---

## 11) CSS hooks (defined in `src/assets/ui/base_theme.css.tpl` + `src/ui/css_injection.py`)

- Layout: `.report-sidebar` (sticky), `.score-card`, `.score-card .score-file`,
  `.report-main`, `.report-group-wrap`, `.report-group`, `.report-group-head`,
  `.report-group-pill`, `.report-group-body`.
- Score bar: `.report-score-ring-wrap` (flex column, auto height, `max-width: 300px`),
  `.report-score-ring` (horizontal 12px bar with linear-gradient fill driven by `--hv-p`),
  `.report-score-ring-label` (flex row, wraps issues span to its own line via `flex-basis: 100%`),
  `.rsr-num`, `.rsr-den`, `.rsr-issues`; `@property --hv-p` (declared at the top of the hero-panel
  CSS block — `syntax: '<percentage>'; inherits: false; initial-value: 92%;`) +
  `@keyframes hv-sweep` (shared with the homepage hero panel — animates `--hv-p` from 0%);
  `--rsr-c` set inline per render. The class names (`*-score-ring*`) are historical from the
  original donut design — the markup is now a horizontal bar.
- Sidebar accordion: `.category`, `.category-head` (`.expanded`), `.category-title`,
  `.category-chevron`, `.category-items` (`.collapsed`/`.expanded`), `.subitem` (`.clickable`),
  `.subitem-icon` (`.icon-ok`/`.icon-warn`), `.subitem-label-wrap`.
- Detail cards: `.detail-card` (`.collapsed`/`.expanded`), `.detail-head`
  (`.detail-head-collapsible`), `.detail-chevron`, `.section-body`, `.section-body-item`,
  `.text-description`, `.score-breakdown-card` (the sidebar variant).
- Inner pieces: `.badge` (`.badge-ok`/`.badge-warn`/`.badge-lock`), `.issue-card`
  (`.good-card`), `.issue-heading`, `.issue-desc`, `.issue-item`, `.issue-x`, `.repeat-group` /
  `.repeat-word-tag` / `.repeat-label` / `.repeat-suggestion`, `.spell-issue-row` / `.spell-tag`,
  `.contact-row` / `.contact-icon` (`.found`/`.missing`) / `.contact-label` / `.contact-sep` /
  `.contact-value` / `.contact-msg`, `.progress-track.dark` / `.progress-fill.dark`.
- CSS variable: `--excelcv-report-top` (written by the sidebar JS; consumed by `.report-sidebar { top: … }`).
- **Now-unused** (left over from the removed header row, harmless): `.report-topline`,
  `.report-fileline`, `.report-mode-label`, `.report-file-row`, `.report-file-title`,
  `.score-pill`, `#report-pdf-row-marker`, `#report-top-actions-marker` — candidates for a future cleanup pass.

---

## 12) Edge cases & known limitations

- **No analysis in session** → `render_report_view` shows an info message and redirects to `home`.
- **Old saved analyses** that pre-date a metric (Bullets Consistency, Sections Order, File Name
  Check) → those cards show a "Not assessed" state and the matching sidebar sub-item is omitted;
  the category averages fall back to the older formula. Re-running the analysis populates them.
- **Snapshots are in-memory** — `_save_report_snapshot` stores into a `@st.cache_resource`
  dict, so a shared `?rid=` link survives reruns but **not** a server restart. (Production: move
  to DB-backed snapshots.)
- **Heuristic checks** — Bullets Consistency relies on detecting experience bullets, and
  Sections Order relies on detecting section headers + inferring experience level, both from
  text extracted from a PDF/DOCX; extraction quirks (merged lines, stripped bullet markers,
  multi-column read order) can mislead them, so both **fail soft** (neutral "ok" / "Not
  assessed" when uncertain) and each card states it works from "detected" content.
- **`recruiter_snapshot` / `priority_action_plan` / `interview_prep` / `learning_roadmap` /
  `portfolio_checklist` / `jd_skill_matrix` / `rewrite_recommendations`** are still computed and
  remain in `analysis` (used by the PDF/JSON export) but are intentionally **not shown** on the
  report page anymore — the Insights category was slimmed to Strengths / Missing Skills /
  Missing Keywords / Suggestions.
- The sidebar HTML must stay a single blank-line-free HTML block (see §5.1) or `st.markdown`
  will render it as literal text.

---

## 13) Where to edit

| To change… | Edit |
|---|---|
| The score card / score bar / file-name line / "N issues" link | `_build_sidebar_html` in `src/ui/report.py`; bar + `.score-file` CSS in `src/assets/ui/base_theme.css.tpl` (`.report-score-ring*` selectors — class names are historical, markup is now a horizontal bar) |
| The category accordion (which checks appear, badge text) | `render_report_page` (`*_items_list` building) + `_build_sidebar_html` (the `is_content_metric` set / badge logic) |
| The "How this score is calculated" card | `_build_score_breakdown_html`; the underlying numbers come from `calculate_final_score_breakdown` in `src/services/scoring.py` |
| A specific detail card's content | the matching `_build_<x>_html` in `src/ui/report.py` |
| Which detail cards appear in a group / their order | `render_report_page` (the `_build_group_card(...)` bodies) |
| The category % / issue-count formulas | `render_report_page` (`content_score` / `insights_score` / `*_issue_count`) |
| Sidebar interactivity (accordion, collapse, scroll-to, sticky offset) | `_build_sidebar_js` in `src/ui/report.py` |
| Download buttons / PDF content | `_render_download_buttons` here; PDF builder in `src/services/reporting.py` |
| The evaluation/benchmark tool | `render_evaluation_toolkit` here; metrics in `src/services/evaluation.py` |
| The end-of-report layout (Upload button, eval expander, header removal) | `render_report_view` in `src/ui/report.py` |
| The underlying scores/metrics themselves | `src/services/scoring.py` (`calculate_*`), `src/gemini_client.py` (`content_metrics` / `sections_metrics` / `ats_essentials_metrics` assembly) |
| Routing to this page / snapshot restore | `app.py` (`page == "report"`, `_restore_report_snapshot`) |
