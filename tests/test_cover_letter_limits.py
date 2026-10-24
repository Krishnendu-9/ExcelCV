"""Cover-letter free-text fields are capped and rejected with a message, never cut."""

import unittest
from unittest.mock import MagicMock, patch

from src import gemini_client, prompt_fence
from src.cover_letter import generator, service, validators
from src.cover_letter.models import CoverLetterRequest

_DELIM = "0123456789abcdef"

# field name on CoverLetterRequest -> (label in the error message, cap)
_FIELDS = {
    "job_title": ("Job title", validators.MAX_JOB_TITLE_CHARS),
    "company_name": ("Company name", validators.MAX_COMPANY_NAME_CHARS),
    "application_source": ("Application source", validators.MAX_APPLICATION_SOURCE_CHARS),
    "additional_information": ("Additional information", validators.MAX_ADDITIONAL_INFO_CHARS),
}


def _request(**overrides) -> CoverLetterRequest:
    fields = {
        "cv_text": "CV body. " * 20,
        "job_title": "Software Engineer",
        "company_name": "Acme Inc",
        "job_description": "Backend role.",
        "additional_information": "",
        "application_source": "",
        "candidate_name": "Jane Doe",
    }
    fields.update(overrides)
    return CoverLetterRequest(**fields)


class _MockedGeneration:
    """Patch every outbound step so no API is called; record what was reached."""

    def __enter__(self):
        self.get_api_key = MagicMock(return_value="test-key")
        self.genai = MagicMock()
        self.generate = MagicMock(side_effect=RuntimeError("stop before the model"))
        self.rate_limit = MagicMock()
        self._patches = [
            patch.object(generator, "get_api_key", self.get_api_key),
            patch.object(generator, "genai", self.genai),
            patch.object(generator, "_generate_json", self.generate),
            patch.object(gemini_client, "_enforce_gemini_rate_limit", self.rate_limit),
            patch.object(prompt_fence, "new_delimiter", return_value=_DELIM),
        ]
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in reversed(self._patches):
            p.stop()
        return False


class FieldCapTests(unittest.TestCase):
    def test_caps_fit_what_each_field_is_for(self) -> None:
        self.assertEqual(validators.MAX_JOB_TITLE_CHARS, 120)
        self.assertEqual(validators.MAX_COMPANY_NAME_CHARS, 120)
        self.assertEqual(validators.MAX_APPLICATION_SOURCE_CHARS, 100)
        self.assertEqual(validators.MAX_ADDITIONAL_INFO_CHARS, 2000)
        self.assertEqual(validators.MAX_CANDIDATE_NAME_CHARS, 60)

    def test_each_field_over_its_cap_is_rejected_before_any_api_setup(self) -> None:
        for field, (label, cap) in _FIELDS.items():
            with self.subTest(field=field), _MockedGeneration() as mocked:
                with self.assertRaisesRegex(ValueError, f"^{label} is too long \\({cap + 1} "):
                    generator.generate_cover_letter_draft(_request(**{field: "x" * (cap + 1)}))
                mocked.rate_limit.assert_not_called()  # a rejected input spends no slot
                mocked.get_api_key.assert_not_called()
                mocked.genai.configure.assert_not_called()
                mocked.generate.assert_not_called()

    def test_a_megabyte_of_additional_information_is_rejected(self) -> None:
        with _MockedGeneration() as mocked:
            with self.assertRaisesRegex(ValueError, "Additional information is too long"):
                generator.generate_cover_letter_draft(
                    _request(additional_information="x" * 1_000_000)
                )
            mocked.generate.assert_not_called()

    def test_each_field_at_its_cap_is_accepted_whole(self) -> None:
        for field, (_label, cap) in _FIELDS.items():
            value = "y" * cap
            with self.subTest(field=field), _MockedGeneration() as mocked:
                with self.assertRaisesRegex(RuntimeError, "Could not generate"):
                    generator.generate_cover_letter_draft(_request(**{field: value}))
                mocked.rate_limit.assert_called_once()
                prompt = mocked.generate.call_args_list[0].args[1]
                self.assertIn(value, prompt)

    def test_prompt_builder_bounds_fields_even_without_validation(self) -> None:
        req = _request(
            job_title="t" * 5000,
            company_name="c" * 5000,
            application_source="s" * 5000,
            additional_information="a" * 50000,
            candidate_name="n" * 5000,
        )
        prompt = generator._build_prompt(req, _DELIM)
        self.assertIn("t" * validators.MAX_JOB_TITLE_CHARS, prompt)
        self.assertNotIn("t" * (validators.MAX_JOB_TITLE_CHARS + 1), prompt)
        self.assertNotIn("c" * (validators.MAX_COMPANY_NAME_CHARS + 1), prompt)
        self.assertNotIn("s" * (validators.MAX_APPLICATION_SOURCE_CHARS + 1), prompt)
        self.assertNotIn("a" * (validators.MAX_ADDITIONAL_INFO_CHARS + 1), prompt)
        self.assertNotIn("n" * (validators.MAX_CANDIDATE_NAME_CHARS + 1), prompt)


class CandidateNameTests(unittest.TestCase):
    def test_overlong_file_name_falls_back_to_candidate(self) -> None:
        self.assertEqual(service._guess_candidate_name("", "x" * 5000 + ".pdf"), "Candidate")

    def test_normal_file_name_is_still_used(self) -> None:
        self.assertEqual(
            service._guess_candidate_name("", "jane_doe_resume.pdf"), "Jane Doe Resume"
        )


class WorstCaseRequestTests(unittest.TestCase):
    def test_prompt_is_bounded_by_template_plus_caps(self) -> None:
        cv_cap = gemini_client.DEFAULT_MAX_CV_INPUT_CHARS
        jd_cap = 40000
        with (
            patch.object(gemini_client, "_MAX_CV_INPUT_CHARS", cv_cap),
            patch.object(gemini_client, "_MAX_JD_INPUT_CHARS", jd_cap),
        ):
            empty = generator._build_prompt(
                CoverLetterRequest(cv_text="", job_title="", company_name=""), _DELIM
            )
            worst = generator._build_prompt(
                _request(
                    cv_text="c" * cv_cap,
                    job_description="j" * jd_cap,
                    job_title="t" * validators.MAX_JOB_TITLE_CHARS,
                    company_name="o" * validators.MAX_COMPANY_NAME_CHARS,
                    application_source="s" * validators.MAX_APPLICATION_SOURCE_CHARS,
                    additional_information="a" * validators.MAX_ADDITIONAL_INFO_CHARS,
                    candidate_name="n" * validators.MAX_CANDIDATE_NAME_CHARS,
                ),
                _DELIM,
            )
        fields = (
            cv_cap
            + jd_cap
            + validators.MAX_JOB_TITLE_CHARS
            + validators.MAX_COMPANY_NAME_CHARS
            + validators.MAX_APPLICATION_SOURCE_CHARS
            + validators.MAX_ADDITIONAL_INFO_CHARS
            + 2 * validators.MAX_CANDIDATE_NAME_CHARS  # the name appears twice
        )
        self.assertLessEqual(len(worst), len(empty) + fields)
        self.assertGreater(len(worst), cv_cap + jd_cap)


if __name__ == "__main__":
    unittest.main()
