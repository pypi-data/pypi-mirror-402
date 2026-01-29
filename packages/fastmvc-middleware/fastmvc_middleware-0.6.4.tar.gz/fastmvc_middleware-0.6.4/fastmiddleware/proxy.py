"""
Proxy Middleware for FastMVC.

Proxies requests to other services.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import httpx
from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class ProxyRoute:
    """Proxy route definition."""

    path_prefix: str
    target: str
    strip_prefix: bool = True
    preserve_host: bool = False
    add_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ProxyConfig:
    """
    Configuration for proxy middleware.

    Attributes:
        routes: List of proxy routes.
        timeout: Request timeout in seconds.
    """

    routes: list[ProxyRoute] = field(default_factory=list)
    timeout: float = 30.0
    follow_redirects: bool = False


class ProxyMiddleware(FastMVCMiddleware):
    """
    Middleware that proxies requests to other services.

    Acts as a reverse proxy for specified path prefixes,
    forwarding requests to configured backend services.

    Example:
        ```python
        from fastmiddleware import ProxyMiddleware, ProxyRoute

        app.add_middleware(
            ProxyMiddleware,
            routes=[
                ProxyRoute(
                    path_prefix="/api/v2",
                    target="http://new-api:8000",
                    strip_prefix=True,
                ),
                ProxyRoute(
                    path_prefix="/legacy",
                    target="http://old-service:3000",
                ),
            ],
        )

        # /api/v2/users -> http://new-api:8000/users
        # /legacy/data -> http://old-service:3000/legacy/data
        ```
    """

    def __init__(
        self,
        app,
        config: ProxyConfig | None = None,
        routes: list[ProxyRoute] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ProxyConfig()

        if routes:
            self.config.routes = routes

    def _find_route(self, path: str) -> ProxyRoute | None:
        """Find matching proxy route."""
        for route in self.config.routes:
            if path.startswith(route.path_prefix):
                return route
        return None

    def _build_target_url(self, route: ProxyRoute, path: str, query: str) -> str:
        """Build target URL for proxying."""
        if route.strip_prefix:
            path = path[len(route.path_prefix) :]
            if not path.startswith("/"):
                path = "/" + path

        url = f"{route.target.rstrip('/')}{path}"
        if query:
            url = f"{url}?{query}"

        return url

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        route = self._find_route(request.url.path)

        if not route:
            return await call_next(request)

        # Build target URL
        target_url = self._build_target_url(
            route,
            request.url.path,
            request.url.query,
        )

        # Build headers
        headers = dict(request.headers)
        headers.pop("host", None)

        if route.preserve_host:
            headers["X-Forwarded-Host"] = request.headers.get("host", "")

        headers.update(route.add_headers)

        # Forward client info
        client_ip = self.get_client_ip(request)
        if "X-Forwarded-For" in headers:
            headers["X-Forwarded-For"] += f", {client_ip}"
        else:
            headers["X-Forwarded-For"] = client_ip

        headers["X-Forwarded-Proto"] = request.url.scheme

        # Get request body
        body = await request.body()

        # Make proxied request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    timeout=self.config.timeout,
                    follow_redirects=self.config.follow_redirects,
                )
            except httpx.RequestError as e:
                from starlette.responses import JSONResponse

                return JSONResponse(
                    status_code=502,
                    content={
                        "error": True,
                        "message": "Bad Gateway",
                        "detail": str(e),
                    },
                )

        # Build response
        response_headers = dict(response.headers)
        response_headers.pop("transfer-encoding", None)
        response_headers.pop("content-encoding", None)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )
