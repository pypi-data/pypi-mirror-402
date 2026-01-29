"""
Load Shedding Middleware for FastMVC.

Protects services under heavy load by rejecting excess requests.
"""

import time
import random
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set
from collections import deque
import asyncio

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class LoadSheddingConfig:
    """
    Configuration for load shedding middleware.
    
    Attributes:
        max_concurrent: Maximum concurrent requests.
        max_queue_size: Maximum queued requests.
        window_size: Time window for rate calculation (seconds).
        max_requests_per_window: Max requests per window.
        shed_probability: Probability of shedding when overloaded.
        priority_header: Header for request priority.
        high_priority_reserved: Reserved slots for high priority.
    
    Example:
        ```python
        from FastMiddleware import LoadSheddingConfig
        
        config = LoadSheddingConfig(
            max_concurrent=100,
            max_queue_size=50,
            shed_probability=0.5,
        )
        ```
    """
    
    max_concurrent: int = 100
    max_queue_size: int = 50
    window_size: float = 60.0
    max_requests_per_window: int = 1000
    shed_probability: float = 0.5
    priority_header: str = "X-Priority"
    high_priority_reserved: int = 10


class LoadSheddingMiddleware(FastMVCMiddleware):
    """
    Middleware that sheds load when service is overloaded.
    
    Protects the service from cascading failures by rejecting
    requests when capacity is exceeded.
    
    Features:
        - Concurrent request limiting
        - Request queue management
        - Priority-based admission
        - Probabilistic shedding
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import LoadSheddingMiddleware
        
        app = FastAPI()
        
        app.add_middleware(
            LoadSheddingMiddleware,
            max_concurrent=100,
            max_queue_size=50,
        )
        
        # Under heavy load, excess requests get 503
        # High-priority requests (X-Priority: high) get reserved slots
        ```
    
    Response (when shedding):
        ```json
        {
            "error": true,
            "message": "Service overloaded, please retry",
            "retry_after": 5
        }
        ```
    """
    
    def __init__(
        self,
        app,
        config: LoadSheddingConfig | None = None,
        max_concurrent: int | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or LoadSheddingConfig()
        
        if max_concurrent is not None:
            self.config.max_concurrent = max_concurrent
        
        self._current_requests = 0
        self._queued_requests = 0
        self._request_times: deque = deque()
        self._lock = asyncio.Lock()
    
    def _is_high_priority(self, request: Request) -> bool:
        """Check if request is high priority."""
        priority = request.headers.get(self.config.priority_header, "").lower()
        return priority in ("high", "critical", "1")
    
    def _should_shed(self) -> bool:
        """Determine if request should be shed."""
        # Simple probabilistic shedding
        return random.random() < self.config.shed_probability
    
    def _clean_old_requests(self) -> None:
        """Remove old request timestamps."""
        now = time.time()
        cutoff = now - self.config.window_size
        
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()
    
    async def _acquire(self, is_high_priority: bool) -> bool:
        """Try to acquire a request slot."""
        async with self._lock:
            self._clean_old_requests()
            
            # Check rate limit
            if len(self._request_times) >= self.config.max_requests_per_window:
                if not is_high_priority:
                    return False
            
            # Check concurrent limit
            max_allowed = self.config.max_concurrent
            if is_high_priority:
                max_allowed = self.config.max_concurrent
            else:
                max_allowed = self.config.max_concurrent - self.config.high_priority_reserved
            
            if self._current_requests >= max_allowed:
                # Check if we should probabilistically shed
                if self._should_shed():
                    return False
                
                # Check queue
                if self._queued_requests >= self.config.max_queue_size:
                    return False
            
            self._current_requests += 1
            self._request_times.append(time.time())
            return True
    
    async def _release(self) -> None:
        """Release a request slot."""
        async with self._lock:
            self._current_requests = max(0, self._current_requests - 1)
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        is_high_priority = self._is_high_priority(request)
        
        # Try to acquire slot
        if not await self._acquire(is_high_priority):
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Service overloaded, please retry",
                    "retry_after": 5,
                },
                headers={
                    "Retry-After": "5",
                    "X-Load-Shedding": "true",
                },
            )
        
        try:
            response = await call_next(request)
            return response
        finally:
            await self._release()

