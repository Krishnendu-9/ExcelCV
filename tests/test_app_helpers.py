import unittest

from app import _sanitize_cv_filename


class AppHelperTests(unittest.TestCase):
    def test_sanitize_cv_filename_removes_path_segments_and_bad_chars(self) -> None:
        raw = "..\\folder/<my>:cv?.pdf\n"
        safe = _sanitize_cv_filename(raw)
        self.assertEqual(safe, "-my-cv-.pdf")

    def test_sanitize_cv_filename_fallback(self) -> None:
        self.assertEqual(_sanitize_cv_filename("   "), "CV.pdf")


if __name__ == "__main__":
    unittest.main()

