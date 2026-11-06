"""Text must not describe dormant code as if it ran.

suggest_cv_bullets() is dormant (docs/KNOWN_ISSUES.md §5). If it is wired back into the
resume builder, the first test passes on its own and the copy can come back.

blend_scores() has no caller: every score is computed in code and the model's scores are
discarded. If it is called again, the blending test skips itself and the claim can return.

Six report enrichments are built into every analysis but nothing reads them
(docs/KNOWN_ISSUES.md §6). Each one's check skips itself once something reads its key.
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


# Analysis-dict key -> how user-facing text would advertise it.
_UNREAD_ENRICHMENTS = {
    "jd_skill_matrix": r"skill matrix|evidence matrix",
    "rewrite_recommendations": r"rewrite assistant|before\s*(?:→|->)\s*after",
    "recruiter_snapshot": r"recruiter snapshot|hiring summary",
    "priority_action_plan": r"action plan",
    "learning_roadmap": r"learning roadmap|skill[- ]gap closure",
    "portfolio_checklist": r"portfolio checklist|readiness check",
}

_USER_FACING_DOCS = ("README.md", "docs/SETUP.md", "docs/excelcv.md")


def _quoted_use(key: str) -> re.Pattern[str]:
    """*key* as a string literal, except as a dict-literal key (`"key": value`)."""
    return re.compile(rf"""["']{re.escape(key)}["'](?!\s*:)""")


def _key_readers(key: str) -> list[str]:
    """Lines in src/ and app.py that use *key* as a string, other than storing it.

    analyze_cv_with_gemini() stores each one as `"key": value`. Any other quoted use
    (a .get(), a subscript, a list of key names to loop over) counts as a reader.
    """
    quoted = _quoted_use(key)
    paths = [REPO_ROOT / "app.py", *sorted((REPO_ROOT / "src").rglob("*.py"))]
    return [
        f"{p.relative_to(REPO_ROOT).as_posix()}:{lineno}"
        for p in paths
        for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1)
        if quoted.search(line) and not line.strip().startswith("#")
    ]


class UnreadEnrichmentClaimTests(unittest.TestCase):
    def test_no_claim_while_nothing_reads_it(self) -> None:
        user_facing = dict(_ui_sources())
        for doc in _USER_FACING_DOCS:
            user_facing[doc] = (REPO_ROOT / doc).read_text(encoding="utf-8")
        for key, claim in _UNREAD_ENRICHMENTS.items():
            with self.subTest(feature=key):
                if _key_readers(key):
                    self.skipTest(f"{key} has a reader again")
                pattern = re.compile(claim, re.I)
                hits = [
                    f"{name}:{lineno}: {line.strip()}"
                    for name, text in user_facing.items()
                    for lineno, line in enumerate(text.splitlines(), start=1)
                    if pattern.search(line)
                ]
                self.assertEqual(hits, [], f"advertises {key}, which nothing renders")

    def test_they_really_have_no_reader(self) -> None:
        for key in _UNREAD_ENRICHMENTS:
            with self.subTest(feature=key):
                self.assertEqual(
                    _key_readers(key),
                    [],
                    f"{key} is read again: restore its copy and update KNOWN_ISSUES §6",
                )

    def test_reader_detection_ignores_storage_and_catches_reads(self) -> None:
        storing = _quoted_use("jd_skill_matrix")
        self.assertIsNone(storing.search('        "jd_skill_matrix": jd_skill_matrix,'))
        for read in (
            'analysis.get("jd_skill_matrix", [])',
            "analysis['jd_skill_matrix']",
            'for key in ("jd_skill_matrix", "learning_roadmap"):',
        ):
            with self.subTest(read=read):
                self.assertIsNotNone(storing.search(read))


if __name__ == "__main__":
    unittest.main()
