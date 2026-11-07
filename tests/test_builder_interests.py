"""Each interest row in the resume builder must show the interest at its position.

The rows are read-only text inputs keyed by position (cvb_interest_readonly_0, _1, ...).
They took their text from value=, which Streamlit applies only when a widget is first
drawn, so after deleting the first interest, row 0 went on showing it although the list
now started with the next one: it looked as if the wrong interest had been deleted.
Observed in headless Edge; this test drives the real page under Streamlit's AppTest.
"""

import unittest

from tests import test_builder_state_navigation as nav


class InterestRowsTests(unittest.TestCase):
    # The navigation tests' harness: the real page under AppTest, with a fake CV lookup.
    setUp = nav.BuilderStateNavigationTests.setUp
    _run = nav.BuilderStateNavigationTests._run
    _open = nav.BuilderStateNavigationTests._open

    def _rows(self):
        return [
            self.at.text_input(key=f"cvb_interest_readonly_{i}").value
            for i in range(len(self.at.session_state["cvb_interests"]))
        ]

    def test_deleting_the_first_interest_shows_the_next_one_in_its_row(self):
        self._open("cv-a")
        self.at.session_state["cvb_interests"] = ["Chess", "Poetry"]
        self._run()
        self.assertEqual(self._rows(), ["Chess", "Poetry"])
        self.at.button(key="rm_int_0").click()
        self._run()
        self.assertEqual(self.at.session_state["cvb_interests"], ["Poetry"])
        self.assertEqual(self._rows(), ["Poetry"])


if __name__ == "__main__":
    unittest.main()
