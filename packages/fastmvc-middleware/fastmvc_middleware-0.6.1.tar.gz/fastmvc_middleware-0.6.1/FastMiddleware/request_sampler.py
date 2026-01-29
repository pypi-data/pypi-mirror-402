"""
Request Sampler Middleware for FastMVC.

Samples requests for logging, tracing, or analytics.
"""

import random
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_sampled_ctx: ContextVar[bool] = ContextVar("is_sampled", default=False)


def is_sampled() -> bool:
    """Check if current request is sampled."""
    return _sampled_ctx.get()


@dataclass
class RequestSamplerConfig:
    """
    Configuration for request sampler middleware.

    Attributes:
        rate: Sampling rate (0.0 to 1.0).
        path_rates: Path-specific sampling rates.
        header_name: Header to indicate sampling.
        force_header: Header to force sampling.
    """

    rate: float = 0.1  # 10% sampling
    path_rates: dict[str, float] = field(default_factory=dict)
    header_name: str = "X-Sampled"
    force_header: str = "X-Force-Sample"


class RequestSamplerMiddleware(FastMVCMiddleware):
    """
    Middleware for request sampling.

    Randomly samples requests for logging, distributed
    tracing, or analytics collection.

    Example:
        ```python
        from FastMiddleware import RequestSamplerMiddleware, is_sampled

        app.add_middleware(
            RequestSamplerMiddleware,
            rate=0.1,  # 10% of requests
            path_rates={
                "/api/high-traffic": 0.01,  # 1% for high-traffic
                "/api/debug": 1.0,  # 100% for debug
            },
        )

        @app.get("/")
        async def handler():
            if is_sampled():
                log_detailed_metrics()
            return result
        ```
    """

    def __init__(
        self,
        app,
        config: RequestSamplerConfig | None = None,
        rate: float | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestSamplerConfig()

        if rate is not None:
            self.config.rate = rate

    def _get_rate(self, path: str) -> float:
        """Get sampling rate for path."""
        for pattern, rate in self.config.path_rates.items():
            if path.startswith(pattern):
                return rate
        return self.config.rate

    def _should_sample(self, request: Request) -> bool:
        """Determine if request should be sampled."""
        # Check force header
        force = request.headers.get(self.config.force_header)
        if force:
            return force.lower() in ("true", "1", "yes")

        rate = self._get_rate(request.url.path)
        return random.random() < rate

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        sampled = self._should_sample(request)

        token = _sampled_ctx.set(sampled)
        request.state.is_sampled = sampled

        try:
            response = await call_next(request)

            if sampled:
                response.headers[self.config.header_name] = "true"

            return response
        finally:
            _sampled_ctx.reset(token)
