# Resume Builder: Current Behavior Reference

Last verified against the repository on **2026-05-19**.

This document tracks the current behavior of the Resume Builder page implemented in `src/ui/cv_builder_page.py` (and the recent split-out modules in the same package — see *Related Modules* below).

## Scope
- Route: `?page=resume-builder`
- Main module: `src/ui/cv_builder_page.py`
- Entry point: `render_cv_builder_page()`

### Related modules
The original monolith was split into focused modules (all in `src/ui/`):

| Module | Responsibility |
|---|---|
| `cv_builder_page.py` | Page composition, rendering, state lifecycle |
| `cv_builder_constants.py` | `TEMPLATE_CONFIGS` (`classic`, `creative`, `modern`), `TEMPLATE_CHOICES`, zoom levels, section order |
| `cv_builder_pdf.py` | PDF export pipeline |
| `cv_builder_preview_data.py` | Preview-data assembly |
| `cv_builder_value_utils.py` | Value normalization helpers |

## Runtime Sequence
1. Initialize state via `_init_builder()`.
2. Load requested CV via `_load_cv_for_builder_if_requested()`.
3. Inject page CSS and middle-panel CSS.
4. Collect data with `collect_cv_data()`.
5. Build a PDF request payload hash for the current state (no eager PDF render).
6. Render toolbar and 3-column workspace.
7. Re-collect live data after middle panel render (`cv_data_live`) so same-rerun section actions appear immediately in preview.
8. Inject JS bridges:
- `_inject_realtime_js()`
- `_inject_sections_relay_js()`
9. Apply final alignment overrides with `_inject_builder_final_alignment_overrides()`.

## State Persistence Guard
To prevent content loss during reruns caused by sidebar actions (reorder, visibility, template/style changes), `_init_builder()` now applies `_protect_builder_widget_state()`:
- Mirrors key `cvb_*` values into `cvb_state_mirror_v1`.
- Restores missing keys when widgets are temporarily unmounted.
- Covers both fixed keys and dynamic row keys (`exp/edu/skill/project/lang/cert`).
- Preserves user-entered middle-panel data while allowing normal delete behavior.

## Page Layout
Three columns:
1. Left rail: sections, templates, style.
2. Middle panel: editable section cards.
3. Right panel: zoom controls and preview.

## Canonical Sections
- `personal`
- `summary`
- `experience`
- `education`
- `skills`
- `projects`
- `languages`
- `certifications`
- `interests`

Default order (`CVR_SECTION_ORDER`):
1. `personal`
2. `summary`
3. `experience`
4. `education`
5. `skills`
6. `projects`
7. `languages`
8. `certifications`
9. `interests`

## Visibility and Collapse
Two independent controls:
1. Sidebar eye (`cvb_section_visibility`): hide/show entire section from output.
2. Section chevron (`cvb_section_open_<section_id>`): collapse/expand editor body only.

## Seeded Rows
Initial rows are seeded:
- Experience: 1 row + 1 bullet
- Education: 1 row
- Skills: 3 rows
- Projects: 1 row
- Languages: 1 row
- Certifications: 1 row
- Interests: empty until added

## Row-Level Visibility
Row eye toggles keep data but exclude hidden rows from preview/save/PDF:
- Experience: `cvb_exp_visible_<id>`
- Education: `cvb_edu_visible_<id>`
- Skills: `cvb_skill_visible_<id>`
- Projects: `cvb_proj_visible_<id>`
- Languages: `cvb_lang_visible_<id>`
- Certifications: `cvb_cert_visible_<id>`

## Personal Information
Visible fields:
- Full Name
- Professional Title
- Email
- Phone
- Location
- LinkedIn (display text)
- Website (display text)
- GitHub (display text)

Hidden URL storage fields:
- `cvb_linkedin_url`
- `cvb_website_url`
- `cvb_github_url`

Form layout:
- Row 1: Email + Phone
- Row 2: Location + LinkedIn
- Row 3: Website + GitHub

### Link Editing Flow (LinkedIn, Website, GitHub)
- Each display-text input has an inline link icon button inside the textbox.
- Clicking the icon opens a custom link URL popover.
- User enters the real URL in the popover.
- Clicking the checkmark saves URL, closes popover, updates preview link target, and commits URL back to Streamlit state.
- Stale `cvb_lurl_*` URL query params are cleared during builder bootstrap, CV load, import, and reset, so links from a previous CV/session do not leak into the current one.

Important behavior:
- Display text field is plain text only.
- No automatic slug-to-URL conversion for display text.
- Hyperlink exists only when explicit URL is saved via the link popover.

## Professional Summary
- Text area without a hard max-character cap.
- Live character counter (`N`).

## Work Experience
Per row:
- Header actions: Duplicate, Eye, Delete
- Fields: Job Title, Company, Start Date, End Date (with Present), Location
- Description
- Bullet list with add/remove and stable reindexing

## Education
Per row:
- Eye, Delete
- Degree
- Institution, Location
- Start Date, End Date (with Present)
- Description/details field

## Skills
Per row:
- Skill text
- Eye
- Delete

## Projects
Per row:
- Eye, Delete
- Project Name, Role
- Date
- Description
- Technologies (comma-separated)
- Project Link

## Languages
Per row:
- Language
- Proficiency (`Basic`, `Intermediate`, `Advanced`, `Fluent`, `Native`)
- Eye
- Delete

Only rows with non-empty language name are included in output.

## Certifications
Per row:
- Eye, Delete
- Title
- Issuer
- Date
- Credential URL

## Interests
- Add on demand
- Read-only rendered rows with delete action

## Date Picker
Date fields use month/year style picker:
- Empty display: `MM/YYYY`
- End fields can be marked Present where configured
- Clear resets value

## Realtime Preview Behavior
Preview sync is powered by JS message bridge and rerun-backed data refresh.

What updates immediately:
- Personal fields and contact lines.
- Non-personal input changes via widget-key updates.
- Add/remove/toggle actions reflected on rerun using `cv_data_live`.
- A debounced full-field sync (`broadcastAllMiddleFields`) is scheduled after middle-panel input/button events to keep first-paint placement and ordering stable.

User-mode transition:
- On first resolvable edit interaction in middle panel, preview switches from demo composition to user-only composition immediately.
- User-mode transition is guarded to avoid destructive blank states before valid payloads are available.

Section placement stability:
- Live section insertion in preview uses deterministic rank ordering derived from normalized `section_order`.
- This prevents transient wrong ordering/placement on first update for non-personal sections (Experience/Education/Skills/Projects/Languages/Certifications/Interests).

Theme-switch resilience:
- Sync bootstrap replays current values after rerender, so toggling light/dark during edits does not leave preview blank.

## Preview Source Rules
Function: `_build_preview_source(cv_data)`.

- If builder is effectively empty, demo preview is shown.
- Once user data is meaningful, preview switches to user-only mode (`_user_only_preview=True`).

Effective-empty check includes personal, list sections, skills, and interests.

## Contact Rendering in Preview
Classic template contact is rendered in 2 centered rows:
1. Email, Phone, Location, LinkedIn
2. Website, GitHub

Link rendering rule:
- LinkedIn/Website/GitHub are clickable only when explicit URL fields are present.
- If only display text exists and no explicit URL, text is shown without hyperlink.

## Toolbar
- Import
- Backup
- Save
- Download PDF
- Reset

## Data Contract (`collect_cv_data()`)
Returns:
- `personal`
- `experience`
- `education`
- `skills`
- `projects`
- `certifications`
- `languages`
- `interests`
- `customization`

`customization` currently includes:
- `accent_color`
- `font`
- `font_size`
- `line_height`
- `entry_spacing`
- `show_icons`
- `section_order`
- `section_visibility`

Filtering:
- Hidden rows excluded
- Empty skill items excluded
- Empty language-name rows excluded
- Empty bullet items excluded

## PDF Export
Pipeline:
1. Build preview-source payload.
2. Generate template HTML (`generate_cv_html(...)`).
3. Wrap print CSS (`_build_pdf_ready_html(...)`).
4. Render with Playwright (`_render_html_to_pdf_bytes(...)`).

Execution behavior:
- PDF rendering is on-demand from the toolbar `Download PDF` action.
- Generated bytes are cached in session state by a payload hash.
- If resume content/style changes, cached PDF bytes are invalidated and regenerated on the next download request.

Sizing behavior:
- Preview uses default HTML sizing (`typography_scale=1.0`) for stable in-app composition.
- PDF export uses mapped sizing via `CVB_PDF_TYPOGRAPHY_SCALE` (passed into `generate_cv_html(...)`) to improve readability.
- This keeps preview visually stable while producing larger FlowCV-like text density in downloaded PDF.

Inner whitespace behavior:
- Classic template now uses wider side padding (`.classic { padding: 18px 38px; }`) so preview and PDF both show larger left/right blank space similar to FlowCV.

Link behavior in exported PDF:
- Exported link target uses explicit URL fields (`*_url`).
- Display text remains independent and can be different from underlying URL.

## Theming Notes
- Dark mode caret color is explicitly styled for visibility.
- Eye button hover/focus styling is aligned across light and dark contexts.
- Middle controls and preview container are styled for dark compatibility.
- Modern sidebar links are explicitly styled for contrast (`.modern-left .ci-val/.ci-link`) so LinkedIn/GitHub/Website text remains visible in both preview and PDF.

## QA Checklist
1. Personal layout is `Email/Phone`, `Location/LinkedIn`, `Website/GitHub`.
2. LinkedIn/Website/GitHub display fields behave as plain text fields.
3. Inline link icon opens popover and saves explicit URL with checkmark.
4. Preview links open the explicit saved URLs.
5. Downloaded PDF links open the same explicit saved URLs.
6. Row eye toggles hide/show output without deleting row data.
7. Middle-panel edits update preview immediately.
8. Theme switch during editing preserves preview content.
9. Empty builder shows demo preview; first user edit switches to user-only preview.
10. Save/Load/Backup/Import/Reset continue to work.
11. Reordering sections does not clear previously entered personal/summary/content data.
12. Preview and PDF sizing behavior matches intended split: stable preview + larger PDF typography.
13. Modern template sidebar shows visible LinkedIn/GitHub/Website text (not icons-only).
14. First realtime non-personal updates are placed in correct section order immediately (no delayed reflow).
15. Long Professional Summary paste appears consistently in field, preview, and PDF.
