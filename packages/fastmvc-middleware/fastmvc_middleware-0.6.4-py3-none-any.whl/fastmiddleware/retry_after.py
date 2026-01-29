"""
Retry-After Middleware for FastMVC.

Adds Retry-After headers to appropriate responses.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class RetryAfterConfig:
    """
    Configuration for retry-after middleware.

    Attributes:
        status_codes: Status codes that should include Retry-After.
        default_retry: Default retry time in seconds.
        status_retry_times: Per-status retry times.

    Example:
        ```python
        from fastmiddleware import RetryAfterConfig

        config = RetryAfterConfig(
            default_retry=60,
            status_retry_times={
                429: 30,   # Rate limited - wait 30s
                503: 120,  # Service unavailable - wait 2min
            },
        )
        ```
    """

    status_codes: set[int] = field(default_factory=lambda: {429, 503, 504})
    default_retry: int = 60
    status_retry_times: dict[int, int] = field(default_factory=dict)


class RetryAfterMiddleware(FastMVCMiddleware):
    """
    Middleware that adds Retry-After headers to error responses.

    Helps clients handle transient errors gracefully by indicating
    when they should retry.

    Features:
        - Automatic Retry-After headers
        - Per-status code retry times
        - Standards-compliant headers

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import RetryAfterMiddleware

        app = FastAPI()

        app.add_middleware(
            RetryAfterMiddleware,
            default_retry=60,
        )

        # 429 and 503 responses will include:
        # Retry-After: 60
        ```

    Standards:
        RFC 7231 defines Retry-After for 503, and it's commonly
        used for 429 rate limiting responses.
    """

    def __init__(
        self,
        app,
        config: RetryAfterConfig | None = None,
        default_retry: int | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the retry-after middleware.

        Args:
            app: The ASGI application.
            config: Retry-after configuration.
            default_retry: Default retry time (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RetryAfterConfig()

        if default_retry is not None:
            self.config.default_retry = default_retry

    def _get_retry_time(self, status_code: int) -> int:
        """Get retry time for status code."""
        return self.config.status_retry_times.get(status_code, self.config.default_retry)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and add Retry-After if needed.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with Retry-After header if applicable.
        """
        if self.should_skip(request):
            return await call_next(request)

        response = await call_next(request)

        # Check if should add Retry-After
        if response.status_code in self.config.status_codes:
            if "Retry-After" not in response.headers:
                retry_time = self._get_retry_time(response.status_code)
                response.headers["Retry-After"] = str(retry_time)

        return response
