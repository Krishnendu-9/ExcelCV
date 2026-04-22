"""CV text extraction helpers used by upload and scoring flows."""

from pathlib import Path
import re
from io import BytesIO
import zipfile
import xml.etree.ElementTree as ET

from PyPDF2 import PdfReader

_MIN_PARSE_TEXT_CHARS = 800


def extract_pdf_text(uploaded_file) -> str:
    """Return concatenated text from all PDF pages or raise on failure."""
    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)
        text_chunks = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text_chunks.append(text)
        combined = "\n".join(text_chunks).strip()
        if not combined:
            raise ValueError("PDF contained no extractable text.")
        return combined
    except Exception as exc:  # pragma: no cover - Streamlit UI path
        raise ValueError("Could not read this PDF.") from exc


def extract_docx_text(uploaded_file) -> str:
    """Return concatenated text from DOCX content or raise on failure."""
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover - environment/config path
        raise ValueError("DOCX support is not installed. Please install python-docx.") from exc

    def _clean_line(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    def _add_line(buffer: list[str], seen: set[str], text: str) -> None:
        line = _clean_line(text)
        if line and line not in seen:
            seen.add(line)
            buffer.append(line)

    def _collect_table_text(table, buffer: list[str], seen: set[str]) -> None:
        for row in getattr(table, "rows", []):
            for cell in getattr(row, "cells", []):
                for paragraph in getattr(cell, "paragraphs", []):
                    _add_line(buffer, seen, getattr(paragraph, "text", ""))

    def _collect_docx_xml_text(raw_docx: bytes, buffer: list[str], seen: set[str]) -> None:
        """Fallback extractor for DOCX XML parts (captures w:t and drawing text a:t)."""
        try:
            with zipfile.ZipFile(BytesIO(raw_docx)) as archive:
                names = sorted(
                    name
                    for name in archive.namelist()
                    if name.startswith("word/") and name.endswith(".xml")
                )
                for name in names:
                    xml_bytes = archive.read(name)
                    try:
                        root = ET.fromstring(xml_bytes)
                    except ET.ParseError:
                        continue
                    for node in root.iter():
                        tag = str(node.tag)
                        # WordprocessingML text + DrawingML text (often used by text boxes/shapes).
                        if tag.endswith("}t") and node.text:
                            _add_line(buffer, seen, node.text)
        except zipfile.BadZipFile:
            return

    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        raw_docx = uploaded_file.read() if hasattr(uploaded_file, "read") else b""
        if not raw_docx:
            raise ValueError("DOCX contained no extractable text.")
        try:
            document = Document(BytesIO(raw_docx))
        except Exception:
            # Some valid DOCX variants may fail python-docx parsing; attempt raw XML extraction.
            lines: list[str] = []
            seen: set[str] = set()
            _collect_docx_xml_text(raw_docx, lines, seen)
            combined = "\n".join(lines).strip()
            if combined:
                return combined
            raise

        lines: list[str] = []
        seen: set[str] = set()

        # 1) Standard body paragraphs.
        for paragraph in getattr(document, "paragraphs", []):
            _add_line(lines, seen, getattr(paragraph, "text", ""))

        # 2) Tables in body (common in resume templates).
        for table in getattr(document, "tables", []):
            _collect_table_text(table, lines, seen)

        # 3) Header/footer text.
        for section in getattr(document, "sections", []):
            header = getattr(section, "header", None)
            footer = getattr(section, "footer", None)
            if header is not None:
                for paragraph in getattr(header, "paragraphs", []):
                    _add_line(lines, seen, getattr(paragraph, "text", ""))
                for table in getattr(header, "tables", []):
                    _collect_table_text(table, lines, seen)
            if footer is not None:
                for paragraph in getattr(footer, "paragraphs", []):
                    _add_line(lines, seen, getattr(paragraph, "text", ""))
                for table in getattr(footer, "tables", []):
                    _collect_table_text(table, lines, seen)

        # 4) Fallback: raw XML text nodes (helps with some textbox-heavy layouts).
        if not lines:
            for node in document.element.xpath(".//w:t"):
                _add_line(lines, seen, getattr(node, "text", ""))

        # 4b) Fallback for drawing/text-box text (a:t) and all word/*.xml parts.
        if not lines:
            _collect_docx_xml_text(raw_docx, lines, seen)

        # 5) Extra fallback: header/footer XML relationship parts via python-docx rels.
        if not lines:
            for rel in document.part.rels.values():
                reltype = str(getattr(rel, "reltype", "")).lower()
                if not (reltype.endswith("/header") or reltype.endswith("/footer")):
                    continue
                part = getattr(rel, "target_part", None)
                element = getattr(part, "element", None)
                if element is None:
                    continue
                for node in element.xpath(".//w:t"):
                    _add_line(lines, seen, getattr(node, "text", ""))

        combined = "\n".join(lines).strip()
        if not combined:
            raise ValueError("DOCX contained no extractable text.")
        return combined
    except Exception as exc:  # pragma: no cover - Streamlit UI path
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Could not read this DOCX file.") from exc


def extract_cv_text(uploaded_file, file_name: str = "") -> str:
    """Extract text from a supported CV file (PDF or DOCX)."""
    candidate_name = file_name or getattr(uploaded_file, "name", "")
    ext = Path(candidate_name).suffix.lower()
    if ext == ".pdf":
        return extract_pdf_text(uploaded_file)
    if ext == ".docx":
        return extract_docx_text(uploaded_file)
    raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")


def parse_confidence_chip(cv_text: str, file_ext: str = ".pdf") -> tuple[str, str]:
    """Return a short parse confidence label and CSS class for a chip."""
    ext = (file_ext or ".pdf").lower()
    source = "DOCX" if ext == ".docx" else "PDF"
    if len(cv_text.strip()) >= _MIN_PARSE_TEXT_CHARS:
        return (f"Parse: text extracted ({source})", "chip")
    return (f"Parse: low text extraction (check {source})", "chip chip-warn")

