# Resume Builder: Implementation Reference (Current)

This document describes the actual current behavior of the Resume Builder page, including UI controls, state keys, section/card behavior, calendar behavior, preview behavior, and data flow.

## Scope
- Route: `?page=cv-builder` (and alias `?page=resume-builder`)
- Main file: `src/ui/cv_builder_page.py`
- Page entry: `render_cv_builder_page()`

## Runtime Flow
1. Initialize state in `_init_builder()`.
2. Load selected CV (if requested) via `_load_cv_for_builder_if_requested()`.
3. Inject page styles via `_inject_builder_css_native(...)` and `_inject_middle_section_exact_css()`.
4. Build editor data with `collect_cv_data()`.
5. Pre-generate PDF bytes via `_cached_generate_cv_pdf(...)`.
6. Render toolbar + 3-panel workspace.
7. Re-collect data after middle panel render and paint right preview.
8. Inject JS bridges (`_inject_realtime_js()`, `_inject_sections_relay_js()`, `_inject_chevron_hider_js()`).

## Page Layout
Three columns:
1. Left panel: sections list, templates, style controls.
2. Middle panel: section editors (cards with custom headers, add buttons, chevron collapse).
3. Right panel: preview zoom controls + resume preview iframe.

## Canonical Sections
Section schema:
- `personal` → Personal Information
- `summary` → Professional Summary
- `experience` → Work Experience
- `education` → Education
- `skills` → Skills
- `projects` → Projects
- `languages` → Languages
- `certifications` → Certifications
- `interests` → Interests

Default order in UI (`CVR_SECTION_ORDER`):
1. personal
2. summary
3. experience
4. education
5. skills
6. projects
7. languages
8. certifications
9. interests

## Section Visibility vs Section Collapse
There are two different controls:

1. Left sidebar eye control (`cvb_section_visibility`):
- Hides/shows an entire section globally.
- Hidden sections are not shown in middle editor and not rendered in preview.

2. Middle panel chevron (`cvb_section_open_<section_id>`):
- Collapses/expands section body only.
- Section remains visible in list and preview logic.

All sections are initialized expanded by migration keys:
- `cvb_sections_open_default_v1`
- `cvb_sections_open_default_v2`
- `cvb_sections_open_default_v3`

## Header Add Buttons
Section headers include add buttons for:
- Experience: `Add Position`
- Education: `Add Education`
- Skills: `Add Skill`
- Projects: `Add Project`
- Languages: `Add Language`
- Certifications: `Add Certification`

The header add handler initializes all required keys for each new row to avoid partial state.

## Row Seeds (Initial Visible Rows)
The editor seeds default rows so sections are immediately usable:
- Experience: 1 row (plus 1 bullet)
- Education: 1 row
- Skills: 3 rows
- Projects: 1 row
- Languages: 1 row
- Certifications: 1 row
- Interests: no seed list item (free-add style)

## Row-Level Eye Toggle (Hide Without Delete)
For card rows that have delete buttons, an eye toggle is present:
- Experience rows: `vis_exp_<id>`
- Education rows: `vis_edu_<id>`
- Skills rows: `vis_skill_<id>`
- Projects rows: `vis_proj_<id>`
- Languages rows: `vis_lang_<id>`
- Certifications rows: `vis_cert_<id>`

Behavior:
- Eye open (`:material/visibility:`): row is included in CV output.
- Eye closed (`:material/visibility_off:`): row remains editable in form but is excluded from preview/PDF data.

Visibility keys:
- `cvb_exp_visible_<id>`
- `cvb_edu_visible_<id>`
- `cvb_skill_visible_<id>`
- `cvb_proj_visible_<id>`
- `cvb_lang_visible_<id>`
- `cvb_cert_visible_<id>`

Initialized by:
- seed paths
- add-row paths
- load-from-DB path
- migration `cvb_item_visibility_defaults_v1`

## Delete Buttons
Delete buttons are standardized to icon style matching Work Experience card actions:
- `:material/delete:`
- `type="tertiary"`
- shared compact icon-button CSS and red hover feedback

Applies to:
- experience rows
- education rows
- skills rows
- projects rows
- languages rows
- certifications rows

Note:
- Experience bullet delete uses close icon (`:material/close:`) and remains separate from row delete.

## Section-by-Section Editor Behavior

### Personal Information
- Full Name
- Professional Title
- Email / Phone
- Location / Website
- LinkedIn / GitHub

### Professional Summary
- Text area (`max_chars=500`, height `130`)
- Live counter (`<count>/500`)

### Work Experience
Each row has:
- Header actions: `Duplicate`, eye toggle, delete
- Job Title, Company
- Start Date (month/year popover)
- End Date (month/year popover + Present toggle inside popover)
- Location
- Description
- Key Achievements bullets:
  - inline bullet rows
  - add bullet
  - remove bullet with stable shifting logic (prevents key holes)

Duplicate behavior:
- Inserts cloned row immediately below source row.
- Clones role/company/location/start/end/current/description and bullets.
- New row visibility defaults to visible.

### Education
Each row has:
- Header actions: eye toggle, delete (delete shown when more than one row exists)
- Degree
- Institution / Location
- Start Date (month/year popover)
- End Date (month/year popover + Present toggle inside popover)
- Description (stored in `cvb_edu_gpa_<id>` field key)

### Skills
Each row has:
- Skill input
- Eye toggle
- Delete

Starts with three empty rows on first use.

### Projects
Each row has:
- Header actions: eye toggle, delete
- Project Name / Your Role
- Date (month/year popover)
- Description
- Technologies (comma-separated string)
- Project Link

### Languages
Each row has:
- Language input
- Proficiency select (`Basic`, `Intermediate`, `Advanced`, `Fluent`, `Native`)
- Eye toggle
- Delete

Important data rule:
- Row is only included in CV output when Language name is non-empty.

### Certifications
Each row has:
- Header actions: eye toggle, delete
- Title
- Issuer
- Date (month/year popover)
- Credential URL

### Interests
- Existing interests shown as readonly rows with delete
- Add input + Add button
- No row-level eye toggle currently

## Date Picker (Month/Year Popover)
Used by experience/education/project/certification dates.

Display:
- Field label rendered above the clickable popover trigger.
- Trigger shows:
  - `MM/YYYY` when empty
  - stored value like `03/2024` when selected
  - `Present (Current)` when current toggle is on

Popover layout:
- Left: Month grid (12 buttons, Jan–Dec, 4x3)
- Right: Year grid in scroll container

Year range:
- Starts from `current year + 1`
- 48 years total
- 3 columns
- compact scrollable year area

Actions:
- Select month/year writes `MM/YYYY` to storage key
- `Clear` resets month/year (and resets current toggle if present-enabled field)
- Optional `Present (Current)` toggle appears for end dates where `allow_present=True`

For present-enabled end date:
- When toggled ON:
  - stored date is cleared
  - field display becomes `Present (Current)`
- When toggled OFF:
  - user selects month/year again

## Realtime and Rerun Behavior
- Streamlit reruns on widget interactions.
- Realtime bridge JS updates preview fields quickly for personal/contact interactions.
- After middle panel renders, app re-collects data (`cv_data_live = collect_cv_data()`) so row-level button actions appear immediately in preview on same rerun.

## Preview Data Source Rules
Function: `_build_preview_source(cv_data)`

1. If CV is effectively empty:
- Show demo resume content (template visibility aid).

2. If user has meaningful content:
- Show user data.

Effective-empty check uses `_is_cv_data_effectively_empty(...)`, with row-level meaningful-data checks and current language blank-name guard.

## Data Collection Contract (`collect_cv_data`)
`collect_cv_data()` builds normalized dict for preview/save/PDF:
- `personal`
- `experience`
- `education`
- `skills` (`items` + `categories`)
- `projects`
- `certifications`
- `languages`
- `interests`
- `customization`

Filtering behavior:
- Any row with row-eye OFF is excluded.
- Skills include only non-empty names.
- Languages include only rows with non-empty language name.
- Experience bullets include only non-empty bullet text.

## Left Panel Component Relay
Left panel uses HTML component + hidden relay buttons:
- Section reorder
- Section eye hide/show
- Template switch
- Style controls

Before relay clicks, JS commits active input value (`input`/`change` + blur) to reduce value-loss during reruns.

## Templates and Zoom
Templates:
- `classic`
- `creative`
- `modern`

Default zoom for each template: `100`.

Zoom steps:
- `35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100`

## Save / Load / Backup / Import / Reset
- Save: `_save_cv(...)`
- Load DB CV: `load_cv_into_builder(...)`
- Backup JSON: `_get_backup_json()`
- Import JSON: `_import_from_json(...)`
- Reset all builder keys: `_reset_all()`

Toolbar buttons:
- Import
- Backup
- Save
- Download PDF
- Reset

## PDF Generation
Pipeline:
1. Build preview source.
2. Generate HTML with active renderer.
3. Wrap print CSS.
4. Render to PDF (Playwright-based).

Goal: keep PDF output aligned with on-screen preview.

## Active Definitions Note
`src/ui/cv_builder_page.py` contains older duplicate definitions kept for historical compatibility.

Python uses the last definition for each function name, so runtime behavior is governed by the last active definitions in the file.

## Practical QA Checklist
1. All sections are open on first load.
2. Chevron can collapse/expand each section.
3. Left sidebar eye hides/shows whole section.
4. Row eye hides row from preview without deleting data.
5. Delete removes row data from state.
6. Month/year popovers are compact and usable.
7. End-date present toggle works in experience and education.
8. Demo CV appears when user data is empty.
9. Typing updates preview in expected rerun cycle.
10. Downloaded PDF matches visible preview content/visibility.
