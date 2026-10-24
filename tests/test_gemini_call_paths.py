"""Every path to the Gemini API checks input length, then the per-user rate limit,
before any API setup."""

import re
import unittest
from unittest.mock import MagicMock, patch

from src import gemini_client
from src.cover_letter import generator, page
from src.cover_letter.models import CoverLetterRequest
from tests.repo_files import REPO_ROOT

_SDK_CALL = re.compile(r"\.generate_content\(|GenerativeModel\(|\.list_models\(")

# Every module that talks to the Gemini SDK, and the public entry points through which
# the app reaches it. Adding a call site elsewhere fails this test on purpose: audit
# the new path for length validation, the rate limit and sign-in before adding it here.
_SDK_MODULES = {"src/gemini_client.py", "src/cover_letter/generator.py"}


def _limited(*_args, **_kwargs):
    raise RuntimeError("AI request rate limit reached for this session.")


def _cover_letter(**overrides) -> CoverLetterRequest:
    fields = {"cv_text": "CV body. " * 20, "job_title": "Engineer", "company_name": "Acme"}
    fields.update(overrides)
    return CoverLetterRequest(**fields)


class CallSiteInventoryTests(unittest.TestCase):
    def test_only_the_audited_modules_call_the_sdk(self) -> None:
        found = set()
        for path in (REPO_ROOT / "src").rglob("*.py"):
            if _SDK_CALL.search(path.read_text(encoding="utf-8")):
                found.add(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(found, _SDK_MODULES)


class RateLimitBeforeApiSetupTests(unittest.TestCase):
    """The limiter runs before the API key is read, for every entry point."""

    def _assert_blocked_before_api(self, call, module) -> None:
        get_key = MagicMock(return_value="test-key")
        with (
            patch.object(gemini_client, "_enforce_gemini_rate_limit", side_effect=_limited),
            patch.object(module, "get_api_key", get_key),
            patch.object(module, "genai", MagicMock()),
        ):
            with self.assertRaisesRegex(RuntimeError, "rate limit"):
                call()
        get_key.assert_not_called()

    def test_analysis(self) -> None:
        self._assert_blocked_before_api(
            lambda: gemini_client.analyze_cv_with_gemini("CV body.", "JD."), gemini_client
        )

    def test_cover_letter(self) -> None:
        self._assert_blocked_before_api(
            lambda: generator.generate_cover_letter_draft(_cover_letter()), generator
        )

    def test_bullet_suggestions(self) -> None:
        self._assert_blocked_before_api(
            lambda: gemini_client.suggest_cv_bullets("Engineer", "Acme"), gemini_client
        )


class LengthCheckBeforeRateLimitTests(unittest.TestCase):
    """Over-long input is rejected with a message and does not spend a rate-limit slot."""

    def _assert_rejected_without_slot(self, call) -> None:
        limiter = MagicMock()
        with patch.object(gemini_client, "_enforce_gemini_rate_limit", limiter):
            with self.assertRaises(ValueError):
                call()
        limiter.assert_not_called()

    def test_analysis(self) -> None:
        with patch.object(gemini_client, "_MAX_JD_INPUT_CHARS", 1000):
            self._assert_rejected_without_slot(
                lambda: gemini_client.analyze_cv_with_gemini("CV body.", "j" * 1001)
            )

    def test_cover_letter(self) -> None:
        self._assert_rejected_without_slot(
            lambda: generator.generate_cover_letter_draft(_cover_letter(job_title="t" * 121))
        )

    def test_bullet_suggestions(self) -> None:
        self._assert_rejected_without_slot(
            lambda: gemini_client.suggest_cv_bullets("r" * 121, "Acme")
        )


class CoverLetterIsMeteredTests(unittest.TestCase):
    def setUp(self) -> None:
        gemini_client._REQUEST_BUCKETS.clear()
        self.addCleanup(gemini_client._REQUEST_BUCKETS.clear)

    def test_real_limiter_stops_the_third_cover_letter(self) -> None:
        get_key = MagicMock(return_value="test-key")
        with (
            patch.object(gemini_client, "_request_actor_key", return_value="user:u1"),
            patch.object(gemini_client, "_GEMINI_MAX_REQUESTS_PER_WINDOW", 2),
            patch.object(gemini_client, "_GEMINI_WINDOW_SECONDS", 60),
            patch.object(generator, "get_api_key", get_key),
            patch.object(generator, "genai", MagicMock()),
            patch.object(generator, "_generate_json", side_effect=RuntimeError("stop")),
        ):
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError, "Could not generate"):
                    generator.generate_cover_letter_draft(_cover_letter())
            with self.assertRaisesRegex(RuntimeError, "rate limit reached"):
                generator.generate_cover_letter_draft(_cover_letter())
        self.assertEqual(get_key.call_count, 2)

    def test_analysis_and_cover_letters_share_one_budget(self) -> None:
        with (
            patch.object(gemini_client, "_request_actor_key", return_value="user:u1"),
            patch.object(gemini_client, "_GEMINI_MAX_REQUESTS_PER_WINDOW", 1),
            patch.object(gemini_client, "_GEMINI_WINDOW_SECONDS", 60),
            patch.object(gemini_client, "get_api_key", return_value=""),
        ):
            with self.assertRaisesRegex(RuntimeError, "GOOGLE_API_KEY"):
                gemini_client.analyze_cv_with_gemini("CV body.", "JD.")  # spends the slot
            with self.assertRaisesRegex(RuntimeError, "rate limit reached"):
                generator.generate_cover_letter_draft(_cover_letter())


class CoverLetterSignInGateTests(unittest.TestCase):
    def test_guest_gets_sign_in_prompt_and_no_form(self) -> None:
        fake_st = MagicMock()
        fake_st.session_state = {}
        # Enough of Streamlit for the full form to render if the gate were missing, so
        # a missing gate fails on the assertions below rather than on a mock error.
        fake_st.columns.side_effect = lambda spec, **_k: [
            MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))
        ]
        fake_st.button.return_value = False
        with (
            patch.object(page, "get_session_user", return_value=None),
            patch.object(page, "st", fake_st),
            patch.object(page, "components", MagicMock()),
            patch.object(page, "_load_user_saved_cvs", return_value=[]),
            patch("src.ui.app_utils.st", fake_st),
            patch.object(page, "generate_cover_letter") as generate,
        ):
            page.render_cover_letter_page()

        rendered = " ".join(str(c.args[0]) for c in fake_st.markdown.call_args_list if c.args)
        self.assertIn("Sign in to generate a cover letter", rendered)
        self.assertIn("page=auth", rendered)
        self.assertIn("next=cover-letter", rendered)
        fake_st.file_uploader.assert_not_called()
        fake_st.button.assert_not_called()
        fake_st.text_input.assert_not_called()
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
