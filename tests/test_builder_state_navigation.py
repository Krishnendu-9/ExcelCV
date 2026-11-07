"""Leaving the resume builder and coming back must not empty its fields.

Streamlit drops a widget's session-state key on any run that does not render the widget,
so visiting another page drops every builder field. _protect_builder_widget_state() keeps
a mirror of them and puts them back. Two gaps let the data go. _init_builder() filled the
dropped base keys (the personal details and summary) with "" before the mirror could
restore them, and a CV opened from My CVs was never mirrored until the next builder
rerun, so leaving straight after opening it lost every section. Either way the next Save
wrote the empty fields over the saved CV.

These tests run the real render_cv_builder_page() under Streamlit's AppTest, which drops
unrendered widget keys the way the live app does, and switch to another page and back.
Only the database lookup for an opened CV is faked. Reset deletes the mirror with the
rest of the builder's keys; if it ever kept the mirror, the restore at the start of
_init_builder() would bring the cleared CV back, and the Reset test would fail.

Not covered: a field edited and left in the same click (typing, then clicking a nav
link without leaving the field). That run never renders the builder, so the edit is
dropped before the mirror sees it; docs/KNOWN_ISSUES.md records it. Import JSON is not
covered either: AppTest cannot drive a file uploader.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from streamlit.testing.v1 import AppTest

from src.ui import cv_builder_page

CV_A = {
    "personal": {
        "full_name": "Ada Lovelace",
        "prof_title": "Software Engineer",
        "email": "ada@example.com",
        "summary": "Engineer with ten years building analytics tools.",
    },
    "experience": [
        {"id": "e1", "role": "Senior Engineer", "company": "Engines Ltd", "bullets": ["Led it"]}
    ],
    "education": [{"id": "d1", "institution": "University of London", "degree": "BSc"}],
    "skills": {"items": [{"id": "s1", "name": "Python"}]},
    "projects": [{"id": "p1", "name": "Difference Engine"}],
    "certifications": [{"id": "c1", "name": "AWS SA", "issuer": "Amazon"}],
    "languages": [{"id": "l1", "language": "French", "proficiency": "Fluent"}],
}
CV_B = {"personal": {"full_name": "Bob Builder", "email": "bob@example.com", "summary": "Bob."}}

# Session-state key -> the value opening CV_A puts there.
CV_A_FIELDS = {
    "cvb_full_name": "Ada Lovelace",
    "cvb_prof_title": "Software Engineer",
    "cvb_email": "ada@example.com",
    "cvb_summary": "Engineer with ten years building analytics tools.",
    "cvb_exp_role_e1": "Senior Engineer",
    "cvb_exp_company_e1": "Engines Ltd",
    "cvb_exp_b_e1_0": "Led it",
    "cvb_edu_inst_d1": "University of London",
    "cvb_edu_degree_d1": "BSc",
    "cvb_skill_item_s1": "Python",
    "cvb_proj_name_p1": "Difference Engine",
    "cvb_cert_name_c1": "AWS SA",
    "cvb_cert_issuer_c1": "Amazon",
    "cvb_lang_name_l1": "French",
    "cvb_lang_prof_l1": "Fluent",
}


def _app():
    import streamlit as st

    from src.ui.cv_builder_page import render_cv_builder_page

    if st.session_state.get("_page", "builder") == "builder":
        render_cv_builder_page()
    else:
        st.write("Another page")


class _FakeDb:
    """Answers the builder's one query, CV by id, from a dict."""

    def __init__(self, records):
        self.records, self.wanted = records, None

    def query(self, _model):
        return self

    def filter(self, *conditions):
        for cond in conditions:
            if getattr(cond.left, "key", None) == "id":
                self.wanted = cond.right.value
        return self

    def first(self):
        return self.records.get(self.wanted)

    def close(self):
        pass


class BuilderStateNavigationTests(unittest.TestCase):
    def setUp(self):
        records = {
            cv_id: SimpleNamespace(
                id=cv_id, title=cv_id, template="classic", data=data, updated_at=None
            )
            for cv_id, data in (("cv-a", CV_A), ("cv-b", CV_B))
        }
        user = {"id": "u1", "email": "u@example.com", "full_name": "U"}
        for name, value in (
            ("get_db", lambda: _FakeDb(records)),
            ("get_session_user", lambda: user),
        ):
            patcher = mock.patch.object(cv_builder_page, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.at = AppTest.from_function(_app, default_timeout=60)
        self.at.run()

    def _run(self):
        self.at.run()
        self.assertFalse(self.at.exception, [e.value for e in self.at.exception])

    def _open(self, cv_id):
        self.at.session_state["cvb_load_id"] = cv_id
        self._run()

    def _leave_and_return(self):
        self.at.session_state["_page"] = "elsewhere"
        self._run()
        self.at.session_state["_page"] = "builder"
        self._run()

    def _state(self, keys):
        return {
            k: self.at.session_state[k] if k in self.at.session_state else "<absent>" for k in keys
        }

    def test_typed_details_survive_leaving_and_returning(self):
        self.at.text_input(key="cvb_full_name").input("Grace Hopper")
        self.at.text_area(key="cvb_summary").input("Compiler pioneer.")
        role_key = f"cvb_exp_role_{self.at.session_state['cvb_exp_ids'][0]}"
        self.at.text_input(key=role_key).input("Rear Admiral")
        self._run()
        self._leave_and_return()
        self.assertEqual(
            self._state(["cvb_full_name", "cvb_summary", role_key]),
            {
                "cvb_full_name": "Grace Hopper",
                "cvb_summary": "Compiler pioneer.",
                role_key: "Rear Admiral",
            },
        )
        self.assertEqual(self.at.text_input(key="cvb_full_name").value, "Grace Hopper")

    def test_an_opened_cv_survives_leaving_straight_after_opening_it(self):
        self._open("cv-a")
        self.assertEqual(self._state(CV_A_FIELDS), CV_A_FIELDS)
        self._leave_and_return()
        self.assertEqual(self._state(CV_A_FIELDS), CV_A_FIELDS)

    def test_a_second_cv_does_not_take_the_first_cvs_details(self):
        self._open("cv-a")
        self._run()
        self._open("cv-b")
        self._leave_and_return()
        self.assertEqual(
            self._state(["cvb_full_name", "cvb_email", "cvb_summary"]),
            {"cvb_full_name": "Bob Builder", "cvb_email": "bob@example.com", "cvb_summary": "Bob."},
        )

    def _assert_cv_a_gone(self, when):
        kept = {k: v for k, v in self._state(CV_A_FIELDS).items() if v == CV_A_FIELDS[k]}
        self.assertEqual(kept, {}, f"CV A's fields {when}")
        mirror = self.at.session_state["cvb_state_mirror_v1"]
        in_mirror = {k: v for k, v in CV_A_FIELDS.items() if mirror.get(k) == v}
        self.assertEqual(in_mirror, {}, f"CV A's fields in the mirror {when}")
        self.assertIsNone(self.at.session_state["cvb_loaded_cv_id"], when)

    def test_reset_clears_an_opened_cv_and_the_mirror(self):
        # _reset_all() calls _init_builder(), so the mirror restore runs inside the Reset
        # run: a mirror that survived Reset would put CV A back by the end of it. AppTest
        # cannot run again after Reset (it reads back the toolbar title Reset deleted
        # mid-run, which a browser resends), so leaving and returning afterwards was
        # checked in headless Edge instead.
        self._open("cv-a")
        self._run()
        self.at.button(key="btn_confirm_reset_native").click()
        self._run()
        self._assert_cv_a_gone("after Reset")


if __name__ == "__main__":
    unittest.main()
