"""Pure value normalization and escaping helpers for CV builder."""
from __future__ import annotations

from src.ui.cv_builder_constants import (
    SECTION_ID_TO_LABEL,
    SECTION_IDS,
    SECTION_LABEL_TO_ID,
    TEMPLATE_CONFIGS,
    TEMPLATE_DEFAULT_ZOOM,
)


def _normalize_template(template: str | None) -> str:
    value = (template or "").strip().lower()
    if value == "minimal":
        return "creative"
    if value in TEMPLATE_CONFIGS:
        return value
    return "classic"


def _default_zoom_for_template(template: str | None) -> int:
    return TEMPLATE_DEFAULT_ZOOM.get(_normalize_template(template), 100)


def _section_id(value: str) -> str | None:
    if value in SECTION_ID_TO_LABEL:
        return value
    return SECTION_LABEL_TO_ID.get(value)


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return default


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
            normalized[sid] = _coerce_bool(value, True)
    return normalized


def _safe_int(value: object, default: int) -> int:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def _safe_float(value: object, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_attr_escape(s: str) -> str:
    return _html_escape(s).replace('"', "&quot;").replace("'", "&#x27;")


def _coerce_href(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    low = value.lower()
    if low.startswith(("http://", "https://", "mailto:", "tel:")):
        return value
    return f"https://{value.lstrip('/')}"


def _normalize_contact_link(field: str, value: str, explicit_url: str = "") -> tuple[str, str]:
    raw_text = str(value or "").strip()
    raw_url = str(explicit_url or "").strip()
    if not raw_text and not raw_url:
        return "", ""

    def _trim_scheme(v: str) -> str:
        out = v.strip()
        low = out.lower()
        if low.startswith("https://"):
            return out[8:]
        if low.startswith("http://"):
            return out[7:]
        return out

    display = raw_text
    href = ""

    if raw_url:
        href = _coerce_href(raw_url)
        if not display:
            display = _trim_scheme(raw_url).replace("www.", "")

    return display, href


def _date_range(start: str, end: str, current: bool = False) -> str:
    end_label = "Present" if current else end
    if start and end_label:
        return f"{start} - {end_label}"
    return start or end_label or ""
