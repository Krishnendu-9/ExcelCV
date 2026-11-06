"""docs/excelcv.md must describe the repository that exists.

The guide's header lists what this file checks. In short: every path it names exists, its
layout section covers every directory and every file in the directories it says it lists in
full, and its route map, protected pages, final-score weights, database models, required
settings, functions and constants match the code.

Not checked, because they are prose and a test would only restate them: the feature
descriptions in section 4 and the gaps in section 8.
"""

import ast
import posixpath
import re
import subprocess
import unittest
from functools import lru_cache

from src.services.scoring import calculate_final_score_breakdown
from tests.repo_files import REPO_ROOT, repo_text_files
from tests.test_metrics_doc import function_references
from tests.test_setup_doc import _github_slug

DOC_REL = "docs/excelcv.md"

_PATH_SUFFIXES = (
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".tpl",
    ".db",
    ".xlsx",
    ".pdf",
    ".png",
    ".svg",
    ".example",
    ".gitkeep",
    ".gitignore",
    ".gitattributes",
)
_DOTFILES = frozenset({".gitignore", ".gitattributes"})


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _doc() -> str:
    return _read(DOC_REL)


def _section(number: int) -> str:
    """The text of `## <number>) ...` up to the next top-level numbered section."""
    parts = re.split(r"(?m)^## (\d+)\) ", _doc())
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == str(number):
            return parts[i + 1]
    raise AssertionError(f"{DOC_REL} has no section {number})")


def _subsections(text: str) -> dict[str, str]:
    """`### heading` -> body, for every level-3 heading in *text*."""
    parts = re.split(r"(?m)^### (.+)$", text)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


@lru_cache(maxsize=1)
def _repo_files() -> frozenset[str]:
    """Repo-relative paths of every file git would commit, .env.example included.

    repo_text_files() leaves out .env* files so content scans never read secrets; this
    check only needs names, and the guide names .env.example.
    """
    # -z: raw names, so the two non-ASCII asset names are not C-quoted.
    result = subprocess.run(
        ["git", "ls-files", "-z", "-co", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        return frozenset(name for name in result.stdout.split("\0") if name)
    return frozenset(p.relative_to(REPO_ROOT).as_posix() for p in repo_text_files())


def path_references(text: str) -> set[str]:
    """Repo-relative paths named in inline code or as relative links (from docs/)."""
    prose = re.sub(r"(?ms)^```.*?^```", "", text)
    paths = set()
    for token in re.findall(r"`([^`\s]+)`", prose):
        if re.search(r"[()=<>*?@:,]", token):
            continue
        if re.fullmatch(r"\.[a-z]+", token) and token not in _DOTFILES:
            continue  # a bare extension such as `.pdf`, not a path
        if "/" in token or token.endswith(_PATH_SUFFIXES):
            paths.add(token)
    for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)", prose):
        if "://" not in link:
            paths.add(posixpath.normpath(posixpath.join("docs", link)))
    return paths


def _db_path_is_data_excelcv_db() -> bool:
    from src import database

    return database.DB_PATH == str(REPO_ROOT / "data" / "excelcv.db")


def _report_scripts_write_docs_submission() -> bool:
    line = '_OUT_DIR = _REPO_ROOT / "docs" / "submission"'
    return all(
        line in _read(f"scripts/{name}")
        for name in ("generate_minor_report.py", "generate_changes_report.py")
    )


# Named on purpose although git does not track them: each is created at run time, and
# the check ties the name to the code that creates it.
_RUNTIME_PATHS = {
    "data/excelcv.db": _db_path_is_data_excelcv_db,
    "docs/submission/": _report_scripts_write_docs_submission,
}


def _missing_paths(paths: set[str]) -> list[str]:
    files = _repo_files()
    missing = []
    for path in sorted(paths):
        if path in _RUNTIME_PATHS:
            if not _RUNTIME_PATHS[path]():
                missing.append(f"{path} (no longer created where the guide says)")
        elif path.endswith("/"):
            if not any(f.startswith(path) for f in files):
                missing.append(path)
        elif path not in files:
            missing.append(path)
    return missing


class PathReferenceTests(unittest.TestCase):
    def test_pattern_finds_paths_and_skips_code(self) -> None:
        found = path_references(
            "`CLAUDE.md`, `src/ui/`, `.env.example`, `data/.gitkeep`, "
            "[guide](../tests/test_project_guide.py), [issues](KNOWN_ISSUES.md#4-x), "
            '`excelcv_session`, `mode="no_jd"`, `render_guide_article()`, `?rid=`, `.pdf`, '
            "`@property --hv-p`, `APP_PAGES`\n```bash\npy -3 -m pip install -r requirements.txt\n```"
        )
        self.assertEqual(
            found,
            {
                "CLAUDE.md",
                "src/ui/",
                ".env.example",
                "data/.gitkeep",
                "tests/test_project_guide.py",
                "docs/KNOWN_ISSUES.md",
            },
        )

    def test_every_named_path_exists(self) -> None:
        paths = path_references(_doc())
        self.assertIn("src/prompt_fence.py", paths)
        self.assertEqual(
            _missing_paths(paths),
            [],
            f"{DOC_REL} names paths that git does not track",
        )

    def test_every_runtime_path_is_still_named(self) -> None:
        paths = path_references(_doc())
        for path in _RUNTIME_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, paths, "stale entry in _RUNTIME_PATHS")

    def test_every_link_anchor_resolves(self) -> None:
        anchors = re.findall(r"\]\(([\w.-]+\.md)#([\w-]+)\)", _doc())
        self.assertTrue(anchors)
        for target, anchor in anchors:
            with self.subTest(link=f"{target}#{anchor}"):
                headings = re.findall(r"(?m)^#{1,6} (.+)$", _read(f"docs/{target}"))
                self.assertIn(anchor, {_github_slug(h) for h in headings})


class LayoutCoverageTests(unittest.TestCase):
    """Section 7 must not silently fall behind the repository it orients a reader in."""

    def test_names_every_directory(self) -> None:
        named = path_references(_section(7))
        directories = {
            "/".join(parts[: i + 1]) + "/"
            for parts in (f.split("/") for f in _repo_files())
            for i in range(len(parts) - 1)
        }
        unnamed = sorted(d for d in directories if not any(p.startswith(d) for p in named))
        self.assertEqual(unnamed, [], "directories with no line in section 7")

    def test_lists_in_full_what_it_says_it_lists_in_full(self) -> None:
        section = _section(7)
        full_dirs = re.findall(r"(?m)^- `([^`]+/)` \(all (?:files|top-level modules)\)", section)
        self.assertIn("src/", full_dirs)
        self.assertIn("### Root (all files)", section)
        named = path_references(_doc())
        expected = {f for f in _repo_files() if "/" not in f}
        for directory in full_dirs:
            expected |= {
                f
                for f in _repo_files()
                if f.startswith(directory) and "/" not in f[len(directory) :]
            }
        unnamed = sorted(f for f in expected if f not in named and not f.endswith("__init__.py"))
        self.assertEqual(unnamed, [], "files missing from a list that says it is complete")

    def test_largest_module_claim(self) -> None:
        sizes = {f: len(_read(f).splitlines()) for f in _repo_files() if f.endswith(".py")}
        self.assertEqual(max(sizes, key=lambda f: sizes[f]), "src/ui/cv_builder_page.py")


def _literal_keys(rel: str, name: str) -> set[str]:
    """Keys of the dict, or members of the set, literal assigned to *name* in *rel*."""
    for node in ast.walk(ast.parse(_read(rel))):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            items = value.keys if isinstance(value, ast.Dict) else getattr(value, "elts", [])
            return {k.value for k in items if isinstance(k, ast.Constant)}
    raise AssertionError(f"{name} is not assigned in {rel}")


def _route_keys(text: str) -> set[str]:
    return set(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`", text))


class RouteMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.subs = _subsections(_section(3))

    def _sub(self, prefix: str) -> str:
        bodies = [body for heading, body in self.subs.items() if heading.startswith(prefix)]
        self.assertEqual(len(bodies), 1, f"section 3 needs one '### {prefix}...' subsection")
        return bodies[0]

    def test_lists_every_registered_page_and_no_other(self) -> None:
        listed = (
            _route_keys(self._sub("Main user flows"))
            | _route_keys(self._sub("Informational pages"))
            | _route_keys(self._sub("Guide articles"))
        )
        self.assertEqual(listed, _literal_keys("src/ui/app_utils.py", "APP_PAGES"))

    def test_guide_articles_are_the_guides(self) -> None:
        guides = _literal_keys("src/ui/guides.py", "GUIDES_META")
        self.assertEqual(_route_keys(self._sub("Guide articles")), guides)
        prose = {
            posixpath.basename(f)[: -len(".md")]
            for f in _repo_files()
            if f.startswith("docs/guides/") and f.endswith(".md")
        }
        self.assertEqual(prose, guides, "the guide says each guide has a docs/guides/ file")

    def test_informational_pages_are_rendered_by_static_pages(self) -> None:
        source = _read("src/ui/static_pages.py")
        for key in _route_keys(self._sub("Informational pages")):
            with self.subTest(page=key):
                self.assertIn(f'page_key == "{key}"', source)

    def test_protected_pages_match_app_py(self) -> None:
        self.assertEqual(
            _route_keys(self._sub("Protected pages")),
            _literal_keys("app.py", "PROTECTED_PAGES"),
        )


class ScoringAndModelTests(unittest.TestCase):
    def _documented_weights(self, mode: str) -> dict[str, float]:
        block = _section(5).split(f'`mode="{mode}"`', 1)[1].split("\n\n", 1)[0]
        return {label: float(w) for label, w in re.findall(r"(?m)^- (.+?): (\d\.\d+)$", block)}

    def test_final_score_weights_match_the_code(self) -> None:
        for has_jd, mode in ((True, "jd_aligned"), (False, "no_jd")):
            with self.subTest(mode=mode):
                result = calculate_final_score_breakdown(
                    ats_parse_rate=50,
                    quant_score=50,
                    repetition_score=50,
                    spelling_score=50,
                    tailoring_score=50,
                    sections_score=50,
                    ats_essentials_score=50,
                    contact_score=50,
                    has_job_description=has_jd,
                )
                self.assertEqual(result["mode"], mode)
                actual = {c["label"]: c["weight"] for c in result["components"]}
                self.assertEqual(self._documented_weights(mode), actual)

    def test_database_models_match_src_database(self) -> None:
        documented = set(re.findall(r"(?m)^- `([A-Z]\w*)`", _section(6)))
        models = {
            node.name
            for node in ast.parse(_read("src/database.py")).body
            if isinstance(node, ast.ClassDef)
            and any(isinstance(b, ast.Name) and b.id == "Base" for b in node.bases)
        }
        self.assertEqual(documented, models)

    def test_required_settings_match_setup_md(self) -> None:
        block = _section(9).split("Required settings", 1)[1].split("\n\n", 1)[0]
        documented = set(re.findall(r"(?m)^- `([A-Z_]+)`$", block))
        required = _read("docs/SETUP.md").split("### Required", 1)[1].split("###", 1)[0]
        self.assertEqual(documented, set(re.findall(r"(?m)^\| `([A-Z_]+)` \|", required)))


class CodeReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        files = sorted((REPO_ROOT / "src").rglob("*.py")) + [REPO_ROOT / "app.py"]
        self.source = "\n".join(p.read_text(encoding="utf-8") for p in files)

    def test_names_only_functions_that_exist(self) -> None:
        names = function_references(_doc())
        self.assertIn("render_guide_article", names)
        missing = sorted(
            name
            for name in names
            if not re.search(rf"(?m)^\s*(?:async\s+)?def {re.escape(name)}\(", self.source)
        )
        self.assertEqual(missing, [], f"{DOC_REL} names functions not defined in src or app.py")

    def test_names_only_constants_and_settings_that_exist(self) -> None:
        names = set(re.findall(r"`([A-Z][A-Z0-9_]{2,})`", _doc()))
        self.assertIn("PROTECTED_PAGES", names)
        missing = sorted(
            name
            for name in names
            if not re.search(rf"(?m)^\s*{name}\s*[:=]", self.source)
            and f'"{name}"' not in self.source
        )
        self.assertEqual(missing, [], f"{DOC_REL} names constants or settings the code lacks")


if __name__ == "__main__":
    unittest.main()
