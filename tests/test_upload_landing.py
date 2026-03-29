import unittest
from unittest.mock import patch

from src.ui.upload import render_upload_landing_sections, render_upload_preview_card


class UploadLandingTests(unittest.TestCase):
    @patch("src.ui.upload.st.markdown")
    def test_render_upload_landing_sections_renders_expected_blocks(self, mock_markdown) -> None:
        render_upload_landing_sections()

        self.assertTrue(mock_markdown.called)
        args, kwargs = mock_markdown.call_args
        html = args[0]

        self.assertIn("landing-extended", html)
        self.assertIn("ExcelCV", html)
        self.assertIn("ATS parse diagnostics", html)
        self.assertIn("Frequently asked questions", html)
        self.assertTrue(kwargs.get("unsafe_allow_html"))

    @patch("src.ui.upload.st.markdown")
    def test_render_upload_preview_card_uses_html_entities_for_icons(self, mock_markdown) -> None:
        render_upload_preview_card()

        self.assertTrue(mock_markdown.called)
        args, kwargs = mock_markdown.call_args
        html = args[0]

        self.assertIn("&#10003;", html)
        self.assertIn("&#9888;", html)
        self.assertIn("&#10005;", html)
        self.assertTrue(kwargs.get("unsafe_allow_html"))


if __name__ == "__main__":
    unittest.main()
