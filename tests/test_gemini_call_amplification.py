"""How many Gemini API calls one rate-limited request can make (docs/KNOWN_ISSUES.md §2).

This pins current, unfixed behaviour. If you change the fallback chain, these counts
change: update the table in docs/KNOWN_ISSUES.md §2 together with this test.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from src import config, gemini_client
from src.cover_letter import generator
from src.cover_letter.models import CoverLetterRequest
from tests.repo_files import REPO_ROOT

_TRANSIENT = "503 service unavailable"
_QUOTA = "429 resource exhausted"
_DISTINCT_MODEL = "models/gemini-distinct-test-model"


def _failing_genai(message: str) -> tuple[MagicMock, MagicMock]:
    """A fake SDK whose every generate_content call fails with *message*."""
    model = MagicMock()
    model.generate_content.side_effect = Exception(message)
    genai = MagicMock()
    genai.GenerativeModel.return_value = model
    return genai, model


def _expect_failure(call) -> None:
    """Run *call*, which must fail once every model in the chain has failed."""
    try:
        call()
    except Exception:
        return
    raise AssertionError("expected the request to fail after the fallback chain")


def _env(distinct_model: bool):
    env = patch.dict(os.environ, {}, clear=False)
    env.start()
    os.environ.pop("GEMINI_MODEL", None)
    if distinct_model:
        os.environ["GEMINI_MODEL"] = _DISTINCT_MODEL
    return env


def _analysis_calls(message: str, distinct_model: bool) -> int:
    genai, model = _failing_genai(message)
    env = _env(distinct_model)
    try:
        with (
            patch.object(gemini_client, "genai", genai),
            patch.object(gemini_client, "get_api_key", return_value="test-key"),
            patch.object(gemini_client, "_enforce_gemini_rate_limit"),
            patch.object(gemini_client, "_pick_model_id", return_value="models/auto-picked"),
            patch("src.gemini_client.time.sleep"),
        ):
            _expect_failure(lambda: gemini_client.analyze_cv_with_gemini("CV body.", "JD."))
    finally:
        env.stop()
    return model.generate_content.call_count


def _cover_letter_calls(message: str, distinct_model: bool) -> int:
    genai, model = _failing_genai(message)
    env = _env(distinct_model)
    req = CoverLetterRequest(cv_text="CV body. " * 20, job_title="Engineer", company_name="Acme")
    try:
        with (
            patch.object(generator, "genai", genai),
            patch.object(generator, "get_api_key", return_value="test-key"),
            patch.object(gemini_client, "_enforce_gemini_rate_limit"),
            patch("src.cover_letter.generator.time.sleep"),
        ):
            _expect_failure(lambda: generator.generate_cover_letter_draft(req))
    finally:
        env.stop()
    return model.generate_content.call_count


class CallAmplificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = (REPO_ROOT / "docs" / "KNOWN_ISSUES.md").read_text(encoding="utf-8")

    def _assert_documented(self, default: int, distinct: int) -> None:
        self.assertIn(f"{default}, or {distinct} with a distinct `GEMINI_MODEL`", self.doc)

    def test_four_built_in_models(self) -> None:
        env = _env(distinct_model=False)
        try:
            self.assertEqual(len(config.preferred_models()), 4)
        finally:
            env.stop()
        self.assertIn("four built-in models", self.doc)

    def test_analysis_on_transient_errors(self) -> None:
        default, distinct = _analysis_calls(_TRANSIENT, False), _analysis_calls(_TRANSIENT, True)
        self.assertEqual((default, distinct), (10, 12))
        self._assert_documented(default, distinct)

    def test_analysis_on_quota_errors(self) -> None:
        default, distinct = _analysis_calls(_QUOTA, False), _analysis_calls(_QUOTA, True)
        self.assertEqual((default, distinct), (5, 6))
        self._assert_documented(default, distinct)

    def test_cover_letter_on_any_error(self) -> None:
        for message in (_TRANSIENT, _QUOTA):
            with self.subTest(message=message):
                default = _cover_letter_calls(message, False)
                distinct = _cover_letter_calls(message, True)
                self.assertEqual((default, distinct), (8, 10))
                self._assert_documented(default, distinct)


if __name__ == "__main__":
    unittest.main()
