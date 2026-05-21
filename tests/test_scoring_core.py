import unittest

from src.services.scoring import (
    calculate_final_score_breakdown,
    calculate_sections_order,
    calculate_tailoring,
)


class ScoringCoreTests(unittest.TestCase):
    def test_final_score_breakdown_modes(self) -> None:
        with_jd = calculate_final_score_breakdown(
            ats_parse_rate=90,
            quant_score=80,
            repetition_score=85,
            spelling_score=88,
            tailoring_score=75,
            sections_score=92,
            ats_essentials_score=84,
            contact_score=95,
            has_job_description=True,
            bullets_consistency_score=86,
        )
        self.assertEqual(with_jd["mode"], "jd_aligned")
        self.assertEqual(len(with_jd["components"]), 5)
        self.assertTrue(0 <= with_jd["final_score"] <= 100)

        no_jd = calculate_final_score_breakdown(
            ats_parse_rate=90,
            quant_score=80,
            repetition_score=85,
            spelling_score=88,
            tailoring_score=75,
            sections_score=92,
            ats_essentials_score=84,
            contact_score=95,
            has_job_description=False,
            bullets_consistency_score=86,
        )
        self.assertEqual(no_jd["mode"], "no_jd")
        self.assertEqual(len(no_jd["components"]), 4)
        self.assertTrue(0 <= no_jd["final_score"] <= 100)

    def test_tailoring_detects_matched_and_missing_keywords(self) -> None:
        cv_text = (
            "Built machine learning pipelines in Python and deployed APIs with FastAPI. "
            "Worked with SQL and cloud deployments."
        )
        jd = "Looking for Python engineer with machine learning, FastAPI, Docker, and SQL skills."

        score, details = calculate_tailoring(cv_text, jd)
        self.assertTrue(0 <= score <= 100)
        matched = set(details.get("matched_keywords", []))
        missing = set(details.get("missing_keywords", []))
        self.assertTrue(any("machine learning" in m for m in matched))
        self.assertIn("docker", missing)

    def test_sections_order_warns_for_entry_like_layout(self) -> None:
        cv_text = """
John Doe
Summary
Intern with hands-on project experience.
Experience
Built a small college project using Python and SQL.
Education
B.Tech Computer Science 2021 - 2025
Skills
Python, SQL
"""
        score, details = calculate_sections_order(cv_text)
        self.assertLessEqual(score, 80)
        self.assertEqual(details.get("status"), "warn")


if __name__ == "__main__":
    unittest.main()
