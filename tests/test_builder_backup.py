"""The resume builder's Backup file must import again, into a builder with another CV open.

Backup used to write every cvb_ session key, about 700 of them, among them some 600
button keys (toolbar, section, template and date-picker buttons). Import wrote them all
back, and Streamlit refuses a session-state value for a button, so the builder crashed
on the next run with StreamlitValueAssignmentNotAllowedError. _builder_backup_data() is
now an allowlist used on both sides: Backup writes only the builder's data, and Import
ignores everything else, so files made before the change import too.

The round-trip tests run the real page, _get_backup_json() and _import_from_json() under
Streamlit's AppTest. AppTest has no file uploader, so the file's bytes are handed to
_import_from_json() directly; the uploader widget itself is not covered.
"""

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from streamlit.testing.v1 import AppTest

from src.ui import cv_builder_page
from src.ui.cv_builder_constants import SECTION_IDS
from tests.test_builder_state_navigation import CV_A, CV_A_FIELDS, _FakeDb

# A non-default section order: if Import loses the setup flags, _init_builder() resets it.
B_ORDER = [
    "personal",
    "skills",
    "summary",
    "experience",
    "education",
    "projects",
    "languages",
    "certifications",
    "interests",
]
CV_B = {
    "personal": {
        "full_name": "Bob Builder",
        "prof_title": "Site Manager",
        "email": "bob@build.example",
        "summary": "Builds sturdy things on time.",
    },
    "experience": [
        {
            "id": "e2",
            "role": "Foreman",
            "company": "Builders Inc",
            "start_date": "02/2015",
            "bullets": ["Built a house"],
        }
    ],
    "education": [{"id": "d2", "institution": "Bob Polytechnic", "degree": "HND"}],
    "skills": {"items": [{"id": "s3", "name": "Bricklaying"}]},
    "projects": [{"id": "p2", "name": "Big Bridge"}],
    "certifications": [{"id": "c2", "name": "CSCS Card", "issuer": "CITB"}],
    "languages": [{"id": "l2", "language": "Spanish", "proficiency": "Basic"}],
    "interests": ["Sailing"],
    "customization": {"accent_color": "#16a34a", "section_order": B_ORDER},
}
CV_B_FIELDS = {
    "cvb_full_name": "Bob Builder",
    "cvb_prof_title": "Site Manager",
    "cvb_email": "bob@build.example",
    "cvb_summary": "Builds sturdy things on time.",
    "cvb_exp_role_e2": "Foreman",
    "cvb_exp_company_e2": "Builders Inc",
    "cvb_exp_start_e2": "02/2015",
    "cvb_exp_b_e2_0": "Built a house",
    "cvb_edu_inst_d2": "Bob Polytechnic",
    "cvb_skill_item_s3": "Bricklaying",
    "cvb_proj_name_p2": "Big Bridge",
    "cvb_cert_name_c2": "CSCS Card",
    "cvb_lang_name_l2": "Spanish",
    "cvb_lang_prof_l2": "Basic",
    "cvb_interests": ["Sailing"],
    "cvb_accent_color": "#16a34a",
    "cvb_section_order": B_ORDER,
}


def _app():
    import io
    import json

    import streamlit as st

    from src.ui.cv_builder_page import (
        _get_backup_json,
        _import_from_json,
        render_cv_builder_page,
    )

    ss = st.session_state
    if "_import" in ss:
        _import_from_json(io.BytesIO(ss.pop("_import").encode("utf-8")))
    render_cv_builder_page()
    ss["_backup"] = _get_backup_json()
    # What Backup wrote before the export was filtered: every cvb_ key in the session.
    ss["_unfiltered_backup"] = json.dumps(
        {k: v for k, v in ss.items() if str(k).startswith("cvb_")}, default=str
    )


def _record(cv_id, data):
    return SimpleNamespace(id=cv_id, title=cv_id, template="classic", data=data, updated_at=None)


class _SessionDict(dict):
    """Stands in for st.session_state in the pure tests."""


class BackupKeysTests(unittest.TestCase):
    def test_keeps_the_builders_data_and_drops_widget_and_session_keys(self):
        data = {
            "cvb_full_name": "Ada",
            "cvb_summary": "Engineer.",
            "cvb_exp_ids": ["e1"],
            "cvb_exp_role_e1": "Engineer",
            "cvb_exp_start_e1": "01/2019",
            "cvb_exp_bcount_e1": 1,
            "cvb_exp_b_e1_0": "Led it",
            "cvb_skill_ids": ["s1"],
            "cvb_skill_item_s1": "Python",
            "cvb_interests": ["Chess"],
            "cvb_section_order": list(SECTION_IDS),
            "cvb_sidebar_layout_v2_migrated": True,
            "cvb_loaded_cv_id": "cv-a",
        }
        junk = {
            "cvb_toolbar_import": False,  # buttons: Streamlit refuses these
            "cvb_toolbar_save": False,
            "cvb_section_add_experience": False,
            "cvb_tpl_modern": False,
            "cvb_exp_start_e1__m_3": False,  # date-picker button
            "cvb_toolbar_backup": False,  # download button
            "cvb_import_file_native": None,  # file uploader
            "cvb_exp_start_e1__month": 1,  # date-picker helper state
            "cvb_exp_start_e1__popover_open": False,
            "cvb_state_mirror_v1": {"cvb_full_name": "Someone else"},
            "cvb_pdf_bytes": "b'%PDF'",
            "cvb_pdf_hash": "abc",
            "cvb_show_import": True,
            "cvb_toolbar_title_native": "My Resume",
            "cvb_interest_readonly_0": "Chess",
            "cvb_new_interest_0": "",
            "cvb_exp_role_9f1c2d3e-0000-4000-8000-000000000000": "",  # row not in the ids
        }
        self.assertEqual(cv_builder_page._builder_backup_data({**data, **junk}), data)

    def _keys_set_by(self, fn, *args):
        state = _SessionDict()
        with mock.patch.object(cv_builder_page.st, "session_state", state):
            fn(*args)
        return state

    def test_keeps_every_key_that_opening_a_cv_sets(self):
        state = self._keys_set_by(cv_builder_page.load_cv_into_builder, _record("cv-a", CV_A))
        dropped = set(state) - set(cv_builder_page._builder_backup_data(state))
        self.assertEqual(dropped, {"cvb_state_mirror_v1"}, "opening a CV sets keys Backup drops")

    def test_keeps_every_key_the_builders_setup_sets(self):
        state = self._keys_set_by(cv_builder_page._init_builder)
        dropped = set(state) - set(cv_builder_page._builder_backup_data(state))
        # The mirror is rebuilt from the data, and the uploader's open state is not data.
        self.assertEqual(
            dropped,
            {"cvb_state_mirror_v1", "cvb_show_import"},
            "_init_builder() sets keys Backup drops: a new setup flag belongs in "
            "CVB_INIT_FLAG_KEYS, a new data key in CVB_PERSIST_BASE_KEYS",
        )


class BackupRoundTripTests(unittest.TestCase):
    def setUp(self):
        records = {"cv-a": _record("cv-a", CV_A), "cv-b": _record("cv-b", CV_B)}
        user = {"id": "u1", "email": "u@example.com", "full_name": "U"}
        for name, value in (
            ("get_db", lambda: _FakeDb(records)),
            ("get_session_user", lambda: user),
        ):
            patcher = mock.patch.object(cv_builder_page, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.at = AppTest.from_function(_app, default_timeout=60)
        self._run()

    def _run(self):
        self.at.run()
        self.assertFalse(self.at.exception, [str(e.value)[:300] for e in self.at.exception])

    def _open(self, cv_id):
        self.at.session_state["cvb_load_id"] = cv_id
        self._run()

    def _state(self, keys):
        return {
            k: self.at.session_state[k] if k in self.at.session_state else "<absent>" for k in keys
        }

    def _import_over_cv_a(self, backup):
        self._open("cv-a")
        self.assertEqual(self._state(CV_A_FIELDS), CV_A_FIELDS)
        self.at.session_state["_import"] = backup
        self._run()
        self.assertEqual(self._state(CV_B_FIELDS), CV_B_FIELDS)
        left = {k: v for k, v in self._state(CV_A_FIELDS).items() if v == CV_A_FIELDS[k]}
        self.assertEqual(left, {}, "CV A's fields survived the import")

    def test_a_backup_holds_no_widget_keys(self):
        self._open("cv-b")
        backup = json.loads(self.at.session_state["_backup"])
        self.assertTrue(set(CV_B_FIELDS) <= set(backup))
        unfiltered = json.loads(self.at.session_state["_unfiltered_backup"])
        self.assertIn("cvb_toolbar_import", unfiltered)
        widget_keys = sorted(
            k for k in backup if k in ("cvb_toolbar_import", "cvb_state_mirror_v1") or "__" in k
        )
        self.assertEqual(widget_keys, [])

    def test_a_backup_imports_over_another_open_cv(self):
        self._open("cv-b")
        self._import_over_cv_a(self.at.session_state["_backup"])

    def test_a_backup_made_before_the_export_was_filtered_imports_too(self):
        self._open("cv-b")
        self._import_over_cv_a(self.at.session_state["_unfiltered_backup"])


if __name__ == "__main__":
    unittest.main()
