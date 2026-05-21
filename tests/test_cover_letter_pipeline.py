import unittest
from dataclasses import dataclass
from unittest.mock import patch

from src.cover_letter.models import CoverLetterDraft
from src.cover_letter.service import generate_cover_letter
from src.cover_letter.validators import validate_form_inputs


@dataclass
class FakeUpload:
    name: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)

    def getvalue(self) -> bytes:
        return self.data


class CoverLetterPipelineTests(unittest.TestCase):
    def test_validate_form_inputs_rejects_unsupported_extension(self) -> None:
        with self.assertRaises(ValueError):
            validate_form_inputs(
                job_title="Software Engineer",
                company_name="Acme",
                uploaded_file_name="resume.txt",
                cv_text="A" * 200,
            )

    def test_generate_cover_letter_orchestrates_pipeline(self) -> None:
        cv_text = (
            "Jane Doe\njane.doe@example.com\n+91 9876543210\nKolkata, India\n"
            "Experience\nDeveloped APIs and improved latency by 30%.\n"
        ) + ("Skills Python SQL " * 20)
        draft = CoverLetterDraft(
            subject="Application for Software Engineer",
            greeting="Dear Hiring Manager,",
            paragraphs=[
                "I am excited to apply for the Software Engineer role.",
                "My experience includes backend API development and optimization.",
                "I would value the opportunity to contribute at Acme.",
            ],
            closing="Sincerely,",
            signature_name="Jane Doe",
        )

        uploaded = FakeUpload(name="Jane-Doe Resume.pdf", data=b"%PDF-1.4 test")

        with (
            patch("src.cover_letter.service.extract_cv_text", return_value=cv_text),
            patch(
                "src.cover_letter.service.calculate_contact_info",
                return_value={
                    "found": [
                        {"type": "email", "value": "jane.doe@example.com"},
                        {"type": "phone", "value": "+91 9876543210"},
                        {"type": "location", "value": "Kolkata, India"},
                    ]
                },
            ),
            patch(
                "src.cover_letter.service.generate_cover_letter_draft", return_value=draft
            ) as m_gen,
            patch("src.cover_letter.service.build_cover_letter_docx", return_value=b"DOCX-BYTES"),
        ):
            result = generate_cover_letter(
                uploaded_cv=uploaded,
                job_title="Software Engineer",
                company_name="Acme Inc",
                job_description="Backend, Python, SQL",
                additional_information="Open source work",
                application_source="LinkedIn",
            )

        self.assertEqual(result.docx_bytes, b"DOCX-BYTES")
        self.assertIn("cover_letter_", result.file_name)
        self.assertTrue(result.file_name.endswith(".docx"))
        self.assertIn("Application for Software Engineer", result.full_text)

        req = m_gen.call_args[0][0]
        self.assertEqual(req.candidate_name, "Jane Doe")
        self.assertEqual(req.candidate_email, "jane.doe@example.com")
        self.assertEqual(req.candidate_phone, "+91 9876543210")
        self.assertEqual(req.candidate_location, "Kolkata, India")


if __name__ == "__main__":
    unittest.main()
