import unittest

from src.gemini_client import (
    _derive_deterministic_insight_fallbacks,
    _extract_balanced_json_object,
    _load_model_json_payload,
    _merge_unique_items,
)


class GeminiJsonParsingTests(unittest.TestCase):
    def test_extract_balanced_json_ignores_trailing_braces_in_text(self) -> None:
        raw = 'Result:\n{"match_score": 84, "strengths": ["A"]}\nNote: use {} templates'
        extracted = _extract_balanced_json_object(raw)
        self.assertEqual(extracted, '{"match_score": 84, "strengths": ["A"]}')

    def test_load_model_json_payload_accepts_trailing_commas(self) -> None:
        raw = """```json
{
  "match_score": 77,
  "strengths": ["clean layout",],
}
```"""
        parsed = _load_model_json_payload(raw)
        self.assertEqual(parsed.get("match_score"), 77)
        self.assertEqual(parsed.get("strengths"), ["clean layout"])

    def test_load_model_json_payload_returns_empty_dict_for_invalid_payload(self) -> None:
        parsed = _load_model_json_payload("not-json-at-all")
        self.assertEqual(parsed, {})

    def test_merge_unique_items_preserves_order_and_dedupes(self) -> None:
        merged = _merge_unique_items(["a", "b"], ["b", "c", "a", "d"], limit=10)
        self.assertEqual(merged, ["a", "b", "c", "d"])

    def test_deterministic_fallbacks_build_non_empty_insights(self) -> None:
        payload = _derive_deterministic_insight_fallbacks(
            ats_parse_rate=90,
            sections_score=88,
            contact_info={"score": 100},
            tailoring_score=62,
            has_job_description=True,
            tailoring_details={"missing_keywords": ["docker", "kubernetes"]},
            jd_skill_matrix=[
                {"skill": "Docker", "status": "Missing"},
                {"skill": "Kubernetes", "status": "Missing"},
                {"skill": "Python", "status": "Found"},
            ],
            rewrite_recommendations=[{"rationale": "added measurable impact placeholders"}],
            quant_score=55,
            repetition_score=75,
            spelling_score=92,
            bullets_score=78,
        )

        self.assertTrue(payload["strengths"])
        self.assertIn("Docker", payload["missing_skills"])
        self.assertNotIn("docker", [str(x).lower() for x in payload["missing_keywords"]])
        self.assertTrue(payload["suggestions"])

    def test_deterministic_fallbacks_include_partial_skill_gaps(self) -> None:
        payload = _derive_deterministic_insight_fallbacks(
            ats_parse_rate=82,
            sections_score=80,
            contact_info={"score": 100},
            tailoring_score=70,
            has_job_description=True,
            tailoring_details={"missing_keywords": ["jira", "stakeholder communication"]},
            jd_skill_matrix=[
                {"skill": "Project Management", "status": "Partial"},
                {"skill": "Risk Management", "status": "Partial"},
            ],
            rewrite_recommendations=[],
            quant_score=72,
            repetition_score=84,
            spelling_score=95,
            bullets_score=82,
        )
        joined = " | ".join(payload["missing_skills"]).lower()
        self.assertIn("partial evidence", joined)
        self.assertIn("project management", joined)

    def test_deterministic_fallbacks_use_role_baseline_missing_skills(self) -> None:
        payload = _derive_deterministic_insight_fallbacks(
            ats_parse_rate=90,
            sections_score=85,
            contact_info={"score": 100},
            tailoring_score=42,
            has_job_description=True,
            tailoring_details={
                "missing_keywords": ["project"],
                "role_baseline": {
                    "missing": ["stakeholder management", "risk management", "jira"],
                    "matched": [],
                },
                "jd_specificity": {"status": "low"},
            },
            jd_skill_matrix=[],
            rewrite_recommendations=[],
            quant_score=68,
            repetition_score=78,
            spelling_score=95,
            bullets_score=82,
        )
        joined = " | ".join(payload["missing_skills"]).lower()
        self.assertIn("stakeholder management", joined)
        self.assertIn("risk management", joined)
        # Missing keywords should now avoid duplicating capability-level skill gaps.
        kw_joined = " | ".join(payload["missing_keywords"]).lower()
        self.assertNotIn("stakeholder management", kw_joined)

    def test_strengths_call_out_when_no_jd_specific_matches(self) -> None:
        payload = _derive_deterministic_insight_fallbacks(
            ats_parse_rate=90,
            sections_score=82,
            contact_info={"score": 100},
            tailoring_score=22,
            has_job_description=True,
            tailoring_details={"matched_skills": [], "missing_keywords": ["blockchain"]},
            jd_skill_matrix=[],
            rewrite_recommendations=[],
            quant_score=72,
            repetition_score=85,
            spelling_score=96,
            bullets_score=88,
        )
        joined = " | ".join(payload["strengths"]).lower()
        self.assertIn("no strong jd-specific strengths", joined)


if __name__ == "__main__":
    unittest.main()
