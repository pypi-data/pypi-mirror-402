"""Tests for the JWKS client."""
import json
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from clerkway import ClerkJWKClient, get_jwks_client
from clerkway.jwks import _jwks_client


@pytest.fixture(autouse=True)
def reset_jwks_client():
    """Reset the global JWKS client before each test."""
    import clerkway.jwks
    clerkway.jwks._jwks_client = None
    yield
    clerkway.jwks._jwks_client = None


class TestClerkJWKClient:
    """Tests for ClerkJWKClient."""

    def test_adds_user_agent_header(self):
        """User-Agent header should be added to requests."""
        client = ClerkJWKClient(
            uri="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"keys": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            client.fetch_data()

            request = mock_urlopen.call_args[0][0]
            # urllib normalizes header names to 'User-agent' format
            assert "User-agent" in request.headers
            assert "ClerkNgrokProxy" in request.headers["User-agent"]

    def test_adds_authorization_header(self):
        """Authorization header should be added when secret_key is provided."""
        client = ClerkJWKClient(
            uri="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"keys": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            client.fetch_data()

            request = mock_urlopen.call_args[0][0]
            assert "Authorization" in request.headers
            assert request.headers["Authorization"] == "Bearer sk_test_123"

    def test_no_authorization_without_secret_key(self):
        """Authorization header should not be added without secret_key."""
        client = ClerkJWKClient(
            uri="https://example.com/.well-known/jwks.json",
            secret_key=None,
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"keys": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            client.fetch_data()

            request = mock_urlopen.call_args[0][0]
            assert "Authorization" not in request.headers


class TestGetJwksClient:
    """Tests for get_jwks_client factory function."""

    def test_requires_secret_key_for_clerk_api(self):
        """Secret key should be required for Clerk API endpoints."""
        with pytest.raises(ValueError, match="secret_key is required"):
            get_jwks_client(
                jwks_url="https://api.clerk.com/v1/jwks",
                secret_key=None,
            )

    def test_returns_clerk_client_for_clerk_api(self):
        """Should return ClerkJWKClient for Clerk API endpoints."""
        client = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )
        assert isinstance(client, ClerkJWKClient)

    def test_returns_standard_client_for_other_urls(self):
        """Should return standard PyJWKClient for non-Clerk URLs."""
        from jwt import PyJWKClient

        client = get_jwks_client(
            jwks_url="https://example.com/.well-known/jwks.json",
            secret_key=None,
            force_new=True,
        )
        # Should be PyJWKClient but not ClerkJWKClient
        assert isinstance(client, PyJWKClient)
        assert not isinstance(client, ClerkJWKClient)

    def test_caches_client_by_default(self):
        """Should return cached client on subsequent calls."""
        client1 = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )
        client2 = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )
        assert client1 is client2

    def test_force_new_creates_new_client(self):
        """force_new=True should create a new client."""
        client1 = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
        )
        client2 = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key="sk_test_123",
            force_new=True,
        )
        assert client1 is not client2
