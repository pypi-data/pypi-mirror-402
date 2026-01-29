"""
Timeout Middleware for FastMVC.

Enforces request timeout limits to prevent long-running requests.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class TimeoutConfig:
    """
    Configuration for timeout middleware.

    Attributes:
        default_timeout: Default timeout in seconds.
        path_timeouts: Path-specific timeout overrides.
        timeout_response_code: HTTP status code for timeout responses.
        timeout_message: Message returned on timeout.

    Example:
        ```python
        from FastMiddleware import TimeoutConfig

        config = TimeoutConfig(
            default_timeout=30.0,
            path_timeouts={
                "/upload": 120.0,
                "/export": 300.0,
            },
        )
        ```
    """

    default_timeout: float = 30.0
    path_timeouts: dict[str, float] = field(default_factory=dict)
    timeout_response_code: int = 504
    timeout_message: str = "Request timed out"


class TimeoutMiddleware(FastMVCMiddleware):
    """
    Middleware that enforces request timeout limits.

    Cancels requests that exceed the configured timeout and returns
    a 504 Gateway Timeout response.

    Features:
        - Configurable default timeout
        - Path-specific timeout overrides
        - Graceful cancellation
        - Custom timeout responses

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import TimeoutMiddleware, TimeoutConfig

        app = FastAPI()

        # 30 second default timeout
        app.add_middleware(TimeoutMiddleware, timeout=30.0)

        # With path-specific timeouts
        config = TimeoutConfig(
            default_timeout=30.0,
            path_timeouts={
                "/upload": 120.0,
                "/long-process": 300.0,
            },
        )
        app.add_middleware(TimeoutMiddleware, config=config)
        ```
    """

    def __init__(
        self,
        app,
        config: TimeoutConfig | None = None,
        timeout: float | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the timeout middleware.

        Args:
            app: The ASGI application.
            config: Timeout configuration.
            timeout: Default timeout (overrides config).
            exclude_paths: Paths to exclude from timeout.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or TimeoutConfig()

        if timeout is not None:
            self.config.default_timeout = timeout

    def _get_timeout(self, path: str) -> float:
        """Get timeout for a specific path."""
        for prefix, timeout in self.config.path_timeouts.items():
            if path.startswith(prefix):
                return timeout
        return self.config.default_timeout

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with timeout enforcement.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The HTTP response or timeout error.
        """
        if self.should_skip(request):
            return await call_next(request)

        timeout = self._get_timeout(request.url.path)

        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=self.config.timeout_response_code,
                content={
                    "error": True,
                    "message": self.config.timeout_message,
                    "timeout_seconds": timeout,
                },
                headers={"X-Timeout": str(timeout)},
            )
