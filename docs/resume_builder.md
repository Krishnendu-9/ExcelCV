# Resume Builder Page Documentation

This document explains the Resume Builder page implementation in this repository, based on the current code.

## CVReviewer visual parity audit (navbar excluded)

Reference used: user-provided screenshots comparing local `localhost:8501/?page=cv-builder` with `cvreviewer.net/builder`.

### Dissimilarities identified

1. **Section order mismatch (left rail + editor flow)**
- Local page default order was `Education -> Personal -> Skills -> ...`
- CVReviewer order is `Personal Information -> Professional Summary -> Work Experience -> Education -> Skills -> Projects -> Languages -> Certifications -> Interests`

2. **Toolbar icon style mismatch**
- Local page used emoji-style icons for `Import`, `Backup`, `Reset`
- CVReviewer uses thin line icons with neutral tone

3. **Preview zoom control mismatch**
- Local controls were large boxed buttons and defaulted to `95%`
- CVReviewer uses compact icon controls with a pill-style zoom label and defaults around `45%`

4. **Editor card/input styling mismatch**
- Local middle panel looked flatter and grayer with less card separation
- CVReviewer has white rounded cards, clearer borders, softer shadows, and cleaner input surfaces

5. **Left rail visual rhythm mismatch**
- Local sections/template/style blocks had tighter/smaller spacing and weaker hierarchy
- CVReviewer uses larger list rows, clearer typography, and more breathing room

6. **Summary counter text mismatch**
- Local rendered `302/500 characters`
- CVReviewer style shows compact `302/500`

### Fixes applied in this update

1. Updated default section order to CVReviewer order.
2. Added safe migration logic so legacy sessions on old default order get migrated without overriding custom user order.
3. Replaced toolbar emoji icons with SVG mask line-icons.
4. Updated toolbar/action sizing to better match CVReviewer proportions.
5. Changed default zoom to `45%` and updated zoom step levels.
6. Restyled zoom controls to compact icon buttons + pill zoom display.
7. Restyled middle panel expanders/cards/inputs for CVReviewer-like card and field appearance.
8. Improved left panel section card spacing and typography.
9. Updated style panel labels/values and spacing behavior to closer CVReviewer look.
10. Changed summary counter text to compact format (`{n}/500`).

### Remaining known gaps

1. Streamlit-native controls can still differ slightly from CVReviewer in exact pixel-level behavior (especially nested expander internals).
2. Top navbar intentionally remains project-specific as requested.

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

---

## High-level architecture

The Resume Builder is a native 3-panel implementation:

1. **Left panel** — section list with drag-to-reorder and visibility toggles, template selection cards, style controls (accent color, font scale, line height, entry spacing, icon/photo toggles)
2. **Middle panel** — editable section forms (personal, experience, education, skills, projects, languages, certifications, interests)
3. **Right panel** — live CV preview with zoom controls

All three panels share a common state through `st.session_state` keys prefixed by `cvb_`.

### Left panel rendering strategy

The left panel uses **custom HTML components** (`components.html`) for all interactive controls, rather than native Streamlit widgets. This gives full CSS control to match the CVReviewer design. All component interactions go through a **postMessage → relay → hidden Streamlit button** pattern:

1. The HTML component posts a message: `window.parent.postMessage({type: 'cvb-...', ...}, '*')`
2. A 0-height relay iframe (`_inject_sections_relay_js()`) listens on the parent document and clicks the matching hidden `st.button` DOM element
3. The hidden button handler updates `st.session_state` and calls `st.rerun()`

All hidden buttons are grouped into a single `st.container(key="cvb-hidden-buttons")` which is collapsed to `position: absolute; height: 1px; overflow: hidden` via CSS so they contribute nothing to normal page layout flow. Programmatic `.click()` calls still work through `pointer-events: none`.

---

## Core constants and schema

Defined near top of `src/ui/cv_builder_page.py`:

- `SECTION_SCHEMA` — list of `(id, label)` tuples for all 9 sections
- `SECTION_IDS` — list of section id strings
- `SECTION_ID_TO_LABEL` / `SECTION_LABEL_TO_ID` — lookup dicts
- `CVR_SECTION_ORDER` — default section order (matches CVReviewer ordering)
- `TEMPLATE_CONFIGS` — per-template color/font config dict
- `TEMPLATE_CHOICES` — list of `(key, label, description)` for the 3 templates
- `ACCENT_COLORS` — list of 8 hex color strings for swatches
- `FONT_OPTIONS` — dict of font name → CSS font-family string
- `PROFICIENCY_OPTIONS` — list of language proficiency levels
- `_SCALE_VALUES` — `[80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]` — font scale integers × 100

---

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

- `cvb_accent_color` — hex string (default `#3b82f6`)
- `cvb_font` — font name key (default `System Sans`)
- `cvb_font_size` — integer pt size (default `11`)
- `cvb_line_height` — float (default `1.4`)
- `cvb_entry_spacing` — integer px (default `8`)
- `cvb_show_icons` — bool (default `True`)
- `cvb_show_photo` — bool (default `False`)

### Section control keys

- `cvb_section_order` — list of section id strings (normalized order)
- `cvb_section_visibility` — dict of `{section_id: bool}`
- `cvb_active_section` — currently focused section id

### Personal fields

- `cvb_full_name`, `cvb_prof_title`, `cvb_email`, `cvb_phone`
- `cvb_location`, `cvb_website`, `cvb_linkedin`, `cvb_github`, `cvb_summary`

### Dynamic list keys

- Experience: `cvb_exp_ids`, per-item `cvb_exp_*`, bullet counters `cvb_exp_bcount_*`
- Education: `cvb_edu_ids`, per-item `cvb_edu_*`
- Skills: `cvb_skill_cat_ids`, per-item `cvb_skill_*`
- Projects: `cvb_proj_ids`, per-item `cvb_proj_*`
- Certifications: `cvb_cert_ids`, per-item `cvb_cert_*`
- Languages: `cvb_lang_ids`, per-item `cvb_lang_*`
- Interests: `cvb_interests`, `cvb_interest_ctr`

---

## Normalization helpers

- `_normalize_template(template)` — maps legacy names (`minimal` → `creative`) and enforces valid keys
- `_section_id(value)` — accepts either a section id or label string and returns the canonical id
- `_normalize_section_order(order)` — deduplicates and fills missing ids
- `_normalize_section_visibility(visibility)` — fills missing keys with `True`

These are critical for stability when loading older backups, migrating schema, or handling mixed label/id inputs.

---

## Data flow

### 1. Initialization and load

- `render_cv_builder_page()`
  - calls `_init_builder()`
  - calls `_load_cv_for_builder_if_requested()`

### 2. Build data model from state

- `collect_cv_data()` composes a structured CV dict from session state, including a `"customization"` sub-dict with all styling keys.

### 3. Render UI

- `_inject_builder_css_native(is_dark)` injects page-level CSS for the builder layout.
- Toolbar rendered (saved status, import, backup, download PDF, reset).
- 3 columns rendered with ratio `[1.2, 3.5, 2.2]` and `gap="small"`.
- Panel renderers:
  - `_render_left_panel_native()`
  - `_render_middle_panel_native()`
  - `_render_right_panel_native(cv_data, is_dark)`

### 4. Real-time bridge

- `_inject_realtime_js()` injects a JS bridge for immediate in-preview updates for Personal Details fields (full name and contact row).
- `_inject_sections_relay_js()` injects the relay iframe for left-panel postMessage routing.

---

## Left panel behavior

Implemented in `_render_left_panel_native()`.

### Hidden buttons container

All relay-driven buttons are rendered inside `st.container(key="cvb-hidden-buttons")`. CSS collapses this container to `position: absolute; height: 1px; overflow: hidden` so it takes no layout space. Buttons present:

| Button key pattern | Count | Purpose |
|---|---|---|
| `cvb_pos_{sid}_{pos}` | 81 (9 × 9) | Reorder: move section `sid` to position `pos` |
| `cvb_eye_{sid}` | 9 | Toggle visibility of section `sid` |
| `cvb_tpl_{key}` | 3 | Select template (`modern`, `classic`, `creative`) |
| `cvb_acc_{i}` | 8 | Select accent color at index `i` |
| `cvb_scale_{val}` | 11 | Select font scale where `val` is scale × 100 (80–130) |
| `cvb_lh_{val}` | 11 | Select line height where `val` is lh × 10 (10–20) |
| `cvb_es_{val}` | 13 | Select entry spacing in px (0, 2, 4, … 24) |
| `cvb_icons_toggle` | 1 | Toggle `cvb_show_icons` |
| `cvb_photo_toggle` | 1 | Toggle `cvb_show_photo` |

Total: 158 hidden buttons, all invisible and outside layout flow.

### postMessage relay — `_inject_sections_relay_js()`

A 0-height `components.html` iframe that runs its script in the parent-page context. It registers a `message` event listener under the key `__cvb_sections_relay__` (de-duped on each Streamlit rerun). Handled message types:

| Message type | Payload | Action |
|---|---|---|
| `cvb-eye-toggle` | `{sectionId}` | Clicks `cvb_eye_{sectionId}` button |
| `cvb-drag-end` | `{movedId, newPos}` | Clicks `cvb_pos_{movedId}_{newPos}` button |
| `cvb-tpl-select` | `{tpl}` | Clicks `cvb_tpl_{tpl}` button |
| `cvb-acc-select` | `{idx}` | Clicks `cvb_acc_{idx}` button |
| `cvb-scale-select` | `{val}` (scale × 100) | Clicks `cvb_scale_{val}` button |
| `cvb-lh-select` | `{val}` (lh × 10) | Clicks `cvb_lh_{val}` button |
| `cvb-es-select` | `{val}` (px int) | Clicks `cvb_es_{val}` button |
| `cvb-icons-toggle` | — | Clicks `cvb_icons_toggle` button |
| `cvb-photo-toggle` | — | Clicks `cvb_photo_toggle` button |

### Sections list — `_render_sections_list_component()`

A custom HTML component (`components.html`) built with SortableJS for drag-to-reorder. Each row shows:

- Drag handle (six-dot grip icon) — drag fires `cvb-drag-end` with `{movedId, newPos}`
- Section label
- Eye icon button — click fires `cvb-eye-toggle` with `{sectionId}`; icon switches between open/closed eye depending on current visibility state

The component receives `section_order` and `visibility` as Python arguments baked into the HTML at render time. It does not read session state directly. After a drag or eye toggle, the relay clicks the matching hidden button which updates session state and reruns.

The component heading reads **SECTIONS** styled via `.cvb-rail-heading` CSS class (11px, font-weight 600, letter-spacing 0.07em, uppercase, muted color) matching CVReviewer's design.

### Template cards — `_render_template_component()`

A custom HTML component rendering three template selection cards (Modern, Classic, Creative). Design matches CVReviewer: compact cards with name + description subtitle, blue ring + tinted background on the selected card.

- Click on a card posts `{type: 'cvb-tpl-select', tpl: 'modern'|'classic'|'creative'}` to parent.
- The relay clicks the matching `cvb_tpl_{key}` hidden button.
- Component height: 188px (3 cards × 54px + gaps + padding).

### Style controls — `_render_style_component()`

A custom HTML component replacing all Streamlit sliders and toggles. Design matches CVReviewer.

**Signature:**
```python
_render_style_component(
    current_accent: str,
    font_size: int,
    line_height: float,
    entry_spacing: int,
    show_icons: bool,
    show_photo: bool,
    is_dark: bool,
) -> None
```

**Controls rendered:**

| Control | Design | Interaction |
|---|---|---|
| Accent Color | 8 × 24px circular swatches, 4-per-row CSS grid, ring-2 + ring-offset-2 in blue on selected | Click → `cvb-acc-select {idx}` |
| Font Scale | 6px-track range slider, 0.80–1.30x, step 0.05; live label updates on `input` | Release → `cvb-scale-select {val×100}` |
| Line Height | 6px-track range slider, 1.0–2.0x, step 0.1; live label updates on `input` | Release → `cvb-lh-select {val×10}` |
| Entry Spacing | 6px-track range slider, 0–24px, step 2; live label updates on `input` | Release → `cvb-es-select {val}` |
| Show icons | 36×20px toggle switch with sliding thumb, blue when on | Click → `cvb-icons-toggle` |
| Show photo | 36×20px toggle switch with sliding thumb, blue when on | Click → `cvb-photo-toggle` |

Scale-to-`cvb_font_size` mapping: `cvb_font_size = round(val / 100.0 * 11)` (e.g. scale 100 → 11pt, 80 → 9pt).
Display conversion: `scale = round((font_size / 11.0) / 0.05) * 0.05`.

Component height: 330px.

### Section headings

Headings between sections (SECTIONS / TEMPLATES / STYLE) are rendered via:
```python
st.markdown("<p class='cvb-rail-heading'>Sections</p>", unsafe_allow_html=True)
```

CSS for `.cvb-rail-heading`: 11px, font-weight 600, letter-spacing 0.07em, uppercase, `#64748b` (light) / `#94a3b8` (dark), no extra margin above.

Dividers between sections use `.cvb-rail-divider` (1px border-top, muted color, 8px vertical margin).

---

## Middle panel behavior

Implemented in `_render_middle_panel_native()`.

- Resolves section order and visibility.
- Computes: `visible_order = [sid for sid in order if visibility.get(sid, True)]`
- If nothing visible, shows info message.
- Renders only visible sections in `visible_order`.
- Each section rendered in an always-expanded `st.expander`.

### Section render map

| Section id | Renderer |
|---|---|
| `personal` | `_personal_section` |
| `summary` | `_summary_section` |
| `experience` | `_experience_section` |
| `education` | `_education_section` |
| `skills` | `_skills_section` |
| `projects` | `_projects_section` |
| `languages` | `_languages_section` |
| `certifications` | `_certifications_section` |
| `interests` | `_interests_section` |

---

## Right panel behavior

Implemented in `_render_right_panel_native(cv_data, is_dark)`.

- Zoom controls update `cvb_zoom`.
- Calls `generate_cv_html(...)` with data, template, style values, `section_visibility`, `section_order`.
- Wraps generated body in a preview document and renders with `components.html(preview_doc, height=1450, scrolling=False)`.

---

## Section ordering and visibility rules

The final behavior is controlled by `cvb_section_order` and `cvb_section_visibility`.

### Middle panel

- Driven by `_render_middle_panel_native()` using `visible_order`.
- Hidden sections do not render.

### Preview panel

- Driven by `generate_cv_html(...)`.
- Uses normalized `order` and `vis`.
- Skips `personal` as a body section because personal data is represented in the header/contact area.

If a section is moved in left ordering, middle and preview both follow. If a section is hidden, it is omitted from both middle and preview.

---

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
- Includes template-specific header variants (classic, modern, creative)
- Generates section blocks only when section is visible and content is non-empty
- `#cv-name` and `#cv-contact` DOM ids are present in all templates to support real-time preview updates via the postMessage JS bridge

---

## Save, backup, import, reset

- `_save_cv(cv_data, title, template)` — writes to DB (`CV` model), rolls back on DB error
- `collect_cv_data()` — includes `"customization"` sub-dict (`accent_color`, `font`, `font_size`, `line_height`, `entry_spacing`) so all style settings persist with saved CVs
- `load_cv_into_builder(cv_record)` — restores all five customization fields from `data["customization"]` when loading a saved CV
- `_get_backup_json()` — exports all `cvb_*` keys as JSON
- `_import_from_json(uploaded_file)` — restores `cvb_*` keys from JSON
- `_reset_all()` — removes all `cvb_*` keys and reruns

---

## PDF generation

- `_cached_generate_cv_pdf(...)` wraps `generate_cv_pdf(...)` with `@st.cache_data(show_spinner=False)`
- PDF bytes are only rebuilt when CV data actually changes, not on every Streamlit rerun
- All user-supplied text is XML-escaped before embedding in ReportLab `Paragraph` markup to prevent parse errors on `<`, `>`, `&` characters

---

## CSS layering

Two builder CSS systems exist in the file:

1. **Legacy CSS injector**: `_inject_builder_css(is_dark)` — not used by active render path
2. **Active CSS injector**: `_inject_builder_css_native(is_dark)` — used by current page

The native CSS sets:

- Page height and fixed block behavior
- Toolbar dimensions and button visuals
- 3-panel heights, scroll behavior, and custom scrollbars
- Left rail heading (`.cvb-rail-heading`) and divider (`.cvb-rail-divider`) styles
- Hidden buttons container collapse (`.st-key-cvb-hidden-buttons`)
- Left panel padding with `!important` to win specificity over general `stVerticalBlock` rules
- `[data-testid="InputInstructions"]` hidden to suppress the "Press Enter to apply" tooltip

---

## JS injectors in file

| Function | Active | Purpose |
|---|---|---|
| `_inject_sections_relay_js()` | Yes | Routes all postMessage events from left-panel components to hidden Streamlit buttons |
| `_inject_realtime_js()` | Yes | Real-time personal details preview update (name + contact row) without a full rerun |
| `_inject_persistent_scrollbar_js()` | No (no-op) | Deprecated; native panel scrollbars used instead |

---

## Legacy/deprecated code currently present

- `_render_left_panel()` — legacy renderer, returns immediately
- `_render_right_panel()` — legacy renderer, returns immediately
- A no-op `for sec_id in []:` loop inside `_render_left_panel_native()` — dead code candidate

---

## Interaction with global CSS

`inject_file_uploader_spacing_css()` in `src/ui/css_injection.py` scopes major spacing rules to `.st-key-upload_form` and `.st-key-comparison_form` to avoid unintentional Resume Builder layout side effects.

---

## Current known dependency

Optional drag-and-drop section sorting in `_render_sections_list_component()` requires SortableJS, which is bundled inside the component HTML string (loaded from CDN or inline). No Python package dependency. If the CDN is unreachable, drag sorting silently degrades (sections still reorderable via the relay buttons if called from other paths).

---

## Quick function index (active path)

| Function | Description |
|---|---|
| `_init_builder()` | Initialize all `cvb_*` session state defaults |
| `_load_cv_for_builder_if_requested()` | Load CV from DB into session state if requested |
| `collect_cv_data()` | Build CV data dict from session state |
| `_inject_builder_css_native(is_dark)` | Inject page CSS for 3-panel layout |
| `_inject_sections_relay_js()` | 0-height relay iframe for postMessage routing |
| `_render_left_panel_native()` | Left rail: hidden buttons, sections list, templates, style |
| `_render_sections_list_component(order, vis, is_dark)` | Sections list with drag and eye toggle |
| `_render_template_component(current_tpl, is_dark)` | Template selection cards |
| `_render_style_component(accent, font_size, lh, es, icons, photo, is_dark)` | Style controls (swatches, sliders, toggles) |
| `_render_middle_panel_native()` | Editor forms for all sections |
| `_render_right_panel_native(cv_data, is_dark)` | Preview panel with zoom controls |
| `_inject_realtime_js()` | Real-time personal details JS bridge |
| `generate_cv_html(...)` | Generate full CV HTML for preview/export |
| `_save_cv(cv_data, title, template)` | Persist CV to database |
| `_cached_generate_cv_pdf(...)` | Cached PDF byte generation |
| `render_cv_builder_page()` | Top-level page entry point |

---

## Summary

The Resume Builder is a state-driven Streamlit page with a native 3-panel layout. The left panel is built entirely from custom HTML components using a postMessage → relay → hidden button pattern for all interactivity, giving full CSS control over the design. The middle and preview panels are both driven by the same section metadata (`cvb_section_order`, `cvb_section_visibility`) so section movement and hide/show stay synchronized. Style customizations (accent color, font scale, line height, entry spacing, icon/photo toggles) are applied live to the preview and persisted with saved CVs.
