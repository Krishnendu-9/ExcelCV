import unittest

from src.career_tools import (
    build_interview_prep_questions,
    build_learning_roadmap,
    build_portfolio_checklist,
    build_priority_action_plan,
    build_recruiter_snapshot,
)


class CareerToolsTests(unittest.TestCase):
    def test_recruiter_snapshot(self) -> None:
        analysis = {
            "match_score": 82,
            "strengths": ["Strong backend architecture"],
            "missing_skills": ["Docker"],
        }
        result = build_recruiter_snapshot(analysis, "Resume.pdf")
        self.assertEqual(result["verdict"], "Strong Fit")
        self.assertIn("Resume.pdf", result["summary"])

    def test_priority_action_plan_contains_high_priority_items(self) -> None:
        analysis = {
            "content_metrics": {
                "ats_parse_rate": 60,
                "quantifying_impact": {"score": 40},
                "repetition": {"score": 55},
                "spelling_grammar": {"score": 65},
            },
            "sections_metrics": {"details": {"missing_sections": ["Education"]}},
            "missing_skills": ["Kubernetes"],
            "missing_keywords": ["Microservices"],
            "suggestions": ["Add measurable impact"],
        }
        plan = build_priority_action_plan(analysis)
        self.assertTrue(plan)
        self.assertTrue(any(item["priority"] == "High" for item in plan))

    def test_interview_prep_questions(self) -> None:
        questions = build_interview_prep_questions(
            {"missing_skills": ["System Design"], "strengths": ["API development"]},
            job_desc="Need backend engineer",
        )
        self.assertGreaterEqual(len(questions), 2)
        self.assertIn("question", questions[0])

    def test_learning_roadmap(self) -> None:
        roadmap = build_learning_roadmap({"missing_skills": ["Docker", "AWS"]})
        self.assertEqual(len(roadmap), 2)
        self.assertIn("plan", roadmap[0])

    def test_portfolio_checklist(self) -> None:
        checklist = build_portfolio_checklist(
            {
                "sections_metrics": {"details": {"has_experience": True, "has_skills": False}},
                "contact_info": {"found": []},
                "ats_essentials_metrics": {"details": {"header_links": {"has_links": False}}},
                "suggestions": ["Improve bullets"],
            }
        )
        self.assertIn("completed", checklist)
        self.assertIn("missing", checklist)
        self.assertTrue(checklist["missing"])


if __name__ == "__main__":
    unittest.main()
