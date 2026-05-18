"""PDF rendering helpers for the CV builder."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

from src.ui.cv_builder_constants import A4_HEIGHT_PX, A4_WIDTH_PX


def _build_pdf_ready_html(preview_html: str) -> str:
    """Wrap preview HTML with print-specific CSS so PDF mirrors preview styles."""
    if not preview_html:
        return "<html><body></body></html>"
    print_css = """
@page { size: A4; margin: 0; }
html, body {
  margin: 0 !important;
  padding: 0 !important;
  background: #ffffff !important;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
body { width: 210mm; min-height: 297mm; }
.cv-paper {
  width: 210mm !important;
  min-height: 297mm !important;
  margin: 0 !important;
  border: 0 !important;
  box-shadow: none !important;
}
"""
    if "</style>" in preview_html:
        return preview_html.replace("</style>", f"{print_css}\n</style>", 1)
    if "</head>" in preview_html:
        return preview_html.replace("</head>", f"<style>{print_css}</style></head>", 1)
    return f"<html><head><style>{print_css}</style></head><body>{preview_html}</body></html>"


def _render_html_to_pdf_bytes(html: str) -> bytes:
    """Render HTML to PDF using headless Chromium for WYSIWYG template fidelity."""
    if sys.platform.startswith("win"):
        return _render_html_to_pdf_bytes_windows_subprocess(html)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(
            "PDF engine unavailable. Install Playwright and Chromium: "
            "'py -3 -m pip install playwright' then 'py -3 -m playwright install chromium'."
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": A4_WIDTH_PX, "height": A4_HEIGHT_PX})
        page.set_content(html, wait_until="load")
        page.emulate_media(media="screen")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
        )
        browser.close()
    return pdf_bytes


def _render_html_to_pdf_bytes_windows_subprocess(html: str) -> bytes:
    """Windows-safe Playwright PDF rendering in a child process.

    Streamlit/tornado can run with a selector loop on Windows where asyncio
    subprocess transport is unsupported. Running Playwright in a fresh process
    avoids that loop-policy conflict.
    """
    html_path = ""
    pdf_path = ""
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as f:
            f.write(html)
            html_path = f.name
        with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
            pdf_path = f.name

        py_script = (
            "import sys, pathlib, asyncio\n"
            "try:\n"
            "    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())\n"
            "except Exception:\n"
            "    pass\n"
            "from playwright.sync_api import sync_playwright\n"
            "html = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
            "outp = pathlib.Path(sys.argv[2])\n"
            "with sync_playwright() as p:\n"
            "    browser = p.chromium.launch(headless=True)\n"
            f"    page = browser.new_page(viewport={{'width': {A4_WIDTH_PX}, 'height': {A4_HEIGHT_PX}}})\n"
            "    page.set_content(html, wait_until='load')\n"
            "    page.emulate_media(media='screen')\n"
            "    page.pdf(format='A4', print_background=True, prefer_css_page_size=True, margin={'top':'0mm','right':'0mm','bottom':'0mm','left':'0mm'}, path=str(outp))\n"
            "    browser.close()\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", py_script, html_path, pdf_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"Playwright PDF process failed. {detail}")
        return pathlib.Path(pdf_path).read_bytes()
    finally:
        for p in (html_path, pdf_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
