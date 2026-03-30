import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    os.getenv("RUN_STREAMLIT_SMOKE") == "1",
    "Set RUN_STREAMLIT_SMOKE=1 to run Streamlit runtime smoke tests.",
)
class StreamlitRuntimeSmokeTests(unittest.TestCase):
    def test_upload_page_renders_and_form_validation_works(self) -> None:
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(ROOT / "app.py"))
        at.run(timeout=90)

        self.assertEqual(len(at.exception), 0, "App should render without runtime exceptions.")
        self.assertGreaterEqual(len(at.text_area), 1, "Expected Job description input to be present.")
        self.assertGreaterEqual(len(at.button), 2, "Expected theme and submit buttons to be present.")

        # Submit with empty JD to verify baseline validation path remains wired.
        at.button[1].click().run(timeout=90)
        self.assertTrue(
            any("Please provide a job description." in err.value for err in at.error),
            "Expected JD-required validation message after empty submit.",
        )


if __name__ == "__main__":
    unittest.main()
