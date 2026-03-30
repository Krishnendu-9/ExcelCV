import unittest

from src.ui.common import get_category_icon


class UiCommonTests(unittest.TestCase):
    def test_get_category_icon_returns_html_entities(self) -> None:
        self.assertEqual(get_category_icon(95), "&#10003;")
        self.assertEqual(get_category_icon(65), "&#9888;")
        self.assertEqual(get_category_icon(30), "&#10005;")


if __name__ == "__main__":
    unittest.main()
