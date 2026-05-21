import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from src.ui.analysis_runner import _analyze_cv_payload, run_multi_resume_comparison


@dataclass
class FakeUpload:
    name: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)

    def getvalue(self) -> bytes:
        return self.data

    def seek(self, _offset: int) -> None:
        return None

    def read(self) -> bytes:
        return self.data


def _analysis(score: int, jd: int, ats: int, sections: int, issues: int) -> dict[str, Any]:
    return {
        "match_score": score,
        "tailoring_metrics": {"score": jd},
        "content_metrics": {"ats_parse_rate": ats},
        "sections_metrics": {"score": sections},
        "ats_essentials_metrics": {"details": {"issues": ["x"] * issues}},
        "missing_skills": ["docker", "kubernetes"],
    }


class AnalysisRunnerTests(unittest.TestCase):
    def test_analyze_payload_requires_job_description(self) -> None:
        fake = FakeUpload(name="resume.pdf", data=b"pdf-bytes")
        with self.assertRaises(ValueError):
            _analyze_cv_payload("   ", fake)

    def test_multi_resume_comparison_deduplicates_and_ranks(self) -> None:
        files = [
            FakeUpload(name="A.pdf", data=b"same"),
            FakeUpload(name="A.pdf", data=b"same"),  # duplicate (name/size/hash)
            FakeUpload(name="B.pdf", data=b"diff"),
        ]

        with patch(
            "src.ui.analysis_runner._analyze_cv_payload",
            side_effect=[
                (_analysis(70, 68, 80, 72, 2), "text-a"),
                (_analysis(92, 90, 95, 89, 1), "text-b"),
            ],
        ):
            result = run_multi_resume_comparison("Python backend JD", files)

        self.assertEqual(len(result["rows"]), 2)
        self.assertTrue(any("Skipped duplicate file selections" in w for w in result["warnings"]))
        # Sorted by final score desc, then issues asc.
        self.assertEqual(result["rows"][0]["Resume"], "B.pdf")
        self.assertEqual(result["rows"][0]["Rank"], 1)
        self.assertEqual(result["rows"][1]["Rank"], 2)

    def test_multi_resume_comparison_quota_short_circuits_remaining(self) -> None:
        files = [
            FakeUpload(name="one.pdf", data=b"1"),
            FakeUpload(name="two.pdf", data=b"2"),
            FakeUpload(name="three.pdf", data=b"3"),
        ]
        progress_events: list[tuple[str, int, int, str]] = []

        def on_progress(name: str, idx: int, total: int, status: str) -> None:
            progress_events.append((name, idx, total, status))

        with patch(
            "src.ui.analysis_runner._analyze_cv_payload",
            side_effect=RuntimeError("429 quota exceeded"),
        ):
            result = run_multi_resume_comparison("JD text", files, progress_callback=on_progress)

        self.assertEqual(result["rows"], [])
        self.assertEqual(len(result["errors"]), 3)
        self.assertTrue(
            any("rate limit hit during comparison" in w.lower() for w in result["warnings"])
        )
        # First file runs + errors, next files are skipped.
        self.assertEqual(progress_events[0][-1], "running")
        self.assertEqual(progress_events[1][-1], "error")
        self.assertEqual(progress_events[2][-1], "skipped")
        self.assertEqual(progress_events[3][-1], "skipped")


if __name__ == "__main__":
    unittest.main()
