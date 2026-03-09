import unittest
from unittest.mock import patch

from src.pdf_utils import extract_pdf_text, parse_confidence_chip


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReaderOK:
    def __init__(self, _uploaded_file) -> None:
        self.pages = [_FakePage("First page text"), _FakePage("Second page text")]


class _FakeReaderEmpty:
    def __init__(self, _uploaded_file) -> None:
        self.pages = [_FakePage(""), _FakePage("")]


class PdfUtilsTests(unittest.TestCase):
    @patch("src.pdf_utils.PdfReader", _FakeReaderOK)
    def test_extract_pdf_text_success(self) -> None:
        text = extract_pdf_text(uploaded_file=object())
        self.assertIn("First page text", text)
        self.assertIn("Second page text", text)

    @patch("src.pdf_utils.PdfReader", _FakeReaderEmpty)
    def test_extract_pdf_text_raises_for_non_extractable_pdf(self) -> None:
        with self.assertRaises(ValueError):
            extract_pdf_text(uploaded_file=object())

    def test_parse_confidence_chip(self) -> None:
        label_good, cls_good = parse_confidence_chip("a" * 900)
        self.assertIn("text layer detected", label_good.lower())
        self.assertEqual(cls_good, "chip")

        label_warn, cls_warn = parse_confidence_chip("short text")
        self.assertIn("low text extraction", label_warn.lower())
        self.assertIn("chip-warn", cls_warn)


if __name__ == "__main__":
    unittest.main()
