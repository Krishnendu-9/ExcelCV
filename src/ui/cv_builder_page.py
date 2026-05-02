"""CV Builder page — 3-panel workspace (left rail · editor · preview)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

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
    "#3b82f6", "#8b5cf6", "#10b981", "#ef4444",
    "#f97316", "#06b6d4", "#ec4899", "#1e40af",
]

FONT_OPTIONS: dict[str, str] = {
    "System Sans":     "system-ui, sans-serif",
    "Georgia":         "Georgia, serif",
    "Helvetica Neue":  "'Helvetica Neue', Arial, sans-serif",
    "Times New Roman": "'Times New Roman', Times, serif",
}

PROFICIENCY_OPTIONS = ["Basic", "Intermediate", "Advanced", "Fluent", "Native"]

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

CVR_SECTION_ORDER: list[str] = [
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


def _normalize_template(template: str | None) -> str:
    value = (template or "").strip().lower()
    if value == "minimal":
        return "creative"
    if value in TEMPLATE_CONFIGS:
        return value
    return "classic"


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

# ─── Session-state initialisation ────────────────────────────────────────────

def _init_builder() -> None:
    defaults: dict = {
        "cvb_cv_title":       "My Resume",
        "cvb_template":       "classic",
        "cvb_loaded_cv_id":   None,
        "cvb_last_saved":     None,
        "cvb_confirm_reset":  False,
        "cvb_show_import":    False,
        "cvb_accent_color":   "#3b82f6",
        "cvb_font":           "System Sans",
        "cvb_font_size":      11,
        "cvb_line_height":    1.4,
        "cvb_entry_spacing":  8,
        "cvb_show_icons":     True,
        "cvb_show_photo":     False,
        "cvb_zoom":           95,
        "cvb_section_order":      list(SECTION_IDS),
        "cvb_section_visibility": {sid: True for sid in SECTION_IDS},
        "cvb_active_section":     "personal",
        "cvb_sections_bridge_payload": "",
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
    skills_cats = []
    for sid in ss.get("cvb_skill_cat_ids", []):
        raw = ss.get(f"cvb_skill_items_{sid}", "")
        items = [x.strip() for x in raw.replace(",", "\n").splitlines() if x.strip()]
        skills_cats.append({"id": sid, "name": ss.get(f"cvb_skill_name_{sid}", ""), "items": items})
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
        "skills":         {"categories": skills_cats},
        "projects":       projects,
        "certifications": certifications,
        "languages":      languages,
        "interests":      ss.get("cvb_interests", []),
        "customization": {
            "accent_color":  ss.get("cvb_accent_color", "#3b82f6"),
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
    skill_ids = []
    for cat in d.get("skills", {}).get("categories", []):
        sid = cat.get("id") or str(uuid.uuid4())
        skill_ids.append(sid)
        ss[f"cvb_skill_name_{sid}"]  = cat.get("name", "")
        ss[f"cvb_skill_items_{sid}"] = ", ".join(cat.get("items", []))
    ss["cvb_skill_cat_ids"] = skill_ids
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

    skills_html = "".join(
        f'<p style="font-size:{fs}px;margin:2px 0;line-height:{lh}">'
        f'<b>{_html_escape(cat.get("name",""))}</b>: {_html_escape(", ".join(cat.get("items",[])))}</p>'
        for cat in data.get("skills", {}).get("categories", []) if cat.get("items")
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
    st.text_input("Full Name", key="cvb_full_name", placeholder="Krishnendu Ghosh")
    st.text_input("Professional Title", key="cvb_prof_title", placeholder="Full-Stack Developer")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Email", key="cvb_email", placeholder="you@email.com")
    with c2:
        st.text_input("Phone", key="cvb_phone", placeholder="+91 98765 43210")
    c3, c4 = st.columns(2)
    with c3:
        st.text_input("Location", key="cvb_location", placeholder="Kolkata, India")
    with c4:
        st.text_input("Website", key="cvb_website", placeholder="https://yoursite.dev")
    st.text_input("LinkedIn", key="cvb_linkedin", placeholder="linkedin.com/in/you")
    st.text_input("GitHub", key="cvb_github", placeholder="github.com/you")


def _summary_section() -> None:
    summary = st.session_state.get("cvb_summary", "")
    char_count = len(summary)
    st.text_area(
        "Professional Summary",
        key="cvb_summary",
        height=130,
        max_chars=500,
        placeholder="3+ years building full-stack web apps with Python and React. Passionate about clean APIs and great UX.",
    )
    st.caption(f"{char_count}/500 characters")


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
        with st.expander(label, expanded=(idx == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Job Title", key=f"cvb_exp_role_{eid}", placeholder="Software Engineer")
            with c2:
                st.text_input("Company", key=f"cvb_exp_company_{eid}", placeholder="Google")
            with c3:
                st.text_input("Location", key=f"cvb_exp_loc_{eid}", placeholder="Bengaluru, India")

            c4, c5, c6 = st.columns(3)
            with c4:
                st.text_input("Start Date", key=f"cvb_exp_start_{eid}", placeholder="Jan 2022")
            with c5:
                curr = st.session_state.get(f"cvb_exp_curr_{eid}", False)
                if not curr:
                    st.text_input("End Date", key=f"cvb_exp_end_{eid}", placeholder="Dec 2024")
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
                    placeholder="Led a team that reduced API latency by 40%",
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
    if st.button("+ Add Education", key="btn_add_edu", type="secondary"):
        eid = str(uuid.uuid4())
        st.session_state["cvb_edu_ids"].append(eid)
        st.rerun()

    for idx, eid in enumerate(list(st.session_state.get("cvb_edu_ids", []))):
        inst = st.session_state.get(f"cvb_edu_inst_{eid}", "")
        with st.expander(inst or f"Education {idx + 1}", expanded=(idx == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Institution", key=f"cvb_edu_inst_{eid}", placeholder="MAKAUT, Kolkata")
            with c2:
                st.text_input("Degree", key=f"cvb_edu_degree_{eid}", placeholder="MCA")
            with c3:
                st.text_input("Field of Study", key=f"cvb_edu_field_{eid}", placeholder="Computer Science")
            c4, c5, c6 = st.columns(3)
            with c4:
                st.text_input("Location", key=f"cvb_edu_loc_{eid}", placeholder="Kolkata, India")
            with c5:
                st.text_input("Start Year", key=f"cvb_edu_start_{eid}", placeholder="2022")
            with c6:
                st.text_input("End Year", key=f"cvb_edu_end_{eid}", placeholder="2024")
            st.text_input("GPA / Percentage", key=f"cvb_edu_gpa_{eid}", placeholder="8.5 / 10")
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
            st.text_input("Category Name", key=f"cvb_skill_name_{sid}", placeholder="Programming Languages")
            st.text_area(
                "Skills (comma-separated)",
                key=f"cvb_skill_items_{sid}",
                height=70,
                placeholder="Python, JavaScript, TypeScript, SQL",
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
        with st.expander(name or f"Project {idx + 1}", expanded=(idx == 0)):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Project Name", key=f"cvb_proj_name_{pid}", placeholder="ExcelCV")
            with c2:
                st.text_input("Your Role", key=f"cvb_proj_role_{pid}", placeholder="Lead Developer")
            with c3:
                st.text_input("Date / Duration", key=f"cvb_proj_start_{pid}", placeholder="Jan–Mar 2024")
            st.text_area("Description", key=f"cvb_proj_desc_{pid}", height=80,
                         placeholder="AI-powered CV builder and ATS analyzer.")
            st.text_input("Technologies (comma-separated)", key=f"cvb_proj_tech_{pid}",
                          placeholder="Python, FastAPI, Next.js")
            st.text_input("Link (GitHub / Live)", key=f"cvb_proj_link_{pid}",
                          placeholder="https://github.com/...")
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
                st.text_input("Language", key=f"cvb_lang_name_{lid}", placeholder="English")
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
                st.text_input("Title", key=f"cvb_cert_name_{cid}", placeholder="AWS Solutions Architect")
            with c2:
                st.text_input("Issuer", key=f"cvb_cert_issuer_{cid}", placeholder="Amazon Web Services")
            with c3:
                st.text_input("Date", key=f"cvb_cert_date_{cid}", placeholder="June 2024")
            st.text_input("Credential URL", key=f"cvb_cert_link_{cid}", placeholder="https://...")
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
            placeholder="e.g. Machine Learning, Open Source",
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
    ss = st.session_state
    section_order = _normalize_section_order(ss.get("cvb_section_order"))
    visibility    = ss.get("cvb_section_visibility", {sid: True for sid in SECTION_IDS})

    st.markdown("<p class='cvb-rail-heading'>Sections</p>", unsafe_allow_html=True)
    if sortable_items is not None:
        order_labels = [SECTION_ID_TO_LABEL.get(sid, sid.title()) for sid in section_order]
        sortable_style = """
        .sortable-component { background: transparent; padding: 0; margin: 0; border: 0; }
        .sortable-container { background: transparent; border: 0; padding: 0; margin: 0; }
        .sortable-container-header { display: none; }
        .sortable-container-body { background: transparent; }
        """
        try:
            sorted_labels = sortable_items(order_labels, key="cvb_sections_sortable_native", custom_style=sortable_style)
        except TypeError:
            sorted_labels = sortable_items(order_labels, custom_style=sortable_style)
        label_to_id = {SECTION_ID_TO_LABEL.get(sid, sid.title()): sid for sid in section_order}
        next_order = [label_to_id[label] for label in (sorted_labels or []) if label in label_to_id]
        next_order = _normalize_section_order(next_order)
        if next_order != section_order:
            ss["cvb_section_order"] = next_order
            section_order = next_order
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
    ss = st.session_state
    zoom = ss.get("cvb_zoom", 95)

    z1, z2, z3, z4 = st.columns([1, 2, 1, 1], gap="small", vertical_alignment="center")
    with z1:
        if st.button("−", key="btn_zoom_out", help="Zoom out"):
            levels = [60, 70, 75, 80, 85, 90, 95, 100, 110, 115]
            idx = levels.index(zoom) if zoom in levels else levels.index(95)
            ss["cvb_zoom"] = levels[max(0, idx - 1)]
            st.rerun()
    with z2:
        st.markdown(f"<div class='cvb-zoom-display'>{zoom}%</div>", unsafe_allow_html=True)
    with z3:
        if st.button("+", key="btn_zoom_in", help="Zoom in"):
            levels = [60, 70, 75, 80, 85, 90, 95, 100, 110, 115]
            idx = levels.index(zoom) if zoom in levels else levels.index(95)
            ss["cvb_zoom"] = levels[min(len(levels) - 1, idx + 1)]
            st.rerun()
    with z4:
        if st.button("⤢", key="btn_zoom_reset", help="Reset zoom"):
            ss["cvb_zoom"] = 95
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


# ─── CSS injection ────────────────────────────────────────────────────────────

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
  font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase;
  color: {text_muted}; margin: 0.5rem 0 0.3rem;
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
  margin: 0.65rem 0 0.2rem;
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
    page_bg = "#0b1220" if is_dark else "#f4f7fb"
    panel_bg = "#0f172a" if is_dark else "#ffffff"
    border = "#334155" if is_dark else "#dbe3ef"
    text = "#e2e8f0" if is_dark else "#1f2937"
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
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"] {{
  height: 100vh !important;
  overflow: hidden !important;
}}
[data-testid="stMainBlockContainer"],
.block-container,
section[data-testid="stMain"] .block-container {{
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
  background:#ffffff !important;
  border-top:1px solid #eef2f7 !important;
  border-bottom:1px solid #dbe3ef !important;
  border-radius:0;
  padding:0 24px !important;
  margin:0 !important;
}}
.st-key-cvb-toolbar-native > div,
.st-key-cvb-toolbar-native [data-testid="stVerticalBlock"],
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"],
.st-key-cvb-toolbar-native [data-testid="stElementContainer"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
  min-height: 56px !important;
}}
.cvb-saved-ts-native {{
  display:inline-flex;
  align-items:center;
  height:24px;
  padding:0 10px;
  border-radius:999px;
  background:#e8f3ff;
  color:#006fe6;
  font-size:12px;
  font-weight:600;
  border:1px solid #b8dcff;
  white-space:nowrap;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 22px !important;
  flex-wrap: nowrap !important;
  white-space: nowrap !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  white-space: nowrap !important;
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  width: auto !important;
  min-width: auto !important;
  max-width: none !important;
  height: 40px !important;
  padding: 0 10px !important;
  border-radius: 10px !important;
  border: none !important;
  outline: none !important;
  border: none !important;
  background: transparent !important;
  color: #64748b !important;
  box-shadow: none !important;
  font-size: 15px !important;
  font-weight: 500 !important;
  flex-direction: row !important;
  cursor: pointer !important;
  transition: background-color .16s ease, color .16s ease, box-shadow .16s ease !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:focus-visible,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:focus-visible {{
  background: #eff6ff !important;
  color: #006fe6 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_reset button:focus-visible {{
  background: #fee2e2 !important;
  color: #ef4444 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"],
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"] {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  white-space: nowrap !important;
  height: 44px !important;
  padding: 0 18px !important;
  border-radius: 8px !important;
  background:#006fe6 !important;
  border-color:#006fe6 !important;
  border: none !important;
  color:#ffffff !important;
  font-size: 15px !important;
  font-weight:600 !important;
  transition: background-color .16s ease, color .16s ease !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"]:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"]:focus-visible,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"]:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"]:focus-visible {{
  background: #005dcc !important;
  border-color: #005dcc !important;
  color: #ffffff !important;
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
  gap: 8px !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  height: 100% !important;
  min-height: 0 !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {{
  flex: 0 0 320px !important;
  width: 320px !important;
  min-width: 300px !important;
  max-width: 340px !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {{
  flex: 1 1 auto !important;
  min-width: 420px !important;
}}
.st-key-cvb-main-row-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {{
  flex: 1.06 1 auto !important;
  min-width: 460px !important;
}}
.st-key-cvb-middle-scroll-native,
.st-key-cvb-right-scroll-native {{
  background:{panel_bg};
  border:1px solid {border};
  border-radius:12px;
  padding:12px;
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}}
.st-key-cvb-left-scroll-native {{
  background:#f8fafc;
  border-right:1px solid #dbe3ef;
  border-left:none;
  border-top:none;
  border-bottom:none;
  border-radius:0;
  padding:14px 18px 14px 18px;
  height: var(--cvb-native-panel-h) !important;
  max-height: var(--cvb-native-panel-h) !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"] {{
  min-height: 0 !important;
  overflow: visible !important;
}}
.cvb-rail-heading {{
  font-size:12px;
  font-weight:700;
  letter-spacing:0.12em;
  color:#64748b;
  text-transform:uppercase;
  margin:10px 0 8px;
}}
.cvb-rail-divider {{ border-top:1px solid #dbe3ef; margin:12px 0 10px; }}

.st-key-cvb-left-scroll-native .sortable-component {{
  background: transparent !important;
  padding: 0 !important;
  margin: 0 0 2px 0 !important;
}}
.st-key-cvb-left-scroll-native .sortable-container {{
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}}
.st-key-cvb-left-scroll-native .sortable-container-header {{
  display: none !important;
}}
.st-key-cvb-left-scroll-native .sortable-container-body {{
  background: transparent !important;
}}
.st-key-cvb-left-scroll-native .sortable-item {{
  height: 44px !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 0 10px !important;
  margin-bottom: 8px !important;
  border: 1px solid #dbe3ef !important;
  border-radius: 9px !important;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
  cursor: grab !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: #1f2937 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  text-align: left !important;
}}
.st-key-cvb-left-scroll-native .sortable-item::before {{
  content: "⠿";
  color: #64748b;
  font-size: 15px;
  margin-right: 2px;
  flex: 0 0 auto;
}}
.st-key-cvb-left-scroll-native .sortable-chosen,
.st-key-cvb-left-scroll-native .sortable-drag {{
  box-shadow: 0 8px 16px rgba(2, 132, 199, 0.16) !important;
  border-color: #93c5fd !important;
}}

.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="stHorizontalBlock"] {{
  height: 44px !important;
  margin-bottom: 8px !important;
  border: 1px solid #dbe3ef !important;
  border-radius: 9px !important;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 0 8px !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:first-child .stButton button {{
  height: 42px !important;
  min-height: 42px !important;
  border: none !important;
  background: transparent !important;
  padding: 0 4px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  color: #1f2937 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:first-child .stButton button:hover {{
  background: #f8fbff !important;
  color: #0f172a !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:last-child .stButton button {{
  width: 24px !important;
  min-width: 24px !important;
  height: 24px !important;
  min-height: 24px !important;
  border: none !important;
  background: transparent !important;
  border-radius: 6px !important;
  padding: 0 !important;
  color: #64748b !important;
  font-size: 13px !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:last-child .stButton button:hover {{
  background: #eff6ff !important;
  color: #006fe6 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:last-child {{
  display:flex !important;
  justify-content:flex-end !important;
  align-items:center !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-vis_native_"]:not([class*="st-key-vis_native_inline_"]) {{
  display: none !important;
}}
/* Left-rail hard overrides to keep rows compact and single-line */
.st-key-cvb-left-scroll-native [class*="st-key-cvb_sections_sortable_native"] {{
  display: none !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="stHorizontalBlock"] {{
  flex-wrap: nowrap !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"] {{
  min-width: 0 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:first-child {{
  flex: 1 1 auto !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:first-child .stButton button p {{
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  text-align: left !important;
  line-height: 1.2 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="column"]:last-child {{
  flex: 0 0 28px !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {{
  min-width: 0 !important;
  flex: 1 1 auto !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-sec-row-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {{
  min-width: 30px !important;
  max-width: 30px !important;
  flex: 0 0 30px !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-sec_native_"] button {{
  width: 100% !important;
  min-width: 0 !important;
  height: 42px !important;
  min-height: 42px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 4px !important;
  justify-content: flex-start !important;
  text-align: left !important;
  color: #1f2937 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-sec_native_"] button p {{
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  text-align: left !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  line-height: 1.2 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-vis_native_inline_"] button {{
  width: 24px !important;
  min-width: 24px !important;
  height: 24px !important;
  min-height: 24px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 6px !important;
  padding: 0 !important;
  font-size: 13px !important;
  color: #64748b !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-vis_native_inline_"] button:hover {{
  background: #eff6ff !important;
  color: #006fe6 !important;
}}

.cvb-template-card {{
  border:1px solid #dbe3ef;
  background:#ffffff;
  border-radius:10px;
  padding:12px 14px;
  margin-bottom:8px;
}}
.st-key-cvb-left-scroll-native .stButton button[kind="secondary"] {{
  border-radius: 10px !important;
}}
.st-key-cvb-left-scroll-native .st-key-cvb-template-btn button {{
  min-height: 66px !important;
  height: 66px !important;
  padding: 10px 12px !important;
  border: 1px solid #dbe3ef !important;
  border-radius: 10px !important;
  background: #ffffff !important;
  justify-content: flex-start !important;
  text-align: left !important;
  color: #0f172a !important;
  white-space: normal !important;
  line-height: 1.2 !important;
}}
.st-key-cvb-left-scroll-native .st-key-cvb-template-btn-active button {{
  background: #e8f3ff !important;
  border-color: #93c5fd !important;
  box-shadow: inset 0 0 0 1px #60a5fa !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-"] button {{
  min-height: 66px !important;
  height: 66px !important;
  padding: 10px 12px !important;
  border: 1px solid #dbe3ef !important;
  border-radius: 10px !important;
  background: #ffffff !important;
  justify-content: flex-start !important;
  text-align: left !important;
  color: #0f172a !important;
  white-space: normal !important;
  line-height: 1.2 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-"] button p {{
  margin: 0 !important;
  text-align: left !important;
  line-height: 1.25 !important;
  font-size: 12px !important;
  color: #64748b !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-"] {{
  margin-bottom: 8px !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-"] button {{
  min-height: 72px !important;
  height: 72px !important;
  padding: 12px 14px !important;
  display: flex !important;
  align-items: flex-start !important;
  justify-content: center !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-"] button p strong {{
  display: block !important;
  margin-bottom: 4px !important;
  color: #0f172a !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-tpl_native_"] button strong {{
  display: block !important;
  margin-bottom: 4px !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
  color: #0f172a !important;
}}
.st-key-cvb-left-scroll-native [class*="st-key-cvb-template-btn-active-"] button {{
  background: #e8f3ff !important;
  border-color: #93c5fd !important;
  box-shadow: inset 0 0 0 1px #60a5fa !important;
}}
.cvb-template-card.active {{ border-color:#93c5fd; background:#e8f3ff; }}
.cvb-template-title {{ margin:0 0 4px 0; color:#0f172a; font-size:14px; font-weight:700; }}
.cvb-template-desc {{ margin:0; color:#64748b; font-size:12px; }}
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
.cvb-zoom-display {{
  border:1px solid {border};
  border-radius:999px;
  background:{panel_bg};
  color:{muted};
  padding:6px 12px;
  text-align:center;
  font-weight:600;
}}
</style>""",
        unsafe_allow_html=True,
    )


def _render_left_panel_native() -> None:
    ss = st.session_state
    section_order = _normalize_section_order(ss.get("cvb_section_order"))
    visibility = _normalize_section_visibility(ss.get("cvb_section_visibility"))
    ss["cvb_section_visibility"] = visibility

    st.markdown("<p class='cvb-rail-heading'>Sections</p>", unsafe_allow_html=True)
    drag_prefix = "\u22EE\u22EE"
    eye_open = "\U0001F441"
    eye_closed = "\U0001F6AB"
    for sec_id in section_order:
        label = SECTION_ID_TO_LABEL.get(sec_id, sec_id.title())
        is_vis = visibility.get(sec_id, True)
        with st.container(key=f"cvb-sec-row-{sec_id}"):
            col_name, col_eye = st.columns([9, 1], gap="small")
            with col_name:
                if st.button(f"{drag_prefix}  {label}", key=f"sec_native_{sec_id}", use_container_width=True):
                    ss["cvb_active_section"] = sec_id
                    st.rerun()
            with col_eye:
                if st.button(eye_open if is_vis else eye_closed, key=f"vis_native_inline_{sec_id}", help=f"Toggle {label} visibility"):
                    visibility[sec_id] = not is_vis
                    ss["cvb_section_visibility"] = visibility
                    st.rerun()
    section_order = []

    for sec_id in section_order:
        label = SECTION_ID_TO_LABEL.get(sec_id, sec_id.title())
        is_vis = visibility.get(sec_id, True)
        with st.container(key=f"cvb-sec-row-{sec_id}"):
            col_name, col_eye = st.columns([9, 1], gap="small")
            with col_name:
                if st.button(f"⠿ {label}", key=f"sec_native_{sec_id}", use_container_width=True):
                    ss["cvb_active_section"] = sec_id
                    st.rerun()
            with col_eye:
                if st.button("👁" if is_vis else "🚫", key=f"vis_native_inline_{sec_id}", help=f"Toggle {label} visibility"):
                    visibility[sec_id] = not is_vis
                    ss["cvb_section_visibility"] = visibility
                    st.rerun()

    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='cvb-rail-heading'>Templates</p>", unsafe_allow_html=True)
    current_tpl = _normalize_template(ss.get("cvb_template", "classic"))
    ss["cvb_template"] = current_tpl
    for tpl_key, tpl_label, tpl_desc in TEMPLATE_CHOICES:
        active = current_tpl == tpl_key
        tpl_btn_class = "cvb-template-btn-active" if active else "cvb-template-btn"
        with st.container(key=f"{tpl_btn_class}-{tpl_key}"):
            tpl_text = f"**{tpl_label}**\n\n{tpl_desc}"
            if st.button(tpl_text, key=f"tpl_native_{tpl_key}", use_container_width=True):
                if not active:
                    ss["cvb_template"] = tpl_key
                    st.rerun()

    st.markdown("<div class='cvb-rail-divider'></div>", unsafe_allow_html=True)
    st.markdown("<p class='cvb-rail-heading'>Style</p>", unsafe_allow_html=True)
    with st.container(key="cvb-style-section-native"):
        with st.container(key="cvb-style-native"):
            st.markdown("<div class='cvb-label cvb-style-label-accent'>Accent Color</div>", unsafe_allow_html=True)
            with st.container(key="cvb-color-dots-native"):
                row_1 = st.columns(4, gap="small")
                for i, col in enumerate(row_1):
                    color = ACCENT_COLORS[i]
                    with col:
                        if st.button(" ", key=f"acc_native_{i}", help=color):
                            ss["cvb_accent_color"] = color
                            st.rerun()
                row_2 = st.columns(4, gap="small")
                for i, color in enumerate(ACCENT_COLORS[4:], start=4):
                    with row_2[i - 4]:
                        if st.button(" ", key=f"acc_native_{i}", help=color):
                            ss["cvb_accent_color"] = color
                            st.rerun()
            font_scale = round(float(ss.get("cvb_font_size", 11)) / 11.0, 2)
            with st.container(key="cvb-style-font-native"):
                st.markdown(f"<div class='cvb-label'>Font Scale <strong>{font_scale:.1f}x</strong></div>", unsafe_allow_html=True)
                current_font_size = int(ss.get("cvb_font_size", 11))
                if current_font_size < 8 or current_font_size > 16:
                    current_font_size = 11
                selected_font_size = st.slider(
                    "Font Scale",
                    min_value=8,
                    max_value=16,
                    step=1,
                    value=current_font_size,
                    key="cvb_font_size_native_select",
                    label_visibility="collapsed",
                )
                ss["cvb_font_size"] = int(selected_font_size)
                st.markdown("<div class='cvb-style-gap'></div>", unsafe_allow_html=True)

            spacing_scale = round(float(ss.get("cvb_entry_spacing", 8)) / 8.0, 2)
            with st.container(key="cvb-style-spacing-native"):
                st.markdown(f"<div class='cvb-label'>Spacing <strong>{spacing_scale:.1f}x</strong></div>", unsafe_allow_html=True)
                current_spacing = int(ss.get("cvb_entry_spacing", 8))
                if current_spacing < 4 or current_spacing > 24:
                    current_spacing = 8
                selected_spacing = st.slider(
                    "Spacing",
                    min_value=4,
                    max_value=24,
                    step=2,
                    value=current_spacing,
                    key="cvb_spacing_native_select",
                    label_visibility="collapsed",
                )
                ss["cvb_entry_spacing"] = int(selected_spacing)
                st.markdown("<div class='cvb-style-gap'></div>", unsafe_allow_html=True)

            line_height = float(ss.get("cvb_line_height", 1.4))
            with st.container(key="cvb-style-line-native"):
                st.markdown(f"<div class='cvb-label'>Line Height <strong>{line_height:.1f}</strong></div>", unsafe_allow_html=True)
                current_line_height = round(float(ss.get("cvb_line_height", 1.4)), 1)
                if current_line_height < 1.0 or current_line_height > 2.0:
                    current_line_height = 1.4
                selected_line_height = st.slider(
                    "Line Height",
                    min_value=1.0,
                    max_value=2.0,
                    step=0.1,
                    value=current_line_height,
                    key="cvb_line_height_native_select",
                    label_visibility="collapsed",
                )
                ss["cvb_line_height"] = float(selected_line_height)
                st.markdown("<div class='cvb-style-gap'></div>", unsafe_allow_html=True)

            with st.container(key="cvb-style-toggles-native"):
                st.toggle("Show icons", key="cvb_show_icons")
                st.toggle("Show photo", key="cvb_show_photo")


def _render_middle_panel_native() -> None:
    ss = st.session_state
    active = ss.get("cvb_active_section", "personal")
    order = _normalize_section_order(ss.get("cvb_section_order"))

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
    for sid in order:
        label = SECTION_ID_TO_LABEL.get(sid, sid.title())
        with st.expander(label, expanded=(sid == active)):
            render_map[sid]()


def _render_right_panel_native(cv_data: dict, is_dark: bool) -> None:
    ss = st.session_state
    zoom = int(ss.get("cvb_zoom", 95))
    levels = [60, 70, 75, 80, 85, 90, 95, 100, 110, 115]

    z1, z2, z3, z4 = st.columns([1, 2, 1, 1], gap="small", vertical_alignment="center")
    with z1:
        if st.button("−", key="btn_zoom_out_native", use_container_width=True):
            idx = levels.index(zoom) if zoom in levels else levels.index(95)
            ss["cvb_zoom"] = levels[max(0, idx - 1)]
            st.rerun()
    with z2:
        st.markdown(f"<div class='cvb-zoom-display'>{zoom}%</div>", unsafe_allow_html=True)
    with z3:
        if st.button("+", key="btn_zoom_in_native", use_container_width=True):
            idx = levels.index(zoom) if zoom in levels else levels.index(95)
            ss["cvb_zoom"] = levels[min(len(levels) - 1, idx + 1)]
            st.rerun()
    with z4:
        if st.button("⤢", key="btn_zoom_reset_native", use_container_width=True):
            ss["cvb_zoom"] = 95
            st.rerun()

    template = _normalize_template(ss.get("cvb_template", "classic"))
    accent = ss.get("cvb_accent_color") or None
    font = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size = int(ss.get("cvb_font_size", 11))
    line_height = float(ss.get("cvb_line_height", 1.4))
    entry_spacing = int(ss.get("cvb_entry_spacing", 8))
    sec_vis = ss.get("cvb_section_visibility")
    sec_order = ss.get("cvb_section_order")

    preview_html = generate_cv_html(
        cv_data,
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
    scale = zoom / 100.0
    bg = "#0b1220" if is_dark else "#f4f7fb"
    preview_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8' />
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin:0; background:{bg}; }}
body {{ padding:16px; }}
.preview-wrap {{ display:flex; justify-content:center; }}
.resume-shell {{
  width: 794px;
  min-height: 1123px;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  zoom: {scale};
}}
</style>
</head>
<body>
  <div class='preview-wrap'><div class='resume-shell'>{preview_body}</div></div>
</body>
</html>"""

    with st.container(height=650):
        components.html(preview_doc, height=1450, scrolling=True)


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
            col_left, col_spacer, col_right = st.columns([1.4, 5.2, 2.4], vertical_alignment="center")
            with col_left:
                last_saved = ss.get("cvb_last_saved")
                saved_txt = f"Saved {last_saved}" if last_saved else "Not saved yet"
                st.markdown(f"<span class='cvb-saved-ts-native'>{saved_txt}</span>", unsafe_allow_html=True)
            with col_right:
                with st.container(key="cvb-toolbar-actions-native"):
                    a1, a2, a3, a4 = st.columns([1, 1, 1.6, 1], gap="small")
                    with a1:
                        if st.button("\u21EA Import", key="cvb_toolbar_import"):
                            ss["cvb_show_import"] = not ss.get("cvb_show_import", False)
                            st.rerun()
                    with a2:
                        st.download_button(
                            "\U0001F4BE Backup",
                            data=_get_backup_json(),
                            file_name="cv_backup.json",
                            mime="application/json",
                            key="cvb_toolbar_backup",
                        )
                    with a3:
                        if pdf_bytes:
                            st.download_button(
                                "\u2193 Download PDF",
                                data=pdf_bytes,
                                file_name=f"{cv_title.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key="cvb_toolbar_download",
                                type="primary",
                            )
                        else:
                            st.button("\u2193 Download PDF", key="cvb_toolbar_download_disabled", disabled=True)
                    with a4:
                        if st.button("\u21BB Reset", key="cvb_toolbar_reset"):
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
                left, middle, right = st.columns([0.72, 2.3, 2.45], gap="small")
                with left:
                    with st.container(key="cvb-left-scroll-native"):
                        _render_left_panel_native()
                with middle:
                    with st.container(key="cvb-middle-scroll-native"):
                        _render_middle_panel_native()
                with right:
                    with st.container(key="cvb-right-scroll-native"):
                        _render_right_panel_native(cv_data, is_dark)

    _inject_realtime_js()
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

    _inject_realtime_js()
