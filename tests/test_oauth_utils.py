import base64
import hashlib
import hmac
import json
import os
import re
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import auth_utils, oauth_utils
from src.database import Base, User
from src.oauth_utils import build_google_auth_url

# 64 hex chars: passes the strong-secret guard. Test-only value.
_TEST_SECRET = "a5" * 32


def _state_payload(state: str) -> dict:
    payload = state.rsplit(".", 1)[0]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def _sign_raw_state(payload_obj: dict) -> str:
    """Sign a state payload the way the server does (used to build legacy/unbound states)."""
    raw = json.dumps(payload_obj, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    sig = hmac.new(_TEST_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


class _SecretMixin(unittest.TestCase):
    def setUp(self) -> None:
        env = patch.dict("os.environ", {"SESSION_SECRET": _TEST_SECRET}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        oauth_utils._CONSUMED_STATE_NONCES.clear()
        self.addCleanup(oauth_utils._CONSUMED_STATE_NONCES.clear)


class OAuthUtilsTests(unittest.TestCase):
    def test_build_google_auth_url_includes_state(self) -> None:
        state = "state-token-123"
        url = build_google_auth_url(state=state)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual(params.get("state", [""])[0], state)


class OAuthStateBindingTests(_SecretMixin):
    """3a: a state is only redeemable by the browser holding the matching nonce, once."""

    def test_state_round_trip_with_matching_nonce(self) -> None:
        nonce = oauth_utils.new_oauth_nonce()
        state = oauth_utils.create_oauth_state_token("home", nonce=nonce)
        data = oauth_utils.parse_oauth_state_token(state, nonce)
        self.assertIsNotNone(data)
        self.assertEqual(data["next"], "home")

    def test_state_carries_nonce_digest_not_nonce(self) -> None:
        nonce = oauth_utils.new_oauth_nonce()
        state = oauth_utils.create_oauth_state_token(nonce=nonce)
        self.assertNotIn(nonce, state)
        self.assertEqual(
            _state_payload(state)["nonce_sha256"], hashlib.sha256(nonce.encode()).hexdigest()
        )

    def test_state_rejected_without_nonce(self) -> None:
        state = oauth_utils.create_oauth_state_token(nonce=oauth_utils.new_oauth_nonce())
        self.assertIsNone(oauth_utils.parse_oauth_state_token(state, None))
        self.assertIsNone(oauth_utils.parse_oauth_state_token(state, ""))

    def test_attacker_state_rejected_in_victim_browser(self) -> None:
        # The attacker loads the login page and gets a valid state for THEIR nonce.
        attacker_state = oauth_utils.create_oauth_state_token(nonce=oauth_utils.new_oauth_nonce())
        victim_nonce = oauth_utils.new_oauth_nonce()
        self.assertIsNone(oauth_utils.parse_oauth_state_token(attacker_state, victim_nonce))
        self.assertFalse(oauth_utils.validate_oauth_state_token(attacker_state, victim_nonce))

    def test_unbound_state_is_rejected(self) -> None:
        now = int(time.time())
        legacy = _sign_raw_state({"iat": now, "exp": now + 600, "next": "home"})
        self.assertIsNone(oauth_utils.parse_oauth_state_token(legacy, "any-nonce"))

    def test_state_is_single_use(self) -> None:
        nonce = oauth_utils.new_oauth_nonce()
        state = oauth_utils.create_oauth_state_token(nonce=nonce)
        self.assertIsNotNone(oauth_utils.parse_oauth_state_token(state, nonce))
        self.assertIsNone(oauth_utils.parse_oauth_state_token(state, nonce))
        # A second state minted for the same nonce is also spent.
        again = oauth_utils.create_oauth_state_token(nonce=nonce)
        self.assertIsNone(oauth_utils.parse_oauth_state_token(again, nonce))

    def test_expired_state_rejected(self) -> None:
        nonce = oauth_utils.new_oauth_nonce()
        with patch("src.oauth_utils.time.time", return_value=1000.0):
            state = oauth_utils.create_oauth_state_token(nonce=nonce)
        self.assertIsNone(oauth_utils.parse_oauth_state_token(state, nonce))

    def test_create_requires_nonce(self) -> None:
        with self.assertRaises(ValueError):
            oauth_utils.create_oauth_state_token(nonce="")


class OAuthBrowserFlowTests(_SecretMixin):
    """The nonce must survive the full-page round trip to Google, which starts a new
    Streamlit session with empty st.session_state, by travelling in a cookie."""

    def test_flow_succeeds_across_sessions_via_cookie(self) -> None:
        browser_cookies: dict[str, str] = {}
        written: list[str] = []

        def fake_write(cookie: str) -> None:
            written.append(cookie)
            name, _, rest = cookie.partition("=")
            value = rest.split(";", 1)[0]
            if "max-age=0" in cookie:
                browser_cookies.pop(name, None)
            else:
                browser_cookies[name] = value

        with (
            patch.object(auth_utils, "_write_browser_cookie", side_effect=fake_write),
            patch.object(
                auth_utils,
                "_read_request_cookie",
                side_effect=lambda name: browser_cookies.get(name, ""),
            ),
        ):
            # Session A: the auth page renders twice (a Streamlit rerun) and keeps one nonce.
            with patch.object(auth_utils.st, "session_state", {}):
                url_1 = auth_utils.begin_google_oauth("home")
                url_2 = auth_utils.begin_google_oauth("home")
            state = parse_qs(urlparse(url_2).query)["state"][0]
            state_1 = parse_qs(urlparse(url_1).query)["state"][0]
            self.assertEqual(
                _state_payload(state)["nonce_sha256"], _state_payload(state_1)["nonce_sha256"]
            )
            self.assertIn("SameSite=Lax", written[0])

            # Session B: Google redirects back. Fresh, empty session_state.
            with patch.object(auth_utils.st, "session_state", {}):
                nonce = auth_utils.take_oauth_nonce()
                self.assertIsNotNone(oauth_utils.parse_oauth_state_token(state, nonce))
            self.assertNotIn(auth_utils._OAUTH_NONCE_COOKIE, browser_cookies)

            # Replaying the same callback URL afterwards fails.
            with patch.object(auth_utils.st, "session_state", {}):
                nonce = auth_utils.take_oauth_nonce()
                self.assertIsNone(oauth_utils.parse_oauth_state_token(state, nonce))

    def _callback_with_browser_cookie(self, state: str, cookie_nonce: str | None):
        """Run the real callback with real take_oauth_nonce against a fake cookie jar."""
        import app

        browser = _FakeBrowser()
        if cookie_nonce is not None:
            browser.jar[auth_utils._OAUTH_NONCE_COOKIE] = cookie_nonce
        session: dict = {}
        exchange = MagicMock(return_value=None)
        with (
            patch.object(auth_utils.components, "html", side_effect=browser.run_component),
            patch.object(app.st, "query_params", {"code": "c", "state": state}),
            patch.object(app.st, "session_state", session),
            patch.object(app.st, "context", browser.context()),
            patch.object(app, "_set_query_params_atomic"),
            patch("src.oauth_utils.exchange_code_for_userinfo", exchange),
        ):
            app._handle_oauth_callback()
        return session, exchange

    def test_callback_without_cookie_explains_the_cookie_problem(self) -> None:
        import app

        state = oauth_utils.create_oauth_state_token(nonce=oauth_utils.new_oauth_nonce())
        session, exchange = self._callback_with_browser_cookie(state, cookie_nonce=None)

        message = session.get("oauth_error", "")
        self.assertEqual(message, app._OAUTH_NO_COOKIE_MESSAGE)
        self.assertIn("browser did not send back the sign-in cookie", message)
        self.assertIn("click Continue with Google again", message)
        self.assertIn("may be blocking cookies", message)
        self.assertNotIn("invalid state", message)
        self.assertEqual(session.get("page"), "auth")
        exchange.assert_not_called()

    def test_callback_with_wrong_cookie_reports_invalid_state(self) -> None:
        import app

        state = oauth_utils.create_oauth_state_token(nonce=oauth_utils.new_oauth_nonce())
        session, exchange = self._callback_with_browser_cookie(
            state, cookie_nonce=oauth_utils.new_oauth_nonce()
        )

        self.assertIn("invalid state", session.get("oauth_error", ""))
        self.assertNotEqual(session.get("oauth_error"), app._OAUTH_NO_COOKIE_MESSAGE)
        exchange.assert_not_called()

    def test_callback_with_matching_cookie_reaches_code_exchange(self) -> None:
        import app

        nonce = oauth_utils.new_oauth_nonce()
        state = oauth_utils.create_oauth_state_token(nonce=nonce)
        session: dict = {}
        exchange = MagicMock(return_value=None)
        with (
            patch.object(app.st, "query_params", {"code": "c", "state": state}),
            patch.object(app.st, "session_state", session),
            patch.object(app, "take_oauth_nonce", return_value=nonce),
            patch.object(app, "_set_query_params_atomic"),
            patch("src.oauth_utils.exchange_code_for_userinfo", exchange),
        ):
            app._handle_oauth_callback()
        exchange.assert_called_once_with("c")
        self.assertNotIn("invalid state", session.get("oauth_error", ""))


class _FakeBrowser:
    """A cookie jar fed by the real _write_browser_cookie output (components.html script)."""

    _COOKIE_JS = re.compile(r"var cookie = (\".*?\");")

    def __init__(self) -> None:
        self.jar: dict[str, str] = {}

    def run_component(self, html: str, **_kwargs) -> None:
        cookie = json.loads(self._COOKIE_JS.search(html).group(1))
        name, _, rest = cookie.partition("=")
        value = rest.split(";", 1)[0]
        if "max-age=0" in cookie:
            self.jar.pop(name, None)
        else:
            self.jar[name] = value

    def context(self) -> SimpleNamespace:
        """What st.context looks like for a new page load from this browser."""
        return SimpleNamespace(cookies=dict(self.jar), headers={}, url="http://localhost:8501")


class OAuthDefaultConfigFlowTests(_SecretMixin):
    """2a: Google sign-in must work in the default config, where persistent login is off.
    Only components.html and the request context are faked; the cookie code is real."""

    def _run_full_flow(self) -> None:
        import app

        self.assertFalse(auth_utils.is_persistent_login_enabled())
        browser = _FakeBrowser()
        user = {"id": "u1", "email": "a@example.com", "full_name": "A"}
        userinfo = {"sub": "g1", "email": "a@example.com", "email_verified": True}

        with patch.object(auth_utils.components, "html", side_effect=browser.run_component):
            # Page load 1: the auth page renders the Google button.
            with (
                patch.object(auth_utils.st, "session_state", {}),
                patch.object(auth_utils.st, "context", browser.context()),
            ):
                url = auth_utils.begin_google_oauth("home")
            self.assertIn(auth_utils._OAUTH_NONCE_COOKIE, browser.jar)
            state = parse_qs(urlparse(url).query)["state"][0]

            # Page load 2: Google redirects back. New Streamlit session, empty state.
            session: dict = {}
            with (
                patch.object(app.st, "query_params", {"code": "c", "state": state}),
                patch.object(app.st, "session_state", session),
                patch.object(app.st, "context", browser.context()),
                patch.object(app, "_set_query_params_atomic"),
                patch("src.oauth_utils.exchange_code_for_userinfo", return_value=userinfo),
                patch.object(app, "get_or_create_google_user", return_value=user),
            ):
                app._handle_oauth_callback()

        self.assertNotIn("oauth_error", session)
        self.assertEqual(session.get("user"), user)
        self.assertNotIn(auth_utils._OAUTH_NONCE_COOKIE, browser.jar)  # cleared after use

    def test_full_flow_with_persistent_login_unset(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("ENABLE_PERSISTENT_LOGIN", None)
            self._run_full_flow()

    def test_full_flow_with_persistent_login_zero(self) -> None:
        with patch.dict("os.environ", {"ENABLE_PERSISTENT_LOGIN": "0"}, clear=False):
            self._run_full_flow()


class ConsumedNonceEvictionTests(_SecretMixin):
    """2c: the single-use record drops entries once their state has expired."""

    def test_expired_entries_are_evicted(self) -> None:
        with patch("src.oauth_utils.time.time", return_value=1000.0):
            for i in range(500):
                self.assertTrue(oauth_utils._consume_nonce_digest(f"d{i}", 1000 + 600))
        self.assertEqual(len(oauth_utils._CONSUMED_STATE_NONCES), 500)

        with patch("src.oauth_utils.time.time", return_value=1000.0 + 601):
            self.assertTrue(oauth_utils._consume_nonce_digest("fresh", 1601 + 600))
        self.assertEqual(list(oauth_utils._CONSUMED_STATE_NONCES), ["fresh"])

    def test_unexpired_entries_are_kept(self) -> None:
        with patch("src.oauth_utils.time.time", return_value=1000.0):
            oauth_utils._consume_nonce_digest("a", 1600)
        with patch("src.oauth_utils.time.time", return_value=1599.0):
            self.assertFalse(oauth_utils._consume_nonce_digest("a", 1600))  # still spent
            oauth_utils._consume_nonce_digest("b", 2199)
        self.assertEqual(set(oauth_utils._CONSUMED_STATE_NONCES), {"a", "b"})

    def test_eviction_through_real_states(self) -> None:
        nonce_1 = oauth_utils.new_oauth_nonce()
        with patch("src.oauth_utils.time.time", return_value=5000.0):
            state_1 = oauth_utils.create_oauth_state_token(nonce=nonce_1)
            self.assertIsNotNone(oauth_utils.parse_oauth_state_token(state_1, nonce_1))
        nonce_2 = oauth_utils.new_oauth_nonce()
        later = 5000.0 + oauth_utils._STATE_TTL_SECONDS + 1
        with patch("src.oauth_utils.time.time", return_value=later):
            state_2 = oauth_utils.create_oauth_state_token(nonce=nonce_2)
            self.assertIsNotNone(oauth_utils.parse_oauth_state_token(state_2, nonce_2))
        self.assertEqual(
            list(oauth_utils._CONSUMED_STATE_NONCES),
            [hashlib.sha256(nonce_2.encode()).hexdigest()],
        )


def _mock_google(userinfo: dict):
    token_resp = MagicMock(status_code=200)
    token_resp.json.return_value = {"access_token": "t"}
    info_resp = MagicMock(status_code=200)
    info_resp.json.return_value = userinfo
    return (
        patch.object(oauth_utils.requests, "post", return_value=token_resp),
        patch.object(oauth_utils.requests, "get", return_value=info_resp),
    )


class GoogleEmailVerifiedTests(unittest.TestCase):
    """3b: an unverified Google email must never log in or link to an existing account."""

    def setUp(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        db = self.Session()
        db.add(User(full_name="Victim", email="victim@example.com", hashed_password="bcrypt"))
        db.commit()
        db.close()
        get_db = patch.object(auth_utils, "get_db", side_effect=self.Session)
        get_db.start()
        self.addCleanup(get_db.stop)

    def _victim_google_id(self):
        db = self.Session()
        try:
            return db.query(User).filter_by(email="victim@example.com").one().google_id
        finally:
            db.close()

    def test_exchange_rejects_userinfo_without_verified_email(self) -> None:
        base = {"sub": "s1", "email": "victim@example.com", "name": "X"}
        for extra in ({}, {"email_verified": False}, {"email_verified": "true"}):
            with self.subTest(extra=extra):
                post, get = _mock_google({**base, **extra})
                with post, get:
                    self.assertIsNone(oauth_utils.exchange_code_for_userinfo("code"))

    def test_exchange_accepts_verified_email(self) -> None:
        info = {"sub": "s1", "email": "a@example.com", "email_verified": True}
        post, get = _mock_google(info)
        with post, get:
            self.assertEqual(oauth_utils.exchange_code_for_userinfo("code"), info)

    def test_unverified_email_not_linked_to_password_account(self) -> None:
        for info in (
            {"sub": "attacker", "email": "victim@example.com"},
            {"sub": "attacker", "email": "victim@example.com", "email_verified": False},
        ):
            with self.subTest(info=info):
                self.assertIsNone(auth_utils.get_or_create_google_user(info))
                self.assertIsNone(self._victim_google_id())

    def test_verified_email_links_to_password_account(self) -> None:
        user = auth_utils.get_or_create_google_user(
            {"sub": "g-victim", "email": "victim@example.com", "email_verified": True}
        )
        self.assertEqual(user["email"], "victim@example.com")
        self.assertEqual(self._victim_google_id(), "g-victim")

    def test_unverified_email_does_not_create_account(self) -> None:
        self.assertIsNone(
            auth_utils.get_or_create_google_user({"sub": "s2", "email": "new@example.com"})
        )
        db = self.Session()
        try:
            self.assertIsNone(db.query(User).filter_by(email="new@example.com").first())
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
