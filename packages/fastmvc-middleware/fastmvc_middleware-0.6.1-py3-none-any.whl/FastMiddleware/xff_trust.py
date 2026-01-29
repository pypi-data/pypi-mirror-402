"""
X-Forwarded-For Trust Middleware for FastMVC.

Handles trusted proxy headers.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class XFFTrustConfig:
    """
    Configuration for X-Forwarded-For trust middleware.

    Attributes:
        trusted_proxies: List of trusted proxy IPs/CIDRs.
        depth: Number of proxies to skip from right.
        trust_all: Trust all X-Forwarded-For values.
    """

    trusted_proxies: list[str] = field(default_factory=list)
    depth: int = 1
    trust_all: bool = False


class XFFTrustMiddleware(FastMVCMiddleware):
    """
    Middleware that handles X-Forwarded-For headers.

    Properly extracts client IP from proxy headers
    based on trusted proxy configuration.

    Example:
        ```python
        from FastMiddleware import XFFTrustMiddleware

        app.add_middleware(
            XFFTrustMiddleware,
            trusted_proxies=["10.0.0.0/8", "172.16.0.0/12"],
            depth=2,  # Skip 2 rightmost proxies
        )
        ```
    """

    def __init__(
        self,
        app,
        config: XFFTrustConfig | None = None,
        trusted_proxies: list[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or XFFTrustConfig()

        if trusted_proxies:
            self.config.trusted_proxies = trusted_proxies

    def _is_trusted(self, ip: str) -> bool:
        """Check if IP is a trusted proxy."""
        if self.config.trust_all:
            return True

        return ip in self.config.trusted_proxies

    def _get_real_ip(self, request: Request) -> str:
        """Get real client IP from forwarded headers."""
        xff = request.headers.get("X-Forwarded-For")

        if not xff:
            client = request.scope.get("client")
            return client[0] if client else "unknown"

        ips = [ip.strip() for ip in xff.split(",")]

        if self.config.depth > 0 and len(ips) > self.config.depth:
            # Get IP at specified depth from right
            return ips[-(self.config.depth + 1)]

        # Return leftmost IP
        return ips[0]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        real_ip = self._get_real_ip(request)
        request.state.real_ip = real_ip

        return await call_next(request)
