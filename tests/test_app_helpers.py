import unittest
from unittest.mock import patch

from src.ui.app_utils import _sanitize_cv_filename
from src.ui.analysis_runner import run_multi_resume_comparison


class _FakeUpload:
    def __init__(self, name: str) -> None:
        self.name = name
        self.size = 1024


class AppHelperTests(unittest.TestCase):
    def test_sanitize_cv_filename_removes_path_segments_and_bad_chars(self) -> None:
        raw = "..\\folder/<my>:cv?.pdf\n"
        safe = _sanitize_cv_filename(raw)
        self.assertEqual(safe, "-my-cv-.pdf")

    def test_sanitize_cv_filename_fallback(self) -> None:
        self.assertEqual(_sanitize_cv_filename("   "), "CV.pdf")

    @patch("src.ui.analysis_runner._analyze_cv_payload")
    def test_multi_resume_comparison_sorts_by_final_score(self, mock_analyze) -> None:
        mock_analyze.side_effect = [
            (
                {
                    "match_score": 72,
                    "tailoring_metrics": {"score": 70},
                    "content_metrics": {"ats_parse_rate": 85},
                    "sections_metrics": {"score": 80},
                    "missing_skills": ["Docker"],
                },
                "text",
            ),
            (
                {
                    "match_score": 91,
                    "tailoring_metrics": {"score": 90},
                    "content_metrics": {"ats_parse_rate": 88},
                    "sections_metrics": {"score": 86},
                    "missing_skills": [],
                },
                "text",
            ),
        ]

        output = run_multi_resume_comparison(
            "Backend role with Python",
            [_FakeUpload("b.pdf"), _FakeUpload("a.pdf")],
        )

        rows = output["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Final Score"], 91)
        self.assertEqual(rows[0]["Resume"], "a.pdf")
        self.assertEqual(rows[1]["Final Score"], 72)

    def test_multi_resume_comparison_requires_at_least_two_files(self) -> None:
        with self.assertRaises(ValueError):
            run_multi_resume_comparison("JD", [_FakeUpload("single.pdf")])

    def test_multi_resume_comparison_limits_to_five_files(self) -> None:
        files = [_FakeUpload(f"{i}.pdf") for i in range(6)]
        with self.assertRaises(ValueError):
            run_multi_resume_comparison("JD", files)

    @patch("src.ui.analysis_runner._analyze_cv_payload")
    def test_multi_resume_comparison_handles_malformed_scores(self, mock_analyze) -> None:
        mock_analyze.side_effect = [
            (
                {
                    "match_score": "N/A",
                    "tailoring_metrics": {"score": None},
                    "content_metrics": {"ats_parse_rate": "bad"},
                    "sections_metrics": {"score": "86.9"},
                    "missing_skills": "Kubernetes",
                },
                "text",
            ),
            (
                {
                    "match_score": "55.2",
                    "tailoring_metrics": {"score": "44.9"},
                    "content_metrics": {"ats_parse_rate": "74"},
                    "sections_metrics": {"score": 61},
                    "missing_skills": ["Docker", "Docker", "CI/CD"],
                },
                "text",
            ),
        ]

        output = run_multi_resume_comparison(
            "Backend role with Python",
            [_FakeUpload("a.pdf"), _FakeUpload("b.pdf")],
        )

        rows = output["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Resume"], "b.pdf")
        self.assertEqual(rows[0]["Final Score"], 55)
        self.assertEqual(rows[1]["Final Score"], 0)
        self.assertEqual(rows[1]["Top Missing Skills"], "Kubernetes")


if __name__ == "__main__":
    unittest.main()
