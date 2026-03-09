import unittest

from src.scoring import (
    calculate_ats_parse_rate,
    calculate_sections,
    calculate_tailoring,
    normalize_score,
)


class ScoringTests(unittest.TestCase):
    def test_normalize_score_bounds_and_types(self) -> None:
        self.assertEqual(normalize_score("87.9"), 87)
        self.assertEqual(normalize_score(-10), 0)
        self.assertEqual(normalize_score(150), 100)
        self.assertEqual(normalize_score(None), 0)

    def test_ats_parse_rate_rewards_text_and_sections(self) -> None:
        cv_text = (
            "Contact\n"
            "Experience\n"
            "Education\n"
            "Skills\n"
            + ("Implemented data pipelines and automation. " * 40)
        )
        score = calculate_ats_parse_rate(cv_text)
        self.assertGreaterEqual(score, 90)
        self.assertLessEqual(score, 100)

    def test_sections_detects_missing_items(self) -> None:
        full_cv = "Contact\nExperience\nEducation\nSkills\nSummary"
        score_full, details_full = calculate_sections(full_cv)
        self.assertEqual(score_full, 100)
        self.assertEqual(details_full.get("missing_sections"), [])

        partial_cv = "Contact\nExperience\nSkills"
        score_partial, details_partial = calculate_sections(partial_cv)
        self.assertLess(score_partial, 100)
        missing = details_partial.get("missing_sections", [])
        self.assertTrue(any("Education" in item for item in missing))

    def test_tailoring_scores_higher_for_relevant_cv(self) -> None:
        jd = (
            "We need Python, SQL, machine learning, and REST API development "
            "experience with cloud deployment."
        )
        strong_cv = (
            "Built Python services and REST API backends. "
            "Created machine learning models and SQL analytics pipelines. "
            "Deployed workloads on cloud infrastructure."
        )
        weak_cv = "Managed office inventory and handled daily administration tasks."

        high_score, high_details = calculate_tailoring(strong_cv, jd)
        low_score, _ = calculate_tailoring(weak_cv, jd)

        self.assertGreater(high_score, low_score)
        self.assertIn("keyword_match_rate", high_details)
        self.assertIn("missing_keywords", high_details)


if __name__ == "__main__":
    unittest.main()
