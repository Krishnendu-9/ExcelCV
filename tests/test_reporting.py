"""build_report_md() must carry what the docs say the Markdown report carries.

README.md and docs/METRICS_DOCUMENTATION.md say the downloadable PDF and Markdown reports
both include the model's three subscores. The guard in test_feature_claims.py checks the
report page offers build_report_md() as a download; this checks what it builds.
"""

import unittest

from src.services.reporting import build_report_md

_ANALYSIS = {
    "match_score": 72,
    "subscores": {"skills_alignment": 61, "experience_alignment": 54, "ats_readiness": 83},
    "strengths": ["Python", "FastAPI"],
    "missing_skills": ["Kubernetes"],
    "missing_keywords": [],
    "suggestions": ["Quantify impact"],
}


class BuildReportMdTests(unittest.TestCase):
    def test_carries_the_score_and_the_three_subscores(self) -> None:
        md = build_report_md("Jane-Doe", _ANALYSIS)
        self.assertTrue(md.startswith("# CV Analysis Report - Jane-Doe\n"))
        for line in (
            "- Match Score: 72%",
            "- Skills Alignment: 61%",
            "- Experience Alignment: 54%",
            "- ATS Readiness: 83%",
        ):
            with self.subTest(line=line):
                self.assertIn(line, md.splitlines())

    def test_carries_the_four_sections_with_their_items(self) -> None:
        md = build_report_md("Jane-Doe", _ANALYSIS)
        self.assertIn("### Strengths\n- Python\n- FastAPI\n", md)
        self.assertIn("### Missing Skills\n- Kubernetes\n", md)
        self.assertIn("### Missing Keywords (ATS)\n- None noted\n", md)
        self.assertIn("### Suggestions\n- Quantify impact\n", md)

    def test_an_empty_analysis_still_builds_every_heading(self) -> None:
        md = build_report_md("CV", {"subscores": None})
        self.assertIn("- Match Score: 0%", md)
        self.assertIn("- ATS Readiness: 0%", md)
        for heading in ("Strengths", "Missing Skills", "Missing Keywords (ATS)", "Suggestions"):
            with self.subTest(heading=heading):
                self.assertIn(f"### {heading}\n- None noted\n", md)


if __name__ == "__main__":
    unittest.main()
