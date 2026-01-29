"""
Slow Response Middleware for FastMVC.

Artificially slows responses for testing.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class SlowResponseConfig:
    """
    Configuration for slow response middleware.

    Attributes:
        enabled: Enable slow responses.
        min_delay: Minimum delay in seconds.
        max_delay: Maximum delay in seconds.
        fixed_delay: Use fixed delay (overrides min/max).
        affected_paths: Only affect these paths.
    """

    enabled: bool = False  # Must be explicitly enabled
    min_delay: float = 0.5
    max_delay: float = 3.0
    fixed_delay: float | None = None
    affected_paths: set[str] | None = None


class SlowResponseMiddleware(FastMVCMiddleware):
    """
    Middleware that artificially slows responses.

    Useful for testing timeout handling, loading states,
    and client behavior under slow network conditions.

    Example:
        ```python
        from fastmiddleware import SlowResponseMiddleware

        # Only enable in development/testing!
        app.add_middleware(
            SlowResponseMiddleware,
            enabled=os.getenv("SLOW_MODE") == "true",
            min_delay=1.0,
            max_delay=3.0,
        )
        ```
    """

    def __init__(
        self,
        app,
        config: SlowResponseConfig | None = None,
        enabled: bool = False,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or SlowResponseConfig()

        if enabled:
            self.config.enabled = True

    def _should_slow(self, path: str) -> bool:
        """Check if path should be slowed."""
        if self.config.affected_paths:
            return path in self.config.affected_paths or any(
                path.startswith(p) for p in self.config.affected_paths
            )
        return True

    def _get_delay(self) -> float:
        """Get delay duration."""
        if self.config.fixed_delay is not None:
            return self.config.fixed_delay
        return random.uniform(self.config.min_delay, self.config.max_delay)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self.config.enabled:
            return await call_next(request)

        if self.should_skip(request):
            return await call_next(request)

        if not self._should_slow(request.url.path):
            return await call_next(request)

        delay = self._get_delay()
        await asyncio.sleep(delay)

        response = await call_next(request)
        response.headers["X-Artificial-Delay"] = str(delay)

        return response
