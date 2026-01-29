"""Clerk authentication proxy for custom domains (ngrok, tunnels, etc.)."""
from clerkway.jwks import ClerkJWKClient, get_jwks_client
from clerkway.proxy import (
    ClerkProxyConfig,
    clerk_proxy_lifespan,
    close_http_client,
    create_clerk_proxy_router,
)

__all__ = [
    "ClerkJWKClient",
    "ClerkProxyConfig",
    "clerk_proxy_lifespan",
    "close_http_client",
    "create_clerk_proxy_router",
    "get_jwks_client",
]

__version__ = "0.1.0"
