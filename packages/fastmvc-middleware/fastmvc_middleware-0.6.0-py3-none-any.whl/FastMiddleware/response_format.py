"""
Response Formatting Middleware for FastMVC.

Provides consistent response structure and content negotiation.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ResponseFormatConfig:
    """
    Configuration for response formatting middleware.
    
    Attributes:
        wrap_responses: Wrap all responses in a standard envelope.
        envelope_format: Format for response envelope.
        include_meta: Include metadata in responses.
        meta_fields: Fields to include in metadata.
    
    Example:
        ```python
        from FastMiddleware import ResponseFormatConfig
        
        config = ResponseFormatConfig(
            wrap_responses=True,
            envelope_format={
                "success": True,
                "data": None,  # Placeholder
                "meta": {},
            },
        )
        ```
    """
    
    wrap_responses: bool = False
    include_meta: bool = True
    add_request_id: bool = True
    add_timestamp: bool = True
    add_version: bool = False
    api_version: str = "v1"


class ResponseFormatMiddleware(FastMVCMiddleware):
    """
    Middleware that ensures consistent response formatting.
    
    Provides a standard envelope structure for all API responses
    and handles content negotiation.
    
    Features:
        - Standard response envelope
        - Automatic metadata injection
        - Request ID propagation
        - Timestamp addition
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import ResponseFormatMiddleware
        
        app = FastAPI()
        
        app.add_middleware(
            ResponseFormatMiddleware,
            wrap_responses=True,
        )
        
        # Response will be wrapped:
        # {
        #   "success": true,
        #   "data": { ... original response ... },
        #   "meta": {
        #     "request_id": "...",
        #     "timestamp": "..."
        #   }
        # }
        ```
    """
    
    def __init__(
        self,
        app,
        config: ResponseFormatConfig | None = None,
        wrap_responses: bool | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        """
        Initialize the response format middleware.
        
        Args:
            app: The ASGI application.
            config: Response format configuration.
            wrap_responses: Enable wrapping (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ResponseFormatConfig()
        
        if wrap_responses is not None:
            self.config.wrap_responses = wrap_responses
    
    def _build_meta(self, request: Request) -> Dict[str, Any]:
        """Build metadata for response."""
        import time
        
        meta = {}
        
        if self.config.add_request_id:
            request_id = getattr(request.state, "request_id", None)
            if request_id:
                meta["request_id"] = request_id
        
        if self.config.add_timestamp:
            meta["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        if self.config.add_version:
            meta["api_version"] = self.config.api_version
        
        return meta
    
    def _is_json_response(self, response: Response) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("Content-Type", "")
        return "application/json" in content_type
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and format response.
        
        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.
            
        Returns:
            The formatted response.
        """
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Only wrap JSON responses
        if not self.config.wrap_responses or not self._is_json_response(response):
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Try to parse JSON
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, return as-is
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Check if already wrapped
        if isinstance(data, dict) and "success" in data and "data" in data:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Wrap response
        is_success = 200 <= response.status_code < 400
        
        wrapped = {
            "success": is_success,
            "data": data,
        }
        
        if self.config.include_meta:
            wrapped["meta"] = self._build_meta(request)
        
        return JSONResponse(
            content=wrapped,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

