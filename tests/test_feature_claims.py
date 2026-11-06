"""Text must not describe dormant code as if it ran.

suggest_cv_bullets() is dormant (docs/KNOWN_ISSUES.md §5). If it is wired back into the
resume builder, the first test passes on its own and the copy can come back.

blend_scores() has no caller: every score is computed in code and the model's scores are
discarded. If it is called again, the blending test skips itself and the claim can return.
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


# A line that names the model and mixing: "optional AI blend", "blend_scores averages AI +
# programmatic", "averaged with the AI score". Naming blend_scores at all counts.
_MODEL = re.compile(r"\bAI\b|Gemini|\bmodel\b|blend_scores", re.I)
_MIXING = re.compile(r"blend|averag", re.I)

# The metrics doc explains the scores; the report script prints its text into a report.
_SCORING_DESCRIPTIONS = ("docs/METRICS_DOCUMENTATION.md", "scripts/generate_minor_report.py")


def _is_blending_claim(line: str) -> bool:
    return bool(_MODEL.search(line) and _MIXING.search(line))


def _blend_scores_callers() -> list[str]:
    """Lines in src/ and app.py, other than comments and the definition, naming blend_scores."""
    paths = [REPO_ROOT / "app.py", *sorted((REPO_ROOT / "src").rglob("*.py"))]
    return [
        f"{p.relative_to(REPO_ROOT).as_posix()}:{lineno}"
        for p in paths
        for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1)
        if "blend_scores" in line and not line.strip().startswith(("#", "def blend_scores("))
    ]


class ScoreBlendingClaimTests(unittest.TestCase):
    def test_pattern_tells_claims_from_denials(self) -> None:
        for claim in (
            "- **Final Score**: Average of programmatic base score and AI-provided parse rate",
            "| ATS Parse Rate score | App + AI blend | blended via blend_scores |",
            '"metrics → blend_scores averages AI + programmatic where both exist.",',
        ):
            with self.subTest(claim=claim):
                self.assertTrue(_is_blending_claim(claim))
        for denial in (
            "- The model's `sections_metrics` value is discarded.",
            "Content score = unweighted average of `ats_parse_rate`, `quantifying_impact.score`",
        ):
            with self.subTest(denial=denial):
                self.assertFalse(_is_blending_claim(denial))

    def test_no_blending_claim_while_blend_scores_has_no_caller(self) -> None:
        if _blend_scores_callers():
            self.skipTest("blend_scores() is called again")
        hits = [
            f"{name}:{lineno}: {line.strip()}"
            for name in _SCORING_DESCRIPTIONS
            for lineno, line in enumerate(
                (REPO_ROOT / name).read_text(encoding="utf-8").splitlines(), start=1
            )
            if _is_blending_claim(line)
        ]
        self.assertEqual(hits, [])

    def test_blend_scores_really_has_no_caller(self) -> None:
        self.assertEqual(
            _blend_scores_callers(),
            [],
            "called again: the metrics doc and the report script may describe blending again",
        )


if __name__ == "__main__":
    unittest.main()
