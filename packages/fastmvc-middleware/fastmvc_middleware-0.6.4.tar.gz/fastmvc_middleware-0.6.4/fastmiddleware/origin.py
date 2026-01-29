"""
Origin Validation Middleware for FastMVC.

Validates Origin and Referer headers for security.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class OriginConfig:
    """
    Configuration for origin validation middleware.

    Attributes:
        allowed_origins: Set of allowed origins.
        allow_null_origin: Allow null Origin header.
        check_referer: Also check Referer header.
        strict_mode: Reject if no Origin/Referer present.
        safe_methods: Methods that skip validation.

    Example:
        ```python
        from fastmiddleware import OriginConfig

        config = OriginConfig(
            allowed_origins={
                "https://example.com",
                "https://app.example.com",
            },
        )
        ```
    """

    allowed_origins: set[str] = field(default_factory=set)
    allow_null_origin: bool = False
    check_referer: bool = True
    strict_mode: bool = False
    safe_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD", "OPTIONS"})


class OriginMiddleware(FastMVCMiddleware):
    """
    Middleware that validates Origin and Referer headers.

    Protects against CSRF by ensuring requests originate
    from trusted sources.

    Features:
        - Origin header validation
        - Referer header fallback
        - Wildcard subdomain support
        - Safe method bypass

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import OriginMiddleware

        app = FastAPI()

        app.add_middleware(
            OriginMiddleware,
            allowed_origins={
                "https://example.com",
                "https://*.example.com",  # Wildcard subdomain
            },
        )

        # POST requests from other origins get 403
        ```
    """

    def __init__(
        self,
        app,
        config: OriginConfig | None = None,
        allowed_origins: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or OriginConfig()

        if allowed_origins is not None:
            self.config.allowed_origins = allowed_origins

    def _normalize_origin(self, origin: str) -> str:
        """Normalize origin URL."""
        if not origin:
            return ""

        parsed = urlparse(origin.lower())
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return origin.lower()

    def _matches_pattern(self, origin: str, pattern: str) -> bool:
        """Check if origin matches pattern (supports wildcards)."""
        origin = self._normalize_origin(origin)
        pattern = pattern.lower()

        # Exact match
        if origin == pattern:
            return True

        # Wildcard subdomain match
        if pattern.startswith("https://*.") or pattern.startswith("http://*."):
            scheme, rest = pattern.split("://", 1)
            domain = rest[2:]  # Remove *.

            origin_parsed = urlparse(origin)
            if origin_parsed.scheme != scheme:
                return False

            # Check if host ends with domain
            host = origin_parsed.netloc
            if host == domain or host.endswith(f".{domain}"):
                return True

        return False

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list."""
        if not origin:
            return False

        if origin.lower() == "null":
            return self.config.allow_null_origin

        for allowed in self.config.allowed_origins:
            if self._matches_pattern(origin, allowed):
                return True

        return False

    def _extract_origin(self, request: Request) -> str | None:
        """Extract origin from request."""
        # Try Origin header first
        origin = request.headers.get("Origin")
        if origin:
            return origin

        # Fall back to Referer
        if self.config.check_referer:
            referer = request.headers.get("Referer")
            if referer:
                parsed = urlparse(referer)
                if parsed.scheme and parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}"

        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Safe methods skip validation
        if request.method in self.config.safe_methods:
            return await call_next(request)

        origin = self._extract_origin(request)

        # No origin
        if not origin:
            if self.config.strict_mode:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": True,
                        "message": "Origin header required",
                    },
                )
            return await call_next(request)

        # Validate origin
        if not self._is_origin_allowed(origin):
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "Origin not allowed",
                },
            )

        return await call_next(request)
