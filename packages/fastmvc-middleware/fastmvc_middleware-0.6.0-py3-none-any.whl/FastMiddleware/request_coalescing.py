"""
Request Coalescing Middleware for FastMVC.

Coalesces identical concurrent requests.
"""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Callable, Awaitable, Set, Dict, Any

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class CoalescingConfig:
    """
    Configuration for request coalescing middleware.
    
    Attributes:
        window: Coalescing window in seconds.
        max_coalesced: Max requests to coalesce.
    """
    window: float = 0.1
    max_coalesced: int = 100


class RequestCoalescingMiddleware(FastMVCMiddleware):
    """
    Middleware that coalesces identical requests.
    
    When multiple identical requests arrive within a short
    window, only one is processed and the result is shared.
    
    Example:
        ```python
        from FastMiddleware import RequestCoalescingMiddleware
        
        app.add_middleware(
            RequestCoalescingMiddleware,
            window=0.1,  # 100ms window
        )
        
        # Multiple /api/data requests within 100ms
        # will be coalesced into a single backend call
        ```
    """
    
    def __init__(
        self,
        app,
        config: CoalescingConfig | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CoalescingConfig()
        self._pending: Dict[str, tuple[asyncio.Event, Any]] = {}
        self._lock = asyncio.Lock()
    
    def _get_key(self, request: Request) -> str:
        """Generate coalescing key."""
        parts = [
            request.method,
            str(request.url),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        # Only coalesce GET/HEAD
        if request.method not in {"GET", "HEAD"}:
            return await call_next(request)
        
        key = self._get_key(request)
        
        async with self._lock:
            if key in self._pending:
                # Wait for existing request
                event, _ = self._pending[key]
        
        if key in self._pending:
            event, _ = self._pending[key]
            await event.wait()
            _, response = self._pending.get(key, (None, None))
            if response:
                return response
            return await call_next(request)
        
        # Create event for this request
        event = asyncio.Event()
        async with self._lock:
            self._pending[key] = (event, None)
        
        try:
            response = await call_next(request)
            
            async with self._lock:
                self._pending[key] = (event, response)
            
            event.set()
            
            # Cleanup after window
            await asyncio.sleep(self.config.window)
            async with self._lock:
                self._pending.pop(key, None)
            
            return response
        except Exception:
            event.set()
            async with self._lock:
                self._pending.pop(key, None)
            raise

