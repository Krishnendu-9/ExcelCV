import unittest

from src.gemini_client import _as_dict, _extract_json_from_text, _normalize_model_name


class GeminiClientHelperTests(unittest.TestCase):
    def test_extract_json_from_markdown_code_block(self) -> None:
        raw = "Here is output:\n```json\n{\"match_score\": 90}\n```\nThanks"
        extracted = _extract_json_from_text(raw)
        self.assertEqual(extracted, '{"match_score": 90}')

    def test_extract_json_from_wrapped_text(self) -> None:
        raw = "noise start {\"k\": 1, \"v\": [1,2]} tail"
        extracted = _extract_json_from_text(raw)
        self.assertEqual(extracted, '{"k": 1, "v": [1,2]}')

    def test_normalize_model_name(self) -> None:
        self.assertEqual(_normalize_model_name("gemini-2.0-flash"), "models/gemini-2.0-flash")
        self.assertEqual(_normalize_model_name("models/gemini-2.5-pro"), "models/gemini-2.5-pro")
        self.assertIsNone(_normalize_model_name(None))

    def test_as_dict(self) -> None:
        self.assertEqual(_as_dict({"a": 1}), {"a": 1})
        self.assertEqual(_as_dict("not-dict"), {})


if __name__ == "__main__":
    unittest.main()
