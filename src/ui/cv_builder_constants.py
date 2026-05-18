"""Constants for the CV builder."""
from __future__ import annotations

SECTION_SCHEMA: list[tuple[str, str]] = [
    ("personal", "Personal Information"),
    ("summary", "Professional Summary"),
    ("experience", "Work Experience"),
    ("education", "Education"),
    ("skills", "Skills"),
    ("projects", "Projects"),
    ("languages", "Languages"),
    ("certifications", "Certifications"),
    ("interests", "Interests"),
]

SECTION_IDS = [sid for sid, _ in SECTION_SCHEMA]
SECTION_ID_TO_LABEL = dict(SECTION_SCHEMA)
SECTION_LABEL_TO_ID = {label: sid for sid, label in SECTION_SCHEMA}

ACCENT_COLORS = [
    "#2563eb",
    "#7c3aed",
    "#059669",
    "#dc2626",
    "#d97706",
    "#0891b2",
    "#4f46e5",
    "#be185d",
]

FONT_OPTIONS: dict[str, str] = {
    "System Sans": "system-ui, sans-serif",
    "Georgia": "Georgia, serif",
    "Helvetica Neue": "'Helvetica Neue', Arial, sans-serif",
    "Times New Roman": "'Times New Roman', Times, serif",
}

PROFICIENCY_OPTIONS = ["Basic", "Intermediate", "Advanced", "Fluent", "Native"]
A4_WIDTH_PX = 794
A4_HEIGHT_PX = 1123
TEMPLATE_DEFAULT_ZOOM: dict[str, int] = {
    "modern": 100,
    "classic": 100,
    "creative": 100,
}
CVB_ZOOM_LEVELS: list[int] = [35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]
CVB_SCALE_VALUES: list[int] = [80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]
CVB_LINE_HEIGHT_VALUES: list[int] = list(range(10, 21))
CVB_ENTRY_SPACING_VALUES: list[int] = list(range(0, 25, 2))
CVB_PDF_TYPOGRAPHY_SCALE: float = 1.45

TEMPLATE_CONFIGS = {
    "classic": {
        "primary": "#1a1a2e",
        "accent": "#16213e",
        "link": "#2563eb",
        "rule": "#1a1a2e",
        "font": "Georgia, serif",
    },
    "modern": {
        "primary": "#2563eb",
        "accent": "#1e3a5f",
        "link": "#2563eb",
        "rule": "#2563eb",
        "font": "system-ui, sans-serif",
    },
    "creative": {
        "primary": "#0ea5e9",
        "accent": "#0369a1",
        "link": "#0284c7",
        "rule": "#38bdf8",
        "font": "system-ui, sans-serif",
    },
}

TEMPLATE_CHOICES: list[tuple[str, str, str]] = [
    ("classic", "Classic", "Single column, ATS-friendly"),
    ("creative", "Creative", "Colored sidebar"),
    ("modern", "Modern", "Two-column sidebar"),
]

LEGACY_SECTION_ORDER_V2: list[str] = [
    "education",
    "personal",
    "skills",
    "summary",
    "projects",
    "experience",
    "languages",
    "interests",
    "certifications",
]

CVR_SECTION_ORDER: list[str] = [
    "personal",
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "languages",
    "certifications",
    "interests",
]

SECTION_ICON_BY_ID: dict[str, str] = {
    "personal": ":material/person:",
    "summary": ":material/description:",
    "experience": ":material/work:",
    "education": ":material/school:",
    "skills": ":material/deployed_code:",
    "projects": ":material/folder:",
    "languages": ":material/language:",
    "certifications": ":material/verified:",
    "interests": ":material/interests:",
}

SECTION_ADD_BUTTON_BY_ID: dict[str, str] = {
    "experience": "Add Position",
    "education": "Add Education",
    "skills": "Add Skill",
    "projects": "Add Project",
    "languages": "Add Language",
    "certifications": "Add Certification",
}

CVB_PERSIST_BASE_KEYS: tuple[str, ...] = (
    "cvb_cv_title",
    "cvb_template",
    "cvb_accent_color",
    "cvb_font",
    "cvb_font_size",
    "cvb_line_height",
    "cvb_entry_spacing",
    "cvb_show_icons",
    "cvb_zoom",
    "cvb_section_order",
    "cvb_section_visibility",
    "cvb_active_section",
    "cvb_full_name",
    "cvb_prof_title",
    "cvb_email",
    "cvb_phone",
    "cvb_location",
    "cvb_website",
    "cvb_linkedin",
    "cvb_github",
    "cvb_website_url",
    "cvb_linkedin_url",
    "cvb_github_url",
    "cvb_summary",
    "cvb_exp_ids",
    "cvb_edu_ids",
    "cvb_proj_ids",
    "cvb_cert_ids",
    "cvb_lang_ids",
    "cvb_skill_ids",
    "cvb_interests",
    "cvb_interest_ctr",
)
