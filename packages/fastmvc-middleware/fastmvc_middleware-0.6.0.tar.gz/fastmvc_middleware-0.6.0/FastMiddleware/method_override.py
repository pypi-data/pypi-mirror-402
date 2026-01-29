"""
Method Override Middleware for FastMVC.

Allows HTTP method override via header or query param.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class MethodOverrideConfig:
    """
    Configuration for method override middleware.
    
    Attributes:
        header_name: Header to check for override.
        query_param: Query param to check.
        allowed_methods: Methods that can be overridden.
    """
    header_name: str = "X-HTTP-Method-Override"
    query_param: str = "_method"
    allowed_methods: Set[str] = field(default_factory=lambda: {
        "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"
    })


class MethodOverrideMiddleware(FastMVCMiddleware):
    """
    Middleware that allows HTTP method override.
    
    Useful for clients that can't send PUT/DELETE directly,
    such as older browsers or certain proxies.
    
    Example:
        ```python
        from FastMiddleware import MethodOverrideMiddleware
        
        app.add_middleware(MethodOverrideMiddleware)
        
        # POST /resource?_method=DELETE
        # or POST /resource with X-HTTP-Method-Override: DELETE
        # becomes DELETE /resource
        ```
    """
    
    def __init__(
        self,
        app,
        config: MethodOverrideConfig | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or MethodOverrideConfig()
    
    def _get_override(self, request: Request) -> str | None:
        """Get override method from request."""
        # Check header first
        override = request.headers.get(self.config.header_name)
        if override:
            return override.upper()
        
        # Check query param
        override = request.query_params.get(self.config.query_param)
        if override:
            return override.upper()
        
        return None
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        # Only allow override from POST
        if request.method != "POST":
            return await call_next(request)
        
        override = self._get_override(request)
        
        if override and override in self.config.allowed_methods:
            request.scope["method"] = override
            request.state.original_method = "POST"
        
        return await call_next(request)

