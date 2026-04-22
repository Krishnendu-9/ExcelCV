import unittest

from src.reporting import build_report_md, build_report_pdf_bytes


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

    def test_build_report_pdf_bytes_returns_pdf(self) -> None:
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
        try:
            pdf_bytes = build_report_pdf_bytes("resume.pdf", analysis)
        except RuntimeError:
            self.skipTest("reportlab is not installed in this environment")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 500)


if __name__ == "__main__":
    unittest.main()
