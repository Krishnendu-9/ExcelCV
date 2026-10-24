"""Dependency hygiene: no PyPDF2, no Google Cloud project ids in committed files."""

import re
import unittest
from pathlib import Path

from src import pdf_utils
from tests.repo_files import REPO_ROOT, repo_text_files, requirement_names


class DependencyTests(unittest.TestCase):
    def test_pypdf2_is_not_a_dependency(self) -> None:
        names = requirement_names(REPO_ROOT / "requirements.txt")
        self.assertIn("pypdf", names)
        self.assertNotIn("pypdf2", names)

    def test_pdf_utils_uses_pypdf_only(self) -> None:
        self.assertTrue(pdf_utils.PdfReader.__module__.startswith("pypdf."))
        source = Path(pdf_utils.__file__).read_text(encoding="utf-8")
        self.assertNotIn("PyPDF2", source)


class NoCloudProjectIdTests(unittest.TestCase):
    def test_no_google_cloud_project_ids_in_repo_files(self) -> None:
        pattern = re.compile(r"gen-lang-client-\d{6,}|[?&]project=[a-z][a-z0-9-]{5,}")
        hits = []
        for path in repo_text_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if pattern.search(text):
                hits.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(hits, [])

    def test_requirements_comment_keeps_the_api_key_pointer(self) -> None:
        text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("https://aistudio.google.com/api-keys", text)


if __name__ == "__main__":
    unittest.main()
