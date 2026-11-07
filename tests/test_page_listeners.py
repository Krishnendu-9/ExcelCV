"""Scripts must not bind page listeners behind a once-per-page flag.

The app's scripts run inside components iframes and add listeners to the page from there.
When Streamlit replaces such an iframe, on a navigation or a layout change, the listeners
its old document created stop running. A script that binds once per window or document,
behind a flag such as `if (doc.__bound) return; doc.__bound = true;`, never binds again,
and the feature goes dead while the flag says it is bound. Reset, the builder's link
popover and the home footer's links broke this way; the fixed top bar, the home page's
demo card and the guide contents links were dead after a navigation, hidden only by an
observer or another listener. Every script now replaces its listeners on every run.

This reads every <script> block in app.py and src/ and fails, naming the line, when a
listener is bound inside the reach of such a flag: an early return on it, or the block
it guards. A flag is a property of the page's window or document that the script sets to
true. Flags on elements are not checked: an element's flag goes away with the element.
"""

import re
import unittest
from pathlib import Path

from tests.repo_files import REPO_ROOT

_SCRIPT = re.compile(r"<script[^>]*>(.*?)</script>", re.S)
# `var w = window.parent ...`, `var doc = w.document`, `var win = window.parent`.
_ALIAS = re.compile(r"\b(?:var|let|const)\s+(\w+)\s*=\s*([^;]+);")
_TRUE = r"(?:true|1|!0|'1'|\"1\")"


def _script_files() -> list[Path]:
    files = [REPO_ROOT / "app.py"]
    files += sorted(p for p in (REPO_ROOT / "src").rglob("*") if p.suffix in (".py", ".tpl", ".js"))
    return files


def _page_objects(script: str) -> list[str]:
    """Names this script uses for the page's window or document."""
    names = ["window", "document", "window.parent", "parent"]
    for name, value in _ALIAS.findall(script):
        value = value.strip()
        if "window.parent" in value or value in ("window", "document", "window.top"):
            names.append(name)
        elif re.fullmatch(r"[\w.]+\.document", value):
            names.append(name)
    return names


def _block_end(text: str, open_brace: int) -> int:
    """Index just past the brace that closes the one at *open_brace*.

    Python f-strings double their braces; counting every brace still pairs them.
    """
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def once_flag_violations(script: str) -> list[tuple[int, str]]:
    """(offset, guard) for each page-level once-flag that has a listener in its reach."""
    found = []
    for obj in _page_objects(script):
        o = re.escape(obj)
        flag = rf"{o}(?:\.[\w$]+|\[\s*[^\]]+?\s*\])"
        for m in re.finditer(rf"if\s*\(\s*(!?)\s*({flag})\s*\)\s*(\{{|return\b)", script):
            negated, target, opener = m.group(1), m.group(2), m.group(3)
            # Only a flag the script itself sets to true is a once-flag; a stored handler
            # checked before removing it is the replace-every-run pattern.
            if not re.search(rf"{re.escape(target)}\s*=\s*{_TRUE}", script):
                continue
            if opener == "return" and not negated:
                reach = script[m.end() :]  # `if (flag) return;`: the rest of the script
            elif opener == "{" and negated:
                reach = script[m.end() - 1 : _block_end(script, m.end() - 1)]
            else:
                continue
            if "addEventListener" in reach:
                found.append((m.start(), m.group(0)))
    return found


def _violations() -> list[str]:
    out = []
    for path in _script_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        for script in _SCRIPT.finditer(text):
            for offset, guard in once_flag_violations(script.group(1)):
                line = text.count("\n", 0, script.start(1) + offset) + 1
                out.append(f"{rel}:{line} {guard}")
    return out


class OnceFlagLintTests(unittest.TestCase):
    def test_no_listener_is_bound_behind_a_page_level_once_flag(self) -> None:
        self.assertEqual(
            _violations(),
            [],
            "replace the listener on every run instead: store the handler on the "
            "window or document, remove the stored one, then add the new one",
        )

    def test_every_listener_is_inside_a_script_block_the_lint_reads(self) -> None:
        """The lint only sees <script> blocks; a listener outside one would go unchecked."""
        for path in _script_files():
            text = path.read_text(encoding="utf-8")
            in_scripts = sum(s.count("addEventListener") for s in _SCRIPT.findall(text))
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                self.assertEqual(text.count("addEventListener"), in_scripts)


class LintSelfTests(unittest.TestCase):
    """The patterns the lint must catch and the ones it must leave alone."""

    def test_catches_an_early_return_on_a_document_flag(self) -> None:
        script = """
        var w = window.parent && window.parent !== window ? window.parent : window;
        var doc = w.document;
        if (doc.__bound__) return;
        doc.__bound__ = true;
        doc.addEventListener('click', function () {}, true);
        """
        self.assertEqual(len(once_flag_violations(script)), 1)

    def test_catches_a_block_guarded_by_a_window_flag(self) -> None:
        script = """
        var target = window.parent && window.parent !== window ? window.parent : window;
        if (!target.__resizeBound) {
            target.__resizeBound = true;
            target.addEventListener('resize', apply);
        }
        """
        self.assertEqual(len(once_flag_violations(script)), 1)

    def test_catches_a_bracketed_flag_in_doubled_f_string_braces(self) -> None:
        script = """
        var w = window.parent;
        if (!w[KEY]) {{
            w[KEY] = true;
            w.addEventListener('message', onMessage);
        }}
        """
        self.assertEqual(len(once_flag_violations(script)), 1)

    def test_allows_replacing_the_listener_every_run(self) -> None:
        script = """
        var w = window.parent;
        var doc = w.document;
        var KEY = '__click__';
        if (doc[KEY]) doc.removeEventListener('click', doc[KEY], true);
        doc[KEY] = handle;
        doc.addEventListener('click', handle, true);
        """
        self.assertEqual(once_flag_violations(script), [])

    def test_allows_an_element_flag_and_a_once_flag_without_listeners(self) -> None:
        script = """
        var w = window.parent;
        var doc = w.document;
        var icon = doc.querySelector('.icon');
        if (!icon.__bound) {
            icon.__bound = true;
            icon.addEventListener('click', open);
        }
        if (!w.__watcher) {
            w.__watcher = true;
            setInterval(sync, 250);
        }
        """
        self.assertEqual(once_flag_violations(script), [])


if __name__ == "__main__":
    unittest.main()
