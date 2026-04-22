import unittest

from src.evaluation import build_evaluation_record, summarize_evaluation


class EvaluationTests(unittest.TestCase):
    def test_build_evaluation_record_normalizes_values(self) -> None:
        record = build_evaluation_record(
            resume_name="candidate.pdf",
            model_score=120,
            human_score=-10,
            notes=" strong fit ",
        )
        self.assertEqual(record["resume_name"], "candidate.pdf")
        self.assertEqual(record["model_score"], 100)
        self.assertEqual(record["human_score"], 0)
        self.assertEqual(record["notes"], "strong fit")
        self.assertIn("created_at", record)
        self.assertEqual(record["absolute_error"], 100)

    def test_summarize_evaluation_metrics(self) -> None:
        records = [
            build_evaluation_record("a.pdf", 80, 70),
            build_evaluation_record("b.pdf", 60, 65),
            build_evaluation_record("c.pdf", 90, 95),
        ]
        summary = summarize_evaluation(records)
        self.assertEqual(summary["count"], 3)
        self.assertIsNotNone(summary["mae"])
        self.assertIsNotNone(summary["rmse"])
        self.assertIn("correlation", summary)

    def test_summarize_evaluation_empty(self) -> None:
        summary = summarize_evaluation([])
        self.assertEqual(summary["count"], 0)
        self.assertIsNone(summary["mae"])
        self.assertIsNone(summary["rmse"])
        self.assertIsNone(summary["correlation"])

    def test_build_evaluation_record_handles_non_numeric_scores(self) -> None:
        record = build_evaluation_record(
            resume_name="candidate.pdf",
            model_score="bad-input",
            human_score=None,
        )
        self.assertEqual(record["model_score"], 0)
        self.assertEqual(record["human_score"], 0)
        self.assertEqual(record["absolute_error"], 0)


if __name__ == "__main__":
    unittest.main()
