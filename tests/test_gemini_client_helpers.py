import unittest

from src.gemini_client import (
    _as_dict,
    _extract_json_from_text,
    _extract_response_text,
    _normalize_model_name,
    _sanitize_prompt_text,
)


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

    def test_extract_response_text_from_text_field(self) -> None:
        class Resp:
            text = "  hello world  "

        self.assertEqual(_extract_response_text(Resp()), "hello world")

    def test_extract_response_text_from_candidates_parts(self) -> None:
        class Part:
            def __init__(self, text: str) -> None:
                self.text = text

        class Content:
            def __init__(self, parts) -> None:
                self.parts = parts

        class Candidate:
            def __init__(self, parts) -> None:
                self.content = Content(parts)

        class Resp:
            text = ""
            candidates = [Candidate([Part("one"), Part("two")])]

        self.assertEqual(_extract_response_text(Resp()), "one\ntwo")

    def test_sanitize_prompt_text_compacts_whitespace_and_truncates(self) -> None:
        raw = "line1\n\nline2\tline3    line4"
        self.assertEqual(_sanitize_prompt_text(raw, 12), "line1 line2 ")


if __name__ == "__main__":
    unittest.main()
