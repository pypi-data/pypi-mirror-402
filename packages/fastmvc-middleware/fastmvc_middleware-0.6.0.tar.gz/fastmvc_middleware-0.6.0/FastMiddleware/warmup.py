"""
Warmup Middleware for FastMVC.

Handles warmup/readiness requests for container orchestration.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, List

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class WarmupConfig:
    """
    Configuration for warmup middleware.
    
    Attributes:
        warmup_paths: Paths that trigger warmup.
        warmup_header: Header to indicate warmup request.
        min_warmup_time: Minimum time app needs to be ready.
        warmup_callbacks: Functions to call during warmup.
    """
    warmup_paths: Set[str] = field(default_factory=lambda: {
        "/_warmup",
        "/_ah/warmup",  # App Engine
        "/warmup",
    })
    warmup_header: str = "X-Warmup"
    min_warmup_time: float = 0.0
    ready: bool = True


class WarmupMiddleware(FastMVCMiddleware):
    """
    Middleware for handling warmup requests.
    
    Used with container orchestration (Kubernetes, App Engine)
    to pre-warm instances before receiving traffic.
    
    Example:
        ```python
        from FastMiddleware import WarmupMiddleware
        
        warmup = WarmupMiddleware(
            app,
            min_warmup_time=5.0,  # 5 seconds warmup
        )
        
        # During warmup, app returns 503 for normal requests
        # /_warmup returns 200 when ready
        ```
    """
    
    def __init__(
        self,
        app,
        config: WarmupConfig | None = None,
        warmup_paths: Set[str] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or WarmupConfig()
        
        if warmup_paths:
            self.config.warmup_paths = warmup_paths
        
        self._start_time = time.time()
        self._warmed_up = False
    
    def _is_ready(self) -> bool:
        """Check if app is ready to serve traffic."""
        if not self.config.ready:
            return False
        
        if self.config.min_warmup_time > 0:
            elapsed = time.time() - self._start_time
            if elapsed < self.config.min_warmup_time:
                return False
        
        return True
    
    def set_ready(self, ready: bool = True) -> None:
        """Set readiness state."""
        self.config.ready = ready
        self._warmed_up = ready
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        is_warmup = (
            path in self.config.warmup_paths or
            request.headers.get(self.config.warmup_header) == "true"
        )
        
        if is_warmup:
            # Handle warmup request
            ready = self._is_ready()
            elapsed = time.time() - self._start_time
            
            return JSONResponse(
                status_code=200 if ready else 503,
                content={
                    "ready": ready,
                    "uptime": elapsed,
                    "warmup_time": self.config.min_warmup_time,
                },
            )
        
        # For normal requests, check readiness
        if not self._is_ready() and not self.should_skip(request):
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Service is warming up",
                },
                headers={"Retry-After": "5"},
            )
        
        return await call_next(request)

