"""
Cost Tracking Middleware for FastMVC.

Tracks request costs for billing and quotas.
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


_cost_ctx: ContextVar[float] = ContextVar("request_cost", default=0.0)


def get_request_cost() -> float:
    """Get current request cost."""
    return _cost_ctx.get()


def add_cost(cost: float) -> None:
    """Add to current request cost."""
    current = _cost_ctx.get()
    _cost_ctx.set(current + cost)


@dataclass
class CostTrackingConfig:
    """
    Configuration for cost tracking middleware.

    Attributes:
        path_costs: Base cost per path.
        method_multipliers: Cost multiplier per method.
        add_header: Add cost header to response.
    """

    path_costs: dict[str, float] = field(default_factory=dict)
    method_multipliers: dict[str, float] = field(
        default_factory=lambda: {
            "GET": 1.0,
            "POST": 2.0,
            "PUT": 2.0,
            "PATCH": 2.0,
            "DELETE": 1.5,
        }
    )
    default_cost: float = 1.0
    add_header: bool = True
    header_name: str = "X-Request-Cost"


class CostTrackingMiddleware(FastMVCMiddleware):
    """
    Middleware for tracking request costs.

    Assigns costs to requests for billing, quotas,
    or resource management.

    Example:
        ```python
        from fastmiddleware import CostTrackingMiddleware, add_cost

        app.add_middleware(
            CostTrackingMiddleware,
            path_costs={
                "/api/expensive": 10.0,
                "/api/cheap": 0.5,
            },
        )

        @app.get("/api/custom")
        async def handler():
            # Add custom costs during processing
            add_cost(5.0)  # External API call
            add_cost(2.0)  # Database query
            return result
        ```
    """

    def __init__(
        self,
        app,
        config: CostTrackingConfig | None = None,
        path_costs: dict[str, float] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CostTrackingConfig()

        if path_costs:
            self.config.path_costs = path_costs

        self._total_costs: dict[str, float] = defaultdict(float)
        self._request_counts: dict[str, int] = defaultdict(int)

    def _get_base_cost(self, path: str) -> float:
        """Get base cost for path."""
        for pattern, cost in self.config.path_costs.items():
            if path.startswith(pattern):
                return cost
        return self.config.default_cost

    def _get_multiplier(self, method: str) -> float:
        """Get cost multiplier for method."""
        return self.config.method_multipliers.get(method, 1.0)

    def get_stats(self) -> dict[str, dict]:
        """Get cost statistics."""
        return {
            "total_costs": dict(self._total_costs),
            "request_counts": dict(self._request_counts),
        }

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Calculate base cost
        base_cost = self._get_base_cost(request.url.path)
        multiplier = self._get_multiplier(request.method)
        initial_cost = base_cost * multiplier

        token = _cost_ctx.set(initial_cost)

        try:
            response = await call_next(request)

            # Get final cost
            final_cost = _cost_ctx.get()

            # Track stats
            self._total_costs[request.url.path] += final_cost
            self._request_counts[request.url.path] += 1

            # Add header
            if self.config.add_header:
                response.headers[self.config.header_name] = str(final_cost)

            request.state.request_cost = final_cost

            return response
        finally:
            _cost_ctx.reset(token)
