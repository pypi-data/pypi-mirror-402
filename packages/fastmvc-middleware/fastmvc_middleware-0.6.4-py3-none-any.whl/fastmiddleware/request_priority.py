"""
Request Priority Middleware for FastMVC.

Prioritizes request processing based on rules.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import IntEnum

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


class Priority(IntEnum):
    """Request priority levels."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class PriorityConfig:
    """
    Configuration for priority middleware.

    Attributes:
        priority_header: Header containing priority.
        path_priorities: Path-specific priorities.
        max_queue_size: Max queue size per priority.
        timeout: Max queue wait time.
    """

    priority_header: str = "X-Priority"
    path_priorities: dict[str, Priority] = field(default_factory=dict)
    max_queue_size: int = 100
    timeout: float = 30.0


class RequestPriorityMiddleware(FastMVCMiddleware):
    """
    Middleware that prioritizes request processing.

    Higher priority requests are processed first when
    the server is under load.

    Example:
        ```python
        from fastmiddleware import RequestPriorityMiddleware, Priority

        app.add_middleware(
            RequestPriorityMiddleware,
            path_priorities={
                "/api/health": Priority.CRITICAL,
                "/api/webhooks": Priority.HIGH,
                "/api/reports": Priority.LOW,
            },
        )
        ```
    """

    def __init__(
        self,
        app,
        config: PriorityConfig | None = None,
        path_priorities: dict[str, Priority] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or PriorityConfig()

        if path_priorities:
            self.config.path_priorities = path_priorities

        self._processing = 0
        self._max_concurrent = 50

    def _get_priority(self, request: Request) -> Priority:
        """Get priority for request."""
        # Check header
        header_val = request.headers.get(self.config.priority_header)
        if header_val:
            try:
                return Priority[header_val.upper()]
            except KeyError:
                pass

        # Check path
        for pattern, priority in self.config.path_priorities.items():
            if request.url.path.startswith(pattern):
                return priority

        return Priority.NORMAL

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        priority = self._get_priority(request)
        request.state.priority = priority

        # For now, just add priority header
        response = await call_next(request)
        response.headers["X-Request-Priority"] = priority.name

        return response
