"""An exception in a page body must not take the nav links' in-app routing with it.

main() injects the script that keeps nav links in-app, along with the header and footer
scripts and the URL clean-up, after the page body. When a page body raised, the run ended
there, Streamlit removed the previous run's copies of those scripts, and the next nav
click did a full page load into a new session: the user was signed out and unsaved work
was lost. Checked in headless Edge. _render_page() now shows an error message in place and
lets main() carry on. The traceback goes to the server log, never to the page.

The first test runs _render_page() under Streamlit's AppTest. The second reads app.py:
the fix holds only while main() renders every page body through _render_page(), which the
first cannot see. The nav handler itself is JavaScript and is not run here.
"""

import ast
import logging
import unittest

from streamlit.testing.v1 import AppTest

from tests.repo_files import REPO_ROOT


def _raising_page():
    from unittest import mock

    import streamlit as st

    import app

    def boom():
        raise RuntimeError("page body failed")

    with (
        mock.patch.object(app, "render_my_cvs_page", boom),
        mock.patch.object(app, "_require_auth", lambda *_: None),
    ):
        app._render_page("my-cvs")
    st.markdown("after the page body")


def _page_text(node):
    """Every element's proto on the page, as text: what the browser is sent."""
    parts = [str(node.proto)] if getattr(node, "proto", None) is not None else []
    for child in getattr(node, "children", {}).values():
        parts.extend(_page_text(child))
    return parts


class RenderPageTests(unittest.TestCase):
    def test_an_exception_in_a_page_body_is_logged_not_shown_and_the_run_goes_on(self):
        with self.assertLogs("app", level="ERROR") as logs:
            at = AppTest.from_function(_raising_page, default_timeout=60).run()

        page = "\n".join(_page_text(at.main) + _page_text(at.sidebar))
        self.assertEqual(len(at.exception), 0, "an exception element is on the page")
        for detail in ("page body failed", "RuntimeError", "Traceback", "boom"):
            self.assertNotIn(detail, page, f"the page carries {detail!r}")
        self.assertEqual(
            [e.value for e in at.error], ["Something went wrong while loading this page."]
        )
        self.assertTrue(
            any(m.value == "after the page body" for m in at.markdown),
            "the run ended at the page body",
        )

        logged = "\n".join(logging.Formatter().format(r) for r in logs.records)
        self.assertIn("'my-cvs'", logged)
        self.assertIn("Traceback", logged, "the log has no traceback")
        self.assertIn("RuntimeError: page body failed", logged)


# Page renderers app.py imports and calls; the header, footer and sign-in page are not
# page bodies.
_NOT_PAGE_BODIES = {"render_top_nav", "render_site_footer", "render_auth_page"}


class MainOrderTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        self.funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    @staticmethod
    def _calls(node):
        return [
            (n.lineno, n.func.id)
            for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        ]

    def test_main_renders_page_bodies_only_through_the_guard(self):
        main_calls = [name for _, name in self._calls(self.funcs["main"])]
        self.assertEqual(main_calls.count("_render_page"), 1, "main() must call _render_page()")
        outside = sorted(
            f"{func}:{line} {name}"
            for func, node in self.funcs.items()
            if func != "_render_page_body"
            for line, name in self._calls(node)
            if (name.startswith("render_") and name not in _NOT_PAGE_BODIES)
            or (name == "_render_page_body" and func != "_render_page")
        )
        self.assertEqual(outside, [], "a page body rendered outside _render_page()")


if __name__ == "__main__":
    unittest.main()
