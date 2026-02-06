from typing import Tuple

from PyPDF2 import PdfReader


def extract_pdf_text(uploaded_file) -> str:
    """Return concatenated text from all PDF pages or raise on failure."""
    try:
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


def parse_confidence_chip(cv_text: str) -> Tuple[str, str]:
    """Return a short parse confidence label and CSS class for a chip."""
    if len(cv_text.strip()) >= 800:
        return ("Parse: text layer detected", "chip")
    return ("Parse: low text extraction (check PDF)", "chip chip-warn")

