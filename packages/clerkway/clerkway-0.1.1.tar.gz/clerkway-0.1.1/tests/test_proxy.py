"""Tests for the Clerk proxy router."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from clerkway import ClerkProxyConfig, create_clerk_proxy_router, close_http_client


@pytest.fixture
def config():
    """Create a test configuration."""
    return ClerkProxyConfig(
        secret_key="sk_test_123456789",
        route_prefix="/__clerk",
    )


@pytest.fixture
def app(config):
    """Create a test FastAPI app with the proxy router."""
    app = FastAPI()
    app.include_router(create_clerk_proxy_router(config))
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
async def cleanup_http_client():
    """Clean up the HTTP client after each test."""
    yield
    await close_http_client()


class TestCookieRewriting:
    """Tests for Set-Cookie header rewriting."""

    def test_rewrites_clerk_domain_in_cookies(self, client):
        """Cookies with frontend-api.clerk.dev domain should be rewritten."""
        mock_response = httpx.Response(
            200,
            headers=[
                ("set-cookie", "session=abc123; domain=.frontend-api.clerk.dev; path=/; secure"),
                ("set-cookie", "client=xyz789; domain=frontend-api.clerk.dev; path=/"),
            ],
            content=b"{}",
        )

        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = client.get(
                "/__clerk/v1/client",
                headers={"host": "myapp.ngrok.dev"},
            )

        assert response.status_code == 200
        cookies = response.headers.get_list("set-cookie")
        assert len(cookies) == 2
        assert "domain=myapp.ngrok.dev" in cookies[0]
        assert "domain=myapp.ngrok.dev" in cookies[1]
        assert "frontend-api.clerk.dev" not in cookies[0]
        assert "frontend-api.clerk.dev" not in cookies[1]


class TestLocationRewriting:
    """Tests for Location header rewriting."""

    def test_rewrites_relative_location(self, client):
        """Relative /v1/ paths should get the prefix added."""
        mock_response = httpx.Response(
            302,
            headers={"location": "/v1/oauth_callback?code=123"},
            content=b"",
        )

        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = client.get(
                "/__clerk/v1/oauth/authorize",
                headers={"host": "myapp.ngrok.dev"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        assert response.headers["location"] == "/__clerk/v1/oauth_callback?code=123"

    def test_rewrites_absolute_clerk_location(self, client):
        """Absolute Clerk URLs should be rewritten to our domain."""
        mock_response = httpx.Response(
            302,
            headers={"location": "https://frontend-api.clerk.dev/v1/oauth_callback?code=123"},
            content=b"",
        )

        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = client.get(
                "/__clerk/v1/oauth/authorize",
                headers={"host": "myapp.ngrok.dev"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        assert response.headers["location"] == "https://myapp.ngrok.dev/__clerk/v1/oauth_callback?code=123"


class TestProxyHeaders:
    """Tests for proxy header handling."""

    def test_adds_clerk_proxy_headers(self, client):
        """Clerk-Proxy-Url and Clerk-Secret-Key headers should be added."""
        mock_response = httpx.Response(200, content=b"{}")

        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client.get(
                "/__clerk/v1/client",
                headers={"host": "myapp.ngrok.dev"},
            )

            call_kwargs = mock_client.request.call_args.kwargs
            assert "Clerk-Proxy-Url" in call_kwargs["headers"]
            assert "Clerk-Secret-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Clerk-Secret-Key"] == "sk_test_123456789"

    def test_strips_hop_by_hop_headers(self, client):
        """Hop-by-hop headers should be stripped from requests."""
        mock_response = httpx.Response(200, content=b"{}")

        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client.get(
                "/__clerk/v1/client",
                headers={
                    "host": "myapp.ngrok.dev",
                    "connection": "keep-alive",
                    "transfer-encoding": "chunked",
                },
            )

            call_kwargs = mock_client.request.call_args.kwargs
            headers_lower = {k.lower(): v for k, v in call_kwargs["headers"].items()}
            assert "connection" not in headers_lower
            assert "transfer-encoding" not in headers_lower


class TestErrorHandling:
    """Tests for error handling."""

    def test_returns_502_on_connection_error(self, client):
        """Connection errors should return 502 Bad Gateway."""
        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_get_client.return_value = mock_client

            response = client.get(
                "/__clerk/v1/client",
                headers={"host": "myapp.ngrok.dev"},
            )

        assert response.status_code == 502
        assert "Proxy error" in response.text

    def test_returns_502_on_timeout(self, client):
        """Timeout errors should return 502 Bad Gateway."""
        with patch("clerkway.proxy._get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
            mock_get_client.return_value = mock_client

            response = client.get(
                "/__clerk/v1/client",
                headers={"host": "myapp.ngrok.dev"},
            )

        assert response.status_code == 502
        assert "Proxy error" in response.text
