import unittest

from src.scoring import (
    build_jd_skill_matrix,
    calculate_ats_essentials,
    calculate_ats_parse_rate,
    calculate_final_score_breakdown,
    calculate_sections,
    calculate_tailoring,
    generate_section_rewrite_recommendations,
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

    def test_ats_essentials_standard_formatting_reflects_header_detection(self) -> None:
        score, details = calculate_ats_essentials("plain text without typical resume sections")
        self.assertGreaterEqual(score, 0)
        self.assertFalse(details.get("section_headers_present"))
        self.assertFalse(details.get("standard_formatting"))

    def test_final_score_breakdown_uses_jd_mode_weights(self) -> None:
        breakdown = calculate_final_score_breakdown(
            ats_parse_rate=90,
            quant_score=80,
            repetition_score=70,
            spelling_score=85,
            tailoring_score=88,
            sections_score=92,
            ats_essentials_score=86,
            contact_score=100,
            has_job_description=True,
        )
        self.assertEqual(breakdown.get("mode"), "jd_aligned")
        self.assertIn("components", breakdown)
        self.assertEqual(len(breakdown.get("components", [])), 5)
        self.assertGreaterEqual(breakdown.get("final_score", 0), 0)
        self.assertLessEqual(breakdown.get("final_score", 0), 100)

    def test_jd_skill_matrix_flags_missing_and_found_skills(self) -> None:
        cv_text = "Built Python APIs with SQL and deployed services to cloud environments."
        job_desc = "Need Python, SQL, Docker, and Kubernetes experience."
        matrix = build_jd_skill_matrix(cv_text=cv_text, job_desc=job_desc)
        self.assertTrue(matrix)
        statuses = {row.get("status") for row in matrix}
        self.assertIn("Found", statuses)
        self.assertIn("Missing", statuses)

    def test_rewrite_recommendations_generated_for_non_quantified_lines(self) -> None:
        recommendations = generate_section_rewrite_recommendations(
            cv_text="Developed backend services.",
            quantifying_impact_data={
                "non_quantified_lines": ["Developed backend services for clients"],
            },
            repetition_data={
                "repeated_words": [
                    {"word": "developed", "suggestions": ["engineered"]},
                ]
            },
        )
        self.assertTrue(recommendations)
        first = recommendations[0]
        self.assertIn("before", first)
        self.assertIn("after", first)
        self.assertIn("[X%]", first.get("after", ""))


if __name__ == "__main__":
    unittest.main()
