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


class SetupInputCapTests(unittest.TestCase):
    def test_setup_states_the_cv_cap_default(self) -> None:
        from src import gemini_client

        setup = (REPO_ROOT / "docs" / "SETUP.md").read_text(encoding="utf-8")
        default = gemini_client.DEFAULT_MAX_CV_INPUT_CHARS
        self.assertRegex(setup, rf"\| `GEMINI_MAX_CV_CHARS` \|.*\| `{default}` \|")
        self.assertNotIn("`120000`", setup)


def _github_slug(heading: str) -> str:
    slug = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return slug.replace(" ", "-")


class KnownIssuesDocTests(unittest.TestCase):
    """docs/KNOWN_ISSUES.md records the unfixed throttling problem; SETUP.md points to it."""

    def setUp(self) -> None:
        self.doc = (REPO_ROOT / "docs" / "KNOWN_ISSUES.md").read_text(encoding="utf-8")
        self.setup = (REPO_ROOT / "docs" / "SETUP.md").read_text(encoding="utf-8")
        self.slugs = {_github_slug(m.group(1)) for m in re.finditer(r"(?m)^#{1,6} (.+)$", self.doc)}

    def test_setup_links_it_before_the_setup_steps(self) -> None:
        before_steps = self.setup.split("## 1) Prerequisites", 1)[0]
        self.assertIn("(KNOWN_ISSUES.md)", before_steps)

    def test_every_link_into_the_doc_resolves(self) -> None:
        anchors = re.findall(r"KNOWN_ISSUES\.md#([\w-]+)", self.setup)
        anchors += re.findall(r"\]\(#([\w-]+)\)", self.doc)
        self.assertTrue(anchors)
        for anchor in anchors:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.slugs)

    def test_states_it_is_unfixed_and_why(self) -> None:
        self.assertIn("**Status: unfixed, deliberately.**", self.doc)
        self.assertIn("No production deployment exists yet", self.doc)

    def test_covers_the_three_problems_the_fix_and_the_deployment_facts(self) -> None:
        for text in (
            "The client identity comes from headers the client controls.",
            "Anyone can lock any account, and keep it locked indefinitely.",
            "Anyone can block password resets for any address.",
            "### Proposed fix",
            "### Deployment facts the fix depends on",
            "### Why there is no safe default",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.doc)
        proposal = self.doc.split("### Proposed fix", 1)[1].split("\n### ", 1)[0]
        self.assertEqual(len(re.findall(r"(?m)^\d\. \*\*", proposal)), 4)

    def test_names_only_code_and_settings_that_exist(self) -> None:
        from src import auth_utils

        for name in set(re.findall(r"`(_?\w+)\(\)`", self.doc)):
            with self.subTest(function=name):
                self.assertTrue(hasattr(auth_utils, name), f"{name}() is not in auth_utils")
        source = (REPO_ROOT / "src" / "auth_utils.py").read_text(encoding="utf-8")
        for setting in set(re.findall(r"`(AUTH_[A-Z_]+)`", self.doc)):
            with self.subTest(setting=setting):
                self.assertIn(f'"{setting}"', source)


if __name__ == "__main__":
    unittest.main()
