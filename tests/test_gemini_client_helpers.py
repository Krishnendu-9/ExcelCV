import unittest
from unittest.mock import patch

from src.gemini_client import (
    _as_dict,
    _extract_json_from_text,
    _extract_response_text,
    _normalize_model_name,
    _pick_model_id,
    _sanitize_prompt_text,
)


class GeminiClientHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        _pick_model_id.cache_clear()

    def tearDown(self) -> None:
        _pick_model_id.cache_clear()

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

    @patch("src.gemini_client.preferred_models")
    @patch("src.gemini_client.genai.list_models")
    def test_pick_model_id_prefers_supported_preferred_model(self, mock_list_models, mock_preferred) -> None:
        class _Model:
            def __init__(self, name: str, methods):
                self.name = name
                self.supported_generation_methods = methods

        mock_preferred.return_value = ["models/gemini-2.5-flash", "models/gemini-2.0-flash"]
        mock_list_models.return_value = [
            _Model("models/gemini-2.0-flash", ["generateContent"]),
            _Model("models/gemini-2.5-flash", ["generateContent"]),
        ]
        self.assertEqual(_pick_model_id(), "models/gemini-2.5-flash")

    @patch("src.gemini_client.genai.list_models", side_effect=RuntimeError("network down"))
    def test_pick_model_id_falls_back_on_list_models_error(self, _mock_list_models) -> None:
        self.assertEqual(_pick_model_id(), "models/gemini-2.0-flash")

    @patch("src.gemini_client._pick_model_id", return_value="models/gemini-2.5-pro")
    @patch("src.gemini_client._generate_with_retry")
    @patch("src.gemini_client.genai.GenerativeModel")
    @patch("src.gemini_client.preferred_models")
    @patch("src.gemini_client.get_api_key", return_value="fake-key")
    @patch("src.gemini_client.genai.configure")
    def test_analyze_cv_returns_friendly_quota_message_when_last_preferred_was_quota(
        self,
        _mock_configure,
        _mock_get_key,
        mock_preferred,
        _mock_model_cls,
        mock_generate,
        _mock_pick_model,
    ) -> None:
        mock_preferred.return_value = [
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite",
        ]
        mock_generate.side_effect = [
            RuntimeError("service unavailable"),
            RuntimeError("429 quota exceeded"),
            RuntimeError("internal error"),
        ]

        with self.assertRaises(RuntimeError) as ctx:
            from src.gemini_client import analyze_cv_with_gemini

            analyze_cv_with_gemini("sample cv text", "sample jd")

        self.assertIn("quota exceeded", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
