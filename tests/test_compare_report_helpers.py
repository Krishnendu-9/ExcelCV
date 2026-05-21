import unittest

from src.ui.compare_report import _apply_sort, _comparison_rows_to_csv


class CompareReportHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "Rank": 1,
                "Resume": "Charlie.pdf",
                "Final Score": 80,
                "JD Alignment": 70,
                "ATS Parse": 88,
                "Sections": 82,
                "Issues": 7,
                "_analysis": {"x": 1},
            },
            {
                "Rank": 2,
                "Resume": "alpha.pdf",
                "Final Score": 92,
                "JD Alignment": 91,
                "ATS Parse": 95,
                "Sections": 90,
                "Issues": 2,
                "_analysis": {"x": 2},
            },
            {
                "Rank": 3,
                "Resume": "Bravo.pdf",
                "Final Score": 92,
                "JD Alignment": 85,
                "ATS Parse": 80,
                "Sections": 78,
                "Issues": 12,
                "_analysis": {"x": 3},
            },
        ]

    def test_apply_sort_issues_low_to_high_renumbers_rank(self) -> None:
        sorted_rows = _apply_sort(self.rows, "Issues (low → high)")
        self.assertEqual(
            [r["Resume"] for r in sorted_rows], ["alpha.pdf", "Charlie.pdf", "Bravo.pdf"]
        )
        self.assertEqual([r["Rank"] for r in sorted_rows], [1, 2, 3])

    def test_apply_sort_resume_name_a_to_z_case_insensitive(self) -> None:
        sorted_rows = _apply_sort(self.rows, "Resume name (A → Z)")
        self.assertEqual(
            [r["Resume"] for r in sorted_rows], ["alpha.pdf", "Bravo.pdf", "Charlie.pdf"]
        )
        self.assertEqual([r["Rank"] for r in sorted_rows], [1, 2, 3])

    def test_apply_sort_unknown_label_falls_back_to_final_score_desc(self) -> None:
        sorted_rows = _apply_sort(self.rows, "non-existent-sort")
        self.assertEqual(
            [r["Resume"] for r in sorted_rows], ["alpha.pdf", "Bravo.pdf", "Charlie.pdf"]
        )

    def test_comparison_rows_to_csv_ignores_extra_columns(self) -> None:
        columns = ["Rank", "Resume", "Final Score", "Issues"]
        csv_text = _comparison_rows_to_csv(self.rows, columns)
        lines = [line.strip() for line in csv_text.strip().splitlines()]
        self.assertEqual(lines[0], "Rank,Resume,Final Score,Issues")
        self.assertEqual(len(lines), 4)
        self.assertNotIn("_analysis", csv_text)


if __name__ == "__main__":
    unittest.main()
