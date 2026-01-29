"""FastAPI router for proxying Clerk Frontend API requests.

This module provides a configurable router that proxies requests from
/__clerk/* to Clerk's frontend-api.clerk.dev, handling:

1. OAuth redirect Location header rewriting
2. Set-Cookie domain rewriting (multi-cookie support)
3. Required Clerk proxy headers (Clerk-Proxy-Url, Clerk-Secret-Key)
4. X-Forwarded-For preservation for client IP

Usage:
    ```python
    from fastapi import FastAPI
    from clerkway import create_clerk_proxy_router, ClerkProxyConfig
    
    app = FastAPI()
    
    config = ClerkProxyConfig(
        secret_key=os.environ["CLERK_SECRET_KEY"],
    )
    app.include_router(create_clerk_proxy_router(config))
    ```
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

CLERK_FRONTEND_API = "https://frontend-api.clerk.dev"


@dataclass
class ClerkProxyConfig:
    """Configuration for the Clerk proxy router.
    
    Attributes:
        secret_key: Clerk secret key (required). Get from Clerk Dashboard.
        route_prefix: URL prefix for proxy routes. Default: "/__clerk"
        timeout: HTTP request timeout in seconds. Default: 30
        log_oauth_callbacks: Whether to log OAuth callback details. Default: True
    """
    secret_key: str
    route_prefix: str = "/__clerk"
    timeout: float = 30.0
    log_oauth_callbacks: bool = True
    # Headers to strip from proxied requests (hop-by-hop headers)
    strip_request_headers: set[str] = field(default_factory=lambda: {
        "host",
        "connection",
        "keep-alive",
        "transfer-encoding",
        "accept-encoding",  # Get uncompressed responses for easier forwarding
    })
    # Headers to strip from proxied responses
    strip_response_headers: set[str] = field(default_factory=lambda: {
        "connection",
        "keep-alive",
        "transfer-encoding",
        "content-encoding",
        "content-length",
    })


def _get_proxy_url(request: Request, prefix: str) -> str:
    """Build the Clerk-Proxy-Url header value from the request."""
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return f"{proto}://{host}{prefix}"


def _get_client_ip(request: Request) -> str:
    """Extract the original client IP from the request."""
    # X-Forwarded-For may contain multiple IPs; take the first (original client)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def _get_domain(request: Request) -> str:
    """Get the domain from the request for cookie rewriting."""
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return host.split(":")[0]  # Remove port if present


# Module-level client for connection reuse
_http_client: httpx.AsyncClient | None = None


async def _get_http_client(timeout: float) -> httpx.AsyncClient:
    """Get or create the shared httpx client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
    return _http_client


async def close_http_client() -> None:
    """Close the shared httpx client. Call this on app shutdown."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


@asynccontextmanager
async def clerk_proxy_lifespan(app) -> AsyncIterator[None]:
    """Lifespan context manager for proper client cleanup.
    
    Usage:
        ```python
        from fastapi import FastAPI
        from clerkway import clerk_proxy_lifespan
        
        app = FastAPI(lifespan=clerk_proxy_lifespan)
        ```
    """
    yield
    await close_http_client()


def create_clerk_proxy_router(config: ClerkProxyConfig) -> APIRouter:
    """Create a FastAPI router that proxies Clerk Frontend API requests.
    
    The router handles:
    - Proxying all HTTP methods to Clerk's frontend-api.clerk.dev
    - Adding required Clerk-Proxy-Url and Clerk-Secret-Key headers
    - Rewriting Set-Cookie domains from frontend-api.clerk.dev to your domain
    - Rewriting Location headers for OAuth redirects
    - Preserving multiple Set-Cookie headers (critical for OAuth flow)
    
    Args:
        config: Proxy configuration including secret key and options.
    
    Returns:
        A FastAPI APIRouter to include in your application.
    
    Example:
        ```python
        from fastapi import FastAPI
        from clerkway import create_clerk_proxy_router, ClerkProxyConfig
        
        app = FastAPI()
        config = ClerkProxyConfig(secret_key=os.environ["CLERK_SECRET_KEY"])
        app.include_router(create_clerk_proxy_router(config))
        ```
    """
    router = APIRouter(tags=["clerk"])
    prefix = config.route_prefix

    @router.api_route(
        f"{prefix}/{{path:path}}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def clerk_proxy(request: Request, path: str) -> Response:
        """Proxy requests to Clerk's Frontend API."""
        # Build target URL
        target_url = f"{CLERK_FRONTEND_API}/{path}"
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"

        # Get request body
        body = await request.body()

        # Build headers - forward most headers but add Clerk-specific ones
        headers = {}
        for key, value in request.headers.items():
            if key.lower() not in config.strip_request_headers:
                headers[key] = value

        # Add required Clerk headers
        headers["Clerk-Proxy-Url"] = _get_proxy_url(request, prefix)
        headers["Clerk-Secret-Key"] = config.secret_key
        headers["X-Forwarded-For"] = _get_client_ip(request)

        # Get domain for cookie/redirect rewriting
        our_host = request.headers.get(
            "x-forwarded-host", request.headers.get("host", "")
        )
        our_domain = _get_domain(request)

        # Log OAuth callbacks for debugging
        is_oauth_callback = "oauth_callback" in path
        if is_oauth_callback and config.log_oauth_callbacks:
            logger.warning(f"OAuth callback URL: {target_url}")
            logger.warning(f"OAuth callback cookies: {request.cookies}")
            # Add Origin header for OAuth callbacks (browser doesn't send on navigation)
            if "origin" not in headers and "Origin" not in headers:
                headers["Origin"] = f"https://{our_host}"

        # Make proxied request - disable redirects to rewrite Location headers
        try:
            client = await _get_http_client(config.timeout)
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
        except httpx.RequestError as e:
            logger.error(f"Clerk proxy request failed: {e}")
            return Response(
                status_code=502,
                content=f"Proxy error: unable to reach Clerk API",
                media_type="text/plain",
            )

        # Log OAuth callback response
        if is_oauth_callback and config.log_oauth_callbacks:
            logger.warning(f"OAuth callback response: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"OAuth callback error: {response.text[:500]}")

        # Build response headers
        response_headers = {}
        set_cookie_headers = []

        # Use multi_items() to get ALL Set-Cookie headers (critical!)
        for key, value in response.headers.multi_items():
            lower_key = key.lower()
            
            if lower_key in config.strip_response_headers:
                continue

            # Rewrite Set-Cookie domain
            if lower_key == "set-cookie":
                value = value.replace(
                    "domain=.frontend-api.clerk.dev", f"domain={our_domain}"
                )
                value = value.replace(
                    "domain=frontend-api.clerk.dev", f"domain={our_domain}"
                )
                set_cookie_headers.append(value)
                continue

            # Rewrite Location header for redirects
            if lower_key == "location":
                # Relative paths like /v1/... need prefix
                if value.startswith("/v1/") or value.startswith("/v1?"):
                    value = f"{prefix}{value}"
                # Absolute URLs to Clerk need full rewrite
                elif "frontend-api.clerk.dev" in value:
                    value = value.replace(
                        "https://frontend-api.clerk.dev",
                        f"https://{our_domain}{prefix}",
                    )

            response_headers[key] = value

        # Create response and add Set-Cookie headers individually
        # (FastAPI Response only keeps one header per key, so we use append)
        resp = Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type"),
        )

        for cookie in set_cookie_headers:
            resp.headers.append("set-cookie", cookie)
        
        return resp

    return router
