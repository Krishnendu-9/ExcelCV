import unittest
from urllib.parse import parse_qs, urlparse

from src.oauth_utils import build_google_auth_url


class OAuthUtilsTests(unittest.TestCase):
    def test_build_google_auth_url_includes_state(self) -> None:
        state = "state-token-123"
        url = build_google_auth_url(state=state)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual(params.get("state", [""])[0], state)


if __name__ == "__main__":
    unittest.main()
