import unittest
from unittest.mock import patch

from src import auth_utils, gemini_client


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
