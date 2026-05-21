import unittest
from dataclasses import dataclass

from src.ui.upload import (
    _comparison_input_signature,
    _comparison_rows_to_csv,
    _read_uploaded_cv_bytes,
)


@dataclass
class _FakeUpload:
    name: str
    raw: bytes

    @property
    def size(self) -> int:
        return len(self.raw)

    def getvalue(self):
        return self.raw

    def seek(self, _offset: int) -> None:
        return None

    def read(self):
        return self.raw


class _GetValueFailsReadWorks:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def getvalue(self):
        raise RuntimeError("simulated getvalue failure")

    def seek(self, _offset: int) -> None:
        return None

    def read(self):
        return self.raw


class UploadHelperTests(unittest.TestCase):
    def test_comparison_input_signature_normalizes_and_sorts(self) -> None:
        jd = "  Senior Python Engineer  "
        files = [
            _FakeUpload(name="B.Resume.PDF", raw=b"aa"),
            _FakeUpload(name="a resume.pdf", raw=b"bbbb"),
        ]
        sig = _comparison_input_signature(jd, files)
        self.assertEqual(sig[0], "senior python engineer")
        self.assertEqual(sig[1], (("a resume.pdf", 4), ("b.resume.pdf", 2)))

    def test_read_uploaded_cv_bytes_prefers_getvalue(self) -> None:
        upload = _FakeUpload(name="x.pdf", raw=b"abc123")
        data = _read_uploaded_cv_bytes(upload)
        self.assertEqual(data, b"abc123")

    def test_read_uploaded_cv_bytes_falls_back_to_read(self) -> None:
        upload = _GetValueFailsReadWorks(raw=b"fallback-bytes")
        data = _read_uploaded_cv_bytes(upload)
        self.assertEqual(data, b"fallback-bytes")

    def test_comparison_rows_to_csv_stable_column_order(self) -> None:
        rows = [
            {"Resume": "A.pdf", "Final Score": 91, "Issues": 3, "_analysis": {"x": 1}},
            {"Resume": "B.pdf", "Final Score": 77, "Issues": 11, "_analysis": {"x": 2}},
        ]
        columns = ["Resume", "Final Score", "Issues"]
        csv_text = _comparison_rows_to_csv(rows, columns)
        lines = [line.strip() for line in csv_text.strip().splitlines()]
        self.assertEqual(lines[0], "Resume,Final Score,Issues")
        self.assertEqual(lines[1], "A.pdf,91,3")
        self.assertEqual(lines[2], "B.pdf,77,11")
        self.assertNotIn("_analysis", csv_text)


if __name__ == "__main__":
    unittest.main()
