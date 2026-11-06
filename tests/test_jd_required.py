"""Every way into an analysis requires a job description.

What this protects: the Explainable Scoring page, docs/METRICS_DOCUMENTATION.md,
docs/excelcv.md and the project report say the app always scores with the JD-aligned
weights, and that calculate_final_score_breakdown's no-JD weights are reachable only by
calling the scoring functions directly. That holds because analyze_cv_with_gemini(), the
only path to those weights, has two callers, both in src/ui/analysis_runner.py, and every
runner rejects a blank job description before reaching them.

If a test here fails because a job description became optional, the no-JD mode is now
live: update that copy (the page's JD Alignment card, the two docs, and the report's
withdrawn TC-26) before making this pass again.
"""

import ast
import unittest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from src.ui import analysis_runner
from tests.repo_files import REPO_ROOT

_BLANK_JOB_DESCRIPTIONS = ("", "   \n\t  ")

# Every function that calls analyze_cv_with_gemini(), as "path:function".
_KNOWN_CALLERS = {
    "src/ui/analysis_runner.py:run_single_analysis",
    "src/ui/analysis_runner.py:_analyze_cv_payload",
}


@dataclass
class _Upload:
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


def _callers_of_analyze_cv_with_gemini() -> set[str]:
    """ "path:function" for every function in app.py and src/ that calls it."""
    callers = set()
    for path in [REPO_ROOT / "app.py", *sorted((REPO_ROOT / "src").rglob("*.py"))]:
        rel = path.relative_to(REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(func):
                target = node.func if isinstance(node, ast.Call) else None
                name = getattr(target, "id", None) or getattr(target, "attr", None)
                if name == "analyze_cv_with_gemini":
                    callers.add(f"{rel}:{func.name}")
    return callers


class JobDescriptionRequiredTests(unittest.TestCase):
    def test_analyze_cv_with_gemini_has_only_the_known_callers(self) -> None:
        self.assertEqual(
            _callers_of_analyze_cv_with_gemini(),
            _KNOWN_CALLERS,
            "a new path into the analysis: make sure it requires a job description, then "
            "add it to _KNOWN_CALLERS and to the entry-point test below",
        )

    def test_no_entry_point_analyses_without_a_job_description(self) -> None:
        upload = _Upload("resume.pdf", b"%PDF-1.4 resume")
        other = _Upload("other.pdf", b"%PDF-1.4 other resume")
        cv_text = "Jane Doe\nExperience\nBuilt APIs.\n" + "Python SQL " * 40
        for jd in _BLANK_JOB_DESCRIPTIONS:
            entry_points = {
                "run_single_analysis": lambda jd=jd: analysis_runner.run_single_analysis(
                    jd, upload, status_container=MagicMock()
                ),
                "_analyze_cv_payload": lambda jd=jd: analysis_runner._analyze_cv_payload(
                    jd, upload
                ),
                "run_multi_resume_comparison": lambda jd=jd: (
                    analysis_runner.run_multi_resume_comparison(jd, [upload, other])
                ),
            }
            for name, call in entry_points.items():
                with self.subTest(entry_point=name, job_description=repr(jd)):
                    analyze = MagicMock(return_value={"match_score": 50})
                    with (
                        patch.object(analysis_runner, "st", MagicMock()),
                        patch.object(analysis_runner, "extract_cv_text", return_value=cv_text),
                        patch.object(analysis_runner, "analyze_cv_with_gemini", analyze),
                    ):
                        try:
                            call()
                        except ValueError:
                            pass  # the runners that raise reject a blank job description
                    self.assertFalse(
                        analyze.called, f"{name} analysed a resume without a job description"
                    )


if __name__ == "__main__":
    unittest.main()
