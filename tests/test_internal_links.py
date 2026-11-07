"""Every link to one of the app's own pages must stay in the app.

A link stays in the app only when it carries data-nav-action (or data-guide-nav on guide
pages): a click handler then clicks the hidden bridge button for that action, and the
session moves to the new page. A plain href is a full page load, which starts a new
session: the user is signed out and unsaved work is lost. This bit three times before
the whole class was fixed: through a dead nav handler, a once-flag on the footer's
smooth-scroll listener, and links that were never routed at all: the header logo, the
footer's links off the home page, and links on the contact, guide and comparison pages.

This renders every page in APP_PAGES with Streamlit's AppTest, signed in and as a guest,
and reads every link out of the HTML and Markdown the app sends. It fails, naming the
page and the link, when a link to one of the app's pages has no routing attribute, or
when the bridge button its attribute names was not rendered in the same run. Two plain
links are allowed: Logout, which must be a fresh request, and sign-in links shown to a
guest, who has no session to lose.

Links that exist only in states these renders do not reach (a guide with no content, an
unregistered guide slug) and links a script creates in the browser are not seen.
"""

import os
import re
import unittest
from html.parser import HTMLParser
from unittest import mock
from urllib.parse import parse_qs, urlparse

from streamlit.testing.v1 import AppTest

from src.ui.app_utils import APP_PAGES, NAV_ACTION_TO_PAGE
from tests.repo_files import REPO_ROOT

_USER = {"id": "internal-links-guard", "email": "guard@example.com", "full_name": "Link Guard"}
_MODAL_ACTIONS = {"give-feedback", "support"}
# States a page renders differently in, beyond signed in or not.
_EXTRA_STATES = [("home", {"comparison_results": [{"Resume": "a.pdf", "Score": 80}]})]
_MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
_PAGE_ERROR = "Something went wrong while loading this page."


class _Links(HTMLParser):
    """(attrs, text) for every <a> in the fed HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[dict, str]] = []
        self._open: list[tuple[dict, list[str]]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._open.append((dict(attrs), []))

    def handle_data(self, data):
        for _, text in self._open:
            text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._open:
            attrs, text = self._open.pop()
            self.links.append((attrs, " ".join("".join(text).split())))


def _bridge_key(action: str) -> str:
    return "nav_action_" + "".join(ch if ch.isalnum() else "_" for ch in action.lower())


def _bodies(node):
    """Every markdown or HTML body in the rendered tree."""
    body = getattr(getattr(node, "proto", None), "body", None)
    if isinstance(body, str) and body:
        yield body
    for child in getattr(node, "children", {}).values():
        yield from _bodies(child)


def _render(page: str, user: dict | None, state: dict) -> AppTest:
    at = AppTest.from_file(str(REPO_ROOT / "app.py"), default_timeout=60)
    if user:
        at.session_state["user"] = user
    for key, value in state.items():
        at.session_state[key] = value
    at.query_params["page"] = page
    return at.run()


def _internal_page(href: str) -> str | None:
    """The app page *href* points at, or None when it leaves the app or stays on this page."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    url = urlparse(href)
    if url.scheme or url.netloc:
        return None  # another site
    if url.path not in ("", "/"):
        return None
    query = parse_qs(url.query)
    if "_logout" in query:
        return "_logout"
    return query.get("page", ["home"])[0]


def _problems(label: str, at: AppTest, user: dict | None) -> list[str]:
    bridges = {b.key for b in at.button if b.key}
    links: list[tuple[dict, str]] = []
    for body in _bodies(at.main):
        parser = _Links()
        parser.feed(body)
        links += parser.links
        links += [({"href": href}, text) for text, href in _MARKDOWN_LINK.findall(body)]

    found = []
    for attrs, text in links:
        page = _internal_page(attrs.get("href") or "")
        if page is None or page == "_logout" or (page == "auth" and user is None):
            continue
        action = attrs.get("data-nav-action")
        guide = attrs.get("data-guide-nav")
        where = f"{label}: '{text}' -> {attrs.get('href')}"
        if action:
            if action not in NAV_ACTION_TO_PAGE and action not in _MODAL_ACTIONS:
                found.append(f"{where} names data-nav-action={action!r}, not in NAV_ACTION_TO_PAGE")
            elif _bridge_key(action) not in bridges:
                found.append(f"{where} names data-nav-action={action!r}, but no bridge rendered")
        elif guide:
            if _bridge_key(guide) not in bridges:
                found.append(f"{where} names data-guide-nav={guide!r}, but no bridge rendered")
        elif not attrs.get("data-smooth-scroll"):
            found.append(f"{where} is a plain link: a full page load, which signs the user out")
    return found


class InternalLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renders: dict[str, tuple[AppTest, dict | None]] = {}
        env = {"SESSION_SECRET": "internal-links-guard-" + "x" * 32}
        with mock.patch.dict(os.environ, env):
            for page in sorted(APP_PAGES):
                for who, user in (("signed in", _USER), ("guest", None)):
                    cls.renders[f"{page} ({who})"] = (_render(page, user, {}), user)
            for page, state in _EXTRA_STATES:
                label = f"{page} (signed in, {', '.join(state)})"
                cls.renders[label] = (_render(page, _USER, state), _USER)

    def test_every_page_renders(self) -> None:
        """A page that fails to render hides its links from this guard."""
        for label, (at, _) in self.renders.items():
            with self.subTest(render=label):
                self.assertEqual([str(e.value) for e in at.exception], [])
                self.assertNotIn(_PAGE_ERROR, [e.value for e in at.error])

    def test_every_internal_link_is_routed_in_app(self) -> None:
        found = []
        for label, (at, user) in self.renders.items():
            found += _problems(label, at, user)
        self.assertEqual(found, [])

    def test_the_renders_reach_the_links(self) -> None:
        """Guards the guard: the links it must check are in what it reads."""
        routed = 0
        footer_privacy = 0
        for at, _ in self.renders.values():
            for body in _bodies(at.main):
                routed += body.count("data-nav-action=")
                footer_privacy += 'data-nav-action="privacy-policy"' in body
        self.assertGreater(routed, 500)
        self.assertGreater(footer_privacy, 40)


class LogoTests(unittest.TestCase):
    """The logo was a full page load to `?_clear=1`, which started over by losing the
    whole session. In-app, it must still start over, and only that."""

    def test_the_logo_clears_the_analysis_and_comparison_but_keeps_the_session(self) -> None:
        env = {"SESSION_SECRET": "internal-links-guard-" + "x" * 32}
        with mock.patch.dict(os.environ, env):
            at = _render(
                "my-cvs",
                _USER,
                {
                    "analysis": {"overall_score": 70},
                    "cv_text": "CV text",
                    "comparison_results": [{"Resume": "a.pdf", "Score": 80}],
                    "cvb_full_name": "Unsaved Name",
                },
            )
            at.button(key=_bridge_key("home")).click().run()
        self.assertEqual(at.session_state["page"], "home")
        for key in ("analysis", "cv_text", "comparison_results"):
            self.assertFalse(key in at.session_state, f"{key} survived the logo")
        self.assertEqual(at.session_state["user"], _USER)
        self.assertEqual(at.session_state["cvb_full_name"], "Unsaved Name")


if __name__ == "__main__":
    unittest.main()
