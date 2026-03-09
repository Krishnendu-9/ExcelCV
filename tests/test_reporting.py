import unittest

from src.reporting import build_report_md


class ReportingTests(unittest.TestCase):
    def test_build_report_md_contains_expected_sections(self) -> None:
        analysis = {
            "match_score": 84,
            "subscores": {
                "skills_alignment": 80,
                "experience_alignment": 86,
                "ats_readiness": 88,
            },
            "strengths": ["Strong backend experience"],
            "missing_skills": ["Kubernetes"],
            "missing_keywords": ["docker"],
            "suggestions": ["Add quantified outcomes"],
        }

        report = build_report_md("resume.pdf", analysis)

        self.assertIn("# CV Analysis Report", report)
        self.assertIn("Match Score: 84%", report)
        self.assertIn("### Strengths", report)
        self.assertIn("### Missing Skills", report)
        self.assertIn("### Missing Keywords (ATS)", report)
        self.assertIn("### Suggestions", report)


if __name__ == "__main__":
    unittest.main()
