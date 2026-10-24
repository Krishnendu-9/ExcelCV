"""Turn the pip-audit ignore list into --ignore-vuln arguments, validating every entry.

Each non-comment line of the list is::

    <ADVISORY-ID> | <YYYY-MM-DD the entry was added> | <reason it is safe to ignore>

All three fields are required. A malformed, duplicate or future-dated entry is an error,
so CI fails instead of silently ignoring something nobody justified.

Usage: python scripts/pip_audit_ignores.py .github/pip-audit-ignore.txt
Prints the arguments on stdout (nothing when the list is empty); exits 1 on error.
"""

import re
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*$")  # PYSEC-, GHSA-, CVE-
MIN_REASON_CHARS = 10


class IgnoreEntry(NamedTuple):
    advisory_id: str
    added: date
    reason: str


def parse_ignore_list(text: str, today: date | None = None) -> list[IgnoreEntry]:
    """Parse and validate the ignore list. Raise ValueError naming the bad line."""
    today = today or date.today()
    entries: list[IgnoreEntry] = []
    seen: set[str] = set()
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3:
            raise ValueError(f"line {lineno}: expected 'ID | YYYY-MM-DD | reason'")
        advisory_id, added_text, reason = parts
        if not _ID_RE.match(advisory_id):
            raise ValueError(f"line {lineno}: {advisory_id!r} is not an advisory ID")
        try:
            added = date.fromisoformat(added_text)
        except ValueError:
            raise ValueError(f"line {lineno}: date {added_text!r} is not YYYY-MM-DD") from None
        if added > today:
            raise ValueError(f"line {lineno}: date {added_text} is in the future")
        if len(reason) < MIN_REASON_CHARS:
            raise ValueError(f"line {lineno}: {advisory_id} needs a reason")
        if advisory_id in seen:
            raise ValueError(f"line {lineno}: {advisory_id} is listed twice")
        seen.add(advisory_id)
        entries.append(IgnoreEntry(advisory_id, added, reason))
    return entries


def ignore_args(entries: list[IgnoreEntry]) -> list[str]:
    args: list[str] = []
    for entry in entries:
        args += ["--ignore-vuln", entry.advisory_id]
    return args


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        entries = parse_ignore_list(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"pip-audit ignore list: {exc}", file=sys.stderr)
        return 1
    for entry in entries:
        print(
            f"ignoring {entry.advisory_id} (added {entry.added}): {entry.reason}",
            file=sys.stderr,
        )
    print(" ".join(ignore_args(entries)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
