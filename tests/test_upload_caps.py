"""Upload caps agree across Streamlit, config.py and the Gemini guardrail."""

import os
import re
import tomllib
import unittest
from unittest.mock import patch

from src import config, gemini_client
from tests.repo_files import REPO_ROOT


class UploadCapTests(unittest.TestCase):
    def _streamlit_server(self) -> dict:
        with open(REPO_ROOT / ".streamlit" / "config.toml", "rb") as fh:
            return tomllib.load(fh)["server"]

    def test_streamlit_upload_cap_matches_app_cap(self) -> None:
        self.assertEqual(self._streamlit_server()["maxUploadSize"], config.MAX_FILE_MB)

    def test_gemini_file_cap_defaults_to_upload_cap(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("GEMINI_MAX_FILE_SIZE_BYTES", None)
            self.assertEqual(gemini_client._file_size_cap(), config.MAX_FILE_BYTES)

    def test_gemini_file_cap_can_lower_but_not_raise(self) -> None:
        with patch.dict("os.environ", {"GEMINI_MAX_FILE_SIZE_BYTES": "1048576"}, clear=False):
            self.assertEqual(gemini_client._file_size_cap(), 1048576)
        with patch.dict("os.environ", {"GEMINI_MAX_FILE_SIZE_BYTES": "5242880"}, clear=False):
            self.assertEqual(gemini_client._file_size_cap(), config.MAX_FILE_BYTES)

    def test_env_example_documents_the_effective_cap(self) -> None:
        text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        match = re.search(r"^GEMINI_MAX_FILE_SIZE_BYTES=(\d+)$", text, re.M)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), config.MAX_FILE_BYTES)


class StreamlitConfigTests(unittest.TestCase):
    def test_run_on_save_is_not_committed(self) -> None:
        with open(REPO_ROOT / ".streamlit" / "config.toml", "rb") as fh:
            server = tomllib.load(fh)["server"]
        self.assertNotIn("runOnSave", server)


if __name__ == "__main__":
    unittest.main()
