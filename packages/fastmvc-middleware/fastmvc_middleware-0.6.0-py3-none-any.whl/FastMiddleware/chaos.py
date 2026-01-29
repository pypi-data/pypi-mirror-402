"""
Chaos Engineering Middleware for FastMVC.

Injects faults for testing resilience.
"""

import random
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable, Set, List

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ChaosConfig:
    """
    Configuration for chaos middleware.
    
    Attributes:
        enabled: Enable chaos injection.
        failure_rate: Probability of failure (0-1).
        latency_rate: Probability of latency injection.
        min_latency: Minimum latency in seconds.
        max_latency: Maximum latency in seconds.
        error_codes: List of error codes to return.
        affected_paths: Only affect these paths (empty = all).
    """
    enabled: bool = False  # Must be explicitly enabled
    failure_rate: float = 0.1
    latency_rate: float = 0.2
    min_latency: float = 0.1
    max_latency: float = 5.0
    error_codes: List[int] = None
    affected_paths: Set[str] = None
    
    def __post_init__(self):
        if self.error_codes is None:
            self.error_codes = [500, 502, 503, 504]
        if self.affected_paths is None:
            self.affected_paths = set()


class ChaosMiddleware(FastMVCMiddleware):
    """
    Middleware for chaos engineering.
    
    Randomly injects failures and latency to test
    application resilience. NEVER enable in production!
    
    Example:
        ```python
        from FastMiddleware import ChaosMiddleware
        
        # Only enable in testing environments!
        app.add_middleware(
            ChaosMiddleware,
            enabled=os.getenv("CHAOS_ENABLED") == "true",
            failure_rate=0.1,  # 10% failure rate
            latency_rate=0.2,  # 20% latency injection
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: ChaosConfig | None = None,
        enabled: bool = False,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ChaosConfig()
        
        if enabled:
            self.config.enabled = True
    
    def _should_affect(self, path: str) -> bool:
        """Check if path should be affected by chaos."""
        if not self.config.affected_paths:
            return True
        return path in self.config.affected_paths or any(
            path.startswith(p) for p in self.config.affected_paths
        )
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self.config.enabled:
            return await call_next(request)
        
        if self.should_skip(request):
            return await call_next(request)
        
        if not self._should_affect(request.url.path):
            return await call_next(request)
        
        # Inject latency
        if random.random() < self.config.latency_rate:
            delay = random.uniform(self.config.min_latency, self.config.max_latency)
            await asyncio.sleep(delay)
        
        # Inject failure
        if random.random() < self.config.failure_rate:
            error_code = random.choice(self.config.error_codes)
            return JSONResponse(
                status_code=error_code,
                content={
                    "error": True,
                    "message": f"Chaos injection: {error_code}",
                    "chaos": True,
                },
            )
        
        return await call_next(request)

