import unittest
from unittest.mock import patch

from src import auth_utils

# 64 hex chars: passes the strong-secret guard. Test-only value.
_TEST_SECRET = "0f" * 32


class AuthUtilsTests(unittest.TestCase):
    def test_hash_and_verify_password(self) -> None:
        hashed = auth_utils.hash_password("StrongPass123!")
        self.assertTrue(auth_utils.verify_password("StrongPass123!", hashed))
        self.assertFalse(auth_utils.verify_password("WrongPass123!", hashed))

    def test_verify_password_invalid_hash_returns_false(self) -> None:
        self.assertFalse(auth_utils.verify_password("anything", "not-a-valid-bcrypt-hash"))

    def test_session_token_round_trip_and_tamper_detection(self) -> None:
        user = {"id": "u1", "email": "a@example.com", "full_name": "A"}
        with patch.dict("os.environ", {"SESSION_SECRET": _TEST_SECRET}, clear=False):
            token = auth_utils.create_session_token(user)
            restored = auth_utils.validate_session_token(token)
            self.assertEqual(restored, user)

            tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
            self.assertIsNone(auth_utils.validate_session_token(tampered))

    def test_session_token_expiry(self) -> None:
        user = {"id": "u2", "email": "b@example.com", "full_name": "B"}
        with (
            patch.dict("os.environ", {"SESSION_SECRET": _TEST_SECRET}, clear=False),
            patch.object(auth_utils, "_SESSION_SECONDS", 1),
            patch("src.auth_utils.time.time", side_effect=[1000, 1002]),
        ):
            token = auth_utils.create_session_token(user)
            self.assertIsNone(auth_utils.validate_session_token(token))


if __name__ == "__main__":
    unittest.main()
