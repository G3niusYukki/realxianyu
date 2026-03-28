"""Tests for app.signing module."""

from app.signing import sign_request


class TestSignRequest:
    """Tests for sign_request function."""

    def test_sign_request_is_deterministic(self) -> None:
        """Same inputs must produce the same output."""
        app_key = "test_app_key"
        app_secret = "test_app_secret"
        body = '{"page":1,"pageSize":20}'
        timestamp = "1700000000"

        sig1 = sign_request(app_key, app_secret, body, timestamp)
        sig2 = sign_request(app_key, app_secret, body, timestamp)

        assert sig1 == sig2
        assert len(sig1) == 32  # MD5 hex digest

    def test_sign_request_different_keys_produce_different_signatures(self) -> None:
        """Different app_key values must produce different signatures."""
        body = '{"page":1}'
        timestamp = "1700000000"
        app_secret = "shared_secret"

        sig1 = sign_request("key_a", app_secret, body, timestamp)
        sig2 = sign_request("key_b", app_secret, body, timestamp)

        assert sig1 != sig2

    def test_sign_request_different_secrets_produce_different_signatures(self) -> None:
        """Different app_secret values must produce different signatures."""
        app_key = "shared_key"
        body = '{"page":1}'
        timestamp = "1700000000"

        sig1 = sign_request(app_key, "secret_a", body, timestamp)
        sig2 = sign_request(app_key, "secret_b", body, timestamp)

        assert sig1 != sig2

    def test_sign_request_different_bodies_produce_different_signatures(self) -> None:
        """Different body values must produce different signatures."""
        app_key = "test_key"
        app_secret = "test_secret"
        timestamp = "1700000000"

        sig1 = sign_request(app_key, app_secret, '{"page":1}', timestamp)
        sig2 = sign_request(app_key, app_secret, '{"page":2}', timestamp)

        assert sig1 != sig2

    def test_sign_request_different_timestamps_produce_different_signatures(self) -> None:
        """Different timestamps must produce different signatures."""
        app_key = "test_key"
        app_secret = "test_secret"
        body = '{"page":1}'

        sig1 = sign_request(app_key, app_secret, body, "1700000000")
        sig2 = sign_request(app_key, app_secret, body, "1700000001")

        assert sig1 != sig2

    def test_sign_request_empty_body(self) -> None:
        """Empty body should produce a valid signature."""
        app_key = "test_key"
        app_secret = "test_secret"
        timestamp = "1700000000"

        sig = sign_request(app_key, app_secret, "", timestamp)

        assert sig is not None
        assert len(sig) == 32
        # Verify determinism
        sig2 = sign_request(app_key, app_secret, "", timestamp)
        assert sig == sig2
