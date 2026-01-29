"""
Quota Middleware for FastMVC.

Implements usage quotas for API resources.
"""

import asyncio
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class QuotaConfig:
    """
    Configuration for quota middleware.

    Attributes:
        default_quota: Default quota per period.
        quota_period: Period in seconds (day=86400).
        quotas: Per-path or per-user quotas.
        key_func: Function to extract quota key from request.
        header_name: Header showing remaining quota.
        reset_header: Header showing reset time.

    Example:
        ```python
        from fastmiddleware import QuotaConfig

        config = QuotaConfig(
            default_quota=1000,  # 1000 requests per day
            quota_period=86400,  # 24 hours
        )
        ```
    """

    default_quota: int = 1000
    quota_period: int = 86400  # 1 day
    quotas: dict[str, int] = field(default_factory=dict)  # key -> quota
    key_func: Callable[[Request], str] | None = None
    header_name: str = "X-Quota-Remaining"
    used_header: str = "X-Quota-Used"
    reset_header: str = "X-Quota-Reset"


class QuotaMiddleware(FastMVCMiddleware):
    """
    Middleware that enforces usage quotas.

    Tracks API usage and enforces limits based on quotas,
    useful for tiered API access.

    Features:
        - Per-user/key quotas
        - Configurable periods
        - Usage headers
        - Customizable key extraction

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import QuotaMiddleware, QuotaConfig

        app = FastAPI()

        config = QuotaConfig(
            default_quota=100,  # 100 requests per day
            quota_period=86400,
        )
        app.add_middleware(QuotaMiddleware, config=config)

        # Response headers show:
        # X-Quota-Remaining: 95
        # X-Quota-Used: 5
        # X-Quota-Reset: 1699999999
        ```
    """

    def __init__(
        self,
        app,
        config: QuotaConfig | None = None,
        default_quota: int | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or QuotaConfig()

        if default_quota is not None:
            self.config.default_quota = default_quota

        # Usage tracking: key -> (count, period_start)
        self._usage: dict[str, tuple[int, float]] = defaultdict(lambda: (0, time.time()))
        self._lock = asyncio.Lock()

    def _get_quota_key(self, request: Request) -> str:
        """Get quota key for request."""
        if self.config.key_func:
            return self.config.key_func(request)

        # Default: by client IP
        return self.get_client_ip(request)

    def _get_quota(self, key: str) -> int:
        """Get quota for key."""
        return self.config.quotas.get(key, self.config.default_quota)

    async def _check_quota(self, key: str) -> tuple[bool, int, int, int]:
        """Check and update quota.

        Returns:
            (allowed, remaining, used, reset_time)
        """
        async with self._lock:
            now = time.time()
            count, period_start = self._usage[key]

            # Check if period has reset
            if now - period_start >= self.config.quota_period:
                count = 0
                period_start = now

            quota = self._get_quota(key)
            reset_time = int(period_start + self.config.quota_period)

            if count >= quota:
                return False, 0, count, reset_time

            # Increment usage
            count += 1
            self._usage[key] = (count, period_start)

            remaining = quota - count
            return True, remaining, count, reset_time

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        key = self._get_quota_key(request)
        allowed, remaining, used, reset_time = await self._check_quota(key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Quota exceeded",
                    "quota": self._get_quota(key),
                    "reset_at": reset_time,
                },
                headers={
                    self.config.header_name: "0",
                    self.config.used_header: str(used),
                    self.config.reset_header: str(reset_time),
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )

        response = await call_next(request)

        # Add quota headers
        response.headers[self.config.header_name] = str(remaining)
        response.headers[self.config.used_header] = str(used)
        response.headers[self.config.reset_header] = str(reset_time)

        return response
