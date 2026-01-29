"""
Request Fingerprinting Middleware for FastMVC.

Creates fingerprints for request identification.
"""

import hashlib
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


_fingerprint_ctx: ContextVar[str | None] = ContextVar("fingerprint", default=None)


def get_fingerprint() -> str | None:
    """Get current request fingerprint."""
    return _fingerprint_ctx.get()


@dataclass
class FingerprintConfig:
    """
    Configuration for fingerprint middleware.

    Attributes:
        include_ip: Include IP in fingerprint.
        include_ua: Include User-Agent.
        include_headers: Additional headers to include.
        include_path: Include path in fingerprint.
        add_header: Add fingerprint to response.
    """

    include_ip: bool = True
    include_ua: bool = True
    include_headers: list[str] = field(
        default_factory=lambda: [
            "Accept-Language",
            "Accept-Encoding",
        ]
    )
    include_path: bool = False
    add_header: bool = True
    header_name: str = "X-Fingerprint"


class RequestFingerprintMiddleware(FastMVCMiddleware):
    """
    Middleware that creates request fingerprints.

    Generates a fingerprint based on various request
    attributes for identification and analytics.

    Example:
        ```python
        from fastmiddleware import RequestFingerprintMiddleware, get_fingerprint

        app.add_middleware(RequestFingerprintMiddleware)

        @app.get("/")
        async def handler():
            fp = get_fingerprint()
            # Use fingerprint for analytics, rate limiting, etc.
            return {"fingerprint": fp}
        ```
    """

    def __init__(
        self,
        app,
        config: FingerprintConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or FingerprintConfig()

    def _compute_fingerprint(self, request: Request) -> str:
        """Compute fingerprint for request."""
        parts = []

        if self.config.include_ip:
            parts.append(self.get_client_ip(request))

        if self.config.include_ua:
            parts.append(request.headers.get("User-Agent", ""))

        for header in self.config.include_headers:
            parts.append(request.headers.get(header, ""))

        if self.config.include_path:
            parts.append(request.url.path)

        combined = "|".join(parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        fingerprint = self._compute_fingerprint(request)

        token = _fingerprint_ctx.set(fingerprint)
        request.state.fingerprint = fingerprint

        try:
            response = await call_next(request)

            if self.config.add_header:
                response.headers[self.config.header_name] = fingerprint

            return response
        finally:
            _fingerprint_ctx.reset(token)
