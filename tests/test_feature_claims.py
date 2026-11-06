"""Text must not describe dormant code as if it ran.

suggest_cv_bullets() is dormant (docs/KNOWN_ISSUES.md §5). If it is wired back into the
resume builder, the first test passes on its own and the copy can come back.

blend_scores() has no caller: every score is computed in code and the model's scores are
discarded. If it is called again, the blending test skips itself and the claim can return.

Six report enrichments are built into every analysis but nothing reads them
(docs/KNOWN_ISSUES.md §6). Each one's check skips itself once something reads its key.

The Markdown export is the inverse case: it is real, and the copy says so. That guard
fails if the report page stops offering it while any copy still promises it.

All four guards scan the same files: everything a user or a reader of the repository can
encounter (see _user_facing_lines). A claim left in any of them is still shipping.
"""

import ast
import re
import unittest
from functools import lru_cache
from typing import Any, Callable
from unittest.mock import MagicMock, patch

from tests.repo_files import REPO_ROOT, repo_text_files

# Every file git would commit with one of these suffixes is scanned, wherever it lives:
# README and docs, the in-app copy in src/ and app.py, and scripts/ (whose strings are
# printed into the project reports).
_TEXT_SUFFIXES = frozenset(
    {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".cfg", ".ini", ".tpl", ".html", ".css"}
)

# Excluded on purpose: the guards and their tests quote the claims they look for.
_EXCLUDED_PREFIXES = ("tests/",)

# Excluded on purpose: these sections record the dormant features, so they name them.
_DORMANT_SECTIONS = {"docs/KNOWN_ISSUES.md": ("## 5. Dormant", "## 6. Dormant")}

# Excluded on purpose: the definitions of the dormant functions and of the builders whose
# output nothing renders. A function's own docstring describing what it builds is not a
# claim that the user sees it.
_DORMANT_DEFINITIONS = {
    "src/gemini_client.py": ("suggest_cv_bullets",),
    "src/services/scoring.py": (
        "blend_scores",
        "build_jd_skill_matrix",
        "generate_section_rewrite_recommendations",
    ),
    "src/services/career_tools.py": (
        "build_recruiter_snapshot",
        "build_priority_action_plan",
        "build_learning_roadmap",
        "build_portfolio_checklist",
    ),
}

# Excluded on purpose, by exact line: text that matches a claim pattern but says nothing
# about this codebase. Each entry gives the reason.
_NOT_CLAIMS = {
    "src/gemini_client.py": {
        "# Build JD-to-skill evidence matrix.": "call-site comment naming what the next line builds",
    },
    "docs/METRICS_DOCUMENTATION.md": {
        "| `strengths`, `missing_skills`, `suggestions`, `missing_keywords` | Not shown. The "
        "report's Insights lists are built in code by `_derive_deterministic_insight_fallbacks` "
        "from the metrics, the tailoring details, the JD skill matrix and the rewrite "
        "recommendations. |": "says the matrix feeds the Insights lists, which is true",
    },
    "scripts/generate_minor_report.py": {
        '"Proposed hybrid AI systems combining generative AI with rule-based scoring; "': (
            "related-work table: describes a cited paper, not ExcelCV"
        ),
        '"[4] T. Miller and I. Bhattacharya, “Hybrid Generative-AI Systems with Rule-Based "': (
            "bibliography entry"
        ),
        '"error list. Combined with text truncation and model fallback, this preserves user "': (
            "about rate-limit handling, not scoring"
        ),
    },
    "scripts/generate_changes_report.py": {
        '"2.2.6 Hybrid Scoring (simple (AI+Rule)/2)",': (
            "Old PDF column: quotes a section title of the superseded report"
        ),
        "'\"Markdown / JSON export\"',": (
            "Old PDF column: quotes the superseded report's export line"
        ),
    },
}


def _section_lines(lines: list[str], heading: str) -> set[int]:
    starts = [n for n, line in enumerate(lines, start=1) if line.startswith(heading)]
    if not starts:
        return set()
    start = starts[0]
    ends = [n for n, line in enumerate(lines, start=1) if n > start and line.startswith("## ")]
    return set(range(start, ends[0] if ends else len(lines) + 1))


def _definition_lines(lines: list[str], name: str) -> set[int]:
    for node in ast.walk(ast.parse("\n".join(lines))):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return set()


def _excluded_lines(rel: str, lines: list[str]) -> set[int]:
    excluded: set[int] = set()
    for heading in _DORMANT_SECTIONS.get(rel, ()):
        excluded |= _section_lines(lines, heading)
    for name in _DORMANT_DEFINITIONS.get(rel, ()):
        excluded |= _definition_lines(lines, name)
    not_claims = _NOT_CLAIMS.get(rel, {})
    excluded |= {n for n, line in enumerate(lines, start=1) if line.strip() in not_claims}
    return excluded


@lru_cache(maxsize=1)
def _user_facing_lines() -> tuple[tuple[str, int, str], ...]:
    """(path, line number, line) for every scanned line, exclusions removed."""
    out: list[tuple[str, int, str]] = []
    for path in sorted(repo_text_files()):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if path.suffix not in _TEXT_SUFFIXES or rel.startswith(_EXCLUDED_PREFIXES):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        excluded = _excluded_lines(rel, lines)
        out.extend((rel, n, line) for n, line in enumerate(lines, start=1) if n not in excluded)
    return tuple(out)


def _hits(is_claim: Callable[[str], bool]) -> list[str]:
    return [f"{rel}:{n}: {line.strip()}" for rel, n, line in _user_facing_lines() if is_claim(line)]


class ScanScopeTests(unittest.TestCase):
    """The scan must keep covering the places these claims have actually shipped from."""

    def test_covers_docs_ui_copy_and_report_scripts(self) -> None:
        scanned = {rel for rel, _, _ in _user_facing_lines()}
        for rel in (
            "README.md",
            "docs/SETUP.md",
            "docs/excelcv.md",
            "docs/METRICS_DOCUMENTATION.md",
            "docs/KNOWN_ISSUES.md",
            "app.py",
            "src/ui/static_pages.py",
            "src/gemini_client.py",
            "scripts/generate_minor_report.py",
            "scripts/generate_changes_report.py",
        ):
            with self.subTest(file=rel):
                self.assertIn(rel, scanned)
        self.assertFalse([rel for rel in scanned if rel.startswith("tests/")])

    def test_every_exclusion_still_points_at_something(self) -> None:
        for rel, headings in _DORMANT_SECTIONS.items():
            lines = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
            for heading in headings:
                with self.subTest(section=heading):
                    self.assertTrue(_section_lines(lines, heading))
        for rel, names in _DORMANT_DEFINITIONS.items():
            lines = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
            for name in names:
                with self.subTest(definition=name):
                    self.assertTrue(_definition_lines(lines, name))
        for rel, entries in _NOT_CLAIMS.items():
            stripped = {
                line.strip() for line in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
            }
            for text in entries:
                with self.subTest(file=rel, line=text):
                    self.assertIn(text, stripped)


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
        if any(_code_references(text) for text in _ui_sources().values()):
            self.skipTest("suggest_cv_bullets() is wired into the UI again")
        self.assertEqual(_hits(lambda line: bool(_CLAIM.search(line))), [])

    def test_the_function_really_has_no_caller(self) -> None:
        callers = [name for name, text in _ui_sources().items() if _code_references(text)]
        self.assertEqual(callers, [], "wired back in: restore the copy and update KNOWN_ISSUES §5")


# A line that names the model and mixing: "optional AI blend", "blend_scores averages AI +
# programmatic", "merged with deterministic scoring", "Two-pronged scoring ... + Gemini",
# "combines them with a model-based review". Naming blend_scores at all counts.
_MODEL = re.compile(r"\bAI\b|Gemini|\bmodel\b|blend_scores", re.I)
_MIXING = re.compile(r"blend|averag|merg|combin|hybrid|two-pronged", re.I)


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
            "is explainable: the model returns structured JSON, which is merged with deterministic",
            '"- Two-pronged scoring: deterministic rules (explainability) + Gemini qualitative"',
            '"section completeness), and combines them with a model-based qualitative review. "',
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
        self.assertEqual(_hits(_is_blending_claim), [])

    def test_blend_scores_really_has_no_caller(self) -> None:
        self.assertEqual(
            _blend_scores_callers(),
            [],
            "called again: user-facing text may describe blending again",
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
        for key, claim in _UNREAD_ENRICHMENTS.items():
            with self.subTest(feature=key):
                if _key_readers(key):
                    self.skipTest(f"{key} has a reader again")
                pattern = re.compile(claim, re.I)
                hits = _hits(lambda line: bool(pattern.search(line)))
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


# Markdown named next to another export format, or as a report: "PDF, Markdown and JSON",
# "`Markdown`, `JSON`", "PDF and Markdown reports", "PDF / Markdown", "Markdown report".
_MARKDOWN_EXPORT_CLAIM = re.compile(
    r"markdown\W{0,4}(?:and|or)?\W{0,4}json"
    r"|pdf\W{0,4}(?:and|or)?\W{0,4}markdown"
    r"|markdown (?:report|export)",
    re.I,
)


def _is_markdown_export_claim(line: str) -> bool:
    return bool(_MARKDOWN_EXPORT_CLAIM.search(line))


_SAMPLE_NAME = "Jane-Doe"
_SAMPLE_ANALYSIS: dict[str, Any] = {
    "match_score": 72,
    "subscores": {"skills_alignment": 70, "experience_alignment": 65, "ats_readiness": 80},
    "strengths": ["Python"],
    "missing_skills": ["Kubernetes"],
    "missing_keywords": ["terraform"],
    "suggestions": ["Quantify impact"],
}


def _render_download_buttons_calls() -> list[dict[str, Any]]:
    """Keyword arguments of every st.download_button the report page's downloads render."""
    from src.ui import report

    fake_st = MagicMock()
    fake_st.columns.side_effect = lambda spec, **_: [
        MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]
    with patch.object(report, "st", fake_st):
        report._render_download_buttons(_SAMPLE_NAME, _SAMPLE_ANALYSIS)
    return [c.kwargs for c in fake_st.download_button.call_args_list]


def _page_calls_download_buttons() -> bool:
    """Whether render_report_page() in src/ui/report.py calls _render_download_buttons()."""
    tree = ast.parse((REPO_ROOT / "src" / "ui" / "report.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "render_report_page":
            return any(
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "_render_download_buttons"
                for call in ast.walk(node)
            )
    return False


def _markdown_export_problems() -> list[str]:
    """Why the report page does not offer build_report_md() as a download; empty if it does."""
    from src.services.reporting import build_report_md

    problems = []
    if not _page_calls_download_buttons():
        problems.append("render_report_page() no longer calls _render_download_buttons()")
    markdown = [kw for kw in _render_download_buttons_calls() if kw.get("mime") == "text/markdown"]
    if not markdown:
        problems.append("_render_download_buttons() renders no text/markdown download")
    for kw in markdown:
        if kw.get("data") != build_report_md(_SAMPLE_NAME, _SAMPLE_ANALYSIS):
            problems.append("the text/markdown download is not build_report_md(name, analysis)")
        if kw.get("file_name") != f"{_SAMPLE_NAME}-analysis.md":
            problems.append(f"unexpected Markdown file name: {kw.get('file_name')!r}")
    return problems


class MarkdownExportClaimTests(unittest.TestCase):
    def test_pattern_tells_export_claims_from_other_markdown(self) -> None:
        for claim in (
            '"- Downloadable PDF, Markdown and JSON reports"',
            '"- Export support (`PDF`, `Markdown`, `JSON`) for demos and portfolio records"',
            "alignment, ATS readiness) for the downloadable PDF and Markdown reports; it sets no",
            "    reporting.py              — Analysis report PDF / Markdown",
            "- Download Markdown report",
            '"(ReportLab), Markdown or JSON; cover letters as DOCX; comparison results as CSV or PDF. "',
        ):
            with self.subTest(claim=claim):
                self.assertTrue(_is_markdown_export_claim(claim))
        for other in (
            "Gemini drafts the letter, which renders as Markdown and downloads as DOCX.",
            "CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no code blocks,",
            "Ask model to respond only in valid JSON, no markdown.",
            '"Robust JSON extraction tolerant of markdown wrappers and partial responses.",',
        ):
            with self.subTest(other=other):
                self.assertFalse(_is_markdown_export_claim(other))

    def test_offered_while_the_copy_promises_it(self) -> None:
        claims = _hits(_is_markdown_export_claim)
        if not claims:
            self.skipTest("nothing promises a Markdown export")
        self.assertEqual(
            _markdown_export_problems(),
            [],
            "the copy promises a Markdown export the report page does not offer:\n"
            + "\n".join(claims),
        )


if __name__ == "__main__":
    unittest.main()
