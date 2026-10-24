"""docs/SETUP.md must not contradict the README or the code."""

import re
import unittest

from src import config
from tests.repo_files import REPO_ROOT


class SetupDocTests(unittest.TestCase):
    """docs/SETUP.md must not contradict the README or the code."""

    def setUp(self) -> None:
        self.setup = (REPO_ROOT / "docs" / "SETUP.md").read_text(encoding="utf-8")

    def test_documents_playwright_chromium_install(self) -> None:
        install_section = self.setup.split("## 2) Install Dependencies", 1)[1].split("\n## ", 1)[0]
        self.assertIn("-m playwright install chromium", install_section)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("playwright install chromium", readme)

    def test_session_secret_is_documented_as_required_and_guarded(self) -> None:
        required = self.setup.split("### Required", 1)[1].split("###", 1)[0]
        row = re.search(r"(?m)^\| `SESSION_SECRET` \|(.*)\|\s*$", required)
        self.assertIsNotNone(row, "SESSION_SECRET is not a row of the Required table")
        row_text = row.group(1)
        self.assertIn("refuses to start", row_text)
        self.assertIn("placeholder", row_text)
        self.assertIn(str(config.SESSION_SECRET_MIN_LENGTH), row_text)
        self.assertIn(config.SESSION_SECRET_GENERATOR.split('"', 1)[1].rstrip('"'), row_text)
        self.assertNotIn("excelcv-session-key-change-in-prod", self.setup)

    def test_no_stale_settings(self) -> None:
        self.assertNotIn("runOnSave = true", self.setup)
        self.assertNotIn("5242880", self.setup)
        self.assertNotIn("Python 3.11", self.setup)


if __name__ == "__main__":
    unittest.main()
