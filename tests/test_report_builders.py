import unittest

from src.ui.report import (
    _build_ats_parse_rate_html,
    _build_contact_information_html,
    _build_email_address_html,
    _build_essential_sections_html,
    _build_explainable_scoring_html,
    _build_file_format_size_html,
    _build_header_links_html,
    _build_interview_prep_html,
    _build_learning_roadmap_html,
    _build_priority_action_plan_html,
    _build_recruiter_snapshot_html,
    _build_rewrite_assistant_html,
    _build_skill_matrix_html,
    _build_list_card,
    _build_quantifying_impact_html,
    _build_repetition_html,
    _build_spelling_grammar_html,
    _escape_html,
)


class ReportBuilderTests(unittest.TestCase):
    def test_escape_html(self) -> None:
        self.assertEqual(_escape_html("<a&b>"), "&lt;a&amp;b&gt;")

    def test_ats_parse_rate_builder_contains_section_and_score(self) -> None:
        html = _build_ats_parse_rate_html(85)
        self.assertIn('id="ats-parse-rate"', html)
        self.assertIn("85%", html)
        self.assertIn("Excellent", html)

    def test_quantifying_impact_builder_escapes_non_quantified_lines(self) -> None:
        html = _build_quantifying_impact_html(
            {
                "score": 62,
                "status": "warn",
                "quantified_count": 2,
                "total_lines": 5,
                "non_quantified_lines": ["Built <internal> tool"],
            }
        )
        self.assertIn('id="quantifying-impact"', html)
        self.assertIn("2 of 5", html)
        self.assertIn("Built &lt;internal&gt; tool", html)

    def test_repetition_builder_shows_suggestions(self) -> None:
        html = _build_repetition_html(
            {
                "score": 58,
                "status": "warn",
                "repeated_words": [
                    {"word": "developed", "count": 5, "suggestions": ["built", "engineered"]},
                ],
            }
        )
        self.assertIn('id="repetition"', html)
        self.assertIn("5 times: developed", html)
        self.assertIn("built", html)
        self.assertIn("engineered", html)

    def test_spelling_builder_escapes_examples(self) -> None:
        html = _build_spelling_grammar_html(
            {
                "score": 70,
                "status": "warn",
                "issues_list": [
                    {"label": "Double spaces", "count": 2, "examples": ["Hello  world", "<bad> token"]},
                ],
            }
        )
        self.assertIn('id="spelling-grammar"', html)
        self.assertIn("Double spaces", html)
        self.assertIn("&lt;bad&gt; token", html)

    def test_sections_and_contact_builders_warn_when_missing(self) -> None:
        sections_html = _build_essential_sections_html(
            {
                "has_contact": True,
                "has_experience": False,
                "has_education": True,
                "has_skills": False,
                "has_summary": False,
            }
        )
        self.assertIn('id="essential-sections"', sections_html)
        self.assertIn("missing", sections_html)

        contact_html = _build_contact_information_html(
            contact_found=[{"label": "Email", "value": "x@y.com"}],
            contact_missing=[{"label": "Phone", "message": "Missing <phone> number"}],
        )
        self.assertIn('id="contact-information"', contact_html)
        self.assertIn("Missing &lt;phone&gt; number", contact_html)

    def test_file_email_header_and_list_builders(self) -> None:
        file_html = _build_file_format_size_html(
            {
                "is_supported_format": True,
                "is_pdf": False,
                "is_docx": True,
                "size_ok": False,
                "file_name": "resume.docx",
                "file_size_kb": 2500,
                "file_size_mb": 2.4,
            }
        )
        self.assertIn('id="file-format-size"', file_html)
        self.assertIn("DOCX", file_html)
        self.assertIn("2.4MB", file_html)

        email_html = _build_email_address_html({"found": False, "email": "", "is_professional": False})
        self.assertIn('id="email-address"', email_html)
        self.assertIn("No email address was found", email_html)

        header_html = _build_header_links_html({"has_links": True, "has_full_url": False, "links": []})
        self.assertIn('id="header-links"', header_html)
        self.assertIn("Partial link detected", header_html)

        list_html = _build_list_card(
            title="Suggestions",
            items=["Use **metrics** in bullets"],
            section_id="suggestions",
            badge_type="ok",
            badge_label="1 tip",
            icon="&#10003;",
            empty_msg="None",
        )
        self.assertIn('id="suggestions"', list_html)
        self.assertIn("<strong>metrics</strong>", list_html)

    def test_new_insights_cards_render(self) -> None:
        scoring_html = _build_explainable_scoring_html(
            {
                "final_score": 84,
                "mode": "jd_aligned",
                "content_average": 80,
                "components": [
                    {"label": "Content Quality", "score": 80, "weight": 0.3, "weighted_points": 24.0},
                ],
            }
        )
        self.assertIn('id="explainable-scoring"', scoring_html)
        self.assertIn("Weighted score breakdown", scoring_html)

        matrix_html = _build_skill_matrix_html(
            [
                {
                    "skill": "Python",
                    "status": "Found",
                    "confidence": "High",
                    "evidence": "Built Python APIs",
                }
            ]
        )
        self.assertIn('id="jd-skill-matrix"', matrix_html)
        self.assertIn("Python", matrix_html)

        rewrite_html = _build_rewrite_assistant_html(
            [
                {
                    "before": "Developed dashboards.",
                    "after": "Engineered dashboards improving adoption by [X%], improving [outcome] by [Y].",
                    "rationale": "added measurable impact placeholders",
                }
            ]
        )
        self.assertIn('id="rewrite-assistant"', rewrite_html)
        self.assertIn("Before", rewrite_html)
        self.assertIn("After", rewrite_html)

    def test_additional_final_project_cards_render(self) -> None:
        snapshot_html = _build_recruiter_snapshot_html(
            {"verdict": "Potential Fit", "summary": "Candidate has strengths but needs keyword alignment."}
        )
        self.assertIn('id="recruiter-snapshot"', snapshot_html)

        action_html = _build_priority_action_plan_html(
            [
                {
                    "title": "Quantify bullets",
                    "priority": "High",
                    "impact": "High",
                    "effort": "Medium",
                    "action": "Add measurable metrics to achievements.",
                }
            ]
        )
        self.assertIn('id="priority-action-plan"', action_html)

        interview_html = _build_interview_prep_html(
            [{"type": "Gap Mitigation", "question": "How would you learn Docker quickly?", "why": "role gap"}]
        )
        self.assertIn('id="interview-prep"', interview_html)

        roadmap_html = _build_learning_roadmap_html(
            [{"skill": "Docker", "target": "2 weeks", "plan": "Build one deployment project"}]
        )
        self.assertIn('id="learning-roadmap"', roadmap_html)


if __name__ == "__main__":
    unittest.main()
