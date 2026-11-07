"""The README's resume builder claims: three distinct templates, and nine section types.

Checked in headless Edge against a running copy of the app: the three templates lay out
differently in the preview and in the exported PDF (Classic one centred column, Modern a
32% solid accent sidebar, Creative a 30% tinted sidebar with its own section split), and
of the 27 section behaviours, collapse holds for all nine sections, while hide and reorder
hold for every section but Personal Information, which is always the resume's header. Its
row now has no eye or drag handle, and a saved order or eye state cannot move or hide it. In
Modern and Creative the order applies within each column. Summary used to be pinned to the
top of the main column there, so moving it did nothing; it now follows the order.

These tests pin what the browser showed, from Python:

- the preview each template renders, read from the builder's preview iframe, keeps its
  layout: whether there is a sidebar and which sections it holds;
- the PDF export renders the same template layout, by capturing the HTML it would hand
  to Chromium;
- every section's chevron, eye and position controls change the editor and the preview,
  driven through the hidden buttons the browser-side scripts click;
- in all three templates, hiding a section removes it and moving it to either end of the
  order moves it to that end of its column, and Personal Information stays the header.

Not covered: the JavaScript that turns a drag or an eye click into those button clicks,
and Chromium's rendering of the HTML into the PDF. Both were checked in a browser.
"""

import re
import unittest
from types import SimpleNamespace
from unittest import mock

from streamlit.testing.v1 import AppTest

from src.ui import cv_builder_page
from src.ui.cv_builder_constants import SECTION_IDS
from tests.test_builder_state_navigation import CV_A, _app, _FakeDb

CV_FULL = dict(CV_A, interests=["Chess"])
TEMPLATES = ("classic", "modern", "creative")
HEADINGS = {
    "summary": "Professional Summary",
    "experience": "Work Experience",
    "education": "Education",
    "skills": "Skills",
    "projects": "Projects",
    "languages": "Languages",
    "certifications": "Certifications",
    "interests": "Interests",
}
# A widget that exists only while the section's editor card is open.
CARD_WIDGET = {
    "personal": "cvb_full_name",
    "summary": "cvb_summary",
    "experience": "cvb_exp_role_e1",
    "education": "cvb_edu_inst_d1",
    "skills": "cvb_skill_item_s1",
    "projects": "cvb_proj_name_p1",
    "languages": "cvb_lang_name_l1",
    "certifications": "cvb_cert_name_c1",
    "interests": "rm_int_0",
}
MOVABLE = [sid for sid in SECTION_IDS if sid != "personal"]
_HEADING = re.compile(r"<(aside|main|div class='cv-paper)[^>]*>|<h2 class='cv-sec-h'>([^<]+)</h2>")


def _heading(sid: str, template: str) -> str:
    return "About Me" if (sid, template) == ("summary", "creative") else HEADINGS[sid]


def layout(html: str) -> list[tuple[str, str]]:
    """(column, heading) for each section heading in the resume, top to bottom."""
    # The resume itself, without the live-preview script that follows it.
    body = html.split("<body>", 1)[-1].split("<script", 1)[0]
    column, found = "main", []
    for m in _HEADING.finditer(body):
        if m.group(1):
            column = "side" if m.group(1) == "aside" else "main"
        else:
            found.append((column, m.group(2).replace("&amp;", "&")))
    return found


def column_of(rows: list[tuple[str, str]], heading: str) -> list[str]:
    col = next(c for c, h in rows if h == heading)
    return [h for c, h in rows if c == col]


class _Builder(unittest.TestCase):
    """The real builder page under AppTest, with a CV that fills all nine sections."""

    def setUp(self):
        record = SimpleNamespace(
            id="cv-full", title="Full", template="classic", data=CV_FULL, updated_at=None
        )
        for name, value in (
            ("get_db", lambda: _FakeDb({"cv-full": record})),
            ("get_session_user", lambda: {"id": "u1", "email": "u@example.com"}),
        ):
            patcher = mock.patch.object(cv_builder_page, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.at = AppTest.from_function(_app, default_timeout=60)
        self.at.run()
        self.at.session_state["cvb_load_id"] = "cv-full"
        self._run()

    def _run(self):
        self.at.run()
        self.assertFalse(self.at.exception, [e.value for e in self.at.exception])

    def _click(self, key: str):
        self.at.button(key=key).click()
        self._run()

    def _nodes(self, node=None):
        node = self.at.main if node is None else node
        yield node
        for child in getattr(node, "children", {}).values():
            yield from self._nodes(child)

    def _keys(self) -> set[str]:
        return {n.key for n in self._nodes() if getattr(n, "key", None)}

    def _preview(self) -> str:
        frames = [
            n.proto.srcdoc
            for n in self._nodes()
            if getattr(n, "type", "") == "iframe" and "cv-paper" in n.proto.srcdoc
        ]
        self.assertEqual(len(frames), 1, "expected one resume preview")
        return frames[0]


class TemplateTests(_Builder):
    def test_each_template_previews_its_own_layout(self):
        side = {}
        for template in TEMPLATES:
            with self.subTest(template=template):
                self._click(f"cvb_tpl_{template}")
                html = self._preview()
                self.assertIn(f"class='cv-paper {template}", html)
                side[template] = [h for c, h in layout(html) if c == "side"]
        self.assertEqual(side["classic"], [])
        self.assertEqual(side["modern"], ["Skills", "Languages", "Certifications", "Interests"])
        self.assertEqual(side["creative"], ["Skills", "Languages", "Interests"])

    def test_the_pdf_is_rendered_from_the_template_layout(self):
        for template in TEMPLATES:
            with self.subTest(template=template):
                self._click(f"cvb_tpl_{template}")
                preview = self._preview()
                captured = []
                cv_builder_page._cached_generate_cv_pdf.clear()
                with mock.patch.object(
                    cv_builder_page,
                    "_render_html_to_pdf_bytes",
                    lambda html: captured.append(html) or b"%PDF",
                ):
                    self._click("cvb_toolbar_download_prepare")
                self.assertEqual(len(captured), 1, "the PDF exporter was not called")
                self.assertIn(f"class='cv-paper {template}", captured[0])
                self.assertEqual(layout(captured[0]), layout(preview))


class SectionControlTests(_Builder):
    def test_every_section_collapses_and_expands(self):
        for sid in SECTION_IDS:
            with self.subTest(section=sid):
                self.assertTrue(CARD_WIDGET[sid] in self._keys(), "card closed before the click")
                self._click(f"cvb_section_toggle_{sid}")
                self.assertFalse(
                    CARD_WIDGET[sid] in self._keys(), "the chevron did not collapse it"
                )
                self._click(f"cvb_section_toggle_{sid}")
                self.assertTrue(CARD_WIDGET[sid] in self._keys(), "the chevron did not reopen it")

    def test_every_section_but_personal_hides_from_the_preview(self):
        for sid in MOVABLE:
            with self.subTest(section=sid):
                self._click(f"cvb_eye_{sid}")
                self.assertNotIn(HEADINGS[sid], [h for _, h in layout(self._preview())])
                self.assertFalse(CARD_WIDGET[sid] in self._keys(), "the eye left the card shown")
                self._click(f"cvb_eye_{sid}")
                self.assertIn(HEADINGS[sid], [h for _, h in layout(self._preview())])

    def test_every_section_but_personal_moves_in_the_preview(self):
        for sid in MOVABLE:
            with self.subTest(section=sid):
                self._click(f"cvb_pos_{sid}_{len(SECTION_IDS) - 1}")
                self.assertEqual([h for _, h in layout(self._preview())][-1], HEADINGS[sid])
                self._click(f"cvb_pos_{sid}_1")
                self.assertEqual([h for _, h in layout(self._preview())][0], HEADINGS[sid])

    def test_personal_information_stays_the_header(self):
        """Its row offers no eye or drag handle, and no saved state can move or hide it."""
        personal_controls = [
            k for k in self._keys() if k.startswith(("cvb_pos_personal_", "cvb_eye_personal"))
        ]
        self.assertEqual(personal_controls, [])
        section_list = next(
            n.proto.srcdoc
            for n in self._nodes()
            if getattr(n, "type", "") == "iframe" and 'class="sec-item' in n.proto.srcdoc
        )
        personal_row = section_list.split('data-id="personal"', 1)[1].split("</li>", 1)[0]
        self.assertNotIn("grip-btn", personal_row)
        self.assertNotIn("eye-btn", personal_row)
        # A CV saved while the Personal row could still be dragged and hidden.
        self.at.session_state["cvb_section_order"] = [*MOVABLE, "personal"]
        self.at.session_state["cvb_section_visibility"] = {"personal": False}
        self._run()
        self.assertEqual(self.at.session_state["cvb_section_order"][0], "personal")
        self.assertTrue(CARD_WIDGET["personal"] in self._keys(), "the Personal card is hidden")
        html = self._preview().split("<body>", 1)[-1]
        self.assertIn("Ada Lovelace", html.split("<h2", 1)[0], "the name left the header")


class TemplateRuleTests(unittest.TestCase):
    """Hide and reorder, in all three templates, at the function the preview and PDF share."""

    def _layout(self, template, order=None, visibility=None):
        return layout(
            cv_builder_page.generate_cv_html(
                CV_FULL, template, section_order=order, section_visibility=visibility
            )
        )

    def test_hiding_removes_the_section_in_every_template(self):
        for template in TEMPLATES:
            for sid in MOVABLE:
                with self.subTest(template=template, section=sid):
                    rows = self._layout(template, visibility={sid: False})
                    self.assertNotIn(_heading(sid, template), [h for _, h in rows])

    def test_moving_a_section_to_either_end_moves_it_in_its_column(self):
        for template in TEMPLATES:
            for sid in MOVABLE:
                rest = [s for s in SECTION_IDS if s not in ("personal", sid)]
                name = _heading(sid, template)
                with self.subTest(template=template, section=sid, to="end"):
                    rows = self._layout(template, ["personal", *rest, sid])
                    self.assertEqual(column_of(rows, name)[-1], name)
                with self.subTest(template=template, section=sid, to="start"):
                    rows = self._layout(template, ["personal", sid, *rest])
                    self.assertEqual(column_of(rows, name)[0], name)

    def test_personal_information_is_the_header_whatever_the_order_or_eye(self):
        for template in TEMPLATES:
            with self.subTest(template=template):
                html = cv_builder_page.generate_cv_html(
                    CV_FULL,
                    template,
                    section_order=[*MOVABLE, "personal"],
                    section_visibility={"personal": False},
                )
                before_sections = html.split("<body>", 1)[-1].split("<h2", 1)[0]
                self.assertIn("Ada Lovelace", before_sections)
                self.assertIn("ada@example.com", before_sections)


if __name__ == "__main__":
    unittest.main()
