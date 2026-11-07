"""Only a keystroke may swap the builder preview's formatted sections for plain lines.

The editor bridge (_inject_realtime_js) and the preview (generate_cv_html) talk by
postMessage. The bridge also replays every field value 80 ms to 2.5 s after the builder
mounts, and again after any button click in the editor. Before a keystroke, the preview
must ignore those replays: it was rendered from the same values. When it did not, opening
a saved CV, returning to the builder or clicking a section chevron replaced the formatted
CV with "Label: value" lines, and it stayed that way until an edit changed the data.

These tests read both scripts and pin the contract that keeps the preview intact: the
bridge sends cv-rt-user-mode only from its keystroke handler, before that handler's field
messages, and the preview enters user mode only on that message. They do not run the
JavaScript or render anything; the behaviour itself was checked in headless Edge. A new
route that rewrites the preview some other way would get past them.
"""

import re
import unittest
from unittest import mock

from src.ui import cv_builder_page


def _function_body(js: str, name: str) -> str:
    """The text between the braces of JS function *name*.

    Braces inside string literals and // comments are skipped.
    """
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", js)
    if match is None:
        raise AssertionError(f"function {name} not found")
    depth, quote, i = 1, "", match.end()
    while depth:
        ch = js[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = ""
        elif ch == "/" and js[i + 1] == "/":
            i = js.index("\n", i)
        elif ch in "'\"`":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return js[match.end() : i - 1]


def _bridge_js() -> str:
    with mock.patch.object(cv_builder_page.components, "html") as html:
        cv_builder_page._inject_realtime_js()
    return html.call_args.args[0]


def _preview_js() -> str:
    page = cv_builder_page.generate_cv_html({})
    return page[page.rindex("<script>") :]


class LivePreviewContractTests(unittest.TestCase):
    def test_bridge_enters_user_mode_only_from_the_keystroke_handler(self):
        js = _bridge_js()
        handler = _function_body(js, "handleInput")
        self.assertEqual(
            js.count("cv-rt-user-mode"),
            handler.count("cv-rt-user-mode"),
            "the bridge sends cv-rt-user-mode outside handleInput, so a load or click sync "
            "would strip the formatted preview",
        )
        mode_at = handler.find("cv-rt-user-mode")
        self.assertNotEqual(mode_at, -1, "handleInput no longer sends cv-rt-user-mode")
        for later in ("cv-rt-widget", "cv-rt-update"):
            self.assertLess(
                mode_at,
                handler.find(later),
                f"handleInput sends {later} before cv-rt-user-mode, so the preview would "
                "ignore that message from the first keystroke",
            )

    def test_preview_ignores_field_replays_before_user_mode(self):
        body = _function_body(_preview_js(), "__liveUpsertField")
        guard = re.search(r"if\s*\([^)]*!\s*\w+\.dataset\.liveUserMode\s*\)\s*return\b", body)
        self.assertIsNotNone(
            guard,
            "__liveUpsertField no longer returns early outside user mode, so the load and "
            "click replays would strip the formatted preview",
        )
        enter_at = body.find("__liveEnterUserMode(")
        self.assertTrue(enter_at == -1 or guard.start() < enter_at)

    def test_preview_enters_user_mode_only_on_the_user_mode_message(self):
        js = _preview_js()
        rest = js.replace(_function_body(js, "__liveEnterUserMode"), "")
        rest = rest.replace(_function_body(rest, "__liveUpsertField"), "")
        branch = re.search(r"if\s*\(\s*d\.type\s*===\s*'cv-rt-user-mode'\s*\)\s*\{([^}]*)\}", rest)
        self.assertIsNotNone(branch, "the preview no longer handles cv-rt-user-mode")
        self.assertIn("__liveEnterUserMode(", branch.group(1))
        outside = rest.replace(branch.group(0), "")
        calls = [
            outside[m.start() : outside.index("\n", m.start())].strip()
            for m in re.finditer(r"(?<!function )__liveEnterUserMode\(", outside)
        ]
        self.assertEqual(
            calls,
            [],
            "the preview enters user mode on something other than cv-rt-user-mode",
        )


if __name__ == "__main__":
    unittest.main()
