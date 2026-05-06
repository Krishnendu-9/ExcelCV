"""CV Builder page — 3-panel workspace (left rail · editor · preview)."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components
try:
    from streamlit_sortables import sort_items as sortable_items
except Exception:
    sortable_items = None

from src.auth_utils import get_session_user
from src.database import CV, get_db
from src.gemini_client import suggest_cv_bullets
from src.services.pdf_generator import generate_cv_pdf


def _get_sortable_items():
    """Lazy-load sortables so a runtime pip install works without full process restart."""
    global sortable_items
    if sortable_items is None:
        try:
            from streamlit_sortables import sort_items as _sortable_items
            sortable_items = _sortable_items
        except Exception:
            sortable_items = None
    return sortable_items

# ─── Constants ────────────────────────────────────────────────────────────────

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

SECTIONS = [label for _, label in SECTION_SCHEMA]
SECTION_IDS = [sid for sid, _ in SECTION_SCHEMA]
SECTION_ID_TO_LABEL = dict(SECTION_SCHEMA)
SECTION_LABEL_TO_ID = {label: sid for sid, label in SECTION_SCHEMA}

ACCENT_COLORS = [
    "#2563eb", "#7c3aed", "#059669", "#dc2626",
    "#d97706", "#0891b2", "#4f46e5", "#be185d",
]

FONT_OPTIONS: dict[str, str] = {
    "System Sans":     "system-ui, sans-serif",
    "Georgia":         "Georgia, serif",
    "Helvetica Neue":  "'Helvetica Neue', Arial, sans-serif",
    "Times New Roman": "'Times New Roman', Times, serif",
}

PROFICIENCY_OPTIONS = ["Basic", "Intermediate", "Advanced", "Fluent", "Native"]
A4_WIDTH_PX = 794
A4_HEIGHT_PX = 1123
TEMPLATE_DEFAULT_ZOOM: dict[str, int] = {
    "modern": 90,
    "classic": 65,
    "creative": 100,
}

TEMPLATE_CONFIGS = {
    "classic": {"primary": "#1a1a2e", "accent": "#16213e", "link": "#2563eb", "rule": "#1a1a2e", "font": "Georgia, serif"},
    "modern":  {"primary": "#2563eb", "accent": "#1e3a5f", "link": "#2563eb", "rule": "#2563eb", "font": "system-ui, sans-serif"},
    "creative": {"primary": "#0ea5e9", "accent": "#0369a1", "link": "#0284c7", "rule": "#38bdf8", "font": "system-ui, sans-serif"},
}

TEMPLATE_CHOICES: list[tuple[str, str, str]] = [
    ("modern", "Modern", "Two-column sidebar"),
    ("classic", "Classic", "Single column, ATS-friendly"),
    ("creative", "Creative", "Colored sidebar"),
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


def _normalize_template(template: str | None) -> str:
    value = (template or "").strip().lower()
    if value == "minimal":
        return "creative"
    if value in TEMPLATE_CONFIGS:
        return value
    return "classic"


def _default_zoom_for_template(template: str | None) -> int:
    return TEMPLATE_DEFAULT_ZOOM.get(_normalize_template(template), 75)


def _section_id(value: str) -> str | None:
    if value in SECTION_ID_TO_LABEL:
        return value
    return SECTION_LABEL_TO_ID.get(value)


def _normalize_section_order(order: list | None) -> list[str]:
    normalized: list[str] = []
    for item in (order or []):
        sid = _section_id(str(item))
        if sid and sid not in normalized:
            normalized.append(sid)
    for sid in SECTION_IDS:
        if sid not in normalized:
            normalized.append(sid)
    return normalized


def _normalize_section_visibility(visibility: dict | None) -> dict[str, bool]:
    normalized = {sid: True for sid in SECTION_IDS}
    if not isinstance(visibility, dict):
        return normalized
    for key, value in visibility.items():
        sid = _section_id(str(key))
        if sid:
            normalized[sid] = bool(value)
    return normalized


def _section_expander(label: str, section_id: str, expanded: bool = True):
    icon = SECTION_ICON_BY_ID.get(section_id)
    try:
        return st.expander(label, expanded=expanded, icon=icon)
    except TypeError:
        return st.expander(label, expanded=expanded)

# ─── Session-state initialisation ────────────────────────────────────────────

def _init_builder() -> None:
    defaults: dict = {
        "cvb_cv_title":       "My Resume",
        "cvb_template":       "classic",
        "cvb_loaded_cv_id":   None,
        "cvb_last_saved":     None,
        "cvb_confirm_reset":  False,
        "cvb_show_import":    False,
        "cvb_accent_color":   "#2563eb",
        "cvb_font":           "System Sans",
        "cvb_font_size":      11,
        "cvb_line_height":    1.4,
        "cvb_entry_spacing":  8,
        "cvb_show_icons":     True,
        "cvb_show_photo":     False,
        "cvb_zoom":           65,
        "cvb_section_order":      list(SECTION_IDS),
        "cvb_section_visibility": {sid: True for sid in SECTION_IDS},
        "cvb_active_section":     "personal",

        "cvb_preview_fullscreen": False,
        "cvb_full_name":   "",
        "cvb_prof_title":  "",
        "cvb_email":       "",
        "cvb_phone":       "",
        "cvb_location":    "",
        "cvb_website":     "",
        "cvb_linkedin":    "",
        "cvb_github":      "",
        "cvb_summary":     "",
        "cvb_exp_ids":       [],
        "cvb_edu_ids":       [],
        "cvb_proj_ids":      [],
        "cvb_cert_ids":      [],
        "cvb_lang_ids":      [],
        "cvb_skill_ids":     [],
        "cvb_skill_cat_ids": [],
        "cvb_interests":     [],
        "cvb_interest_ctr":  0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v.copy() if isinstance(v, (dict, list)) else v
    st.session_state["cvb_template"] = _normalize_template(st.session_state.get("cvb_template"))
    st.session_state["cvb_section_order"] = _normalize_section_order(st.session_state.get("cvb_section_order"))
    if st.session_state["cvb_section_order"] == SECTION_IDS:
        st.session_state["cvb_section_order"] = list(CVR_SECTION_ORDER)
    if "cvb_sidebar_layout_v2_migrated" not in st.session_state:
        st.session_state["cvb_section_order"] = list(CVR_SECTION_ORDER)
        st.session_state["cvb_sidebar_layout_v2_migrated"] = True
    if "cvb_sidebar_layout_v3_migrated" not in st.session_state:
        current_order = st.session_state.get("cvb_section_order", [])
        if list(current_order) == list(LEGACY_SECTION_ORDER_V2):
            st.session_state["cvb_section_order"] = list(CVR_SECTION_ORDER)
        st.session_state["cvb_sidebar_layout_v3_migrated"] = True
    if "cvb_zoom_default_v4_migrated" not in st.session_state:
        current_zoom = int(st.session_state.get("cvb_zoom", 65))
        if current_zoom in (45, 75, 95):
            st.session_state["cvb_zoom"] = _default_zoom_for_template(st.session_state.get("cvb_template", "classic"))
        st.session_state["cvb_zoom_default_v4_migrated"] = True
    if "cvb_skills_flat_v1_migrated" not in st.session_state:
        if not st.session_state.get("cvb_skill_ids"):
            migrated: list[str] = []
            seen: set[str] = set()
            for sid in st.session_state.get("cvb_skill_cat_ids", []):
                raw = st.session_state.get(f"cvb_skill_items_{sid}", "")
                for item in [x.strip() for x in raw.replace(",", "\n").splitlines() if x.strip()]:
                    token = item.lower()
                    if token in seen:
                        continue
                    seen.add(token)
                    kid = str(uuid.uuid4())
                    migrated.append(kid)
                    st.session_state[f"cvb_skill_item_{kid}"] = item
            st.session_state["cvb_skill_ids"] = migrated
        st.session_state["cvb_skills_flat_v1_migrated"] = True
    st.session_state["cvb_section_visibility"] = _normalize_section_visibility(st.session_state.get("cvb_section_visibility"))
    if st.session_state.get("cvb_active_section") not in SECTION_IDS:
        st.session_state["cvb_active_section"] = SECTION_IDS[0]


# ─── Data collection ──────────────────────────────────────────────────────────

def collect_cv_data() -> dict:
    ss = st.session_state
    personal = {
        "full_name":  ss.get("cvb_full_name", ""),
        "prof_title": ss.get("cvb_prof_title", ""),
        "email":      ss.get("cvb_email", ""),
        "phone":      ss.get("cvb_phone", ""),
        "location":   ss.get("cvb_location", ""),
        "website":    ss.get("cvb_website", ""),
        "linkedin":   ss.get("cvb_linkedin", ""),
        "github":     ss.get("cvb_github", ""),
        "summary":    ss.get("cvb_summary", ""),
    }
    experience = []
    for eid in ss.get("cvb_exp_ids", []):
        bcount = ss.get(f"cvb_exp_bcount_{eid}", 1)
        bullets = [ss.get(f"cvb_exp_b_{eid}_{i}", "") for i in range(bcount)]
        experience.append({
            "id":         eid,
            "role":       ss.get(f"cvb_exp_role_{eid}", ""),
            "company":    ss.get(f"cvb_exp_company_{eid}", ""),
            "location":   ss.get(f"cvb_exp_loc_{eid}", ""),
            "start_date": ss.get(f"cvb_exp_start_{eid}", ""),
            "end_date":   ss.get(f"cvb_exp_end_{eid}", ""),
            "current":    ss.get(f"cvb_exp_curr_{eid}", False),
            "bullets":    [b for b in bullets if b.strip()],
        })
    education = []
    for eid in ss.get("cvb_edu_ids", []):
        education.append({
            "id":          eid,
            "institution": ss.get(f"cvb_edu_inst_{eid}", ""),
            "degree":      ss.get(f"cvb_edu_degree_{eid}", ""),
            "field":       ss.get(f"cvb_edu_field_{eid}", ""),
            "location":    ss.get(f"cvb_edu_loc_{eid}", ""),
            "start_date":  ss.get(f"cvb_edu_start_{eid}", ""),
            "end_date":    ss.get(f"cvb_edu_end_{eid}", ""),
            "gpa":         ss.get(f"cvb_edu_gpa_{eid}", ""),
        })
    skill_items = []
    for sid in ss.get("cvb_skill_ids", []):
        value = ss.get(f"cvb_skill_item_{sid}", "").strip()
        if value:
            skill_items.append({"id": sid, "name": value})
    skills_cats = [{"id": "primary", "name": "Skills", "items": [item["name"] for item in skill_items]}] if skill_items else []
    projects = []
    for pid in ss.get("cvb_proj_ids", []):
        projects.append({
            "id":          pid,
            "name":        ss.get(f"cvb_proj_name_{pid}", ""),
            "role":        ss.get(f"cvb_proj_role_{pid}", ""),
            "description": ss.get(f"cvb_proj_desc_{pid}", ""),
            "tech_stack":  [t.strip() for t in ss.get(f"cvb_proj_tech_{pid}", "").split(",") if t.strip()],
            "link":        ss.get(f"cvb_proj_link_{pid}", ""),
            "start_date":  ss.get(f"cvb_proj_start_{pid}", ""),
            "end_date":    ss.get(f"cvb_proj_end_{pid}", ""),
        })
    certifications = []
    for cid in ss.get("cvb_cert_ids", []):
        certifications.append({
            "id":     cid,
            "name":   ss.get(f"cvb_cert_name_{cid}", ""),
            "issuer": ss.get(f"cvb_cert_issuer_{cid}", ""),
            "date":   ss.get(f"cvb_cert_date_{cid}", ""),
            "link":   ss.get(f"cvb_cert_link_{cid}", ""),
        })
    languages = []
    for lid in ss.get("cvb_lang_ids", []):
        languages.append({
            "id":          lid,
            "language":    ss.get(f"cvb_lang_name_{lid}", ""),
            "proficiency": ss.get(f"cvb_lang_prof_{lid}", "Intermediate"),
        })
    return {
        "personal":       personal,
        "experience":     experience,
        "education":      education,
        "skills":         {"items": skill_items, "categories": skills_cats},
        "projects":       projects,
        "certifications": certifications,
        "languages":      languages,
        "interests":      ss.get("cvb_interests", []),
        "customization": {
            "accent_color":  ss.get("cvb_accent_color", "#2563eb"),
            "font":          ss.get("cvb_font", "System Sans"),
            "font_size":     ss.get("cvb_font_size", 11),
            "line_height":   ss.get("cvb_line_height", 1.4),
            "entry_spacing": ss.get("cvb_entry_spacing", 8),
        },
    }


# ─── Load from DB ─────────────────────────────────────────────────────────────

def load_cv_into_builder(cv_record: CV) -> None:
    d = cv_record.data or {}
    ss = st.session_state
    ss["cvb_cv_title"]     = cv_record.title
    ss["cvb_template"]     = _normalize_template(cv_record.template)
    ss["cvb_loaded_cv_id"] = cv_record.id
    p = d.get("personal", {})
    for field in ["full_name", "prof_title", "email", "phone", "location", "website", "linkedin", "github", "summary"]:
        ss[f"cvb_{field}"] = p.get(field, "")
    exp_ids = []
    for exp in d.get("experience", []):
        eid = exp.get("id") or str(uuid.uuid4())
        exp_ids.append(eid)
        ss[f"cvb_exp_role_{eid}"]    = exp.get("role", "")
        ss[f"cvb_exp_company_{eid}"] = exp.get("company", "")
        ss[f"cvb_exp_loc_{eid}"]     = exp.get("location", "")
        ss[f"cvb_exp_start_{eid}"]   = exp.get("start_date", "")
        ss[f"cvb_exp_end_{eid}"]     = exp.get("end_date", "")
        ss[f"cvb_exp_curr_{eid}"]    = exp.get("current", False)
        bullets = exp.get("bullets", [""])
        ss[f"cvb_exp_bcount_{eid}"]  = len(bullets) or 1
        for i, b in enumerate(bullets):
            ss[f"cvb_exp_b_{eid}_{i}"] = b
    ss["cvb_exp_ids"] = exp_ids
    edu_ids = []
    for edu in d.get("education", []):
        eid = edu.get("id") or str(uuid.uuid4())
        edu_ids.append(eid)
        ss[f"cvb_edu_inst_{eid}"]   = edu.get("institution", "")
        ss[f"cvb_edu_degree_{eid}"] = edu.get("degree", "")
        ss[f"cvb_edu_field_{eid}"]  = edu.get("field", "")
        ss[f"cvb_edu_loc_{eid}"]    = edu.get("location", "")
        ss[f"cvb_edu_start_{eid}"]  = edu.get("start_date", "")
        ss[f"cvb_edu_end_{eid}"]    = edu.get("end_date", "")
        ss[f"cvb_edu_gpa_{eid}"]    = edu.get("gpa", "")
    ss["cvb_edu_ids"] = edu_ids
    parsed_skill_items = d.get("skills", {}).get("items", [])
    if not parsed_skill_items:
        for cat in d.get("skills", {}).get("categories", []):
            for item in cat.get("items", []):
                parsed_skill_items.append({"name": item})
    skill_ids = []
    for item in parsed_skill_items:
        sid = item.get("id") or str(uuid.uuid4())
        skill_ids.append(sid)
        ss[f"cvb_skill_item_{sid}"] = item.get("name", "")
    ss["cvb_skill_ids"] = skill_ids
    ss["cvb_skill_cat_ids"] = []
    proj_ids = []
    for proj in d.get("projects", []):
        pid = proj.get("id") or str(uuid.uuid4())
        proj_ids.append(pid)
        ss[f"cvb_proj_name_{pid}"]  = proj.get("name", "")
        ss[f"cvb_proj_role_{pid}"]  = proj.get("role", "")
        ss[f"cvb_proj_desc_{pid}"]  = proj.get("description", "")
        ss[f"cvb_proj_tech_{pid}"]  = ", ".join(proj.get("tech_stack", []))
        ss[f"cvb_proj_link_{pid}"]  = proj.get("link", "")
        ss[f"cvb_proj_start_{pid}"] = proj.get("start_date", "")
        ss[f"cvb_proj_end_{pid}"]   = proj.get("end_date", "")
    ss["cvb_proj_ids"] = proj_ids
    cert_ids = []
    for cert in d.get("certifications", []):
        cid = cert.get("id") or str(uuid.uuid4())
        cert_ids.append(cid)
        ss[f"cvb_cert_name_{cid}"]   = cert.get("name", "")
        ss[f"cvb_cert_issuer_{cid}"] = cert.get("issuer", "")
        ss[f"cvb_cert_date_{cid}"]   = cert.get("date", "")
        ss[f"cvb_cert_link_{cid}"]   = cert.get("link", "")
    ss["cvb_cert_ids"] = cert_ids
    lang_ids = []
    for lang in d.get("languages", []):
        lid = lang.get("id") or str(uuid.uuid4())
        lang_ids.append(lid)
        ss[f"cvb_lang_name_{lid}"] = lang.get("language", "")
        ss[f"cvb_lang_prof_{lid}"] = lang.get("proficiency", "Intermediate")
    ss["cvb_lang_ids"] = lang_ids
    ss["cvb_interests"] = d.get("interests", [])
    cust = d.get("customization", {})
    ss["cvb_accent_color"]  = cust.get("accent_color", ss.get("cvb_accent_color", "#3b82f6"))
    ss["cvb_font"]          = cust.get("font", ss.get("cvb_font", "System Sans"))
    ss["cvb_font_size"]     = int(cust.get("font_size", ss.get("cvb_font_size", 11)))
    ss["cvb_line_height"]   = float(cust.get("line_height", ss.get("cvb_line_height", 1.4)))
    ss["cvb_entry_spacing"] = int(cust.get("entry_spacing", ss.get("cvb_entry_spacing", 8)))


def _load_cv_for_builder_if_requested() -> None:
    load_id = st.session_state.pop("cvb_load_id", None)
    if not load_id:
        return
    user = get_session_user()
    if not user:
        return
    db = get_db()
    try:
        cv = db.query(CV).filter(CV.id == load_id, CV.user_id == user["id"]).first()
        if cv:
            load_cv_into_builder(cv)
            st.session_state["ui_toast"] = {"message": f"Loaded '{cv.title}'", "icon": "✅"}
        else:
            st.warning("CV not found.")
    finally:
        db.close()


# ─── HTML escape helpers ──────────────────────────────────────────────────────

def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _date_range(start: str, end: str, current: bool = False) -> str:
    end_label = "Present" if current else end
    if start and end_label:
        return f"{start} – {end_label}"
    return start or end_label or ""


# ─── CV HTML preview generator ────────────────────────────────────────────────

def _parse_date_for_input(value: str | date | None) -> date | None:
    if isinstance(value, date):
        return value
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%b %Y",
        "%B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _format_date_for_storage(value: date | None) -> str:
    if not value:
        return ""
    return value.strftime("%b %Y")


def _date_field(label: str, storage_key: str, disabled: bool = False) -> None:
    ui_key = f"{storage_key}__ui"
    parsed = _parse_date_for_input(st.session_state.get(storage_key, ""))
    if ui_key not in st.session_state:
        st.session_state[ui_key] = parsed
    elif parsed is None and st.session_state.get(storage_key, "") == "":
        st.session_state[ui_key] = None

    picked = st.date_input(
        label,
        value=st.session_state.get(ui_key),
        key=ui_key,
        format="YYYY-MM-DD",
        disabled=disabled,
    )
    st.session_state[storage_key] = _format_date_for_storage(picked)


def generate_cv_html(
    data: dict,
    template: str = "classic",
    accent_color: str | None = None,
    font_family: str | None = None,
    font_size: int = 11,
    line_height: float = 1.4,
    entry_spacing: int = 8,
    preview_dark: bool = False,
    section_visibility: dict | None = None,
    section_order: list | None = None,
) -> str:
    cfg = dict(TEMPLATE_CONFIGS.get(template, TEMPLATE_CONFIGS["classic"]))
    if accent_color:
        cfg["primary"] = accent_color
        cfg["rule"] = accent_color
        cfg["link"] = accent_color
    if font_family:
        cfg["font"] = font_family

    vis = _normalize_section_visibility(section_visibility)
    order = _normalize_section_order(section_order)

    p        = data.get("personal", {})
    contacts = [p.get(f, "") for f in ["email", "phone", "location", "website", "linkedin", "github"] if p.get(f)]

    fs           = font_size
    fs_sm        = max(fs - 1, 7)
    lh           = line_height
    es           = entry_spacing
    sec_mb       = es + 6
    page_bg      = "#0b1220" if preview_dark else "#ffffff"
    text_color   = "#e2e8f0" if preview_dark else "#222222"
    muted_color  = "#94a3b8" if preview_dark else "#666666"
    subtle_color = "#cbd5e1" if preview_dark else "#444444"
    soft_muted   = "#a3b3c7" if preview_dark else "#555555"
    heading_color = "#e2e8f0" if preview_dark else cfg["primary"]
    rule_color    = "#334155" if preview_dark else cfg["rule"]

    def _sec(section_id: str, title: str, content: str) -> str:
        if not vis.get(section_id, True):
            return ""
        if not content.strip():
            return ""
        return (
            f'<div style="margin-bottom:{sec_mb}px">'
            f'<h2 style="font-size:{fs_sm}px;font-weight:700;letter-spacing:2px;text-transform:uppercase;'
            f'color:{heading_color};margin:0 0 3px;border-bottom:1.5px solid {rule_color};padding-bottom:3px;">{title}</h2>'
            f'{content}</div>'
        )

    def _exp_block(exp: dict) -> str:
        bhtml = "".join(
            f'<p style="margin:1px 0 0 10px;font-size:{fs_sm}px;line-height:{lh}">• {_html_escape(b)}</p>'
            for b in exp.get("bullets", []) if b.strip()
        )
        dr = _html_escape(_date_range(exp.get("start_date", ""), exp.get("end_date", ""), exp.get("current", False)))
        loc = f', {_html_escape(exp.get("location",""))}' if exp.get("location") else ""
        return (
            f'<div style="margin-bottom:{es}px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span style="font-size:{fs}px;font-weight:700">{_html_escape(exp.get("role",""))}</span>'
            f'<span style="font-size:{fs_sm}px;color:{muted_color}">{dr}</span></div>'
            f'<p style="margin:1px 0;font-size:{fs_sm}px;color:{subtle_color};line-height:{lh}">'
            f'{_html_escape(exp.get("company",""))}{loc}</p>'
            f'{bhtml}</div>'
        )

    def _edu_block(edu: dict) -> str:
        deg   = _html_escape(edu.get("degree", ""))
        field = _html_escape(edu.get("field", ""))
        gpa   = edu.get("gpa", "")
        dl    = f"{deg}{', ' + field if field else ''}{' | GPA: ' + gpa if gpa else ''}"
        dr    = _html_escape(_date_range(edu.get("start_date", ""), edu.get("end_date", "")))
        return (
            f'<div style="margin-bottom:{es}px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span style="font-size:{fs}px;font-weight:700">{_html_escape(edu.get("institution",""))}</span>'
            f'<span style="font-size:{fs_sm}px;color:{muted_color}">{dr}</span></div>'
            f'<p style="margin:1px 0;font-size:{fs_sm}px;color:{subtle_color};line-height:{lh}">{dl}</p></div>'
        )

    experience_html = "".join(_exp_block(e) for e in data.get("experience", []))
    education_html  = "".join(_edu_block(e) for e in data.get("education", []))

    skill_values = [s.get("name", "").strip() for s in data.get("skills", {}).get("items", []) if s.get("name", "").strip()]
    if not skill_values:
        for cat in data.get("skills", {}).get("categories", []):
            skill_values.extend([x for x in cat.get("items", []) if x])
    skills_html = (
        f'<p style="font-size:{fs}px;margin:2px 0;line-height:{lh}">{_html_escape(", ".join(skill_values))}</p>'
        if skill_values else ""
    )

    projects_html = ""
    for proj in data.get("projects", []):
        tech = proj.get("tech_stack", [])
        dr   = _html_escape(_date_range(proj.get("start_date",""), proj.get("end_date","")))
        projects_html += (
            f'<div style="margin-bottom:{es}px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span style="font-size:{fs}px;font-weight:700">{_html_escape(proj.get("name",""))}</span>'
            f'<span style="font-size:{fs_sm}px;color:{muted_color}">{dr}</span></div>'
            + (f'<p style="margin:1px 0;font-size:{fs_sm}px;font-style:italic;color:{soft_muted};line-height:{lh}">Tech: {_html_escape(", ".join(tech))}</p>' if tech else "")
            + (f'<p style="margin:2px 0;font-size:{fs_sm}px;line-height:{lh}">{_html_escape(proj.get("description",""))}</p>' if proj.get("description") else "")
            + (f'<p style="margin:1px 0;font-size:{max(fs_sm-1,7)}px;color:{cfg["link"]}">{_html_escape(proj.get("link",""))}</p>' if proj.get("link") else "")
            + f'</div>'
        )

    certs_html = "".join(
        f'<p style="font-size:{fs}px;margin:2px 0;line-height:{lh}">• <b>{_html_escape(c.get("name",""))}</b>'
        f'{" — " + _html_escape(c.get("issuer","")) if c.get("issuer") else ""}'
        f'{" (" + _html_escape(c.get("date","")) + ")" if c.get("date") else ""}</p>'
        for c in data.get("certifications", [])
    )

    languages_html = "".join(
        f'<p style="font-size:{fs}px;margin:2px 0;line-height:{lh}">'
        f'<b>{_html_escape(lang.get("language",""))}</b>'
        f'{" — " + _html_escape(lang.get("proficiency","")) if lang.get("proficiency") else ""}</p>'
        for lang in data.get("languages", []) if lang.get("language")
    )

    interests = data.get("interests", [])
    interests_html = (
        f'<p style="font-size:{fs}px;margin:2px 0;line-height:{lh}">{_html_escape(", ".join(interests))}</p>'
        if interests else ""
    )

    name    = _html_escape(p.get("full_name") or "Your Name")
    title   = _html_escape(p.get("prof_title", ""))
    contact = _html_escape(" · ".join(contacts))
    summary = _html_escape(p.get("summary", ""))
    _cd     = "" if contact else ";display:none"

    if template == "modern":
        header_html = (
            f'<div style="background:{cfg["primary"]};color:#fff;padding:18px 24px;margin:-20px -20px 14px;">'
            f'<h1 id="cv-name" style="font-size:22px;font-weight:800;margin:0">{name}</h1>'
            + (f'<p style="font-size:10px;color:#bfdbfe;margin:3px 0 0">{title}</p>' if title else "")
            + f'<p id="cv-contact" style="font-size:9px;color:#bfdbfe;margin:4px 0 0{_cd}">{contact}</p>'
            + (f'<p style="font-size:10px;color:#dbeafe;margin:8px 0 0;line-height:1.5">{summary}</p>' if summary and vis.get("summary", True) else "")
            + f'</div>'
        )
        summary_html = ""
    else:
        header_html = (
            f'<h1 id="cv-name" style="font-size:22px;font-weight:700;text-align:center;margin:0;color:{heading_color}">{name}</h1>'
            + (f'<p style="text-align:center;font-size:10px;color:{muted_color};margin:2px 0 4px">{title}</p>' if title else "")
            + f'<p id="cv-contact" style="text-align:center;font-size:9.5px;color:{muted_color};margin:4px 0 10px{_cd}">{contact}</p>'
        )
        summary_html = (
            _sec("summary", "Professional Summary",
                 f'<p style="font-size:10.5px;line-height:1.5;margin:4px 0">{summary}</p>')
            if summary else ""
        )

    section_content_map = {
        "summary":        summary_html,
        "experience":     _sec("experience", "Work Experience", experience_html),
        "education":      _sec("education", "Education", education_html),
        "skills":         _sec("skills", "Skills", skills_html),
        "projects":       _sec("projects", "Projects", projects_html),
        "languages":      _sec("languages", "Languages", languages_html),
        "certifications": _sec("certifications", "Certifications", certs_html),
        "interests":      _sec("interests", "Interests", interests_html),
    }

    body = ""
    for section_id in order:
        if section_id == "personal":
            continue
        body += section_content_map.get(section_id, "")

    hr_tag = "<hr>" if template == "classic" else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  font-family:{cfg["font"]}; font-size:{fs}px;
  color:{text_color}; background:{page_bg}; padding:20px; line-height:{lh};
}}
hr {{ border:none; border-top:1.5px solid {cfg["rule"]}; margin:6px 0 10px; }}
</style></head><body>
{header_html}
{hr_tag}
{body}
<script>
window.addEventListener('message', function(ev) {{
  var d = ev.data;
  if (!d || d.type !== 'cv-rt-update') return;
  var el;
  if (d.field === 'cvb_full_name') {{
    el = document.getElementById('cv-name');
    if (el) el.textContent = d.value || 'Your Name';
  }} else if (d.field === 'cvb_contact') {{
    el = document.getElementById('cv-contact');
    if (el) {{ el.textContent = d.value; el.style.display = d.value ? '' : 'none'; }}
  }}
}});
</script>
</body></html>"""


# ─── Save to DB ───────────────────────────────────────────────────────────────

def _save_cv(cv_data: dict, title: str, template: str) -> bool:
    user = get_session_user()
    if not user:
        st.warning("Please sign in to save your CV.")
        return False
    db = get_db()
    try:
        loaded_id = st.session_state.get("cvb_loaded_cv_id")
        if loaded_id:
            cv = db.query(CV).filter(CV.id == loaded_id, CV.user_id == user["id"]).first()
            if cv:
                cv.title = title
                cv.template = template
                cv.data = cv_data
                db.commit()
                return True
        cv = CV(user_id=user["id"], title=title, template=template, data=cv_data)
        db.add(cv)
        db.commit()
        db.refresh(cv)
        st.session_state["cvb_loaded_cv_id"] = cv.id
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


# ─── PDF / backup helpers ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _cached_generate_cv_pdf(
    data_json: str, template: str, accent_color: str | None,
    font_family: str | None, font_size: int, line_height: float, entry_spacing: int,
) -> bytes | None:
    try:
        return generate_cv_pdf(
            json.loads(data_json), template,
            accent_color=accent_color, font_family=font_family,
            font_size=font_size, line_height=line_height, entry_spacing=entry_spacing,
        )
    except Exception:
        return None


def _get_backup_json() -> str:
    data = {k: v for k, v in st.session_state.items() if k.startswith("cvb_")}
    return json.dumps(data, indent=2, default=str)


def _import_from_json(uploaded_file) -> None:
    try:
        data = json.loads(uploaded_file.read())
        for k, v in data.items():
            if k.startswith("cvb_"):
                st.session_state[k] = v
        st.session_state["cvb_show_import"] = False
        st.rerun()
    except Exception as exc:
        st.error(f"Import failed: {exc}")


def _reset_all() -> None:
    keys = [k for k in st.session_state if k.startswith("cvb_")]
    for k in keys:
        del st.session_state[k]
    st.rerun()


# ─── Form section renderers ───────────────────────────────────────────────────

def _personal_section() -> None:
    st.text_input("Full Name", key="cvb_full_name", placeholder="Enter full name")
    st.text_input("Professional Title", key="cvb_prof_title", placeholder="Enter professional title")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Email", key="cvb_email", placeholder="you@email.com")
    with c2:
        st.text_input("Phone", key="cvb_phone", placeholder="Enter phone number")
    c3, c4 = st.columns(2)
    with c3:
        st.text_input("Location", key="cvb_location", placeholder="Enter location")
    with c4:
        st.text_input("Website", key="cvb_website", placeholder="Enter website URL")
    st.text_input("LinkedIn", key="cvb_linkedin", placeholder="Enter LinkedIn profile URL")
    st.text_input("GitHub", key="cvb_github", placeholder="Enter GitHub profile URL")


def _summary_section() -> None:
    summary = st.session_state.get("cvb_summary", "")
    char_count = len(summary)
    st.text_area(
        "Professional Summary",
        key="cvb_summary",
        height=130,
        max_chars=500,
        placeholder="Write a short summary of your experience and strengths.",
    )
    st.caption(f"{char_count}/500")


def _experience_section() -> None:
    _exp_spacer, _exp_action = st.columns([5, 2])
    with _exp_action:
        add_position = st.button("+ Add Position", key="btn_add_exp", type="secondary")
    if add_position:
        eid = str(uuid.uuid4())
        st.session_state["cvb_exp_ids"].append(eid)
        st.session_state[f"cvb_exp_bcount_{eid}"] = 1
        st.session_state[f"cvb_exp_b_{eid}_0"] = ""
        st.rerun()

    for idx, eid in enumerate(list(st.session_state.get("cvb_exp_ids", []))):
        role = st.session_state.get(f"cvb_exp_role_{eid}", "")
        label = role or f"Position {idx + 1}"
        with st.expander(label, expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Job Title", key=f"cvb_exp_role_{eid}", placeholder="Enter job title")
            with c2:
                st.text_input("Company", key=f"cvb_exp_company_{eid}", placeholder="Enter company name")
            with c3:
                st.text_input("Location", key=f"cvb_exp_loc_{eid}", placeholder="Enter location")

            c4, c5, c6 = st.columns(3)
            with c4:
                st.text_input("Start Date", key=f"cvb_exp_start_{eid}", placeholder="Enter start date")
            with c5:
                curr = st.session_state.get(f"cvb_exp_curr_{eid}", False)
                if not curr:
                    st.text_input("End Date", key=f"cvb_exp_end_{eid}", placeholder="Enter end date")
                else:
                    st.text_input("End Date", value="Present", disabled=True, key=f"cvb_exp_end_dis_{eid}")
            with c6:
                st.checkbox("Currently working here", key=f"cvb_exp_curr_{eid}")

            st.markdown("**Key Achievements**")
            bcount = st.session_state.get(f"cvb_exp_bcount_{eid}", 1)
            for i in range(bcount):
                st.text_input(
                    f"• Bullet {i + 1}",
                    key=f"cvb_exp_b_{eid}_{i}",
                    placeholder="Describe a measurable impact or responsibility",
                )

            ba, bb, bc, bd = st.columns([1, 1, 1.6, 1.6])
            with ba:
                if st.button("+ Bullet", key=f"add_b_{eid}"):
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount + 1
                    st.rerun()
            with bb:
                if bcount > 1 and st.button("− Bullet", key=f"rem_b_{eid}"):
                    st.session_state.pop(f"cvb_exp_b_{eid}_{bcount - 1}", None)
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount - 1
                    st.rerun()
            with bc:
                if st.button("✨ AI Suggest", key=f"ai_suggest_{eid}"):
                    role_val    = st.session_state.get(f"cvb_exp_role_{eid}", "").strip()
                    company_val = st.session_state.get(f"cvb_exp_company_{eid}", "").strip()
                    if not role_val:
                        st.warning("Enter a job title first.")
                    else:
                        with st.spinner("Generating…"):
                            try:
                                existing = [
                                    st.session_state.get(f"cvb_exp_b_{eid}_{i}", "")
                                    for i in range(bcount)
                                    if st.session_state.get(f"cvb_exp_b_{eid}_{i}", "").strip()
                                ]
                                context = ("Existing: " + " | ".join(existing)) if existing else ""
                                st.session_state[f"cvb_ai_sug_{eid}"] = suggest_cv_bullets(role_val, company_val, context)
                            except Exception as exc:
                                st.error(str(exc))
            with bd:
                if st.button("🗑 Delete Position", key=f"rem_exp_{eid}"):
                    st.session_state["cvb_exp_ids"].remove(eid)
                    st.session_state.pop(f"cvb_ai_sug_{eid}", None)
                    st.rerun()

            suggestions = st.session_state.get(f"cvb_ai_sug_{eid}", [])
            if suggestions:
                st.markdown("**AI Suggestions** — click Use to insert:")
                for si, sug in enumerate(suggestions):
                    sc1, sc2 = st.columns([6, 1])
                    with sc1:
                        st.caption(f"- {sug}")
                    with sc2:
                        if st.button("Use", key=f"use_s_{eid}_{si}"):
                            new_idx = st.session_state.get(f"cvb_exp_bcount_{eid}", 1)
                            st.session_state[f"cvb_exp_b_{eid}_{new_idx}"] = sug
                            st.session_state[f"cvb_exp_bcount_{eid}"] = new_idx + 1
                            st.rerun()


def _education_section() -> None:
    _edu_spacer, _edu_action = st.columns([5, 2])
    with _edu_action:
        add_education = st.button("+ Add Education", key="btn_add_edu", type="secondary")
    if add_education:
        eid = str(uuid.uuid4())
        st.session_state["cvb_edu_ids"].append(eid)
        st.rerun()

    for idx, eid in enumerate(list(st.session_state.get("cvb_edu_ids", []))):
        inst = st.session_state.get(f"cvb_edu_inst_{eid}", "")
        with st.expander(inst or f"Education {idx + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Institution", key=f"cvb_edu_inst_{eid}", placeholder="Enter institution name")
            with c2:
                st.text_input("Degree", key=f"cvb_edu_degree_{eid}", placeholder="Enter degree")
            with c3:
                st.text_input("Field of Study", key=f"cvb_edu_field_{eid}", placeholder="Enter field of study")
            c4, c5, c6 = st.columns(3)
            with c4:
                st.text_input("Location", key=f"cvb_edu_loc_{eid}", placeholder="Enter location")
            with c5:
                st.text_input("Start Year", key=f"cvb_edu_start_{eid}", placeholder="Enter start year")
            with c6:
                st.text_input("End Year", key=f"cvb_edu_end_{eid}", placeholder="Enter end year")
            st.text_input("GPA / Percentage", key=f"cvb_edu_gpa_{eid}", placeholder="Enter GPA or percentage")
            if st.button("🗑 Delete", key=f"rem_edu_{eid}"):
                st.session_state["cvb_edu_ids"].remove(eid)
                st.rerun()


def _skills_section() -> None:
    st.caption("Add skill categories (e.g. Languages, Frameworks, Tools). Items separated by commas.")
    if st.button("+ Add Category", key="btn_add_skill", type="secondary"):
        sid = str(uuid.uuid4())
        st.session_state["cvb_skill_cat_ids"].append(sid)
        st.rerun()
    for idx, sid in enumerate(list(st.session_state.get("cvb_skill_cat_ids", []))):
        name = st.session_state.get(f"cvb_skill_name_{sid}", "")
        with st.expander(name or f"Category {idx + 1}", expanded=True):
            st.text_input("Category Name", key=f"cvb_skill_name_{sid}", placeholder="Enter category name")
            st.text_area(
                "Skills (comma-separated)",
                key=f"cvb_skill_items_{sid}",
                height=70,
                placeholder="Enter skills separated by commas",
            )
            if st.button("🗑 Delete Category", key=f"rem_skill_{sid}"):
                st.session_state["cvb_skill_cat_ids"].remove(sid)
                st.rerun()


def _projects_section() -> None:
    if st.button("+ Add Project", key="btn_add_proj", type="secondary"):
        pid = str(uuid.uuid4())
        st.session_state["cvb_proj_ids"].append(pid)
        st.rerun()
    for idx, pid in enumerate(list(st.session_state.get("cvb_proj_ids", []))):
        name = st.session_state.get(f"cvb_proj_name_{pid}", "")
        with st.expander(name or f"Project {idx + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Project Name", key=f"cvb_proj_name_{pid}", placeholder="Enter project name")
            with c2:
                st.text_input("Your Role", key=f"cvb_proj_role_{pid}", placeholder="Enter your role")
            with c3:
                st.text_input("Date / Duration", key=f"cvb_proj_start_{pid}", placeholder="Enter date or duration")
            st.text_area("Description", key=f"cvb_proj_desc_{pid}", height=80,
                         placeholder="Describe what the project does and your impact")
            st.text_input("Technologies (comma-separated)", key=f"cvb_proj_tech_{pid}",
                          placeholder="Enter technologies separated by commas")
            st.text_input("Link (GitHub / Live)", key=f"cvb_proj_link_{pid}",
                          placeholder="Enter project link")
            if st.button("🗑 Delete", key=f"rem_proj_{pid}"):
                st.session_state["cvb_proj_ids"].remove(pid)
                st.rerun()


def _languages_section() -> None:
    if st.button("+ Add Language", key="btn_add_lang", type="secondary"):
        lid = str(uuid.uuid4())
        st.session_state["cvb_lang_ids"].append(lid)
        st.rerun()
    for idx, lid in enumerate(list(st.session_state.get("cvb_lang_ids", []))):
        lang_name = st.session_state.get(f"cvb_lang_name_{lid}", "")
        lbl = lang_name or f"Language {idx + 1}"
        with st.expander(lbl, expanded=True):
            c1, c2, c3 = st.columns([3, 3, 1])
            with c1:
                st.text_input("Language", key=f"cvb_lang_name_{lid}", placeholder="Enter language")
            with c2:
                st.selectbox("Proficiency", PROFICIENCY_OPTIONS, key=f"cvb_lang_prof_{lid}")
            with c3:
                st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
                if st.button("🗑", key=f"rem_lang_{lid}", help="Delete"):
                    st.session_state["cvb_lang_ids"].remove(lid)
                    st.rerun()


def _certifications_section() -> None:
    if st.button("+ Add Certification", key="btn_add_cert", type="secondary"):
        cid = str(uuid.uuid4())
        st.session_state["cvb_cert_ids"].append(cid)
        st.rerun()
    for idx, cid in enumerate(list(st.session_state.get("cvb_cert_ids", []))):
        name = st.session_state.get(f"cvb_cert_name_{cid}", "")
        with st.expander(name or f"Certification {idx + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Title", key=f"cvb_cert_name_{cid}", placeholder="Enter certification title")
            with c2:
                st.text_input("Issuer", key=f"cvb_cert_issuer_{cid}", placeholder="Enter issuer")
            with c3:
                st.text_input("Date", key=f"cvb_cert_date_{cid}", placeholder="Enter date")
            st.text_input("Credential URL", key=f"cvb_cert_link_{cid}", placeholder="Enter credential URL")
            if st.button("🗑 Delete", key=f"rem_cert_{cid}"):
                st.session_state["cvb_cert_ids"].remove(cid)
                st.rerun()


def _interests_section() -> None:
    interests = list(st.session_state.get("cvb_interests", []))
    if interests:
        tags_html = "<div style='display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.6rem'>" + "".join(
            f"<span style='display:inline-flex;align-items:center;gap:0.2rem;padding:0.2rem 0.6rem;"
            f"border-radius:999px;background:#dbeafe;color:#1d4ed8;font-size:0.82rem;font-weight:500'>"
            f"{_html_escape(t)}</span>"
            for t in interests
        ) + "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)
        remove_cols = st.columns(min(len(interests), 5))
        for i, interest in enumerate(interests):
            with remove_cols[i % 5]:
                if st.button(f"× {interest[:12]}", key=f"rm_int_{i}", help=f"Remove {interest}"):
                    interests.pop(i)
                    st.session_state["cvb_interests"] = interests
                    st.rerun()

    ctr   = st.session_state.get("cvb_interest_ctr", 0)
    ia, ib = st.columns([4, 1])
    with ia:
        new_tag = st.text_input(
            "Add interest",
            key=f"cvb_new_interest_{ctr}",
            label_visibility="collapsed",
            placeholder="Enter an interest",
        )
    with ib:
        if st.button("Add", key=f"btn_add_int_{ctr}"):
            tag = new_tag.strip()
            if tag and tag not in interests:
                interests.append(tag)
                st.session_state["cvb_interests"] = interests
                st.session_state["cvb_interest_ctr"] = ctr + 1
                st.rerun()


# ─── Left panel ───────────────────────────────────────────────────────────────

def _render_left_panel() -> None:
    """Deprecated legacy renderer."""
    return
    ss = st.session_state
    section_order = _normalize_section_order(ss.get("cvb_section_order"))
    visibility    = ss.get("cvb_section_visibility", {sid: True for sid in SECTION_IDS})

    st.markdown("<p class='cvb-rail-heading'>Sections</p>", unsafe_allow_html=True)
    sort_fn = _get_sortable_items()
    sortable_rendered = False
    if sort_fn is not None:
        display_items: list[str] = []
        display_to_id: dict[str, str] = {}
        for sec_id in section_order:
            label = SECTION_ID_TO_LABEL.get(sec_id, sec_id.title())
            vis_icon = "\U0001F441" if visibility.get(sec_id, True) else "\U0001F6AB"
            item_text = f"{label}   {vis_icon}"
            display_items.append(item_text)
            display_to_id[item_text] = sec_id

        sortable_style = """
        .sortable-component { background: transparent; padding: 0; margin: 0; border: 0; }
        .sortable-container { background: transparent; border: 0; padding: 0; margin: 0; overflow-x: hidden; }
        .sortable-container-header { display: none; }
        .sortable-container-body { background: transparent; overflow-x: hidden; }
        .sortable-item {
          position: relative;
          height: 54px;
          margin: 0 0 10px 0;
          width: 100%;
          box-sizing: border-box;
          border: 1px solid #cfd7e5;
          border-radius: 12px;
          background: #ffffff;
          display: flex;
          align-items: center;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
          color: #1f2937;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.2;
          padding: 0 14px 0 46px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          transform: none !important;
          transition: border-color .12s ease, box-shadow .12s ease !important;
        }
        .sortable-item::before {
          content: "⋮⋮";
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: #1f2937;
          font-size: 18px;
          line-height: 1;
          opacity: 0.9;
        }
        .sortable-item:focus,
        .sortable-item:active {
          transform: none !important;
        }
        .sortable-item:hover {
          box-shadow: 0 2px 6px rgba(2, 132, 199, 0.10);
          border-color: #93c5fd;
        }
        .sortable-chosen,
        .sortable-drag {
          transform: none !important;
          box-shadow: 0 2px 6px rgba(2, 132, 199, 0.10) !important;
          border-color: #93c5fd !important;
        }
        """
        try:
            sorted_items = sort_fn(display_items, key="cvb_sections_sortable_native", custom_style=sortable_style)
        except TypeError:
            sorted_items = sort_fn(display_items, custom_style=sortable_style)
        next_order = [display_to_id[item] for item in (sorted_items or []) if item in display_to_id]
        next_order = _normalize_section_order(next_order)
        if next_order != section_order:
            ss["cvb_section_order"] = next_order
            section_order = next_order
        sortable_rendered = True
    else:
        st.caption("Install `streamlit-sortables` to enable drag-and-drop section reordering.")
    for sec_name in section_order:
        is_vis = visibility.get(sec_name, True)
        label = SECTION_ID_TO_LABEL.get(sec_name, str(sec_name).title())
        col_name, col_eye = st.columns([5, 1], gap="small")
        with col_name:
            st.markdown(
                f"<div class='cvb-section-item'>⠿ {sec_name}</div>",
                unsafe_allow_html=True,
            )
        with col_eye:
            if st.button("👁" if is_vis else "🚫", key=f"vis_{sec_name.replace(' ','_')}", help="Toggle visibility"):
                visibility[sec_name] = not is_vis
                ss["cvb_section_visibility"] = visibility
                st.rerun()

    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='cvb-rail-heading'>Templates</p>", unsafe_allow_html=True)
    current_tpl = _normalize_template(ss.get("cvb_template", "classic"))
    ss["cvb_template"] = current_tpl
    for tpl_key, tpl_label, tpl_desc in TEMPLATE_CHOICES:
        ("classic", "Classic", "Single column · ATS-friendly"),
        ("modern",  "Modern",  "Colored header banner"),
        ("minimal", "Minimal", "Clean neutral style"),
        active = (current_tpl == tpl_key)
        active_cls = " active" if active else ""
        check_mark = "✓ " if active else ""
        st.markdown(
            f"<div class='cvb-template-card{active_cls}'>"
            f"<p class='cvb-template-title'>{tpl_label}</p>"
            f"<p class='cvb-template-desc'>{tpl_desc}</p></div>",
            unsafe_allow_html=True,
        )
        if not active:
            if st.button(f"Select", key=f"tpl_{tpl_key}", use_container_width=True):
                ss["cvb_template"] = tpl_key
                ss["cvb_zoom"] = _default_zoom_for_template(tpl_key)
                st.rerun()

    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='cvb-rail-heading'>Style</p>", unsafe_allow_html=True)

    st.markdown("<div class='cvb-label'>Accent Color</div>", unsafe_allow_html=True)
    with st.container(key="cvb-color-dots"):
        acc_cols = st.columns(len(ACCENT_COLORS))
        for i, (col, color) in enumerate(zip(acc_cols, ACCENT_COLORS)):
            with col:
                if st.button(" ", key=f"acc_{i}", help=color):
                    ss["cvb_accent_color"] = color
                    st.rerun()

    font_scale = round(float(ss.get("cvb_font_size", 11)) / 11.0, 2)
    st.markdown(f"<div class='cvb-label'>Font Scale <strong>{font_scale:.1f}x</strong></div>", unsafe_allow_html=True)
    st.slider("Font Scale", min_value=8, max_value=16, step=1, key="cvb_font_size", label_visibility="collapsed")

    spacing_scale = round(float(ss.get("cvb_entry_spacing", 8)) / 8.0, 2)
    st.markdown(f"<div class='cvb-label'>Spacing <strong>{spacing_scale:.1f}x</strong></div>", unsafe_allow_html=True)
    st.slider("Spacing", min_value=4, max_value=24, step=2, key="cvb_entry_spacing", label_visibility="collapsed")

    line_height = float(ss.get("cvb_line_height", 1.4))
    st.markdown(f"<div class='cvb-label'>Line Height <strong>{line_height:.1f}</strong></div>", unsafe_allow_html=True)
    st.slider("Line Height", min_value=1.0, max_value=2.0, step=0.1, key="cvb_line_height", label_visibility="collapsed")

    st.toggle("Show icons", key="cvb_show_icons")
    st.toggle("Show photo", key="cvb_show_photo")


# ─── Right panel (preview) ────────────────────────────────────────────────────

def _render_right_panel(cv_data: dict, is_dark: bool) -> None:
    """Deprecated legacy renderer."""
    return
    ss = st.session_state
    zoom = ss.get("cvb_zoom", 95)

    z1, z2, z3, z4 = st.columns([0.6, 1.7, 0.6, 0.6], gap="small", vertical_alignment="center")
    with z1:
        if st.button("−", key="btn_zoom_out", help="Zoom out"):
            levels = [60, 70, 75, 80, 85, 90, 95, 100, 110, 115]
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[max(0, idx - 1)]
            st.rerun()
    with z2:
        st.markdown(f"<div class='cvb-zoom-display'>{zoom}%</div>", unsafe_allow_html=True)
    with z3:
        if st.button("+", key="btn_zoom_in", help="Zoom in"):
            levels = [60, 70, 75, 80, 85, 90, 95, 100, 110, 115]
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[min(len(levels) - 1, idx + 1)]
            st.rerun()
    with z4:
        if st.button("⤢", key="btn_zoom_reset", help="Reset zoom"):
            ss["cvb_zoom"] = 45
            st.rerun()

    template      = ss.get("cvb_template", "classic")
    accent        = ss.get("cvb_accent_color") or None
    font          = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size     = int(ss.get("cvb_font_size", 11))
    line_height   = float(ss.get("cvb_line_height", 1.4))
    entry_spacing = int(ss.get("cvb_entry_spacing", 8))
    sec_vis       = ss.get("cvb_section_visibility")
    sec_order     = ss.get("cvb_section_order")

    preview_html = generate_cv_html(
        cv_data, template,
        accent_color=accent,
        font_family=font,
        font_size=font_size,
        line_height=line_height,
        entry_spacing=entry_spacing,
        preview_dark=is_dark,
        section_visibility=sec_vis,
        section_order=sec_order,
    )

    scale = zoom / 100.0
    # Wrap preview_html in a zoom shell so the CV paper scales without clipping
    zoomed_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; background: {'#060d1c' if is_dark else '#e2e8f0'}; }}
body {{ padding: 8px; }}
.cv-paper {{
  background: #ffffff;
  transform-origin: top center;
  transform: scale({scale});
  box-shadow: 0 4px 24px rgba(0,0,0,0.20);
  border-radius: 3px;
  width: {round(100 / scale)}%;
  margin: 0 auto;
  min-height: 1000px;
}}
</style></head><body>
<div class="cv-paper">{preview_html.split('<body>',1)[-1].split('</body>')[0] if '<body>' in preview_html else preview_html}</div>
<script>
// Forward postMessages from parent to this nested context
window.addEventListener('message', function(ev) {{
  var d = ev.data;
  if (!d || d.type !== 'cv-rt-update') return;
  var el;
  if (d.field === 'cvb_full_name') {{
    el = document.getElementById('cv-name');
    if (el) el.textContent = d.value || 'Your Name';
  }} else if (d.field === 'cvb_contact') {{
    el = document.getElementById('cv-contact');
    if (el) {{ el.textContent = d.value; el.style.display = d.value ? '' : 'none'; }}
  }}
}});
</script>
</body></html>"""

    frame_height = max(980, int(1123 * scale) + 120)
    with st.container(key="cvb-preview-frame"):
        components.html(zoomed_html, height=frame_height, scrolling=False)


# ─── Real-time JS bridge ──────────────────────────────────────────────────────

def _inject_realtime_js() -> None:
    components.html(
        """<script>
(function() {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;
  var CONTACT_LABELS = ['Email', 'Phone', 'Location', 'Website / Portfolio', 'LinkedIn', 'GitHub'];
  var NAME_LABEL = 'Full Name';

  function getInput(labelText, cardSel) {
    var card = doc.querySelector(cardSel);
    if (!card) return null;
    var labels = card.querySelectorAll('label');
    for (var i = 0; i < labels.length; i++) {
      if (labels[i].textContent.trim() === labelText) {
        var c = labels[i].closest('[data-testid="stTextInput"]');
        if (c) return c.querySelector('input');
      }
    }
    return null;
  }

  function computeContact(cardSel) {
    return CONTACT_LABELS
      .map(function(lbl) { var inp = getInput(lbl, cardSel); return inp ? inp.value.trim() : ''; })
      .filter(function(v) { return v.length > 0; })
      .join(' · ');
  }

  function broadcast(msg) {
    var iframes = doc.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
      try { iframes[i].contentWindow.postMessage(msg, '*'); } catch(e) {}
    }
  }

  function handleInput(e) {
    var input = e.target;
    if (!input || input.tagName !== 'INPUT') return;
    var CARD = '.st-key-cvb-personal-card, .st-key-cvb-center-panel';
    if (!input.closest(CARD)) return;
    var c = input.closest('[data-testid="stTextInput"]');
    if (!c) return;
    var lbl = c.querySelector('label');
    if (!lbl) return;
    var lt = lbl.textContent.trim();
    if (lt === NAME_LABEL) {
      broadcast({ type: 'cv-rt-update', field: 'cvb_full_name', value: input.value });
    } else if (CONTACT_LABELS.indexOf(lt) !== -1) {
      broadcast({ type: 'cv-rt-update', field: 'cvb_contact', value: computeContact(CARD) });
    }
  }

  var KEY = '__excalcv_rt__';
  if (doc[KEY]) doc.removeEventListener('input', doc[KEY], true);
  doc[KEY] = handleInput;
  doc.addEventListener('input', handleInput, true);
})();
</script>""",
        height=0,
    )


def _inject_sections_relay_js() -> None:
    """Relay postMessage events from the section-list iframe to hidden Streamlit buttons.

    The section-list iframe (components.html) posts:
      {type:'cvb-eye-toggle', sectionId:'education'}   — user clicked an eye button
      {type:'cvb-drag-end',   order:['education',...]}  — user finished a drag

    This relay (also a components.html, height=0) runs its script in the parent-page
    context, so it can freely access window.parent.document and click hidden buttons.
    """
    components.html("""<script>
(function() {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;

  function findBtn(classFragment) {
    return doc.querySelector('[class*="' + classFragment + '"] button') || null;
  }

  var KEY = '__cvb_sections_relay__';
  try { if (w[KEY]) w.removeEventListener('message', w[KEY]); } catch(e) {}

  w[KEY] = function(ev) {
    if (!ev.data || typeof ev.data !== 'object') return;

    if (ev.data.type === 'cvb-eye-toggle') {
      var sid = String(ev.data.sectionId || '');
      if (!sid) return;
      var btn = findBtn('st-key-cvb_eye_' + sid);
      if (!btn) btn = findBtn('st-key-cvb-eye-' + sid.replace(/_/g, '-'));
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-drag-end') {
      var movedId = String(ev.data.movedId || '');
      var newPos  = Number(ev.data.newPos);
      if (!movedId) return;
      var btn = findBtn('st-key-cvb_pos_' + movedId + '_' + newPos);
      if (!btn) btn = findBtn('st-key-cvb-pos-' + movedId.replace(/_/g,'-') + '-' + newPos);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-tpl-select') {
      var tpl = String(ev.data.tpl || '');
      if (!tpl) return;
      var btn = findBtn('st-key-cvb_tpl_' + tpl);
      if (!btn) btn = findBtn('st-key-cvb-tpl-' + tpl);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-acc-select') {
      var idx = String(ev.data.idx || '0');
      var btn = findBtn('st-key-cvb_acc_' + idx);
      if (!btn) btn = findBtn('st-key-cvb-acc-' + idx);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-scale-select') {
      var val = String(ev.data.val || '100');
      var btn = findBtn('st-key-cvb_scale_' + val);
      if (!btn) btn = findBtn('st-key-cvb-scale-' + val);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-icons-toggle') {
      var btn = findBtn('st-key-cvb_icons_toggle');
      if (!btn) btn = findBtn('st-key-cvb-icons-toggle');
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-photo-toggle') {
      var btn = findBtn('st-key-cvb_photo_toggle');
      if (!btn) btn = findBtn('st-key-cvb-photo-toggle');
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-lh-select') {
      var val = String(ev.data.val || '14');
      var btn = findBtn('st-key-cvb_lh_' + val);
      if (!btn) btn = findBtn('st-key-cvb-lh-' + val);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-es-select') {
      var val = String(ev.data.val || '8');
      var btn = findBtn('st-key-cvb_es_' + val);
      if (!btn) btn = findBtn('st-key-cvb-es-' + val);
      if (btn) { try { btn.click(); } catch(e) {} }
    }

    if (ev.data.type === 'cvb-zoom-toolbar') {
      var action = String(ev.data.action || '');
      var btn = null;
      if (action === 'out') {
        btn = findBtn('st-key-cvb_zoom_out_relay');
        if (!btn) btn = findBtn('st-key-cvb-zoom-out-relay');
      } else if (action === 'in') {
        btn = findBtn('st-key-cvb_zoom_in_relay');
        if (!btn) btn = findBtn('st-key-cvb-zoom-in-relay');
      } else if (action === 'reset') {
        btn = findBtn('st-key-cvb_zoom_reset_relay');
        if (!btn) btn = findBtn('st-key-cvb-zoom-reset-relay');
      }
      if (btn) { try { btn.click(); } catch(e) {} }
    }
  };

  w.addEventListener('message', w[KEY]);
})();
</script>""", height=0)


# ─── CSS injection ────────────────────────────────────────────────────────────

def _inject_persistent_scrollbar_js() -> None:
    """Deprecated no-op. Native panel scrollbars are now used directly."""
    return
    components.html(
        """<script>
(function() {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;
  var PANEL_SELECTORS = [
    '.st-key-cvb-left-scroll-native',
    '.st-key-cvb-middle-scroll-native',
    '.st-key-cvb-right-scroll-native'
  ];

  function ensureTrack(panel) {
    var track = panel.querySelector(':scope > .cvb-persistent-scrollbar-track');
    if (!track) {
      track = doc.createElement('div');
      track.className = 'cvb-persistent-scrollbar-track';
      var thumb = doc.createElement('div');
      thumb.className = 'cvb-persistent-scrollbar-thumb';
      track.appendChild(thumb);
      panel.appendChild(track);
    }
    return track;
  }

  function bindPanel(panel) {
    if (!panel) return;
    panel.style.setProperty('position', 'relative', 'important');
    var track = ensureTrack(panel);
    var thumb = track.firstElementChild;
    if (!thumb) return;

    function sync() {
      var clientH = Math.max(1, panel.clientHeight || 1);
      var scrollH = Math.max(1, panel.scrollHeight || clientH);
      var scrollTop = Math.max(0, panel.scrollTop || 0);
      var maxScroll = Math.max(1, scrollH - clientH);
      var thumbH = Math.max(24, Math.round(clientH * Math.min(1, clientH / scrollH)));
      var maxTop = Math.max(0, clientH - thumbH);
      var top = Math.round((scrollTop / maxScroll) * maxTop);

      track.style.height = clientH + 'px';
      thumb.style.height = thumbH + 'px';
      thumb.style.transform = 'translateY(' + top + 'px)';
      track.style.display = (scrollH > clientH + 1) ? 'block' : 'none';
    }

    if (!panel.__cvbPersistentScrollbarBound) {
      panel.addEventListener('scroll', sync, { passive: true });
      w.addEventListener('resize', sync);
      panel.__cvbPersistentScrollbarBound = true;
    }
    sync();
  }

  function apply() {
    for (var i = 0; i < PANEL_SELECTORS.length; i++) {
      var panel = doc.querySelector(PANEL_SELECTORS[i]);
      if (panel) bindPanel(panel);
    }
  }

  apply();
  setTimeout(apply, 120);
  setTimeout(apply, 420);
  setTimeout(apply, 900);

  if (w.__cvbPersistentScrollbarObserver) {
    w.__cvbPersistentScrollbarObserver.disconnect();
  }
  w.__cvbPersistentScrollbarObserver = new MutationObserver(function() { apply(); });
  w.__cvbPersistentScrollbarObserver.observe(doc.body, { childList: true, subtree: true });
})();
</script>""",
        height=0,
    )


def _inject_builder_css(is_dark: bool) -> None:
    """Compatibility wrapper for older call-sites."""
    _inject_builder_css_native(is_dark)
    return

    card_bg        = "#0f172a"  if is_dark else "#ffffff"
    page_bg        = "#060d1c"  if is_dark else "#f1f5f9"
    border_soft    = "rgba(148,163,184,0.18)" if is_dark else "rgba(15,23,42,0.10)"
    text_primary   = "#e2e8f0"  if is_dark else "#0f172a"
    text_muted     = "#94a3b8"  if is_dark else "#64748b"
    input_bg       = "#1e293b"  if is_dark else "#ffffff"
    input_text     = "#e2e8f0"  if is_dark else "#111827"
    input_border   = "rgba(148,163,184,0.28)" if is_dark else "rgba(15,23,42,0.16)"
    placeholder    = "#475569"  if is_dark else "#9ca3af"
    label_color    = "#94a3b8"  if is_dark else "#374151"
    accent_2       = "#60a5fa"  if is_dark else "#2563eb"
    expander_body  = "#1a2744"  if is_dark else "#f8fafc"
    shadow         = "0 2px 8px rgba(2,6,23,0.3)"  if is_dark else "0 2px 8px rgba(15,23,42,0.08)"
    scroll_thumb   = "#334155"  if is_dark else "#cbd5e1"
    scroll_track   = "#0f172a"  if is_dark else "#f1f5f9"
    toolbar_bg     = "#0a1628"  if is_dark else "#ffffff"

    # Build per-color dot CSS (must be before st.markdown so _dot_css is in scope)
    _cur_accent = st.session_state.get("cvb_accent_color", ACCENT_COLORS[0])
    _dot_parts: list[str] = []
    for _i, _c in enumerate(ACCENT_COLORS):
        _ring = (
            f"box-shadow:0 0 0 2px {card_bg},0 0 0 4px {_c} !important;"
            if _c == _cur_accent else ""
        )
        _dot_parts.append(
            f'.st-key-cvb-color-dots [data-testid="column"]:nth-child({_i + 1})'
            f" .stButton button {{ background:{_c} !important; {_ring} }}"
        )
    _dot_css = "\n".join(_dot_parts)

    st.markdown(f"""<style>
/* ── Hide footer & Streamlit chrome ────────────────────────────────── */
.site-footer-band {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="InputInstructions"] {{ display: none !important; }}

/* ── Block-container: full width, no padding ─────────────────────── */
[data-testid="stMainBlockContainer"],
section[data-testid="stMain"] .block-container {{
  max-width: 100% !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}}

/* ── Workspace: fixed overlay below site header ──────────────────── */
/* Start invisible at top:0 (behind header); JS measures header and   */
/* sets the correct top + makes it visible — no blank-space flash.    */
.st-key-cvb-workspace {{
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  overflow: hidden !important;
  z-index: 50 !important;
  visibility: hidden !important;
  background: {page_bg} !important;
}}
.st-key-cvb-workspace > [data-testid="stVerticalBlock"] {{
  background: {page_bg} !important;
}}

/* ── Toolbar ─────────────────────────────────────────────────────── */
.st-key-cvb-toolbar,
.st-key-cvb-toolbar > [data-testid="stVerticalBlock"] {{
  background: {toolbar_bg} !important;
  border-bottom: 1px solid {border_soft} !important;
  padding: 0.3rem 0.75rem !important;
}}
.cvb-saved-ts {{
  font-size: 0.78rem;
  color: {text_muted};
  line-height: 2.4;
  white-space: nowrap;
}}
.st-key-cvb-toolbar [data-testid="stTextInput"] {{
  margin-bottom: 0 !important;
}}

/* ── Panel height CSS variable — fallback keeps panels visible before JS runs */
:root {{ --cvb-panel-h: calc(100vh - 210px); }}

.st-key-cvb-main-grid [data-testid="stHorizontalBlock"] {{
  align-items: stretch !important;
  gap: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-main-grid [data-testid="column"] {{
  overflow: hidden !important;
  min-width: 0 !important;
}}

/* ── Left panel ──────────────────────────────────────────────────── */
/* Outer element-container: clips overflow so only the inner scrolls  */
.st-key-cvb-left-panel {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  background: {card_bg} !important;
  border-right: 1px solid {border_soft} !important;
}}
/* Inner stVerticalBlock: the actual scrollable surface.
   Two selectors cover: direct child (Pattern A) and one wrapper deep (Pattern C). */
.st-key-cvb-left-panel > [data-testid="stVerticalBlock"],
.st-key-cvb-left-panel > div > [data-testid="stVerticalBlock"] {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-width: thin;
  scrollbar-color: {scroll_thumb} {scroll_track};
  box-sizing: border-box !important;
  padding: 0.65rem 0.6rem !important;
}}
.st-key-cvb-left-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-left-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar {{ width: 7px; }}
.st-key-cvb-left-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track,
.st-key-cvb-left-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track {{ background: {scroll_track}; }}
.st-key-cvb-left-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb,
.st-key-cvb-left-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{ background: {scroll_thumb}; border-radius: 4px; }}
.st-key-cvb-left-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover,
.st-key-cvb-left-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover {{ background: {"#64748b" if is_dark else "#94a3b8"}; }}

/* ── Center panel ────────────────────────────────────────────────── */
.st-key-cvb-center-panel {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  background: {page_bg} !important;
}}
.st-key-cvb-center-panel > [data-testid="stVerticalBlock"],
.st-key-cvb-center-panel > div > [data-testid="stVerticalBlock"] {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-width: thin;
  scrollbar-color: {scroll_thumb} {scroll_track};
  box-sizing: border-box !important;
  padding: 0.65rem 0.85rem !important;
}}
.st-key-cvb-center-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-center-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar {{ width: 7px; }}
.st-key-cvb-center-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track,
.st-key-cvb-center-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track {{ background: {scroll_track}; }}
.st-key-cvb-center-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb,
.st-key-cvb-center-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{ background: {scroll_thumb}; border-radius: 4px; }}
.st-key-cvb-center-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover,
.st-key-cvb-center-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover {{ background: {"#64748b" if is_dark else "#94a3b8"}; }}

/* ── Right panel: no CSS scroll (iframe handles its own scroll) ──── */
.st-key-cvb-right-panel {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  background: {page_bg} !important;
  border-left: 1px solid {border_soft} !important;
  padding: 0.65rem 0.7rem !important;
}}
.st-key-cvb-right-panel > [data-testid="stVerticalBlock"],
.st-key-cvb-right-panel > div > [data-testid="stVerticalBlock"] {{
  height: var(--cvb-panel-h) !important;
  min-height: 320px !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-width: thin;
  scrollbar-color: {scroll_thumb} {scroll_track};
  box-sizing: border-box !important;
}}
.st-key-cvb-right-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-right-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar {{ width: 7px; }}
.st-key-cvb-right-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track,
.st-key-cvb-right-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track {{ background: {scroll_track}; }}
.st-key-cvb-right-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb,
.st-key-cvb-right-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{ background: {scroll_thumb}; border-radius: 4px; }}
.st-key-cvb-right-panel > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover,
.st-key-cvb-right-panel > div > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover {{ background: {"#64748b" if is_dark else "#94a3b8"}; }}

/* ── Labels ─────────────────────────────────────────────────────── */
.st-key-cvb-workspace .stTextInput label,
.st-key-cvb-workspace .stTextArea label,
.st-key-cvb-workspace .stSelectbox label,
.st-key-cvb-workspace .stNumberInput label,
.st-key-cvb-workspace .stCheckbox label,
.st-key-cvb-workspace .stColorPicker label,
.st-key-cvb-workspace .stSlider label {{
  font-size: 0.82rem !important;
  color: {label_color} !important;
  font-weight: 600 !important;
}}

/* ── Inputs ──────────────────────────────────────────────────────── */
.st-key-cvb-workspace div[data-baseweb="input"],
.st-key-cvb-workspace div[data-baseweb="input"] > div,
.st-key-cvb-workspace div[data-baseweb="input"] > div > div {{
  background: {input_bg} !important;
  border-color: {input_border} !important;
}}
.st-key-cvb-workspace .stTextInput input,
.st-key-cvb-workspace div[data-baseweb="input"] input {{
  background: {input_bg} !important;
  color: {input_text} !important;
  border-color: {input_border} !important;
  border-radius: 8px !important;
  font-size: 0.87rem !important;
}}
.st-key-cvb-workspace .stTextInput input::placeholder,
.st-key-cvb-workspace div[data-baseweb="input"] input::placeholder {{
  color: {placeholder} !important; opacity: 1 !important;
}}

/* ── Textarea ────────────────────────────────────────────────────── */
.st-key-cvb-workspace div[data-baseweb="textarea"],
.st-key-cvb-workspace div[data-baseweb="textarea"] > div {{
  background: {input_bg} !important;
  border-color: {input_border} !important;
}}
.st-key-cvb-workspace .stTextArea textarea {{
  background: {input_bg} !important;
  color: {input_text} !important;
  border-color: {input_border} !important;
  border-radius: 8px !important;
  font-size: 0.87rem !important;
}}
.st-key-cvb-workspace .stTextArea textarea::placeholder {{
  color: {placeholder} !important; opacity: 1 !important;
}}

/* ── Selectbox ───────────────────────────────────────────────────── */
.st-key-cvb-workspace div[data-baseweb="select"] > div {{
  background: {input_bg} !important;
  border-color: {input_border} !important;
  border-radius: 8px !important;
}}
.st-key-cvb-workspace div[data-baseweb="select"] span {{
  color: {input_text} !important; font-size: 0.87rem !important;
}}

/* ── Expanders ───────────────────────────────────────────────────── */
.st-key-cvb-center-panel [data-testid="stExpander"] {{ margin: 0 0 0.45rem !important; }}
.st-key-cvb-center-panel [data-testid="stExpander"] details {{
  background: {card_bg};
  border: 1px solid {border_soft};
  border-radius: 12px;
  overflow: hidden;
  box-shadow: {shadow};
}}
.st-key-cvb-center-panel [data-testid="stExpander"] summary {{
  padding: 0.65rem 0.9rem !important;
  background: {card_bg} !important;
}}
.st-key-cvb-center-panel [data-testid="stExpander"] summary p,
.st-key-cvb-center-panel [data-testid="stExpander"] summary span {{
  font-size: 0.93rem !important;
  font-weight: 700 !important;
  color: {text_primary} !important;
}}
.st-key-cvb-center-panel [data-testid="stExpander"] details > div {{
  background: {expander_body} !important;
  padding: 0 0.9rem 0.75rem !important;
}}

/* ── Left rail items ─────────────────────────────────────────────── */
.cvb-rail-heading {{
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.07em; text-transform: uppercase;
  color: {text_muted};
  margin: 14px 0 10px;
  padding: 0;
  display: block;
  line-height: 1.25;
  position: relative;
  z-index: 2;
  clear: both;
}}
.cvb-section-item {{
  padding: 0.35rem 0.55rem;
  border: 1px solid {border_soft};
  border-radius: 8px;
  margin-bottom: 0.28rem;
  background: {page_bg};
  color: {text_primary};
  font-size: 0.86rem; font-weight: 500;
}}
.st-key-cvb-left-panel [data-testid="column"]:last-child .stButton button {{
  padding: 0.1rem 0.2rem !important;
  min-height: unset !important;
  height: 28px !important;
  font-size: 0.75rem !important;
  background: transparent !important;
  border: none !important;
  color: {text_muted} !important;
}}
.cvb-rail-divider {{
  margin: 0.95rem 0 0.7rem;
  border-top: 1px solid {border_soft};
}}
.cvb-template-card {{
  border: 1px solid {border_soft};
  border-radius: 9px;
  padding: 0.48rem 0.65rem;
  margin-bottom: 0.28rem;
  background: {page_bg};
}}
.cvb-template-card.active {{
  border-color: {accent_2};
  background: {"#1e3a5f" if is_dark else "#eff6ff"};
  box-shadow: 0 0 0 1px rgba(37,99,235,0.18);
}}
.cvb-template-title {{
  margin: 0; color: {text_primary};
  font-weight: 700; font-size: 0.88rem;
}}
.cvb-template-desc {{
  margin: 0.12rem 0 0; color: {text_muted}; font-size: 0.78rem;
}}
.cvb-style-label {{
  font-size: 0.82rem; color: {text_muted}; margin: 0.3rem 0 0.15rem;
}}

/* ── Zoom bar ────────────────────────────────────────────────────── */
.cvb-zoom-display {{
  text-align: center;
  font-size: 0.8rem; color: {text_muted};
  border: 1px solid {border_soft};
  border-radius: 999px;
  padding: 0.1rem 0.4rem;
  background: {card_bg};
}}

/* ── Preview iframe ──────────────────────────────────────────────── */
.st-key-cvb-preview-frame iframe {{
  width: 100% !important;
  border: 1px solid {border_soft} !important;
  border-radius: 8px !important;
  background: #ffffff !important;
}}

/* ── Buttons ─────────────────────────────────────────────────────── */
.st-key-cvb-workspace .stButton button,
.st-key-cvb-workspace .stDownloadButton button {{
  font-size: 0.82rem !important;
  border-radius: 7px !important;
}}
.st-key-cvb-toolbar .stButton button,
.st-key-cvb-toolbar .stDownloadButton button {{
  font-size: 0.82rem !important;
  border-radius: 7px !important;
  padding: 0.3rem 0.65rem !important;
}}

/* ── Markdown text ───────────────────────────────────────────────── */
.st-key-cvb-workspace .stMarkdown p,
.st-key-cvb-workspace .stMarkdown span,
.st-key-cvb-workspace .stCaption span {{
  color: {text_muted} !important;
}}
.st-key-cvb-workspace .stMarkdown strong,
.st-key-cvb-workspace .stMarkdown b {{
  color: {text_primary} !important;
}}

/* ── Section item rows: name + eye as one seamless flex row ──────── */
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) {{
  gap: 0 !important;
  margin-bottom: 0.25rem;
  align-items: stretch !important;
}}
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) .cvb-section-item {{
  border-radius: 8px 0 0 8px !important;
  border-right: none !important;
  margin-bottom: 0 !important;
  min-height: 34px;
  height: 34px;
  display: flex !important;
  align-items: center !important;
}}
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) [data-testid="column"]:last-child {{
  display: flex !important;
  align-items: stretch !important;
  min-width: 0 !important;
}}
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) [data-testid="column"]:last-child .stButton,
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) [data-testid="column"]:last-child .stButton > div {{
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
}}
.st-key-cvb-left-panel [data-testid="stHorizontalBlock"]:has(.cvb-section-item) [data-testid="column"]:last-child .stButton button {{
  border-radius: 0 8px 8px 0 !important;
  border: 1px solid {border_soft} !important;
  border-left: none !important;
  min-height: 34px !important;
  height: 100% !important;
  width: 100% !important;
  background: {page_bg} !important;
  color: {text_muted} !important;
  padding: 0 !important;
  font-size: 0.82rem !important;
}}

/* ── Accent color dot buttons: filled circles ────────────────────── */
.st-key-cvb-color-dots [data-testid="stHorizontalBlock"] {{
  gap: 4px !important;
  flex-wrap: wrap !important;
  padding: 2px 0 !important;
}}
.st-key-cvb-color-dots .stButton button {{
  border-radius: 50% !important;
  width: 22px !important;
  height: 22px !important;
  min-width: 22px !important;
  min-height: 22px !important;
  max-width: 22px !important;
  max-height: 22px !important;
  padding: 0 !important;
  color: transparent !important;
  font-size: 0 !important;
  line-height: 0 !important;
  border: 2px solid transparent !important;
  margin: 0 auto !important;
  display: block !important;
}}
/* Per-color backgrounds injected dynamically */
{_dot_css}

/* ── Download PDF button: always blue ────────────────────────────── */
.st-key-cvb-toolbar [data-testid="stDownloadButton"] button[kind="primary"],
.st-key-cvb-toolbar [data-testid="stDownloadButton"] button[data-testid="baseButton-primary"] {{
  background: #2563eb !important;
  color: #ffffff !important;
  border-color: #2563eb !important;
}}
</style>""", unsafe_allow_html=True)

    # JS: update --cvb-panel-h CSS variable with real measurements.
    # Using a CSS variable (not direct element.style) means the panels are
    # ALWAYS visible via the calc() fallback, and JS only refines the height.
    components.html(f"""<script>
(function() {{
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;
  var PAGE_BG = '{page_bg}';

  function findInner(outerEl) {{
    // Handles all Streamlit DOM patterns for st.container(key=...):
    //   Pattern A: .st-key-xyz.element-container > [data-testid="stVerticalBlock"]
    //   Pattern B: .st-key-xyz IS the stVerticalBlock itself
    //   Pattern C: .st-key-xyz > stVerticalBlockBorderWrapper > stVerticalBlock
    if (!outerEl) return null;
    if (outerEl.getAttribute('data-testid') === 'stVerticalBlock') return outerEl;
    var direct = outerEl.querySelector(':scope > [data-testid="stVerticalBlock"]');
    if (direct) return direct;
    return outerEl.querySelector('[data-testid="stVerticalBlock"]') || null;
  }}

  function applyLayout() {{
    // 1. Measure where the fixed site header ends (robust fallback chain).
    function getTopOffset() {{
      var spacer = doc.getElementById('excelcv-fixed-header-spacer');
      if (spacer) {{
        var spacerRect = spacer.getBoundingClientRect();
        if (spacerRect && spacerRect.height > 40) {{
          return Math.ceil(spacerRect.bottom);
        }}
      }}
      var rule = doc.querySelector('.site-header-rule');
      if (rule) {{
        var ruleRect = rule.getBoundingClientRect();
        if (ruleRect && ruleRect.bottom > 20) {{
          return Math.ceil(ruleRect.bottom);
        }}
      }}
      var header = doc.querySelector('[data-testid="stHorizontalBlock"]:has(.site-brand)');
      if (header) {{
        var headerRect = header.getBoundingClientRect();
        if (headerRect && headerRect.bottom > 20) {{
          return Math.ceil(headerRect.bottom + 8);
        }}
      }}
      return 96;
    }}
    var headerBottom = Math.max(86, getTopOffset());

    // 2. Position the workspace as a fixed overlay starting just below the header.
    //    visibility: hidden → visible prevents any blank-space flash before measurement.
    var workspace = doc.querySelector('.st-key-cvb-workspace');
    if (workspace) {{
      workspace.style.setProperty('position',   'fixed',             'important');
      workspace.style.setProperty('top',        headerBottom + 'px', 'important');
      workspace.style.setProperty('left',       '0',                 'important');
      workspace.style.setProperty('right',      '0',                 'important');
      workspace.style.setProperty('bottom',     '0',                 'important');
      workspace.style.setProperty('overflow',   'hidden',            'important');
      workspace.style.setProperty('z-index',    '50',                'important');
      workspace.style.setProperty('visibility', 'visible',           'important');
      workspace.style.setProperty('background', PAGE_BG,             'important');
    }}

    // 3. Compute panel height = available space below header minus toolbar
    var toolbar  = doc.querySelector('.st-key-cvb-toolbar');
    var toolbarH = toolbar ? Math.ceil(toolbar.getBoundingClientRect().height) : 52;
    var panelH   = Math.max(320, w.innerHeight - headerBottom - toolbarH - 4);

    doc.documentElement.style.setProperty('--cvb-panel-h', panelH + 'px');

    // 4. For each panel: outer element-container clips (overflow:hidden),
    //    inner stVerticalBlock scrolls (overflow-y:scroll or hidden for right).
    //    This gives each panel exactly ONE scrollbar track.
    var panels = [
      {{ sel: '.st-key-cvb-left-panel',   innerScroll: 'scroll' }},
      {{ sel: '.st-key-cvb-center-panel', innerScroll: 'scroll' }},
      {{ sel: '.st-key-cvb-right-panel',  innerScroll: 'scroll' }}
    ];
    for (var i = 0; i < panels.length; i++) {{
      var outerEl = doc.querySelector(panels[i].sel);
      if (!outerEl) continue;

      outerEl.style.setProperty('height',     panelH + 'px', 'important');
      outerEl.style.setProperty('min-height', '320px',       'important');
      outerEl.style.setProperty('overflow',   'hidden',      'important');
      outerEl.style.setProperty('box-sizing', 'border-box',  'important');

      var innerEl = findInner(outerEl);
      if (!innerEl) continue;

      innerEl.style.setProperty('height',     panelH + 'px', 'important');
      innerEl.style.setProperty('min-height', '320px',       'important');
      innerEl.style.setProperty('overflow-y', panels[i].innerScroll, 'important');
      innerEl.style.setProperty('overflow-x', 'hidden',      'important');
      innerEl.style.setProperty('box-sizing', 'border-box',  'important');
    }}
  }}

  applyLayout();
  w.addEventListener('resize', applyLayout);
  [80, 250, 600, 1400].forEach(function(ms) {{ setTimeout(applyLayout, ms); }});

  var debounce;
  new MutationObserver(function(muts) {{
    for (var i = 0; i < muts.length; i++) {{
      if (muts[i].addedNodes.length || muts[i].removedNodes.length) {{
        clearTimeout(debounce);
        debounce = setTimeout(applyLayout, 100);
        break;
      }}
    }}
  }}).observe(doc.body, {{ childList: true, subtree: true }});
}})();
</script>""", height=0)


# ─── Main page renderer ───────────────────────────────────────────────────────

def _inject_builder_css_native(is_dark: bool) -> None:
    page_bg = "#0b1220" if is_dark else "#f3f5f8"
    panel_bg = "#0f172a" if is_dark else "#ffffff"
    border = "#334155" if is_dark else "#d3dce8"
    text = "#e2e8f0" if is_dark else "#0f172a"
    muted = "#94a3b8" if is_dark else "#64748b"
    cur_accent = st.session_state.get("cvb_accent_color", ACCENT_COLORS[0])
    native_dot_parts: list[str] = []
    for i, color in enumerate(ACCENT_COLORS):
        ring = f"box-shadow:0 0 0 2px #ffffff,0 0 0 4px {color} !important;" if color == cur_accent else ""
        native_dot_parts.append(
            f'.st-key-cvb-color-dots-native [class*="st-key-acc_native_{i}"] button '
            f'{{ background:{color} !important; {ring} }}'
        )
    native_dot_css = "\n".join(native_dot_parts)
    st.markdown(
        f"""<style>
.site-footer-band {{ display:none !important; }}
.st-key-cvb-page-native {{
  height: calc(100vh - 92px) !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  background: {page_bg} !important;
  margin: 0 !important;
  padding: 0 !important;
}}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{
  gap: 0 !important;
  row-gap: 0 !important;
}}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(.st-key-cvb-page-native),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(.st-key-cvb-toolbar-native),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.st-key-cvb-page-native) {{
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
.st-key-cvb-page-native > div,
.st-key-cvb-page-native [data-testid="stVerticalBlock"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
  gap: 0 !important;
}}
[data-testid="stAppViewContainer"]:has(.st-key-cvb-page-native),
[data-testid="stMain"]:has(.st-key-cvb-page-native) {{
  height: 100vh !important;
  overflow: hidden !important;
}}
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native),
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native) .block-container,
section[data-testid="stMain"]:has(.st-key-cvb-page-native) .block-container {{
  height: 100vh !important;
  min-height: 0 !important;
  overflow: hidden !important;
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
  padding-bottom: 0 !important;
}}
.st-key-cvb-toolbar-native {{
  height: 56px !important;
  min-height: 56px !important;
  display: flex !important;
  align-items: center !important;
  flex-shrink: 0 !important;
  background: linear-gradient(90deg, #edf3fa 0%, #f6f9fe 18%, #ffffff 48%, #ffffff 100%) !important;
  border-top:1px solid #d7e1ec !important;
  border-bottom:1px solid #d7e1ec !important;
  border-radius:0;
  padding:0 20px !important;
  margin:0 !important;
}}
.st-key-cvb-toolbar-native > div,
.st-key-cvb-toolbar-native [data-testid="stVerticalBlock"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}}
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] {{
  align-items: center !important;
}}
.cvb-saved-ts-native {{
  display:inline-flex;
  align-items:center;
  min-height: 24px;
  padding: 3px 11px;
  border-radius:999px;
  background: rgba(0, 89, 179, 0.10);
  color:#0059B3;
  font-size:12px;
  font-weight:500;
  line-height: 1;
  border:1px solid rgba(0, 89, 179, 0.22);
  white-space:nowrap;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 12px !important;
  flex-wrap: nowrap !important;
  white-space: nowrap !important;
}}
.st-key-cvb-toolbar-actions-native {{
  display: block !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="column"] {{
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: fit-content !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  white-space: nowrap !important;
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  width: auto !important;
  min-width: auto !important;
  max-width: none !important;
  height: 40px !important;
  padding: 0 12px !important;
  border-radius: 8px !important;
  border: none !important;
  outline: none !important;
  border: none !important;
  background: transparent !important;
  color: #65758B !important;
  box-shadow: none !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  flex-direction: row !important;
  cursor: pointer !important;
  transition: background-color .16s ease, color .16s ease, box-shadow .16s ease !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button {{
  width: 88px !important;
  min-width: 88px !important;
  max-width: 88px !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button {{
  width: 93px !important;
  min-width: 93px !important;
  max-width: 93px !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button {{
  width: 80px !important;
  min-width: 80px !important;
  max-width: 80px !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button::before,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button::before,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button::before {{
  content: "" !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 16px !important;
  height: 16px !important;
  margin-right: 4px !important;
  line-height: 1 !important;
  background-color: currentColor !important;
  -webkit-mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  -webkit-mask-size: 16px 16px !important;
  mask-repeat: no-repeat !important;
  mask-position: center !important;
  mask-size: 16px 16px !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button::before {{
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M12 16V4m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M12 16V4m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2'/%3E%3C/svg%3E") !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button::before {{
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M4 7a2 2 0 0 1 2-2h9l5 5v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 3v5h6'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M4 7a2 2 0 0 1 2-2h9l5 5v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 3v5h6'/%3E%3C/svg%3E") !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button::before {{
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M4 4v6h6M20 20v-6h-6'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M20 9a8 8 0 0 0-13.66-4.66L4 6m16 12l-2.34 1.66A8 8 0 0 1 4 15'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M4 4v6h6M20 20v-6h-6'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M20 9a8 8 0 0 0-13.66-4.66L4 6m16 12l-2.34 1.66A8 8 0 0 1 4 15'/%3E%3C/svg%3E") !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:focus-visible,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:focus-visible {{
  background: #eff4fa !important;
  color: #0d5ec0 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button:focus-visible {{
  background: #fcebec !important;
  color: #e53935 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"],
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"] {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  white-space: nowrap !important;
  height: 40px !important;
  width: 176px !important;
  min-width: 176px !important;
  max-width: 176px !important;
  padding: 0 12px !important;
  border-radius: 8px !important;
  background:#0059B3 !important;
  border-color:#0059B3 !important;
  border: none !important;
  color:#FAFAFA !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  text-shadow: none !important;
  transition: background-color .16s ease, color .16s ease !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"]::before,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"]::before {{
  content: "" !important;
  display: inline-flex !important;
  width: 14px !important;
  height: 14px !important;
  margin-right: 4px !important;
  line-height: 1 !important;
  background-color: #FAFAFA !important;
  -webkit-mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  -webkit-mask-size: 14px 14px !important;
  mask-repeat: no-repeat !important;
  mask-position: center !important;
  mask-size: 14px 14px !important;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpolyline points='7 10 12 15 17 10' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cline x1='12' y1='15' x2='12' y2='3' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpolyline points='7 10 12 15 17 10' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cline x1='12' y1='15' x2='12' y2='3' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"]:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"]:focus-visible,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"]:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"]:focus-visible {{
  background: #0059B3 !important;
  border-color: #0059B3 !important;
  box-shadow: 0 1px 2px rgba(0, 89, 179, 0.32), 0 0 0 3px rgba(0, 89, 179, 0.20) !important;
  color: #FAFAFA !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button *,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button p,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button span {{
  color: #FAFAFA !important;
}}
.st-key-cvb-toolbar-actions-native button p {{
  margin: 0 !important;
  line-height: 1 !important;
}}
.st-key-cvb-main-native {{
  --cvb-native-panel-h: calc(100vh - 145px);
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  flex: 1 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 0 8px 0 !important;
  margin: 0 !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] {{
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  align-items: stretch !important;
  gap: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  height: 100% !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {{
  flex: 0 0 256px !important;
  width: 256px !important;
  min-width: 256px !important;
  max-width: 256px !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {{
  flex: 9 1 0 !important;
  width: auto !important;
  max-width: none !important;
  min-width: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {{
  flex: 7 1 0 !important;
  width: auto !important;
  max-width: none !important;
  min-width: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stElementContainer"],
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"] {{
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
}}
.st-key-cvb-middle-scroll-native {{
  background:#f3f5f8;
  border:none;
  border-radius:0;
  padding:8px !important;
  margin:0 !important;
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  scrollbar-width: thin !important;
  scrollbar-color: #c1c7cd #e6ebf2 !important;
}}
.st-key-cvb-right-scroll-native {{
  background:#f6f7f9;
  border-left:1px solid #d3dce8;
  border-top:none;
  border-right:none;
  border-bottom:none;
  border-radius:0;
  padding:8px !important;
  margin:0 !important;
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  scrollbar-width: thin !important;
  scrollbar-color: #c1c7cd #e6ebf2 !important;
}}
.st-key-cvb-left-scroll-native {{
  background:#f7f9fc;
  border-right:1px solid #d3dce8;
  border-left:none;
  border-top:none;
  border-bottom:none;
  border-radius:0;
  padding:16px !important;
  margin:0 !important;
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  scrollbar-width: thin !important;
  scrollbar-color: #c1c7cd #e6ebf2 !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading {{
  font-size: 12px !important;
  font-weight: 600 !important;
  font-family: Poppins, Montserrat, system-ui, sans-serif !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: #65758b !important;
  margin: 0 0 8px 0 !important;
  padding: 0 !important;
  line-height: 1.35 !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  position: relative !important;
  z-index: 2 !important;
  clear: both !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"] > div:first-child .cvb-rail-heading {{
  margin-top: 0 !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading-icon {{
  width: 14px !important;
  height: 14px !important;
  line-height: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: #65758b !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading-icon svg {{
  width: 14px !important;
  height: 14px !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"],
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"] {{
  min-height: 0 !important;
  overflow: visible !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar,
.st-key-cvb-right-scroll-native::-webkit-scrollbar {{
  width: 6px !important;
  height: 6px !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar-track,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar-track,
.st-key-cvb-right-scroll-native::-webkit-scrollbar-track {{
  background: transparent !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar-thumb,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar-thumb,
.st-key-cvb-right-scroll-native::-webkit-scrollbar-thumb {{
  background: #c1c7cd !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar-thumb:hover,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar-thumb:hover,
.st-key-cvb-right-scroll-native::-webkit-scrollbar-thumb:hover {{
  background: #aeb6bf !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar {{
  width: 6px !important;
  height: 6px !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] {{
  margin: 0 0 12px !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] details {{
  background: #ffffff !important;
  border: 1px solid #d3dce8 !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] summary {{
  min-height: 58px !important;
  padding: 0 18px !important;
  background: #ffffff !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] summary p,
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] summary span {{
  color: #0f172a !important;
  font-size: 17px !important;
  font-weight: 700 !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] summary svg {{
  color: #0b63ce !important;
}}
.st-key-cvb-middle-scroll-native [data-testid="stExpander"] details > div {{
  background: #ffffff !important;
  border-top: 1px solid #e2e8f0 !important;
  padding: 10px 18px 18px !important;
}}
.st-key-cvb-middle-scroll-native .stTextInput label,
.st-key-cvb-middle-scroll-native .stTextArea label,
.st-key-cvb-middle-scroll-native .stSelectbox label,
.st-key-cvb-middle-scroll-native .stCheckbox label {{
  color: #475569 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}}
.st-key-cvb-middle-scroll-native .stTextInput input,
.st-key-cvb-middle-scroll-native .stTextArea textarea,
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea,
.st-key-cvb-middle-scroll-native div[data-baseweb="select"] > div {{
  border: 1px solid #cfd8e3 !important;
  background: #f8fafc !important;
  border-radius: 10px !important;
  color: #0f172a !important;
  font-size: 15px !important;
  min-height: 48px !important;
}}
.st-key-cvb-middle-scroll-native .stTextArea textarea {{
  min-height: 118px !important;
}}
.st-key-cvb-middle-scroll-native .stTextInput input::placeholder,
.st-key-cvb-middle-scroll-native .stTextArea textarea::placeholder,
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input::placeholder,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea::placeholder {{
  color: #64748b !important;
  opacity: 1 !important;
}}
.st-key-cvb-middle-scroll-native .stButton button,
.st-key-cvb-middle-scroll-native .stDownloadButton button {{
  height: 42px !important;
  min-height: 42px !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}}
.st-key-cvb-section-experience [class*="st-key-btn_add_exp"] button,
.st-key-cvb-section-education [class*="st-key-btn_add_edu"] button,
.st-key-cvb-section-skills [class*="st-key-btn_add_skill"] button,
.st-key-cvb-section-projects [class*="st-key-btn_add_proj"] button,
.st-key-cvb-section-languages [class*="st-key-btn_add_lang"] button,
.st-key-cvb-section-certifications [class*="st-key-btn_add_cert"] button {{
  background: #eaf2fb !important;
  color: #0b63ce !important;
  border: 1px solid #b8d4f3 !important;
  box-shadow: none !important;
  height: 34px !important;
  min-height: 34px !important;
  border-radius: 999px !important;
  padding: 0 16px !important;
}}
.cvb-rail-heading {{
  font-size:12px;
  font-weight:600;
  font-family:Poppins,Montserrat,system-ui,sans-serif;
  letter-spacing:0.08em;
  color:#65758b;
  text-transform:uppercase;
  margin:0 0 8px;
  padding:0;
  display:flex;
  align-items:center;
  gap:8px;
  line-height:1.35;
  position:relative;
  z-index:2;
  clear:both;
}}
.cvb-rail-divider {{
  border-top:1px solid #dbe3ef;
  margin:12px 0 12px;
}}
.cvb-rail-heading-icon {{
  width:14px;
  height:14px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  line-height:0;
}}
.cvb-rail-heading-icon svg {{
  width:14px;
  height:14px;
}}

/* All relay-driven hidden buttons are grouped inside .st-key-cvb-hidden-buttons.
   Collapsing the single container to 0-height takes them out of the flow entirely.
   JS .click() still fires through position:absolute + overflow:hidden. */
.st-key-cvb-left-scroll-native .st-key-cvb-hidden-buttons {{
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}}
/* Section-list custom component iframe — full width, no extra margin */
.st-key-cvb-left-scroll-native [data-testid="stCustomComponentV1"] {{
  width: 100% !important;
  margin: 0 0 8px 0 !important;
  padding: 0 !important;
  display: block !important;
  position: relative !important;
  z-index: 1 !important;
}}

.cvb-style-label, .cvb-label {{ font-size:14px; color:#334155; margin:10px 0 4px; font-weight:500; }}
.st-key-cvb-style-section-native {{
  display: flex !important;
  flex-direction: column !important;
  gap: 14px !important;
  overflow: visible !important;
}}
.st-key-cvb-style-section-native > [data-testid="stVerticalBlock"] {{
  display: flex !important;
  flex-direction: column !important;
  gap: 14px !important;
  overflow: visible !important;
}}
.st-key-cvb-style-native {{
  padding-top: 4px !important;
}}
.st-key-cvb-style-native > [data-testid="stVerticalBlock"] {{
  display: flex !important;
  flex-direction: column !important;
  gap: 0 !important;
  overflow: visible !important;
}}
.st-key-cvb-style-native .cvb-style-label {{
  display: block !important;
  position: relative !important;
  z-index: 5 !important;
  margin: 12px 0 8px !important;
  padding: 0 !important;
  color: #475569 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 1.3 !important;
  clear: both !important;
}}
.st-key-cvb-style-native .cvb-label {{
  display: block !important;
  position: relative !important;
  z-index: 5 !important;
  margin-top: 12px !important;
  margin-bottom: 6px !important;
  padding: 0 !important;
  color: #475569 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  clear: both !important;
}}
.st-key-cvb-style-native .cvb-label strong {{
  color: #0b5cb8 !important;
  font-weight: 700 !important;
}}
.st-key-cvb-style-native .cvb-style-label-accent {{
  margin-top: 0 !important;
  margin-bottom: 12px !important;
}}
.st-key-cvb-style-native [data-testid="stMarkdownContainer"] p {{
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}}
.st-key-cvb-style-native .element-container {{
  margin-bottom: 0 !important;
}}
.st-key-cvb-style-native .st-key-cvb-style-font-native,
.st-key-cvb-style-native .st-key-cvb-style-spacing-native,
.st-key-cvb-style-native .st-key-cvb-style-line-native {{
  margin-bottom: 12px !important;
}}
.st-key-cvb-style-native .st-key-cvb-style-toggles-native {{
  margin-top: 6px !important;
}}

.st-key-cvb-color-dots-native [data-testid="stHorizontalBlock"] {{
  gap: 10px !important;
  row-gap: 10px !important;
  margin: 0 !important;
  align-items: center !important;
}}
.st-key-cvb-style-native .st-key-cvb-color-dots-native {{
  margin-top: 2px !important;
  margin-bottom: 12px !important;
}}
.st-key-cvb-color-dots-native .stButton button {{
  width: 32px !important;
  min-width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  border-radius: 50% !important;
  padding: 0 !important;
  color: transparent !important;
  font-size: 0 !important;
  border: 2px solid transparent !important;
}}
{native_dot_css}
.st-key-cvb-color-dots-native .stButton button:hover {{
  transform: scale(1.04);
}}
.st-key-cvb-left-scroll-native .stSlider > div > div {{
  padding-top: 2px !important;
  padding-bottom: 4px !important;
}}
.st-key-cvb-left-scroll-native .stSlider {{
  margin: 2px 0 10px 0 !important;
}}
.st-key-cvb-style-native .stSlider {{
  margin-top: 6px !important;
  margin-bottom: 18px !important;
}}
.st-key-cvb-style-native .stSlider [data-baseweb="slider"] > div:nth-child(1) {{
  height: 6px !important;
  border-radius: 999px !important;
}}
.st-key-cvb-style-native [data-testid="stSlider"] {{
  margin-top: 2px !important;
  margin-bottom: 0 !important;
}}
.st-key-cvb-style-native [data-testid*="ThumbValue"],
.st-key-cvb-style-native [data-testid="stThumbValue"],
.st-key-cvb-style-native [data-testid*="TickBar"],
.st-key-cvb-style-native [data-testid="stTickBar"],
.st-key-cvb-style-native .stSlider [role="tooltip"],
.st-key-cvb-style-native .stSlider output {{
  display: none !important;
}}
.st-key-cvb-left-scroll-native [data-testid*="ThumbValue"],
.st-key-cvb-left-scroll-native [data-testid="stThumbValue"],
.st-key-cvb-left-scroll-native [data-testid*="TickBar"],
.st-key-cvb-left-scroll-native [data-testid="stTickBar"],
.st-key-cvb-left-scroll-native [role="tooltip"],
.st-key-cvb-left-scroll-native .stSlider output {{
  display: none !important;
}}
.st-key-cvb-left-scroll-native .stSlider [role="slider"] {{
  width: 14px !important;
  height: 14px !important;
  background: #0b6fd6 !important;
  border: 2px solid #ffffff !important;
  box-shadow: 0 1px 4px rgba(14, 116, 214, 0.25) !important;
}}
.st-key-cvb-left-scroll-native .stSlider [data-baseweb="slider"] > div:nth-child(1) {{
  height: 4px !important;
}}
.st-key-cvb-left-scroll-native .stCheckbox [data-baseweb="checkbox"] > div:first-child,
.st-key-cvb-left-scroll-native .stToggle [data-baseweb="checkbox"] > div:first-child {{
  border-radius: 999px !important;
}}
.st-key-cvb-left-scroll-native .stCheckbox label,
.st-key-cvb-left-scroll-native .stToggle label {{
  color: #334155 !important;
  font-size: 14px !important;
}}
.st-key-cvb-left-scroll-native .stToggle {{
  margin-top: 6px !important;
  margin-bottom: 2px !important;
}}
.st-key-cvb-style-native .stToggle {{
  margin-top: 8px !important;
  margin-bottom: 8px !important;
}}
.st-key-cvb-style-native .stToggle [data-baseweb="checkbox"] > div:first-child {{
  min-width: 40px !important;
  height: 24px !important;
}}
.cvb-style-gap {{
  height: 8px;
}}
.st-key-cvb-preview-tools-native {{
  margin: -8px -10px 10px !important;
  padding: 0 !important;
}}
.st-key-cvb-preview-tools-native > div,
.st-key-cvb-preview-tools-native [data-testid="stVerticalBlock"],
.st-key-cvb-preview-tools-native [data-testid="stElementContainer"],
.st-key-cvb-preview-tools-native [data-testid="stCustomComponentV1"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-zoom-hidden-buttons {{
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}}
</style>""",
        unsafe_allow_html=True,
    )


def _render_sections_list_component(section_order: list[str], visibility: dict[str, bool], is_dark: bool) -> None:
    """Render a unified section list via components.html with SortableJS.

    Each row is [grip SVG | truncated label | eye SVG] — all inside one card,
    matching CVReviewer's layout exactly.  Order and visibility changes are
    communicated back to Streamlit via a hidden text-input bridge widget.
    """
    ITEM_H  = 46
    ITEM_GAP = 8
    n = len(section_order)
    comp_h = max(n * (ITEM_H + ITEM_GAP) + 8, 44)

    bg     = "#1e293b" if is_dark else "#ffffff"
    border = "#334155" if is_dark else "#d3dce8"
    text   = "#e2e8f0" if is_dark else "#0f172a"
    muted  = "#94a3b8" if is_dark else "#64748b"
    hov    = "#60a5fa" if is_dark else "#0a64ca"
    pg_bg  = "transparent"

    items_html = "".join(
        f'<li class="sec-item" data-id="{sid}">'
        f'<button class="grip-btn" tabindex="-1" aria-label="Drag to reorder"></button>'
        f'<span class="sec-label">{SECTION_ID_TO_LABEL.get(sid, sid.title())}</span>'
        f'<button class="eye-btn" data-visible="{str(visibility.get(sid, True)).lower()}"'
        f' aria-label="Toggle visibility"></button>'
        f'</li>'
        for sid in section_order
    )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{pg_bg};overflow:hidden;font-family:system-ui,-apple-system,sans-serif}}
#sl{{list-style:none;padding:4px 0 2px}}
.sec-item{{
  display:flex;align-items:center;gap:8px;
  padding:0 12px;
  background:{bg};border:1px solid {border};border-radius:8px;
  margin-bottom:{ITEM_GAP}px;height:{ITEM_H}px;
  cursor:default;user-select:none;overflow:hidden;
  transition:border-color .12s,box-shadow .12s;
}}
.sec-item:hover{{border-color:{hov};box-shadow:0 2px 6px rgba(2,132,199,.10)}}
.sec-item.s-ghost{{opacity:.3;background:{bg}}}
.sec-item.s-chosen{{border-color:{hov};box-shadow:0 4px 12px rgba(2,132,199,.15)}}
.grip-btn{{
  cursor:grab;color:{muted};border:none;background:none;
  padding:2px;display:flex;align-items:center;flex-shrink:0;
  border-radius:4px;transition:color .12s;
}}
.grip-btn:hover{{color:{text}}}
.grip-btn:active{{cursor:grabbing}}
.sec-label{{
  flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  font-size:14px;font-weight:600;color:{text};line-height:1.2;
}}
.eye-btn{{
  border:none;background:none;padding:2px;cursor:pointer;
  color:{muted};display:flex;align-items:center;flex-shrink:0;
  border-radius:4px;transition:color .12s;
}}
.eye-btn:hover{{color:{hov}}}
.eye-btn.sec-off{{color:#cbd5e1}}
</style>
</head>
<body>
<ul id="sl">{items_html}</ul>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
<script>
var GRIP='<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><circle cx="9" cy="5" r="1.5"/><circle cx="9" cy="12" r="1.5"/><circle cx="9" cy="19" r="1.5"/><circle cx="15" cy="5" r="1.5"/><circle cx="15" cy="12" r="1.5"/><circle cx="15" cy="19" r="1.5"/></svg>';
var EYON='<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
var EYOFF='<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>';

document.querySelectorAll('.grip-btn').forEach(function(b){{b.innerHTML=GRIP;}});
document.querySelectorAll('.eye-btn').forEach(function(b){{
  var v=b.dataset.visible==='true';
  b.innerHTML=v?EYON:EYOFF;
  if(!v) b.classList.add('sec-off');
}});

function sendEyeToggle(secId){{
  try{{window.parent.postMessage({{type:'cvb-eye-toggle',sectionId:secId}},'*');}}catch(e){{}}
}}
function sendDragEnd(movedId,newPos){{
  try{{window.parent.postMessage({{type:'cvb-drag-end',movedId:movedId,newPos:newPos}},'*');}}catch(e){{}}
}}

if(typeof Sortable!=='undefined'){{
  Sortable.create(document.getElementById('sl'),{{
    animation:150,handle:'.grip-btn',
    ghostClass:'s-ghost',chosenClass:'s-chosen',
    onEnd:function(evt){{
      sendDragEnd(evt.item.dataset.id, evt.newIndex);
    }}
  }});
}}

document.querySelectorAll('.eye-btn').forEach(function(btn){{
  btn.addEventListener('click',function(e){{
    e.stopPropagation();
    var v=this.dataset.visible==='true';
    this.dataset.visible=String(!v);
    this.innerHTML=!v?EYON:EYOFF;
    this.classList.toggle('sec-off',v);
    sendEyeToggle(this.closest('.sec-item').dataset.id);
  }});
}});
</script>
</body></html>"""

    components.html(html, height=comp_h, scrolling=False)


def _render_template_component(current_tpl: str, is_dark: bool) -> None:
    """Render template-selection cards as a custom HTML component (like the sections list).

    Clicking a card sends postMessage → relay clicks hidden cvb_tpl_{key} button → Python reruns.
    Design matches CVReviewer: compact cards with blue ring on selected, muted subtitle text.
    """
    bg        = "#1e293b" if is_dark else "#ffffff"
    bg_hover  = "#334155" if is_dark else "#f8fbff"
    bg_active = "#1e3a5f" if is_dark else "rgba(59,130,246,0.12)"
    border    = "#334155" if is_dark else "#d3dce8"
    border_act= "rgba(96,165,250,0.6)" if is_dark else "rgba(59,130,246,0.55)"
    text_main = "#f1f5f9"  if is_dark else "#0f172a"
    text_act  = "#bfdbfe"  if is_dark else "#2563eb"
    text_sub  = "#94a3b8"  if is_dark else "#64748b"
    text_sub_act="#93c5fd" if is_dark else "#2563eb"

    cards_html = ""
    for tpl_key, tpl_label, tpl_desc in TEMPLATE_CHOICES:
        active = current_tpl == tpl_key
        act_cls = " tpl-active" if active else ""
        cards_html += (
            f"<div class='tpl-card{act_cls}' data-tpl='{tpl_key}'>"
            f"<div class='tpl-name'>{tpl_label}</div>"
            f"<div class='tpl-desc'>{tpl_desc}</div>"
            f"</div>"
        )

    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;padding:2px 0 0;margin:0;font-family:system-ui,sans-serif;}}
.tpl-card{{
  display:block;width:100%;text-align:left;cursor:pointer;
  background:{bg};border:1px solid {border};border-radius:8px;
  padding:12px 14px;margin-bottom:8px;transition:all 0.15s;
  position:relative;
}}
.tpl-card:last-child{{margin-bottom:0;}}
.tpl-card:hover{{background:{bg_hover};border-color:rgba(37,99,235,0.25);}}
.tpl-card.tpl-active{{
  background:{bg_active};
  border-color:{border_act};
  box-shadow:inset 0 0 0 1px {border_act};
}}
.tpl-name{{
  font-size:13px;font-weight:600;color:{text_main};
  line-height:1.2;margin-bottom:4px;letter-spacing:-0.01em;
}}
.tpl-active .tpl-name{{color:{text_act};}}
.tpl-desc{{font-size:11px;color:{text_sub};line-height:1.35;}}
.tpl-active .tpl-desc{{color:{text_sub_act};}}
</style>
<div id='tpl-wrap'>{cards_html}</div>
<script>
document.querySelectorAll('.tpl-card').forEach(function(card){{
  card.addEventListener('click',function(){{
    try{{window.parent.postMessage({{type:'cvb-tpl-select',tpl:this.dataset.tpl}},'*');}}catch(e){{}}
  }});
}});
</script>
"""
    # 3 cards: ~54px each + 7px gap × 2 + 2px top padding = 182px; use 188 for safety
    components.html(html, height=188, scrolling=False)


# --- Modern template fidelity overrides (preview-first placeholders) ---
def _build_preview_data_with_demo_defaults(user_data: dict) -> dict:
    """Merge demo placeholders with user data for live preview.

    Personal fields merge field-by-field.
    Repeating sections use user rows when meaningful, with per-field fallback to demo rows.
    """
    demo = _get_demo_cv_data()
    user = user_data if isinstance(user_data, dict) else {}

    def _merge_personal() -> dict:
        up = user.get("personal", {}) if isinstance(user.get("personal", {}), dict) else {}
        dp = demo.get("personal", {}) if isinstance(demo.get("personal", {}), dict) else {}
        out = {}
        for k in set(dp.keys()) | set(up.keys()):
            uv = up.get(k, "")
            out[k] = uv if _has_meaningful_text(uv) else dp.get(k, "")
        return out

    def _meaningful_rows(rows: list) -> list[dict]:
        return [r for r in rows if _row_has_meaningful_data(r)]

    def _merge_rows(section_key: str) -> list[dict]:
        urows = user.get(section_key, []) if isinstance(user.get(section_key, []), list) else []
        drows = demo.get(section_key, []) if isinstance(demo.get(section_key, []), list) else []
        urows = _meaningful_rows(urows)
        if not urows:
            return drows
        merged: list[dict] = []
        for i, urow in enumerate(urows):
            drow = drows[i] if i < len(drows) and isinstance(drows[i], dict) else {}
            keys = set(drow.keys()) | set(urow.keys())
            row_out: dict = {}
            for k in keys:
                uv = urow.get(k)
                dv = drow.get(k)
                if isinstance(uv, bool):
                    row_out[k] = uv
                elif isinstance(uv, list):
                    row_out[k] = uv if any(_has_meaningful_text(x) for x in uv) else (dv if isinstance(dv, list) else [])
                elif isinstance(uv, dict):
                    row_out[k] = uv if _row_has_meaningful_data(uv) else (dv if isinstance(dv, dict) else {})
                else:
                    row_out[k] = uv if _has_meaningful_text(uv) else (dv if dv is not None else "")
            merged.append(row_out)
        return merged

    out = {
        "personal": _merge_personal(),
        "experience": _merge_rows("experience"),
        "education": _merge_rows("education"),
        "projects": _merge_rows("projects"),
        "certifications": _merge_rows("certifications"),
        "languages": _merge_rows("languages"),
        "interests": [],
        "skills": {"items": [], "categories": []},
        "customization": user.get("customization", {}),
    }

    # Skills: preserve one-by-one entry behavior with demo fallback.
    uskills = user.get("skills", {}) if isinstance(user.get("skills", {}), dict) else {}
    uitems = uskills.get("items", []) if isinstance(uskills.get("items", []), list) else []
    cleaned = []
    for it in uitems:
        if isinstance(it, dict) and _has_meaningful_text(it.get("name", "")):
            cleaned.append({"name": str(it.get("name", "")).strip()})
    if cleaned:
        out["skills"]["items"] = cleaned
        out["skills"]["categories"] = [{"id": "primary", "name": "Skills", "items": [x["name"] for x in cleaned]}]
    else:
        out["skills"] = demo.get("skills", {"items": [], "categories": []})

    uinterests = user.get("interests", []) if isinstance(user.get("interests", []), list) else []
    ints = [str(x).strip() for x in uinterests if _has_meaningful_text(x)]
    out["interests"] = ints if ints else demo.get("interests", [])
    return out


def generate_cv_html(
    data: dict,
    template: str = "classic",
    accent_color: str | None = None,
    font_family: str | None = None,
    font_size: int = 11,
    line_height: float = 1.4,
    entry_spacing: int = 8,
    preview_dark: bool = False,
    section_visibility: dict | None = None,
    section_order: list | None = None,
) -> str:
    """Final preview renderer with CVReviewer-style Modern structure."""
    tpl = _normalize_template(template)
    cfg = dict(TEMPLATE_CONFIGS.get(tpl, TEMPLATE_CONFIGS["classic"]))
    if accent_color:
        cfg["primary"] = accent_color
        cfg["rule"] = accent_color
        cfg["link"] = accent_color
    if font_family:
        cfg["font"] = font_family

    vis = _normalize_section_visibility(section_visibility)
    order = _normalize_section_order(section_order)
    fs = max(9, int(font_size))
    fs_sm = max(8, fs - 1)
    fs_xs = max(7, fs - 2)
    lh = max(1.15, float(line_height))
    es = max(4, int(entry_spacing))

    p = data.get("personal", {}) or {}
    name = _html_escape((p.get("full_name") or "Your Name").strip() or "Your Name")
    title = _html_escape((p.get("prof_title") or "Professional Title").strip() or "Professional Title")
    summary = _html_escape((p.get("summary") or "").strip())

    def _skill_values() -> list[str]:
        out: list[str] = []
        for item in data.get("skills", {}).get("items", []):
            nm = str(item.get("name", "")).strip()
            if nm:
                out.append(nm)
        if not out:
            for cat in data.get("skills", {}).get("categories", []):
                out.extend([str(x).strip() for x in cat.get("items", []) if str(x).strip()])
        return out

    skills = _skill_values()

    def _sec_label(sid: str) -> str:
        return SECTION_ID_TO_LABEL.get(sid, sid.replace("_", " ").title()).upper()

    def _date_text(start: str, end: str, current: bool = False) -> str:
        return _html_escape(_date_range(start, end, current))

    def _summary_block() -> str:
        if not summary:
            return ""
        return f"<p class='p'>{summary}</p>"

    def _experience_block() -> str:
        parts = []
        for exp in data.get("experience", []) or []:
            role = _html_escape(exp.get("role", ""))
            company = _html_escape(exp.get("company", ""))
            loc = _html_escape(exp.get("location", ""))
            dr = _date_text(exp.get("start_date", ""), exp.get("end_date", ""), bool(exp.get("current", False)))
            bullets = [str(x).strip() for x in exp.get("bullets", []) if str(x).strip()]
            bhtml = "".join(f"<li>{_html_escape(b)}</li>" for b in bullets)
            parts.append(
                "<div class='entry'>"
                "<div class='top'><span class='role'>%s</span><span class='date'>%s</span></div>"
                "<div class='sub'>%s%s</div>"
                "%s"
                "</div>"
                % (role, dr, company, (", " + loc) if loc else "", f"<ul class='ul'>{bhtml}</ul>" if bhtml else "")
            )
        return "".join(parts)

    def _education_block() -> str:
        parts = []
        for edu in data.get("education", []) or []:
            inst = _html_escape(edu.get("institution", ""))
            degree = _html_escape(edu.get("degree", ""))
            field = _html_escape(edu.get("field", ""))
            loc = _html_escape(edu.get("location", ""))
            gpa = _html_escape(edu.get("gpa", ""))
            dr = _date_text(edu.get("start_date", ""), edu.get("end_date", ""))
            desc = " | ".join([x for x in [degree, field] if x])
            if gpa:
                desc = f"{desc}{' | ' if desc else ''}GPA: {gpa}"
            parts.append(
                "<div class='entry'>"
                "<div class='top'><span class='role'>%s</span><span class='date'>%s</span></div>"
                "<div class='sub'>%s%s</div>"
                "</div>"
                % (inst, dr, desc, (", " + loc) if loc else "")
            )
        return "".join(parts)

    def _projects_block() -> str:
        parts = []
        for proj in data.get("projects", []) or []:
            namev = _html_escape(proj.get("name", ""))
            rolev = _html_escape(proj.get("role", ""))
            desc = _html_escape(proj.get("description", ""))
            dr = _date_text(proj.get("start_date", ""), proj.get("end_date", ""))
            tech = [str(x).strip() for x in proj.get("tech_stack", []) if str(x).strip()]
            chips = "".join(f"<span class='chip'>{_html_escape(t)}</span>" for t in tech)
            parts.append(
                "<div class='entry'>"
                "<div class='top'><span class='role'>%s</span><span class='date'>%s</span></div>"
                "%s%s%s"
                "</div>"
                % (
                    namev,
                    dr,
                    f"<div class='sub'>{rolev}</div>" if rolev else "",
                    f"<p class='p'>{desc}</p>" if desc else "",
                    f"<div class='chips'>{chips}</div>" if chips else "",
                )
            )
        return "".join(parts)

    def _langs_block() -> str:
        rows = []
        for lang in data.get("languages", []) or []:
            lv = _html_escape(lang.get("language", ""))
            pv = _html_escape(lang.get("proficiency", ""))
            if lv:
                rows.append(f"<div class='kv'><span>{lv}</span><span>{pv}</span></div>")
        return "".join(rows)

    def _certs_block() -> str:
        rows = []
        for cert in data.get("certifications", []) or []:
            nm = _html_escape(cert.get("name", ""))
            iss = _html_escape(cert.get("issuer", ""))
            dt = _html_escape(cert.get("date", ""))
            if nm:
                tail = " - ".join([x for x in [iss, dt] if x])
                rows.append(f"<p class='p'><strong>{nm}</strong>{(' - ' + tail) if tail else ''}</p>")
        return "".join(rows)

    def _interests_block() -> str:
        vals = [str(x).strip() for x in data.get("interests", []) if str(x).strip()]
        return "".join(f"<span class='chip'>{_html_escape(v)}</span>" for v in vals)

    # shared map for classic/creative and right side modern
    sec_map = {
        "summary": _summary_block(),
        "experience": _experience_block(),
        "education": _education_block(),
        "projects": _projects_block(),
        "languages": _langs_block(),
        "certifications": _certs_block(),
        "interests": f"<div class='chips'>{_interests_block()}</div>" if _interests_block() else "",
        "skills": "".join(f"<p class='p'>{_html_escape(s)}</p>" for s in skills),
    }

    def _sec(title: str, inner: str, compact: bool = False) -> str:
        if not inner.strip():
            return ""
        cls = "sec compact" if compact else "sec"
        return f"<section class='{cls}'><h2>{_html_escape(title)}</h2>{inner}</section>"

    # modern layout
    icon_map = {"email": "✉", "phone": "☎", "location": "⌖", "website": "◉", "linkedin": "in", "github": "⌂"}
    contact_rows = []
    for key in ["email", "phone", "location", "website", "linkedin", "github"]:
        val = str(p.get(key, "")).strip()
        if val:
            contact_rows.append(
                f"<div class='contact-row'><span class='ico'>{icon_map.get(key,'•')}</span><span>{_html_escape(val)}</span></div>"
            )
    contact_html = "".join(contact_rows)

    # skills with dot-rating look (deterministic)
    modern_skill_rows = []
    for i, sk in enumerate(skills):
        fill = 3 + ((len(sk) + i) % 3)
        dots = "".join("<i class='dot on'></i>" if d < fill else "<i class='dot'></i>" for d in range(5))
        modern_skill_rows.append(
            f"<div class='skill-row'><span>{_html_escape(sk)}</span><span class='dots'>{dots}</span></div>"
        )
    modern_skills = "".join(modern_skill_rows)

    left_pref = {"skills", "languages", "certifications", "interests"}
    left_ids = [sid for sid in order if sid in left_pref and vis.get(sid, True)]
    right_ids = [sid for sid in order if sid not in left_pref and sid != "personal" and vis.get(sid, True)]

    left_blocks: list[str] = []
    for sid in left_ids:
        if sid == "skills":
            left_blocks.append(_sec("Skills", modern_skills, compact=True))
        elif sid == "interests":
            chips = _interests_block()
            if chips:
                left_blocks.append(_sec("Interests", f"<div class='chips'>{chips}</div>", compact=True))
        else:
            inner = sec_map.get(sid, "")
            if inner:
                left_blocks.append(_sec(_sec_label(sid), inner, compact=True))

    right_blocks: list[str] = []
    for sid in right_ids:
        if sid == "summary":
            ttl = "Professional Summary"
        else:
            ttl = _sec_label(sid).title()
        inner = sec_map.get(sid, "")
        if inner:
            right_blocks.append(_sec(ttl, inner, compact=False))

    modern_body = (
        "<div class='paper modern'>"
        "<div class='m-grid'>"
        "<aside class='m-left'>"
        f"<h1 id='cv-name'>{name}</h1>"
        f"<p class='title'>{title}</p>"
        + (_sec("Contact", contact_html, compact=True) if contact_html else "")
        + "".join(left_blocks)
        + "</aside>"
        "<main class='m-right'>"
        + "".join(right_blocks)
        + "</main>"
        + "</div></div>"
    )

    # keep current non-modern rendering simple/stable
    contact_line = " · ".join(_html_escape(str(p.get(k, "")).strip()) for k in ["email", "phone", "location", "website", "linkedin", "github"] if str(p.get(k, "")).strip())
    classic_sections = "".join(
        _sec(_sec_label(sid).title(), sec_map.get(sid, ""), compact=False)
        for sid in order if sid != "personal" and vis.get(sid, True)
    )
    classic_body = (
        "<div class='paper classic'>"
        f"<h1 id='cv-name'>{name}</h1>"
        f"<p class='title'>{title}</p>"
        + (f"<p class='contact-line'>{contact_line}</p>" if contact_line else "")
        + classic_sections
        + "</div>"
    )

    creative_left = []
    for sid in ["skills", "languages", "interests"]:
        if vis.get(sid, True):
            inner = sec_map.get(sid, "")
            if inner:
                creative_left.append(_sec(_sec_label(sid).title(), inner, compact=True))
    creative_right = "".join(
        _sec(("About Me" if sid == "summary" else _sec_label(sid).title()), sec_map.get(sid, ""), compact=False)
        for sid in order if sid not in {"skills", "languages", "interests", "personal"} and vis.get(sid, True)
    )
    creative_body = (
        "<div class='paper creative'><div class='c-grid'>"
        "<aside class='c-left'>"
        f"<h1 id='cv-name'>{name}</h1><p class='title'>{title}</p>"
        + (_sec("Contact", contact_html, compact=True) if contact_html else "")
        + "".join(creative_left)
        + "</aside><main class='c-right'>"
        + creative_right
        + "</main></div></div>"
    )

    body_html = {"modern": modern_body, "creative": creative_body}.get(tpl, classic_body)
    primary = cfg["primary"]
    primary_soft = f"{primary}26"
    text = "#e2e8f0" if preview_dark else "#0f172a"
    muted = "#94a3b8" if preview_dark else "#64748b"
    paper_bg = "#111827" if preview_dark else "#ffffff"
    page_bg = "#0b1220" if preview_dark else "#f8fafc"
    border = "#334155" if preview_dark else "#dbe4f0"

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; }}
body {{ background:{page_bg}; font-family:{cfg["font"]}; color:{text}; }}
.paper {{ width:100%; background:{paper_bg}; border:1px solid {border}; }}
h1 {{ margin:0; font-size:{max(20, fs + 7)}px; line-height:1.12; font-weight:800; }}
.title {{ margin:3px 0 0; color:{muted}; font-size:{fs}px; }}
.sec {{ margin-top:{max(6, es)}px; }}
.sec h2 {{
  margin:0 0 5px; font-size:{fs_xs}px; letter-spacing:.9px;
  text-transform:uppercase; font-weight:800; color:{primary};
  border-bottom:1.5px solid {primary}; padding-bottom:3px;
}}
.sec.compact h2 {{ font-size:{max(7, fs_xs - 1)}px; border-bottom:1px solid currentColor; }}
.p {{ margin:0 0 3px; font-size:{fs_xs}px; line-height:{lh}; }}
.entry {{ margin:0 0 {max(5, es - 1)}px; }}
.top {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-end; }}
.role {{ font-size:{fs}px; font-weight:700; }}
.date {{ font-size:{fs_xs}px; color:{muted}; white-space:nowrap; }}
.sub {{ font-size:{fs_xs}px; color:{muted}; margin-top:1px; font-style:italic; line-height:{lh}; }}
.ul {{ margin:4px 0 0 14px; padding:0; }}
.ul li {{ margin:1px 0; font-size:{fs_xs}px; line-height:{lh}; }}
.kv {{ display:flex; justify-content:space-between; gap:8px; font-size:{fs_xs}px; line-height:{lh}; margin-bottom:3px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:4px; }}
.chip {{ font-size:{max(7, fs_xs - 1)}px; line-height:1.1; padding:2px 6px; border-radius:999px; background:{primary_soft}; color:{primary}; border:1px solid {primary_soft}; }}
.contact-line {{ margin:4px 0 0; font-size:{fs_xs}px; color:{muted}; text-align:center; }}

/* modern exact-ish */
.modern .m-grid {{ display:grid; grid-template-columns:31% 69%; min-height:1122px; }}
.m-left {{
  background:{primary}; color:#f8fbff; padding:16px 14px;
}}
.m-left h1 {{ color:#fff; font-size:{max(20, fs + 8)}px; }}
.m-left .title {{ color:#dbeafe; font-size:{fs_sm}px; }}
.m-left .sec h2 {{ color:#fff; border-bottom-color:rgba(255,255,255,.32); }}
.contact-row {{ display:flex; gap:6px; align-items:flex-start; margin:0 0 4px; font-size:{fs_xs}px; line-height:{lh}; }}
.contact-row .ico {{
  display:inline-flex; align-items:center; justify-content:center;
  width:12px; min-width:12px; margin-top:1px; color:#e2e8f0; font-size:{max(8, fs_xs - 1)}px;
}}
.skill-row {{ display:flex; justify-content:space-between; align-items:center; gap:6px; margin:0 0 4px; font-size:{fs_xs}px; }}
.dots {{ display:inline-flex; gap:3px; }}
.dot {{ width:7px; height:7px; border-radius:50%; background:rgba(255,255,255,.30); }}
.dot.on {{ background:#fff; }}
.m-left .chip {{ background:rgba(255,255,255,.15); border-color:rgba(255,255,255,.18); color:#fff; }}

.m-right {{ padding:14px 16px; background:#fff; color:#1e293b; }}
.m-right .sec h2 {{ color:{primary}; border-bottom-color:{primary}; }}
.m-right .p, .m-right .sub, .m-right .date, .m-right .kv {{ color:#64748b; }}
.m-right .role {{ color:#0f172a; }}

/* classic */
.classic {{ min-height:1122px; padding:16px; }}
.classic h1 {{ color:{primary}; text-align:center; }}
.classic .title {{ text-align:center; }}

/* creative */
.creative .c-grid {{ display:grid; grid-template-columns:30% 70%; min-height:1122px; }}
.c-left {{ background:{primary_soft}; border-right:2px solid {primary}; padding:14px 12px; }}
.c-left h1 {{ color:{primary}; font-size:{max(19, fs + 7)}px; }}
.c-right {{ padding:14px 16px; background:#fff; color:#1e293b; }}
.c-right .entry {{ border-left:2px solid {primary_soft}; padding-left:10px; }}
</style>
</head><body>
{body_html}
</body></html>"""


_SCALE_VALUES = [80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]


def _render_style_component(
    current_accent: str, font_size: int, line_height: float, entry_spacing: int,
    show_icons: bool, show_photo: bool, is_dark: bool
) -> None:
    """STYLE section as a custom HTML component matching CVReviewer exactly.

    Accent swatches (24px circles, 4-per-row grid, ring-2 on selected),
    Font Scale / Line Height / Entry Spacing sliders (6px track),
    Show icons / Show photo toggle switches (36x20px, sliding thumb).
    All interactions via postMessage -> relay -> hidden buttons.
    """
    lbl_color = "#94a3b8" if is_dark else "#64748b"
    txt_color = "#f1f5f9" if is_dark else "#0f172a"
    track_bg  = "#334155" if is_dark else "#e2e8f0"
    tog_off   = "#475569" if is_dark else "#e2e8f0"
    ring_bg   = "#1e293b" if is_dark else "#ffffff"

    # Font scale: clamp to 0.80-1.30 snapped to nearest 0.05
    raw_scale = font_size / 11.0
    scale = max(0.80, min(1.30, round(raw_scale / 0.05) * 0.05))

    # Line height: clamp to 1.0-2.0 snapped to nearest 0.1
    lh = max(1.0, min(2.0, round(line_height / 0.1) * 0.1))

    # Entry spacing: clamp to 0-24 snapped to nearest 2
    es = max(0, min(24, round(entry_spacing / 2) * 2))
    spacing_scale = es / 8.0

    # Build swatches — 4 per row using CSS grid so they never overflow
    swatches_html = ""
    for i, color in enumerate(ACCENT_COLORS):
        active = color.lower() == (current_accent or "").lower()
        sel_cls = " sel" if active else ""
        swatches_html += (
            f"<button class='sw{sel_cls}' data-idx='{i}' "
            f"style='background:{color}' title='{color}'></button>"
        )

    icons_on = "on" if show_icons else ""
    photo_on = "on" if show_photo else ""

    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:transparent;font-family:Poppins,Montserrat,system-ui,-apple-system,sans-serif;overflow:hidden;padding:2px 0 4px;}}
.lbl{{font-size:12px;font-weight:500;color:{lbl_color};display:block;margin-bottom:8px;line-height:1.2;}}
.swatches{{display:flex;flex-wrap:wrap;gap:8px;width:208px;max-width:100%;}}
.sw{{
  width:28px;height:28px;border-radius:999px;border:none;cursor:pointer;
  box-shadow:0 0 0 1px #cbd5e1;outline:none;
  transition:transform 0.12s,box-shadow 0.12s;
}}
.sw:hover{{transform:scale(1.10);}}
.sw.sel{{transform:scale(1.10);box-shadow:0 0 0 1px #cbd5e1,0 0 0 3px {ring_bg},0 0 0 5px #2563eb;}}
.section{{margin-top:14px;}}
.row-lbl{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;}}
.row-lbl span{{font-size:13px;font-weight:500;color:{lbl_color};}}
.row-lbl strong{{font-size:13px;font-weight:700;color:#0b5cb8;}}
input[type=range]{{
  -webkit-appearance:none;width:100%;height:6px;border-radius:9999px;
  background:{track_bg};cursor:pointer;outline:none;border:none;
}}
input[type=range]::-webkit-slider-thumb{{
  -webkit-appearance:none;width:14px;height:14px;border-radius:50%;
  background:#2563eb;cursor:pointer;
  box-shadow:0 1px 3px rgba(0,0,0,0.25);transition:transform 0.12s;
}}
input[type=range]::-webkit-slider-thumb:hover{{transform:scale(1.15);}}
.tog-row{{display:flex;align-items:center;gap:10px;cursor:pointer;margin-top:12px;}}
.tog-track{{
  position:relative;width:36px;height:20px;border-radius:9999px;
  flex-shrink:0;transition:background 0.15s;background:{tog_off};
}}
.tog-track.on{{background:#2563eb;}}
.tog-thumb{{
  position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;
  background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.2);
  transition:transform 0.15s;
}}
.tog-track.on .tog-thumb{{transform:translateX(16px);}}
.tog-text{{font-size:13px;color:{lbl_color};user-select:none;transition:color 0.12s;}}
.tog-row:hover .tog-text{{color:{txt_color};}}
</style></head><body>
<span class='lbl'>Accent Color</span>
<div class='swatches' id='sw-wrap'>{swatches_html}</div>

<div class='section'>
  <div class='row-lbl'>
    <span>Font Scale</span>
    <strong id='sv'>{scale:.1f}x</strong>
  </div>
  <input type='range' id='sl' min='0.80' max='1.30' step='0.05' value='{scale:.2f}'>
</div>

<div class='section'>
  <div class='row-lbl'>
    <span>Line Height</span>
    <strong id='lhv'>{lh:.1f}x</strong>
  </div>
  <input type='range' id='lh' min='1.0' max='2.0' step='0.1' value='{lh:.1f}'>
</div>

<div class='section'>
  <div class='row-lbl'>
    <span>Spacing</span>
    <strong id='esv'>{spacing_scale:.1f}x</strong>
  </div>
  <input type='range' id='es' min='0' max='24' step='2' value='{es}'>
</div>

<label class='tog-row' id='icons-lbl'>
  <div class='tog-track {icons_on}' id='icons-trk'><div class='tog-thumb'></div></div>
  <span class='tog-text'>Show icons</span>
</label>
<label class='tog-row' id='photo-lbl'>
  <div class='tog-track {photo_on}' id='photo-trk'><div class='tog-thumb'></div></div>
  <span class='tog-text'>Show photo</span>
</label>

<script>
document.querySelectorAll('.sw').forEach(function(b){{
  b.addEventListener('click',function(){{
    try{{window.parent.postMessage({{type:'cvb-acc-select',idx:this.dataset.idx}},'*');}}catch(e){{}}
  }});
}});
var sl=document.getElementById('sl'),sv=document.getElementById('sv');
sl.addEventListener('input',function(){{sv.textContent=parseFloat(this.value).toFixed(1)+'x';}});
sl.addEventListener('change',function(){{
  var v=Math.round(parseFloat(this.value)*100);
  try{{window.parent.postMessage({{type:'cvb-scale-select',val:v}},'*');}}catch(e){{}}
}});
var lhEl=document.getElementById('lh'),lhvEl=document.getElementById('lhv');
lhEl.addEventListener('input',function(){{lhvEl.textContent=parseFloat(this.value).toFixed(1)+'x';}});
lhEl.addEventListener('change',function(){{
  var v=Math.round(parseFloat(this.value)*10);
  try{{window.parent.postMessage({{type:'cvb-lh-select',val:v}},'*');}}catch(e){{}}
}});
var esEl=document.getElementById('es'),esvEl=document.getElementById('esv');
esEl.addEventListener('input',function(){{esvEl.textContent=(parseFloat(this.value)/8).toFixed(1)+'x';}});
esEl.addEventListener('change',function(){{
  var v=Math.round(parseFloat(this.value));
  try{{window.parent.postMessage({{type:'cvb-es-select',val:v}},'*');}}catch(e){{}}
}});
function tog(trackId,msgType){{
  var t=document.getElementById(trackId);
  var on=t.classList.toggle('on');
  try{{window.parent.postMessage({{type:msgType,on:on}},'*');}}catch(e){{}}
}}
document.getElementById('icons-lbl').addEventListener('click',function(e){{e.preventDefault();tog('icons-trk','cvb-icons-toggle');}});
document.getElementById('photo-lbl').addEventListener('click',function(e){{e.preventDefault();tog('photo-trk','cvb-photo-toggle');}});
</script>
</body></html>"""
    # Swatches (2 rows of 4 × 24px + gap): ~66px
    # Accent label: ~20px
    # 3 sliders (label+slider+section margin): 3 × 46px = 138px
    # 2 toggles (36px each + margin): ~80px
    # padding: ~10px
    # Total: ~314px → use 330 for safety
    components.html(html, height=380, scrolling=False)


def _render_zoom_toolbar_component(zoom: int) -> None:
    html = f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:transparent;overflow:hidden;font-family:Poppins,Montserrat,system-ui,sans-serif}}
.bar{{
  height:44.8px;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  padding:8px 16px;
  background:#ffffff;
  border-bottom:1px solid #dbe3ef;
}}
.icon-btn{{
  width:28px;height:28px;border:0;border-radius:8px;background:transparent;
  color:#65758B;display:inline-flex;align-items:center;justify-content:center;
  padding:6px;cursor:pointer;transition:background .15s,color .15s;
}}
.icon-btn:hover{{background:#f3f5f7;color:#0059B3}}
.icon-btn svg{{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.zoom-pill{{
  width:56px;min-width:56px;height:19px;border-radius:999px;
  background:rgba(0,89,179,.10);border:1px solid rgba(0,89,179,.20);
  color:#0059B3;font-size:10px;font-weight:500;line-height:1;
  display:inline-flex;align-items:center;justify-content:center;
}}
</style></head>
<body>
<div class='bar'>
  <button class='icon-btn' data-act='out' aria-label='Zoom out'>
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle cx='11' cy='11' r='7'/><path d='M8 11h6'/><path d='m21 21-4.3-4.3'/></svg>
  </button>
  <span class='zoom-pill'>{zoom}%</span>
  <button class='icon-btn' data-act='in' aria-label='Zoom in'>
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle cx='11' cy='11' r='7'/><path d='M11 8v6'/><path d='M8 11h6'/><path d='m21 21-4.3-4.3'/></svg>
  </button>
  <button class='icon-btn' data-act='reset' aria-label='Reset zoom'>
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M15 3h6v6'/><path d='m21 3-7 7'/><path d='m3 21 7-7'/><path d='M9 21H3v-6'/></svg>
  </button>
</div>
<script>
document.querySelectorAll('.icon-btn').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    try {{
      window.parent.postMessage({{type:'cvb-zoom-toolbar', action:this.dataset.act}}, '*');
    }} catch(e) {{}}
  }});
}});
</script>
</body></html>"""
    components.html(html, height=45, scrolling=False)


_RAIL_HEADING_ICONS = {
    "sections": "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M8 6h13'/><path d='M8 12h13'/><path d='M8 18h13'/><path d='M3 6h.01'/><path d='M3 12h.01'/><path d='M3 18h.01'/></svg>",
    "templates": "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect width='18' height='18' x='3' y='3' rx='2'/><path d='M3 9h18'/><path d='M9 21V9'/></svg>",
    "style": "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='13.5' cy='6.5' r='.5'/><circle cx='17.5' cy='10.5' r='.5'/><circle cx='8.5' cy='7.5' r='.5'/><circle cx='6.5' cy='12.5' r='.5'/><path d='M12 22a1 1 0 0 0 1-1v-1a2 2 0 0 1 2-2h1a4 4 0 0 0 0-8 7 7 0 1 0-4 12Z'/></svg>",
}


def _render_left_rail_heading(label: str, icon_key: str) -> None:
    icon_svg = _RAIL_HEADING_ICONS.get(icon_key, "")
    icon_html = f"<span class='cvb-rail-heading-icon'>{icon_svg}</span>" if icon_svg else ""
    st.markdown(
        f"<h4 class='cvb-rail-heading'>{icon_html}<span>{_html_escape(label)}</span></h4>",
        unsafe_allow_html=True,
    )


def _render_left_panel_native() -> None:
    ss = st.session_state

    section_order = _normalize_section_order(ss.get("cvb_section_order"))
    visibility    = _normalize_section_visibility(ss.get("cvb_section_visibility"))
    ss["cvb_section_order"]      = section_order
    ss["cvb_section_visibility"] = visibility

    is_dark = ss.get("theme", "light") == "dark"

    # All relay-driven hidden buttons grouped in one 0-height absolutely-positioned
    # container so they take NO space in the normal flow.
    # JS .click() fires through position:absolute + overflow:hidden; pointer-events:none
    # only blocks user mouse — programmatic .click() always works.
    with st.container(key="cvb-hidden-buttons"):
        for sid in SECTION_IDS:
            for pos in range(len(SECTION_IDS)):
                if st.button("_", key=f"cvb_pos_{sid}_{pos}"):
                    order = list(ss.get("cvb_section_order", list(SECTION_IDS)))
                    if sid in order:
                        order.remove(sid)
                    order.insert(pos, sid)
                    ss["cvb_section_order"] = _normalize_section_order(order)
                    st.rerun()
        for sid in SECTION_IDS:
            if st.button("_", key=f"cvb_eye_{sid}"):
                current_vis = _normalize_section_visibility(ss.get("cvb_section_visibility"))
                current_vis[sid] = not current_vis.get(sid, True)
                ss["cvb_section_visibility"] = current_vis
                st.rerun()
        for tpl_key, _, _ in TEMPLATE_CHOICES:
            if st.button("_", key=f"cvb_tpl_{tpl_key}"):
                ss["cvb_template"] = tpl_key
                ss["cvb_zoom"] = _default_zoom_for_template(tpl_key)
                st.rerun()
        # Hidden accent color buttons
        for i, color in enumerate(ACCENT_COLORS):
            if st.button("_", key=f"cvb_acc_{i}"):
                ss["cvb_accent_color"] = color
                st.rerun()
        # Hidden font scale buttons (scale × 100 as int: 80,85,...,130)
        SCALE_VALUES = [80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130]
        for sv in SCALE_VALUES:
            if st.button("_", key=f"cvb_scale_{sv}"):
                ss["cvb_font_size"] = max(8, min(16, round(sv / 100.0 * 11)))
                st.rerun()
        # Hidden line-height buttons (val = lh × 10: 10,11,...,20 → 1.0 to 2.0)
        for lhv in range(10, 21):
            if st.button("_", key=f"cvb_lh_{lhv}"):
                ss["cvb_line_height"] = lhv / 10.0
                st.rerun()
        # Hidden entry-spacing buttons (val = px: 0,2,4,...,24)
        for esv in range(0, 25, 2):
            if st.button("_", key=f"cvb_es_{esv}"):
                ss["cvb_entry_spacing"] = esv
                st.rerun()
        # Hidden toggle buttons
        if st.button("_", key="cvb_icons_toggle"):
            ss["cvb_show_icons"] = not ss.get("cvb_show_icons", True)
            st.rerun()
        if st.button("_", key="cvb_photo_toggle"):
            ss["cvb_show_photo"] = not ss.get("cvb_show_photo", False)
            st.rerun()

    _render_left_rail_heading("Sections", "")
    _render_sections_list_component(section_order, visibility, is_dark)
    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    _render_left_rail_heading("Templates", "templates")
    current_tpl = _normalize_template(ss.get("cvb_template", "classic"))
    ss["cvb_template"] = current_tpl
    _render_template_component(current_tpl, is_dark)

    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    _render_left_rail_heading("Style", "style")
    _render_style_component(
        current_accent=ss.get("cvb_accent_color", "#3b82f6"),
        font_size=int(ss.get("cvb_font_size", 11)),
        line_height=float(ss.get("cvb_line_height", 1.4)),
        entry_spacing=int(ss.get("cvb_entry_spacing", 8)),
        show_icons=bool(ss.get("cvb_show_icons", True)),
        show_photo=bool(ss.get("cvb_show_photo", False)),
        is_dark=is_dark,
    )


def _render_middle_panel_native() -> None:
    ss = st.session_state
    order = _normalize_section_order(ss.get("cvb_section_order"))
    visibility = _normalize_section_visibility(ss.get("cvb_section_visibility"))
    ss["cvb_section_visibility"] = visibility

    render_map = {
        "personal": _personal_section,
        "summary": _summary_section,
        "experience": _experience_section,
        "education": _education_section,
        "skills": _skills_section,
        "projects": _projects_section,
        "languages": _languages_section,
        "certifications": _certifications_section,
        "interests": _interests_section,
    }
    visible_order = [sid for sid in order if visibility.get(sid, True)]
    if not visible_order:
        st.info("All sections are hidden. Enable sections from the left sidebar.")
        return

    current_active = ss.get("cvb_active_section", "personal")
    if current_active not in visible_order:
        ss["cvb_active_section"] = visible_order[0]

    for sid in visible_order:
        label = SECTION_ID_TO_LABEL.get(sid, sid.title())
        with st.container(key=f"cvb-section-{sid}"):
            with _section_expander(label, sid, expanded=True):
                render_map[sid]()


def _render_right_panel_native(cv_data: dict, is_dark: bool) -> None:
    ss = st.session_state
    zoom = int(ss.get("cvb_zoom", _default_zoom_for_template(ss.get("cvb_template", "classic"))))
    levels = [35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]

    with st.container(key="cvb-zoom-hidden-buttons"):
        if st.button("_", key="cvb_zoom_out_relay"):
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[max(0, idx - 1)]
            st.rerun()
        if st.button("_", key="cvb_zoom_in_relay"):
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[min(len(levels) - 1, idx + 1)]
            st.rerun()
        if st.button("_", key="cvb_zoom_reset_relay"):
            ss["cvb_zoom"] = _default_zoom_for_template(ss.get("cvb_template", "classic"))
            st.rerun()

    with st.container(key="cvb-preview-tools-native"):
        _render_zoom_toolbar_component(zoom)

    template = _normalize_template(ss.get("cvb_template", "classic"))
    accent = ss.get("cvb_accent_color") or None
    font = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size = int(ss.get("cvb_font_size", 11))
    line_height = float(ss.get("cvb_line_height", 1.4))
    entry_spacing = int(ss.get("cvb_entry_spacing", 8))
    sec_vis = ss.get("cvb_section_visibility")
    sec_order = ss.get("cvb_section_order")

    preview_source = _build_preview_data_with_demo_defaults(cv_data)

    preview_html = generate_cv_html(
        preview_source,
        template,
        accent_color=accent,
        font_family=font,
        font_size=font_size,
        line_height=line_height,
        entry_spacing=entry_spacing,
        preview_dark=is_dark,
        section_visibility=sec_vis,
        section_order=sec_order,
    )
    preview_body = preview_html.split("<body>", 1)[-1].split("</body>", 1)[0] if "<body>" in preview_html else preview_html
    preview_styles = ""
    style_start = preview_html.find("<style>")
    if style_start != -1:
        style_end = preview_html.find("</style>", style_start + 7)
        if style_end != -1:
            preview_styles = preview_html[style_start + 7:style_end]
    scale = zoom / 100.0
    bg = "#0b1220" if is_dark else "#f4f7fb"
    preview_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8' />
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin:0; background:{bg}; }}
body {{ padding:0; }}
.preview-wrap {{ display:flex; justify-content:center; padding:8px; }}
.resume-shell {{
  width: {A4_WIDTH_PX}px;
  min-height: {A4_HEIGHT_PX}px;
  background: #fff;
  box-shadow: none;
  zoom: {scale};
}}
.resume-shell > .paper {{
  width: {A4_WIDTH_PX}px;
  min-height: {A4_HEIGHT_PX}px;
}}
{preview_styles}
</style>
</head>
<body>
  <div class='preview-wrap'><div class='resume-shell'>{preview_body}</div></div>
</body>
</html>"""

    components.html(preview_doc, height=1160, scrolling=False)


def render_cv_builder_page() -> None:
    _init_builder()
    _load_cv_for_builder_if_requested()

    is_dark = st.session_state.get("theme", "light") == "dark"
    _inject_builder_css_native(is_dark)

    ss        = st.session_state
    cv_data   = collect_cv_data()
    template  = _normalize_template(ss.get("cvb_template", "classic"))
    accent    = ss.get("cvb_accent_color") or None
    font      = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size = int(ss.get("cvb_font_size", 11))
    lh        = float(ss.get("cvb_line_height", 1.4))
    spacing   = int(ss.get("cvb_entry_spacing", 8))
    cv_title  = ss.get("cvb_cv_title", "resume") or "resume"

    pdf_bytes = _cached_generate_cv_pdf(
        json.dumps(cv_data, sort_keys=True),
        template, accent, font, font_size, lh, spacing,
    )

    with st.container(key="cvb-page-native"):
        with st.container(key="cvb-toolbar-native"):
            col_left, col_spacer, col_right = st.columns([1.25, 5.75, 3.0], vertical_alignment="center")
            with col_left:
                last_saved = ss.get("cvb_last_saved")
                saved_txt = f"Saved {last_saved}" if last_saved else "Saved --:--:--"
                st.markdown(f"<span class='cvb-saved-ts-native'>{saved_txt}</span>", unsafe_allow_html=True)
            with col_right:
                with st.container(key="cvb-toolbar-actions-native"):
                    a1, a2, a3, a4 = st.columns([1.0, 1.06, 1.57, 0.91], gap="small")
                    with a1:
                        if st.button("Import", key="cvb_toolbar_import"):
                            ss["cvb_show_import"] = not ss.get("cvb_show_import", False)
                            st.rerun()
                    with a2:
                        st.download_button(
                            "Backup",
                            data=_get_backup_json(),
                            file_name="cv_backup.json",
                            mime="application/json",
                            key="cvb_toolbar_backup",
                        )
                    with a3:
                        if pdf_bytes:
                            st.download_button(
                                "Download PDF",
                                data=pdf_bytes,
                                file_name=f"{cv_title.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key="cvb_toolbar_download",
                                type="primary",
                            )
                        else:
                            st.button("Download PDF", key="cvb_toolbar_download_disabled", disabled=True)
                    with a4:
                        if st.button("Reset", key="cvb_toolbar_reset"):
                            ss["cvb_confirm_reset"] = True
                            st.rerun()

        if ss.get("cvb_confirm_reset"):
            st.warning("This will clear all your CV data. This cannot be undone.")
            rc1, rc2, _ = st.columns([1, 1, 6])
            with rc1:
                if st.button("Yes, Reset", key="btn_confirm_reset_native", type="primary"):
                    _reset_all()
            with rc2:
                if st.button("Cancel", key="btn_cancel_reset_native"):
                    ss["cvb_confirm_reset"] = False
                    st.rerun()

        if ss.get("cvb_show_import"):
            uploaded = st.file_uploader("Upload JSON backup", type=["json"], key="cvb_import_file_native")
            if uploaded:
                _import_from_json(uploaded)

        with st.container(key="cvb-main-native"):
            with st.container(key="cvb-main-row-native"):
                col_sidebar, col_editor, col_preview = st.columns(
                    [1.2, 3.2, 2.5],
                    gap="small",
                )
                with col_sidebar:
                    with st.container(key="cvb-left-scroll-native"):
                        _render_left_panel_native()
                with col_editor:
                    with st.container(key="cvb-middle-scroll-native"):
                        _render_middle_panel_native()
                with col_preview:
                    with st.container(key="cvb-right-scroll-native"):
                        _render_right_panel_native(cv_data, is_dark)

    _inject_realtime_js()
    _inject_sections_relay_js()
    return


        # ── TOOLBAR ──────────────────────────────────────────────────────
    if False:
        pass
        with st.container(key="cvb-toolbar"):
            tc_left, tc_title, tc_imp, tc_bak, tc_pdf, tc_save, tc_rst = st.columns(
                [1.5, 2.5, 0.8, 0.8, 1.2, 0.8, 0.7], vertical_alignment="center"
            )
            with tc_left:
                last_saved = ss.get("cvb_last_saved")
                saved_txt  = f"Saved {last_saved}" if last_saved else "Not saved yet"
                st.markdown(f"<span class='cvb-saved-ts'>{saved_txt}</span>", unsafe_allow_html=True)
            with tc_title:
                st.text_input(
                    "Resume title",
                    key="cvb_cv_title",
                    placeholder="My Resume",
                    label_visibility="collapsed",
                )
            with tc_imp:
                if st.button("↑ Import", key="btn_import", use_container_width=True, help="Import JSON backup"):
                    ss["cvb_show_import"] = not ss.get("cvb_show_import", False)
                    st.rerun()
            with tc_bak:
                st.download_button(
                    "Backup", data=_get_backup_json(),
                    file_name="cv_backup.json", mime="application/json",
                    use_container_width=True, key="btn_backup", help="Download JSON backup",
                )
            with tc_pdf:
                if pdf_bytes:
                    st.download_button(
                        "⬇ Download PDF", data=pdf_bytes,
                        file_name=f"{cv_title.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True, key="btn_pdf", type="primary",
                    )
                else:
                    st.button("⬇ Download PDF", disabled=True, use_container_width=True, key="btn_pdf_dis")
            with tc_save:
                if st.button("Save", key="btn_save", use_container_width=True):
                    title = ss.get("cvb_cv_title", "My Resume") or "My Resume"
                    if _save_cv(cv_data, title, template):
                        ss["cvb_last_saved"] = datetime.now().strftime("%I:%M %p")
                        st.rerun()
                    else:
                        st.error("Save failed.")
            with tc_rst:
                if st.button("↺ Reset", key="btn_reset", use_container_width=True):
                    ss["cvb_confirm_reset"] = True
                    st.rerun()

        # ── RESET CONFIRMATION ────────────────────────────────────────────
        if ss.get("cvb_confirm_reset"):
            st.warning("This will clear all your CV data. This cannot be undone.")
            rc1, rc2, rc3 = st.columns([1, 1, 4])
            with rc1:
                if st.button("Yes, Reset", key="btn_confirm_reset", type="primary"):
                    _reset_all()
            with rc2:
                if st.button("Cancel", key="btn_cancel_reset"):
                    ss["cvb_confirm_reset"] = False
                    st.rerun()

        # ── IMPORT PANEL ─────────────────────────────────────────────────
        if ss.get("cvb_show_import"):
            uploaded = st.file_uploader(
                "Upload JSON backup", type=["json"],
                key="cvb_import_file", label_visibility="collapsed",
            )
            if uploaded:
                _import_from_json(uploaded)

        # ── MAIN 3-PANEL GRID ─────────────────────────────────────────────
        with st.container(key="cvb-main-grid"):
            col_left, col_mid, col_right = st.columns([0.75, 1.5, 1.75], gap="small")

            with col_left:
                with st.container(key="cvb-left-panel"):
                    _render_left_panel()

            with col_mid:
                with st.container(key="cvb-center-panel"):
                    with st.container(key="cvb-personal-card"):
                        with st.expander("👤 Personal Information", expanded=True):
                            _personal_section()
                    with st.expander("📄 Professional Summary", expanded=False):
                        _summary_section()
                    with st.expander("💼 Work Experience", expanded=False):
                        _experience_section()
                    with st.expander("🎓 Education", expanded=False):
                        _education_section()
                    with st.expander("⚙ Skills", expanded=False):
                        _skills_section()
                    with st.expander("📁 Projects", expanded=False):
                        _projects_section()
                    with st.expander("🌐 Languages", expanded=False):
                        _languages_section()
                    with st.expander("🏆 Certifications", expanded=False):
                        _certifications_section()
                    with st.expander("⭐ Interests", expanded=False):
                        _interests_section()

            with col_right:
                with st.container(key="cvb-right-panel"):
                    _render_right_panel(cv_data, is_dark)


# --- CVReviewer middle-panel overrides (latest) ---
def _experience_section() -> None:
    if st.button("+ Add Position", key="btn_add_exp", type="secondary"):
        eid = str(uuid.uuid4())
        st.session_state["cvb_exp_ids"].append(eid)
        st.session_state[f"cvb_exp_bcount_{eid}"] = 1
        st.session_state[f"cvb_exp_b_{eid}_0"] = ""
        st.rerun()

    for idx, eid in enumerate(list(st.session_state.get("cvb_exp_ids", []))):
        role = st.session_state.get(f"cvb_exp_role_{eid}", "")
        label = role or f"Position {idx + 1}"
        with st.expander(label, expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Job Title", key=f"cvb_exp_role_{eid}", placeholder="Enter job title")
            with c2:
                st.text_input("Company", key=f"cvb_exp_company_{eid}", placeholder="Enter company name")

            c3, c4 = st.columns(2)
            with c3:
                st.text_input("Location", key=f"cvb_exp_loc_{eid}", placeholder="Enter location")
            with c4:
                st.checkbox("Currently working here", key=f"cvb_exp_curr_{eid}")

            c5, c6 = st.columns(2)
            with c5:
                _date_field("Start Date", f"cvb_exp_start_{eid}")
            with c6:
                if st.session_state.get(f"cvb_exp_curr_{eid}", False):
                    st.text_input("End Date", value="Present", disabled=True, key=f"cvb_exp_end_dis_{eid}")
                    st.session_state[f"cvb_exp_end_{eid}"] = ""
                else:
                    _date_field("End Date", f"cvb_exp_end_{eid}")

            st.markdown("**Key Achievements**")
            bcount = st.session_state.get(f"cvb_exp_bcount_{eid}", 1)
            for i in range(bcount):
                st.text_input(
                    f"Bullet {i + 1}",
                    key=f"cvb_exp_b_{eid}_{i}",
                    placeholder="Describe a measurable impact or responsibility",
                )

            ba, bb, bc, bd = st.columns([1, 1, 1.4, 1.4])
            with ba:
                if st.button("+ Bullet", key=f"add_b_{eid}"):
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount + 1
                    st.rerun()
            with bb:
                if bcount > 1 and st.button("Remove Bullet", key=f"rem_b_{eid}"):
                    st.session_state.pop(f"cvb_exp_b_{eid}_{bcount - 1}", None)
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount - 1
                    st.rerun()
            with bc:
                if st.button("AI Suggest", key=f"ai_suggest_{eid}"):
                    role_val = st.session_state.get(f"cvb_exp_role_{eid}", "").strip()
                    company_val = st.session_state.get(f"cvb_exp_company_{eid}", "").strip()
                    if not role_val:
                        st.warning("Enter a job title first.")
                    else:
                        with st.spinner("Generating..."):
                            try:
                                existing = [
                                    st.session_state.get(f"cvb_exp_b_{eid}_{i}", "")
                                    for i in range(bcount)
                                    if st.session_state.get(f"cvb_exp_b_{eid}_{i}", "").strip()
                                ]
                                context = ("Existing: " + " | ".join(existing)) if existing else ""
                                st.session_state[f"cvb_ai_sug_{eid}"] = suggest_cv_bullets(role_val, company_val, context)
                            except Exception as exc:
                                st.error(str(exc))
            with bd:
                if st.button("Delete Position", key=f"rem_exp_{eid}"):
                    st.session_state["cvb_exp_ids"].remove(eid)
                    st.session_state.pop(f"cvb_ai_sug_{eid}", None)
                    st.rerun()

            suggestions = st.session_state.get(f"cvb_ai_sug_{eid}", [])
            if suggestions:
                st.markdown("**AI Suggestions**")
                for si, sug in enumerate(suggestions):
                    sc1, sc2 = st.columns([6, 1])
                    with sc1:
                        st.caption(f"- {sug}")
                    with sc2:
                        if st.button("Use", key=f"use_s_{eid}_{si}"):
                            new_idx = st.session_state.get(f"cvb_exp_bcount_{eid}", 1)
                            st.session_state[f"cvb_exp_b_{eid}_{new_idx}"] = sug
                            st.session_state[f"cvb_exp_bcount_{eid}"] = new_idx + 1
                            st.rerun()


def _education_section() -> None:
    if st.button("+ Add Education", key="btn_add_edu", type="secondary"):
        eid = str(uuid.uuid4())
        st.session_state["cvb_edu_ids"].append(eid)
        st.rerun()

    for idx, eid in enumerate(list(st.session_state.get("cvb_edu_ids", []))):
        inst = st.session_state.get(f"cvb_edu_inst_{eid}", "")
        with st.expander(inst or f"Education {idx + 1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Institution", key=f"cvb_edu_inst_{eid}", placeholder="Enter institution name")
            with c2:
                st.text_input("Degree", key=f"cvb_edu_degree_{eid}", placeholder="Enter degree")

            c3, c4 = st.columns(2)
            with c3:
                st.text_input("Field of Study", key=f"cvb_edu_field_{eid}", placeholder="Enter field of study")
            with c4:
                st.text_input("Location", key=f"cvb_edu_loc_{eid}", placeholder="Enter location")

            c5, c6 = st.columns(2)
            with c5:
                _date_field("Start Date", f"cvb_edu_start_{eid}")
            with c6:
                _date_field("End Date", f"cvb_edu_end_{eid}")

            st.text_input("GPA / Percentage", key=f"cvb_edu_gpa_{eid}", placeholder="Enter GPA or percentage")
            if st.button("Delete Education", key=f"rem_edu_{eid}"):
                st.session_state["cvb_edu_ids"].remove(eid)
                st.rerun()


def _skills_section() -> None:
    _skill_spacer, _skill_action = st.columns([5, 2])
    with _skill_action:
        add_skill = st.button("+ Add Skill", key="btn_add_skill", type="secondary")
    if add_skill:
        sid = str(uuid.uuid4())
        st.session_state["cvb_skill_ids"].append(sid)
        st.session_state[f"cvb_skill_item_{sid}"] = ""
        st.rerun()

    skill_ids = list(st.session_state.get("cvb_skill_ids", []))
    if not skill_ids:
        st.info("Add skills one by one, for example: React, Python, SQL.")
        return

    for idx, sid in enumerate(skill_ids):
        c1, c2 = st.columns([8, 1])
        with c1:
            st.text_input(
                f"Skill {idx + 1}",
                key=f"cvb_skill_item_{sid}",
                placeholder="Enter skill",
                label_visibility="collapsed",
            )
        with c2:
            st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
            if st.button("Delete", key=f"rem_skill_{sid}", help="Remove skill"):
                st.session_state["cvb_skill_ids"].remove(sid)
                st.session_state.pop(f"cvb_skill_item_{sid}", None)
                st.rerun()


def _projects_section() -> None:
    _proj_spacer, _proj_action = st.columns([5, 2])
    with _proj_action:
        add_project = st.button("+ Add Project", key="btn_add_proj", type="secondary")
    if add_project:
        pid = str(uuid.uuid4())
        st.session_state["cvb_proj_ids"].append(pid)
        st.rerun()
    for idx, pid in enumerate(list(st.session_state.get("cvb_proj_ids", []))):
        name = st.session_state.get(f"cvb_proj_name_{pid}", "")
        with st.expander(name or f"Project {idx + 1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Project Name", key=f"cvb_proj_name_{pid}", placeholder="Enter project name")
            with c2:
                st.text_input("Your Role", key=f"cvb_proj_role_{pid}", placeholder="Enter your role")

            c3, c4 = st.columns(2)
            with c3:
                _date_field("Start Date", f"cvb_proj_start_{pid}")
            with c4:
                _date_field("End Date", f"cvb_proj_end_{pid}")

            st.text_area(
                "Description",
                key=f"cvb_proj_desc_{pid}",
                height=80,
                placeholder="Describe what the project does and your impact",
            )
            st.text_input(
                "Technologies (comma-separated)",
                key=f"cvb_proj_tech_{pid}",
                placeholder="Enter technologies separated by commas",
            )
            st.text_input("Link (GitHub / Live)", key=f"cvb_proj_link_{pid}", placeholder="Enter project link")
            if st.button("Delete Project", key=f"rem_proj_{pid}"):
                st.session_state["cvb_proj_ids"].remove(pid)
                st.rerun()


def _certifications_section() -> None:
    _cert_spacer, _cert_action = st.columns([5, 2])
    with _cert_action:
        add_cert = st.button("+ Add Certification", key="btn_add_cert", type="secondary")
    if add_cert:
        cid = str(uuid.uuid4())
        st.session_state["cvb_cert_ids"].append(cid)
        st.rerun()
    for idx, cid in enumerate(list(st.session_state.get("cvb_cert_ids", []))):
        name = st.session_state.get(f"cvb_cert_name_{cid}", "")
        with st.expander(name or f"Certification {idx + 1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Title", key=f"cvb_cert_name_{cid}", placeholder="Enter certification title")
            with c2:
                st.text_input("Issuer", key=f"cvb_cert_issuer_{cid}", placeholder="Enter issuer")
            _date_field("Date", f"cvb_cert_date_{cid}")
            st.text_input("Credential URL", key=f"cvb_cert_link_{cid}", placeholder="Enter credential URL")
            if st.button("Delete Certification", key=f"rem_cert_{cid}"):
                st.session_state["cvb_cert_ids"].remove(cid)
                st.rerun()


# --- CVReviewer template-structure overrides (safe, isolated) ---
def generate_cv_html(
    data: dict,
    template: str = "classic",
    accent_color: str | None = None,
    font_family: str | None = None,
    font_size: int = 11,
    line_height: float = 1.4,
    entry_spacing: int = 8,
    preview_dark: bool = False,
    section_visibility: dict | None = None,
    section_order: list | None = None,
) -> str:
    """Generate template-accurate resume preview HTML.

    This override keeps data contracts intact while aligning structure with CVReviewer:
    - modern: strong sidebar + main content
    - classic: ATS single-column
    - creative: light sidebar + editorial right content
    """
    tpl = _normalize_template(template)
    cfg = dict(TEMPLATE_CONFIGS.get(tpl, TEMPLATE_CONFIGS["classic"]))
    if accent_color:
        cfg["primary"] = accent_color
        cfg["rule"] = accent_color
        cfg["link"] = accent_color
    if font_family:
        cfg["font"] = font_family

    vis = _normalize_section_visibility(section_visibility)
    order = _normalize_section_order(section_order)
    fs = max(9, int(font_size))
    fs_sm = max(8, fs - 1)
    fs_xs = max(7, fs - 2)
    lh = max(1.15, float(line_height))
    es = max(4, int(entry_spacing))

    bg_page = "#0b1220" if preview_dark else "#f8fafc"
    paper_bg = "#111827" if preview_dark else "#ffffff"
    text = "#e5e7eb" if preview_dark else "#0f172a"
    muted = "#94a3b8" if preview_dark else "#64748b"
    line = "#334155" if preview_dark else "#dbe4f0"

    p = data.get("personal", {}) or {}
    name = _html_escape((p.get("full_name") or "Your Name").strip() or "Your Name")
    title = _html_escape((p.get("prof_title") or "").strip())
    summary = _html_escape((p.get("summary") or "").strip())

    contacts_raw = [
        ("Email", p.get("email", "")),
        ("Phone", p.get("phone", "")),
        ("Location", p.get("location", "")),
        ("Website", p.get("website", "")),
        ("LinkedIn", p.get("linkedin", "")),
        ("GitHub", p.get("github", "")),
    ]
    contacts = [(k, str(v).strip()) for k, v in contacts_raw if str(v or "").strip()]
    contact_line = " \u00b7 ".join(_html_escape(v) for _, v in contacts)

    def _skills_list() -> list[str]:
        vals: list[str] = []
        for item in data.get("skills", {}).get("items", []):
            name_val = str(item.get("name", "")).strip()
            if name_val:
                vals.append(name_val)
        if not vals:
            for cat in data.get("skills", {}).get("categories", []):
                for it in cat.get("items", []):
                    txt = str(it).strip()
                    if txt:
                        vals.append(txt)
        return vals

    skill_values = _skills_list()

    def _date_range_html(start: str, end: str, current: bool = False) -> str:
        return _html_escape(_date_range(start, end, current))

    def _sec(title_text: str, inner: str) -> str:
        if not inner.strip():
            return ""
        return (
            "<section class='cv-sec'>"
            f"<h2 class='cv-sec-h'>{_html_escape(title_text)}</h2>"
            f"{inner}</section>"
        )

    def _sec_compact(title_text: str, inner: str) -> str:
        if not inner.strip():
            return ""
        return (
            "<section class='cv-sec cv-sec-compact'>"
            f"<h2 class='cv-sec-h'>{_html_escape(title_text)}</h2>"
            f"{inner}</section>"
        )

    def _summary_html() -> str:
        if not summary:
            return ""
        return f"<p class='cv-p'>{summary}</p>"

    def _experience_html() -> str:
        parts: list[str] = []
        for exp in data.get("experience", []) or []:
            role = _html_escape(exp.get("role", ""))
            company = _html_escape(exp.get("company", ""))
            loc = _html_escape(exp.get("location", ""))
            dr = _date_range_html(exp.get("start_date", ""), exp.get("end_date", ""), bool(exp.get("current", False)))
            bullets = [str(b).strip() for b in exp.get("bullets", []) if str(b).strip()]

            row_top = (
                "<div class='row-top'>"
                f"<div class='role'>{role}</div>"
                f"<div class='dr'>{dr}</div>"
                "</div>"
            )
            row_sub = f"<div class='row-sub'>{company}{(', ' + loc) if loc else ''}</div>"
            bullet_html = "".join(f"<li>{_html_escape(b)}</li>" for b in bullets)
            parts.append(
                "<div class='cv-entry'>"
                f"{row_top}{row_sub}"
                + (f"<ul class='cv-ul'>{bullet_html}</ul>" if bullet_html else "")
                + "</div>"
            )
        return "".join(parts)

    def _education_html() -> str:
        parts: list[str] = []
        for edu in data.get("education", []) or []:
            inst = _html_escape(edu.get("institution", ""))
            degree = _html_escape(edu.get("degree", ""))
            field = _html_escape(edu.get("field", ""))
            loc = _html_escape(edu.get("location", ""))
            gpa = _html_escape(edu.get("gpa", ""))
            dr = _date_range_html(edu.get("start_date", ""), edu.get("end_date", ""), False)
            desc_left = " \u00b7 ".join([x for x in [degree, field] if x])
            if gpa:
                desc_left = f"{desc_left}{' \u00b7 ' if desc_left else ''}GPA: {gpa}"

            parts.append(
                "<div class='cv-entry'>"
                "<div class='row-top'>"
                f"<div class='role'>{inst}</div>"
                f"<div class='dr'>{dr}</div>"
                "</div>"
                f"<div class='row-sub'>{desc_left}{(', ' + loc) if loc else ''}</div>"
                "</div>"
            )
        return "".join(parts)

    def _projects_html() -> str:
        parts: list[str] = []
        for proj in data.get("projects", []) or []:
            name_val = _html_escape(proj.get("name", ""))
            role_val = _html_escape(proj.get("role", ""))
            desc = _html_escape(proj.get("description", ""))
            link_val = _html_escape(proj.get("link", ""))
            tech = [str(x).strip() for x in proj.get("tech_stack", []) if str(x).strip()]
            dr = _date_range_html(proj.get("start_date", ""), proj.get("end_date", ""), False)
            row_sub = role_val or ""
            if tech:
                tech_line = _html_escape(", ".join(tech))
                row_sub = f"{row_sub}{' \u00b7 ' if row_sub else ''}{tech_line}"
            parts.append(
                "<div class='cv-entry'>"
                "<div class='row-top'>"
                f"<div class='role'>{name_val}</div>"
                f"<div class='dr'>{dr}</div>"
                "</div>"
                + (f"<div class='row-sub'>{row_sub}</div>" if row_sub else "")
                + (f"<p class='cv-p'>{desc}</p>" if desc else "")
                + (f"<p class='cv-link'>{link_val}</p>" if link_val else "")
                + "</div>"
            )
        return "".join(parts)

    def _languages_html() -> str:
        rows: list[str] = []
        for lang in data.get("languages", []) or []:
            nm = _html_escape(lang.get("language", ""))
            pf = _html_escape(lang.get("proficiency", ""))
            if not nm:
                continue
            rows.append(f"<div class='kv'><span>{nm}</span><span>{pf}</span></div>")
        return "".join(rows)

    def _certifications_html() -> str:
        rows: list[str] = []
        for cert in data.get("certifications", []) or []:
            nm = _html_escape(cert.get("name", ""))
            if not nm:
                continue
            issuer = _html_escape(cert.get("issuer", ""))
            dt = _html_escape(cert.get("date", ""))
            extra = " \u00b7 ".join([x for x in [issuer, dt] if x])
            rows.append(f"<p class='cv-p'><strong>{nm}</strong>{(' \u2014 ' + extra) if extra else ''}</p>")
        return "".join(rows)

    def _interests_html() -> str:
        vals = [str(x).strip() for x in (data.get("interests", []) or []) if str(x).strip()]
        if not vals:
            return ""
        return f"<p class='cv-p'>{_html_escape(', '.join(vals))}</p>"

    def _skills_plain_html() -> str:
        if not skill_values:
            return ""
        return "".join(f"<p class='cv-p'>{_html_escape(v)}</p>" for v in skill_values)

    def _skills_dots_html() -> str:
        if not skill_values:
            return ""
        rows: list[str] = []
        for idx, sk in enumerate(skill_values):
            filled = 3 + ((len(sk) + idx) % 3)  # 3..5 (deterministic for preview stability)
            dots = "".join("<i class='dot on'></i>" if i < filled else "<i class='dot'></i>" for i in range(5))
            rows.append(f"<div class='skill-row'><span>{_html_escape(sk)}</span><span class='dots'>{dots}</span></div>")
        return "".join(rows)

    section_map = {
        "summary": _summary_html(),
        "experience": _experience_html(),
        "education": _education_html(),
        "skills": _skills_plain_html(),
        "projects": _projects_html(),
        "languages": _languages_html(),
        "certifications": _certifications_html(),
        "interests": _interests_html(),
    }

    def _section_label(section_id: str) -> str:
        return SECTION_ID_TO_LABEL.get(section_id, section_id.replace("_", " ").title())

    def _ordered_sections(ids: list[str], compact: bool = False) -> str:
        html_parts: list[str] = []
        for sid in ids:
            if sid == "personal":
                continue
            if not vis.get(sid, True):
                continue
            inner = section_map.get(sid, "")
            if not inner.strip():
                continue
            label = _section_label(sid)
            html_parts.append(_sec_compact(label, inner) if compact else _sec(label, inner))
        return "".join(html_parts)

    # Classic (ATS single column)
    classic_body = (
        "<div class='cv-paper classic'>"
        "<header class='cv-head center'>"
        f"<h1 id='cv-name'>{name}</h1>"
        + (f"<p class='cv-title'>{title}</p>" if title else "")
        + (f"<p id='cv-contact' class='cv-contact'>{contact_line}</p>" if contact_line else "<p id='cv-contact' class='cv-contact' style='display:none'></p>")
        + "</header>"
        + _ordered_sections(order, compact=False)
        + "</div>"
    )

    # Modern (CVReviewer-like blue sidebar)
    left_pref_modern = {"skills", "languages", "certifications", "interests"}
    left_modern_ids = [sid for sid in order if sid in left_pref_modern and vis.get(sid, True)]
    right_modern_ids = [sid for sid in order if sid not in left_pref_modern and sid != "personal" and vis.get(sid, True)]
    modern_left_sections: list[str] = []
    for sid in left_modern_ids:
        if sid == "skills":
            modern_left_sections.append(_sec_compact("Skills", _skills_dots_html()))
        else:
            inner = section_map.get(sid, "")
            if inner.strip():
                modern_left_sections.append(_sec_compact(_section_label(sid), inner))

    modern_body = (
        "<div class='cv-paper modern'>"
        "<div class='modern-grid'>"
        "<aside class='modern-left'>"
        f"<h1 id='cv-name'>{name}</h1>"
        + (f"<p class='cv-title'>{title}</p>" if title else "")
        + (
            "<div class='contact-stack'>"
            + "".join(f"<p>{_html_escape(v)}</p>" for _, v in contacts)
            + "</div>"
            if contacts else ""
        )
        + "".join(modern_left_sections)
        + "</aside>"
        "<main class='modern-right'>"
        + ( _sec("Professional Summary", section_map.get("summary", "")) if vis.get("summary", True) else "" )
        + _ordered_sections([sid for sid in right_modern_ids if sid != "summary"], compact=False)
        + "</main>"
        + "</div></div>"
    )

    # Creative (CVReviewer-like light/colored sidebar)
    left_pref_creative = {"skills", "languages", "interests"}
    right_creative_ids = [sid for sid in order if sid not in left_pref_creative and sid != "personal" and vis.get(sid, True)]
    left_creative_ids = [sid for sid in order if sid in left_pref_creative and vis.get(sid, True)]
    creative_left_sections: list[str] = []
    for sid in left_creative_ids:
        if sid == "skills":
            if skill_values:
                bars = "".join(
                    f"<div class='bar-row'><span>{_html_escape(sk)}</span><i></i></div>"
                    for sk in skill_values
                )
                creative_left_sections.append(_sec_compact("Skills", f"<div class='bars'>{bars}</div>"))
        else:
            inner = section_map.get(sid, "")
            if inner.strip():
                creative_left_sections.append(_sec_compact(_section_label(sid), inner))

    creative_body = (
        "<div class='cv-paper creative'>"
        "<div class='creative-grid'>"
        "<aside class='creative-left'>"
        f"<h1 id='cv-name'>{name}</h1>"
        + (f"<p class='cv-title'>{title}</p>" if title else "")
        + (
            "<div class='contact-stack'>"
            + "".join(f"<p>{_html_escape(v)}</p>" for _, v in contacts)
            + "</div>"
            if contacts else ""
        )
        + "".join(creative_left_sections)
        + "</aside>"
        "<main class='creative-right'>"
        + ( _sec("About Me", section_map.get("summary", "")) if vis.get("summary", True) else "" )
        + _ordered_sections([sid for sid in right_creative_ids if sid != "summary"], compact=False)
        + "</main>"
        + "</div></div>"
    )

    selected_body = classic_body
    if tpl == "modern":
        selected_body = modern_body
    elif tpl == "creative":
        selected_body = creative_body

    primary = cfg["primary"]
    primary_soft = f"{primary}1A"
    link_color = cfg["link"]

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; }}
body {{
  background:{bg_page};
  font-family:{cfg["font"]};
  color:{text};
  padding:0;
}}
.cv-paper {{
  width:100%;
  background:{paper_bg};
  color:{text};
  border:1px solid {line};
}}
.classic {{ padding:14px 16px; }}
.cv-head.center {{ text-align:center; margin-bottom:8px; }}
#cv-name {{ margin:0; font-size:{max(20, fs + 8)}px; font-weight:800; color:{primary}; line-height:1.1; }}
.cv-title {{ margin:3px 0 0; color:{muted}; font-size:{fs}px; }}
.cv-contact {{ margin:5px 0 0; color:{muted}; font-size:{fs_xs}px; }}
.cv-sec {{ margin-top:{max(7, es)}px; }}
.cv-sec-h {{
  margin:0 0 5px;
  font-size:{fs_xs}px;
  text-transform:uppercase;
  letter-spacing:1px;
  font-weight:800;
  color:{primary};
  border-bottom:1.5px solid {primary};
  padding-bottom:3px;
}}
.cv-sec-compact .cv-sec-h {{
  border-bottom:1px solid {primary};
  font-size:{max(7, fs_xs - 1)}px;
  margin-bottom:4px;
}}
.cv-entry {{ margin:0 0 {max(5, es - 1)}px; }}
.row-top {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-end; }}
.role {{ font-size:{fs}px; font-weight:700; }}
.dr {{ font-size:{fs_xs}px; color:{muted}; white-space:nowrap; }}
.row-sub {{ font-size:{fs_xs}px; color:{muted}; margin-top:1px; font-style:italic; }}
.cv-ul {{ margin:3px 0 0 14px; padding:0; }}
.cv-ul li {{ margin:1px 0; font-size:{fs_xs}px; line-height:{lh}; }}
.cv-p {{ margin:0 0 3px; font-size:{fs_xs}px; line-height:{lh}; color:{text}; }}
.cv-link {{ margin:2px 0 0; font-size:{fs_xs}px; color:{link_color}; word-break:break-word; }}
.kv {{ display:flex; justify-content:space-between; gap:8px; margin:0 0 3px; font-size:{fs_xs}px; line-height:{lh}; }}

/* Modern template */
.modern .modern-grid {{ display:grid; grid-template-columns: 32% 68%; }}
.modern-left {{
  background:{primary};
  color:#ffffff;
  padding:16px 14px;
  border-right:1px solid {line};
}}
.modern-left #cv-name {{ color:#ffffff; font-size:{max(18, fs + 7)}px; }}
.modern-left .cv-title {{ color:#dbeafe; }}
.contact-stack {{ margin-top:8px; }}
.contact-stack p {{
  margin:0 0 4px;
  font-size:{fs_xs}px;
  line-height:{lh};
  color:inherit;
  word-break:break-word;
}}
.modern-left .cv-sec {{ margin-top:{max(6, es - 1)}px; }}
.modern-left .cv-sec-h {{
  color:#ffffff;
  border-bottom:1px solid rgba(255,255,255,0.45);
}}
.modern-left .cv-p, .modern-left .kv, .modern-left .row-sub {{ color:#eff6ff; }}
.modern-right {{ padding:14px 16px; }}
.skill-row {{
  display:flex;
  justify-content:space-between;
  gap:8px;
  margin:0 0 4px;
  font-size:{fs_xs}px;
}}
.dots {{ display:inline-flex; gap:3px; align-items:center; }}
.dot {{
  width:6px; height:6px; border-radius:50%;
  background:rgba(255,255,255,0.35);
}}
.dot.on {{ background:#ffffff; }}

/* Creative template */
.creative .creative-grid {{ display:grid; grid-template-columns: 30% 70%; }}
.creative-left {{
  background:{primary_soft};
  border-right:2px solid {primary};
  padding:14px 12px;
}}
.creative-left #cv-name {{ font-size:{max(18, fs + 7)}px; color:{primary}; }}
.creative-left .cv-title {{ color:{muted}; }}
.creative-left .cv-sec-h {{
  color:{primary};
  border-bottom:1px solid {primary};
}}
.creative-right {{ padding:14px 16px; }}
.creative-right .cv-entry {{
  border-left:2px solid {primary_soft};
  padding-left:10px;
}}
.bars .bar-row {{
  display:grid;
  grid-template-columns:1fr 1fr;
  align-items:center;
  gap:8px;
  margin:0 0 4px;
  font-size:{fs_xs}px;
}}
.bars .bar-row i {{
  display:block;
  height:5px;
  border-radius:999px;
  background:linear-gradient(90deg, {primary} 70%, #cbd5e1 70%);
}}
</style>
</head>
<body>
{selected_body}
<script>
window.addEventListener('message', function(ev) {{
  var d = ev.data;
  if (!d || d.type !== 'cv-rt-update') return;
  var el;
  if (d.field === 'cvb_full_name') {{
    el = document.getElementById('cv-name');
    if (el) el.textContent = d.value || 'Your Name';
  }}
}});
</script>
</body>
</html>"""


def _get_demo_cv_data() -> dict:
    """Static demo data for previewing template structures."""
    return {
        "personal": {
            "full_name": "Your Name",
            "prof_title": "Professional Title",
            "email": "you@email.com",
            "phone": "+1 (555) 123-4567",
            "location": "Your City, Country",
            "website": "yourwebsite.dev",
            "linkedin": "linkedin.com/in/yourprofile",
            "github": "github.com/yourhandle",
            "summary": (
                "Write a concise professional summary highlighting your years of experience, "
                "core strengths, and measurable impact."
            ),
        },
        "experience": [
            {
                "role": "Senior Full-Stack Developer",
                "company": "TechVista Inc.",
                "location": "San Francisco, CA",
                "start_date": "2021-03-01",
                "end_date": "",
                "current": True,
                "bullets": [
                    "Architected and built real-time collaboration features.",
                    "Reduced page load times by 60% through code optimization.",
                    "Mentored a team of 5 developers.",
                ],
            },
            {
                "role": "Full-Stack Developer",
                "company": "DataFlow Systems",
                "location": "Austin, TX",
                "start_date": "2018-06-01",
                "end_date": "2021-02-01",
                "current": False,
                "bullets": [
                    "Built RESTful APIs serving high-traffic SaaS products.",
                    "Improved developer productivity by modernizing tooling.",
                ],
            },
        ],
        "education": [
            {
                "institution": "University of California",
                "degree": "B.S.",
                "field": "Computer Science",
                "location": "Berkeley, CA",
                "start_date": "2014-08-01",
                "end_date": "2018-05-01",
                "gpa": "3.8/4.0",
            }
        ],
        "skills": {
            "items": [
                {"name": "React / Next.js"},
                {"name": "TypeScript"},
                {"name": "Node.js"},
                {"name": "Python"},
                {"name": "PostgreSQL"},
                {"name": "AWS / Cloud"},
                {"name": "Docker / K8s"},
                {"name": "GraphQL"},
            ],
            "categories": [],
        },
        "projects": [
            {
                "name": "OpenBoard",
                "role": "Creator & Maintainer",
                "description": "Real-time collaborative whiteboard for distributed teams.",
                "tech_stack": ["React", "WebSocket", "Canvas API"],
                "link": "github.com/alexchen/openboard",
                "start_date": "2023-01-01",
                "end_date": "",
            }
        ],
        "certifications": [
            {"name": "AWS Solutions Architect", "issuer": "Amazon", "date": "Apr 2023", "link": ""},
            {"name": "Google Cloud Professional Developer", "issuer": "Google", "date": "Aug 2022", "link": ""},
        ],
        "languages": [
            {"language": "English", "proficiency": "Native"},
            {"language": "Mandarin", "proficiency": "Fluent"},
            {"language": "Spanish", "proficiency": "Intermediate"},
        ],
        "interests": ["Open Source", "Technical Writing", "Photography"],
    }


def _has_meaningful_text(value: object) -> bool:
    return bool(str(value or "").strip())


def _row_has_meaningful_data(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    for value in row.values():
        if isinstance(value, list):
            if any(_has_meaningful_text(v) for v in value):
                return True
        elif isinstance(value, dict):
            if _row_has_meaningful_data(value):
                return True
        elif isinstance(value, bool):
            if value:
                return True
        else:
            if _has_meaningful_text(value):
                return True
    return False


def _build_preview_data_with_demo_defaults(user_data: dict) -> dict:
    """Merge user CV data over demo defaults for preview-only rendering.

    Rules:
    - Personal fields: fallback field-by-field to demo values.
    - List sections (experience, education, projects, etc.): if user has real rows, use user rows;
      otherwise use demo rows.
    - Skills: if user has skill items, use them; otherwise demo skills.
    """
    demo = _get_demo_cv_data()
    user = user_data if isinstance(user_data, dict) else {}

    out = {
        "personal": {},
        "experience": [],
        "education": [],
        "skills": {"items": [], "categories": []},
        "projects": [],
        "certifications": [],
        "languages": [],
        "interests": [],
        "customization": user.get("customization", {}),
    }

    up = user.get("personal", {}) if isinstance(user.get("personal", {}), dict) else {}
    dp = demo.get("personal", {})
    for key in set(dp.keys()) | set(up.keys()):
        uval = up.get(key, "")
        out["personal"][key] = uval if _has_meaningful_text(uval) else dp.get(key, "")

    for section_key in ["experience", "education", "projects", "certifications", "languages"]:
        urows = user.get(section_key, []) if isinstance(user.get(section_key, []), list) else []
        drows = demo.get(section_key, [])
        meaningful_user_rows = [row for row in urows if _row_has_meaningful_data(row)]
        out[section_key] = meaningful_user_rows if meaningful_user_rows else drows

    uskills = user.get("skills", {}) if isinstance(user.get("skills", {}), dict) else {}
    uitems = uskills.get("items", []) if isinstance(uskills.get("items", []), list) else []
    cleaned_uitems = []
    for item in uitems:
        if isinstance(item, dict) and _has_meaningful_text(item.get("name", "")):
            cleaned_uitems.append({"name": str(item.get("name", "")).strip()})
    if cleaned_uitems:
        out["skills"]["items"] = cleaned_uitems
        out["skills"]["categories"] = [{"id": "primary", "name": "Skills", "items": [s["name"] for s in cleaned_uitems]}]
    else:
        out["skills"] = demo.get("skills", {"items": [], "categories": []})

    uinterests = user.get("interests", []) if isinstance(user.get("interests", []), list) else []
    cleaned_interests = [str(v).strip() for v in uinterests if _has_meaningful_text(v)]
    out["interests"] = cleaned_interests if cleaned_interests else demo.get("interests", [])

    return out


def _is_cv_data_effectively_empty(cv_data: dict) -> bool:
    """True when user has not entered meaningful builder content yet."""
    if not isinstance(cv_data, dict):
        return True

    personal = cv_data.get("personal", {}) or {}
    for field in ["full_name", "prof_title", "email", "phone", "location", "website", "linkedin", "github", "summary"]:
        if str(personal.get(field, "")).strip():
            return False

    for key in ["experience", "education", "projects", "certifications", "languages"]:
        rows = cv_data.get(key, []) or []
        for row in rows:
            if isinstance(row, dict) and any(str(v).strip() for v in row.values() if not isinstance(v, (list, dict, bool))):
                return False
            if isinstance(row, dict):
                for v in row.values():
                    if isinstance(v, list) and any(str(x).strip() for x in v):
                        return False

    skills = cv_data.get("skills", {}) or {}
    for item in skills.get("items", []) or []:
        if str(item.get("name", "")).strip():
            return False
    for cat in skills.get("categories", []) or []:
        if any(str(x).strip() for x in (cat.get("items", []) or [])):
            return False

    if any(str(x).strip() for x in (cv_data.get("interests", []) or [])):
        return False
    return True


def _render_template_component(current_tpl: str, is_dark: bool) -> None:
    """Render template-selection cards as a custom HTML component.

    Keep the left bar compact (same style as before), while preview shows the template demo.
    """
    bg        = "#1e293b" if is_dark else "#ffffff"
    bg_hover  = "#334155" if is_dark else "#f8fbff"
    bg_active = "#1e3a5f" if is_dark else "rgba(59,130,246,0.12)"
    border    = "#334155" if is_dark else "#d3dce8"
    border_act= "rgba(96,165,250,0.6)" if is_dark else "rgba(59,130,246,0.55)"
    text_main = "#f1f5f9"  if is_dark else "#0f172a"
    text_act  = "#bfdbfe"  if is_dark else "#2563eb"
    text_sub  = "#94a3b8"  if is_dark else "#64748b"
    text_sub_act="#93c5fd" if is_dark else "#2563eb"

    cards_html = ""
    for tpl_key, tpl_label, tpl_desc in TEMPLATE_CHOICES:
        active = current_tpl == tpl_key
        act_cls = " tpl-active" if active else ""
        cards_html += (
            f"<div class='tpl-card{act_cls}' data-tpl='{tpl_key}'>"
            f"<div class='tpl-name'>{tpl_label}</div>"
            f"<div class='tpl-desc'>{tpl_desc}</div>"
            f"</div>"
        )

    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;padding:2px 0 0;margin:0;font-family:system-ui,sans-serif;}}
.tpl-card{{
  display:block;width:100%;text-align:left;cursor:pointer;
  background:{bg};border:1px solid {border};border-radius:8px;
  padding:12px 14px;margin-bottom:8px;transition:all 0.15s;
  position:relative;
}}
.tpl-card:last-child{{margin-bottom:0;}}
.tpl-card:hover{{background:{bg_hover};border-color:rgba(37,99,235,0.25);}}
.tpl-card.tpl-active{{
  background:{bg_active};
  border-color:{border_act};
  box-shadow:inset 0 0 0 1px {border_act};
}}
.tpl-name{{
  font-size:13px;font-weight:600;color:{text_main};
  line-height:1.2;margin-bottom:4px;letter-spacing:-0.01em;
}}
.tpl-active .tpl-name{{color:{text_act};}}
.tpl-desc{{font-size:11px;color:{text_sub};line-height:1.35;}}
.tpl-active .tpl-desc{{color:{text_sub_act};}}
</style>
<div id='tpl-wrap'>{cards_html}</div>
<script>
document.querySelectorAll('.tpl-card').forEach(function(card){{
  card.addEventListener('click',function(){{
    try{{window.parent.postMessage({{type:'cvb-tpl-select',tpl:this.dataset.tpl}},'*');}}catch(e){{}}
  }});
}});
</script>
"""
    components.html(html, height=188, scrolling=False)
