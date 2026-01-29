"""
API Version Header Middleware for FastMVC.

Adds API version information to responses.
"""

from dataclasses import dataclass
from typing import Callable, Awaitable, Set

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class APIVersionHeaderConfig:
    """
    Configuration for API version header middleware.
    
    Attributes:
        version: Current API version.
        header_name: Header name for version.
        deprecated_header: Header for deprecation notice.
        min_version: Minimum supported version.
        sunset_date: API sunset date.
    """
    version: str = "1.0.0"
    header_name: str = "X-API-Version"
    deprecated_header: str = "X-API-Deprecated"
    min_version: str | None = None
    sunset_date: str | None = None


class APIVersionHeaderMiddleware(FastMVCMiddleware):
    """
    Middleware that adds API version headers.
    
    Adds version, deprecation, and sunset information
    to all API responses.
    
    Example:
        ```python
        from FastMiddleware import APIVersionHeaderMiddleware
        
        app.add_middleware(
            APIVersionHeaderMiddleware,
            version="2.1.0",
            min_version="1.5.0",
            sunset_date="2025-12-31",
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: APIVersionHeaderConfig | None = None,
        version: str | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or APIVersionHeaderConfig()
        
        if version:
            self.config.version = version
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Add version header
        response.headers[self.config.header_name] = self.config.version
        
        # Add min version if set
        if self.config.min_version:
            response.headers["X-API-Min-Version"] = self.config.min_version
        
        # Add sunset date if set
        if self.config.sunset_date:
            response.headers["Sunset"] = self.config.sunset_date
        
        return response

