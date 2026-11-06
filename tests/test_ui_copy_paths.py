"""Repository paths named in the app's own copy must exist.

The Project Notes page pointed readers at src/scoring.py long after the module moved to
src/services/scoring.py, and nothing noticed: tests/test_project_guide.py checks the paths
in docs/excelcv.md, but nothing checked the in-app pages. This scans every string literal
in app.py and src/ (page copy, captions, docstrings) for repository paths and fails,
naming the line, when one does not exist.
"""

import ast
import re
import unittest
from functools import lru_cache

from tests.repo_files import REPO_ROOT
from tests.test_project_guide import _missing_paths

# A repository path: one of the top-level files, or anything under a top-level directory.
# The lookbehind keeps it from matching inside a longer path or a URL.
_PATH = re.compile(
    r"(?<![\w./-])(?:app\.py|requirements\.txt|\.env\.example"
    r"|(?:src|docs|tests|scripts|assets|data)/[\w./-]*[\w/])"
)


def path_tokens(text: str) -> set[str]:
    """Repository paths in *text*. A last segment without an extension is a directory."""
    paths = set()
    for token in _PATH.findall(text):
        last = token.rstrip("/").rsplit("/", 1)[-1]
        paths.add(token if token.endswith("/") or "." in last else token + "/")
    return paths


@lru_cache(maxsize=1)
def _named_paths() -> dict[str, list[str]]:
    """path -> ["file:line", ...] for every path named in a string literal."""
    named: dict[str, list[str]] = {}
    for path in [REPO_ROOT / "app.py", *sorted((REPO_ROOT / "src").rglob("*.py"))]:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for token in path_tokens(node.value):
                    named.setdefault(token, []).append(f"{rel}:{node.lineno}")
    return named


class UiCopyPathTests(unittest.TestCase):
    def test_pattern_finds_paths_and_skips_urls_and_names(self) -> None:
        self.assertEqual(
            path_tokens(
                "- `src/services/scoring.py`: scoring\n"
                "- `app.py` (routing), see docs/SETUP.md and src/ui\n"
                "https://example.com/src/x.py, excelcv-benchmark.json, my_src/thing.py"
            ),
            {"src/services/scoring.py", "app.py", "docs/SETUP.md", "src/ui/"},
        )

    def test_scan_reaches_the_project_notes_page(self) -> None:
        # Keeps the scan from passing vacuously if string extraction ever breaks.
        self.assertIn(
            "src/ui/static_pages.py", " ".join(_named_paths().get("src/ui/report.py", []))
        )

    def test_every_named_path_exists(self) -> None:
        named = _named_paths()
        missing = _missing_paths(set(named))
        self.assertEqual(
            [f"{path} (named at {', '.join(named[path])})" for path in missing],
            [],
            "the app's copy names paths that do not exist",
        )


if __name__ == "__main__":
    unittest.main()
