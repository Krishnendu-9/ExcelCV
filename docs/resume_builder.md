# Resume Builder: Current Behavior and Implementation Guide

This document is the source of truth for the current Resume Builder behavior in this repository.

## Scope
- Page route: `?page=cv-builder` and `?page=resume-builder`
- Main implementation file: `src/ui/cv_builder_page.py`
- Entry function: `render_cv_builder_page()`
- Goal: CVReviewer-like editing experience with three synchronized panels and WYSIWYG PDF output

## Runtime Entry Flow
1. `render_cv_builder_page()` initializes builder state via `_init_builder()`.
2. Optional DB load is handled via `_load_cv_for_builder_if_requested()`.
3. Page-level CSS is injected via `_inject_builder_css_native(is_dark)`.
4. Current builder data is assembled via `collect_cv_data()`.
5. PDF bytes are precomputed via `_cached_generate_cv_pdf(...)`.
6. Toolbar + 3-column workspace are rendered.
7. Realtime JS bridges are injected:
- `_inject_realtime_js()` for live preview updates.
- `_inject_sections_relay_js()` for component postMessage -> hidden button routing.

## Layout Model
The page uses a 3-panel layout with fixed-height scroll regions.

1. Left panel (`cvb-left-scroll-native`)
- Sections list (reorder + hide/show)
- Templates
- Style controls

2. Middle panel (`cvb-middle-scroll-native`)
- Section editors in expanders

3. Right panel (`cvb-right-scroll-native`)
- Fixed zoom toolbar at top
- Scrollable preview canvas below

## Section Schema
Canonical section ids and labels:
- `personal`: Personal Information
- `summary`: Professional Summary
- `experience`: Work Experience
- `education`: Education
- `skills`: Skills
- `projects`: Projects
- `languages`: Languages
- `certifications`: Certifications
- `interests`: Interests

Default section order (`CVR_SECTION_ORDER`):
1. personal
2. summary
3. experience
4. education
5. skills
6. projects
7. languages
8. certifications
9. interests

## Templates
Template choices and left-rail card order:
1. `classic` (Single column, ATS-friendly)
2. `creative` (Colored sidebar)
3. `modern` (Two-column sidebar)

Template default zoom:
- classic: `65%`
- creative: `100%`
- modern: `90%`

## Builder State Contract (`st.session_state`)
Primary keys:
- `cvb_cv_title`, `cvb_template`, `cvb_loaded_cv_id`, `cvb_last_saved`
- `cvb_show_import`, `cvb_confirm_reset`, `cvb_zoom`

Style keys:
- `cvb_accent_color`
- `cvb_font`
- `cvb_font_size`
- `cvb_line_height`
- `cvb_entry_spacing`
- `cvb_show_icons`

Section control keys:
- `cvb_section_order`
- `cvb_section_visibility`
- `cvb_active_section`

Personal fields:
- `cvb_full_name`, `cvb_prof_title`, `cvb_email`, `cvb_phone`
- `cvb_location`, `cvb_website`, `cvb_linkedin`, `cvb_github`, `cvb_summary`

Dynamic list keys:
- Experience: `cvb_exp_ids`, per-item `cvb_exp_*`
- Education: `cvb_edu_ids`, per-item `cvb_edu_*`
- Skills: `cvb_skill_ids`, per-item `cvb_skill_item_*`
- Projects: `cvb_proj_ids`, per-item `cvb_proj_*`
- Certifications: `cvb_cert_ids`, per-item `cvb_cert_*`
- Languages: `cvb_lang_ids`, per-item `cvb_lang_*`
- Interests: `cvb_interests`

Compatibility note:
- `cvb_show_photo` may still exist in state for backward compatibility, but photo toggle UI is intentionally removed from active style panel.

## Data Normalization Rules
- `_normalize_template(...)` maps invalid/legacy values to valid template keys.
- `_normalize_section_order(...)` deduplicates and fills missing ids.
- `_normalize_section_visibility(...)` ensures full `{section_id: bool}` map.

## Left Panel Behavior
Left panel interactive components use `components.html` and a relay pattern.

### Relay Pattern
1. Component posts message: `window.parent.postMessage(...)`.
2. `_inject_sections_relay_js()` listens in parent context.
3. Relay finds hidden Streamlit button and clicks it.
4. Python handler updates state and triggers rerun.

### Hidden Buttons
Hidden controls are rendered inside `st.container(key="cvb-hidden-buttons")`.

Supported hidden actions:
- Reorder: `cvb_pos_{sid}_{pos}`
- Eye toggle: `cvb_eye_{sid}`
- Template select: `cvb_tpl_{template}`
- Accent select: `cvb_acc_{index}`
- Font scale: `cvb_scale_{80..130}`
- Line height: `cvb_lh_{10..20}`
- Spacing: `cvb_es_{0..24 step 2}`
- Icons toggle: `cvb_icons_toggle`

### Input-Commit Safety Before Relay Click
The relay now commits currently-focused text input before clicking hidden buttons.

Behavior:
- Dispatches `input` and `change`
- Blurs active `input/textarea`
- Waits briefly
- Clicks hidden button

Why:
- Prevents loss of in-progress typed values when style/template/section actions rerun the app.
- This specifically fixes the `Show icons` toggle wiping unsaved text.

### Sections Component
`_render_sections_list_component(...)` provides:
- Drag handle reorder
- Eye visibility toggle
- CVReviewer-like list styling

### Template Component
`_render_template_component(...)` provides:
- Card list for Classic / Creative / Modern
- Active card state styling
- Click -> `cvb-tpl-select`

### Style Component
`_render_style_component(...)` provides:
- Accent color swatches
- Font scale slider
- Line height slider
- Spacing slider
- Show icons toggle

No Show Photo toggle is rendered in active UI.

## Middle Panel Behavior
`_render_middle_panel_native()` renders visible sections only.

Section renderer map:
- `personal` -> `_personal_section`
- `summary` -> `_summary_section`
- `experience` -> `_experience_section`
- `education` -> `_education_section`
- `skills` -> `_skills_section`
- `projects` -> `_projects_section`
- `languages` -> `_languages_section`
- `certifications` -> `_certifications_section`
- `interests` -> `_interests_section`

If all sections are hidden, an info message is shown.

## Right Panel Behavior
`_render_right_panel_native(cv_data, is_dark)`:
- Reads current template/style/visibility/order
- Builds `preview_source = _build_preview_source(cv_data)`
- Generates HTML via `generate_cv_html(...)`
- Wraps it in a zoom shell
- Renders via `components.html(..., scrolling=False)`

Zoom controls:
- Toolbar UI comes from `_render_zoom_toolbar_component(zoom)`
- Actions are relayed to hidden zoom buttons in right panel
- Zoom levels: `[35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]`

## Demo-to-User Content Switching
Core function: `_build_preview_source(cv_data)`

Rules:
- If builder data is effectively empty (`_is_cv_data_effectively_empty(...) == True`):
- Preview uses demo placeholders so selected layout is visible.
- If any meaningful user content exists:
- Preview uses user data only, without demo fallback.

This behavior is used consistently in:
- Live preview (`_render_right_panel_native`)
- PDF generation (`_cached_generate_cv_pdf`)

## Realtime Preview Behavior
`_inject_realtime_js()` listens to middle-panel input events and broadcasts live updates to preview iframe(s).

Realtime events:
- `cv-rt-update` for personal/contact fields
- `cv-rt-user-mode` to switch preview from demo mode to user-only mode as soon as typing starts

Key realtime guarantees:
- Name/title/contact/summary update while typing.
- Untouched personal fields are also synchronized so demo leftovers clear immediately.
- User mode is toggled on first meaningful input without waiting for blur.

## Realtime Icon Toggle Behavior
`Show icons` now has two paths:
1. Immediate client-side update:
- Relay posts `cv-rt-icons-toggle` to preview.
- Preview toggles CSS class (`icons-on` / `icons-off`) instantly.
2. Server state persistence:
- Relay clicks hidden `cvb_icons_toggle` to persist state and rerun.

This gives instant visual feedback and keeps state/PDF output consistent.

## CV HTML Rendering Rules
Active renderer: the later `generate_cv_html(...)` definition in `cv_builder_page.py`.

Important behavior:
- Builds template-accurate layout for `classic`, `creative`, `modern`.
- Applies section order and visibility from state.
- Renders sections only when they have meaningful content.
- Contact icons are always present in markup.
- Icon visibility is controlled by paper class:
- `icons-on`
- `icons-off` (`.icons-off .ci-ico { display:none !important; }`)

Skills formatting by template:
- Classic: 3-column bullet grid (`skills-cols-3`)
- Creative: 2-column bullet grid (`skills-cols-2`)
- Modern: 2-column bullet grid (`skills-cols-2`)

## Save / Load / Import / Backup / Reset
- Save: `_save_cv(cv_data, title, template)` stores CV + customization to DB.
- Load: `load_cv_into_builder(cv_record)` restores fields and list ids.
- Backup: `_get_backup_json()` exports all `cvb_*` keys.
- Import: `_import_from_json(...)` restores `cvb_*` keys and reruns.
- Reset: `_reset_all()` clears `cvb_*` keys and reruns.

Toolbar detail:
- Backup and PDF download buttons use `on_click="ignore"` to reduce needless rerun/media churn.

## PDF Pipeline (Preview-Parity First)
Entry: `_cached_generate_cv_pdf(...)` with `@st.cache_data(show_spinner=False)`.

Steps:
1. Deserialize CV and section settings.
2. Build preview source via `_build_preview_source`.
3. Render HTML via `generate_cv_html`.
4. Wrap with print CSS via `_build_pdf_ready_html`.
5. Render with Playwright Chromium.

Windows behavior:
- Uses `_render_html_to_pdf_bytes_windows_subprocess(...)`.
- Child process enforces Proactor loop policy to avoid `NotImplementedError` subprocess transport failures seen in Streamlit/Tornado environments.

Dependency requirement:
1. `py -3 -m pip install playwright`
2. `py -3 -m playwright install chromium`

## Known Runtime Messages
### `MediaFileHandler: Missing file <id>.json`
Meaning:
- Streamlit component/media ID got recycled between reruns.

Impact:
- Usually non-fatal noise; app keeps working.

Mitigations already in place:
- Reduced unnecessary rerun paths.
- `on_click="ignore"` on download buttons.
- Input commit before relay click.

### Temporary “blurred/faded” UI overlay
Meaning:
- Streamlit is processing a rerun cycle.

Impact:
- Expected transient behavior when state-changing actions run.

## Active vs Legacy Code Notes
`src/ui/cv_builder_page.py` still contains older/deprecated definitions for compatibility/history.

Practical rule:
- In Python, the last definition with the same name wins.
- Current runtime uses the later/native path (`render_cv_builder_page` + native panel renderers + latest `generate_cv_html`).

## Quick Element Behavior Matrix
| Element | Where | Behavior |
|---|---|---|
| Sections list row drag | Left panel | Reorders section ids and reruns |
| Eye icon | Left panel | Toggles section visibility and reruns |
| Template card | Left panel | Switches template, resets zoom to template default, reruns |
| Accent swatch | Left panel | Updates accent color and reruns |
| Font scale slider | Left panel | Live number in component; commits on change and reruns |
| Line height slider | Left panel | Live number in component; commits on change and reruns |
| Spacing slider | Left panel | Live number in component; commits on change and reruns |
| Show icons toggle | Left panel | Instant preview icon hide/show + persisted rerun |
| Middle text inputs | Middle panel | Realtime preview updates while typing |
| Preview zoom controls | Right toolbar | Updates zoom step and reruns |
| Download PDF | Toolbar | Exports current preview-equivalent layout/content |

## Recommended Maintenance Rule
When changing behavior in `src/ui/cv_builder_page.py`, always validate all 3 surfaces together:
1. Live preview in right panel
2. Saved DB data and restore flow
3. Downloaded PDF parity with preview
