"""The comparison exports follow the user's sort; the top match does not.

docs/compareCV.md: the sorted rows from _apply_sort flow to the table, the drill-downs,
the CSV and the PDF, and the ★ top match stays on the true top match (rank 1 in scoring
order) whatever the sort. These tests drive the exports from _apply_sort itself, never
from a hand-sorted fixture, and read the PDF that ReportLab actually writes.
"""

import csv
import io
import re
import unittest

from pypdf import PdfReader

from src.ui.compare_report import (
    _SORT_OPTIONS,
    _apply_sort,
    _build_comparison_pdf_bytes,
    _comparison_rows_to_csv,
)

# The page's CSV column order (csv_columns in render_compare_report_page).
_CSV_COLUMNS = [
    "Rank",
    "Resume",
    "Final Score",
    "JD Alignment",
    "ATS Parse",
    "Sections",
    "Issues",
    "Top Missing Skills",
]

# The PDF's winner-row tint, _WIN_BG = #ecfdf5, as ReportLab writes it.
_WIN_BG_RGB = (round(0xEC / 255, 3), round(0xFD / 255, 3), round(0xF5 / 255, 3))


def _scored_rows() -> list[dict[str, object]]:
    """Rows as the comparison runner returns them: ranked by final score."""
    return [
        {
            "Rank": 1,
            "Resume": "alice_cv.pdf",
            "Final Score": 91,
            "JD Alignment": 80,
            "ATS Parse": 95,
            "Sections": 100,
            "Issues": 9,
            "Top Missing Skills": "Kubernetes",
        },
        {
            "Rank": 2,
            "Resume": "bob_cv.pdf",
            "Final Score": 77,
            "JD Alignment": 88,
            "ATS Parse": 70,
            "Sections": 80,
            "Issues": 3,
            "Top Missing Skills": "Terraform",
        },
        {
            "Rank": 3,
            "Resume": "carol_cv.pdf",
            "Final Score": 64,
            "JD Alignment": 60,
            "ATS Parse": 85,
            "Sections": 60,
            "Issues": 14,
            "Top Missing Skills": "SQL",
        },
    ]


# Expected order per sort, written out by hand rather than recomputed.
_EXPECTED_ORDER = {
    "Final Score (high → low)": ["alice_cv.pdf", "bob_cv.pdf", "carol_cv.pdf"],
    "Final Score (low → high)": ["carol_cv.pdf", "bob_cv.pdf", "alice_cv.pdf"],
    "Issues (low → high)": ["bob_cv.pdf", "alice_cv.pdf", "carol_cv.pdf"],
    "ATS Parse (high → low)": ["alice_cv.pdf", "carol_cv.pdf", "bob_cv.pdf"],
}


def _pdf_for(sort_label: str) -> bytes:
    rows = _scored_rows()
    return _build_comparison_pdf_bytes(
        _apply_sort(rows, sort_label),
        "Python developer with cloud experience.",
        77.3,
        [],
        [],
        str(rows[0]["Resume"]),
    )


def _pdf_text(pdf: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)


def _tinted_resumes(pdf: bytes) -> list[str]:
    """Resume names whose ranked-table row sits inside a winner-tint rectangle."""
    page = PdfReader(io.BytesIO(pdf)).pages[0]
    fill: list[tuple[float, ...]] = [()]
    bands: list[tuple[float, float]] = []
    names: list[tuple[str, float]] = []

    def before(op: bytes, args: list, cm: list, tm: list) -> None:
        if op == b"rg":
            fill[0] = tuple(round(float(a), 3) for a in args)
        elif op == b"re" and fill[0] == _WIN_BG_RGB:
            y, h = float(args[1]) + cm[5], float(args[3])
            bands.append((min(y, y + h), max(y, y + h)))

    def text(t: str, cm: list, tm: list, font: object, size: float) -> None:
        if re.fullmatch(r"\w+_cv\.pdf", t.strip()):
            names.append((t.strip(), tm[5] + cm[5]))

    page.extract_text(visitor_operand_before=before, visitor_text=text)
    return [name for name, y in names if any(lo <= y <= hi for lo, hi in bands)]


class CsvFollowsTheSortTests(unittest.TestCase):
    def test_sort_options_under_test_exist(self) -> None:
        labels = {label for label, _key, _desc in _SORT_OPTIONS}
        for label in _EXPECTED_ORDER:
            with self.subTest(sort=label):
                self.assertIn(label, labels)

    def test_csv_rows_and_ranks_follow_apply_sort(self) -> None:
        for label, expected in _EXPECTED_ORDER.items():
            with self.subTest(sort=label):
                exported = _comparison_rows_to_csv(_apply_sort(_scored_rows(), label), _CSV_COLUMNS)
                records = list(csv.DictReader(io.StringIO(exported)))
                self.assertEqual([r["Resume"] for r in records], expected)
                self.assertEqual([r["Rank"] for r in records], ["1", "2", "3"])


class PdfFollowsTheSortButKeepsTheTopMatchTests(unittest.TestCase):
    def test_ranked_table_follows_apply_sort(self) -> None:
        for label, expected in _EXPECTED_ORDER.items():
            with self.subTest(sort=label):
                text = _pdf_text(_pdf_for(label))
                table = text.split("Ranked Comparison", 1)[1].split("Per-Resume Details", 1)[0]
                self.assertEqual(re.findall(r"\w+_cv\.pdf", table), expected)
                details = text.split("Per-Resume Details", 1)[1]
                self.assertEqual(
                    re.findall(r"#(\d)\s+(\w+_cv\.pdf)", details),
                    [(str(n), name) for n, name in enumerate(expected, start=1)],
                )

    def test_header_names_the_true_top_match_after_a_resort(self) -> None:
        # "Final Score (low → high)" puts carol_cv.pdf in row 1 with Rank 1; the true
        # top match is still alice_cv.pdf, as the on-page Top Match card shows.
        text = _pdf_text(_pdf_for("Final Score (low → high)"))
        header = re.search(r"top match (\S+) at (\d+)/100", text)
        self.assertIsNotNone(header, "no top-match line in the PDF header")
        self.assertEqual(header.groups(), ("alice_cv.pdf", "91"))

    def test_tinted_row_is_the_true_top_match_after_a_resort(self) -> None:
        for label in _EXPECTED_ORDER:
            with self.subTest(sort=label):
                self.assertEqual(_tinted_resumes(_pdf_for(label)), ["alice_cv.pdf"])


if __name__ == "__main__":
    unittest.main()
