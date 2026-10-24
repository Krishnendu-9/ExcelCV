import importlib.util
import unittest
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "pip_audit_ignores", _REPO_ROOT / "scripts" / "pip_audit_ignores.py"
)
pip_audit_ignores = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pip_audit_ignores)

_TODAY = date(2026, 10, 24)


def _parse(text: str):
    return pip_audit_ignores.parse_ignore_list(text, today=_TODAY)


class IgnoreListTests(unittest.TestCase):
    def test_valid_entries_become_ignore_args(self) -> None:
        entries = _parse(
            "# comment\n\n"
            "PYSEC-2026-1835 | 2026-10-20 | Unreachable fallback import; removed next release.\n"
            "GHSA-4vvm-4w3v-6mr8 | 2026-10-21 | Same advisory, GHSA alias, same justification.\n"
        )
        self.assertEqual(
            pip_audit_ignores.ignore_args(entries),
            ["--ignore-vuln", "PYSEC-2026-1835", "--ignore-vuln", "GHSA-4vvm-4w3v-6mr8"],
        )
        self.assertEqual(entries[0].added, date(2026, 10, 20))

    def test_entry_without_reason_is_rejected(self) -> None:
        for line in (
            "PYSEC-2026-1835 | 2026-10-20 |",
            "PYSEC-2026-1835 | 2026-10-20 | ok",
            "PYSEC-2026-1835 | 2026-10-20",
            "PYSEC-2026-1835",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                _parse(line)

    def test_entry_without_valid_date_is_rejected(self) -> None:
        for line in (
            "PYSEC-2026-1835 | | Unreachable fallback import.",
            "PYSEC-2026-1835 | 20/10/2026 | Unreachable fallback import.",
            "PYSEC-2026-1835 | 2026-10-25 | Future-dated entries are not allowed.",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                _parse(line)

    def test_bad_id_and_duplicates_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _parse("pypdf2 | 2026-10-20 | A package name is not an advisory ID.")
        with self.assertRaises(ValueError):
            _parse(
                "PYSEC-2026-1835 | 2026-10-20 | First listing of this advisory.\n"
                "PYSEC-2026-1835 | 2026-10-21 | Second listing of this advisory.\n"
            )

    def test_committed_list_is_valid(self) -> None:
        text = (_REPO_ROOT / ".github" / "pip-audit-ignore.txt").read_text(encoding="utf-8")
        pip_audit_ignores.parse_ignore_list(text)

    def test_main_fails_on_malformed_list(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "ignore.txt"
            bad.write_text("PYSEC-2026-1835 | 2026-10-20 |\n", encoding="utf-8")
            self.assertEqual(pip_audit_ignores.main(["x", str(bad)]), 1)
            good = Path(tmp) / "empty.txt"
            good.write_text("# nothing ignored\n", encoding="utf-8")
            self.assertEqual(pip_audit_ignores.main(["x", str(good)]), 0)


if __name__ == "__main__":
    unittest.main()
