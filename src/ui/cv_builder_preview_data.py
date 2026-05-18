"""Preview/demo data helpers for the CV builder."""
from __future__ import annotations


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
            "github": "github.com/yourprofile",
            "website_url": "https://yourwebsite.dev",
            "linkedin_url": "https://www.linkedin.com/in/yourprofile",
            "github_url": "https://github.com/yourprofile",
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
    for key, value in row.items():
        # Internal row ids should never count as user content.
        if str(key).strip().lower() == "id":
            continue
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
    """Merge user CV data over demo defaults for preview-only rendering."""
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
    for field in [
        "full_name",
        "prof_title",
        "email",
        "phone",
        "location",
        "linkedin",
        "website",
        "github",
        "linkedin_url",
        "website_url",
        "github_url",
        "summary",
    ]:
        if str(personal.get(field, "")).strip():
            return False

    for key in ["experience", "education", "projects", "certifications", "languages"]:
        rows = cv_data.get(key, []) or []
        for row in rows:
            if _row_has_meaningful_data(row):
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
