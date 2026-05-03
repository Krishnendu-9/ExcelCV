# Resume Builder Page Documentation

This document explains the Resume Builder page implementation in this repository, based on the current code.

## Primary file

- `src/ui/cv_builder_page.py`

## Related files

- `app.py` (routing and page mount)
- `src/ui/layout.py` (global header and shared layout shell)
- `src/ui/css_injection.py` (global CSS that can affect builder layout)

## Where this page is rendered

In `app.py`, when `current_page` is `cv-builder` or `resume-builder`, the app calls:

- `render_cv_builder_page()`

The page is protected by auth via `_require_auth('cv-builder')`.

## High-level architecture

The active Resume Builder UI is the native 3-panel implementation:

1. Left panel: section list, visibility toggles, template selection, style controls
2. Middle panel: editable section forms
3. Right panel: live CV preview with zoom controls

The page is mostly state-driven through `st.session_state` keys prefixed by `cvb_`.

## Core constants and schema

Defined near top of `src/ui/cv_builder_page.py`:

- `SECTION_SCHEMA`
- `SECTION_IDS`
- `SECTION_ID_TO_LABEL`
- `SECTION_LABEL_TO_ID`
- `CVR_SECTION_ORDER` (default section order)
- `TEMPLATE_CONFIGS`
- `TEMPLATE_CHOICES`
- `ACCENT_COLORS`
- `FONT_OPTIONS`
- `PROFICIENCY_OPTIONS`

## Session state contract

`_init_builder()` initializes all required `cvb_*` keys.

### Core UI/state keys

- `cvb_cv_title`
- `cvb_template`
- `cvb_loaded_cv_id`
- `cvb_last_saved`
- `cvb_confirm_reset`
- `cvb_show_import`
- `cvb_zoom`
- `cvb_preview_fullscreen`

### Styling keys

- `cvb_accent_color`
- `cvb_font`
- `cvb_font_size`
- `cvb_line_height`
- `cvb_entry_spacing`
- `cvb_show_icons`
- `cvb_show_photo`

### Section control keys

- `cvb_section_order`
- `cvb_section_visibility`
- `cvb_active_section`

### Personal fields

- `cvb_full_name`
- `cvb_prof_title`
- `cvb_email`
- `cvb_phone`
- `cvb_location`
- `cvb_website`
- `cvb_linkedin`
- `cvb_github`
- `cvb_summary`

### Dynamic list keys

- Experience: `cvb_exp_ids`, per-item `cvb_exp_*`, bullet counters `cvb_exp_bcount_*`
- Education: `cvb_edu_ids`, per-item `cvb_edu_*`
- Skills: `cvb_skill_cat_ids`, per-item `cvb_skill_*`
- Projects: `cvb_proj_ids`, per-item `cvb_proj_*`
- Certifications: `cvb_cert_ids`, per-item `cvb_cert_*`
- Languages: `cvb_lang_ids`, per-item `cvb_lang_*`
- Interests: `cvb_interests`, `cvb_interest_ctr`

## Normalization helpers

- `_normalize_template(template)`
- `_section_id(value)`
- `_normalize_section_order(order)`
- `_normalize_section_visibility(visibility)`

These are critical for stability when loading older backups, migrating schema, or handling mixed label/id inputs.

## Data flow

### 1. Initialization and load

- `render_cv_builder_page()`
  - calls `_init_builder()`
  - calls `_load_cv_for_builder_if_requested()`

### 2. Build data model from state

- `collect_cv_data()` composes a structured CV dict from session state.

### 3. Render UI

- `_inject_builder_css_native(is_dark)` injects page-level CSS for the builder layout.
- Toolbar rendered (saved status, import, backup, download PDF, reset).
- 3 columns rendered with ratio `[1.2, 3.5, 2.2]` and `gap="small"`.
- Panel renderers:
  - `_render_left_panel_native()`
  - `_render_middle_panel_native()`
  - `_render_right_panel_native(cv_data, is_dark)`

### 4. Real-time bridge

- `_inject_realtime_js()` injects JS bridge for immediate in-preview updates for selected fields.

## Left panel behavior

Implemented in `_render_left_panel_native()`.

### Sections list

- Source order: `cvb_section_order` normalized by `_normalize_section_order`.
- Visibility source: `cvb_section_visibility` normalized by `_normalize_section_visibility`.
- Optional drag sort via `streamlit_sortables`:
  - import attempt at module top:
    - `from streamlit_sortables import sort_items as sortable_items`
  - if unavailable, caption informs user drag reorder is not enabled.
- Each row includes:
  - section button (sets `cvb_active_section`)
  - eye toggle button (updates `cvb_section_visibility[section_id]`)

### Template controls

- Uses `TEMPLATE_CHOICES`.
- Active template in `cvb_template`.

### Style controls

- Accent color swatches
- Font scale slider (`cvb_font_size`)
- Spacing slider (`cvb_entry_spacing`)
- Line-height slider (`cvb_line_height`)
- Toggles (`cvb_show_icons`, `cvb_show_photo`)

## Middle panel behavior

Implemented in `_render_middle_panel_native()`.

- Resolves section order and visibility.
- Computes:
  - `visible_order = [sid for sid in order if visibility.get(sid, True)]`
- If nothing visible, shows info message.
- Renders only visible sections, in `visible_order`.
- Each section is rendered in an always-expanded `st.expander`.

### Section render map

- `personal -> _personal_section`
- `summary -> _summary_section`
- `experience -> _experience_section`
- `education -> _education_section`
- `skills -> _skills_section`
- `projects -> _projects_section`
- `languages -> _languages_section`
- `certifications -> _certifications_section`
- `interests -> _interests_section`

## Right panel behavior

Implemented in `_render_right_panel_native(cv_data, is_dark)`.

- Zoom controls update `cvb_zoom`.
- Calls `generate_cv_html(...)` with:
  - data
  - selected template/style values
  - `section_visibility`
  - `section_order`
- Wraps generated body in a preview document and renders with:
  - `components.html(preview_doc, height=1450, scrolling=False)`

## Section ordering and visibility rules

The final behavior is controlled by `cvb_section_order` and `cvb_section_visibility`.

### Middle panel

- Driven by `_render_middle_panel_native()` using `visible_order`.
- Hidden sections do not render.

### Preview panel

- Driven by `generate_cv_html(...)`.
- Uses normalized `order` and `vis`.
- Skips `personal` as a body section because personal data is represented in header/contact area.

If a section is moved in left ordering, middle and preview should follow that order.
If a section is hidden, it should be omitted from both middle and preview.

## CV HTML generator

`generate_cv_html(...)` is the preview/paper renderer.

### Inputs

- `data`
- `template`
- `accent_color`
- `font_family`
- `font_size`
- `line_height`
- `entry_spacing`
- `preview_dark`
- `section_visibility`
- `section_order`

### Output

- Full HTML string for CV page
- Includes template-specific header variants
- Generates section blocks only when:
  - section is visible
  - section content is non-empty

## Save, backup, import, reset

- `_save_cv(cv_data, title, template)` writes to DB (`CV` model)
- `_get_backup_json()` exports all `cvb_*` keys
- `_import_from_json(uploaded_file)` restores `cvb_*` keys
- `_reset_all()` removes all `cvb_*` keys and reruns

## PDF generation

- `_cached_generate_cv_pdf(...)` wraps `generate_cv_pdf(...)`
- Called during page render to power toolbar download button
- Uses `st.cache_data(show_spinner=False)`

## CSS layering

Two builder CSS systems exist in file:

1. Legacy CSS injector: `_inject_builder_css(is_dark)` (not used by active render path)
2. Active CSS injector: `_inject_builder_css_native(is_dark)` (used by current page)

The native CSS sets:

- Page height and fixed block behavior
- Toolbar dimensions and button visuals
- 3-panel heights
- Panel scroll behavior and custom scrollbars
- Left rail cards/sortable styles
- Expander and form controls styling

## JS injectors in file

- `_inject_realtime_js()` is active in current render path.
- `_inject_persistent_scrollbar_js()` exists but is not called by current native renderer.

## Legacy/deprecated code currently present

The file still contains deprecated functions that return immediately:

- `_render_left_panel()` (legacy)
- `_render_right_panel()` (legacy)

There are also legacy non-executing fragments in the native path, for example:

- A no-op loop in `_render_left_panel_native()`:
  - `for sec_id in []: ...`

These are not active logic but are dead code candidates.

## Interaction with global CSS

`inject_file_uploader_spacing_css()` in `src/ui/css_injection.py` is intended for upload/comparison forms.
It now scopes major spacing rules to:

- `.st-key-upload_form`
- `.st-key-comparison_form`

This is important to avoid unintentional Resume Builder layout side effects.

## Current known dependency

Optional drag-and-drop section sorting requires:

- `streamlit-sortables`

If not installed, the page still works, but drag reordering UI is disabled and a caption is shown.

## Quick function index (active path)

- `_init_builder()`
- `_load_cv_for_builder_if_requested()`
- `collect_cv_data()`
- `_inject_builder_css_native(is_dark)`
- `_render_left_panel_native()`
- `_render_middle_panel_native()`
- `_render_right_panel_native(cv_data, is_dark)`
- `_inject_realtime_js()`
- `render_cv_builder_page()`

## Summary

The current Resume Builder is a state-driven Streamlit page with a native 3-panel layout, shared section-order/visibility state, live HTML preview generation, and export/import/save tooling. The middle and preview panels are both driven by the same section metadata (`cvb_section_order`, `cvb_section_visibility`) so section movement and hide/show behavior stay synchronized.

