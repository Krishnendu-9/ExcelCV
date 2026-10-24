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
        source = "\n".join(
            p.read_text(encoding="utf-8") for p in sorted((REPO_ROOT / "src").rglob("*.py"))
        )
        for name in set(re.findall(r"`(_?\w+)\(\)`", self.doc)):
            with self.subTest(function=name):
                self.assertRegex(
                    source, rf"(?m)^\s*def {re.escape(name)}\(", f"{name}() not in src"
                )
        for setting in set(re.findall(r"`((?:AUTH|GEMINI|SMTP)_[A-Z_]+)`", self.doc)):
            with self.subTest(setting=setting):
                self.assertIn(f'"{setting}"', source)

    def test_records_the_abuse_findings_as_unfixed_with_their_dependencies(self) -> None:
        for heading in (
            "## 2. The Gemini rate limit counts user actions, not API calls",
            "## 3. Anyone can register any number of accounts",
        ):
            with self.subTest(heading=heading):
                section = self.doc.split(heading, 1)[1].split("\n## ", 1)[0]
                self.assertIn("**Status: unfixed, deliberately.**", section)
                for part in ("### What it is", "### When it starts to matter"):
                    self.assertIn(part, section)
                self.assertIn("### What the fix depends on", section)

    def test_notes_that_sign_in_checks_live_in_the_ui_layer(self) -> None:
        section = self.doc.split("## 4. Sign-in checks for AI features live in the UI layer", 1)[1]
        section = section.split("\n## ", 1)[0]
        self.assertIn("Cover Letter", section)
        self.assertIn("HTTP API", section)
        self.assertIn("`generate_cover_letter_draft()`", section)

    def test_records_bullet_suggestions_as_dormant_with_a_restore_plan(self) -> None:
        section = self.doc.split("## 5. Dormant: AI bullet suggestions", 1)[1]
        self.assertIn("**Status: dormant.**", section)
        self.assertIn("### What restoring it would take", section)
        for commit in ("3e0f3fb", "88f3f1a"):
            self.assertIn(commit, section)


if __name__ == "__main__":
    unittest.main()
