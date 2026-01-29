"""
Deprecation Warning Middleware for FastMVC.

Adds deprecation warnings to API responses.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class DeprecationInfo:
    """Information about a deprecated endpoint."""

    message: str
    sunset_date: str | None = None  # ISO 8601 date
    replacement: str | None = None  # Alternative endpoint
    link: str | None = None  # Documentation link


@dataclass
class DeprecationConfig:
    """
    Configuration for deprecation middleware.

    Attributes:
        deprecated_paths: Map of deprecated paths to info.
        deprecated_headers: Map of deprecated headers to info.
        add_sunset_header: Add Sunset header for deprecated endpoints.
        add_warning_header: Add Warning header (RFC 7234).

    Example:
        ```python
        from fastmiddleware import DeprecationConfig, DeprecationInfo

        config = DeprecationConfig(
            deprecated_paths={
                "/api/v1/users": DeprecationInfo(
                    message="Use /api/v2/users instead",
                    sunset_date="2025-01-01",
                    replacement="/api/v2/users",
                ),
            },
        )
        ```
    """

    deprecated_paths: dict[str, DeprecationInfo] = field(default_factory=dict)
    deprecated_prefixes: dict[str, DeprecationInfo] = field(default_factory=dict)
    add_sunset_header: bool = True
    add_warning_header: bool = True
    add_deprecation_header: bool = True


class DeprecationMiddleware(FastMVCMiddleware):
    """
    Middleware that adds deprecation warnings to responses.

    Helps communicate API deprecations to clients through
    standard HTTP headers.

    Features:
        - Sunset header (RFC 8594)
        - Warning header (RFC 7234)
        - Custom deprecation messages
        - Replacement endpoint hints

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import DeprecationMiddleware, DeprecationInfo

        app = FastAPI()

        app.add_middleware(
            DeprecationMiddleware,
            deprecated_paths={
                "/api/v1/users": DeprecationInfo(
                    message="v1 API is deprecated",
                    sunset_date="2025-06-01",
                    replacement="/api/v2/users",
                ),
            },
        )

        # Deprecated endpoints will include headers:
        # Deprecation: true
        # Sunset: Sat, 01 Jun 2025 00:00:00 GMT
        # Warning: 299 - "v1 API is deprecated"
        # Link: </api/v2/users>; rel="successor-version"
        ```
    """

    def __init__(
        self,
        app,
        config: DeprecationConfig | None = None,
        deprecated_paths: dict[str, DeprecationInfo] | None = None,
        deprecated_prefixes: dict[str, DeprecationInfo] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the deprecation middleware.

        Args:
            app: The ASGI application.
            config: Deprecation configuration.
            deprecated_paths: Deprecated paths (overrides config).
            deprecated_prefixes: Deprecated path prefixes.
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or DeprecationConfig()

        if deprecated_paths is not None:
            self.config.deprecated_paths = deprecated_paths
        if deprecated_prefixes is not None:
            self.config.deprecated_prefixes = deprecated_prefixes

    def _get_deprecation_info(self, path: str) -> DeprecationInfo | None:
        """Get deprecation info for path."""
        # Check exact match
        if path in self.config.deprecated_paths:
            return self.config.deprecated_paths[path]

        # Check prefix match
        for prefix, info in self.config.deprecated_prefixes.items():
            if path.startswith(prefix):
                return info

        return None

    def _format_sunset_date(self, date_str: str) -> str:
        """Format sunset date as HTTP date."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            return date_str

    def _add_deprecation_headers(self, response: Response, info: DeprecationInfo) -> None:
        """Add deprecation headers to response."""
        if self.config.add_deprecation_header:
            response.headers["Deprecation"] = "true"

        if self.config.add_warning_header and info.message:
            response.headers["Warning"] = f'299 - "{info.message}"'

        if self.config.add_sunset_header and info.sunset_date:
            response.headers["Sunset"] = self._format_sunset_date(info.sunset_date)

        if info.replacement:
            response.headers["Link"] = f'<{info.replacement}>; rel="successor-version"'

        if info.link:
            existing_link = response.headers.get("Link", "")
            doc_link = f'<{info.link}>; rel="deprecation"'
            if existing_link:
                response.headers["Link"] = f"{existing_link}, {doc_link}"
            else:
                response.headers["Link"] = doc_link

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and add deprecation warnings.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with deprecation headers.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Check if endpoint is deprecated
        deprecation_info = self._get_deprecation_info(request.url.path)

        # Store in request state
        request.state.is_deprecated = deprecation_info is not None

        response = await call_next(request)

        # Add deprecation headers
        if deprecation_info:
            self._add_deprecation_headers(response, deprecation_info)

        return response
