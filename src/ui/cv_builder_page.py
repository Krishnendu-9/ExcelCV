"""CV Builder page — 3-panel workspace (left rail · editor · preview)."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import uuid
from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.database import CV, get_db
from src.ui.cv_builder_constants import (
    A4_HEIGHT_PX,
    A4_WIDTH_PX,
    ACCENT_COLORS,
    CVB_ENTRY_SPACING_VALUES,
    CVB_LINE_HEIGHT_VALUES,
    CVB_PDF_TYPOGRAPHY_SCALE,
    CVB_PERSIST_BASE_KEYS,
    CVB_SCALE_VALUES,
    CVB_ZOOM_LEVELS,
    CVR_SECTION_ORDER,
    FONT_OPTIONS,
    LEGACY_SECTION_ORDER_V2,
    PROFICIENCY_OPTIONS,
    SECTION_ADD_BUTTON_BY_ID,
    SECTION_ICON_BY_ID,
    SECTION_ID_TO_LABEL,
    SECTION_IDS,
    TEMPLATE_CHOICES,
    TEMPLATE_CONFIGS,
)
from src.ui.cv_builder_pdf import _build_pdf_ready_html, _render_html_to_pdf_bytes
from src.ui.cv_builder_preview_data import (
    _build_preview_data_with_demo_defaults,
    _is_cv_data_effectively_empty,
    _row_has_meaningful_data,
)
from src.ui.cv_builder_value_utils import (
    _coerce_bool,
    _date_range,
    _default_zoom_for_template,
    _html_attr_escape,
    _html_escape,
    _normalize_contact_link,
    _normalize_section_order,
    _normalize_section_visibility,
    _normalize_template,
    _safe_float,
    _safe_int,
)

# ─── Constants ────────────────────────────────────────────────────────────────


try:
    _POPOVER_PARAMS = inspect.signature(st.popover).parameters
except Exception:
    _POPOVER_PARAMS = {}

_SUPPORTS_POPOVER_KEY = "key" in _POPOVER_PARAMS
_SUPPORTS_POPOVER_ON_CHANGE = "on_change" in _POPOVER_PARAMS


def _normalize_builder_tuning_state() -> None:
    ss = st.session_state
    ss["cvb_font_size"] = max(8, min(16, _safe_int(ss.get("cvb_font_size", 11), 11)))
    ss["cvb_line_height"] = max(1.0, min(2.0, _safe_float(ss.get("cvb_line_height", 1.4), 1.4)))
    ss["cvb_entry_spacing"] = max(0, min(24, _safe_int(ss.get("cvb_entry_spacing", 8), 8)))
    ss["cvb_show_icons"] = _coerce_bool(ss.get("cvb_show_icons", True), True)
    default_zoom = _default_zoom_for_template(ss.get("cvb_template"))
    ss["cvb_zoom"] = max(35, min(100, _safe_int(ss.get("cvb_zoom", default_zoom), default_zoom)))


def _clear_link_query_params() -> None:
    try:
        for qk in list(st.query_params.keys()):
            if str(qk).startswith("cvb_lurl_"):
                del st.query_params[qk]
    except Exception:
        pass


def _query_param_str(name: str) -> str | None:
    """Return a query param as a trimmed string, or None if not present."""
    try:
        params = st.query_params
    except Exception:
        return None
    try:
        raw = params.get(name, None)
    except Exception:
        return None
    if raw is None:
        return None
    if isinstance(raw, list):
        raw = raw[-1] if raw else None
    if raw is None:
        return None
    return str(raw).strip()


def _rerun_resume_builder() -> None:
    """Rerun while pinning the active route to Resume Builder."""
    st.session_state["page"] = "resume-builder"
    try:
        current = dict(st.query_params.to_dict())
        target = dict(current)
        target["page"] = "resume-builder"
        target.pop("next", None)
        if target != current:
            st.query_params.from_dict(target)
    except Exception:
        try:
            st.query_params["page"] = "resume-builder"
        except Exception:
            pass
    st.rerun()


# ─── Session-state initialisation ────────────────────────────────────────────


def _copy_state_value(value: object) -> object:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return list(value)
    return value


def _persistable_dynamic_keys(ss: dict) -> set[str]:
    keys: set[str] = set()
    for sid in SECTION_IDS:
        keys.add(f"cvb_section_open_{sid}")

    for eid in ss.get("cvb_exp_ids", []):
        keys.update(
            {
                f"cvb_exp_role_{eid}",
                f"cvb_exp_company_{eid}",
                f"cvb_exp_loc_{eid}",
                f"cvb_exp_start_{eid}",
                f"cvb_exp_end_{eid}",
                f"cvb_exp_curr_{eid}",
                f"cvb_exp_desc_{eid}",
                f"cvb_exp_visible_{eid}",
                f"cvb_exp_bcount_{eid}",
            }
        )
        bcount = max(1, _safe_int(ss.get(f"cvb_exp_bcount_{eid}", 1), 1))
        for i in range(bcount):
            keys.add(f"cvb_exp_b_{eid}_{i}")

    for eid in ss.get("cvb_edu_ids", []):
        keys.update(
            {
                f"cvb_edu_inst_{eid}",
                f"cvb_edu_degree_{eid}",
                f"cvb_edu_field_{eid}",
                f"cvb_edu_loc_{eid}",
                f"cvb_edu_start_{eid}",
                f"cvb_edu_end_{eid}",
                f"cvb_edu_curr_{eid}",
                f"cvb_edu_desc_{eid}",
                f"cvb_edu_gpa_{eid}",
                f"cvb_edu_visible_{eid}",
            }
        )

    for sid in ss.get("cvb_skill_ids", []):
        keys.update({f"cvb_skill_item_{sid}", f"cvb_skill_visible_{sid}"})

    for pid in ss.get("cvb_proj_ids", []):
        keys.update(
            {
                f"cvb_proj_name_{pid}",
                f"cvb_proj_role_{pid}",
                f"cvb_proj_desc_{pid}",
                f"cvb_proj_tech_{pid}",
                f"cvb_proj_link_{pid}",
                f"cvb_proj_link_url_{pid}",
                f"cvb_proj_start_{pid}",
                f"cvb_proj_end_{pid}",
                f"cvb_proj_visible_{pid}",
            }
        )

    for lid in ss.get("cvb_lang_ids", []):
        keys.update({f"cvb_lang_name_{lid}", f"cvb_lang_prof_{lid}", f"cvb_lang_visible_{lid}"})

    for cid in ss.get("cvb_cert_ids", []):
        keys.update(
            {
                f"cvb_cert_name_{cid}",
                f"cvb_cert_issuer_{cid}",
                f"cvb_cert_date_{cid}",
                f"cvb_cert_link_{cid}",
                f"cvb_cert_link_url_{cid}",
                f"cvb_cert_visible_{cid}",
            }
        )
    return keys


def _protect_builder_widget_state() -> None:
    """Preserve builder data even when widgets are temporarily not mounted."""
    ss = st.session_state
    mirror_key = "cvb_state_mirror_v1"
    mirror = ss.get(mirror_key, {})
    if not isinstance(mirror, dict):
        mirror = {}

    protected_keys = set(CVB_PERSIST_BASE_KEYS)
    protected_keys.update(_persistable_dynamic_keys(ss))

    for key in list(mirror.keys()):
        if key not in protected_keys:
            mirror.pop(key, None)

    for key in protected_keys:
        if key not in ss and key in mirror:
            ss[key] = _copy_state_value(mirror[key])

    for key in protected_keys:
        if key in ss:
            value = _copy_state_value(ss[key])
            # Re-assigning keeps values from being dropped during Streamlit widget cleanup.
            ss[key] = value
            mirror[key] = _copy_state_value(value)

    ss[mirror_key] = mirror


def _init_builder() -> None:
    defaults: dict = {
        "cvb_cv_title": "My Resume",
        "cvb_template": "classic",
        "cvb_loaded_cv_id": None,
        "cvb_last_saved": None,
        "cvb_show_import": False,
        "cvb_accent_color": "#2563eb",
        "cvb_font": "System Sans",
        "cvb_font_size": 11,
        "cvb_line_height": 1.4,
        "cvb_entry_spacing": 8,
        "cvb_show_icons": True,
        "cvb_zoom": 100,
        "cvb_section_order": list(SECTION_IDS),
        "cvb_section_visibility": {sid: True for sid in SECTION_IDS},
        "cvb_full_name": "",
        "cvb_prof_title": "",
        "cvb_email": "",
        "cvb_phone": "",
        "cvb_location": "",
        "cvb_website": "",
        "cvb_linkedin": "",
        "cvb_github": "",
        "cvb_website_url": "",
        "cvb_linkedin_url": "",
        "cvb_github_url": "",
        "cvb_summary": "",
        "cvb_exp_ids": [],
        "cvb_edu_ids": [],
        "cvb_proj_ids": [],
        "cvb_cert_ids": [],
        "cvb_lang_ids": [],
        "cvb_skill_ids": [],
        "cvb_interests": [],
        "cvb_interest_ctr": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v.copy() if isinstance(v, (dict, list)) else v
    st.session_state["cvb_template"] = _normalize_template(st.session_state.get("cvb_template"))
    st.session_state["cvb_section_order"] = _normalize_section_order(
        st.session_state.get("cvb_section_order")
    )
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
        current_zoom = _safe_int(st.session_state.get("cvb_zoom", 65), 65)
        if current_zoom in (45, 75, 95):
            st.session_state["cvb_zoom"] = _default_zoom_for_template(
                st.session_state.get("cvb_template", "classic")
            )
        st.session_state["cvb_zoom_default_v4_migrated"] = True
    if "cvb_zoom_default_v5_migrated" not in st.session_state:
        current_zoom = _safe_int(st.session_state.get("cvb_zoom", 100), 100)
        if current_zoom in (65, 90):
            st.session_state["cvb_zoom"] = 100
        st.session_state["cvb_zoom_default_v5_migrated"] = True
    if "cvb_exp_default_seed_v1" not in st.session_state:
        if not st.session_state.get("cvb_exp_ids"):
            eid = str(uuid.uuid4())
            st.session_state["cvb_exp_ids"] = [eid]
            st.session_state[f"cvb_exp_bcount_{eid}"] = 1
            st.session_state[f"cvb_exp_b_{eid}_0"] = ""
            st.session_state[f"cvb_exp_curr_{eid}"] = False
            st.session_state[f"cvb_exp_desc_{eid}"] = ""
            st.session_state[f"cvb_exp_visible_{eid}"] = True
        st.session_state["cvb_exp_default_seed_v1"] = True
    if "cvb_sections_open_default_v1" not in st.session_state:
        for sid in SECTION_IDS:
            st.session_state[f"cvb_section_open_{sid}"] = True
        st.session_state["cvb_sections_open_default_v1"] = True
    if "cvb_sections_open_default_v2" not in st.session_state:
        # One-time migration to clear stale collapsed states from older runs.
        for sid in SECTION_IDS:
            st.session_state[f"cvb_section_open_{sid}"] = True
        st.session_state["cvb_sections_open_default_v2"] = True
    if "cvb_sections_open_default_v3" not in st.session_state:
        # Ensure every section starts expanded for existing sessions too.
        for sid in SECTION_IDS:
            st.session_state[f"cvb_section_open_{sid}"] = True
        st.session_state["cvb_sections_open_default_v3"] = True
    if "cvb_proj_default_seed_v1" not in st.session_state:
        if not st.session_state.get("cvb_proj_ids"):
            pid = str(uuid.uuid4())
            st.session_state["cvb_proj_ids"] = [pid]
            st.session_state[f"cvb_proj_name_{pid}"] = ""
            st.session_state[f"cvb_proj_role_{pid}"] = ""
            st.session_state[f"cvb_proj_desc_{pid}"] = ""
            st.session_state[f"cvb_proj_tech_{pid}"] = ""
            st.session_state[f"cvb_proj_link_{pid}"] = ""
            st.session_state[f"cvb_proj_link_url_{pid}"] = ""
            st.session_state[f"cvb_proj_start_{pid}"] = ""
            st.session_state[f"cvb_proj_end_{pid}"] = ""
            st.session_state[f"cvb_proj_visible_{pid}"] = True
        st.session_state["cvb_proj_default_seed_v1"] = True
    if "cvb_lang_default_seed_v1" not in st.session_state:
        if not st.session_state.get("cvb_lang_ids"):
            lid = str(uuid.uuid4())
            st.session_state["cvb_lang_ids"] = [lid]
            st.session_state[f"cvb_lang_name_{lid}"] = ""
            st.session_state[f"cvb_lang_prof_{lid}"] = "Intermediate"
            st.session_state[f"cvb_lang_visible_{lid}"] = True
        st.session_state["cvb_lang_default_seed_v1"] = True
    if "cvb_cert_default_seed_v1" not in st.session_state:
        if not st.session_state.get("cvb_cert_ids"):
            cid = str(uuid.uuid4())
            st.session_state["cvb_cert_ids"] = [cid]
            st.session_state[f"cvb_cert_name_{cid}"] = ""
            st.session_state[f"cvb_cert_issuer_{cid}"] = ""
            st.session_state[f"cvb_cert_date_{cid}"] = ""
            st.session_state[f"cvb_cert_link_{cid}"] = ""
            st.session_state[f"cvb_cert_link_url_{cid}"] = ""
            st.session_state[f"cvb_cert_visible_{cid}"] = True
        st.session_state["cvb_cert_default_seed_v1"] = True
    if "cvb_item_visibility_defaults_v1" not in st.session_state:
        for eid in st.session_state.get("cvb_exp_ids", []):
            st.session_state.setdefault(f"cvb_exp_visible_{eid}", True)
        for eid in st.session_state.get("cvb_edu_ids", []):
            st.session_state.setdefault(f"cvb_edu_visible_{eid}", True)
        for sid in st.session_state.get("cvb_skill_ids", []):
            st.session_state.setdefault(f"cvb_skill_visible_{sid}", True)
        for pid in st.session_state.get("cvb_proj_ids", []):
            st.session_state.setdefault(f"cvb_proj_visible_{pid}", True)
        for lid in st.session_state.get("cvb_lang_ids", []):
            st.session_state.setdefault(f"cvb_lang_visible_{lid}", True)
        for cid in st.session_state.get("cvb_cert_ids", []):
            st.session_state.setdefault(f"cvb_cert_visible_{cid}", True)
        st.session_state["cvb_item_visibility_defaults_v1"] = True
    if "cvb_link_url_defaults_v1" not in st.session_state:
        for pid in st.session_state.get("cvb_proj_ids", []):
            st.session_state.setdefault(f"cvb_proj_link_url_{pid}", "")
        for cid in st.session_state.get("cvb_cert_ids", []):
            st.session_state.setdefault(f"cvb_cert_link_url_{cid}", "")
        st.session_state["cvb_link_url_defaults_v1"] = True
    if "cvb_edu_desc_migration_v1" not in st.session_state:
        # Older sessions used `cvb_edu_gpa_<id>` for freeform details.
        for eid in st.session_state.get("cvb_edu_ids", []):
            legacy_key = f"cvb_edu_gpa_{eid}"
            desc_key = f"cvb_edu_desc_{eid}"
            if not str(st.session_state.get(desc_key, "")).strip():
                st.session_state[desc_key] = st.session_state.get(legacy_key, "")
        st.session_state["cvb_edu_desc_migration_v1"] = True
    st.session_state["cvb_section_visibility"] = _normalize_section_visibility(
        st.session_state.get("cvb_section_visibility")
    )
    _normalize_builder_tuning_state()
    if "cvb_link_query_bootstrap_v1" not in st.session_state:
        _clear_link_query_params()
        st.session_state["cvb_link_query_bootstrap_v1"] = True
    _protect_builder_widget_state()


# ─── Data collection ──────────────────────────────────────────────────────────


def collect_cv_data() -> dict:
    ss = st.session_state
    # JS link popover persists explicit URLs into query params as a reliable
    # export-time source when Streamlit widget state lags behind live preview.
    q_linkedin = _query_param_str("cvb_lurl_linkedin")
    q_website = _query_param_str("cvb_lurl_website")
    q_github = _query_param_str("cvb_lurl_github")
    personal = {
        "full_name": ss.get("cvb_full_name", ""),
        "prof_title": ss.get("cvb_prof_title", ""),
        "email": ss.get("cvb_email", ""),
        "phone": ss.get("cvb_phone", ""),
        "location": ss.get("cvb_location", ""),
        "website": ss.get("cvb_website", ""),
        "linkedin": ss.get("cvb_linkedin", ""),
        "github": ss.get("cvb_github", ""),
        "website_url": q_website if q_website is not None else ss.get("cvb_website_url", ""),
        "linkedin_url": q_linkedin if q_linkedin is not None else ss.get("cvb_linkedin_url", ""),
        "github_url": q_github if q_github is not None else ss.get("cvb_github_url", ""),
        "summary": ss.get("cvb_summary", ""),
    }
    experience = []
    for eid in ss.get("cvb_exp_ids", []):
        if not _coerce_bool(ss.get(f"cvb_exp_visible_{eid}", True), True):
            continue
        bcount = ss.get(f"cvb_exp_bcount_{eid}", 1)
        bullets = [ss.get(f"cvb_exp_b_{eid}_{i}", "") for i in range(bcount)]
        experience.append(
            {
                "id": eid,
                "role": ss.get(f"cvb_exp_role_{eid}", ""),
                "company": ss.get(f"cvb_exp_company_{eid}", ""),
                "location": ss.get(f"cvb_exp_loc_{eid}", ""),
                "start_date": ss.get(f"cvb_exp_start_{eid}", ""),
                "end_date": ss.get(f"cvb_exp_end_{eid}", ""),
                "current": ss.get(f"cvb_exp_curr_{eid}", False),
                "description": ss.get(f"cvb_exp_desc_{eid}", ""),
                "bullets": [b for b in bullets if b.strip()],
            }
        )
    education = []
    for eid in ss.get("cvb_edu_ids", []):
        if not _coerce_bool(ss.get(f"cvb_edu_visible_{eid}", True), True):
            continue
        edu_description = str(ss.get(f"cvb_edu_desc_{eid}", ss.get(f"cvb_edu_gpa_{eid}", "")))
        education.append(
            {
                "id": eid,
                "institution": ss.get(f"cvb_edu_inst_{eid}", ""),
                "degree": ss.get(f"cvb_edu_degree_{eid}", ""),
                "field": ss.get(f"cvb_edu_field_{eid}", ""),
                "location": ss.get(f"cvb_edu_loc_{eid}", ""),
                "start_date": ss.get(f"cvb_edu_start_{eid}", ""),
                "end_date": ss.get(f"cvb_edu_end_{eid}", ""),
                "current": ss.get(f"cvb_edu_curr_{eid}", False),
                "description": edu_description,
                "gpa": edu_description,
            }
        )
    skill_items = []
    for sid in ss.get("cvb_skill_ids", []):
        if not _coerce_bool(ss.get(f"cvb_skill_visible_{sid}", True), True):
            continue
        value = ss.get(f"cvb_skill_item_{sid}", "").strip()
        if value:
            skill_items.append({"id": sid, "name": value})
    skills_cats = (
        [{"id": "primary", "name": "Skills", "items": [item["name"] for item in skill_items]}]
        if skill_items
        else []
    )
    projects = []
    for pid in ss.get("cvb_proj_ids", []):
        if not _coerce_bool(ss.get(f"cvb_proj_visible_{pid}", True), True):
            continue
        q_proj_link = _query_param_str(f"cvb_lurl_proj_{pid}")
        projects.append(
            {
                "id": pid,
                "name": ss.get(f"cvb_proj_name_{pid}", ""),
                "role": ss.get(f"cvb_proj_role_{pid}", ""),
                "description": ss.get(f"cvb_proj_desc_{pid}", ""),
                "tech_stack": [
                    t.strip() for t in ss.get(f"cvb_proj_tech_{pid}", "").split(",") if t.strip()
                ],
                "link": ss.get(f"cvb_proj_link_{pid}", ""),
                "link_url": (
                    q_proj_link
                    if q_proj_link is not None
                    else ss.get(f"cvb_proj_link_url_{pid}", "")
                ),
                "start_date": ss.get(f"cvb_proj_start_{pid}", ""),
                "end_date": ss.get(f"cvb_proj_end_{pid}", ""),
            }
        )
    certifications = []
    for cid in ss.get("cvb_cert_ids", []):
        if not _coerce_bool(ss.get(f"cvb_cert_visible_{cid}", True), True):
            continue
        q_cert_link = _query_param_str(f"cvb_lurl_cert_{cid}")
        certifications.append(
            {
                "id": cid,
                "name": ss.get(f"cvb_cert_name_{cid}", ""),
                "issuer": ss.get(f"cvb_cert_issuer_{cid}", ""),
                "date": ss.get(f"cvb_cert_date_{cid}", ""),
                "link": ss.get(f"cvb_cert_link_{cid}", ""),
                "link_url": (
                    q_cert_link
                    if q_cert_link is not None
                    else ss.get(f"cvb_cert_link_url_{cid}", "")
                ),
            }
        )
    languages = []
    for lid in ss.get("cvb_lang_ids", []):
        lang_name = str(ss.get(f"cvb_lang_name_{lid}", "") or "").strip()
        if not lang_name:
            continue
        if not _coerce_bool(ss.get(f"cvb_lang_visible_{lid}", True), True):
            continue
        languages.append(
            {
                "id": lid,
                "language": lang_name,
                "proficiency": ss.get(f"cvb_lang_prof_{lid}", "Intermediate"),
            }
        )
    return {
        "personal": personal,
        "experience": experience,
        "education": education,
        "skills": {"items": skill_items, "categories": skills_cats},
        "projects": projects,
        "certifications": certifications,
        "languages": languages,
        "interests": ss.get("cvb_interests", []),
        "customization": {
            "accent_color": ss.get("cvb_accent_color", "#2563eb"),
            "font": ss.get("cvb_font", "System Sans"),
            "font_size": ss.get("cvb_font_size", 11),
            "line_height": ss.get("cvb_line_height", 1.4),
            "entry_spacing": ss.get("cvb_entry_spacing", 8),
            "show_icons": _coerce_bool(ss.get("cvb_show_icons", True), True),
            "section_order": _normalize_section_order(ss.get("cvb_section_order")),
            "section_visibility": _normalize_section_visibility(ss.get("cvb_section_visibility")),
        },
    }


# ─── Load from DB ─────────────────────────────────────────────────────────────


def load_cv_into_builder(cv_record: CV) -> None:
    d = cv_record.data or {}
    ss = st.session_state
    _clear_link_query_params()
    ss["cvb_cv_title"] = cv_record.title
    ss["cvb_template"] = _normalize_template(cv_record.template)
    ss["cvb_loaded_cv_id"] = cv_record.id
    updated_at = getattr(cv_record, "updated_at", None)
    if updated_at:
        try:
            ss["cvb_last_saved"] = updated_at.strftime("%I:%M %p")
        except Exception:
            ss["cvb_last_saved"] = None
    else:
        ss["cvb_last_saved"] = None
    p = d.get("personal", {})
    for field in [
        "full_name",
        "prof_title",
        "email",
        "phone",
        "location",
        "website",
        "linkedin",
        "github",
        "website_url",
        "linkedin_url",
        "github_url",
        "summary",
    ]:
        ss[f"cvb_{field}"] = p.get(field, "")
    exp_ids = []
    for exp in d.get("experience", []):
        eid = exp.get("id") or str(uuid.uuid4())
        exp_ids.append(eid)
        ss[f"cvb_exp_role_{eid}"] = exp.get("role", "")
        ss[f"cvb_exp_company_{eid}"] = exp.get("company", "")
        ss[f"cvb_exp_loc_{eid}"] = exp.get("location", "")
        ss[f"cvb_exp_start_{eid}"] = exp.get("start_date", "")
        ss[f"cvb_exp_end_{eid}"] = exp.get("end_date", "")
        ss[f"cvb_exp_curr_{eid}"] = exp.get("current", False)
        ss[f"cvb_exp_desc_{eid}"] = exp.get("description", "")
        ss[f"cvb_exp_visible_{eid}"] = True
        bullets = exp.get("bullets", [""])
        ss[f"cvb_exp_bcount_{eid}"] = len(bullets) or 1
        for i, b in enumerate(bullets):
            ss[f"cvb_exp_b_{eid}_{i}"] = b
    ss["cvb_exp_ids"] = exp_ids
    edu_ids = []
    for edu in d.get("education", []):
        eid = edu.get("id") or str(uuid.uuid4())
        edu_ids.append(eid)
        ss[f"cvb_edu_inst_{eid}"] = edu.get("institution", "")
        ss[f"cvb_edu_degree_{eid}"] = edu.get("degree", "")
        ss[f"cvb_edu_field_{eid}"] = edu.get("field", "")
        ss[f"cvb_edu_loc_{eid}"] = edu.get("location", "")
        ss[f"cvb_edu_start_{eid}"] = edu.get("start_date", "")
        ss[f"cvb_edu_end_{eid}"] = edu.get("end_date", "")
        ss[f"cvb_edu_curr_{eid}"] = edu.get("current", False)
        edu_description = edu.get("description", edu.get("gpa", ""))
        ss[f"cvb_edu_desc_{eid}"] = edu_description
        ss[f"cvb_edu_gpa_{eid}"] = edu_description
        ss[f"cvb_edu_visible_{eid}"] = True
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
        ss[f"cvb_skill_visible_{sid}"] = True
    ss["cvb_skill_ids"] = skill_ids
    ss["cvb_skill_default_seed_done"] = bool(skill_ids)
    proj_ids = []
    for proj in d.get("projects", []):
        pid = proj.get("id") or str(uuid.uuid4())
        proj_ids.append(pid)
        ss[f"cvb_proj_name_{pid}"] = proj.get("name", "")
        ss[f"cvb_proj_role_{pid}"] = proj.get("role", "")
        ss[f"cvb_proj_desc_{pid}"] = proj.get("description", "")
        ss[f"cvb_proj_tech_{pid}"] = ", ".join(proj.get("tech_stack", []))
        ss[f"cvb_proj_link_{pid}"] = proj.get("link", "")
        ss[f"cvb_proj_link_url_{pid}"] = proj.get("link_url", "")
        ss[f"cvb_proj_start_{pid}"] = proj.get("start_date", "")
        ss[f"cvb_proj_end_{pid}"] = proj.get("end_date", "")
        ss[f"cvb_proj_visible_{pid}"] = True
    ss["cvb_proj_ids"] = proj_ids
    cert_ids = []
    for cert in d.get("certifications", []):
        cid = cert.get("id") or str(uuid.uuid4())
        cert_ids.append(cid)
        ss[f"cvb_cert_name_{cid}"] = cert.get("name", "")
        ss[f"cvb_cert_issuer_{cid}"] = cert.get("issuer", "")
        ss[f"cvb_cert_date_{cid}"] = cert.get("date", "")
        ss[f"cvb_cert_link_{cid}"] = cert.get("link", "")
        ss[f"cvb_cert_link_url_{cid}"] = cert.get("link_url", "")
        ss[f"cvb_cert_visible_{cid}"] = True
    ss["cvb_cert_ids"] = cert_ids
    lang_ids = []
    for lang in d.get("languages", []):
        lid = lang.get("id") or str(uuid.uuid4())
        lang_ids.append(lid)
        ss[f"cvb_lang_name_{lid}"] = lang.get("language", "")
        ss[f"cvb_lang_prof_{lid}"] = lang.get("proficiency", "Intermediate")
        ss[f"cvb_lang_visible_{lid}"] = True
    ss["cvb_lang_ids"] = lang_ids
    ss["cvb_interests"] = d.get("interests", [])
    cust = d.get("customization", {})
    ss["cvb_accent_color"] = cust.get("accent_color", ss.get("cvb_accent_color", "#3b82f6"))
    ss["cvb_font"] = cust.get("font", ss.get("cvb_font", "System Sans"))
    ss["cvb_font_size"] = _safe_int(cust.get("font_size", ss.get("cvb_font_size", 11)), 11)
    ss["cvb_line_height"] = _safe_float(
        cust.get("line_height", ss.get("cvb_line_height", 1.4)), 1.4
    )
    ss["cvb_entry_spacing"] = _safe_int(
        cust.get("entry_spacing", ss.get("cvb_entry_spacing", 8)), 8
    )
    ss["cvb_show_icons"] = _coerce_bool(
        cust.get("show_icons", ss.get("cvb_show_icons", True)), True
    )
    if isinstance(cust, dict):
        if "section_order" in cust:
            ss["cvb_section_order"] = _normalize_section_order(cust.get("section_order"))
        if "section_visibility" in cust:
            ss["cvb_section_visibility"] = _normalize_section_visibility(
                cust.get("section_visibility")
            )
    _normalize_builder_tuning_state()


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
        "%m/%Y",
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


_MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _parse_month_year(value: str | date | None) -> tuple[int | None, int | None]:
    if isinstance(value, date):
        return value.month, value.year
    raw = str(value or "").strip()
    if not raw:
        return None, None
    parts = raw.split("/")
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        month = int(parts[0])
        year = int(parts[1])
        if 1 <= month <= 12 and 1900 <= year <= 2200:
            return month, year
    parsed = _parse_date_for_input(raw)
    if parsed:
        return parsed.month, parsed.year
    return None, None


def _set_month_year_storage(storage_key: str, month: int | None, year: int | None) -> None:
    if month and year:
        st.session_state[storage_key] = f"{month:02d}/{year:04d}"
    else:
        st.session_state[storage_key] = ""


def _date_field(
    label: str,
    storage_key: str,
    disabled: bool = False,
    allow_present: bool = False,
    current_key: str | None = None,
) -> None:
    ss = st.session_state
    month_key = f"{storage_key}__month"
    year_key = f"{storage_key}__year"
    current_prev_key = f"{storage_key}__current_prev"
    popover_state_key = f"{storage_key}__popover_open"
    popover_close_request_key = f"{storage_key}__popover_close_requested"
    popover_nonce_key = f"{storage_key}__popover_nonce"
    token = abs(hash(storage_key)) % 1000000
    pop_wrap_key = f"cvb-date-popover-{token}"
    year_scroll_key = f"cvb-date-year-scroll-{token}"

    if allow_present and current_key and current_key not in ss:
        ss[current_key] = False
    if allow_present and current_key and current_prev_key not in ss:
        ss[current_prev_key] = bool(ss.get(current_key, False))

    if month_key not in ss or year_key not in ss:
        parsed_month, parsed_year = _parse_month_year(ss.get(storage_key, ""))
        ss[month_key] = parsed_month
        ss[year_key] = parsed_year

    if popover_state_key not in ss:
        ss[popover_state_key] = False
    if popover_nonce_key not in ss:
        ss[popover_nonce_key] = 0
    if ss.pop(popover_close_request_key, False):
        if _SUPPORTS_POPOVER_KEY:
            ss[popover_state_key] = False
        else:
            ss[popover_nonce_key] = int(ss.get(popover_nonce_key, 0)) + 1

    def _close_date_popover() -> None:
        ss[popover_close_request_key] = True
        _rerun_resume_builder()

    is_current = bool(ss.get(current_key, False)) if (allow_present and current_key) else False
    raw_value = str(ss.get(storage_key, "") or "").strip()
    display_value = "Present (Current)" if is_current else (raw_value if raw_value else "MM/YYYY")

    st.markdown(
        f"<div class='cvb-date-field-label'>{_html_escape(label)}</div>", unsafe_allow_html=True
    )
    if disabled:
        st.text_input(label, value=display_value, disabled=True, label_visibility="collapsed")
        return

    popover_kwargs: dict[str, object] = {"width": "stretch"}
    if _SUPPORTS_POPOVER_KEY:
        popover_kwargs["key"] = popover_state_key
    if _SUPPORTS_POPOVER_ON_CHANGE:
        popover_kwargs["on_change"] = "rerun"

    popover_host = st
    if not _SUPPORTS_POPOVER_KEY:
        # Legacy fallback: render popover in alternating host containers.
        # Moving the widget to a different host forces remount and closes any open popover.
        slot_a = st.container()
        slot_b = st.container()
        if int(ss.get(popover_nonce_key, 0)) % 2 == 0:
            popover_host = slot_a
            slot_b.empty()
        else:
            popover_host = slot_b
            slot_a.empty()

    with popover_host.popover(display_value, **popover_kwargs):
        with st.container(key=pop_wrap_key):
            if allow_present and current_key:
                was_current = bool(ss.get(current_prev_key, False))
                now_current = st.toggle("Present (Current)", key=current_key)
                ss[current_prev_key] = now_current
                if now_current:
                    ss[month_key] = None
                    ss[year_key] = None
                    _set_month_year_storage(storage_key, None, None)
                    if not was_current:
                        _close_date_popover()
                    return

            selected_month = ss.get(month_key)
            selected_year = ss.get(year_key)

            month_col, year_col = st.columns([1, 1], gap="small")
            with month_col:
                st.caption("Month")
                for r in range(4):
                    cols = st.columns(3, gap="small")
                    for c in range(3):
                        m = (r * 3) + c + 1
                        with cols[c]:
                            m_label = _MONTH_ABBR[m - 1]
                            m_type = "primary" if selected_month == m else "secondary"
                            if st.button(
                                m_label, key=f"{storage_key}__m_{m}", type=m_type, width="stretch"
                            ):
                                ss[month_key] = m
                                selected_month = m
                                _set_month_year_storage(storage_key, selected_month, selected_year)
                                if selected_month and selected_year:
                                    _close_date_popover()

            with year_col:
                st.caption("Year")
                top_year = datetime.now().year + 1
                years = [top_year - i for i in range(48)]
                with st.container(key=year_scroll_key):
                    total_rows = (len(years) + 2) // 3
                    for r in range(total_rows):
                        cols = st.columns(3, gap="small")
                        for c in range(3):
                            idx = (r * 3) + c
                            if idx >= len(years):
                                continue
                            y = years[idx]
                            with cols[c]:
                                y_type = "primary" if selected_year == y else "secondary"
                                if st.button(
                                    str(y),
                                    key=f"{storage_key}__y_{y}",
                                    type=y_type,
                                    width="stretch",
                                ):
                                    ss[year_key] = y
                                    selected_year = y
                                    _set_month_year_storage(
                                        storage_key, selected_month, selected_year
                                    )
                                    if selected_month and selected_year:
                                        _close_date_popover()

            if st.button("Clear", key=f"{storage_key}__clear"):
                if allow_present and current_key:
                    ss[current_key] = False
                    ss[current_prev_key] = False
                ss[month_key] = None
                ss[year_key] = None
                _set_month_year_storage(storage_key, None, None)
                _close_date_popover()


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
    data_json: str,
    template: str,
    accent_color: str | None,
    font_family: str | None,
    font_size: int,
    line_height: float,
    entry_spacing: int,
    show_icons: bool,
    preview_dark: bool,
    section_visibility_json: str,
    section_order_json: str,
) -> tuple[bytes | None, str]:
    try:
        cv_data = json.loads(data_json) if data_json else {}
        section_visibility = (
            json.loads(section_visibility_json) if section_visibility_json else None
        )
        section_order = json.loads(section_order_json) if section_order_json else None
        preview_source = _build_preview_source(cv_data)
        preview_html = generate_cv_html(
            preview_source,
            template,
            accent_color=accent_color,
            font_family=font_family,
            font_size=font_size,
            line_height=line_height,
            entry_spacing=entry_spacing,
            show_icons=show_icons,
            preview_dark=preview_dark,
            section_visibility=section_visibility,
            section_order=section_order,
            typography_scale=CVB_PDF_TYPOGRAPHY_SCALE,
        )
        pdf_ready_html = _build_pdf_ready_html(preview_html)
        return _render_html_to_pdf_bytes(pdf_ready_html), ""
    except Exception as exc:
        return None, str(exc)


def _pdf_request_payload(
    cv_data: dict,
    template: str,
    accent_color: str | None,
    font_family: str | None,
    font_size: int,
    line_height: float,
    entry_spacing: int,
    show_icons: bool,
    preview_dark: bool,
    section_visibility: dict[str, bool],
    section_order: list[str],
) -> tuple[str, tuple]:
    data_json = json.dumps(cv_data, sort_keys=True)
    section_visibility_json = json.dumps(section_visibility, sort_keys=True)
    section_order_json = json.dumps(section_order)
    payload = {
        "data_json": data_json,
        "template": template,
        "accent_color": accent_color,
        "font_family": font_family,
        "font_size": font_size,
        "line_height": line_height,
        "entry_spacing": entry_spacing,
        "show_icons": show_icons,
        "preview_dark": preview_dark,
        "section_visibility_json": section_visibility_json,
        "section_order_json": section_order_json,
    }
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload_hash, (
        data_json,
        template,
        accent_color,
        font_family,
        font_size,
        line_height,
        entry_spacing,
        show_icons,
        preview_dark,
        section_visibility_json,
        section_order_json,
    )


def _get_backup_json() -> str:
    data = {k: v for k, v in st.session_state.items() if k.startswith("cvb_")}
    return json.dumps(data, indent=2, default=str)


def _build_resume_pdf_filename(ss: dict) -> str:
    full_name = str(ss.get("cvb_full_name", "") or "").strip()
    cv_title = str(ss.get("cvb_cv_title", "") or "").strip()

    if full_name:
        base = f"{full_name}_CV"
    elif cv_title:
        base = cv_title
    else:
        base = "resume"

    base = re.sub(r"\s+", "_", base)
    base = re.sub(r'[<>:"/\\|?*\r\n\t]+', "_", base).strip(" ._")
    if not base:
        base = "resume"
    return f"{base}.pdf"


def _import_from_json(uploaded_file) -> None:
    try:
        payload = uploaded_file.read()
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Backup payload must be a JSON object.")
        for k in [k for k in st.session_state.keys() if str(k).startswith("cvb_")]:
            st.session_state.pop(k, None)
        _clear_link_query_params()
        for k, v in data.items():
            if k.startswith("cvb_"):
                st.session_state[k] = v
        _init_builder()
        st.session_state["cvb_show_import"] = False
        _rerun_resume_builder()
    except Exception as exc:
        st.error(f"Import failed: {exc}")


def _reset_all() -> None:
    keys = [k for k in st.session_state if k.startswith("cvb_")]
    for k in keys:
        del st.session_state[k]
    _clear_link_query_params()
    _init_builder()


def _inject_reset_popup_native_js() -> None:
    components.html(
        """<script>
(function () {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;

  function closeResetPopup() {
    try { doc.body.classList.remove('cvb-reset-open'); } catch (_e) {}
  }
  function openResetPopup() {
    try { doc.body.classList.add('cvb-reset-open'); } catch (_e) {}
  }

  closeResetPopup();

  if (!w.__excelcvResetPopupBound) {
    w.__excelcvResetPopupBound = true;

    doc.addEventListener('click', function (evt) {
      var t = evt && evt.target;
      if (!t) return;

      var openBtn = t.closest && t.closest('.cvb-reset-open-native');
      if (openBtn) {
        evt.preventDefault();
        evt.stopPropagation();
        openResetPopup();
        return;
      }

      var cancelBtn = t.closest && t.closest('.cvb-reset-cancel-native');
      if (cancelBtn) {
        evt.preventDefault();
        evt.stopPropagation();
        closeResetPopup();
        return;
      }

      if (doc.body.classList.contains('cvb-reset-open')) {
        var panel = doc.querySelector('.st-key-cvb-reset-float-native');
        if (panel && !panel.contains(t)) {
          closeResetPopup();
        }
      }
    }, true);

    w.addEventListener('keydown', function (evt) {
      if (evt && evt.key === 'Escape') closeResetPopup();
    }, true);
  }
})();
</script>""",
        height=0,
    )


# ─── Form section renderers ───────────────────────────────────────────────────


def _render_backup_button_fragment(backup_payload: str) -> None:
    st.download_button(
        "Backup",
        data=backup_payload,
        file_name="cv_backup.json",
        mime="application/json",
        key="cvb_toolbar_backup",
        on_click="ignore",
    )


def _render_save_button_fragment(template: str) -> None:
    ss = st.session_state
    if st.button("Save", key="cvb_toolbar_save"):
        cv_data = collect_cv_data()
        title = (
            ss.get("cvb_cv_title", "") or ss.get("cvb_toolbar_title_native", "") or "My Resume"
        ).strip()
        if _save_cv(cv_data, title, template):
            ss["cvb_cv_title"] = title
            ss["cvb_last_saved"] = datetime.now().strftime("%I:%M %p")
            _rerun_resume_builder()
        else:
            st.error("Save failed.")


def _inject_realtime_js() -> None:
    components.html(
        """<script>
(function() {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;
  var FIELD_BY_LABEL = {
    'Full Name': 'cvb_full_name',
    'Professional Title': 'cvb_prof_title',
    'Email': 'cvb_email',
    'Phone': 'cvb_phone',
    'Location': 'cvb_location',
    'Website': 'cvb_website',
    'LinkedIn': 'cvb_linkedin',
    'GitHub': 'cvb_github',
    'Summary': 'cvb_summary',
    'Professional Summary': 'cvb_summary'
  };
  var LINK_URL_KEYS = {
    linkedin: 'cvb_linkedin_url',
    website: 'cvb_website_url',
    github: 'cvb_github_url'
  };
  var LINK_URL_QUERY_KEYS = {
    linkedin: 'cvb_lurl_linkedin',
    website: 'cvb_lurl_website',
    github: 'cvb_lurl_github'
  };
  var FIELD_BY_KEY = {
    cvb_linkedin_url: 'cvb_linkedin_url',
    cvb_website_url: 'cvb_website_url',
    cvb_github_url: 'cvb_github_url'
  };

  function linkStateKeyForCf(cf) {
    if (LINK_URL_KEYS[cf]) return LINK_URL_KEYS[cf];
    if (String(cf || '').indexOf('proj-') === 0) return 'cvb_proj_link_url_' + String(cf).slice(5);
    if (String(cf || '').indexOf('cert-') === 0) return 'cvb_cert_link_url_' + String(cf).slice(5);
    return '';
  }

  function linkQueryKeyForCf(cf) {
    if (LINK_URL_QUERY_KEYS[cf]) return LINK_URL_QUERY_KEYS[cf];
    if (String(cf || '').indexOf('proj-') === 0) return 'cvb_lurl_proj_' + String(cf).slice(5);
    if (String(cf || '').indexOf('cert-') === 0) return 'cvb_lurl_cert_' + String(cf).slice(5);
    return '';
  }

  function getFieldValue(labelText, cardSel) {
    var card = doc.querySelector(cardSel);
    if (!card) return '';
    var labels = card.querySelectorAll('label');
    for (var i = 0; i < labels.length; i++) {
      if (labels[i].textContent.trim() !== labelText) continue;
      var t1 = labels[i].closest('[data-testid="stTextInput"]');
      if (t1) {
        var inp = t1.querySelector('input');
        return inp ? String(inp.value || '') : '';
      }
      var t2 = labels[i].closest('[data-testid="stTextArea"]');
      if (t2) {
        var ta = t2.querySelector('textarea');
        return ta ? String(ta.value || '') : '';
      }
    }
    return '';
  }

  function getWidgetKey(node) {
    function normKey(raw) {
      var key = String(raw || '').trim();
      if (!key) return '';
      if (key.indexOf('st-key-') === 0) key = key.slice(7);
      if (key.indexOf('cvb-') === 0) key = key.replace(/-/g, '_');
      return key.indexOf('cvb_') === 0 ? key : '';
    }

    var el = node;
    for (var depth = 0; el && depth < 120; depth++, el = el.parentElement) {
      if (!el) break;
      var classes = String(el.className || '').split(/\\s+/);
      for (var i = 0; i < classes.length; i++) {
        var key = normKey(classes[i]);
        if (key) return key;
      }
    }
    if (node && node.getAttribute) {
      var keyFromId = normKey(node.getAttribute('id'));
      if (keyFromId) return keyFromId;
      var keyFromName = normKey(node.getAttribute('name'));
      if (keyFromName) return keyFromName;
      var keyFromData = normKey(node.getAttribute('data-testid'));
      if (keyFromData) return keyFromData;
    }
    return '';
  }

  function getLabelText(container, input) {
    if (container) {
      var lbl = container.querySelector('label');
      if (lbl && lbl.textContent) {
        var txt = String(lbl.textContent || '').trim();
        if (txt) return txt;
      }
    }
    var aria = input && input.getAttribute ? String(input.getAttribute('aria-label') || '').trim() : '';
    if (aria) return aria;
    var ph = input && input.getAttribute ? String(input.getAttribute('placeholder') || '').trim() : '';
    if (ph) return ph;
    return '';
  }

  function broadcast(msg) {
    var iframes = doc.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
      try { iframes[i].contentWindow.postMessage(msg, '*'); } catch(e) {}
    }
  }

  function syncAllPersonalFields(cardSel) {
    var labels = [
      'Full Name', 'Professional Title', 'Email', 'Phone',
      'Location', 'LinkedIn', 'Website', 'GitHub', 'Professional Summary'
    ];
    for (var i = 0; i < labels.length; i++) {
      var l = labels[i];
      var f = FIELD_BY_LABEL[l];
      if (!f) continue;
      broadcast({ type: 'cv-rt-update', field: f, value: getFieldValue(l, cardSel) });
    }
    ['linkedin', 'website', 'github'].forEach(function(cf) {
      var urlInput = getUrlInputFromField(cf);
      if (!urlInput) return;
      var key = LINK_URL_KEYS[cf];
      if (!key) return;
      broadcast({ type: 'cv-rt-update', field: key, value: String(urlInput.value || '') });
    });
  }

  function hasAnyPersonalInput(cardSel) {
    var labels = [
      'Full Name', 'Professional Title', 'Email', 'Phone',
      'Location', 'LinkedIn', 'Website', 'GitHub', 'Professional Summary'
    ];
    for (var i = 0; i < labels.length; i++) {
      if (getFieldValue(labels[i], cardSel).trim().length > 0) return true;
    }
    var linkKinds = ['linkedin', 'website', 'github'];
    for (var j = 0; j < linkKinds.length; j++) {
      var urlInput = getUrlInputFromField(linkKinds[j]);
      if (urlInput && String(urlInput.value || '').trim().length > 0) return true;
    }
    return false;
  }

  function looksLikeExplicitUrl(cf, raw) {
    var v = String(raw || '').trim();
    if (!v) return false;
    var lower = v.toLowerCase();
    if (lower.indexOf('http://') === 0 || lower.indexOf('https://') === 0 || lower.indexOf('www.') === 0) return true;
    if (cf === 'linkedin') return lower.indexOf('linkedin.com/') >= 0;
    if (cf === 'github') return lower.indexOf('github.com/') >= 0;
    if (cf === 'website') return v.indexOf('.') >= 0;
    if (String(cf || '').indexOf('proj-') === 0 || String(cf || '').indexOf('cert-') === 0) return v.indexOf('.') >= 0;
    return false;
  }

  function getUrlInputFromField(cf) {
    var host = doc.querySelector('.st-key-cvb-link-url-' + cf);
    if (!host) return null;
    return host.querySelector('input');
  }

  function persistLinkUrlQuery(cf, nextUrl) {
    try {
      var key = linkQueryKeyForCf(cf);
      if (!key) return;
      var url = new URL(w.location.href);
      if (String(nextUrl || '').trim()) {
        url.searchParams.set(key, String(nextUrl || '').trim());
      } else {
        url.searchParams.delete(key);
      }
      w.history.replaceState({}, '', url.toString());
    } catch (_) {}
  }

  function setInputValue(input, value) {
    if (!input) return;
    var ownerWin = (input.ownerDocument && input.ownerDocument.defaultView) || w;
    try {
      var proto = ownerWin.HTMLInputElement && ownerWin.HTMLInputElement.prototype;
      var setter = proto ? Object.getOwnPropertyDescriptor(proto, 'value') : null;
      if (setter && setter.set) setter.set.call(input, value);
      else input.value = value;
    } catch (_) {
      input.value = value;
    }
    var InputEventCtor = ownerWin.Event || Event;
    input.dispatchEvent(new InputEventCtor('input', { bubbles: true }));
    input.dispatchEvent(new InputEventCtor('change', { bubbles: true }));
    try {
      input.focus();
    } catch (_) {}
    try {
      var KeyboardCtor = ownerWin.KeyboardEvent || KeyboardEvent;
      input.dispatchEvent(new KeyboardCtor('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
      input.dispatchEvent(new KeyboardCtor('keyup', { key: 'Enter', code: 'Enter', bubbles: true }));
    } catch (_) {}
    try {
      input.blur();
    } catch (_) {}
  }

  var __linkPopover = null;
  var __linkEditorState = null;

  function ensureLinkPopover() {
    if (__linkPopover && __linkPopover.parentElement) return __linkPopover;

    var stale = doc.querySelectorAll('.cvb-link-popover:not([data-cvb-link-popover="1"])');
    for (var si = 0; si < stale.length; si++) stale[si].remove();

    var existing = doc.querySelector('.cvb-link-popover[data-cvb-link-popover="1"]');
    if (existing) {
      var dups = doc.querySelectorAll('.cvb-link-popover[data-cvb-link-popover="1"]');
      for (var di = 1; di < dups.length; di++) dups[di].remove();
      __linkPopover = existing;
    } else {
      var root = doc.createElement('div');
      root.className = 'cvb-link-popover';
      root.setAttribute('data-cvb-link-popover', '1');
      root.style.display = 'none';
      root.innerHTML = ''
        + '<div class="cvb-link-popover-title">Link URL</div>'
        + '<div class="cvb-link-popover-row">'
        +   '<input class="cvb-link-popover-input" type="text" placeholder="https://example.com" />'
        +   '<button type="button" class="cvb-link-popover-save" title="Save link">&#10003;</button>'
        + '</div>';
      doc.body.appendChild(root);
      __linkPopover = root;
    }

    if (__linkPopover && !__linkPopover.__cvbBound) {
      __linkPopover.__cvbBound = true;
      __linkPopover.addEventListener('mousedown', function(ev) { ev.stopPropagation(); }, true);
      __linkPopover.addEventListener('click', function(ev) { ev.stopPropagation(); }, true);

      var inputEl = __linkPopover.querySelector('.cvb-link-popover-input');
      var saveBtn = __linkPopover.querySelector('.cvb-link-popover-save');
      if (saveBtn) {
        var commitFromBtn = function(ev) {
          if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
          }
          commitLinkPopover();
        };
        saveBtn.addEventListener('pointerdown', commitFromBtn, true);
        saveBtn.addEventListener('mousedown', commitFromBtn, true);
        saveBtn.addEventListener('click', commitFromBtn, true);
      }
      if (inputEl) {
        inputEl.addEventListener('keydown', function(ev) {
          if (ev.key === 'Enter') {
            ev.preventDefault();
            commitLinkPopover();
          } else if (ev.key === 'Escape') {
            ev.preventDefault();
            closeLinkPopover();
          }
        });
      }
    }

    return __linkPopover;
  }

  function closeLinkPopover() {
    if (!__linkPopover) return;
    __linkPopover.style.display = 'none';
    __linkPopover.classList.remove('cvb-link-popover-open');
    __linkEditorState = null;
  }

  function commitLinkPopover() {
    if (!__linkPopover || !__linkEditorState) return;
    var state = __linkEditorState;
    var inputEl = __linkPopover.querySelector('.cvb-link-popover-input');
    var nextUrl = inputEl ? String(inputEl.value || '').trim() : '';
    persistLinkUrlQuery(state.cf, nextUrl);
    closeLinkPopover();
    setInputValue(state.urlInput, nextUrl);
    w.setTimeout(function() {
      setInputValue(state.urlInput, nextUrl);
    }, 120);
    var linkKey = linkStateKeyForCf(state.cf);
    if (linkKey) {
      broadcast({ type: 'cv-rt-update', field: linkKey, value: nextUrl });
    }
    syncInlineLinkIcons();
  }

  function positionLinkPopover(anchorEl) {
    if (!__linkPopover) return;
    var anchor = anchorEl;
    if (!anchor || !anchor.isConnected) {
      if (__linkEditorState) {
        if (__linkEditorState.iconEl && __linkEditorState.iconEl.isConnected) anchor = __linkEditorState.iconEl;
        else if (__linkEditorState.displayInput && __linkEditorState.displayInput.isConnected) anchor = __linkEditorState.displayInput;
      }
    }
    if (!anchor) return;
    var rect = anchor.getBoundingClientRect();
    if ((!rect || (!rect.width && !rect.height)) && __linkEditorState && __linkEditorState.displayInput && __linkEditorState.displayInput.isConnected) {
      rect = __linkEditorState.displayInput.getBoundingClientRect();
    }
    if (!rect) return;
    var margin = 12;
    var popW = Math.min(360, Math.max(280, Math.floor(w.innerWidth - 24)));
    __linkPopover.style.width = popW + 'px';
    var left = Math.max(12, Math.min(rect.left - popW + rect.width, w.innerWidth - popW - 12));
    var top = rect.bottom + margin;
    __linkPopover.style.left = Math.round(left) + 'px';
    __linkPopover.style.top = Math.round(top) + 'px';
  }

  function openLinkEditor(cf, displayInput, iconEl) {
    var urlInput = getUrlInputFromField(cf);
    if (!urlInput) return;

    var currentUrl = String(urlInput.value || '').trim();
    var fallbackFromDisplay = looksLikeExplicitUrl(cf, displayInput ? displayInput.value : '') ? String(displayInput.value || '').trim() : '';
    var seed = currentUrl || fallbackFromDisplay;

    var pop = ensureLinkPopover();
    var inputEl = pop.querySelector('.cvb-link-popover-input');
    if (!inputEl) return;

    __linkEditorState = { cf: cf, urlInput: urlInput, displayInput: displayInput, iconEl: iconEl };
    inputEl.value = seed;
    positionLinkPopover(iconEl || displayInput);
    pop.style.display = 'block';
    pop.classList.add('cvb-link-popover-open');
    w.setTimeout(function() {
      inputEl.focus();
      inputEl.select();
    }, 0);
  }

  function attachInlineLinkIcon(cf, keySuffix) {
    var host = doc.querySelector('.st-key-' + keySuffix);
    if (!host) return;
    var wrap = host.querySelector('div[data-baseweb="input"]');
    var input = host.querySelector('input');
    if (!wrap || !input) return;
    if (!wrap.style.position) wrap.style.position = 'relative';

    var icon = wrap.querySelector('.cvb-inline-link-js');
    if (!icon) {
      icon = doc.createElement('button');
      icon.type = 'button';
      icon.className = 'cvb-inline-link cvb-inline-link-js';
      icon.setAttribute('title', 'Set link URL');
      wrap.appendChild(icon);
    }
    icon.innerHTML = '&#128279;';
    if (!icon.__cvbBound) {
      icon.__cvbBound = true;
      icon.addEventListener('click', function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        openLinkEditor(cf, input, icon);
      });
    }

    var urlInput = getUrlInputFromField(cf);
    var hasUrl = !!(urlInput && String(urlInput.value || '').trim());
    icon.classList.toggle('cvb-inline-link-active', hasUrl);
  }

  function syncInlineLinkIcons() {
    attachInlineLinkIcon('linkedin', 'cvb-link-field-linkedin');
    attachInlineLinkIcon('website', 'cvb-link-field-website');
    attachInlineLinkIcon('github', 'cvb-link-field-github');

    var projectHosts = doc.querySelectorAll('[class*="st-key-cvb-link-field-proj-"]');
    for (var i = 0; i < projectHosts.length; i++) {
      var classes = String(projectHosts[i].className || '').split(/\\s+/);
      for (var ci = 0; ci < classes.length; ci++) {
        var cls = classes[ci];
        if (!cls || cls.indexOf('st-key-cvb-link-field-proj-') !== 0) continue;
        var keySuffix = cls.slice(7);
        var cf = keySuffix.replace('cvb-link-field-', '');
        attachInlineLinkIcon(cf, keySuffix);
      }
    }

    var certHosts = doc.querySelectorAll('[class*="st-key-cvb-link-field-cert-"]');
    for (var j = 0; j < certHosts.length; j++) {
      var classes2 = String(certHosts[j].className || '').split(/\\s+/);
      for (var cj = 0; cj < classes2.length; cj++) {
        var cls2 = classes2[cj];
        if (!cls2 || cls2.indexOf('st-key-cvb-link-field-cert-') !== 0) continue;
        var keySuffix2 = cls2.slice(7);
        var cf2 = keySuffix2.replace('cvb-link-field-', '');
        attachInlineLinkIcon(cf2, keySuffix2);
      }
    }
  }

  function setupLinkPopoverDismiss() {
    var KEY = '__cvb_link_popover_dismiss__';
    if (doc[KEY]) return;
    var handler = function(ev) {
      if (!__linkPopover || __linkPopover.style.display === 'none') return;
      var t = ev.target;
      if (t && (__linkPopover.contains(t) || t.closest('.cvb-inline-link'))) return;
      closeLinkPopover();
    };
    doc.addEventListener('mousedown', handler, true);
    doc.addEventListener('touchstart', handler, true);
    doc.addEventListener('keydown', function(ev) {
      if (ev.key === 'Escape') closeLinkPopover();
    }, true);
    w.addEventListener('resize', function() {
      if (!__linkPopover || __linkPopover.style.display === 'none') return;
      if (__linkEditorState && (__linkEditorState.iconEl || __linkEditorState.displayInput)) {
        positionLinkPopover(__linkEditorState.iconEl || __linkEditorState.displayInput);
      }
    });
    doc[KEY] = 1;
  }

  function hasAnyMiddleInputValue(middleEl) {
    if (!middleEl) return false;
    var nodes = middleEl.querySelectorAll('input, textarea, select');
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n) continue;
      var t = String(n.type || '').toLowerCase();
      if (t === 'hidden' || t === 'button' || t === 'submit' || t === 'reset') continue;
      if (String(n.value || '').trim().length > 0) return true;
    }
    return false;
  }

  function broadcastAllMiddleFields() {
    var middle = doc.querySelector('.st-key-cvb-middle-scroll-native');
    if (!middle) return;
    var nodes = middle.querySelectorAll('input, textarea, select');
    for (var i = 0; i < nodes.length; i++) {
      var input = nodes[i];
      if (!input) continue;
      var t = String(input.type || '').toLowerCase();
      if (t === 'hidden' || t === 'button' || t === 'submit' || t === 'reset') continue;
      var c = input.closest('[data-testid="stTextInput"], [data-testid="stTextArea"], [data-testid="stSelectbox"], [data-testid="stNumberInput"]')
        || input.closest('[class*="st-key-"]');
      var lt = getLabelText(c || null, input);
      var widgetKey = getWidgetKey(c || input) || getWidgetKey(input) || '';
      if (!lt && widgetKey) lt = widgetKey;

      if (widgetKey) {
        var vWidget = String(input.value || '');
        broadcast({ type: 'cv-rt-widget', key: widgetKey, label: lt || widgetKey, value: vWidget });
      }

      var field = FIELD_BY_LABEL[lt] || FIELD_BY_KEY[widgetKey];
      if (field) {
        var vField = String(input.value || '');
        broadcast({ type: 'cv-rt-update', field: field, value: vField });
      }
    }
  }

  function handleInput(e) {
    var input = e.target;
    if (!input) return;
    syncInlineLinkIcons();
    var tag = input.tagName;
    if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT') return;
    var middle = doc.querySelector('.st-key-cvb-middle-scroll-native');
    if (!middle || !middle.contains(input)) return;
    var CARD = '.st-key-cvb-middle-scroll-native';
    var c = input.closest('[data-testid="stTextInput"], [data-testid="stTextArea"], [data-testid="stSelectbox"], [data-testid="stNumberInput"]')
      || input.closest('[class*="st-key-"]');
    var lt = getLabelText(c || null, input);
    var widgetKey = getWidgetKey(c || input) || getWidgetKey(input) || '';
    if (!lt && widgetKey) lt = widgetKey;
    if (!lt && !widgetKey) {
      syncAllPersonalFields(CARD);
      return;
    }
    // Enter user-mode once we have a resolvable source field, so the first
    // keystroke switches to user-only formatting immediately.
    broadcast({ type: 'cv-rt-user-mode' });
    var field = FIELD_BY_LABEL[lt] || FIELD_BY_KEY[widgetKey];
    if (widgetKey) {
      var widgetVal = String(input.value || '');
      broadcast({ type: 'cv-rt-widget', key: widgetKey, label: lt, value: widgetVal });
    }
    if (field) {
      var fieldVal = String(input.value || '');
      broadcast({ type: 'cv-rt-update', field: field, value: fieldVal });
    }
    syncAllPersonalFields(CARD);
    scheduleFullRealtimeSync();
  }

  function handleClick(e) {
    var t = e.target;
    if (!t) return;
    var middle = doc.querySelector('.st-key-cvb-middle-scroll-native');
    if (!middle || !middle.contains(t)) return;
    if (!t.closest('button, [role="button"]')) return;
    // Non-input button clicks should not force user-mode; doing so can clear
    // the preview before a usable field payload is emitted.
    syncInlineLinkIcons();
    scheduleFullRealtimeSync();
  }

  var __rtFullSyncTimer = null;
  function scheduleFullRealtimeSync() {
    if (__rtFullSyncTimer) clearTimeout(__rtFullSyncTimer);
    __rtFullSyncTimer = setTimeout(function() {
      broadcastAllMiddleFields();
      __rtFullSyncTimer = null;
    }, 40);
  }

  var KEY_INPUT = '__excalcv_rt_input__';
  var KEY_CLICK = '__excalcv_rt_click__';
  if (doc[KEY_INPUT]) {
    doc.removeEventListener('input', doc[KEY_INPUT], true);
    doc.removeEventListener('change', doc[KEY_INPUT], true);
  }
  if (doc[KEY_CLICK]) doc.removeEventListener('click', doc[KEY_CLICK], true);
  doc[KEY_INPUT] = handleInput;
  doc[KEY_CLICK] = handleClick;
  doc.addEventListener('input', handleInput, true);
  doc.addEventListener('change', handleInput, true);
  doc.addEventListener('click', handleClick, true);

  function bootstrapSync() {
    var CARD = '.st-key-cvb-middle-scroll-native';
    var middle = doc.querySelector(CARD);
    if (!middle) return;
    if (!hasAnyMiddleInputValue(middle) && !hasAnyPersonalInput(CARD)) return;
    syncAllPersonalFields(CARD);
    broadcastAllMiddleFields();
  }

  [80, 220, 420, 900, 1500, 2500].forEach(function(ms) {
    setTimeout(bootstrapSync, ms);
    setTimeout(syncInlineLinkIcons, ms);
  });
  setupLinkPopoverDismiss();
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
    components.html(
        """<script>
(function() {
  var w = window.parent && window.parent !== window ? window.parent : window;
  var doc = w.document;

  function findBtn(classFragment) {
    var root = doc.querySelector('.st-key-cvb-hidden-buttons');
    if (root) {
      var scoped = root.querySelector('[class*="' + classFragment + '"] button');
      if (scoped) return scoped;
    }
    return doc.querySelector('[class*="' + classFragment + '"] button') || null;
  }

  function postToPreview(msg) {
    var iframes = doc.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
      try { iframes[i].contentWindow.postMessage(msg, '*'); } catch(e) {}
    }
  }

  function clickWithInputCommit(btn) {
    if (!btn) return;
    try {
      var ae = doc.activeElement;
      if (ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) {
        try { ae.dispatchEvent(new Event('input', { bubbles: true })); } catch(e) {}
        try { ae.dispatchEvent(new Event('change', { bubbles: true })); } catch(e) {}
        try { ae.blur(); } catch(e) {}
      }
    } catch(e) {}
    setTimeout(function() {
      try { btn.click(); } catch(e) {}
    }, 40);
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
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-drag-end') {
      var movedId = String(ev.data.movedId || '');
      var newPos  = Number(ev.data.newPos);
      if (!movedId) return;
      if (!Number.isFinite(newPos) || newPos < 0) return;
      var btn = findBtn('st-key-cvb_pos_' + movedId + '_' + newPos);
      if (!btn) btn = findBtn('st-key-cvb-pos-' + movedId.replace(/_/g,'-') + '-' + newPos);
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-tpl-select') {
      var tpl = String(ev.data.tpl || '');
      if (!tpl) return;
      var btn = findBtn('st-key-cvb_tpl_' + tpl);
      if (!btn) btn = findBtn('st-key-cvb-tpl-' + tpl);
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-acc-select') {
      var idx = String(ev.data.idx || '0');
      var btn = findBtn('st-key-cvb_acc_' + idx);
      if (!btn) btn = findBtn('st-key-cvb-acc-' + idx);
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-scale-select') {
      var val = String(ev.data.val || '100');
      var btn = findBtn('st-key-cvb_scale_' + val);
      if (!btn) btn = findBtn('st-key-cvb-scale-' + val);
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-icons-toggle') {
      postToPreview({ type: 'cv-rt-icons-toggle', on: !!ev.data.on });
      var btn = findBtn('st-key-cvb_icons_toggle');
      if (!btn) btn = findBtn('st-key-cvb-icons-toggle');
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-lh-select') {
      var val = String(ev.data.val || '14');
      var btn = findBtn('st-key-cvb_lh_' + val);
      if (!btn) btn = findBtn('st-key-cvb-lh-' + val);
      clickWithInputCommit(btn);
    }

    if (ev.data.type === 'cvb-es-select') {
      var val = String(ev.data.val || '8');
      var btn = findBtn('st-key-cvb_es_' + val);
      if (!btn) btn = findBtn('st-key-cvb-es-' + val);
      clickWithInputCommit(btn);
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
      clickWithInputCommit(btn);
    }

  };

  w.addEventListener('message', w[KEY]);
})();
</script>""",
        height=0,
    )


def _inject_middle_section_exact_css(is_dark: bool = False) -> None:
    """Final high-specificity middle-panel card overrides for CVReviewer parity."""
    st.markdown(
        """
<style>
.st-key-cvb-middle-scroll-native .st-key-cvb-section-personal,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-summary,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-experience,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-education,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-skills,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-projects,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-languages,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-certifications,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-interests {
  border: 1px solid #d3dce8 !important;
  border-radius: 14px !important;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
  overflow: hidden !important;
  margin: 0 0 12px !important;
}
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-personal,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-summary,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-experience,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-education,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-skills,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-projects,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-languages,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-certifications,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-interests {
  background: #f7f9fc !important;
  border-bottom: 1px solid #e2e8f0 !important;
  padding: 12px 16px !important;
  min-height: 64.8px !important;
  box-sizing: border-box !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-header-"] [data-testid="stHorizontalBlock"] {
  min-height: 100% !important;
  align-items: center !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-header-"] .stMarkdown p {
  margin: 0 !important;
  color: #0f172a !important;
  font-size: 15px !important;
  font-weight: 700 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-header-"] .stMarkdown [data-testid="stIconMaterial"] {
  color: #0b63ce !important;
}

.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
  min-height: 24px !important;
  height: 24px !important;
  max-height: 24px !important;
  border-radius: 999px !important;
  padding: 4px 10px !important;
  border: none !important;
  background: rgba(0,89,179,0.10) !important;
  color: #0059b3 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  box-shadow: inset 0 0 0 1px rgba(0,89,179,0.20) !important;
  cursor: pointer !important;
  white-space: nowrap !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button:hover {
  background: rgba(0,89,179,0.15) !important;
  box-shadow: inset 0 0 0 1px rgba(0,89,179,0.20) !important;
  color: #0059b3 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button [data-testid="stIconMaterial"] {
  font-size: 14px !important;
  line-height: 1 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button > div,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button p,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button span,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button > div,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button p,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button span {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button p,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button p {
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 4px !important;
}

.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] > div,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stElementContainer"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] > div,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stElementContainer"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 24px !important;
  min-width: 24px !important;
  max-width: 24px !important;
  height: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  padding: 4px !important;
  border-radius: 8px !important;
  border: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  color: #94a3b8 !important;
  cursor: pointer !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] button:hover {
  background: rgba(37, 99, 235, 0.14) !important;
  border: 0 !important;
  color: #bfdbfe !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] button [data-testid="stIconMaterial"] {
  font-size: 16px !important;
  line-height: 1 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Final force-override for header action buttons:
   Streamlit can emit either underscore or hyphen key classes and nested wrappers.
   This block neutralizes any remaining default button tile/skin. */
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] button,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
  height: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  border-radius: 999px !important;
  padding: 4px 10px !important;
  background: rgba(0,89,179,0.10) !important;
  box-shadow: inset 0 0 0 1px rgba(0,89,179,0.20) !important;
  color: #0059b3 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  cursor: pointer !important;
}
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button:hover,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] button:hover,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] [data-testid="stButton"] > button:hover {
  background: rgba(0,89,179,0.15) !important;
  box-shadow: inset 0 0 0 1px rgba(0,89,179,0.20) !important;
  color: #0059b3 !important;
}
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button *,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] button *,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button *,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] [data-testid="stButton"] > button * {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: #0059b3 !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button [data-testid="stIconMaterial"],
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-add-"] button [data-testid="stIconMaterial"] {
  font-size: 14px !important;
  line-height: 1 !important;
}

.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-content-"] {
  background: #ffffff !important;
  padding: 14px 18px 18px !important;
}
.st-key-cvb-middle-scroll-native .st-key-cvb-section-content-summary textarea {
  min-height: 94px !important;
}
.cvb-summary-counter {
  text-align: right;
  color: #7a889b;
  font-size: 14px;
  line-height: 1.2;
  margin-top: 6px;
}
.cvb-date-field-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  line-height: 1.25;
  /* top: 22px so the date label sits at the same vertical position as
     Streamlit's text_input labels in the sibling row above. Streamlit's
     auto-generated emotion-cache wrapper around stMarkdown applies a
     negative margin-bottom (≈-16px) — we add extra top margin here to
     compensate and push the date row down so it lines up visually with
     the natural sibling spacing of plain text_input rows. */
  margin: 22px 0 11px;
  padding-left: 1px;
  display: block;
}
.st-key-cvb-middle-scroll-native [data-testid="stPopover"] {
  display: block !important;
  margin: 0 !important;
}
.st-key-cvb-middle-scroll-native [data-testid="stPopover"] > button {
  display: flex !important;
  width: 100% !important;
  min-height: 42px !important;
  height: 42px !important;
  justify-content: flex-start !important;
  border: 1px solid #dbe4ee !important;
  border-radius: 10px !important;
  background: #fbfcfe !important;
  color: #0f172a !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 0 12px !important;
  box-shadow: none !important;
}
.st-key-cvb-middle-scroll-native [data-testid="stPopover"] > button:hover {
  border-color: #c9d7e8 !important;
  background: #ffffff !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] {
  min-width: 472px !important;
  max-width: 472px !important;
  width: 472px !important;
  border-radius: 14px !important;
  padding: 12px !important;
  box-sizing: border-box !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] > [data-testid="stVerticalBlock"] {
  gap: 10px !important;
  row-gap: 10px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stHorizontalBlock"] {
  align-items: start !important;
  column-gap: 8px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
  min-width: 184px !important;
  max-width: 184px !important;
  flex: 0 0 184px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
  min-width: 236px !important;
  max-width: 236px !important;
  flex: 0 0 236px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stButton"] > button {
  min-height: 36px !important;
  height: 36px !important;
  padding: 0 9px !important;
  border-radius: 12px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  font-variant-numeric: tabular-nums !important;
  font-feature-settings: "tnum" 1 !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stButton"] > button p,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stButton"] > button span {
  margin: 0 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="__y_"] [data-testid="stButton"] > button {
  width: 100% !important;
  min-width: 0 !important;
  max-width: none !important;
  min-height: 36px !important;
  height: 36px !important;
  max-height: 36px !important;
  padding: 0 8px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
  letter-spacing: 0 !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="__y_"] [data-testid="stButton"] > button *,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="__y_"] [data-testid="stButton"] > button p,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="__y_"] [data-testid="stButton"] > button span,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="__y_"] [data-testid="stButton"] > button div {
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
  display: inline !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"] {
  max-height: 200px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-right: 8px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"] [data-testid="stVerticalBlock"] {
  max-height: none !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-right: 2px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"]::-webkit-scrollbar,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"] [data-testid="stVerticalBlock"]::-webkit-scrollbar {
  width: 6px !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"]::-webkit-scrollbar-thumb,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"] [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
  background: #c9d7e8 !important;
  border-radius: 999px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-date-start-"] [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-date-end-"] [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-edu-date-start-"] [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-edu-date-end-"] [data-testid="stVerticalBlock"] {
  gap: 4px !important;
  row-gap: 4px !important;
}
/* Date rows (Work Experience / Education) — the outer cvb-*-date-row wrapper
   was removed in Python so the start/end columns render as direct siblings
   of the Job Title / Institution rows. The date label inside each column
   carries explicit margin-top via .cvb-date-field-label so it sits at the
   same vertical baseline as Streamlit's text_input labels in sibling rows.

   ROOT CAUSE FOUND VIA DEVTOOLS: Streamlit auto-generates a wrapper div
   (class="st-emotion-cache-<hash>") inside stMarkdown that ships with
   `margin: 0 0 -16px` — a negative bottom margin that pulls the popover
   button up toward the label, AND collapses with the label's margin-top
   to swallow the breathing space above the row. We override that wrapper
   with high specificity. The selector chain reaches (0,5,0) so it beats
   Streamlit's default rule for the emotion-cache class. */
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stElementContainer"]:has(.cvb-date-field-label) [data-testid="stMarkdown"],
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stElementContainer"]:has(.cvb-date-field-label) [data-testid="stMarkdown"] > div,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stMarkdown"]:has(.cvb-date-field-label),
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stMarkdown"]:has(.cvb-date-field-label) > div,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stMarkdown"]:has(.cvb-date-field-label) > [class*="st-emotion-cache-"] {
  margin: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

.st-key-cvb-middle-scroll-native [class*="st-key-cvb-personal-inner-card"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-summary-inner-card"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-edu-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-skill-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-proj-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-lang-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-cert-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-int-item-"] {
  border: 1px solid #d3deec !important;
  border-radius: 12px !important;
  background: #ffffff !important;
  padding: 12px 14px 14px !important;
  margin: 8px 0 8px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-summary-inner-card"] {
  margin-top: 2px !important;
}
/* Skills rows should be a single-line input row (no extra outer card box). */
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-skill-item-"] {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 10px 0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-skill-item-"] [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  gap: 10px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-skill-item-"] div[data-baseweb="input"] {
  border-radius: 12px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  height: 28px !important;
  min-height: 28px !important;
  max-height: 28px !important;
  width: auto !important;
  min-width: auto !important;
  padding: 6px !important;
  border-radius: 6px !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: #475569 !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  cursor: pointer !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] [data-testid="stButton"] > button:hover {
  background: rgba(0,89,179,0.14) !important;
  color: #0059b3 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-dup_exp_"] [data-testid="stButton"] > button * {
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: inherit !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 28px !important;
  min-width: 28px !important;
  max-width: 28px !important;
  height: 28px !important;
  min-height: 28px !important;
  max-height: 28px !important;
  padding: 0 !important;
  border-radius: 6px !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: #65758b !important;
  cursor: pointer !important;
  transition: background-color .12s ease, color .12s ease !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] [data-testid="stButton"]:hover > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"]:hover [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button:focus-visible {
  background: rgba(239, 68, 68, 0.18) !important;
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.26) !important;
  color: #ef4444 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"] > button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] [data-testid="stButton"] > button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"] > button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] [data-testid="stButton"] > button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"] > button *,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] [data-testid="stButton"] > button * {
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: inherit !important;
  margin: 0 !important;
  padding: 0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button [data-testid="stIconMaterial"] {
  color: #475569 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] [data-testid="stButton"]:hover > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"]:hover [data-testid="stButton"] > button [data-testid="stIconMaterial"] {
  color: #ef4444 !important;
}
/* Match Work Experience delete style for project/language/certification card deletes too. */
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 28px !important;
  min-width: 28px !important;
  max-width: 28px !important;
  height: 28px !important;
  min-height: 28px !important;
  max-height: 28px !important;
  padding: 0 !important;
  border-radius: 6px !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: #65758b !important;
  cursor: pointer !important;
  transition: background-color .12s ease, color .12s ease !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-testid="stButton"] > button:hover {
  background: rgba(239, 68, 68, 0.18) !important;
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.26) !important;
  color: #ef4444 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button [data-testid="stIconMaterial"] {
  color: #475569 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button:hover [data-testid="stIconMaterial"] {
  color: #ef4444 !important;
}
/* Row visibility eye buttons (hide from preview without deleting data). */
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 28px !important;
  min-width: 28px !important;
  max-width: 28px !important;
  height: 28px !important;
  min-height: 28px !important;
  max-height: 28px !important;
  padding: 0 !important;
  border-radius: 6px !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
  color: #65758b !important;
  cursor: pointer !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] [data-testid="stButton"] > button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] [data-testid="stButton"] > button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] [data-testid="stButton"] > button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] [data-testid="stButton"] > button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] [data-testid="stButton"] > button:focus-visible,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] [data-testid="stButton"] > button:focus-visible {
  background: rgba(250, 204, 21, 0.18) !important;
  border: 0 !important;
  color: #fde047 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] [data-testid="stButton"] > button:hover *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_exp_"] [data-testid="stButton"] > button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_edu_"] [data-testid="stButton"] > button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_skill_"] [data-testid="stButton"] > button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_proj_"] [data-testid="stButton"] > button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_lang_"] [data-testid="stButton"] > button:focus-visible *,
.st-key-cvb-middle-scroll-native [class*="st-key-vis_cert_"] [data-testid="stButton"] > button:focus-visible * {
  color: #fde047 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] [data-testid="stButton"] > button {
  all: unset !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 28px !important;
  min-width: 28px !important;
  max-width: 28px !important;
  height: 28px !important;
  min-height: 28px !important;
  max-height: 28px !important;
  padding: 0 !important;
  border-radius: 7px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: #7c8ba1 !important;
  cursor: pointer !important;
  transition: background-color .12s ease, color .12s ease !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] [data-testid="stButton"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] [data-testid="stButton"] {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 28px !important;
  min-width: 28px !important;
  max-width: 28px !important;
  align-self: center !important;
  margin-top: 1px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] [data-testid="stButton"] > button:hover {
  background: rgba(239, 68, 68, 0.18) !important;
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.26) !important;
  color: #ef4444 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] button [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] button [data-testid="stIconMaterial"] {
  font-size: 16px !important;
  line-height: 1 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem_bullet_"] [data-testid="stButton"] > button:hover [data-testid="stIconMaterial"],
.st-key-cvb-middle-scroll-native [class*="st-key-rem-bullet-"] [data-testid="stButton"] > button:hover [data-testid="stIconMaterial"] {
  color: #ef4444 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-actions-"] [data-testid="stHorizontalBlock"] {
  justify-content: flex-end !important;
  align-items: center !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-item-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([class*="st-key-rem_bullet_"]),
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-item-"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([class*="st-key-rem-bullet-"]) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button {
  display: inline-flex !important;
  align-items: center !important;
  gap: 4px !important;
  border: none !important;
  background: transparent !important;
  color: #0059b3 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  min-height: 16px !important;
  height: 16px !important;
  padding: 0 !important;
  justify-content: flex-start !important;
  box-shadow: none !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button::before {
  content: "+" !important;
  margin-right: 2px !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button:hover {
  color: rgba(0,89,179,0.80) !important;
  background: transparent !important;
}

.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] button {
  display: inline-flex !important;
  align-items: center !important;
  gap: 4px !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  color: #0059b3 !important;
  height: 16px !important;
  min-height: 16px !important;
  padding: 0 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  justify-content: flex-start !important;
}
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button *,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] button * {
  color: #0059b3 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
}
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button:hover,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] button:hover {
  background: transparent !important;
  color: rgba(0,89,179,0.80) !important;
}

/* Final CV Builder delete-button override:
   keep icon buttons transparent in all wrapper variants; only show red on hover/focus. */
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem-exp-"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem-edu-"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem-skill-"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-testid="stButton"] > button,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-baseweb="button"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-baseweb="button"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-baseweb="button"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-baseweb="button"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-baseweb="button"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-baseweb="button"] {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: 0 !important;
  box-shadow: none !important;
  filter: none !important;
  color: #64748b !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-baseweb="button"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button * {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  color: inherit !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-baseweb="button"]:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] [data-baseweb="button"]:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] [data-baseweb="button"]:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] [data-baseweb="button"]:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] [data-baseweb="button"]:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] [data-baseweb="button"]:focus-visible,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] [data-baseweb="button"]:focus-visible {
  background: rgba(239, 68, 68, 0.14) !important;
  border-color: rgba(239, 68, 68, 0.78) !important;
  color: #dc2626 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )
    if is_dark:
        st.markdown(
            """
<style>
.st-key-cvb-middle-scroll-native .st-key-cvb-section-personal,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-summary,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-experience,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-education,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-skills,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-projects,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-languages,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-certifications,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-interests {
  background: #0f172a !important;
  border-color: #334155 !important;
  box-shadow: 0 1px 2px rgba(2, 6, 23, 0.45) !important;
}
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-personal,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-summary,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-experience,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-education,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-skills,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-projects,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-languages,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-certifications,
.st-key-cvb-middle-scroll-native .st-key-cvb-section-header-interests {
  background: #111827 !important;
  border-bottom-color: #334155 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-header-"] .stMarkdown p {
  color: #e2e8f0 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-header-"] .stMarkdown [data-testid="stIconMaterial"] {
  color: #60a5fa !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-content-"] {
  background: #0f172a !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-personal-inner-card"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-summary-inner-card"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-exp-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-edu-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-proj-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-lang-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-cert-item-"],
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-int-item-"] {
  background: #111827 !important;
  border-color: #334155 !important;
}
.st-key-cvb-middle-scroll-native .cvb-summary-counter,
.st-key-cvb-middle-scroll-native .cvb-date-field-label {
  color: #94a3b8 !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"],
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"],
.st-key-cvb-middle-scroll-native div[data-baseweb="select"] > div,
.st-key-cvb-middle-scroll-native [data-testid="stPopover"] > button {
  background: #111827 !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea,
.st-key-cvb-middle-scroll-native div[data-baseweb="select"] span {
  color: #e2e8f0 !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] > div,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] > div {
  background: transparent !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input::placeholder,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea::placeholder {
  color: #94a3b8 !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"]:hover,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"]:hover,
.st-key-cvb-middle-scroll-native div[data-baseweb="select"] > div:hover {
  background: #111827 !important;
  border-color: #475569 !important;
  box-shadow: none !important;
}
.st-key-cvb-middle-scroll-native div[data-baseweb="input"]:focus-within,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"]:focus-within,
.st-key-cvb-middle-scroll-native [data-testid="stPopover"] > button:hover {
  background: #0b1220 !important;
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.22) !important;
}
.st-key-cvb-middle-scroll-native .stTextInput label,
.st-key-cvb-middle-scroll-native .stTextArea label,
.st-key-cvb-middle-scroll-native .stSelectbox label,
.st-key-cvb-middle-scroll-native .stDateInput label {
  color: #cbd5e1 !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] {
  background: #0f172a !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 14px 30px rgba(2, 6, 23, 0.55) !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] .stCaption,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] .stCaption span {
  color: #cbd5e1 !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stButton"] > button {
  background: #111827 !important;
  border: 1px solid #475569 !important;
  color: #e2e8f0 !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [data-testid="stButton"] > button:hover {
  background: #1e293b !important;
  border-color: #60a5fa !important;
}
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"]::-webkit-scrollbar-thumb,
[data-baseweb="popover"] [class*="st-key-cvb-date-popover-"] [class*="st-key-cvb-date-year-scroll-"] [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
  background: #475569 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_add_"] [data-testid="stButton"] > button {
  background: rgba(37, 99, 235, 0.18) !important;
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.45) !important;
  color: #93c5fd !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"] > button,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] > button {
  background: transparent !important;
  border: 0 !important;
  color: #94a3b8 !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-section-chevron-"] [data-testid="stButton"] > button:hover,
.st-key-cvb-middle-scroll-native [class*="st-key-cvb_section_toggle_"] [data-testid="stButton"] > button:hover {
  background: rgba(37, 99, 235, 0.16) !important;
  border: 0 !important;
  color: #bfdbfe !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [class*="st-key-add_b_"] [data-testid="stButton"] > button {
  color: #93c5fd !important;
}
.st-key-cvb-middle-scroll-native [class*="st-key-rem_exp_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_edu_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_skill_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_proj_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_lang_"] button,
.st-key-cvb-middle-scroll-native [class*="st-key-rem_cert_"] button {
  color: #94a3b8 !important;
}

</style>
            """,
            unsafe_allow_html=True,
        )


def _inject_builder_final_alignment_overrides() -> None:
    """Last-pass CSS overrides to defeat global theme alignment defaults."""
    st.markdown(
        """
<style>
[data-testid="stAppViewContainer"]:has(.st-key-cvb-page-native),
[data-testid="stAppViewContainer"]:has(.st-key-cvb-page-native) > section.main,
[data-testid="stMain"]:has(.st-key-cvb-page-native) {
  width: 100vw !important;
  max-width: 100vw !important;
  overflow: hidden !important;
  scrollbar-gutter: unset !important;
  padding-right: 0 !important;
  margin-right: 0 !important;
}
html:has(.st-key-cvb-page-native),
body:has(.st-key-cvb-page-native) {
  overflow-y: hidden !important;
  scrollbar-gutter: unset !important;
}
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native),
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native) .block-container {
  width: 100vw !important;
  max-width: 100vw !important;
  padding-right: 0 !important;
  margin-right: 0 !important;
  scrollbar-gutter: unset !important;
  overflow: hidden !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stVerticalBlock"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stElementContainer"] {
  margin: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  min-height: 56px !important;
  height: 56px !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] {
  align-self: stretch !important;
  display: flex !important;
  align-items: center !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"] {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stButton"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stDownloadButton"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-toolbar-native [data-testid="stTextInput"] {
  margin: 0 !important;
  padding: 0 !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native > div,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native > [data-testid="stVerticalBlock"],
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-main-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
  margin-top: 0 !important;
  padding-top: 0 !important;
}
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .st-key-cvb-left-scroll-native .cvb-rail-heading,
[data-testid="stAppViewContainer"] .st-key-cvb-page-native .cvb-rail-heading {
  margin-top: 0 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


# ─── CSS injection ────────────────────────────────────────────────────────────


def _inject_builder_css_native(is_dark: bool) -> None:
    page_bg = "#0b1220" if is_dark else "#f3f5f8"
    border = "#334155" if is_dark else "#d3dce8"
    toolbar_input_bg = "#1e293b" if is_dark else "#ffffff"
    toolbar_input_brd = "#475569" if is_dark else "#d7e1ec"
    toolbar_input_text = "#e2e8f0" if is_dark else "#0f172a"
    saved_bg = "rgba(37,99,235,0.15)" if is_dark else "rgba(0, 89, 179, 0.10)"
    saved_color = "#93c5fd" if is_dark else "#0059B3"
    saved_brd = "rgba(37,99,235,0.30)" if is_dark else "rgba(0, 89, 179, 0.22)"
    toolbar_btn_color = "#94a3b8" if is_dark else "#65758B"
    rail_heading_color = "#94a3b8" if is_dark else "#65758b"
    rail_body_text = "#cbd5e1" if is_dark else "#334155"
    rail_divider = "#334155" if is_dark else "#dbe3ef"
    scroll_thumb = "#475569" if is_dark else "#8d97a5"
    scroll_thumb_hover = "#64748b" if is_dark else "#748193"
    left_slider_border = "#0f172a" if is_dark else "#ffffff"
    preview_tools_bg = "#0f172a" if is_dark else "#f6f7f9"
    style_label = "#94a3b8" if is_dark else "#475569"
    style_value = "#93c5fd" if is_dark else "#0b5cb8"
    toolbar_hover_bg = "rgba(148,163,184,0.14)" if is_dark else "#eff4fa"
    toolbar_hover_color = "#bfdbfe" if is_dark else "#0d5ec0"
    toolbar_save_hover_bg = "rgba(16,185,129,0.18)" if is_dark else "#ebf8f1"
    toolbar_save_hover_color = "#6ee7b7" if is_dark else "#0f8a4c"
    # Segmented control surrounding Import / Backup / Save
    segment_bg = "#1e293b" if is_dark else "#ffffff"
    segment_brd = "#475569" if is_dark else "#d7e1ec"
    segment_divider = "#334155" if is_dark else "#e4ebf3"
    segment_shadow = "0 1px 2px rgba(0,0,0,0.35)" if is_dark else "0 1px 2px rgba(15,23,42,0.04)"
    # Reset (destructive) button
    reset_color = "#cbd5e1" if is_dark else "#64748b"
    reset_hover_bg = "rgba(239,68,68,0.14)" if is_dark else "#fef2f2"
    reset_hover_color = "#fca5a5" if is_dark else "#dc2626"
    reset_hover_brd = "rgba(239,68,68,0.45)" if is_dark else "#fecaca"
    middle_panel_bg = "#0f172a" if is_dark else "#f3f5f8"
    right_panel_bg = "#0b1220" if is_dark else "#f6f7f9"
    left_panel_bg = "#0f172a" if is_dark else "#f7f9fc"
    scroll_track = "#111827" if is_dark else "#e6ebf2"
    expander_card_bg = "#0f172a" if is_dark else "#ffffff"
    expander_content_bg = "#0f172a" if is_dark else "#ffffff"
    expander_border = "#334155" if is_dark else "#d3dce8"
    card_shadow = (
        "0 1px 2px rgba(2, 6, 23, 0.45)" if is_dark else "0 1px 2px rgba(15, 23, 42, 0.05)"
    )
    field_bg = "#111827" if is_dark else "rgba(243,245,247,0.75)"
    field_border = "#475569" if is_dark else "#d1dae6"
    field_text = "#e2e8f0" if is_dark else "#0f172a"
    field_focus_bg = "#0b1220" if is_dark else "#ffffff"
    field_focus_border = "#60a5fa" if is_dark else "#0b63ce"
    field_focus_ring = (
        "0 0 0 3px rgba(59,130,246,0.22)" if is_dark else "0 0 0 3px rgba(11,99,206,0.14)"
    )
    label_color = "#cbd5e1" if is_dark else "#64748b"
    accent_ring_inner = "#0f172a" if is_dark else "#ffffff"
    cur_accent = st.session_state.get("cvb_accent_color", ACCENT_COLORS[0])
    native_dot_parts: list[str] = []
    for i, color in enumerate(ACCENT_COLORS):
        ring = (
            f"box-shadow:0 0 0 2px {accent_ring_inner},0 0 0 4px {color} !important;"
            if color == cur_accent
            else ""
        )
        native_dot_parts.append(
            f'.st-key-cvb-color-dots-native [class*="st-key-acc_native_{i}"] button '
            f"{{ background:{color} !important; {ring} }}"
        )
    native_dot_css = "\n".join(native_dot_parts)
    st.markdown(
        f"""<style>
.site-footer-band {{ display:none !important; }}
body:has(.st-key-cvb-page-native) {{
  height: 100vh !important;
  height: 100dvh !important;
  overflow: hidden !important;
  overflow-y: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
}}
[data-testid="stAppViewContainer"]:has(.st-key-cvb-page-native),
[data-testid="stAppViewContainer"]:has(.st-key-cvb-page-native) > .main,
[data-testid="stApp"]:has(.st-key-cvb-page-native),
section[data-testid="stMain"]:has(.st-key-cvb-page-native) {{
  height: 100vh !important;
  height: 100dvh !important;
  max-height: 100vh !important;
  max-height: 100dvh !important;
  width: 100vw !important;
  max-width: 100vw !important;
  scrollbar-gutter: unset !important;
  overflow: hidden !important;
  padding-right: 0 !important;
  margin-right: 0 !important;
}}
.st-key-cvb-page-native {{
  height: calc(100vh - var(--excelcv-fixed-header-space, 78px)) !important;
  height: calc(100dvh - var(--excelcv-fixed-header-space, 78px)) !important;
  max-height: calc(100vh - var(--excelcv-fixed-header-space, 78px)) !important;
  max-height: calc(100dvh - var(--excelcv-fixed-header-space, 78px)) !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 0 !important;
  row-gap: 0 !important;
  column-gap: 0 !important;
  overflow: hidden !important;
  background: {page_bg} !important;
  margin: 0 !important;
  padding: 0 !important;
  --cvb-workspace-h: calc(100vh - var(--excelcv-fixed-header-space, 78px) - 56px);
  --cvb-workspace-h: calc(100dvh - var(--excelcv-fixed-header-space, 78px) - 56px);
}}
.st-key-cvb-page-native > [data-testid="stLayoutWrapper"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-page-native > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] {{
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
  row-gap: 0 !important;
}}
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] {{
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
  row-gap: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  height: 100% !important;
}}
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > div,
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > div > [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
  min-height: 0 !important;
}}
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:empty,
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > div:empty,
.st-key-cvb-page-native > [data-testid="stVerticalBlock"] > div > [data-testid="stElementContainer"]:empty {{
  display: none !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-toolbar-native) {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-main-native) {{
  margin: 0 !important;
  padding: 0 !important;
  flex: 1 1 auto !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
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
  height: 100dvh !important;
  overflow: hidden !important;
}}
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native),
[data-testid="stMainBlockContainer"]:has(.st-key-cvb-page-native) .block-container,
section[data-testid="stMain"]:has(.st-key-cvb-page-native) .block-container {{
  height: 100vh !important;
  height: 100dvh !important;
  max-height: 100vh !important;
  max-height: 100dvh !important;
  width: 100vw !important;
  max-width: 100vw !important;
  padding-right: 0 !important;
  margin-right: 0 !important;
  scrollbar-gutter: unset !important;
  min-height: 0 !important;
  overflow: hidden !important;
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
  background: transparent !important;
  border-top: 0 !important;
  border-bottom: 0 !important;
  border-radius: 0;
  padding: 0 20px !important;
  margin: 0 !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-reset-float-native) {{
  margin: 0 !important;
  padding: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  overflow: visible !important;
}}
.st-key-cvb-reset-float-native {{
  display: none !important;
  pointer-events: none !important;
  position: fixed !important;
  top: calc(var(--excelcv-fixed-header-space, 78px) + 12px) !important;
  right: 16px !important;
  width: min(520px, calc(100vw - 24px)) !important;
  z-index: 1250 !important;
  border: 1px solid #f5c2c7 !important;
  border-radius: 12px !important;
  background: #fff7f7 !important;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.16) !important;
  padding: 18px 20px 16px !important;
}}
body.cvb-reset-open .st-key-cvb-reset-float-native {{
  display: block !important;
  pointer-events: auto !important;
}}
.st-key-cvb-reset-float-native > [data-testid="stVerticalBlock"] {{
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 14px !important;
}}
.st-key-cvb-reset-float-actions {{
  margin: 0 !important;
  display: block !important;
  clear: both !important;
}}
.st-key-cvb-reset-float-actions [data-testid="stHorizontalBlock"] {{
  gap: 8px !important;
  align-items: center !important;
  justify-content: center !important;
}}
.st-key-cvb-reset-float-actions [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}}
.st-key-cvb-reset-float-actions [data-testid="stButton"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-reset-float-native .cvb-reset-float-title {{
  margin: 0 0 8px 0 !important;
  color: #9f1239 !important;
  font-size: 14px !important;
  font-weight: 700 !important;
}}
.st-key-cvb-reset-float-native .cvb-reset-float-msg {{
  margin: 0 !important;
  padding: 0 8px !important;
  color: #6b2138 !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  text-align: center !important;
  display: block !important;
  margin-bottom: 2px !important;
}}
/* Match My CVs confirm-button behavior (transparent base, red/green hover), small size. */
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button,
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button:focus,
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] [data-baseweb="button"] {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  border-radius: 8px !important;
  width: auto !important;
  min-width: 96px !important;
  min-height: 36px !important;
  height: 36px !important;
  padding: 0 12px !important;
  font-weight: 600 !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button *,
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button p {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button {{
  color: #ef4444 !important;
  border: 1px solid rgba(239, 68, 68, 0.45) !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button * {{
  color: #ef4444 !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-reset-float-native [class*="st-key-btn_confirm_reset_native"][class*="st-key-btn_confirm_reset_native"] button:hover {{
  background: rgba(239, 68, 68, 0.12) !important;
  background-color: rgba(239, 68, 68, 0.12) !important;
  border-color: rgba(239, 68, 68, 0.65) !important;
}}
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native {{
  appearance: none !important;
  border: 1px solid transparent !important;
  background: transparent !important;
  color: {reset_color} !important;
  border-radius: 8px !important;
  min-height: 36px !important;
  height: 36px !important;
  padding: 0 12px !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  transition: background-color .16s ease, color .16s ease, border-color .16s ease !important;
}}
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native::before {{
  content: "";
  display: inline-block;
  width: 14px;
  height: 14px;
  background-color: currentColor;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-position: center;
  -webkit-mask-size: 14px 14px;
  mask-repeat: no-repeat;
  mask-position: center;
  mask-size: 14px 14px;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M3 12a9 9 0 1 0 3-6.7L3 8'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M3 3v5h5'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M3 12a9 9 0 1 0 3-6.7L3 8'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M3 3v5h5'/%3E%3C/svg%3E");
}}
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native:hover,
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native:focus-visible {{
  background: {reset_hover_bg} !important;
  border-color: {reset_hover_brd} !important;
  color: {reset_hover_color} !important;
}}
.st-key-cvb-reset-float-native .cvb-reset-cancel-native {{
  appearance: none !important;
  border: 1px solid #d1d5db !important;
  background: transparent !important;
  color: #334155 !important;
  border-radius: 8px !important;
  min-height: 36px !important;
  height: 36px !important;
  padding: 0 12px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
}}
.st-key-cvb-reset-float-native .cvb-reset-cancel-native:hover,
.st-key-cvb-reset-float-native .cvb-reset-cancel-native:focus-visible {{
  background: rgba(34, 197, 94, 0.12) !important;
  border-color: rgba(34, 197, 94, 0.55) !important;
  color: #15803d !important;
}}
@media (max-width: 760px) {{
  .st-key-cvb-reset-float-native {{
    left: 12px !important;
    right: 12px !important;
    width: auto !important;
  }}
}}

.st-key-cvb-toolbar-native > [data-testid="stLayoutWrapper"],
.st-key-cvb-toolbar-native > [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-toolbar-native > div,
.st-key-cvb-toolbar-native [data-testid="stVerticalBlock"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}}
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] {{
  height: 100% !important;
  align-items: center !important;
}}
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
}}
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stElementContainer"],
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"] {{
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
}}
.st-key-cvb-toolbar-native [data-testid="stMarkdownContainer"] p,
.st-key-cvb-toolbar-native p {{
  margin: 0 !important;
}}
.cvb-saved-ts-native {{
  display:inline-flex;
  align-items:center;
  gap: 6px;
  min-height: 26px;
  padding: 3px 12px;
  border-radius:999px;
  background: {saved_bg};
  color:{saved_color};
  font-size:12px;
  font-weight:500;
  line-height: 1;
  border:1px solid {saved_brd};
  white-space:nowrap;
  margin-left: auto !important;
}}
.cvb-saved-ts-native::before {{
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: {saved_color};
  box-shadow: 0 0 0 2px {saved_bg};
  flex-shrink: 0;
}}
/* Title input width is now controlled in the inline meta group below */
.st-key-cvb_toolbar_title_native {{
  min-width: 260px !important;
  max-width: 280px !important;
  width: 280px !important;
  flex: 0 0 auto !important;
}}
.st-key-cvb_toolbar_title_native label {{
  display: none !important;
}}
.st-key-cvb_toolbar_title_native [data-baseweb="input"] {{
  border-radius: 8px !important;
  border: 1px solid {toolbar_input_brd} !important;
  background: {toolbar_input_bg} !important;
  min-height: 38px !important;
}}
.st-key-cvb_toolbar_title_native input {{
  font-size: 13px !important;
  font-weight: 500 !important;
  color: {toolbar_input_text} !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 0 !important;
  flex-wrap: nowrap !important;
  white-space: nowrap !important;
}}
/* Spacing between the segment (cols 1-3), Download PDF (col 4), and Reset (col 5) */
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {{
  margin-left: 14px !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5) {{
  margin-left: 8px !important;
}}
.st-key-cvb-toolbar-actions-native {{
  display: block !important;
  width: 100% !important;
  margin-left: 0 !important;
}}
.st-key-cvb-toolbar-actions-native > div,
.st-key-cvb-toolbar-actions-native [data-testid="stVerticalBlock"],
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  width: 100% !important;
  margin-left: 0 !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="column"] {{
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: fit-content !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stButton"] > button,
.st-key-cvb-toolbar-actions-native [data-testid="stDownloadButton"] > button,
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native {{
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  padding: 0 12px !important;
  line-height: 1 !important;
  margin: 0 !important;
  border-radius: 8px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  white-space: nowrap !important;
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: none !important;
  height: 36px !important;
  padding: 0 14px !important;
  outline: none !important;
  background: {segment_bg} !important;
  color: {toolbar_btn_color} !important;
  box-shadow: none !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  flex-direction: row !important;
  cursor: pointer !important;
  transition: background-color .16s ease, color .16s ease, box-shadow .16s ease !important;
  position: relative !important;
}}
/* Segment: shared border, dividers between, rounded only on outer corners */
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button {{
  border: 1px solid {segment_brd} !important;
  border-right: 1px solid {segment_divider} !important;
  border-radius: 8px 0 0 8px !important;
  box-shadow: {segment_shadow} !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button {{
  border-top: 1px solid {segment_brd} !important;
  border-bottom: 1px solid {segment_brd} !important;
  border-left: 0 !important;
  border-right: 1px solid {segment_divider} !important;
  border-radius: 0 !important;
  box-shadow: {segment_shadow} !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button {{
  border: 1px solid {segment_brd} !important;
  border-left: 0 !important;
  border-radius: 0 8px 8px 0 !important;
  box-shadow: {segment_shadow} !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button::before,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button::before,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button::before {{
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
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button::before {{
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 21H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M17 21v-8H7v8'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M7 3v5h8'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23000' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 21H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M17 21v-8H7v8'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M7 3v5h8'/%3E%3C/svg%3E") !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_import button:focus-visible,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_backup button:focus-visible {{
  background: {toolbar_hover_bg} !important;
  color: {toolbar_hover_color} !important;
  z-index: 2 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button:hover,
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_save button:focus-visible {{
  background: {toolbar_save_hover_bg} !important;
  color: {toolbar_save_hover_color} !important;
  z-index: 2 !important;
}}
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[kind="primary"],
.st-key-cvb-toolbar-actions-native .st-key-cvb_toolbar_download button[data-testid="baseButton-primary"] {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  white-space: nowrap !important;
  height: 36px !important;
  width: 138px !important;
  min-width: 138px !important;
  max-width: 138px !important;
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
  height: var(--cvb-workspace-h) !important;
  max-height: var(--cvb-workspace-h) !important;
  flex: 1 1 auto !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
  margin: 0 !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
.st-key-cvb-main-native > div,
.st-key-cvb-main-native > [data-testid="stVerticalBlock"],
.st-key-cvb-main-native > [data-testid="stVerticalBlock"] > div,
.st-key-cvb-main-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
  row-gap: 0 !important;
}}
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"],
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"],
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] {{
  height: var(--cvb-workspace-h) !important;
  max-height: var(--cvb-workspace-h) !important;
  min-height: 0 !important;
  align-items: stretch !important;
  gap: 0 !important;
  column-gap: 0 !important;
  row-gap: 0 !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"],
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"],
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  height: 100% !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1),
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1),
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {{
  flex: 0 0 256px !important;
  width: 256px !important;
  min-width: 256px !important;
  max-width: 256px !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2),
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2),
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {{
  flex: 9 1 0 !important;
  width: auto !important;
  max-width: none !important;
  min-width: 0 !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3),
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3),
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {{
  flex: 7 1 0 !important;
  width: auto !important;
  max-width: none !important;
  min-width: 0 !important;
}}
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stElementContainer"],
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-main-native > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"],
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stElementContainer"],
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-main-native > div > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"],
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stElementContainer"],
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
.st-key-cvb-main-native [data-testid="stElementContainer"]:has(> [data-testid="stHorizontalBlock"]) > [data-testid="stHorizontalBlock"] > [data-testid="column"] [data-testid="stVerticalBlock"] {{
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
}}
.st-key-cvb-middle-scroll-native {{
  background:{middle_panel_bg};
  border:none;
  border-radius:0;
  padding:0 0 8px 8px !important;
  margin:0 !important;
  height: var(--cvb-workspace-h) !important;
  max-height: var(--cvb-workspace-h) !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  scrollbar-width: thin !important;
  scrollbar-color: {scroll_thumb} {scroll_track} !important;
}}
.st-key-cvb-right-scroll-native {{
  background:{right_panel_bg};
  border-left:1px solid {border};
  border-top:none;
  border-right:none;
  border-bottom:none;
  border-radius:0;
  padding:0 0 8px 0 !important;
  margin:0 !important;
  height: var(--cvb-workspace-h) !important;
  max-height: var(--cvb-workspace-h) !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  position: relative !important;
  scrollbar-gutter: unset !important;
  scrollbar-width: thin !important;
  scrollbar-color: {scroll_thumb} {scroll_track} !important;
  box-sizing: border-box !important;
}}
.st-key-cvb-left-scroll-native {{
  background:{left_panel_bg};
  border-right:1px solid {border};
  border-left:none;
  border-top:none;
  border-bottom:none;
  border-radius:0;
  padding:0 0 16px 16px !important;
  margin:0 !important;
  height: var(--cvb-workspace-h) !important;
  max-height: var(--cvb-workspace-h) !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  scrollbar-gutter: auto !important;
  scrollbar-width: thin !important;
  scrollbar-color: {scroll_thumb} {scroll_track} !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading {{
  font-size: 12px !important;
  font-weight: 600 !important;
  font-family: Poppins, Montserrat, system-ui, sans-serif !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: {rail_heading_color} !important;
  margin: 0 0 16px 0 !important;
  padding: 0 !important;
  line-height: 1.45 !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
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
  color: {rail_heading_color} !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading-icon svg {{
  width: 14px !important;
  height: 14px !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"],
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"],
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"] {{
  min-height: 0 !important;
  height: 100% !important;
  max-height: 100% !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
  row-gap: 0 !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stLayoutWrapper"],
.st-key-cvb-middle-scroll-native > [data-testid="stLayoutWrapper"],
.st-key-cvb-right-scroll-native > [data-testid="stLayoutWrapper"],
.st-key-cvb-left-scroll-native > [data-testid="stElementContainer"],
.st-key-cvb-middle-scroll-native > [data-testid="stElementContainer"],
.st-key-cvb-right-scroll-native > [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"] {{
  padding-right: 8px !important;
}}
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"] {{
  padding-right: 8px !important;
}}
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"] {{
  padding-left: 8px !important;
  padding-right: 0 !important;
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
  background: {scroll_track} !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar-thumb,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar-thumb,
.st-key-cvb-right-scroll-native::-webkit-scrollbar-thumb {{
  background: {scroll_thumb} !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native::-webkit-scrollbar-thumb:hover,
.st-key-cvb-middle-scroll-native::-webkit-scrollbar-thumb:hover,
.st-key-cvb-right-scroll-native::-webkit-scrollbar-thumb:hover {{
  background: {scroll_thumb_hover} !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar,
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar {{
  width: 6px !important;
  height: 6px !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track,
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track,
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-track {{
  background: {scroll_track} !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb,
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb,
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{
  background: {scroll_thumb} !important;
  border-radius: 8px !important;
}}
.st-key-cvb-left-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover,
.st-key-cvb-middle-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover,
.st-key-cvb-right-scroll-native > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover {{
  background: {scroll_thumb_hover} !important;
}}
/* Custom section cards replaced st.expander; chevron is rendered as a plain
   st.button so no DOM hiding is needed. */

/* ─── Custom section card (CVReviewer-style: icon+label LEFT, chevron RIGHT) ─── */
/* Outer card */
.st-key-cvb-section-personal,
.st-key-cvb-section-summary,
.st-key-cvb-section-experience,
.st-key-cvb-section-education,
.st-key-cvb-section-skills,
.st-key-cvb-section-projects,
.st-key-cvb-section-languages,
.st-key-cvb-section-certifications,
.st-key-cvb-section-interests {{
  background: {expander_card_bg} !important;
  border: 1px solid {expander_border} !important;
  border-radius: 14px !important;
  margin: 0 0 12px !important;
  overflow: hidden !important;
  box-shadow: {card_shadow} !important;
}}
/* Header/add/chevron styling is centralized in _inject_middle_section_exact_css().
   Keeping only one source of truth prevents size drift and cross-rule conflicts. */
/* Content area — white, with consistent padding */
[class*="st-key-cvb-section-content-"] {{
  background: {expander_content_bg} !important;
  padding: 14px 18px 18px !important;
  margin: 0 !important;
}}

.st-key-cvb-middle-scroll-native [data-testid="InputInstructions"],
.st-key-cvb-middle-scroll-native [data-testid="stTextInputInstructions"],
.st-key-cvb-middle-scroll-native [data-testid="stTextAreaInstructions"] {{
  display: none !important;
}}
/* Input / textarea / select — wrapper gets the visible border & background */
.st-key-cvb-middle-scroll-native div[data-baseweb="input"],
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"],
.st-key-cvb-middle-scroll-native div[data-baseweb="select"] > div {{
  border: 1.5px solid {field_border} !important;
  background: {field_bg} !important;
  border-radius: 8px !important;
  min-height: 42px !important;
  transition: border-color .15s ease, box-shadow .15s ease, background .15s ease !important;
  box-shadow: none !important;
}}
/* Inner input/textarea element — transparent so wrapper shows through */
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea {{
  background: transparent !important;
  border: none !important;
  outline: none !important;
  color: {field_text} !important;
  caret-color: {field_focus_border} !important;
  -webkit-text-fill-color: {field_text} !important;
  font-size: 14px !important;
  padding: 8px 12px !important;
}}
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea {{
  min-height: 86px !important;
}}
/* Focus: blue border + soft glow on wrapper, white background */
.st-key-cvb-middle-scroll-native div[data-baseweb="input"]:focus-within,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"]:focus-within {{
  border-color: {field_focus_border} !important;
  box-shadow: {field_focus_ring} !important;
  background: {field_focus_bg} !important;
}}
/* Placeholder */
.st-key-cvb-middle-scroll-native div[data-baseweb="input"] input::placeholder,
.st-key-cvb-middle-scroll-native div[data-baseweb="textarea"] textarea::placeholder {{
  color: #94a3b8 !important;
  opacity: 1 !important;
}}
/* Field labels */
.st-key-cvb-middle-scroll-native .stTextInput label,
.st-key-cvb-middle-scroll-native .stTextArea label,
.st-key-cvb-middle-scroll-native .stSelectbox label,
.st-key-cvb-middle-scroll-native .stDateInput label {{
  font-size: 13px !important;
  font-weight: 500 !important;
  color: {label_color} !important;
  margin-bottom: 3px !important;
}}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-link-field-"] {{
  position: relative;
}}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-link-field-"] input {{
  padding-right: 42px !important;
}}
.st-key-cvb-middle-scroll-native [class*="st-key-cvb-link-url-"] {{
  position: absolute !important;
  left: -10000px !important;
  top: auto !important;
  width: 1px !important;
  height: 1px !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}}
.st-key-cvb-middle-scroll-native .cvb-inline-link {{
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid {field_border};
  background: {field_bg};
  color: {field_text} !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none !important;
  font-size: 14px;
  line-height: 1;
  z-index: 3;
  cursor: pointer;
}}
.st-key-cvb-middle-scroll-native .cvb-inline-link:hover {{
  border-color: {field_focus_border};
  background: {field_focus_bg};
  box-shadow: {field_focus_ring};
}}
.st-key-cvb-middle-scroll-native .cvb-inline-link.cvb-inline-link-active {{
  border-color: {field_focus_border};
  color: {field_focus_border} !important;
}}
.cvb-link-popover {{
  position: fixed;
  z-index: 10020;
  width: min(360px, calc(100vw - 24px));
  max-width: calc(100vw - 24px);
  padding: 14px;
  border-radius: 14px;
  border: 1px solid {field_border};
  background: {expander_card_bg};
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.34);
}}
.cvb-link-popover-title {{
  font-size: 13px;
  font-weight: 700;
  color: {label_color};
  margin-bottom: 9px;
}}
.cvb-link-popover-row {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.cvb-link-popover-input {{
  flex: 1;
  height: 42px;
  border-radius: 10px;
  border: 1px solid {field_border};
  background: {field_bg};
  color: {field_text};
  font-size: 14px;
  padding: 0 12px;
  outline: none;
}}
.cvb-link-popover-input:focus {{
  border-color: {field_focus_border};
  box-shadow: {field_focus_ring};
}}
.cvb-link-popover-save {{
  width: 42px;
  height: 42px;
  border-radius: 10px;
  border: 1px solid {field_focus_border};
  background: {field_focus_bg};
  color: {field_focus_border};
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
  cursor: pointer;
}}
.cvb-link-popover-save:hover {{
  filter: brightness(1.03);
}}
.st-key-cvb-middle-scroll-native .stButton button,
.st-key-cvb-middle-scroll-native .stDownloadButton button {{
  height: 42px !important;
  min-height: 42px !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}}
/* Header/add/chevron styling is defined only in _inject_middle_section_exact_css(). */
.cvb-rail-heading {{
  font-size:12px;
  font-weight:600;
  font-family:Poppins,Montserrat,system-ui,sans-serif;
  letter-spacing:0.08em;
  color:{rail_heading_color};
  text-transform:uppercase;
  margin:6px 0 16px;
  padding:0;
  display:flex;
  align-items:center;
  gap:10px;
  line-height:1.45;
  position:relative;
  z-index:2;
  clear:both;
}}
.cvb-rail-divider {{
  border-top:1px solid {rail_divider};
  margin:16px 0 16px;
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

.cvb-style-label, .cvb-label {{ font-size:14px; color:{rail_body_text}; margin:10px 0 4px; font-weight:500; }}
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
  color: {style_label} !important;
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
  color: {style_label} !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  clear: both !important;
}}
.st-key-cvb-style-native .cvb-label strong {{
  color: {style_value} !important;
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
  border: 2px solid {left_slider_border} !important;
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
  color: {rail_body_text} !important;
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
  margin: 0 !important;
  padding: 0 !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 8 !important;
  background: {preview_tools_bg} !important;
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

/* Final layout overrides (keep last): toolbar vertical centering + remove seam gap */
.st-key-cvb-toolbar-native,
.st-key-cvb-toolbar-native > div,
.st-key-cvb-toolbar-native [data-testid="stVerticalBlock"],
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"],
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"],
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
.st-key-cvb-toolbar-native [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  align-items: center !important;
}}
.st-key-cvb-toolbar-native [data-testid="stButton"],
.st-key-cvb-toolbar-native [data-testid="stDownloadButton"],
.st-key-cvb-toolbar-native [data-testid="stTextInput"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-toolbar-native [data-testid="stButton"] > div,
.st-key-cvb-toolbar-native [data-testid="stDownloadButton"] > div,
.st-key-cvb-toolbar-native [data-testid="stTextInput"] > div {{
  margin: 0 !important;
  padding: 0 !important;
}}
.st-key-cvb-main-native,
.st-key-cvb-main-native > div,
.st-key-cvb-main-native > [data-testid="stVerticalBlock"],
.st-key-cvb-main-native > [data-testid="stVerticalBlock"] > div,
.st-key-cvb-main-native > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-toolbar-native),
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-main-native) {{
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  flex-direction: column !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-toolbar-native) {{
  flex: 0 0 auto !important;
  min-height: auto !important;
}}
.st-key-cvb-page-native [data-testid="stElementContainer"]:has(.st-key-cvb-main-native) {{
  flex: 1 1 auto !important;
  min-height: 0 !important;
}}
.st-key-cvb-page-native .st-key-cvb-left-scroll-native,
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native,
.st-key-cvb-page-native .st-key-cvb-right-scroll-native {{
  overflow-y: auto !important;
  overflow-x: hidden !important;
  min-height: 0 !important;
}}
.st-key-cvb-page-native .st-key-cvb-left-scroll-native [data-testid="stVerticalBlock"],
.st-key-cvb-page-native .st-key-cvb-middle-scroll-native [data-testid="stVerticalBlock"],
.st-key-cvb-page-native .st-key-cvb-right-scroll-native [data-testid="stVerticalBlock"] {{
  min-height: 0 !important;
}}
.st-key-cvb-left-scroll-native .cvb-rail-heading,
.cvb-rail-heading {{
  margin-top: 0 !important;
}}

/* Toolbar parity pass: equal button height + strict right-cluster alignment */
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child > div,
.st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stVerticalBlock"] {{
  justify-content: flex-end !important;
}}
.st-key-cvb-toolbar-actions-native,
.st-key-cvb-toolbar-actions-native > div,
.st-key-cvb-toolbar-actions-native [data-testid="stVerticalBlock"],
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  width: 100% !important;
  margin-left: 0 !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 0 !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  display: flex !important;
  align-items: center !important;
  width: auto !important;
  flex: 0 0 auto !important;
  padding: 0 !important;
  margin: 0 !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {{
  margin-left: 14px !important;
}}
.st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5) {{
  margin-left: 8px !important;
}}
[data-testid="stElementContainer"].st-key-cvb_toolbar_import [data-testid="stButton"] > button {{
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  width: 96px !important;
  min-width: 96px !important;
  padding: 0 12px !important;
  line-height: 1 !important;
  border-radius: 8px 0 0 8px !important;
}}
[data-testid="stElementContainer"].st-key-cvb_toolbar_backup [data-testid="stButton"] > button {{
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  width: 96px !important;
  min-width: 96px !important;
  padding: 0 12px !important;
  line-height: 1 !important;
  border-radius: 0 !important;
}}
[data-testid="stElementContainer"].st-key-cvb_toolbar_save [data-testid="stButton"] > button {{
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  width: 96px !important;
  min-width: 96px !important;
  padding: 0 12px !important;
  line-height: 1 !important;
  border-radius: 0 8px 8px 0 !important;
}}
[data-testid="stElementContainer"].st-key-cvb_toolbar_download [data-testid="stDownloadButton"] > button {{
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  width: 138px !important;
  min-width: 138px !important;
  max-width: 138px !important;
  line-height: 1 !important;
}}
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  height: 36px !important;
  min-height: 36px !important;
  line-height: 1 !important;
  margin: 0 !important;
}}
.st-key-cvb-toolbar-actions-native button p,
.st-key-cvb-toolbar-actions-native button span,
.st-key-cvb-toolbar-actions-native .cvb-reset-open-native {{
  margin: 0 !important;
  line-height: 1 !important;
}}

/* ─────────────────────────────────────────────────────────────────────────────
   NUCLEAR FINAL OVERRIDES (keep last) — beats base_theme.css.tpl button rules.
   These selectors are prefixed with [data-testid="stAppViewContainer"] so they
   have higher specificity than any earlier global button rule.
   ───────────────────────────────────────────────────────────────────────────── */

/* ── META GROUP (left): Saved chip + Title input displayed INLINE on one row ── */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native > [data-testid="stVerticalBlock"] {{
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 14px !important;
  flex-wrap: nowrap !important;
  width: 100% !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native [data-testid="stElementContainer"] {{
  flex: 0 0 auto !important;
  width: auto !important;
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
}}
/* Saved chip wrapper-chain alignment: span lives inside stMarkdown, whose default
   baseline metrics offset it slightly above center vs the text_input next to it.
   Force every wrapper to flex-center the chip so it sits on the same row baseline. */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native [data-testid="stElementContainer"]:has(.cvb-saved-ts-native),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native [data-testid="stMarkdown"]:has(.cvb-saved-ts-native),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native [data-testid="stMarkdownContainer"]:has(.cvb-saved-ts-native) {{
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  height: 40px !important;
  min-height: 40px !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
}}
[data-testid="stAppViewContainer"] .cvb-saved-ts-native {{
  align-self: center !important;
  vertical-align: middle !important;
  margin: 0 !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-meta-native .st-key-cvb_toolbar_title_native {{
  flex: 0 0 280px !important;
  width: 280px !important;
  min-width: 280px !important;
  max-width: 280px !important;
}}
[data-testid="stAppViewContainer"] .cvb-saved-ts-native {{
  margin: 0 !important;
}}
/* Two-column outer layout: meta-left | actions-right.
   Actions hug the right edge of the page (matches CVReviewer's placement — their Reset
   button sits ~60px from viewport right edge). Toolbar's natural 20px right padding +
   page padding already gives that breathing room, so no extra padding-right is needed here.
   ⚠️ Streamlit renamed data-testid="column" → "stColumn" in newer versions, so we target BOTH.
   Without the "stColumn" variant, none of these rules apply on current Streamlit, which was
   the silent blocker preventing the layout/padding/alignment changes from taking effect. */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {{
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
  padding-right: 0 !important;
}}
/* Also nudge the meta group inward from the left edge for visual balance */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-native [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {{
  padding-left: 8px !important;
}}

/* Comfortable spacing between flat buttons */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] {{
  gap: 4px !important;
  column-gap: 4px !important;
  row-gap: 0 !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"],
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
  margin: 0 !important;
  padding: 0 !important;
  flex: 0 0 auto !important;
  width: auto !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"],
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stButton"],
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stDownloadButton"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
/* Extra breathing room before Download PDF (the primary CTA) and Reset */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {{
  margin-left: 10px !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5) {{
  margin-left: 6px !important;
}}

/* ── FLAT TEXT+ICON BUTTONS (CVReviewer style): Import / Backup / Save ──
   No borders, no card backgrounds; subtle pill highlight on hover only. */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_import button,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_backup button,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_save button {{
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  padding: 0 14px !important;
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  border-top: 0 !important;
  border-right: 0 !important;
  border-bottom: 0 !important;
  border-left: 0 !important;
  border-radius: 8px !important;
  -webkit-border-radius: 8px !important;
  color: #6b7280 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
  box-shadow: none !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  cursor: pointer !important;
  transition: background-color .16s ease, color .16s ease !important;
}}
/* Bigger Lucide-style icons (18px) to match CVReviewer */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_import button::before,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_backup button::before,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_save button::before {{
  width: 18px !important;
  height: 18px !important;
  margin-right: 0 !important;
  -webkit-mask-size: 18px 18px !important;
  mask-size: 18px 18px !important;
  background-color: currentColor !important;
}}
/* Lucide "upload" — up-arrow into open tray */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_import button::before {{
  -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='17 8 12 3 7 8'/%3E%3Cline x1='12' x2='12' y1='3' y2='15'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='17 8 12 3 7 8'/%3E%3Cline x1='12' x2='12' y1='3' y2='15'/%3E%3C/svg%3E") !important;
}}
/* Lucide "file-text" — document with text lines */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_backup button::before {{
  -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z'/%3E%3Cpolyline points='14 2 14 8 20 8'/%3E%3Cline x1='16' x2='8' y1='13' y2='13'/%3E%3Cline x1='16' x2='8' y1='17' y2='17'/%3E%3Cline x1='10' x2='8' y1='9' y2='9'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z'/%3E%3Cpolyline points='14 2 14 8 20 8'/%3E%3Cline x1='16' x2='8' y1='13' y2='13'/%3E%3Cline x1='16' x2='8' y1='17' y2='17'/%3E%3Cline x1='10' x2='8' y1='9' y2='9'/%3E%3C/svg%3E") !important;
}}
/* Lucide "save" — floppy disk */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_save button::before {{
  -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z'/%3E%3Cpolyline points='17 21 17 13 7 13 7 21'/%3E%3Cpolyline points='7 3 7 8 15 8'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z'/%3E%3Cpolyline points='17 21 17 13 7 13 7 21'/%3E%3Cpolyline points='7 3 7 8 15 8'/%3E%3C/svg%3E") !important;
}}
/* Hover: subtle pill */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_import button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_backup button:hover {{
  background: {toolbar_hover_bg} !important;
  background-color: {toolbar_hover_bg} !important;
  border: 0 !important;
  color: {toolbar_hover_color} !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_save button:hover {{
  background: {toolbar_save_hover_bg} !important;
  background-color: {toolbar_save_hover_bg} !important;
  border: 0 !important;
  color: {toolbar_save_hover_color} !important;
}}
/* Button text/children inherit color, no bg of their own */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_import button *,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_backup button *,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_save button * {{
  background: transparent !important;
  background-color: transparent !important;
  color: inherit !important;
}}

/* ── Download PDF: primary blue CTA (CVReviewer style: vibrant blue, larger icon) ──
   Covers BOTH variants:
   - cvb_toolbar_download         → real download button (PDF bytes ready)
   - cvb_toolbar_download_prepare → "Prepare PDF" button (lazy generation fallback)
   Both must look identical so the toolbar is visually stable regardless of cache state. */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download button,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download_prepare button {{
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  width: auto !important;
  min-width: 150px !important;
  max-width: none !important;
  padding: 0 18px !important;
  background: #2563eb !important;
  background-color: #2563eb !important;
  border: 0 !important;
  border-radius: 8px !important;
  color: #ffffff !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.18) !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  cursor: pointer !important;
  transition: background-color .16s ease, box-shadow .16s ease !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download button *,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download_prepare button * {{
  color: #ffffff !important;
  background: transparent !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download button::before,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download_prepare button::before {{
  content: "" !important;
  display: inline-flex !important;
  width: 18px !important;
  height: 18px !important;
  margin-right: 0 !important;
  background-color: #ffffff !important;
  -webkit-mask-repeat: no-repeat !important;
  -webkit-mask-position: center !important;
  -webkit-mask-size: 18px 18px !important;
  mask-repeat: no-repeat !important;
  mask-position: center !important;
  mask-size: 18px 18px !important;
  -webkit-mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' x2='12' y1='15' y2='3'/%3E%3C/svg%3E") !important;
  mask-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' x2='12' y1='15' y2='3'/%3E%3C/svg%3E") !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download button:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"].st-key-cvb_toolbar_download_prepare button:hover {{
  background: #1d4ed8 !important;
  background-color: #1d4ed8 !important;
  border: 0 !important;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.32) !important;
}}

/* ── Reset: flat text+icon (matches Import/Backup/Save) with red hover ──
   The Reset element is an HTML <div role='button'> rendered inside stMarkdown,
   while Import/Backup/Save are <button> inside stButton. Those two wrapper chains
   align children differently by default, which pushes Reset a few pixels lower than
   the row. The parent-chain rule below forces Reset's wrappers to flex-center-align
   so it sits on the same baseline as the buttons. */
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stElementContainer"]:has(.cvb-reset-open-native),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stMarkdown"]:has(.cvb-reset-open-native),
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native [data-testid="stMarkdownContainer"]:has(.cvb-reset-open-native) {{
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: center !important;
  height: 40px !important;
  min-height: 40px !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native .cvb-reset-open-native {{
  height: 40px !important;
  min-height: 40px !important;
  padding: 0 14px !important;
  margin: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  border-radius: 8px !important;
  color: #6b7280 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
  box-shadow: none !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  vertical-align: middle !important;
  align-self: center !important;
  cursor: pointer !important;
  transition: background-color .16s ease, color .16s ease !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native .cvb-reset-open-native::before {{
  width: 18px !important;
  height: 18px !important;
  background-color: currentColor !important;
  -webkit-mask-size: 18px 18px !important;
  mask-size: 18px 18px !important;
}}
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native .cvb-reset-open-native:hover,
[data-testid="stAppViewContainer"] .st-key-cvb-toolbar-actions-native .cvb-reset-open-native:focus-visible {{
  background: {reset_hover_bg} !important;
  background-color: {reset_hover_bg} !important;
  border: 0 !important;
  color: {reset_hover_color} !important;
}}
</style>""",
        unsafe_allow_html=True,
    )


def _render_sections_list_component(
    section_order: list[str], visibility: dict[str, bool], is_dark: bool
) -> None:
    """Render a unified section list via components.html with SortableJS.

    Each row is [grip SVG | truncated label | eye SVG] — all inside one card,
    matching CVReviewer's layout exactly.  Order and visibility changes are
    communicated back to Streamlit via a hidden text-input bridge widget.
    """
    ITEM_H = 46
    ITEM_GAP = 8
    n = len(section_order)
    comp_h = max(n * (ITEM_H + ITEM_GAP) + 8, 44)

    bg = "#1e293b" if is_dark else "#ffffff"
    border = "#334155" if is_dark else "#d3dce8"
    text = "#e2e8f0" if is_dark else "#0f172a"
    muted = "#94a3b8" if is_dark else "#64748b"
    hov = "#60a5fa" if is_dark else "#0a64ca"
    pg_bg = "transparent"

    items_html = "".join(
        f'<li class="sec-item" data-id="{sid}">'
        f'<button type="button" class="grip-btn" tabindex="-1" aria-label="Drag to reorder"></button>'
        f'<span class="sec-label">{SECTION_ID_TO_LABEL.get(sid, sid.title())}</span>'
        f'<button type="button" class="eye-btn" data-visible="{str(visibility.get(sid, True)).lower()}"'
        f' aria-label="Toggle visibility"></button>'
        f"</li>"
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
  border-radius:4px;transition:color .12s,background-color .12s;
}}
.eye-btn:hover{{color:#fde047;background:rgba(250,204,21,.18);}}
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
      if(!evt || evt.oldIndex === evt.newIndex) return;
      sendDragEnd(evt.item.dataset.id, evt.newIndex);
    }}
  }});
}}

document.querySelectorAll('.eye-btn').forEach(function(btn){{
  btn.addEventListener('click',function(e){{
    e.preventDefault();
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


def _build_preview_source(cv_data: dict) -> dict:
    """Return preview data source.

    - Empty builder state: show demo preview.
    - Once user has meaningful data: show only user data.
    """
    if _is_cv_data_effectively_empty(cv_data):
        return _build_preview_data_with_demo_defaults(cv_data)
    src = dict(cv_data) if isinstance(cv_data, dict) else {}
    src["_user_only_preview"] = True
    return src


def _render_style_component(
    current_accent: str,
    font_size: int,
    line_height: float,
    entry_spacing: int,
    show_icons: bool,
    is_dark: bool,
) -> None:
    """STYLE section as a custom HTML component matching CVReviewer exactly.

    Accent swatches (24px circles, 4-per-row grid, ring-2 on selected),
    Font Scale / Line Height / Entry Spacing sliders (6px track),
    Show icons toggle switch (36x20px, sliding thumb).
    All interactions via postMessage -> relay -> hidden buttons.
    """
    lbl_color = "#94a3b8" if is_dark else "#64748b"
    txt_color = "#f1f5f9" if is_dark else "#0f172a"
    track_bg = "#334155" if is_dark else "#e2e8f0"
    tog_off = "#475569" if is_dark else "#e2e8f0"
    ring_bg = "#1e293b" if is_dark else "#ffffff"
    value_color = "#93c5fd" if is_dark else "#0b5cb8"
    sw_border = "#475569" if is_dark else "#cbd5e1"

    # Font scale: clamp to 0.80-1.30 snapped to nearest 0.05
    raw_scale = font_size / 11.0
    scale = max(0.80, min(1.30, round(raw_scale / 0.05) * 0.05))

    # Line height: clamp to 1.0-2.0 snapped to nearest 0.1
    lh = max(1.0, min(2.0, round(line_height / 0.1) * 0.1))

    # Entry spacing: clamp to 0-24 snapped to nearest 2
    es = max(0, min(24, round(entry_spacing / 2) * 2))
    spacing_scale = es / 8.0

    # Build swatches — 4 per row using CSS grid so they never overflow
    accent_name_by_hex = {
        "#2563eb": "Blue",
        "#4f46e5": "Indigo",
        "#059669": "Emerald",
        "#d97706": "Orange",
        "#dc2626": "Red",
        "#64748b": "Slate",
        "#9db6a8": "Muted Mint",
        "#93a8c3": "Soft Steel Blue",
        "#7a8f7a": "Sage",
    }
    swatches_html = ""
    for i, color in enumerate(ACCENT_COLORS):
        active = color.lower() == (current_accent or "").lower()
        sel_cls = " sel" if active else ""
        color_label = accent_name_by_hex.get(color.lower(), "Accent Color")
        swatches_html += (
            f"<button class='sw{sel_cls}' data-idx='{i}' "
            f"style='background:{color}' title='{color_label}'></button>"
        )

    icons_on = "on" if show_icons else ""

    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:transparent;font-family:Poppins,Montserrat,system-ui,-apple-system,sans-serif;overflow:hidden;padding:2px 0 4px;}}
.lbl{{font-size:12px;font-weight:500;color:{lbl_color};display:block;margin-bottom:8px;line-height:1.2;}}
.swatches{{display:flex;flex-wrap:wrap;gap:8px;width:220px;max-width:100%;padding:4px 6px 2px;box-sizing:border-box;}}
.sw{{
  width:28px;height:28px;border-radius:999px;border:none;cursor:pointer;
  box-shadow:0 0 0 1px {sw_border};outline:none;border:2px solid transparent;
  transition:transform 0.12s,box-shadow 0.12s;
}}
.sw:hover{{transform:scale(1.05);}}
.sw.sel{{transform:none;border-color:#2563eb;box-shadow:inset 0 0 0 2px {ring_bg},0 0 0 1px #2563eb;}}
.section{{margin-top:14px;padding-right:14px;}}
.row-lbl{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;padding-right:4px;}}
.row-lbl span{{font-size:13px;font-weight:500;color:{lbl_color};}}
.row-lbl strong{{font-size:13px;font-weight:700;color:{value_color};padding-right:6px;}}
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
</script>
</body></html>"""
    # Swatches (2 rows of 4 × 24px + gap): ~66px
    # Accent label: ~20px
    # 3 sliders (label+slider+section margin): 3 × 46px = 138px
    # 1 toggle (36px + margin): ~40px
    # padding: ~10px
    # Total: ~314px → use 330 for safety
    components.html(html, height=340, scrolling=False)


def _render_zoom_toolbar_component(zoom: int, is_dark: bool = False) -> None:
    bar_bg = "#0f172a" if is_dark else "#ffffff"
    bar_border = "#334155" if is_dark else "#dbe3ef"
    icon_color = "#94a3b8" if is_dark else "#65758B"
    icon_hover_bg = "rgba(148,163,184,0.14)" if is_dark else "#f3f5f7"
    icon_hover_color = "#bfdbfe" if is_dark else "#0059B3"
    pill_bg = "rgba(37,99,235,.22)" if is_dark else "rgba(0,89,179,.10)"
    pill_border = "rgba(96,165,250,.45)" if is_dark else "rgba(0,89,179,.20)"
    pill_color = "#bfdbfe" if is_dark else "#0059B3"
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
  background:{bar_bg};
  border-bottom:1px solid {bar_border};
}}
.icon-btn{{
  width:28px;height:28px;border:0;border-radius:8px;background:transparent;
  color:{icon_color};display:inline-flex;align-items:center;justify-content:center;
  padding:6px;cursor:pointer;transition:background .15s,color .15s;
}}
.icon-btn:hover{{background:{icon_hover_bg};color:{icon_hover_color}}}
.icon-btn svg{{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.zoom-pill{{
  width:56px;min-width:56px;height:19px;border-radius:999px;
  background:{pill_bg};border:1px solid {pill_border};
  color:{pill_color};font-size:10px;font-weight:500;line-height:1;
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
    visibility = _normalize_section_visibility(ss.get("cvb_section_visibility"))
    ss["cvb_section_order"] = section_order
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
                    _rerun_resume_builder()
        for sid in SECTION_IDS:
            if st.button("_", key=f"cvb_eye_{sid}"):
                current_vis = _normalize_section_visibility(ss.get("cvb_section_visibility"))
                current_vis[sid] = not current_vis.get(sid, True)
                ss["cvb_section_visibility"] = current_vis
                _rerun_resume_builder()
        for tpl_key, _, _ in TEMPLATE_CHOICES:
            if st.button("_", key=f"cvb_tpl_{tpl_key}"):
                ss["cvb_template"] = tpl_key
                ss["cvb_zoom"] = _default_zoom_for_template(tpl_key)
                _rerun_resume_builder()
        # Hidden accent color buttons
        for i, color in enumerate(ACCENT_COLORS):
            if st.button("_", key=f"cvb_acc_{i}"):
                ss["cvb_accent_color"] = color
                _rerun_resume_builder()
        # Hidden font scale buttons (scale × 100 as int: 80,85,...,130)
        for sv in CVB_SCALE_VALUES:
            if st.button("_", key=f"cvb_scale_{sv}"):
                ss["cvb_font_size"] = max(8, min(16, round(sv / 100.0 * 11)))
                _rerun_resume_builder()
        # Hidden line-height buttons (val = lh × 10: 10,11,...,20 → 1.0 to 2.0)
        for lhv in CVB_LINE_HEIGHT_VALUES:
            if st.button("_", key=f"cvb_lh_{lhv}"):
                ss["cvb_line_height"] = lhv / 10.0
                _rerun_resume_builder()
        # Hidden entry-spacing buttons (val = px: 0,2,4,...,24)
        for esv in CVB_ENTRY_SPACING_VALUES:
            if st.button("_", key=f"cvb_es_{esv}"):
                ss["cvb_entry_spacing"] = esv
                _rerun_resume_builder()
        # Hidden toggle buttons
        if st.button("_", key="cvb_icons_toggle"):
            ss["cvb_show_icons"] = not ss.get("cvb_show_icons", True)
            _rerun_resume_builder()

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
        font_size=_safe_int(ss.get("cvb_font_size", 11), 11),
        line_height=_safe_float(ss.get("cvb_line_height", 1.4), 1.4),
        entry_spacing=_safe_int(ss.get("cvb_entry_spacing", 8), 8),
        show_icons=_coerce_bool(ss.get("cvb_show_icons", True), True),
        is_dark=is_dark,
    )


def _render_middle_panel_native() -> None:
    def _handle_header_add(section_id: str) -> bool:
        if section_id == "experience":
            eid = str(uuid.uuid4())
            st.session_state["cvb_exp_ids"].append(eid)
            st.session_state[f"cvb_exp_role_{eid}"] = ""
            st.session_state[f"cvb_exp_company_{eid}"] = ""
            st.session_state[f"cvb_exp_loc_{eid}"] = ""
            st.session_state[f"cvb_exp_start_{eid}"] = ""
            st.session_state[f"cvb_exp_end_{eid}"] = ""
            st.session_state[f"cvb_exp_curr_{eid}"] = False
            st.session_state[f"cvb_exp_desc_{eid}"] = ""
            st.session_state[f"cvb_exp_bcount_{eid}"] = 1
            st.session_state[f"cvb_exp_b_{eid}_0"] = ""
            st.session_state[f"cvb_exp_visible_{eid}"] = True
            return True
        if section_id == "education":
            eid = str(uuid.uuid4())
            st.session_state["cvb_edu_ids"].append(eid)
            st.session_state[f"cvb_edu_inst_{eid}"] = ""
            st.session_state[f"cvb_edu_degree_{eid}"] = ""
            st.session_state[f"cvb_edu_field_{eid}"] = ""
            st.session_state[f"cvb_edu_loc_{eid}"] = ""
            st.session_state[f"cvb_edu_start_{eid}"] = ""
            st.session_state[f"cvb_edu_end_{eid}"] = ""
            st.session_state[f"cvb_edu_curr_{eid}"] = False
            st.session_state[f"cvb_edu_desc_{eid}"] = ""
            st.session_state[f"cvb_edu_gpa_{eid}"] = ""
            st.session_state[f"cvb_edu_visible_{eid}"] = True
            return True
        if section_id == "skills":
            sid = str(uuid.uuid4())
            st.session_state["cvb_skill_ids"].append(sid)
            st.session_state[f"cvb_skill_item_{sid}"] = ""
            st.session_state[f"cvb_skill_visible_{sid}"] = True
            st.session_state["cvb_skill_default_seed_done"] = True
            return True
        if section_id == "projects":
            pid = str(uuid.uuid4())
            st.session_state["cvb_proj_ids"].append(pid)
            st.session_state[f"cvb_proj_name_{pid}"] = ""
            st.session_state[f"cvb_proj_role_{pid}"] = ""
            st.session_state[f"cvb_proj_desc_{pid}"] = ""
            st.session_state[f"cvb_proj_tech_{pid}"] = ""
            st.session_state[f"cvb_proj_link_{pid}"] = ""
            st.session_state[f"cvb_proj_link_url_{pid}"] = ""
            st.session_state[f"cvb_proj_start_{pid}"] = ""
            st.session_state[f"cvb_proj_end_{pid}"] = ""
            st.session_state[f"cvb_proj_visible_{pid}"] = True
            return True
        if section_id == "languages":
            lid = str(uuid.uuid4())
            st.session_state["cvb_lang_ids"].append(lid)
            st.session_state[f"cvb_lang_name_{lid}"] = ""
            st.session_state[f"cvb_lang_prof_{lid}"] = "Intermediate"
            st.session_state[f"cvb_lang_visible_{lid}"] = True
            return True
        if section_id == "certifications":
            cid = str(uuid.uuid4())
            st.session_state["cvb_cert_ids"].append(cid)
            st.session_state[f"cvb_cert_name_{cid}"] = ""
            st.session_state[f"cvb_cert_issuer_{cid}"] = ""
            st.session_state[f"cvb_cert_date_{cid}"] = ""
            st.session_state[f"cvb_cert_link_{cid}"] = ""
            st.session_state[f"cvb_cert_link_url_{cid}"] = ""
            st.session_state[f"cvb_cert_visible_{cid}"] = True
            return True
        return False

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

    # Custom CVReviewer-style section: header row (icon + label on left, chevron button
    # on right) + conditionally-rendered content. Replaces st.expander entirely so we
    # have full control over the visual layout.
    for sid in visible_order:
        label = SECTION_ID_TO_LABEL.get(sid, sid.title())
        icon_md = SECTION_ICON_BY_ID.get(sid, "")
        state_key = f"cvb_section_open_{sid}"
        if state_key not in ss:
            ss[state_key] = True
        is_open = bool(ss[state_key])

        with st.container(key=f"cvb-section-{sid}"):
            # Header row: title on left, chevron button on right
            with st.container(key=f"cvb-section-header-{sid}"):
                add_label = SECTION_ADD_BUTTON_BY_ID.get(sid)
                if add_label:
                    hl, ha, hr = st.columns([14, 6, 1], gap="small")
                else:
                    hl, hr = st.columns([20, 1], gap="small")
                with hl:
                    title_md = f"{icon_md} **{label}**" if icon_md else f"**{label}**"
                    st.markdown(title_md)
                if add_label:
                    add_btn_label = f":material/add: {add_label}"
                    with ha:
                        if st.button(add_btn_label, key=f"cvb_section_add_{sid}", type="secondary"):
                            if _handle_header_add(sid):
                                _rerun_resume_builder()
                with hr:
                    with st.container(key=f"cvb-section-chevron-{sid}"):
                        chevron_glyph = (
                            ":material/keyboard_arrow_down:"
                            if is_open
                            else ":material/chevron_right:"
                        )
                        if st.button(
                            chevron_glyph,
                            key=f"cvb_section_toggle_{sid}",
                            type="tertiary",
                            help="Collapse" if is_open else "Expand",
                        ):
                            ss[state_key] = not is_open
                            _rerun_resume_builder()

            # Content — only rendered when open. Widget values in st.session_state persist
            # across collapse/expand because session_state is independent of widget render.
            if is_open:
                with st.container(key=f"cvb-section-content-{sid}"):
                    render_map[sid]()


def _render_right_panel_native(cv_data: dict, is_dark: bool) -> None:
    ss = st.session_state
    zoom = _safe_int(
        ss.get("cvb_zoom", _default_zoom_for_template(ss.get("cvb_template", "classic"))), 100
    )
    levels = CVB_ZOOM_LEVELS

    with st.container(key="cvb-zoom-hidden-buttons"):
        if st.button("_", key="cvb_zoom_out_relay"):
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[max(0, idx - 1)]
            _rerun_resume_builder()
        if st.button("_", key="cvb_zoom_in_relay"):
            idx = levels.index(zoom) if zoom in levels else levels.index(45)
            ss["cvb_zoom"] = levels[min(len(levels) - 1, idx + 1)]
            _rerun_resume_builder()
        if st.button("_", key="cvb_zoom_reset_relay"):
            ss["cvb_zoom"] = _default_zoom_for_template(ss.get("cvb_template", "classic"))
            _rerun_resume_builder()

    template = _normalize_template(ss.get("cvb_template", "classic"))
    accent = ss.get("cvb_accent_color") or None
    font = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size = _safe_int(ss.get("cvb_font_size", 11), 11)
    line_height = _safe_float(ss.get("cvb_line_height", 1.4), 1.4)
    entry_spacing = _safe_int(ss.get("cvb_entry_spacing", 8), 8)
    sec_vis = ss.get("cvb_section_visibility")
    sec_order = ss.get("cvb_section_order")

    preview_source = _build_preview_source(cv_data)

    preview_html = generate_cv_html(
        preview_source,
        template,
        accent_color=accent,
        font_family=font,
        font_size=font_size,
        line_height=line_height,
        entry_spacing=entry_spacing,
        show_icons=_coerce_bool(ss.get("cvb_show_icons", True), True),
        preview_dark=is_dark,
        section_visibility=sec_vis,
        section_order=sec_order,
    )
    preview_body = (
        preview_html.split("<body>", 1)[-1].split("</body>", 1)[0]
        if "<body>" in preview_html
        else preview_html
    )
    preview_styles = ""
    style_start = preview_html.find("<style>")
    if style_start != -1:
        style_end = preview_html.find("</style>", style_start + 7)
        if style_end != -1:
            preview_styles = preview_html[style_start + 7 : style_end]
    scale = zoom / 100.0
    bg = "#0b1220" if is_dark else "#f4f7fb"
    paper_bg = "#0f172a" if is_dark else "#ffffff"
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
  background: {paper_bg};
  box-shadow: none;
  zoom: {scale};
}}
.resume-shell > .paper {{
  width: {A4_WIDTH_PX}px;
  min-height: {A4_HEIGHT_PX}px;
  background: {paper_bg};
}}
{preview_styles}
</style>
</head>
<body>
  <div class='preview-wrap'><div class='resume-shell'>{preview_body}</div></div>
</body>
</html>"""

    frame_height = max(900, int(A4_HEIGHT_PX * scale) + 80)
    components.html(preview_doc, height=frame_height, scrolling=False)


def render_cv_builder_page() -> None:
    _init_builder()
    _load_cv_for_builder_if_requested()

    is_dark = st.session_state.get("theme", "light") == "dark"
    _inject_builder_css_native(is_dark)
    _inject_middle_section_exact_css(is_dark)

    ss = st.session_state
    cv_data_snapshot = collect_cv_data()
    template = _normalize_template(ss.get("cvb_template", "classic"))
    accent = ss.get("cvb_accent_color") or None
    font = FONT_OPTIONS.get(ss.get("cvb_font", "System Sans"))
    font_size = _safe_int(ss.get("cvb_font_size", 11), 11)
    lh = _safe_float(ss.get("cvb_line_height", 1.4), 1.4)
    spacing = _safe_int(ss.get("cvb_entry_spacing", 8), 8)
    show_icons = _coerce_bool(ss.get("cvb_show_icons", True), True)
    sec_vis = _normalize_section_visibility(ss.get("cvb_section_visibility"))
    sec_order = _normalize_section_order(ss.get("cvb_section_order"))
    ss["cvb_section_visibility"] = sec_vis
    ss["cvb_section_order"] = sec_order
    pdf_hash, pdf_args = _pdf_request_payload(
        cv_data_snapshot,
        template,
        accent,
        font,
        font_size,
        lh,
        spacing,
        show_icons,
        is_dark,
        sec_vis,
        sec_order,
    )

    if ss.get("cvb_pdf_hash", "") != pdf_hash:
        ss["cvb_pdf_bytes"] = None
        ss["cvb_pdf_error"] = ""
        ss["cvb_pdf_hash"] = pdf_hash

    pdf_bytes = ss.get("cvb_pdf_bytes")
    pdf_error = str(ss.get("cvb_pdf_error", "") or "")

    with st.container(key="cvb-page-native"):
        with st.container(key="cvb-toolbar-native"):
            col_meta, col_actions = st.columns([1.0, 1.0], vertical_alignment="center")
            with col_meta:
                with st.container(key="cvb-toolbar-meta-native"):
                    last_saved = ss.get("cvb_last_saved")
                    saved_txt = f"Saved {last_saved}" if last_saved else "Saved --:--:--"
                    st.markdown(
                        f"<span class='cvb-saved-ts-native'>{saved_txt}</span>",
                        unsafe_allow_html=True,
                    )
                    current_title = (ss.get("cvb_cv_title", "My Resume") or "My Resume").strip()
                    if ss.get("cvb_toolbar_title_native", "") != current_title:
                        ss["cvb_toolbar_title_native"] = current_title
                    st.text_input(
                        "Resume title",
                        key="cvb_toolbar_title_native",
                        label_visibility="collapsed",
                        placeholder="My Resume",
                    )
                    title_from_toolbar = st.session_state.get(
                        "cvb_toolbar_title_native", ""
                    ).strip()
                    if title_from_toolbar and title_from_toolbar != ss.get("cvb_cv_title", ""):
                        ss["cvb_cv_title"] = title_from_toolbar
            with col_actions:
                with st.container(key="cvb-toolbar-actions-native"):
                    a1, a2, a3, a4, a5 = st.columns([0.95, 0.95, 0.85, 1.45, 0.85], gap="small")
                    with a1:
                        if st.button("Import", key="cvb_toolbar_import"):
                            ss["cvb_show_import"] = not ss.get("cvb_show_import", False)
                    with a2:
                        _render_backup_button_fragment(_get_backup_json())
                    with a3:
                        _render_save_button_fragment(template)
                    with a4:
                        pdf_filename = _build_resume_pdf_filename(ss)
                        if pdf_bytes:
                            st.download_button(
                                "Download PDF",
                                data=pdf_bytes,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key="cvb_toolbar_download",
                                type="primary",
                                on_click="ignore",
                            )
                        else:
                            if st.button(
                                "Download PDF", key="cvb_toolbar_download_prepare", type="primary"
                            ):
                                with st.spinner("Preparing PDF..."):
                                    bytes_out, err_out = _cached_generate_cv_pdf(*pdf_args)
                                ss["cvb_pdf_hash"] = pdf_hash
                                ss["cvb_pdf_bytes"] = bytes_out
                                ss["cvb_pdf_error"] = err_out
                                _rerun_resume_builder()
                    with a5:
                        st.markdown(
                            "<div role='button' tabindex='0' class='cvb-reset-open-native'>Reset</div>",
                            unsafe_allow_html=True,
                        )

        with st.container(key="cvb-reset-float-native"):
            st.markdown(
                "<div class='cvb-reset-float-title'>Reset CV Data?</div>"
                "<div class='cvb-reset-float-msg'>This will clear all your CV data. This cannot be undone.</div>",
                unsafe_allow_html=True,
            )
            with st.container(key="cvb-reset-float-actions"):
                _, rc1, rc2, _ = st.columns([0.16, 1, 1, 0.16], gap="small")
                with rc1:
                    if st.button("Yes, Reset", key="btn_confirm_reset_native", type="primary"):
                        _reset_all()
                with rc2:
                    st.markdown(
                        "<div role='button' tabindex='0' class='cvb-reset-cancel-native'>Cancel</div>",
                        unsafe_allow_html=True,
                    )

        if ss.get("cvb_show_import"):
            uploaded = st.file_uploader(
                "Upload JSON backup", type=["json"], key="cvb_import_file_native"
            )
            if uploaded:
                _import_from_json(uploaded)
        if pdf_error:
            st.warning(f"PDF export unavailable: {pdf_error}")

        with st.container(key="cvb-main-native"):
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
                # Re-collect after editor render so button-driven mutations
                # (date picker month/year, bullet add/remove, etc.) appear
                # in preview within the same rerun.
                cv_data_live = collect_cv_data()
                with st.container(key="cvb-right-scroll-native"):
                    with st.container(key="cvb-preview-tools-native"):
                        _render_zoom_toolbar_component(
                            _safe_int(
                                ss.get(
                                    "cvb_zoom",
                                    _default_zoom_for_template(ss.get("cvb_template", "classic")),
                                ),
                                100,
                            ),
                            is_dark=is_dark,
                        )
                    _render_right_panel_native(cv_data_live, is_dark)

    _inject_realtime_js()
    _inject_reset_popup_native_js()
    _inject_sections_relay_js()
    _inject_builder_final_alignment_overrides()
    return


def _summary_section() -> None:
    with st.container(key="cvb-summary-inner-card"):
        st.text_area(
            "Professional Summary",
            key="cvb_summary",
            height=130,
            placeholder="Write a short summary of your experience and strengths.",
        )
        summary_val = str(st.session_state.get("cvb_summary", "") or "")
        char_count = len(summary_val)
        st.markdown(f"<div class='cvb-summary-counter'>{char_count}</div>", unsafe_allow_html=True)


def _education_section() -> None:
    edu_ids = list(st.session_state.get("cvb_edu_ids", []))
    if not edu_ids:
        seeded_id = str(uuid.uuid4())
        st.session_state["cvb_edu_ids"] = [seeded_id]
        st.session_state[f"cvb_edu_degree_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_degree_{seeded_id}", ""
        )
        st.session_state[f"cvb_edu_inst_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_inst_{seeded_id}", ""
        )
        st.session_state[f"cvb_edu_loc_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_loc_{seeded_id}", ""
        )
        st.session_state[f"cvb_edu_start_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_start_{seeded_id}", ""
        )
        st.session_state[f"cvb_edu_end_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_end_{seeded_id}", ""
        )
        st.session_state[f"cvb_edu_curr_{seeded_id}"] = bool(
            st.session_state.get(f"cvb_edu_curr_{seeded_id}", False)
        )
        st.session_state[f"cvb_edu_desc_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_desc_{seeded_id}",
            st.session_state.get(f"cvb_edu_gpa_{seeded_id}", ""),
        )
        st.session_state[f"cvb_edu_gpa_{seeded_id}"] = st.session_state.get(
            f"cvb_edu_gpa_{seeded_id}",
            st.session_state[f"cvb_edu_desc_{seeded_id}"],
        )
        st.session_state[f"cvb_edu_visible_{seeded_id}"] = True
        edu_ids = [seeded_id]

    def _remove_education(edu_id: str) -> None:
        ids = list(st.session_state.get("cvb_edu_ids", []))
        if edu_id in ids:
            ids.remove(edu_id)
            st.session_state["cvb_edu_ids"] = ids
        for field in ["degree", "inst", "field", "loc", "start", "end", "curr", "desc", "gpa"]:
            st.session_state.pop(f"cvb_edu_{field}_{edu_id}", None)
        st.session_state.pop(f"cvb_edu_visible_{edu_id}", None)
        st.session_state.pop(f"cvb_edu_start_{edu_id}__month", None)
        st.session_state.pop(f"cvb_edu_start_{edu_id}__year", None)
        st.session_state.pop(f"cvb_edu_end_{edu_id}__month", None)
        st.session_state.pop(f"cvb_edu_end_{edu_id}__year", None)

    for eid in edu_ids:
        with st.container(key=f"cvb-edu-item-{eid}"):
            edu_spacer, edu_actions = st.columns([8.0, 2.0], gap="small")
            with edu_actions:
                eye_col, del_col = st.columns(2, gap="small")
                with eye_col:
                    edu_visible = bool(st.session_state.get(f"cvb_edu_visible_{eid}", True))
                    edu_eye_icon = (
                        ":material/visibility:" if edu_visible else ":material/visibility_off:"
                    )
                    if st.button(
                        edu_eye_icon, key=f"vis_edu_{eid}", type="tertiary", help="Show/Hide in CV"
                    ):
                        st.session_state[f"cvb_edu_visible_{eid}"] = not edu_visible
                        _rerun_resume_builder()
                with del_col:
                    if len(edu_ids) > 1 and st.button(
                        ":material/delete:", key=f"rem_edu_{eid}", type="tertiary"
                    ):
                        _remove_education(eid)
                        _rerun_resume_builder()

            st.text_input(
                "Degree", key=f"cvb_edu_degree_{eid}", placeholder="B.S. Computer Science"
            )

            c1, c2 = st.columns(2)
            with c1:
                st.text_input(
                    "Institution", key=f"cvb_edu_inst_{eid}", placeholder="University of..."
                )
            with c2:
                st.text_input("Location", key=f"cvb_edu_loc_{eid}", placeholder="City, Country")

            # Date row — direct sibling of the Institution/Location row (no
            # extra wrapper container) so Streamlit's natural sibling gap applies.
            c3, c4 = st.columns(2)
            with c3:
                with st.container(key=f"cvb-edu-date-start-{eid}"):
                    _date_field("Start Date", f"cvb_edu_start_{eid}")
            with c4:
                with st.container(key=f"cvb-edu-date-end-{eid}"):
                    _date_field(
                        "End Date",
                        f"cvb_edu_end_{eid}",
                        allow_present=True,
                        current_key=f"cvb_edu_curr_{eid}",
                    )

            st.text_area(
                "Description / Details",
                key=f"cvb_edu_desc_{eid}",
                height=74,
                placeholder="Additional details...",
            )
            st.session_state[f"cvb_edu_gpa_{eid}"] = st.session_state.get(f"cvb_edu_desc_{eid}", "")


def _skills_section() -> None:
    ss = st.session_state
    skill_ids = list(ss.get("cvb_skill_ids", []))

    # Keep Skills consistent with Education/Experience card behavior:
    # show pre-seeded editable rows instead of an empty-state hint.
    if not skill_ids and not ss.get("cvb_skill_default_seed_done", False):
        seeded_ids: list[str] = []
        for _ in range(3):
            sid = str(uuid.uuid4())
            seeded_ids.append(sid)
            ss[f"cvb_skill_item_{sid}"] = ss.get(f"cvb_skill_item_{sid}", "")
            ss[f"cvb_skill_visible_{sid}"] = True
        ss["cvb_skill_ids"] = seeded_ids
        ss["cvb_skill_default_seed_done"] = True
        skill_ids = seeded_ids

    def _remove_skill(skill_id: str) -> None:
        ids = list(ss.get("cvb_skill_ids", []))
        if skill_id in ids:
            ids.remove(skill_id)
            ss["cvb_skill_ids"] = ids
        ss.pop(f"cvb_skill_item_{skill_id}", None)
        ss.pop(f"cvb_skill_visible_{skill_id}", None)

    if not skill_ids:
        st.info("Add a skill to continue.")
        return

    for idx, sid in enumerate(skill_ids):
        with st.container(key=f"cvb-skill-item-{sid}"):
            c1, c2, c3 = st.columns([8.0, 0.8, 0.8], gap="small")
            with c1:
                st.text_input(
                    f"Skill {idx + 1}",
                    key=f"cvb_skill_item_{sid}",
                    placeholder="Skill name...",
                    label_visibility="collapsed",
                )
            with c2:
                skill_visible = bool(ss.get(f"cvb_skill_visible_{sid}", True))
                skill_eye_icon = (
                    ":material/visibility:" if skill_visible else ":material/visibility_off:"
                )
                if st.button(
                    skill_eye_icon, key=f"vis_skill_{sid}", type="tertiary", help="Show/Hide in CV"
                ):
                    ss[f"cvb_skill_visible_{sid}"] = not skill_visible
                    _rerun_resume_builder()
            with c3:
                st.button(
                    ":material/delete:",
                    key=f"rem_skill_{sid}",
                    type="tertiary",
                    on_click=_remove_skill,
                    args=(sid,),
                )


def _projects_section() -> None:
    proj_ids = list(st.session_state.get("cvb_proj_ids", []))
    if not proj_ids:
        seeded_id = str(uuid.uuid4())
        st.session_state["cvb_proj_ids"] = [seeded_id]
        st.session_state[f"cvb_proj_name_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_role_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_desc_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_tech_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_link_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_link_url_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_start_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_end_{seeded_id}"] = ""
        st.session_state[f"cvb_proj_visible_{seeded_id}"] = True
        proj_ids = [seeded_id]

    for idx, pid in enumerate(proj_ids):
        with st.container(key=f"cvb-proj-item-{pid}"):
            ph1, ph_eye, ph_del = st.columns([8.0, 1.0, 1.0], gap="small")
            with ph1:
                st.markdown(f"**Project {idx + 1}**")
            with ph_eye:
                proj_visible = bool(st.session_state.get(f"cvb_proj_visible_{pid}", True))
                proj_eye_icon = (
                    ":material/visibility:" if proj_visible else ":material/visibility_off:"
                )
                if st.button(
                    proj_eye_icon, key=f"vis_proj_{pid}", type="tertiary", help="Show/Hide in CV"
                ):
                    st.session_state[f"cvb_proj_visible_{pid}"] = not proj_visible
                    _rerun_resume_builder()
            with ph_del:
                if st.button(":material/delete:", key=f"rem_proj_{pid}", type="tertiary"):
                    st.session_state["cvb_proj_ids"].remove(pid)
                    st.session_state.pop(f"cvb_proj_visible_{pid}", None)
                    st.session_state.pop(f"cvb_proj_link_url_{pid}", None)
                    try:
                        qk = f"cvb_lurl_proj_{pid}"
                        if qk in st.query_params:
                            del st.query_params[qk]
                    except Exception:
                        pass
                    _rerun_resume_builder()
            c1, c2 = st.columns(2)
            with c1:
                st.text_input(
                    "Project Name", key=f"cvb_proj_name_{pid}", placeholder="Enter project name"
                )
            with c2:
                st.text_input(
                    "Your Role", key=f"cvb_proj_role_{pid}", placeholder="Enter your role"
                )

            _date_field("Date", f"cvb_proj_start_{pid}")
            st.text_area(
                "Description",
                key=f"cvb_proj_desc_{pid}",
                height=90,
                placeholder="Describe what the project does and your impact",
            )
            st.text_input(
                "Technologies",
                key=f"cvb_proj_tech_{pid}",
                placeholder="React, Node.js, PostgreSQL",
                help="Comma separated technologies used in this project.",
            )
            with st.container(key=f"cvb-link-field-proj-{pid}"):
                st.text_input(
                    "Project Link",
                    key=f"cvb_proj_link_{pid}",
                    placeholder="Enter project link display text",
                )
            with st.container(key=f"cvb-link-url-proj-{pid}"):
                st.text_input(
                    "Project Link URL",
                    key=f"cvb_proj_link_url_{pid}",
                    label_visibility="collapsed",
                    placeholder="https://project-url.com",
                )


def _languages_section() -> None:
    lang_ids = list(st.session_state.get("cvb_lang_ids", []))
    if not lang_ids:
        seeded_id = str(uuid.uuid4())
        st.session_state["cvb_lang_ids"] = [seeded_id]
        st.session_state[f"cvb_lang_name_{seeded_id}"] = ""
        st.session_state[f"cvb_lang_prof_{seeded_id}"] = "Intermediate"
        st.session_state[f"cvb_lang_visible_{seeded_id}"] = True
        lang_ids = [seeded_id]
    for lid in lang_ids:
        with st.container(key=f"cvb-lang-item-{lid}"):
            c1, c2, c3, c4 = st.columns([3.7, 3.7, 0.8, 0.8])
            with c1:
                st.text_input(
                    "Language",
                    key=f"cvb_lang_name_{lid}",
                    placeholder="e.g. English",
                    label_visibility="collapsed",
                )
            with c2:
                st.selectbox(
                    "Proficiency",
                    PROFICIENCY_OPTIONS,
                    key=f"cvb_lang_prof_{lid}",
                    label_visibility="collapsed",
                )
            with c3:
                lang_visible = bool(st.session_state.get(f"cvb_lang_visible_{lid}", True))
                lang_eye_icon = (
                    ":material/visibility:" if lang_visible else ":material/visibility_off:"
                )
                if st.button(
                    lang_eye_icon, key=f"vis_lang_{lid}", type="tertiary", help="Show/Hide in CV"
                ):
                    st.session_state[f"cvb_lang_visible_{lid}"] = not lang_visible
                    _rerun_resume_builder()
            with c4:
                if st.button(":material/delete:", key=f"rem_lang_{lid}", type="tertiary"):
                    st.session_state["cvb_lang_ids"].remove(lid)
                    st.session_state.pop(f"cvb_lang_visible_{lid}", None)
                    _rerun_resume_builder()


def _certifications_section() -> None:
    cert_ids = list(st.session_state.get("cvb_cert_ids", []))
    if not cert_ids:
        seeded_id = str(uuid.uuid4())
        st.session_state["cvb_cert_ids"] = [seeded_id]
        st.session_state[f"cvb_cert_name_{seeded_id}"] = ""
        st.session_state[f"cvb_cert_issuer_{seeded_id}"] = ""
        st.session_state[f"cvb_cert_date_{seeded_id}"] = ""
        st.session_state[f"cvb_cert_link_{seeded_id}"] = ""
        st.session_state[f"cvb_cert_link_url_{seeded_id}"] = ""
        st.session_state[f"cvb_cert_visible_{seeded_id}"] = True
        cert_ids = [seeded_id]
    for idx, cid in enumerate(cert_ids):
        with st.container(key=f"cvb-cert-item-{cid}"):
            ch1, ch_eye, ch_del = st.columns([8.0, 1.0, 1.0], gap="small")
            with ch1:
                st.markdown(f"**Certification {idx + 1}**")
            with ch_eye:
                cert_visible = bool(st.session_state.get(f"cvb_cert_visible_{cid}", True))
                cert_eye_icon = (
                    ":material/visibility:" if cert_visible else ":material/visibility_off:"
                )
                if st.button(
                    cert_eye_icon, key=f"vis_cert_{cid}", type="tertiary", help="Show/Hide in CV"
                ):
                    st.session_state[f"cvb_cert_visible_{cid}"] = not cert_visible
                    _rerun_resume_builder()
            with ch_del:
                if st.button(":material/delete:", key=f"rem_cert_{cid}", type="tertiary"):
                    st.session_state["cvb_cert_ids"].remove(cid)
                    st.session_state.pop(f"cvb_cert_visible_{cid}", None)
                    st.session_state.pop(f"cvb_cert_link_url_{cid}", None)
                    try:
                        qk = f"cvb_lurl_cert_{cid}"
                        if qk in st.query_params:
                            del st.query_params[qk]
                    except Exception:
                        pass
                    _rerun_resume_builder()
            st.text_input(
                "Title", key=f"cvb_cert_name_{cid}", placeholder="Enter certification title"
            )
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Issuer", key=f"cvb_cert_issuer_{cid}", placeholder="Enter issuer")
            with c2:
                _date_field("Date", f"cvb_cert_date_{cid}")
            with st.container(key=f"cvb-link-field-cert-{cid}"):
                st.text_input(
                    "Credential URL",
                    key=f"cvb_cert_link_{cid}",
                    placeholder="Enter credential display text",
                )
            with st.container(key=f"cvb-link-url-cert-{cid}"):
                st.text_input(
                    "Credential URL Link",
                    key=f"cvb_cert_link_url_{cid}",
                    label_visibility="collapsed",
                    placeholder="https://credential-url.com",
                )


def _interests_section() -> None:
    interests = list(st.session_state.get("cvb_interests", []))
    if interests:
        for i, interest in enumerate(interests):
            with st.container(key=f"cvb-int-item-{i}"):
                c1, c2 = st.columns([8, 1.4])
                with c1:
                    st.text_input(
                        f"Interest {i + 1}",
                        value=interest,
                        key=f"cvb_interest_readonly_{i}",
                        disabled=True,
                        label_visibility="collapsed",
                    )
                with c2:
                    if st.button("Delete", key=f"rm_int_{i}", help=f"Remove {interest}"):
                        interests.pop(i)
                        st.session_state["cvb_interests"] = interests
                        _rerun_resume_builder()

    ctr = st.session_state.get("cvb_interest_ctr", 0)
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
                _rerun_resume_builder()


# --- CVReviewer middle-panel runtime overrides (v2) ---
def _personal_section() -> None:
    with st.container(key="cvb-personal-inner-card"):
        st.text_input("Full Name", key="cvb_full_name", placeholder="Enter full name")
        st.text_input(
            "Professional Title", key="cvb_prof_title", placeholder="Enter professional title"
        )

        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Email", key="cvb_email", placeholder="you@email.com")
        with c2:
            st.text_input("Phone", key="cvb_phone", placeholder="Enter phone number")

        c3, c4 = st.columns(2)
        with c3:
            st.text_input("Location", key="cvb_location", placeholder="Enter location")
        with c4:
            with st.container(key="cvb-link-field-linkedin"):
                st.text_input(
                    "LinkedIn", key="cvb_linkedin", placeholder="Enter LinkedIn display text"
                )
            with st.container(key="cvb-link-url-linkedin"):
                st.text_input(
                    "LinkedIn URL",
                    key="cvb_linkedin_url",
                    label_visibility="collapsed",
                    placeholder="https://www.linkedin.com/in/username",
                )

        c5, c6 = st.columns(2)
        with c5:
            with st.container(key="cvb-link-field-website"):
                st.text_input(
                    "Website", key="cvb_website", placeholder="Enter website display text"
                )
            with st.container(key="cvb-link-url-website"):
                st.text_input(
                    "Website URL",
                    key="cvb_website_url",
                    label_visibility="collapsed",
                    placeholder="https://yourwebsite.com",
                )
        with c6:
            with st.container(key="cvb-link-field-github"):
                st.text_input("GitHub", key="cvb_github", placeholder="Enter GitHub display text")
            with st.container(key="cvb-link-url-github"):
                st.text_input(
                    "GitHub URL",
                    key="cvb_github_url",
                    label_visibility="collapsed",
                    placeholder="https://github.com/username",
                )


def _experience_section() -> None:
    exp_ids = list(st.session_state.get("cvb_exp_ids", []))
    if not exp_ids:
        st.info("Add a position to start building your work experience.")
        return

    def _clone_position(source_id: str) -> None:
        new_id = str(uuid.uuid4())
        ids = list(st.session_state.get("cvb_exp_ids", []))
        try:
            insert_at = ids.index(source_id) + 1
        except ValueError:
            insert_at = len(ids)
        ids.insert(insert_at, new_id)
        st.session_state["cvb_exp_ids"] = ids

        for field in ["role", "company", "loc", "start", "end", "curr", "desc"]:
            st.session_state[f"cvb_exp_{field}_{new_id}"] = st.session_state.get(
                f"cvb_exp_{field}_{source_id}",
                "",
            )
        st.session_state[f"cvb_exp_visible_{new_id}"] = True
        bcount = max(1, int(st.session_state.get(f"cvb_exp_bcount_{source_id}", 1)))
        st.session_state[f"cvb_exp_bcount_{new_id}"] = bcount
        for i in range(bcount):
            st.session_state[f"cvb_exp_b_{new_id}_{i}"] = st.session_state.get(
                f"cvb_exp_b_{source_id}_{i}",
                "",
            )

    def _remove_position(exp_id: str) -> None:
        ids = list(st.session_state.get("cvb_exp_ids", []))
        if exp_id in ids:
            ids.remove(exp_id)
            st.session_state["cvb_exp_ids"] = ids
        for field in ["role", "company", "loc", "start", "end", "curr", "desc", "bcount"]:
            st.session_state.pop(f"cvb_exp_{field}_{exp_id}", None)
        st.session_state.pop(f"cvb_exp_visible_{exp_id}", None)
        st.session_state.pop(f"cvb_exp_start_{exp_id}__month", None)
        st.session_state.pop(f"cvb_exp_start_{exp_id}__year", None)
        st.session_state.pop(f"cvb_exp_end_{exp_id}__month", None)
        st.session_state.pop(f"cvb_exp_end_{exp_id}__year", None)
        for key in list(st.session_state.keys()):
            if key.startswith(f"cvb_exp_b_{exp_id}_"):
                st.session_state.pop(key, None)

    def _remove_bullet(exp_id: str, bullet_index: int) -> None:
        bcount = max(1, int(st.session_state.get(f"cvb_exp_bcount_{exp_id}", 1)))
        if bcount > 1:
            for j in range(bullet_index, bcount - 1):
                st.session_state[f"cvb_exp_b_{exp_id}_{j}"] = st.session_state.get(
                    f"cvb_exp_b_{exp_id}_{j + 1}",
                    "",
                )
            st.session_state.pop(f"cvb_exp_b_{exp_id}_{bcount - 1}", None)
            st.session_state[f"cvb_exp_bcount_{exp_id}"] = bcount - 1
        else:
            st.session_state[f"cvb_exp_b_{exp_id}_0"] = ""

    for idx, eid in enumerate(exp_ids):
        with st.container(key=f"cvb-exp-item-{eid}"):
            ch1, ch2 = st.columns([7.2, 2.8], gap="small")
            with ch1:
                st.markdown(f"**Position {idx + 1}**")
            with ch2:
                with st.container(key=f"cvb-exp-actions-{eid}"):
                    act_dup, act_eye, act_del = st.columns([2.0, 1.0, 1.0], gap="small")
                    with act_dup:
                        if st.button("Duplicate", key=f"dup_exp_{eid}", type="tertiary"):
                            _clone_position(eid)
                            _rerun_resume_builder()
                    with act_eye:
                        exp_visible = bool(st.session_state.get(f"cvb_exp_visible_{eid}", True))
                        exp_eye_icon = (
                            ":material/visibility:" if exp_visible else ":material/visibility_off:"
                        )
                        if st.button(
                            exp_eye_icon,
                            key=f"vis_exp_{eid}",
                            type="tertiary",
                            help="Show/Hide in CV",
                        ):
                            st.session_state[f"cvb_exp_visible_{eid}"] = not exp_visible
                            _rerun_resume_builder()
                    with act_del:
                        if st.button(":material/delete:", key=f"rem_exp_{eid}", type="tertiary"):
                            _remove_position(eid)
                            _rerun_resume_builder()

            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Job Title", key=f"cvb_exp_role_{eid}", placeholder="Enter job title")
            with c2:
                st.text_input("Company", key=f"cvb_exp_company_{eid}", placeholder="Enter company")

            # Date row — rendered as a direct sibling of the Job Title row so it
            # picks up Streamlit's natural vertical-block sibling gap. The two
            # inner cvb-exp-date-{start,end}-{eid} containers are kept because
            # other CSS rules style the popover button + label spacing inside.
            c3, c4 = st.columns(2)
            with c3:
                with st.container(key=f"cvb-exp-date-start-{eid}"):
                    _date_field("Start Date", f"cvb_exp_start_{eid}")
            with c4:
                curr_key = f"cvb_exp_curr_{eid}"
                end_key = f"cvb_exp_end_{eid}"
                with st.container(key=f"cvb-exp-date-end-{eid}"):
                    _date_field(
                        "End Date",
                        end_key,
                        allow_present=True,
                        current_key=curr_key,
                    )
            st.text_input("Location", key=f"cvb_exp_loc_{eid}", placeholder="City, Country")

            st.text_area(
                "Description",
                key=f"cvb_exp_desc_{eid}",
                height=78,
                placeholder="Briefly describe your core responsibilities in this role",
            )

            st.markdown("**Key Achievements**")
            bcount = max(1, int(st.session_state.get(f"cvb_exp_bcount_{eid}", 1)))
            for i in range(bcount):
                bc1, bc2, bc3 = st.columns([0.25, 8.2, 0.55])
                with bc1:
                    st.markdown(
                        "<div style='color:#0b63ce;font-size:1rem;line-height:2.1;'>&bull;</div>",
                        unsafe_allow_html=True,
                    )
                with bc2:
                    st.text_input(
                        f"bullet_{eid}_{i}",
                        key=f"cvb_exp_b_{eid}_{i}",
                        placeholder="Describe an achievement...",
                        label_visibility="collapsed",
                    )
                with bc3:
                    st.button(
                        ":material/close:",
                        key=f"rem_bullet_{eid}_{i}",
                        type="tertiary",
                        help="Remove bullet",
                        on_click=_remove_bullet,
                        args=(eid, i),
                    )

            if st.button("Add bullet point", key=f"add_b_{eid}", type="tertiary"):
                st.session_state[f"cvb_exp_bcount_{eid}"] = bcount + 1
                _rerun_resume_builder()


# --- CVReviewer template-structure overrides (safe, isolated) ---
def generate_cv_html(
    data: dict,
    template: str = "classic",
    accent_color: str | None = None,
    font_family: str | None = None,
    font_size: int = 11,
    line_height: float = 1.4,
    entry_spacing: int = 8,
    show_icons: bool = True,
    preview_dark: bool = False,
    section_visibility: dict | None = None,
    section_order: list | None = None,
    typography_scale: float = 1.0,
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
    scale = max(0.85, min(2.0, _safe_float(typography_scale, 1.0)))
    fs = max(9, int(font_size))
    fs_xs = max(7, fs - 2)
    lh = max(1.15, float(line_height))
    es = max(4, int(entry_spacing))

    def _sx(value: float) -> float:
        return round(float(value) * scale, 2)

    bg_page = "#0b1220" if preview_dark else "#f8fafc"
    paper_bg = "#111827" if preview_dark else "#ffffff"
    text = "#e5e7eb" if preview_dark else "#0f172a"
    muted = "#94a3b8" if preview_dark else "#64748b"
    line = "#334155" if preview_dark else "#dbe4f0"

    strict_user_preview = bool(data.get("_user_only_preview", False))
    p = data.get("personal", {}) or {}
    name_raw = str(p.get("full_name", "") or "").strip()
    name_text = name_raw if strict_user_preview else (name_raw or "Your Name")
    title_text = str(p.get("prof_title", "") or "").strip()
    summary_text = str(p.get("summary", "") or "").strip()
    name = _html_escape(name_text)
    title = _html_escape(title_text)
    summary = _html_escape(summary_text)
    name_hidden_attr = "" if name_text else " style='display:none'"

    contacts_raw = [
        ("email", "Email", p.get("email", "")),
        ("phone", "Phone", p.get("phone", "")),
        ("location", "Location", p.get("location", "")),
        ("linkedin", "LinkedIn", p.get("linkedin", "")),
        ("website", "Website", p.get("website", "")),
        ("github", "GitHub", p.get("github", "")),
    ]
    contact_urls = {
        "linkedin": str(p.get("linkedin_url", "") or "").strip(),
        "website": str(p.get("website_url", "") or "").strip(),
        "github": str(p.get("github_url", "") or "").strip(),
    }
    contacts = []
    for k, lbl, v in contacts_raw:
        display_val = str(v or "").strip()
        href_val = contact_urls.get(k, "")
        if display_val or (k in {"linkedin", "website", "github"} and href_val):
            contacts.append((k, lbl, display_val))
    icon_map = {
        "email": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1zm13 2.383-4.708 2.825L15 11.105zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741M1 11.105l4.708-2.897L1 5.383z'/></svg>",
        "phone": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.6 17.6 0 0 0 4.168 6.608 17.6 17.6 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.68.68 0 0 0-.58-.122l-2.19.547a1.75 1.75 0 0 1-1.657-.459L5.482 8.062a1.75 1.75 0 0 1-.46-1.657l.548-2.19a.68.68 0 0 0-.122-.58z'/><path d='M1.884.511a1.745 1.745 0 0 1 2.612.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.68.68 0 0 0 .178.643l2.457 2.457a.68.68 0 0 0 .644.178l2.189-.547a1.75 1.75 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.6 18.6 0 0 1-7.01-4.42 18.6 18.6 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877z'/></svg>",
        "location": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M12.166 8.94c-.524 1.062-1.234 2.12-1.96 3.07A32 32 0 0 1 8 14.58a32 32 0 0 1-2.206-2.57c-.726-.95-1.436-2.008-1.96-3.07C3.304 7.867 3 6.862 3 6a5 5 0 0 1 10 0c0 .862-.305 1.867-.834 2.94M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10'/><path d='M8 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4m0 1a3 3 0 1 0 0-6 3 3 0 0 0 0 6'/></svg>",
        "website": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m7.5-6.923c-.67.204-1.335.82-1.887 1.855A8 8 0 0 0 5.145 4H7.5zM4.09 4a9.3 9.3 0 0 1 .64-1.539 7 7 0 0 1 .597-.933A7.03 7.03 0 0 0 2.255 4zm-.582 3.5c.03-.877.138-1.718.312-2.5H1.674a7 7 0 0 0-.656 2.5zM4.847 5a12.5 12.5 0 0 0-.338 2.5H7.5V5zM8.5 5v2.5h2.99a12.5 12.5 0 0 0-.337-2.5zM4.51 8.5a12.5 12.5 0 0 0 .337 2.5H7.5V8.5zm3.99 0V11h2.653c.187-.765.306-1.608.338-2.5zM5.145 12q.208.58.468 1.068c.552 1.035 1.218 1.65 1.887 1.855V12zm.182 2.472a7 7 0 0 1-.597-.933A9.3 9.3 0 0 1 4.09 12H2.255a7 7 0 0 0 3.072 2.472M3.82 11a13.7 13.7 0 0 1-.312-2.5h-2.49c.062.89.291 1.733.656 2.5zm6.853 3.472A7 7 0 0 0 13.745 12H11.91a9.3 9.3 0 0 1-.64 1.539 7 7 0 0 1-.597.933M8.5 12v2.923c.67-.204 1.335-.82 1.887-1.855q.26-.487.468-1.068zm3.68-1h2.146c.365-.767.594-1.61.656-2.5h-2.49a13.7 13.7 0 0 1-.312 2.5m2.802-3.5a7 7 0 0 0-.656-2.5H12.18c.174.782.282 1.623.312 2.5zM11.27 2.461c.247.464.462.98.64 1.539h1.835a7 7 0 0 0-3.072-2.472c.218.284.418.598.597.933M10.855 4a8 8 0 0 0-.468-1.068C9.835 1.897 9.17 1.282 8.5 1.077V4z'/></svg>",
        "linkedin": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z'/></svg>",
        "github": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor'><path d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8'/></svg>",
    }
    icons_class = "icons-on" if show_icons else "icons-off"

    def _classic_contact_row() -> str:
        link_fields = {"linkedin", "website", "github"}

        def _row(order: list[str], row_class: str) -> str:
            chunk: list[str] = []
            for field_key in order:
                raw_val = ""
                for k, _, v in contacts_raw:
                    if k == field_key:
                        raw_val = str(v or "").strip()
                        break
                disp, href = (
                    _normalize_contact_link(
                        field_key,
                        raw_val,
                        contact_urls.get(field_key, ""),
                    )
                    if field_key in link_fields
                    else (raw_val, "")
                )
                visible = bool(str(disp or "").strip())
                hidden = " style='display:none'" if not visible else ""
                ico = icon_map.get(field_key, "")
                if field_key in link_fields:
                    if href:
                        value_html = (
                            f"<a class='ci-link ci-val' data-cf='{field_key}' href='{_html_attr_escape(href)}' "
                            f"target='_blank' rel='noopener noreferrer'>{_html_escape(disp)}</a>"
                        )
                    else:
                        value_html = f"<span class='ci-val' data-cf='{field_key}'>{_html_escape(disp)}</span>"
                else:
                    value_html = f"<span class='ci-val'>{_html_escape(disp)}</span>"
                chunk.append(
                    f"<span class='ci-wrapper' data-cf='{field_key}'{hidden}>"
                    f"<span class='ci-sep' style='display:none'>\u00b7</span>"
                    f"<span class='ci-item'><span class='ci-ico'>{ico}</span>{value_html}</span>"
                    f"</span>"
                )
            return f"<div class='cv-contact-row {row_class}'>{''.join(chunk)}</div>"

        row_top = _row(["email", "phone", "location", "linkedin"], "row-top")
        row_bottom = _row(["website", "github"], "row-bottom")
        any_visible = bool(contacts)
        hidden_row = "" if any_visible else " style='display:none'"
        return f"<div id='cv-contact' class='cv-contact'{hidden_row}>{row_top}{row_bottom}</div>"

    def _modern_contact_stack() -> str:
        link_fields = {"linkedin", "website", "github"}
        parts = []
        for k, _, v in contacts_raw:
            val = str(v or "").strip()
            disp, href = (
                _normalize_contact_link(k, val, contact_urls.get(k, ""))
                if k in link_fields
                else (val, "")
            )
            ico = icon_map.get(k, "")
            hidden_attr = " style='display:none'" if not disp else ""
            if k in link_fields:
                if href:
                    value_html = (
                        f"<a class='ci-link ci-val' data-cf='{k}' href='{_html_attr_escape(href)}' "
                        f"target='_blank' rel='noopener noreferrer'>{_html_escape(disp)}</a>"
                    )
                else:
                    value_html = f"<span class='ci-val' data-cf='{k}'>{_html_escape(disp)}</span>"
            else:
                value_html = f"<span class='ci-val' data-cf='{k}'>{_html_escape(disp)}</span>"
            parts.append(
                f"<p class='contact-item' data-cf='{k}'{hidden_attr}>"
                f"<span class='ci-ico'>{ico}</span>"
                f"{value_html}"
                f"</p>"
            )
        return f"<div class='contact-stack'>{''.join(parts)}</div>"

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
        return f"<p id='cv-summary' class='cv-p'>{summary}</p>"

    def _experience_html() -> str:
        parts: list[str] = []
        for exp in data.get("experience", []) or []:
            if not _row_has_meaningful_data(exp):
                continue
            role = _html_escape(exp.get("role", ""))
            company = _html_escape(exp.get("company", ""))
            loc = _html_escape(exp.get("location", ""))
            desc = _html_escape(exp.get("description", ""))
            dr = _date_range_html(
                exp.get("start_date", ""), exp.get("end_date", ""), bool(exp.get("current", False))
            )
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
                + (f"<p class='cv-p'>{desc}</p>" if desc else "")
                + (f"<ul class='cv-ul'>{bullet_html}</ul>" if bullet_html else "")
                + "</div>"
            )
        return "".join(parts)

    def _education_html() -> str:
        parts: list[str] = []
        for edu in data.get("education", []) or []:
            if not _row_has_meaningful_data(edu):
                continue
            inst = _html_escape(edu.get("institution", ""))
            degree = _html_escape(edu.get("degree", ""))
            field = _html_escape(edu.get("field", ""))
            loc = _html_escape(edu.get("location", ""))
            details = _html_escape(edu.get("description", edu.get("gpa", "")))
            dr = _date_range_html(
                edu.get("start_date", ""), edu.get("end_date", ""), bool(edu.get("current", False))
            )
            desc_left = " \u00b7 ".join([x for x in [degree, field] if x])

            parts.append(
                "<div class='cv-entry'>"
                "<div class='row-top'>"
                f"<div class='role'>{inst}</div>"
                f"<div class='dr'>{dr}</div>"
                "</div>"
                f"<div class='row-sub'>{desc_left}{(', ' + loc) if loc else ''}</div>"
                + (f"<p class='cv-p'>{details}</p>" if details else "")
                + "</div>"
            )
        return "".join(parts)

    def _projects_html() -> str:
        parts: list[str] = []
        for proj in data.get("projects", []) or []:
            if not _row_has_meaningful_data(proj):
                continue
            name_val = _html_escape(proj.get("name", ""))
            role_val = _html_escape(proj.get("role", ""))
            desc = _html_escape(proj.get("description", ""))
            link_disp, link_href = _normalize_contact_link(
                "website",
                str(proj.get("link", "") or ""),
                str(proj.get("link_url", "") or ""),
            )
            link_val = _html_escape(link_disp)
            link_href_attr = _html_attr_escape(link_href)
            tech = [str(x).strip() for x in proj.get("tech_stack", []) if str(x).strip()]
            dr = _date_range_html(proj.get("start_date", ""), proj.get("end_date", ""), False)
            row_sub = role_val or ""
            if tech:
                tech_line = _html_escape(", ".join(tech))
                row_sub = f"{row_sub}{' \u00b7 ' if row_sub else ''}{tech_line}"
            link_html = ""
            if link_val:
                if link_href:
                    link_html = (
                        f"<p class='cv-link'><a class='ci-link' href='{link_href_attr}' target='_blank' "
                        f"rel='noopener noreferrer'>{link_val}</a></p>"
                    )
                else:
                    link_html = f"<p class='cv-link'>{link_val}</p>"
            parts.append(
                "<div class='cv-entry'>"
                "<div class='row-top'>"
                f"<div class='role'>{name_val}</div>"
                f"<div class='dr'>{dr}</div>"
                "</div>"
                + (f"<div class='row-sub'>{row_sub}</div>" if row_sub else "")
                + (f"<p class='cv-p'>{desc}</p>" if desc else "")
                + link_html
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
            link_disp, link_href = _normalize_contact_link(
                "website",
                str(cert.get("link", "") or ""),
                str(cert.get("link_url", "") or ""),
            )
            link_val = _html_escape(link_disp)
            link_href_attr = _html_attr_escape(link_href)
            extra = " \u00b7 ".join([x for x in [issuer, dt] if x])
            link_html = ""
            if link_val:
                if link_href:
                    link_html = (
                        f"<p class='cv-link'><a class='ci-link' href='{link_href_attr}' target='_blank' "
                        f"rel='noopener noreferrer'>{link_val}</a></p>"
                    )
                else:
                    link_html = f"<p class='cv-link'>{link_val}</p>"
            rows.append(
                "<div class='cv-entry'>"
                f"<p class='cv-p'><strong>{nm}</strong>{(' \u2014 ' + extra) if extra else ''}</p>"
                + link_html
                + "</div>"
            )
        return "".join(rows)

    def _interests_html() -> str:
        vals = [str(x).strip() for x in (data.get("interests", []) or []) if str(x).strip()]
        if not vals:
            return ""
        return f"<p class='cv-p'>{_html_escape(', '.join(vals))}</p>"

    def _skills_bullet_columns_html(column_count: int) -> str:
        if not skill_values:
            return ""
        cols = max(1, min(3, int(column_count)))
        items = "".join(f"<li>{_html_escape(v)}</li>" for v in skill_values)
        return f"<ul class='skills-grid skills-cols-{cols}'>{items}</ul>"

    section_map = {
        "summary": _summary_html(),
        "experience": _experience_html(),
        "education": _education_html(),
        "skills": _skills_bullet_columns_html(3),
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
        f"<div class='cv-paper classic {icons_class}'>"
        "<header class='cv-head center'>"
        f"<h1 id='cv-name'{name_hidden_attr}>{name}</h1>"
        + (
            f"<p class='cv-title' id='cv-title'>{title}</p>"
            if title
            else "<p class='cv-title' id='cv-title' style='display:none'></p>"
        )
        + _classic_contact_row()
        + "</header>"
        + _ordered_sections(order, compact=False)
        + "</div>"
    )

    # Modern (CVReviewer-like blue sidebar)
    left_pref_modern = {"skills", "languages", "certifications", "interests"}
    left_modern_ids = [sid for sid in order if sid in left_pref_modern and vis.get(sid, True)]
    right_modern_ids = [
        sid
        for sid in order
        if sid not in left_pref_modern and sid != "personal" and vis.get(sid, True)
    ]
    modern_left_sections: list[str] = []
    for sid in left_modern_ids:
        if sid == "skills":
            modern_left_sections.append(_sec_compact("Skills", _skills_bullet_columns_html(2)))
        else:
            inner = section_map.get(sid, "")
            if inner.strip():
                modern_left_sections.append(_sec_compact(_section_label(sid), inner))

    modern_body = (
        f"<div class='cv-paper modern {icons_class}'>"
        "<div class='modern-grid'>"
        "<aside class='modern-left'>"
        f"<h1 id='cv-name'{name_hidden_attr}>{name}</h1>"
        + (
            f"<p class='cv-title' id='cv-title'>{title}</p>"
            if title
            else "<p class='cv-title' id='cv-title' style='display:none'></p>"
        )
        + _modern_contact_stack()
        + "".join(modern_left_sections)
        + "</aside>"
        "<main class='modern-right'>"
        + (
            _sec("Professional Summary", section_map.get("summary", ""))
            if vis.get("summary", True)
            else ""
        )
        + _ordered_sections([sid for sid in right_modern_ids if sid != "summary"], compact=False)
        + "</main>"
        + "</div></div>"
    )

    # Creative (CVReviewer-like light/colored sidebar)
    left_pref_creative = {"skills", "languages", "interests"}
    right_creative_ids = [
        sid
        for sid in order
        if sid not in left_pref_creative and sid != "personal" and vis.get(sid, True)
    ]
    left_creative_ids = [sid for sid in order if sid in left_pref_creative and vis.get(sid, True)]
    creative_left_sections: list[str] = []
    for sid in left_creative_ids:
        if sid == "skills":
            creative_left_sections.append(_sec_compact("Skills", _skills_bullet_columns_html(2)))
        else:
            inner = section_map.get(sid, "")
            if inner.strip():
                creative_left_sections.append(_sec_compact(_section_label(sid), inner))

    creative_body = (
        f"<div class='cv-paper creative {icons_class}'>"
        "<div class='creative-grid'>"
        "<aside class='creative-left'>"
        f"<h1 id='cv-name'{name_hidden_attr}>{name}</h1>"
        + (
            f"<p class='cv-title' id='cv-title'>{title}</p>"
            if title
            else "<p class='cv-title' id='cv-title' style='display:none'></p>"
        )
        + _modern_contact_stack()
        + "".join(creative_left_sections)
        + "</aside>"
        "<main class='creative-right'>"
        + (_sec("About Me", section_map.get("summary", "")) if vis.get("summary", True) else "")
        + _ordered_sections([sid for sid in right_creative_ids if sid != "summary"], compact=False)
        + "</main>"
        + "</div></div>"
    )

    selected_body = classic_body
    if tpl == "modern":
        selected_body = modern_body
    elif tpl == "creative":
        selected_body = creative_body

    live_section_order = json.dumps([sid for sid in order if sid != "personal"])

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
.classic {{ padding:18px 38px; }}
.cv-head.center {{ text-align:center; margin-bottom:8px; }}
#cv-name {{ margin:0; font-size:{_sx(max(20, fs + 8))}px; font-weight:800; color:{primary}; line-height:1.1; }}
.cv-title {{ margin:3px 0 0; color:{muted}; font-size:{_sx(fs)}px; line-height:1.2; }}
.cv-contact {{ margin:5px 0 0; color:{muted}; font-size:{_sx(fs_xs)}px; line-height:1.28; display:flex; flex-direction:column; align-items:center; gap:2px; }}
.cv-contact-row {{ display:flex; align-items:center; justify-content:center; gap:0 1px; flex-wrap:wrap; }}
.ci-wrapper {{ display:inline-flex; align-items:center; min-width:0; flex-shrink:1; }}
.ci-item {{ display:inline-flex; align-items:center; gap:4px; vertical-align:middle; }}
.ci-sep {{ opacity:.75; margin:0 3px; }}
.ci-ico {{ width:{_sx(max(9, fs_xs + 1))}px; height:{_sx(max(9, fs_xs + 1))}px; display:inline-flex; color:currentColor; flex:0 0 auto; }}
.ci-ico svg {{ width:100%; height:100%; display:block; }}
.ci-val {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:{_sx(170)}px; }}
.ci-link {{ color:{link_color}; text-decoration:underline; text-decoration-thickness:1px; text-underline-offset:2px; }}
.ci-link:hover {{ filter:brightness(1.05); }}
.icons-off .ci-ico {{ display:none !important; }}
.cv-sec {{ margin-top:{max(7, es)}px; }}
.cv-sec-h {{
  margin:0 0 5px;
  font-size:{_sx(fs_xs)}px;
  text-transform:uppercase;
  letter-spacing:1px;
  font-weight:800;
  color:{primary};
  border-bottom:1.5px solid {primary};
  padding-bottom:3px;
}}
.cv-sec-compact .cv-sec-h {{
  border-bottom:1px solid {primary};
  font-size:{_sx(max(7, fs_xs - 1))}px;
  margin-bottom:4px;
}}
.cv-entry {{ margin:0 0 {max(5, es - 1)}px; }}
.row-top {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-end; }}
.role {{ font-size:{_sx(fs)}px; font-weight:700; }}
.dr {{ font-size:{_sx(fs_xs)}px; color:{muted}; white-space:nowrap; }}
.row-sub {{ font-size:{_sx(fs_xs)}px; color:{muted}; margin-top:1px; font-style:italic; }}
.cv-ul {{ margin:3px 0 0 14px; padding:0; }}
.cv-ul li {{ margin:1px 0; font-size:{_sx(fs_xs)}px; line-height:{lh}; }}
.cv-p {{ margin:0 0 3px; font-size:{_sx(fs_xs)}px; line-height:{lh}; color:{text}; }}
.cv-link {{ margin:2px 0 0; font-size:{_sx(fs_xs)}px; color:{link_color}; word-break:break-word; }}
.kv {{ display:flex; justify-content:space-between; gap:8px; margin:0 0 3px; font-size:{_sx(fs_xs)}px; line-height:{lh}; }}
.skills-grid {{
  margin:0;
  padding-left:14px;
  display:grid;
  gap:2px 14px;
}}
.skills-grid li {{
  margin:0;
  font-size:{_sx(fs_xs)}px;
  line-height:{lh};
  break-inside:avoid;
}}
.skills-cols-2 {{ grid-template-columns:repeat(2, minmax(0, 1fr)); }}
.skills-cols-3 {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }}

/* Modern template */
.modern .modern-grid {{ display:grid; grid-template-columns: 32% 68%; }}
.modern-left {{
  background:{primary};
  color:#ffffff;
  padding:16px 14px;
  border-right:1px solid {line};
}}
.modern-left #cv-name {{ color:#ffffff; font-size:{_sx(max(18, fs + 7))}px; }}
.modern-left .cv-title {{ color:#dbeafe; }}
.contact-stack {{ margin-top:8px; }}
.contact-stack p {{
  margin:0 0 4px;
  font-size:{_sx(fs_xs)}px;
  line-height:{lh};
  color:inherit;
  word-break:break-word;
}}
.contact-item {{ display:flex; align-items:flex-start; gap:6px; }}
.modern-left .cv-sec {{ margin-top:{max(6, es - 1)}px; }}
.modern-left .cv-sec-h {{
  color:#ffffff;
  border-bottom:1px solid rgba(255,255,255,0.45);
}}
.modern-left .cv-p, .modern-left .kv, .modern-left .row-sub {{ color:#eff6ff; }}
.modern-left .skills-grid li {{ color:#eff6ff; }}
.modern-left .ci-val {{ color:#ffffff; }}
.modern-left .ci-link {{ color:#ffffff; text-decoration-color:rgba(255,255,255,0.75); }}
.modern-left .ci-link:hover {{ color:#ffffff; filter:none; }}
.modern-right {{ padding:14px 16px; }}

/* Creative template */
.creative .creative-grid {{ display:grid; grid-template-columns: 30% 70%; }}
.creative-left {{
  background:{primary_soft};
  border-right:2px solid {primary};
  padding:14px 12px;
}}
.creative-left #cv-name {{ font-size:{_sx(max(18, fs + 7))}px; color:{primary}; }}
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
</style>
</head>
<body>
{selected_body}
<script>
function setRealtimeIcons(on) {{
  var papers = document.querySelectorAll('.cv-paper');
  for (var i = 0; i < papers.length; i++) {{
    papers[i].classList.toggle('icons-on', !!on);
    papers[i].classList.toggle('icons-off', !on);
  }}
}}

var __liveSectionOrder = {live_section_order};
var __liveSectionRank = (function() {{
  var out = {{}};
  for (var i = 0; i < __liveSectionOrder.length; i++) out[__liveSectionOrder[i]] = i;
  return out;
}})();

function updateClassicSeps() {{
  var rows = document.querySelectorAll('#cv-contact .cv-contact-row');
  for (var r = 0; r < rows.length; r++) {{
    var wrappers = rows[r].querySelectorAll('.ci-wrapper');
    var firstVisible = true;
    var anyInRow = false;
    for (var i = 0; i < wrappers.length; i++) {{
      if (wrappers[i].style.display === 'none') continue;
      anyInRow = true;
      var sep = wrappers[i].querySelector('.ci-sep');
      if (sep) sep.style.display = firstVisible ? 'none' : '';
      firstVisible = false;
    }}
    rows[r].style.display = anyInRow ? '' : 'none';
  }}
  var contact = document.getElementById('cv-contact');
  if (contact) {{
    var allVisibleWrappers = contact.querySelectorAll('.ci-wrapper');
    var anyVis = false;
    for (var j = 0; j < allVisibleWrappers.length; j++) {{
      if (allVisibleWrappers[j].style.display !== 'none') {{ anyVis = true; break; }}
    }}
    contact.style.display = anyVis ? '' : 'none';
  }}
}}

function coerceContactHref(raw) {{
  var v = String(raw || '').trim();
  if (!v) return '';
  var lower = v.toLowerCase();
  if (lower.indexOf('http://') === 0 || lower.indexOf('https://') === 0 || lower.indexOf('mailto:') === 0 || lower.indexOf('tel:') === 0) {{
    return v;
  }}
  return 'https://' + v.replace(/^\\/+/, '');
}}

var __contactTextByField = {{}};
var __contactLinkByField = {{
  linkedin: '',
  website: '',
  github: ''
}};

function normalizeContactLink(cf, rawText, rawLink) {{
  var text = String(rawText || '').trim();
  var link = String(rawLink || '').trim();
  var href = '';
  if (link) {{
    href = coerceContactHref(link);
  }}
  return {{ text: text, href: href }};
}}

function setContactField(cf, v) {{
  __contactTextByField[cf] = String(v || '');
  var wrapper = document.querySelector('#cv-contact .ci-wrapper[data-cf="' + cf + '"]');
  var linkData = normalizeContactLink(cf, v, __contactLinkByField[cf] || '');
  var isLinkField = (cf === 'linkedin' || cf === 'website' || cf === 'github');
  var textValue = isLinkField ? linkData.text : String(v || '').trim();
  if (wrapper) {{
    var valEl = wrapper.querySelector('.ci-val');
    if (isLinkField && valEl) {{
      if (linkData.href && valEl.tagName !== 'A') {{
        var linkEl = document.createElement('a');
        linkEl.className = valEl.className;
        linkEl.setAttribute('data-cf', cf);
        linkEl.setAttribute('target', '_blank');
        linkEl.setAttribute('rel', 'noopener noreferrer');
        valEl.replaceWith(linkEl);
        valEl = linkEl;
      }} else if (!linkData.href && valEl.tagName === 'A') {{
        var spanEl = document.createElement('span');
        spanEl.className = valEl.className;
        spanEl.setAttribute('data-cf', cf);
        valEl.replaceWith(spanEl);
        valEl = spanEl;
      }}
    }}
    if (valEl) {{
      valEl.textContent = textValue;
      if (isLinkField && valEl.tagName === 'A') {{
        if (linkData.href) valEl.setAttribute('href', linkData.href);
        else valEl.removeAttribute('href');
      }}
    }}
    wrapper.style.display = textValue ? '' : 'none';
    updateClassicSeps();
  }}
  var item = document.querySelector('.contact-item[data-cf="' + cf + '"]');
  if (item) {{
    var valEl2 = item.querySelector('.ci-val');
    if (isLinkField && valEl2) {{
      if (linkData.href && valEl2.tagName !== 'A') {{
        var linkEl2 = document.createElement('a');
        linkEl2.className = valEl2.className;
        linkEl2.setAttribute('data-cf', cf);
        linkEl2.setAttribute('target', '_blank');
        linkEl2.setAttribute('rel', 'noopener noreferrer');
        valEl2.replaceWith(linkEl2);
        valEl2 = linkEl2;
      }} else if (!linkData.href && valEl2.tagName === 'A') {{
        var spanEl2 = document.createElement('span');
        spanEl2.className = valEl2.className;
        spanEl2.setAttribute('data-cf', cf);
        valEl2.replaceWith(spanEl2);
        valEl2 = spanEl2;
      }}
    }}
    if (valEl2) {{
      valEl2.textContent = textValue;
      if (isLinkField && valEl2.tagName === 'A') {{
        if (linkData.href) valEl2.setAttribute('href', linkData.href);
        else valEl2.removeAttribute('href');
      }}
    }}
    item.style.display = textValue ? '' : 'none';
  }}
}}

function setContactLink(cf, rawLink) {{
  __contactLinkByField[cf] = String(rawLink || '').trim();
  setContactField(cf, __contactTextByField[cf] || '');
}}

function __liveSectionTitle(key, label) {{
  if (key.indexOf('cvb_exp_') === 0) return 'WORK EXPERIENCE';
  if (key.indexOf('cvb_edu_') === 0) return 'EDUCATION';
  if (key.indexOf('cvb_skill_') === 0) return 'SKILLS';
  if (key.indexOf('cvb_proj_') === 0) return 'PROJECTS';
  if (key.indexOf('cvb_lang_') === 0) return 'LANGUAGES';
  if (key.indexOf('cvb_cert_') === 0) return 'CERTIFICATIONS';
  if (key.indexOf('cvb_interest_') === 0 || key.indexOf('cvb_interests') === 0) return 'INTERESTS';
  if (key === 'cvb_summary') return 'PROFESSIONAL SUMMARY';
  return (label || 'DETAILS').toUpperCase();
}}

function __liveSectionIdForKey(key) {{
  if (key.indexOf('cvb_exp_') === 0) return 'experience';
  if (key.indexOf('cvb_edu_') === 0) return 'education';
  if (key.indexOf('cvb_skill_') === 0) return 'skills';
  if (key.indexOf('cvb_proj_') === 0) return 'projects';
  if (key.indexOf('cvb_lang_') === 0) return 'languages';
  if (key.indexOf('cvb_cert_') === 0) return 'certifications';
  if (key.indexOf('cvb_interest_') === 0 || key.indexOf('cvb_interests') === 0) return 'interests';
  if (key === 'cvb_summary') return 'summary';
  return '';
}}

function __liveTargetRoot(paper) {{
  return paper.querySelector('.modern-right, .creative-right') || paper;
}}

function __liveEnterUserMode(clearDemo) {{
  var paper = document.querySelector('.cv-paper');
  if (!paper) return null;
  if (!paper.dataset.liveUserMode && clearDemo) {{
    var demoSections = paper.querySelectorAll('.cv-sec, .cv-sec-compact');
    for (var i = 0; i < demoSections.length; i++) demoSections[i].remove();
  }}
  if (!paper.dataset.liveUserMode) paper.dataset.liveUserMode = '1';
  var target = __liveTargetRoot(paper);
  var root = target.querySelector('#cv-live-root');
  if (!root) {{
    root = document.createElement('div');
    root.id = 'cv-live-root';
    target.appendChild(root);
  }}
  return root;
}}

function __liveUpsertField(key, label, value) {{
  var personalKeys = {{
    cvb_full_name: 1,
    cvb_prof_title: 1,
    cvb_email: 1,
    cvb_phone: 1,
    cvb_location: 1,
    cvb_website: 1,
    cvb_linkedin: 1,
    cvb_github: 1,
    cvb_website_url: 1,
    cvb_linkedin_url: 1,
    cvb_github_url: 1
  }};
  if (personalKeys[key]) return;

  var root = __liveEnterUserMode(true);
  if (!root) return;
  var sectionId = __liveSectionIdForKey(key);
  var rank = (sectionId && Object.prototype.hasOwnProperty.call(__liveSectionRank, sectionId))
    ? __liveSectionRank[sectionId]
    : 999;
  var secId = __liveSectionTitle(key, label).toLowerCase().replace(/[^a-z0-9]+/g, '-');
  var sec = root.querySelector('[data-live-sec="' + secId + '"]');
  if (!sec) {{
    sec = document.createElement('section');
    sec.className = 'cv-sec';
    sec.setAttribute('data-live-sec', secId);
    sec.setAttribute('data-live-rank', String(rank));
    sec.innerHTML = "<h2 class='cv-sec-h'>" + __liveSectionTitle(key, label) + "</h2><div class='cv-live-lines'></div>";
    var inserted = false;
    var children = root.querySelectorAll('[data-live-sec]');
    for (var ci = 0; ci < children.length; ci++) {{
      var childRank = parseInt(children[ci].getAttribute('data-live-rank') || '999', 10);
      if (rank < childRank) {{
        root.insertBefore(sec, children[ci]);
        inserted = true;
        break;
      }}
    }}
    if (!inserted) root.appendChild(sec);
  }}
  var lines = sec.querySelector('.cv-live-lines');
  if (!lines) return;

  var val = (value || '').trim();
  var line = lines.querySelector('[data-live-key="' + key + '"]');
  if (!val) {{
    if (line) line.remove();
    if (!lines.children.length) sec.remove();
    return;
  }}
  if (!line) {{
    line = document.createElement('p');
    line.className = 'cv-p';
    line.setAttribute('data-live-key', key);
    lines.appendChild(line);
  }}
  var cleanLabel = (label || key).replace(/\\s+/g, ' ').trim();
  line.textContent = cleanLabel + ': ' + val;
}}

updateClassicSeps();

window.addEventListener('message', function(ev) {{
  var d = ev.data;
  if (!d) return;
  if (d.type === 'cv-rt-user-mode') {{
    __liveEnterUserMode(true);
    return;
  }}
  if (d.type === 'cv-rt-widget') {{
    __liveUpsertField(String(d.key || ''), String(d.label || ''), String(d.value || ''));
    return;
  }}
  if (d.type === 'cv-rt-icons-toggle') {{
    setRealtimeIcons(!!d.on);
    return;
  }}
  if (d.type !== 'cv-rt-update') return;

  var el, val;
  if (d.field === 'cvb_full_name') {{
    el = document.getElementById('cv-name');
    if (el) {{
      val = (d.value || '').trim();
      el.textContent = val;
      el.style.display = val ? '' : 'none';
    }}
    return;
  }}
  if (d.field === 'cvb_prof_title') {{
    el = document.getElementById('cv-title');
    if (el) {{
      val = (d.value || '').trim();
      el.textContent = val;
      el.style.display = val ? '' : 'none';
    }}
    return;
  }}
  if (d.field === 'cvb_summary') {{
    el = document.getElementById('cv-summary');
    if (el) {{
      val = (d.value || '').trim();
      el.textContent = val;
      el.style.display = val ? '' : 'none';
    }} else {{
      __liveUpsertField('cvb_summary', 'Professional Summary', String(d.value || ''));
    }}
    return;
  }}
  var keyMap = {{
    cvb_email: 'email',
    cvb_phone: 'phone',
    cvb_location: 'location',
    cvb_website: 'website',
    cvb_linkedin: 'linkedin',
    cvb_github: 'github'
  }};
  if (keyMap[d.field]) {{
    setContactField(keyMap[d.field], (d.value || '').trim());
    return;
  }}
  var linkKeyMap = {{
    cvb_website_url: 'website',
    cvb_linkedin_url: 'linkedin',
    cvb_github_url: 'github'
  }};
  if (linkKeyMap[d.field]) {{
    setContactLink(linkKeyMap[d.field], (d.value || '').trim());
  }}
}});
</script>
</body>
</html>"""


def _render_template_component(current_tpl: str, is_dark: bool) -> None:
    """Render template-selection cards as a custom HTML component.

    Keep the left bar compact (same style as before), while preview shows the template demo.
    """
    bg = "#1e293b" if is_dark else "#ffffff"
    bg_hover = "#334155" if is_dark else "#f8fbff"
    bg_active = "#1e3a5f" if is_dark else "rgba(59,130,246,0.12)"
    border = "#334155" if is_dark else "#d3dce8"
    border_act = "rgba(96,165,250,0.6)" if is_dark else "rgba(59,130,246,0.55)"
    text_main = "#f1f5f9" if is_dark else "#0f172a"
    text_act = "#bfdbfe" if is_dark else "#2563eb"
    text_sub = "#94a3b8" if is_dark else "#64748b"
    text_sub_act = "#93c5fd" if is_dark else "#2563eb"

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
    card_count = max(1, len(TEMPLATE_CHOICES))
    comp_h = 10 + (card_count * 58) + ((card_count - 1) * 8)
    components.html(html, height=comp_h, scrolling=False)
