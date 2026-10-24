"""CI and pre-commit configuration: mypy, pip-audit, one formatter."""

import re
import tomllib
import unittest

from tests.repo_files import REPO_ROOT, requirement_names


class ToolingTests(unittest.TestCase):
    """CI and pre-commit configuration (checked as text; PyYAML is not a dependency)."""

    def _ci(self) -> str:
        return (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_ci_runs_mypy(self) -> None:
        self.assertRegex(self._ci(), r"(?m)^\s+mypy app\.py src\s*$")
        self.assertIn("mypy", requirement_names(REPO_ROOT / "requirements-dev.txt"))

    def test_ci_runs_pip_audit_failing_on_any_advisory(self) -> None:
        ci = self._ci()
        self.assertIn("pip_audit_ignores.py .github/pip-audit-ignore.txt", ci)
        self.assertRegex(ci, r"(?m)^\s+pip-audit --strict\b.*\$ignore_args\s*$")
        # pip-audit has no severity gate; make sure nobody bolts one on (comments excepted).
        commands = "\n".join(ln for ln in ci.lower().splitlines() if not ln.strip().startswith("#"))
        self.assertNotRegex(commands, r"severity|cvss|--fail-on|\|\| *true|continue-on-error")
        self.assertIn("pip-audit", requirement_names(REPO_ROOT / "requirements-dev.txt"))

    def test_actions_are_on_node24_majors(self) -> None:
        # checkout and setup-python v7 run on node24; v4/v5 target the deprecated node20.
        uses = dict(re.findall(r"uses: (actions/[\w-]+)@v(\d+)", self._ci()))
        self.assertEqual(set(uses), {"actions/checkout", "actions/setup-python"})
        for action, major in uses.items():
            with self.subTest(action=action):
                self.assertGreaterEqual(int(major), 7)

    def test_runner_image_is_pinned(self) -> None:
        runs_on = re.findall(r"(?m)^\s+runs-on: (\S+)\s*$", self._ci())
        self.assertEqual(runs_on, ["ubuntu-26.04"])

    def test_one_formatter_ruff_format(self) -> None:
        pre_commit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        self.assertIn("id: ruff-format", pre_commit)
        self.assertNotIn("psf/black", pre_commit)
        self.assertNotIn("black", requirement_names(REPO_ROOT / "requirements-dev.txt"))
        with open(REPO_ROOT / "pyproject.toml", "rb") as fh:
            self.assertNotIn("black", tomllib.load(fh).get("tool", {}))


if __name__ == "__main__":
    unittest.main()
