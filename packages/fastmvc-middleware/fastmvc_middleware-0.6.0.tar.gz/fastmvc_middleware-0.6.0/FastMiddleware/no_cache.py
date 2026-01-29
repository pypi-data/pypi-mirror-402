"""
No-Cache Middleware for FastMVC.

Disables caching for responses.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, List

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class NoCacheConfig:
    """
    Configuration for no-cache middleware.
    
    Attributes:
        paths: Paths to apply no-cache (empty = all).
        methods: Methods to apply no-cache.
        headers: Cache control headers to add.
    """
    paths: Set[str] = field(default_factory=set)
    methods: Set[str] = field(default_factory=lambda: {"GET", "HEAD"})
    pragma: bool = True
    expires: bool = True


class NoCacheMiddleware(FastMVCMiddleware):
    """
    Middleware that disables caching.
    
    Adds headers to prevent caching of responses,
    useful for dynamic content or sensitive data.
    
    Example:
        ```python
        from FastMiddleware import NoCacheMiddleware
        
        app.add_middleware(
            NoCacheMiddleware,
            paths={"/api/user", "/api/session"},
        )
        
        # Responses will have:
        # Cache-Control: no-store, no-cache, must-revalidate
        # Pragma: no-cache
        # Expires: 0
        ```
    """
    
    def __init__(
        self,
        app,
        config: NoCacheConfig | None = None,
        paths: Set[str] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or NoCacheConfig()
        
        if paths:
            self.config.paths = paths
    
    def _should_apply(self, path: str, method: str) -> bool:
        """Check if no-cache should apply."""
        if method not in self.config.methods:
            return False
        
        if not self.config.paths:
            return True
        
        for p in self.config.paths:
            if path.startswith(p):
                return True
        
        return False
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        if self._should_apply(request.url.path, request.method):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            
            if self.config.pragma:
                response.headers["Pragma"] = "no-cache"
            
            if self.config.expires:
                response.headers["Expires"] = "0"
        
        return response

