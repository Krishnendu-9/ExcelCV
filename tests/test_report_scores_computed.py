"""Every analysis carries a computed Sections and ATS Essentials score.

What this protects: the README says Gemini "sets no score on the report page". That
holds only because render_report_page() in src/ui/report.py never reaches its two
subscore fallbacks:

    sections_metrics.get("score", subs.get("experience_alignment", score))
    ats_essentials_metrics.get("score", subs.get("ats_readiness", score))

If analyze_cv_with_gemini() ever returned an analysis without either score, the report
would silently show the model's experience_alignment or ats_readiness subscore as the
Sections or ATS Essentials percentage, and the README would be false. Those fallbacks
stay unreachable for saved analyses too, because every version of the function since
analyses were first saved has always written both scores.

So if this test fails, do not just make it pass: either keep both scores unconditional,
or remove the fallbacks and correct the README sentence.

Only these two scores are pinned, and only that each is present, numeric and computed
by the scoring code rather than taken from the model. The rest of the analysis dict is
free to change.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from src import gemini_client
from src.services.scoring import calculate_ats_essentials, calculate_sections

_CV = """Jane Doe
jane@example.com | +1 555 0100 | linkedin.com/in/janedoe

Summary
Backend engineer with five years of Python and cloud experience.

Experience
Senior Engineer, Acme Corp, 2021 - Present
- Built a FastAPI service handling 2 million requests a day.
- Cut deployment time by 40% by moving CI to GitHub Actions.

Education
BSc Computer Science, State University, 2019

Skills
Python, FastAPI, PostgreSQL, Docker, AWS
"""

_JD = "Backend engineer with Python, FastAPI, Docker and AWS experience."

# Values a model might return for the two metrics; none of them may reach the report.
_MODEL_SECTIONS_SCORE = 7
_MODEL_ATS_SCORE = 3

_FULL_RESPONSE = json.dumps(
    {
        "match_score": 99,
        "strengths": ["Python"],
        "missing_skills": ["Kubernetes"],
        "suggestions": ["Add metrics"],
        "missing_keywords": ["terraform"],
        "subscores": {"skills_alignment": 11, "experience_alignment": 12, "ats_readiness": 13},
        "content_metrics": {"ats_parse_rate": 1},
        "sections_metrics": {"score": _MODEL_SECTIONS_SCORE, "details": {}},
        "ats_essentials_metrics": {"score": _MODEL_ATS_SCORE, "details": {}},
        "tailoring_metrics": {"score": 5, "details": {}},
    }
)


def _analyze(response_text: str, job_desc: str = _JD) -> dict:
    """Run a real analysis with the Gemini SDK replaced by one fixed response."""
    model = MagicMock()
    model.generate_content.return_value = MagicMock(text=response_text)
    genai = MagicMock()
    genai.GenerativeModel.return_value = model
    with (
        patch.object(gemini_client, "genai", genai),
        patch.object(gemini_client, "get_api_key", return_value="test-key"),
        patch.object(gemini_client, "_enforce_gemini_rate_limit"),
        patch.object(gemini_client, "_pick_model_id", return_value="models/auto-picked"),
        patch("src.gemini_client.time.sleep"),
    ):
        try:
            return gemini_client.analyze_cv_with_gemini(_CV, job_desc)
        finally:
            assert model.generate_content.called, "the mocked model was never called"


class ComputedMetricScoreTests(unittest.TestCase):
    def _assert_computed_scores(self, analysis: dict) -> None:
        sections = analysis.get("sections_metrics")
        ats = analysis.get("ats_essentials_metrics")
        self.assertIsInstance(sections, dict, "sections_metrics missing")
        self.assertIsInstance(ats, dict, "ats_essentials_metrics missing")
        self.assertIn("score", sections, "sections_metrics has no score")
        self.assertIn("score", ats, "ats_essentials_metrics has no score")
        for name, value in (("sections", sections["score"]), ("ats_essentials", ats["score"])):
            with self.subTest(metric=name):
                self.assertIsInstance(value, int)
                self.assertNotIsInstance(value, bool)
        self.assertEqual(sections["score"], calculate_sections(_CV)[0])
        self.assertEqual(ats["score"], calculate_ats_essentials(_CV)[0])

    def test_model_returns_every_metric_block(self) -> None:
        analysis = _analyze(_FULL_RESPONSE)
        self._assert_computed_scores(analysis)
        self.assertNotEqual(analysis["sections_metrics"]["score"], _MODEL_SECTIONS_SCORE)
        self.assertNotEqual(analysis["ats_essentials_metrics"]["score"], _MODEL_ATS_SCORE)

    def test_model_returns_none_of_the_metric_blocks(self) -> None:
        self._assert_computed_scores(_analyze(json.dumps({"match_score": 50})))

    def test_model_returns_an_empty_object(self) -> None:
        self._assert_computed_scores(_analyze("{}"))

    def test_model_returns_text_that_is_not_json(self) -> None:
        self._assert_computed_scores(_analyze("I'm sorry, I can't help with that."))

    def test_model_returns_json_that_is_not_an_object(self) -> None:
        self._assert_computed_scores(_analyze("[1, 2, 3]"))

    def test_model_returns_metric_blocks_of_the_wrong_type(self) -> None:
        malformed = json.dumps(
            {"sections_metrics": "high", "ats_essentials_metrics": None, "subscores": "n/a"}
        )
        self._assert_computed_scores(_analyze(malformed))

    def test_without_a_job_description(self) -> None:
        self._assert_computed_scores(_analyze(_FULL_RESPONSE, job_desc=""))

    def test_empty_model_responses_raise_rather_than_return_a_partial_analysis(self) -> None:
        with self.assertRaises(RuntimeError):
            _analyze("")


if __name__ == "__main__":
    unittest.main()
