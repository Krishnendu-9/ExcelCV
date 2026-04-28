"""Full CV Builder page for the Streamlit app."""

from __future__ import annotations

import uuid
from typing import Any
import streamlit as st
import streamlit.components.v1 as components

from src.auth_utils import get_session_user
from src.database import CV, get_db
from src.services.pdf_generator import generate_cv_pdf

# ─── Session-state key helpers ──────────────────────────────────────────────

def _ss(key: str, default: Any = "") -> Any:
    return st.session_state.get(key, default)


def _init_builder() -> None:
    """Seed session-state keys with empty defaults if not already set."""
    defaults = {
        "cvb_cv_title": "My Resume",
        "cvb_template": "classic",
        "cvb_loaded_cv_id": None,
        # personal
        "cvb_full_name": "", "cvb_email": "", "cvb_phone": "",
        "cvb_location": "", "cvb_website": "", "cvb_linkedin": "",
        "cvb_github": "", "cvb_summary": "",
        # list ids
        "cvb_exp_ids": [], "cvb_edu_ids": [],
        "cvb_proj_ids": [], "cvb_cert_ids": [],
        "cvb_skill_cat_ids": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def collect_cv_data() -> dict:
    """Read all builder widgets from session_state into a CV data dict."""
    ss = st.session_state

    personal = {
        "full_name": ss.get("cvb_full_name", ""),
        "email":     ss.get("cvb_email", ""),
        "phone":     ss.get("cvb_phone", ""),
        "location":  ss.get("cvb_location", ""),
        "website":   ss.get("cvb_website", ""),
        "linkedin":  ss.get("cvb_linkedin", ""),
        "github":    ss.get("cvb_github", ""),
        "summary":   ss.get("cvb_summary", ""),
    }

    experience = []
    for eid in ss.get("cvb_exp_ids", []):
        bullet_count = ss.get(f"cvb_exp_bcount_{eid}", 1)
        bullets = [ss.get(f"cvb_exp_b_{eid}_{i}", "") for i in range(bullet_count)]
        experience.append({
            "id": eid,
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
        skills_cats.append({
            "id":    sid,
            "name":  ss.get(f"cvb_skill_name_{sid}", ""),
            "items": items,
        })

    projects = []
    for pid in ss.get("cvb_proj_ids", []):
        projects.append({
            "id":          pid,
            "name":        ss.get(f"cvb_proj_name_{pid}", ""),
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

    return {
        "personal":       personal,
        "experience":     experience,
        "education":      education,
        "skills":         {"categories": skills_cats},
        "projects":       projects,
        "certifications": certifications,
    }


def load_cv_into_builder(cv_record: CV) -> None:
    """Populate builder session-state from a saved CV record."""
    d = cv_record.data or {}
    ss = st.session_state
    ss["cvb_cv_title"]     = cv_record.title
    ss["cvb_template"]     = cv_record.template
    ss["cvb_loaded_cv_id"] = cv_record.id

    p = d.get("personal", {})
    for field in ["full_name","email","phone","location","website","linkedin","github","summary"]:
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
        ss[f"cvb_exp_bcount_{eid}"] = len(bullets) or 1
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


# ─── HTML template generator ─────────────────────────────────────────────────

def _html_escape(s: str) -> str:
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def _date_range(start: str, end: str, current: bool = False) -> str:
    end_label = "Present" if current else end
    if start and end_label:
        return f"{start} – {end_label}"
    return start or end_label or ""


TEMPLATE_CONFIGS = {
    "classic": {"primary": "#1a1a2e", "accent": "#16213e",  "link": "#2563eb", "rule": "#1a1a2e", "font": "Georgia, serif"},
    "modern":  {"primary": "#2563eb", "accent": "#1e3a5f",  "link": "#2563eb", "rule": "#2563eb", "font": "system-ui, sans-serif"},
    "minimal": {"primary": "#1f2937", "accent": "#6b7280",  "link": "#374151", "rule": "#d1d5db", "font": "'Helvetica Neue', sans-serif"},
}


def generate_cv_html(data: dict, template: str = "classic") -> str:
    cfg = TEMPLATE_CONFIGS.get(template, TEMPLATE_CONFIGS["classic"])
    p = data.get("personal", {})
    contacts = [p.get(f, "") for f in ["email","phone","location","website","linkedin","github"] if p.get(f)]

    def section(title: str, content: str) -> str:
        if not content.strip():
            return ""
        rule_color = cfg["rule"]
        primary    = cfg["primary"]
        return f"""
        <div style="margin-bottom:14px">
          <h2 style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                     color:{primary};margin:0 0 3px;border-bottom:1px solid #ccc;padding-bottom:3px;">{title}</h2>
          {content}
        </div>"""

    def exp_block(exp: dict) -> str:
        bullets_html = "".join(
            f'<p style="margin:1px 0 0 10px;font-size:10px;">• {_html_escape(b)}</p>'
            for b in exp.get("bullets", []) if b.strip()
        )
        dr = _html_escape(_date_range(exp.get("start_date",""), exp.get("end_date",""), exp.get("current", False)))
        return f"""
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <span style="font-size:11px;font-weight:700">{_html_escape(exp.get('role',''))}</span>
            <span style="font-size:9.5px;color:#666">{dr}</span>
          </div>
          <p style="margin:1px 0;font-size:10px;color:#444">
            {_html_escape(exp.get('company',''))}{(', ' + _html_escape(exp.get('location',''))) if exp.get('location') else ''}
          </p>
          {bullets_html}
        </div>"""

    def edu_block(edu: dict) -> str:
        deg = _html_escape(edu.get("degree",""))
        field = _html_escape(edu.get("field",""))
        gpa = edu.get("gpa","")
        degree_line = f"{deg}{', ' + field if field else ''}{' | GPA: ' + gpa if gpa else ''}"
        dr = _html_escape(_date_range(edu.get("start_date",""), edu.get("end_date","")))
        return f"""
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <span style="font-size:11px;font-weight:700">{_html_escape(edu.get('institution',''))}</span>
            <span style="font-size:9.5px;color:#666">{dr}</span>
          </div>
          <p style="margin:1px 0;font-size:10px;color:#444">{degree_line}</p>
        </div>"""

    experience_html  = "".join(exp_block(e) for e in data.get("experience", []))
    education_html   = "".join(edu_block(e) for e in data.get("education", []))

    skills_html = ""
    for cat in data.get("skills", {}).get("categories", []):
        items = cat.get("items", [])
        if items:
            skills_html += f'<p style="font-size:10.5px;margin:2px 0"><b>{_html_escape(cat.get("name",""))}</b>: {_html_escape(", ".join(items))}</p>'

    projects_html = ""
    for proj in data.get("projects", []):
        tech = proj.get("tech_stack", [])
        dr   = _html_escape(_date_range(proj.get("start_date",""), proj.get("end_date","")))
        projects_html += f"""
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <span style="font-size:11px;font-weight:700">{_html_escape(proj.get('name',''))}</span>
            <span style="font-size:9.5px;color:#666">{dr}</span>
          </div>
          {f'<p style="margin:1px 0;font-size:9.5px;font-style:italic;color:#555">Tech: {_html_escape(", ".join(tech))}</p>' if tech else ''}
          {f'<p style="margin:2px 0;font-size:10px">{_html_escape(proj.get("description",""))}</p>' if proj.get("description") else ''}
          {f'<p style="margin:1px 0;font-size:9px;color:{cfg["link"]}">{_html_escape(proj.get("link",""))}</p>' if proj.get("link") else ''}
        </div>"""

    certs_html = "".join(
        f'<p style="font-size:10.5px;margin:2px 0">• <b>{_html_escape(c.get("name",""))}</b>'
        f'{" — " + _html_escape(c.get("issuer","")) if c.get("issuer") else ""}'
        f'{" (" + _html_escape(c.get("date","")) + ")" if c.get("date") else ""}</p>'
        for c in data.get("certifications", [])
    )

    name    = _html_escape(p.get("full_name") or "Your Name")
    contact = _html_escape(" · ".join(contacts))
    summary = _html_escape(p.get("summary",""))

    modern_header = ""
    if template == "modern":
        modern_header = f"""
        <div style="background:{cfg['primary']};color:#fff;padding:18px 24px;margin:-20px -20px 14px;">
          <h1 style="font-size:22px;font-weight:800;margin:0;letter-spacing:-0.5px">{name}</h1>
          {f'<p style="font-size:9px;color:#bfdbfe;margin:4px 0 0">{contact}</p>' if contact else ''}
          {f'<p style="font-size:10px;color:#dbeafe;margin:8px 0 0;line-height:1.5">{summary}</p>' if summary else ''}
        </div>"""
        name_section = ""
        contact_section = ""
        summary_section = ""
    else:
        name_section = f'<h1 style="font-size:22px;font-weight:700;text-align:center;margin:0;color:{cfg["primary"]}">{name}</h1>'
        contact_section = f'<p style="text-align:center;font-size:9.5px;color:#666;margin:4px 0 10px">{contact}</p>' if contact else ""
        summary_section = section("Professional Summary", f'<p style="font-size:10.5px;line-height:1.5;margin:4px 0">{summary}</p>') if summary else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family:{cfg["font"]}; font-size:11px; color:#222;
    background:#fff; padding:20px; line-height:1.4;
  }}
  hr {{ border:none; border-top:1.5px solid {cfg["rule"]}; margin:6px 0 10px; }}
</style>
</head><body>
  {modern_header}
  {name_section}
  {contact_section}
  {f'<hr>' if template == "classic" and (name or contact) else ''}
  {summary_section}
  {section("Experience", experience_html)}
  {section("Education", education_html)}
  {section("Skills", skills_html)}
  {section("Projects", projects_html)}
  {section("Certifications", certs_html)}
</body></html>"""


# ─── Form sections ──────────────────────────────────────────────────────────

def _personal_section() -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Full Name", key="cvb_full_name", placeholder="Krishnendu Das")
        st.text_input("Email", key="cvb_email", placeholder="you@email.com")
        st.text_input("Phone", key="cvb_phone", placeholder="+91 98765 43210")
        st.text_input("Location", key="cvb_location", placeholder="Kolkata, India")
    with c2:
        st.text_input("Website / Portfolio", key="cvb_website", placeholder="https://yoursite.dev")
        st.text_input("LinkedIn", key="cvb_linkedin", placeholder="linkedin.com/in/you")
        st.text_input("GitHub", key="cvb_github", placeholder="github.com/you")
    st.text_area("Professional Summary", key="cvb_summary", height=120,
                 placeholder="3+ years experience in full-stack development…")


def _experience_section() -> None:
    if st.button("＋ Add Experience", key="btn_add_exp"):
        eid = str(uuid.uuid4())
        st.session_state["cvb_exp_ids"].append(eid)
        st.session_state[f"cvb_exp_bcount_{eid}"] = 1
        st.session_state[f"cvb_exp_b_{eid}_0"] = ""
        st.rerun()

    for idx, eid in enumerate(st.session_state.get("cvb_exp_ids", [])):
        role = st.session_state.get(f"cvb_exp_role_{eid}", "")
        label = role or f"Experience {idx + 1}"
        with st.expander(label, expanded=(idx == 0)):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Job Title", key=f"cvb_exp_role_{eid}", placeholder="Software Engineer")
                st.text_input("Company", key=f"cvb_exp_company_{eid}", placeholder="Google")
                st.text_input("Location", key=f"cvb_exp_loc_{eid}", placeholder="Bengaluru, India")
            with c2:
                st.text_input("Start Date", key=f"cvb_exp_start_{eid}", placeholder="Jan 2022")
                curr = st.checkbox("Currently working here", key=f"cvb_exp_curr_{eid}")
                if not curr:
                    st.text_input("End Date", key=f"cvb_exp_end_{eid}", placeholder="Dec 2024")

            st.markdown("**Achievements / Responsibilities**")
            bcount = st.session_state.get(f"cvb_exp_bcount_{eid}", 1)
            for i in range(bcount):
                st.text_input(f"Bullet {i+1}", key=f"cvb_exp_b_{eid}_{i}",
                              placeholder="Led a team that reduced API latency by 40%")

            bc1, bc2, bc3 = st.columns([1, 1, 2])
            with bc1:
                if st.button("＋ Bullet", key=f"add_b_{eid}"):
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount + 1
                    st.rerun()
            with bc2:
                if bcount > 1 and st.button("− Bullet", key=f"rem_b_{eid}"):
                    st.session_state[f"cvb_exp_bcount_{eid}"] = bcount - 1
                    st.rerun()
            with bc3:
                if st.button(f"🗑 Remove Experience", key=f"rem_exp_{eid}"):
                    st.session_state["cvb_exp_ids"].remove(eid)
                    st.rerun()


def _education_section() -> None:
    if st.button("＋ Add Education", key="btn_add_edu"):
        eid = str(uuid.uuid4())
        st.session_state["cvb_edu_ids"].append(eid)
        st.rerun()

    for idx, eid in enumerate(st.session_state.get("cvb_edu_ids", [])):
        inst = st.session_state.get(f"cvb_edu_inst_{eid}", "")
        with st.expander(inst or f"Education {idx + 1}", expanded=(idx == 0)):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Institution", key=f"cvb_edu_inst_{eid}", placeholder="MAKAUT, Kolkata")
                st.text_input("Degree", key=f"cvb_edu_degree_{eid}", placeholder="Master of Computer Applications")
                st.text_input("Field of Study", key=f"cvb_edu_field_{eid}", placeholder="Computer Science")
            with c2:
                st.text_input("Location", key=f"cvb_edu_loc_{eid}", placeholder="Kolkata, India")
                st.text_input("Start Year", key=f"cvb_edu_start_{eid}", placeholder="2022")
                st.text_input("End Year", key=f"cvb_edu_end_{eid}", placeholder="2024")
                st.text_input("GPA / Percentage", key=f"cvb_edu_gpa_{eid}", placeholder="8.5 / 10")

            if st.button(f"🗑 Remove", key=f"rem_edu_{eid}"):
                st.session_state["cvb_edu_ids"].remove(eid)
                st.rerun()


def _skills_section() -> None:
    st.caption("Create skill categories (e.g. 'Languages', 'Frameworks', 'Tools') and list items separated by commas.")
    if st.button("＋ Add Skill Category", key="btn_add_skill"):
        sid = str(uuid.uuid4())
        st.session_state["cvb_skill_cat_ids"].append(sid)
        st.rerun()

    for idx, sid in enumerate(st.session_state.get("cvb_skill_cat_ids", [])):
        name = st.session_state.get(f"cvb_skill_name_{sid}", "")
        with st.expander(name or f"Category {idx + 1}", expanded=True):
            st.text_input("Category Name", key=f"cvb_skill_name_{sid}", placeholder="Programming Languages")
            st.text_area("Skills (comma-separated)", key=f"cvb_skill_items_{sid}", height=80,
                         placeholder="Python, JavaScript, TypeScript, SQL")
            if st.button(f"🗑 Remove Category", key=f"rem_skill_{sid}"):
                st.session_state["cvb_skill_cat_ids"].remove(sid)
                st.rerun()


def _projects_section() -> None:
    if st.button("＋ Add Project", key="btn_add_proj"):
        pid = str(uuid.uuid4())
        st.session_state["cvb_proj_ids"].append(pid)
        st.rerun()

    for idx, pid in enumerate(st.session_state.get("cvb_proj_ids", [])):
        name = st.session_state.get(f"cvb_proj_name_{pid}", "")
        with st.expander(name or f"Project {idx + 1}", expanded=(idx == 0)):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Project Name", key=f"cvb_proj_name_{pid}", placeholder="ExcelCV")
                st.text_input("Tech Stack (comma-separated)", key=f"cvb_proj_tech_{pid}",
                              placeholder="Python, FastAPI, Next.js")
                st.text_input("Link (GitHub / Live)", key=f"cvb_proj_link_{pid}", placeholder="https://github.com/...")
            with c2:
                st.text_input("Start Date", key=f"cvb_proj_start_{pid}", placeholder="Jan 2024")
                st.text_input("End Date", key=f"cvb_proj_end_{pid}", placeholder="Mar 2024")
            st.text_area("Description", key=f"cvb_proj_desc_{pid}", height=80,
                         placeholder="AI-powered CV builder and ATS analyzer built with Gemini API.")
            if st.button(f"🗑 Remove Project", key=f"rem_proj_{pid}"):
                st.session_state["cvb_proj_ids"].remove(pid)
                st.rerun()


def _certifications_section() -> None:
    if st.button("＋ Add Certification", key="btn_add_cert"):
        cid = str(uuid.uuid4())
        st.session_state["cvb_cert_ids"].append(cid)
        st.rerun()

    for idx, cid in enumerate(st.session_state.get("cvb_cert_ids", [])):
        name = st.session_state.get(f"cvb_cert_name_{cid}", "")
        with st.expander(name or f"Certification {idx + 1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Certification Name", key=f"cvb_cert_name_{cid}", placeholder="AWS Solutions Architect")
                st.text_input("Issuer", key=f"cvb_cert_issuer_{cid}", placeholder="Amazon Web Services")
            with c2:
                st.text_input("Date", key=f"cvb_cert_date_{cid}", placeholder="June 2024")
                st.text_input("Credential URL", key=f"cvb_cert_link_{cid}", placeholder="https://...")
            if st.button(f"🗑 Remove", key=f"rem_cert_{cid}"):
                st.session_state["cvb_cert_ids"].remove(cid)
                st.rerun()


# ─── Save / load ─────────────────────────────────────────────────────────────

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
                cv.title    = title
                cv.template = template
                cv.data     = cv_data
                db.commit()
                return True
        cv = CV(user_id=user["id"], title=title, template=template, data=cv_data)
        db.add(cv)
        db.commit()
        db.refresh(cv)
        st.session_state["cvb_loaded_cv_id"] = cv.id
        return True
    finally:
        db.close()


# ─── Main page renderer ──────────────────────────────────────────────────────

def render_cv_builder_page() -> None:
    _init_builder()

    st.markdown(
        "<h2 style='margin-bottom:0.1rem'>📄 Resume Builder</h2>"
        "<p style='color:#94a3b8;margin-top:0'>Fill in your details — the preview updates automatically.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Top bar: title, template, actions ────────────────────────────────────
    top1, top2, top3, top4 = st.columns([2, 1.5, 1, 1])
    with top1:
        st.text_input("Resume Title", key="cvb_cv_title", placeholder="My Resume",
                      label_visibility="collapsed")
    with top2:
        st.selectbox("Template", ["classic", "modern", "minimal"], key="cvb_template",
                     label_visibility="collapsed",
                     format_func=lambda x: {"classic":"Classic","modern":"Modern","minimal":"Minimal"}[x])
    with top3:
        save_clicked = st.button("💾 Save", use_container_width=True, type="primary")
    with top4:
        export_clicked = st.button("📄 Export PDF", use_container_width=True)

    st.divider()

    # ── Main: form (left) + preview (right) ──────────────────────────────────
    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
        tabs = st.tabs(["👤 Personal", "💼 Experience", "🎓 Education",
                        "🔧 Skills", "📁 Projects", "🏆 Certifications"])
        with tabs[0]: _personal_section()
        with tabs[1]: _experience_section()
        with tabs[2]: _education_section()
        with tabs[3]: _skills_section()
        with tabs[4]: _projects_section()
        with tabs[5]: _certifications_section()

    with col_preview:
        st.markdown("**Live Preview**")
        cv_data  = collect_cv_data()
        template = st.session_state.get("cvb_template", "classic")
        html     = generate_cv_html(cv_data, template)
        components.html(html, height=860, scrolling=True)

    # ── Handle actions ────────────────────────────────────────────────────────
    if save_clicked:
        title = st.session_state.get("cvb_cv_title", "My Resume") or "My Resume"
        if _save_cv(cv_data, title, template):
            st.success("✅ CV saved to your account!")
        else:
            st.error("Save failed. Please try again.")

    if export_clicked:
        try:
            pdf_bytes = generate_cv_pdf(cv_data, template)
            title     = st.session_state.get("cvb_cv_title", "resume") or "resume"
            st.download_button(
                "⬇ Download PDF",
                data=pdf_bytes,
                file_name=f"{title.replace(' ','_')}.pdf",
                mime="application/pdf",
                key="download_pdf_btn",
            )
        except Exception as exc:
            st.error(f"PDF export failed: {exc}")
