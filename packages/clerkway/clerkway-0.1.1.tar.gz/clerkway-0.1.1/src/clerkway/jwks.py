"""Custom JWKS client for Clerk Backend API authentication.

Clerk's Backend API (api.clerk.com/v1/jwks) requires:
1. Authorization header with Bearer token (CLERK_SECRET_KEY)
2. User-Agent header (urllib omits this by default, causing 403)

This module provides a PyJWKClient subclass that handles these requirements.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

from jwt import PyJWKClient

# Module-level cache for the JWKS client
_jwks_client: PyJWKClient | None = None


class ClerkJWKClient(PyJWKClient):
    """PyJWKClient subclass that adds required headers for Clerk API.
    
    Clerk's api.clerk.com endpoint requires:
    - User-Agent header (urllib doesn't send one by default)
    - Authorization: Bearer <secret_key> header
    
    Without these, requests return 403 Forbidden.
    """

    def __init__(
        self,
        uri: str,
        secret_key: str | None = None,
        user_agent: str = "ClerkNgrokProxy/1.0",
        **kwargs: Any,
    ) -> None:
        """Initialize the Clerk JWKS client.
        
        Args:
            uri: The JWKS endpoint URL (e.g., https://api.clerk.com/v1/jwks)
            secret_key: Clerk secret key for Authorization header
            user_agent: User-Agent string to send with requests
            **kwargs: Additional arguments passed to PyJWKClient
        """
        super().__init__(uri, **kwargs)
        self._secret_key = secret_key
        self._user_agent = user_agent

    def fetch_data(self) -> Any:
        """Override fetch_data to add required headers."""
        req = urllib.request.Request(self.uri)
        req.add_header("User-Agent", self._user_agent)
        
        if self._secret_key:
            req.add_header("Authorization", f"Bearer {self._secret_key}")

        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode())


def get_jwks_client(
    jwks_url: str,
    secret_key: str | None = None,
    cache_keys: bool = True,
    timeout: int = 30,
    force_new: bool = False,
) -> PyJWKClient:
    """Get or create a JWKS client for Clerk JWT verification.
    
    Uses a module-level singleton by default. Pass force_new=True to create
    a fresh client.
    
    Args:
        jwks_url: The JWKS endpoint URL. Use https://api.clerk.com/v1/jwks
                  for Clerk's Backend API (recommended for speed).
        secret_key: Clerk secret key. Required if using api.clerk.com endpoint.
        cache_keys: Whether to cache signing keys (recommended).
        timeout: Request timeout in seconds.
        force_new: If True, create a new client instead of using cached one.
    
    Returns:
        A PyJWKClient instance configured for Clerk.
    
    Example:
        ```python
        client = get_jwks_client(
            jwks_url="https://api.clerk.com/v1/jwks",
            secret_key=os.environ["CLERK_SECRET_KEY"],
        )
        signing_key = client.get_signing_key_from_jwt(token)
        ```
    """
    global _jwks_client
    
    if _jwks_client is not None and not force_new:
        return _jwks_client
    
    # Use custom client for Clerk API endpoints (requires auth headers)
    if "api.clerk.dev" in jwks_url or "api.clerk.com" in jwks_url:
        if not secret_key:
            raise ValueError(
                "secret_key is required when using Clerk Backend API JWKS endpoint"
            )
        _jwks_client = ClerkJWKClient(
            jwks_url,
            secret_key=secret_key,
            cache_keys=cache_keys,
            timeout=timeout,
        )
    else:
        # Standard client for other endpoints (e.g., proxied JWKS)
        _jwks_client = PyJWKClient(
            jwks_url,
            cache_keys=cache_keys,
            timeout=timeout,
        )
    
    return _jwks_client
