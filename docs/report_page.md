# ExcelCV - Report Page Reference

This document describes the current `?page=report` implementation.

Primary file: `src/ui/report.py`

## 1) What the page shows

After analysis is complete, the report page renders:

- Left sticky sidebar:
  - Resume file name
  - Score bar (0-100)
  - Issue count
  - Collapsed "How this score is calculated" card
  - Category accordion: Content, Sections, ATS Essentials, Insights
- Right main lane:
  - Group cards for Content, Sections, ATS Essentials, Insights
  - Detail cards under each group
  - Download buttons (PDF and JSON)
- Bottom actions:
  - "Upload another resume" button
  - Collapsed "Model evaluation (project benchmark)"

## 2) Routing and lifecycle

- `app.py` routes to `render_report_view()` when `st.session_state["page"] == "report"`.
- URL format is `?page=report&rid=<snapshot_id>`.
- Snapshot restore is handled by app/session helpers.
- `render_report_view()` refreshes snapshot id on every render.

If no analysis exists:

- Shows info message
- Switches page to `home`
- Removes `rid` from query params

## 3) Entry points

### `render_report_view()`

- Reads `analysis` and `cv_name` from session state
- Refreshes report snapshot id
- Calls `render_report_page(analysis, name)`
- Renders bottom actions (Upload another resume + evaluation expander)

### `render_report_page(analysis, name="CV")`

- Builds sidebar + main content from `analysis`
- Computes category scores and issue counts
- Renders detail cards and downloads

## 4) Analysis data contract consumed by report page

Main keys used:

- `match_score`
- `subscores`
- `score_breakdown`
- `content_metrics`
- `sections_metrics`
- `contact_info`
- `ats_essentials_metrics`
- `strengths`
- `missing_skills`
- `missing_keywords`
- `suggestions`

Other keys may exist in `analysis` (for export and other tooling), but are not displayed as separate report sections.

## 5) Category logic

### Content

Built from:

- ATS Parse Rate
- Quantifying Impact
- Repetition
- Spelling and Grammar
- Bullets Consistency (when present)

### Sections

Built from:

- Essential Sections
- Contact Information
- Sections Order

### ATS Essentials

Built from:

- File Format and Size
- Design
- Email Address
- Header Links
- File Name Check

### Insights (current behavior)

Built from:

- Strengths
- Missing Skills
- Missing Keywords
- Suggestions

Current code behavior:

- `Suggestions` is treated as `warn` when non-empty.
- `Suggestions` affects `insights_score` and `insights_issue_count`.

This is important because older docs described Suggestions as informational-only. That is not the current code behavior.

## 6) Group card markup

Group cards are built by `_build_group_card(...)`.

Current markup:

- Wrapper has `id="group-<name>"` via function argument.
- Header uses class `report-group-head`.
- Header does **not** include `id="group-head-<id>"`.

## 7) Detail card builders in `report.py`

Main detail builders include:

- `_build_ats_parse_rate_html`
- `_build_quantifying_impact_html`
- `_build_repetition_html`
- `_build_spelling_grammar_html`
- `_build_bullets_consistency_html`
- `_build_essential_sections_html`
- `_build_contact_information_html`
- `_build_sections_order_html`
- `_build_file_format_size_html`
- `_build_design_html`
- `_build_email_address_html`
- `_build_header_links_html`
- `_build_file_name_check_html`
- `_build_list_card` (used for strengths, missing skills, missing keywords, suggestions)

## 8) Sidebar JavaScript behavior

`_build_sidebar_js()` handles:

- Category accordion open/close
- Detail card collapse/expand
- Scroll to section from sidebar clicks
- Sticky top offset sync with site header
- Observer/listener cleanup on reruns

## 9) Downloads

`_render_download_buttons(name, analysis)` renders:

- Download PDF report
- Download JSON export

## 10) Evaluation toolkit

`render_evaluation_toolkit(analysis, resume_name)` is shown in a collapsed expander.

It supports:

- Human reviewer score input
- Optional notes
- Session-based benchmark record list
- MAE/RMSE/correlation summary
- Benchmark JSON download

## 11) Re-export notes

- `src/ui/__init__.py` re-exports `render_report_page`, `_build_sidebar_html`, `_build_sidebar_js`.
- `src/ui/ui_components.py` also re-exports these for backward compatibility.

## 12) Known caveats

- Snapshot storage is in-memory; restart clears restorable `rid` state.
- Heuristic sections (for example bullets consistency and section order) depend on extraction quality.
- Older saved analyses may not contain newer sub-metrics; report handles missing keys gracefully.

## 13) Where to edit

- Layout/behavior: `src/ui/report.py`
- Scoring inputs and metric generation: `src/services/scoring.py`, `src/gemini_client.py`
- Snapshot routing/restore: `app.py`, `src/ui/app_utils.py`
- CSS styling: `src/assets/ui/base_theme.css.tpl`
