"""
Trusted Host Middleware for FastMVC.

Validates the Host header to prevent host header attacks.
"""

import re
from collections.abc import Awaitable, Callable, Sequence

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from fastmiddleware.base import FastMVCMiddleware


class TrustedHostMiddleware(FastMVCMiddleware):
    """
    Middleware that validates the Host header against a list of trusted hosts.

    Protects against host header attacks by rejecting requests with
    unrecognized Host headers. This is important for security when
    your application generates URLs based on the Host header.

    Features:
        - Exact host matching
        - Wildcard subdomain support (*.example.com)
        - Configurable response for rejected requests
        - Optional redirect to primary host

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import TrustedHostMiddleware

        app = FastAPI()

        # Single host
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["example.com", "www.example.com"],
        )

        # Wildcard subdomains
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.example.com"],
        )

        # Allow any host (development only!)
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],
        )
        ```

    Security:
        Never use `allowed_hosts=["*"]` in production. Always specify
        the exact hosts your application should respond to.
    """

    def __init__(
        self,
        app,
        allowed_hosts: Sequence[str] | None = None,
        redirect_to_primary: bool = False,
        primary_host: str | None = None,
        www_redirect: bool = False,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the trusted host middleware.

        Args:
            app: The ASGI application.
            allowed_hosts: List of allowed host names. Use "*" for any.
            redirect_to_primary: Redirect non-primary hosts to primary.
            primary_host: The primary host for redirects.
            www_redirect: Redirect www to non-www (or vice versa).
            exclude_paths: Paths to exclude from host validation.
            exclude_methods: HTTP methods to exclude from host validation.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        self.allowed_hosts = list(allowed_hosts) if allowed_hosts else ["*"]
        self.redirect_to_primary = redirect_to_primary
        self.primary_host = primary_host
        self.www_redirect = www_redirect

        # Pre-compile patterns for wildcard hosts
        self._host_patterns: list[re.Pattern | str] = []
        self._allow_any = False

        for host in self.allowed_hosts:
            if host == "*":
                self._allow_any = True
            elif host.startswith("*."):
                # Convert *.example.com to regex
                pattern = r"^([a-zA-Z0-9-]+\.)*" + re.escape(host[2:]) + r"$"
                self._host_patterns.append(re.compile(pattern, re.IGNORECASE))
            else:
                self._host_patterns.append(host.lower())

    def _is_valid_host(self, host: str) -> bool:
        """Check if host is in the allowed list."""
        if self._allow_any:
            return True

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        host = host.lower()

        for pattern in self._host_patterns:
            if isinstance(pattern, re.Pattern):
                if pattern.match(host):
                    return True
            elif pattern == host:
                return True

        return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Validate the Host header and process the request.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response, or 400 if host is invalid.
        """
        # Skip excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        host = request.headers.get("Host", "")

        if not self._is_valid_host(host):
            return PlainTextResponse(
                "Invalid host header",
                status_code=400,
            )

        # Handle www redirect if enabled
        if self.www_redirect and self.primary_host:
            host_without_port = host.split(":")[0].lower()
            primary_without_port = self.primary_host.split(":")[0].lower()

            if host_without_port != primary_without_port:
                # Redirect to primary host
                url = request.url.replace(netloc=self.primary_host)
                return Response(
                    status_code=301,
                    headers={"Location": str(url)},
                )

        return await call_next(request)
