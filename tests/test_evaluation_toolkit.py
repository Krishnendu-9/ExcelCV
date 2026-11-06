"""The evaluation toolkit benchmarks the computed score, never a model output.

What this protects: the README, the toolkit's labels and the Evaluation Toolkit page say
the toolkit compares ExcelCV's computed score with human reviewer scores, and that Gemini
sets no score. That holds because render_evaluation_toolkit() records the analysis's
match_score, and analyze_cv_with_gemini() sets match_score from the scoring code's final
score, ignoring the model's own match_score and subscores.

The test runs a real analysis against two mocked model responses that disagree on every
score, records a human score from each report, and checks the toolkit stored the same
score both times. If it fails, the toolkit now measures something the model controls:
either restore the computed score or correct the README, the toolkit's labels and the
Evaluation Toolkit page.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.ui import report
from tests.test_report_scores_computed import _analyze


def _model_response(score: int) -> str:
    return json.dumps(
        {
            "match_score": score,
            "strengths": ["Python"],
            "missing_skills": [],
            "suggestions": [],
            "missing_keywords": [],
            "subscores": {
                "skills_alignment": score,
                "experience_alignment": score,
                "ats_readiness": score,
            },
        }
    )


def _record_human_score(analysis: dict, human_score: int = 60) -> dict:
    """Submit the toolkit's form once and return the record it stored."""
    fake_st = MagicMock()
    fake_st.session_state = {}
    fake_st.number_input.return_value = human_score
    fake_st.text_input.return_value = ""
    fake_st.form_submit_button.return_value = True
    fake_st.columns.side_effect = lambda n, **_: [MagicMock() for _ in range(n)]
    with patch.object(report, "st", fake_st):
        report.render_evaluation_toolkit(analysis, "resume.pdf")
    records = fake_st.session_state.get("evaluation_records", [])
    assert len(records) == 1, f"expected one stored record, found {len(records)}"
    return records[0]


class EvaluationToolkitScoreTests(unittest.TestCase):
    def test_recorded_score_does_not_depend_on_the_model(self) -> None:
        low = _record_human_score(_analyze(_model_response(1)))
        high = _record_human_score(_analyze(_model_response(99)))
        self.assertEqual(
            low["model_score"],
            high["model_score"],
            "the toolkit's score changed with the model's response",
        )

    def test_recorded_score_is_the_reports_match_score(self) -> None:
        analysis = _analyze(_model_response(99))
        record = _record_human_score(analysis)
        self.assertEqual(record["model_score"], analysis["match_score"])
        self.assertEqual(record["human_score"], 60)


if __name__ == "__main__":
    unittest.main()
