"""
Logging Middleware for FastMVC.

Provides structured request/response logging with configurable log levels and filters.
"""

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


logger = logging.getLogger("fastmvc.middleware")


class LoggingMiddleware(FastMVCMiddleware):
    """
    Middleware that logs incoming requests and outgoing responses.

    Features:
        - Configurable log levels
        - Request/response body logging (optional)
        - Path exclusion for health checks and metrics
        - Processing time tracking
        - Client IP logging

    Logs include:
        - Request method, path, and query parameters
        - Response status code
        - Request processing time
        - Client IP address

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import LoggingMiddleware
        import logging

        app = FastAPI()

        # Basic usage
        app.add_middleware(LoggingMiddleware)

        # With custom configuration
        app.add_middleware(
            LoggingMiddleware,
            log_level=logging.DEBUG,
            exclude_paths={"/health", "/metrics"},
            log_request_headers=True,
        )
        ```
    """

    # Default paths to exclude from logging
    DEFAULT_EXCLUDE_PATHS = {
        "/health",
        "/healthz",
        "/ready",
        "/readiness",
        "/metrics",
        "/favicon.ico",
    }

    def __init__(
        self,
        app,
        log_level: int = logging.INFO,
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_request_headers: bool = False,
        log_response_headers: bool = False,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
        custom_logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the logging middleware.

        Args:
            app: The ASGI application.
            log_level: The logging level to use.
            log_request_body: Whether to log request bodies.
            log_response_body: Whether to log response bodies.
            log_request_headers: Whether to log request headers.
            log_response_headers: Whether to log response headers.
            exclude_paths: Paths to exclude from logging.
            exclude_methods: HTTP methods to exclude from logging.
            custom_logger: Custom logger instance to use.
        """
        _exclude_paths = exclude_paths if exclude_paths is not None else self.DEFAULT_EXCLUDE_PATHS
        super().__init__(app, exclude_paths=_exclude_paths, exclude_methods=exclude_methods)

        self.log_level = log_level
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_request_headers = log_request_headers
        self.log_response_headers = log_response_headers
        self._logger = custom_logger or logger

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request, logging request and response details.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response.
        """
        # Skip logging for excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        # Get client IP
        client_ip = self.get_client_ip(request)

        # Get request ID if available
        request_id = getattr(request.state, "request_id", None)

        # Build log context
        log_context = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
        }

        if request_id:
            log_context["request_id"] = request_id

        if request.url.query:
            log_context["query"] = str(request.url.query)

        if self.log_request_headers:
            log_context["request_headers"] = dict(request.headers)

        # Log incoming request
        self._logger.log(
            self.log_level,
            f"→ {request.method} {request.url.path}",
            extra=log_context,
        )

        # Process request and measure time
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        # Build response log context
        log_context["status_code"] = response.status_code
        log_context["process_time_ms"] = round(process_time, 2)

        if self.log_response_headers:
            log_context["response_headers"] = dict(response.headers)

        # Log outgoing response
        status_emoji = "✓" if response.status_code < 400 else "✗"
        self._logger.log(
            self.log_level,
            f"← {status_emoji} {request.method} {request.url.path} [{response.status_code}] {process_time:.2f}ms",
            extra=log_context,
        )

        return response
