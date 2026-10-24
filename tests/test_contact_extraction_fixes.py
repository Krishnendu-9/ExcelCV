import unittest
from unittest.mock import patch

from src.pdf_utils import extract_pdf_text
from src.services.scoring import calculate_contact_info


class _FakeUpload:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw
        self.name = "resume.pdf"
        self.size = len(raw)

    def getvalue(self) -> bytes:
        return self._raw


class _FakeAnnotRef:
    def __init__(self, uri: str) -> None:
        self._uri = uri

    def get_object(self):
        return {"/A": {"/URI": self._uri}}


class _FakePage:
    def __init__(self, text: str, uris: list[str]) -> None:
        self._text = text
        self._uris = uris

    def extract_text(self) -> str:
        return self._text

    def get(self, key: str):
        if key == "/Annots":
            return [_FakeAnnotRef(uri) for uri in self._uris]
        return None


class _FakeReader:
    def __init__(self) -> None:
        self.is_encrypted = False
        self.pages = [
            _FakePage(
                "Krishnendu Ghosh\nthisiskrishnendughosh @gmail.com\nGitHub\nJava\n",
                [
                    "mailto:thisiskrishnendughosh@gmail.com",
                    "tel:+91 6289862288",
                    "https://www.linkedin.com/in/krishnendughoshh",
                    "https://www.udemy.com/certificate/example",
                ],
            )
        ]


class ContactExtractionFixTests(unittest.TestCase):
    def test_contact_info_detects_spaced_email_and_avoids_github_false_positive(self) -> None:
        cv_text = (
            "Krishnendu Ghosh\n"
            "thisiskrishnendughosh @gmail.com\n"
            "GitHub\n"
            "Java\n"
            "+91 6289862288\n"
        )
        info = calculate_contact_info(cv_text)
        found_types = {row["type"]: row["value"] for row in info["found"]}

        self.assertEqual(found_types.get("email"), "thisiskrishnendughosh@gmail.com")
        self.assertEqual(found_types.get("phone"), "+91 6289862288")
        self.assertNotIn("github", found_types)

    def test_extract_pdf_text_appends_contact_annotation_uris(self) -> None:
        upload = _FakeUpload(b"%PDF-1.7 fake")

        with patch("src.pdf_utils.PdfReader", return_value=_FakeReader()):
            text = extract_pdf_text(upload)

        self.assertIn("thisiskrishnendughosh@gmail.com", text)
        self.assertIn("+91 6289862288", text)
        self.assertIn("https://www.linkedin.com/in/krishnendughoshh", text)
        self.assertNotIn("udemy.com/certificate", text)


if __name__ == "__main__":
    unittest.main()
