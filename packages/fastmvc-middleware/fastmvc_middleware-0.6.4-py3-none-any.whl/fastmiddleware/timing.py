"""
Timing Middleware for FastMVC.

Adds request processing time to response headers for performance monitoring.
"""

import time
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


class TimingMiddleware(FastMVCMiddleware):
    """
    Middleware that adds request processing time to response headers.

    Adds a configurable header (default: `X-Process-Time`) to all responses
    with the time taken to process the request.

    Features:
        - Configurable header name
        - Optional unit suffix (ms)
        - High-precision timing using perf_counter
        - Path exclusion support

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import TimingMiddleware

        app = FastAPI()

        # Basic usage - adds X-Process-Time header
        app.add_middleware(TimingMiddleware)

        # Custom header name without unit
        app.add_middleware(
            TimingMiddleware,
            header_name="X-Response-Time",
            include_unit=False,
        )
        ```

    Response Header:
        ```
        X-Process-Time: 12.34ms
        ```
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Process-Time",
        include_unit: bool = True,
        precision: int = 2,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the timing middleware.

        Args:
            app: The ASGI application.
            header_name: Name of the response header to add.
            include_unit: Whether to include "ms" suffix in the value.
            precision: Number of decimal places for the time value.
            exclude_paths: Paths to exclude from timing headers.
            exclude_methods: HTTP methods to exclude from timing headers.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)
        self.header_name = header_name
        self.include_unit = include_unit
        self.precision = precision

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and add timing header to response.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response with timing header.
        """
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        # Format the timing value
        time_value = f"{process_time:.{self.precision}f}"
        if self.include_unit:
            time_value = f"{time_value}ms"

        response.headers[self.header_name] = time_value

        return response
