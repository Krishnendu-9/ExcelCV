"""docs/METRICS_DOCUMENTATION.md must name only functions and modules that exist."""

import builtins
import re
import unittest

from tests.repo_files import REPO_ROOT

DOC_PATH = REPO_ROOT / "docs" / "METRICS_DOCUMENTATION.md"

# An identifier directly followed by "(", with or without arguments:
# `calculate_sections(cv_text)`, `issue_count()`, scoring.get_metric_status(80, 60).
FUNCTION_REFERENCE = re.compile(r"\b([A-Za-z_]\w*)\(")

# The doc's pseudocode calls built-ins (len, max) and reads the analysis dict
# (analysis.get(...)); those are Python's, not the repository's.
NOT_REPOSITORY_CODE = set(dir(builtins)) | set(dir(dict))

# The legacy-names note names the old locations on purpose.
LEGACY_NOTE_PREFIX = "> **Note on legacy names.**"


def function_references(text: str) -> set[str]:
    return {name for name in FUNCTION_REFERENCE.findall(text) if name not in NOT_REPOSITORY_CODE}


def module_references(text: str) -> set[str]:
    """Repo-relative .py paths named in backticks or as ../ links, outside the legacy note."""
    current = "\n".join(
        line for line in text.splitlines() if not line.startswith(LEGACY_NOTE_PREFIX)
    )
    paths = set(re.findall(r"`([\w.-]+(?:/[\w.-]+)+\.py)`", current))
    paths |= set(re.findall(r"\]\(\.\./([\w./-]+\.py)\)", current))
    return paths


class FunctionReferencePatternTests(unittest.TestCase):
    """The pattern must catch references that carry arguments, not only `name()`."""

    def test_matches_references_with_and_without_arguments(self) -> None:
        self.assertEqual(
            function_references(
                "`_calculate_sections(cv_text)`, `issue_count()`, "
                "services/scoring.get_metric_status(80, 60), `len(analysis['x'])`, "
                '`analysis.get("match_score", 0)`'
            ),
            {"_calculate_sections", "issue_count", "get_metric_status"},
        )

    def test_ignores_legacy_wildcards_and_prose_parentheses(self) -> None:
        self.assertEqual(function_references("`_calculate_*` helpers, Sections (0-100)"), set())


class MetricsDocTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = DOC_PATH.read_text(encoding="utf-8")
        files = sorted((REPO_ROOT / "src").rglob("*.py")) + [REPO_ROOT / "app.py"]
        self.source = "\n".join(p.read_text(encoding="utf-8") for p in files)

    def test_names_only_functions_that_exist(self) -> None:
        names = function_references(self.doc)
        self.assertIn("calculate_tailoring", names)
        for name in sorted(names):
            with self.subTest(function=name):
                # assertIsNotNone, not assertRegex: a failing assertRegex prints all of src.
                self.assertIsNotNone(
                    re.search(rf"(?m)^\s*(?:async\s+)?def {re.escape(name)}\(", self.source),
                    f"METRICS_DOCUMENTATION.md names {name}(), which is not defined in src or app.py",
                )

    def test_names_only_modules_that_exist(self) -> None:
        paths = module_references(self.doc)
        self.assertIn("src/services/scoring.py", paths)
        for path in sorted(paths):
            with self.subTest(module=path):
                self.assertTrue(
                    (REPO_ROOT / path).is_file(),
                    f"METRICS_DOCUMENTATION.md names {path}, which does not exist",
                )


if __name__ == "__main__":
    unittest.main()
