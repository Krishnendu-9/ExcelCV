import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import auth_utils, config, gemini_client, oauth_utils

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PUBLISHED_PLACEHOLDER = "change-this-to-a-random-secret"


def _env_example_session_secret() -> str:
    """Return the SESSION_SECRET value committed in .env.example (public by definition)."""
    for line in (_REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith("SESSION_SECRET="):
            return line.split("=", 1)[1].strip()
    raise AssertionError(".env.example has no SESSION_SECRET line")


class SessionSecretGuardTests(unittest.TestCase):
    """The startup guard must reject secrets an attacker could know or guess."""

    def _assert_guard_raises(self, value) -> None:
        env = {} if value is None else {"SESSION_SECRET": value}
        with patch.dict(os.environ, env, clear=False):
            if value is None:
                os.environ.pop("SESSION_SECRET", None)
            with self.assertRaises(RuntimeError) as ctx:
                auth_utils.assert_session_secret_configured()
            # The message must tell the operator how to make a real one.
            self.assertIn(config.SESSION_SECRET_GENERATOR, str(ctx.exception))
            with self.assertRaises(RuntimeError):
                oauth_utils._state_secret()

    def test_guard_raises_for_published_placeholder(self) -> None:
        self.assertEqual(_env_example_session_secret(), _PUBLISHED_PLACEHOLDER)
        self._assert_guard_raises(_PUBLISHED_PLACEHOLDER)
        self._assert_guard_raises(_env_example_session_secret())

    def test_guard_raises_for_empty_or_missing(self) -> None:
        self._assert_guard_raises("")
        self._assert_guard_raises("   ")
        self._assert_guard_raises(None)

    def test_guard_raises_for_placeholder_variants_even_when_long(self) -> None:
        for value in (
            "changeme",
            "CHANGE_ME",
            "change-this",
            _PUBLISHED_PLACEHOLDER.upper(),
            "change-this-to-a-random-secret-please-0123456789",  # long, still a placeholder
            "changeme" + "0" * 40,
        ):
            with self.subTest(value=value):
                self._assert_guard_raises(value)

    def test_guard_raises_for_short_secret(self) -> None:
        self._assert_guard_raises("a1" * 15 + "b")  # 31 chars
        self._assert_guard_raises("unit-test-secret")

    def test_guard_passes_for_real_64_hex_secret(self) -> None:
        real = secrets.token_hex(32)
        self.assertEqual(len(real), 64)
        with patch.dict(os.environ, {"SESSION_SECRET": real}, clear=False):
            auth_utils.assert_session_secret_configured()
            self.assertEqual(oauth_utils._state_secret(), real)

    def test_no_session_token_works_while_secret_is_placeholder(self) -> None:
        user = {"id": "u1", "email": "victim@example.com", "full_name": "V"}
        with patch.dict(os.environ, {"SESSION_SECRET": _PUBLISHED_PLACEHOLDER}, clear=False):
            with self.assertRaises(RuntimeError):
                auth_utils.create_session_token(user)
        real = secrets.token_hex(32)
        with patch.dict(os.environ, {"SESSION_SECRET": real}, clear=False):
            token = auth_utils.create_session_token(user)
        with patch.dict(os.environ, {"SESSION_SECRET": _PUBLISHED_PLACEHOLDER}, clear=False):
            self.assertIsNone(auth_utils.validate_session_token(token))

    def test_oauth_state_not_signed_or_accepted_with_placeholder(self) -> None:
        with patch.dict(os.environ, {"SESSION_SECRET": _PUBLISHED_PLACEHOLDER}, clear=False):
            with self.assertRaises(RuntimeError):
                oauth_utils.create_oauth_state_token(nonce="n")
            self.assertIsNone(oauth_utils.parse_oauth_state_token("a.b", "n"))


class EnvExampleIsNotConfigTests(unittest.TestCase):
    """src.config must not read .env.example: its values are published placeholders."""

    def test_no_message_or_doc_says_env_example_is_used_at_runtime(self) -> None:
        from tests.repo_files import repo_text_files

        runtime_claim = re.compile(r"fallback|falls back|safe default|\bloaded\b|\bloads\b", re.I)
        negated = re.compile(r"\bnever\b|\bnot\b|n't\b", re.I)
        hits = []
        for path in repo_text_files():
            rel = path.relative_to(_REPO_ROOT).as_posix()
            if rel.startswith("tests/"):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for lineno, line in enumerate(lines, start=1):
                if ".env.example" in line and runtime_claim.search(line):
                    if not negated.search(line):
                        hits.append(f"{rel}:{lineno}: {line.strip()[:90]}")
        self.assertEqual(hits, [])

    def test_env_example_values_are_not_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # A directory holding only .env.example, so no real .env can be picked up.
            shutil.copy(_REPO_ROOT / ".env.example", Path(tmp) / ".env.example")
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in {"SESSION_SECRET", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"}
            }
            env["PYTHONPATH"] = str(_REPO_ROOT)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            probe = (
                "import os, src.config; "
                "print(repr(os.environ.get('SESSION_SECRET')), "
                "repr(os.environ.get('GOOGLE_CLIENT_ID')))"
            )
            result = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "None None")


class AuthThrottleTests(unittest.TestCase):
    def setUp(self) -> None:
        auth_utils._LOGIN_FAILURES.clear()
        auth_utils._LOGIN_LOCK_UNTIL.clear()
        auth_utils._RESET_REQUESTS.clear()

    def test_login_throttle_locks_after_limit(self) -> None:
        with (
            patch.object(auth_utils, "_login_throttle_keys", return_value=["k"]),
            patch.object(auth_utils, "_LOGIN_MAX_ATTEMPTS", 2),
            patch.object(auth_utils, "_LOGIN_LOCK_SECONDS", 30),
            patch("src.auth_utils.time.time", side_effect=[100.0, 101.0, 102.0]),
        ):
            auth_utils.record_login_failure("user@example.com")
            auth_utils.record_login_failure("user@example.com")
            allowed, retry_after = auth_utils.check_login_throttle("user@example.com")

        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_clear_login_failures_resets_lock(self) -> None:
        with (
            patch.object(auth_utils, "_login_throttle_keys", return_value=["k"]),
            patch.object(auth_utils, "_LOGIN_MAX_ATTEMPTS", 1),
            patch.object(auth_utils, "_LOGIN_LOCK_SECONDS", 30),
            patch("src.auth_utils.time.time", side_effect=[100.0, 101.0]),
        ):
            auth_utils.record_login_failure("user@example.com")
            allowed_before, _ = auth_utils.check_login_throttle("user@example.com")
        self.assertFalse(allowed_before)

        with patch.object(auth_utils, "_login_throttle_keys", return_value=["k"]):
            auth_utils.clear_login_failures("user@example.com")

        with patch("src.auth_utils.time.time", return_value=101.0):
            allowed_after, retry_after = auth_utils.check_login_throttle("user@example.com")
        self.assertTrue(allowed_after)
        self.assertEqual(retry_after, 0)

    def test_password_reset_throttle_blocks_after_limit(self) -> None:
        with (
            patch.object(auth_utils, "_reset_throttle_keys", return_value=["r"]),
            patch.object(auth_utils, "_RESET_MAX_ATTEMPTS", 2),
            patch.object(auth_utils, "_RESET_WINDOW_SECONDS", 60),
            patch("src.auth_utils.time.time", side_effect=[100.0, 101.0, 102.0]),
        ):
            auth_utils.record_password_reset_attempt("user@example.com")
            auth_utils.record_password_reset_attempt("user@example.com")
            allowed, retry_after = auth_utils.check_password_reset_throttle("user@example.com")

        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)


class GeminiGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        gemini_client._REQUEST_BUCKETS.clear()

    def test_gemini_rate_limit_blocks_after_cap(self) -> None:
        with (
            patch.object(gemini_client, "_request_actor_key", return_value="actor"),
            patch.object(gemini_client, "_GEMINI_MAX_REQUESTS_PER_WINDOW", 2),
            patch.object(gemini_client, "_GEMINI_WINDOW_SECONDS", 60),
            patch("src.gemini_client.time.time", side_effect=[100.0, 101.0, 102.0]),
        ):
            gemini_client._enforce_gemini_rate_limit()
            gemini_client._enforce_gemini_rate_limit()
            with self.assertRaises(RuntimeError):
                gemini_client._enforce_gemini_rate_limit()

    def test_analysis_input_size_validation(self) -> None:
        with patch.object(gemini_client, "_MAX_CV_INPUT_CHARS", 10):
            with self.assertRaises(ValueError):
                gemini_client._validate_analysis_inputs("x" * 11, "jd", 0)

        with patch.object(gemini_client, "_MAX_JD_INPUT_CHARS", 5):
            with self.assertRaises(ValueError):
                gemini_client._validate_analysis_inputs("cv", "j" * 6, 0)

        with patch.object(gemini_client, "_MAX_FILE_SIZE_BYTES", 100):
            with self.assertRaises(ValueError):
                gemini_client._validate_analysis_inputs("cv", "jd", 101)


if __name__ == "__main__":
    unittest.main()
