"""SQLite connection settings. Uses a temp-file database, never data/excelcv.db."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from src import database

_REPO_ROOT = Path(__file__).resolve().parent.parent


class SqlitePragmaTests(unittest.TestCase):
    def test_fresh_connection_gets_wal_busy_timeout_and_foreign_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = database.create_sqlite_engine(str(Path(tmp) / "pragma_test.db"))
            try:
                with engine.connect() as conn:
                    journal = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
                    busy = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
                    fks = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
            finally:
                engine.dispose()  # release the file so the temp dir can be removed

        self.assertEqual(str(journal).lower(), "wal")
        # Differs from the sqlite3 driver's own 5000 ms default, so this proves the
        # pragma is applied rather than inherited.
        self.assertEqual(busy, database.SQLITE_BUSY_TIMEOUT_MS)
        self.assertNotEqual(busy, 5000)
        self.assertEqual(fks, 1)

    def test_app_engine_uses_the_configured_factory(self) -> None:
        # Inspect the listener registration only; never connect to the real database.
        from sqlalchemy import event

        self.assertTrue(event.contains(database.engine, "connect", database._set_sqlite_pragma))

    def test_wal_side_files_are_gitignored(self) -> None:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=_REPO_ROOT, capture_output=True
        )
        if inside.returncode != 0:
            self.skipTest("not a git work tree (CI checkouts are)")
        for name in ("excelcv.db", "excelcv.db-wal", "excelcv.db-shm", "excelcv.db-journal"):
            with self.subTest(name=name):
                result = subprocess.run(
                    ["git", "check-ignore", "-q", f"data/{name}"],
                    cwd=_REPO_ROOT,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, f"data/{name} is not gitignored")


if __name__ == "__main__":
    unittest.main()
