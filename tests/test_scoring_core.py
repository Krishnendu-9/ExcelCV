import unittest

from src.services.scoring import (
    _extract_requirement_phrases,
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

    def test_tailoring_applies_specificity_guardrail_for_role_only_jd(self) -> None:
        cv_text = "Cloud engineer with DevOps experience in AWS, Kubernetes, and CI/CD."
        short_jd = "Cloud Engineer"
        full_jd = (
            "Cloud Engineer role requiring AWS, Kubernetes, Terraform, CI/CD pipelines, "
            "monitoring, incident response, and infrastructure automation."
        )

        short_score, short_details = calculate_tailoring(cv_text, short_jd)
        full_score, full_details = calculate_tailoring(cv_text, full_jd)

        self.assertLess(short_score, 90)
        self.assertEqual(short_details.get("jd_specificity", {}).get("status"), "low")
        self.assertLess(short_score, int(short_details.get("raw_alignment_score", 0) or 0))
        self.assertEqual(full_details.get("jd_specificity", {}).get("status"), "good")
        self.assertEqual(full_details.get("jd_specificity", {}).get("factor"), 1.0)

    def test_tailoring_short_project_manager_jd_surfaces_role_baseline_gaps(self) -> None:
        cv_text = "Software engineer with Python and cloud deployment experience."
        score, details = calculate_tailoring(cv_text, "IT Project Manager")
        missing = [str(x).lower() for x in details.get("missing_skills", [])]
        missing_keywords = [str(x).lower() for x in details.get("missing_keywords", [])]
        self.assertTrue(any("stakeholder" in item for item in missing))
        self.assertTrue(any("risk management" in item for item in missing))
        self.assertTrue(any(item == "project" for item in missing_keywords))
        self.assertFalse(any("stakeholder management" == item for item in missing_keywords))
        self.assertLess(score, 70)

    def test_tailoring_avoids_role_title_false_positive_match(self) -> None:
        cv_text = "Junior AI Developer with Python and SQL."
        score, details = calculate_tailoring(cv_text, "Blockchain Developer")
        matched_skills = [str(x).lower() for x in details.get("matched_skills", [])]
        missing_skills = [str(x).lower() for x in details.get("missing_skills", [])]
        self.assertFalse(any("blockchain developer" == item for item in matched_skills))
        self.assertIn("blockchain", missing_skills)
        self.assertLess(score, 80)

    def test_extract_requirement_phrases_generic_jd(self) -> None:
        jd = (
            "Must have: Solidity, smart contracts, Ethereum, Web3.js. "
            "Experience with Truffle and gas optimization."
        )
        phrases = _extract_requirement_phrases(jd)
        joined = " | ".join(phrases)
        self.assertIn("solidity", joined)
        self.assertIn("smart contracts", joined)


if __name__ == "__main__":
    unittest.main()
