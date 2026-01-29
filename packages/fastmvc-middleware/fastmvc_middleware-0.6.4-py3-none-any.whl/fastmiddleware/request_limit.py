"""
Request Size Limit Middleware for FastMVC.

Limits the size of request bodies to prevent abuse.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


def parse_size(size: str | int) -> int:
    """Parse size string (e.g., '10MB') to bytes."""
    if isinstance(size, int):
        return size

    size = size.strip().upper()
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "K": 1024,
        "M": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
    }

    for unit, multiplier in units.items():
        if size.endswith(unit):
            return int(float(size[: -len(unit)].strip()) * multiplier)

    return int(size)


@dataclass
class RequestLimitConfig:
    """
    Configuration for request size limit middleware.

    Attributes:
        max_size: Maximum request body size (bytes or string like '10MB').
        path_limits: Path-specific size limits.
        response_code: HTTP status code for oversized requests.
        error_message: Message returned for oversized requests.

    Example:
        ```python
        from fastmiddleware import RequestLimitConfig

        config = RequestLimitConfig(
            max_size="10MB",
            path_limits={
                "/upload": "100MB",
                "/api": "1MB",
            },
        )
        ```
    """

    max_size: str | int = "10MB"
    path_limits: dict[str, str | int] = field(default_factory=dict)
    response_code: int = 413
    error_message: str = "Request body too large"


class RequestLimitMiddleware(FastMVCMiddleware):
    """
    Middleware that limits request body size.

    Protects your server from memory exhaustion attacks by rejecting
    requests with bodies larger than the configured limit.

    Features:
        - Global size limit
        - Path-specific overrides
        - Human-readable size strings
        - Early rejection (checks Content-Length)

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import RequestLimitMiddleware

        app = FastAPI()

        # 10MB limit
        app.add_middleware(RequestLimitMiddleware, max_size="10MB")

        # With path-specific limits
        app.add_middleware(
            RequestLimitMiddleware,
            max_size="10MB",
            path_limits={
                "/upload": "100MB",
                "/api": "1MB",
            },
        )
        ```
    """

    def __init__(
        self,
        app,
        config: RequestLimitConfig | None = None,
        max_size: str | int | None = None,
        path_limits: dict[str, str | int] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the request limit middleware.

        Args:
            app: The ASGI application.
            config: Request limit configuration.
            max_size: Maximum size (overrides config).
            path_limits: Path-specific limits (overrides config).
            exclude_paths: Paths to exclude from limit.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestLimitConfig()

        if max_size is not None:
            self.config.max_size = max_size
        if path_limits is not None:
            self.config.path_limits = path_limits

        # Parse sizes
        self._max_size_bytes = parse_size(self.config.max_size)
        self._path_limits_bytes = {
            path: parse_size(size) for path, size in self.config.path_limits.items()
        }

    def _get_limit(self, path: str) -> int:
        """Get size limit for a specific path."""
        for prefix, limit in self._path_limits_bytes.items():
            if path.startswith(prefix):
                return limit
        return self._max_size_bytes

    def _format_size(self, size: int) -> str:
        """Format bytes as human-readable size."""
        for unit, threshold in [("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)]:
            if size >= threshold:
                return f"{size / threshold:.1f}{unit}"
        return f"{size}B"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with size limit check.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response or 413 if too large.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Check Content-Length header
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                size = int(content_length)
                limit = self._get_limit(request.url.path)

                if size > limit:
                    return JSONResponse(
                        status_code=self.config.response_code,
                        content={
                            "error": True,
                            "message": self.config.error_message,
                            "max_size": self._format_size(limit),
                            "request_size": self._format_size(size),
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)
