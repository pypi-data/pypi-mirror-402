"""
Payload Size Middleware for FastMVC.

Limits request and response payload sizes.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class PayloadSizeConfig:
    """
    Configuration for payload size middleware.

    Attributes:
        max_request_size: Max request body size in bytes.
        max_response_size: Max response size in bytes.
        check_content_length: Check Content-Length header.
        add_header: Add size header to response.
    """

    max_request_size: int = 10 * 1024 * 1024  # 10 MB
    max_response_size: int | None = None  # None = no limit
    check_content_length: bool = True
    add_header: bool = True


class PayloadSizeMiddleware(FastMVCMiddleware):
    """
    Middleware that limits payload sizes.

    Enforces maximum request body size and optionally
    limits response sizes.

    Example:
        ```python
        from FastMiddleware import PayloadSizeMiddleware

        app.add_middleware(
            PayloadSizeMiddleware,
            max_request_size=5 * 1024 * 1024,  # 5 MB
        )
        ```
    """

    def __init__(
        self,
        app,
        config: PayloadSizeConfig | None = None,
        max_request_size: int | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or PayloadSizeConfig()

        if max_request_size:
            self.config.max_request_size = max_request_size

    def _format_size(self, size: int) -> str:
        """Format size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size:.1f} TB"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Check request size via Content-Length
        if self.config.check_content_length:
            content_length = request.headers.get("Content-Length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.config.max_request_size:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": True,
                                "message": "Request payload too large",
                                "max_size": self._format_size(self.config.max_request_size),
                                "received_size": self._format_size(size),
                            },
                        )
                except ValueError:
                    pass

        response = await call_next(request)

        # Check response size
        if self.config.max_response_size:
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.config.max_response_size:
                        return JSONResponse(
                            status_code=500,
                            content={
                                "error": True,
                                "message": "Response too large",
                            },
                        )
                except ValueError:
                    pass

        if self.config.add_header:
            response.headers["X-Max-Request-Size"] = self._format_size(self.config.max_request_size)

        return response
