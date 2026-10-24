"""Shared helpers for tests that check committed repository files."""

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SKIP_DIRS = {".git", "data", "__pycache__", ".venv", "venv", ".mypy_cache", ".ruff_cache"}


def requirement_names(path: Path) -> set[str]:
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].lower())
    return names


def repo_text_files() -> list[Path]:
    """Files git would commit (tracked + untracked-not-ignored), never .env files."""
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        paths = [REPO_ROOT / line for line in result.stdout.splitlines() if line]
    else:  # not a git work tree: walk, skipping data and tool directories
        paths = []
        for root, dirs, files in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            paths.extend(Path(root) / name for name in files)
    return [p for p in paths if not p.name.startswith(".env") and p.is_file()]
