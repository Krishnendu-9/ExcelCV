"""User-facing text must not advertise AI bullet suggestions while nothing calls them.

suggest_cv_bullets() is dormant (docs/KNOWN_ISSUES.md §5). If it is wired back into the
resume builder, the first test passes on its own and the copy can come back.
"""

import re
import unittest

from tests.repo_files import REPO_ROOT

_CLAIM = re.compile(r"bullet suggestion|ai[- ]suggest|ai bullet|suggested bullet", re.I)


def _ui_sources() -> dict[str, str]:
    paths = [REPO_ROOT / "app.py", *sorted((REPO_ROOT / "src" / "ui").rglob("*.py"))]
    paths += sorted((REPO_ROOT / "src" / "cover_letter").rglob("*.py"))
    return {p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8") for p in paths}


def _code_references(text: str) -> list[str]:
    """Lines of code (not comments) that name suggest_cv_bullets."""
    return [
        line
        for line in text.splitlines()
        if "suggest_cv_bullets" in line and not line.strip().startswith("#")
    ]


class BulletSuggestionClaimTests(unittest.TestCase):
    def test_no_claim_while_the_feature_is_unreachable(self) -> None:
        ui = _ui_sources()
        if any(_code_references(text) for text in ui.values()):
            self.skipTest("suggest_cv_bullets() is wired into the UI again")
        user_facing = dict(ui)
        for doc in ("README.md", "docs/SETUP.md"):
            user_facing[doc] = (REPO_ROOT / doc).read_text(encoding="utf-8")
        hits = [
            f"{name}:{lineno}"
            for name, text in user_facing.items()
            for lineno, line in enumerate(text.splitlines(), start=1)
            if _CLAIM.search(line)
        ]
        self.assertEqual(hits, [])

    def test_the_function_really_has_no_caller(self) -> None:
        callers = [name for name, text in _ui_sources().items() if _code_references(text)]
        self.assertEqual(callers, [], "wired back in: restore the copy and update KNOWN_ISSUES §5")


if __name__ == "__main__":
    unittest.main()
