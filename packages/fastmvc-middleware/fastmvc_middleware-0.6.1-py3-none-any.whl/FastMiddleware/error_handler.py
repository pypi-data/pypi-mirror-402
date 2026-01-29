"""
Error Handling Middleware for FastMVC.

Provides consistent error response formatting and exception handling.
"""

import logging
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


logger = logging.getLogger("fastmvc.middleware.error")


@dataclass
class ErrorConfig:
    """
    Configuration for error handling middleware.

    Attributes:
        include_traceback: Include traceback in error responses (development).
        include_exception_type: Include exception class name in response.
        log_exceptions: Whether to log exceptions.
        log_level: Logging level for exceptions.
        default_message: Default error message for unhandled exceptions.
        error_handlers: Custom handlers for specific exception types.

    Example:
        ```python
        from FastMiddleware import ErrorConfig

        # Development config
        config = ErrorConfig(
            include_traceback=True,
            include_exception_type=True,
        )

        # Production config
        config = ErrorConfig(
            include_traceback=False,
            log_exceptions=True,
        )
        ```
    """

    include_traceback: bool = False
    include_exception_type: bool = False
    log_exceptions: bool = True
    log_level: int = logging.ERROR
    default_message: str = "An internal error occurred"
    status_code: int = 500

    # Custom error handlers: {ExceptionType: (status_code, message)}
    error_handlers: dict[type[Exception], tuple[int, str]] = field(default_factory=dict)


class ErrorHandlerMiddleware(FastMVCMiddleware):
    """
    Middleware that catches exceptions and returns consistent error responses.

    Provides a uniform error response format across your API, with configurable
    detail levels for development vs production environments.

    Features:
        - Consistent JSON error responses
        - Configurable traceback inclusion
        - Custom handlers for specific exceptions
        - Request ID inclusion (if available)
        - Exception logging

    Response Format:
        ```json
        {
            "error": true,
            "message": "Error description",
            "status_code": 500,
            "request_id": "abc-123",
            "type": "ValueError",
            "traceback": ["..."]
        }
        ```

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import ErrorHandlerMiddleware, ErrorConfig

        app = FastAPI()

        # Development mode
        app.add_middleware(
            ErrorHandlerMiddleware,
            include_traceback=True,
        )

        # Production mode
        app.add_middleware(
            ErrorHandlerMiddleware,
            include_traceback=False,
            log_exceptions=True,
        )

        # Custom error handlers
        config = ErrorConfig()
        config.error_handlers[ValueError] = (400, "Invalid value provided")
        config.error_handlers[PermissionError] = (403, "Permission denied")

        app.add_middleware(ErrorHandlerMiddleware, config=config)
        ```
    """

    def __init__(
        self,
        app,
        config: ErrorConfig | None = None,
        include_traceback: bool | None = None,
        include_exception_type: bool | None = None,
        log_exceptions: bool | None = None,
        default_message: str | None = None,
        custom_logger: logging.Logger | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the error handler middleware.

        Args:
            app: The ASGI application.
            config: Error handling configuration.
            include_traceback: Include traceback in responses (overrides config).
            include_exception_type: Include exception type (overrides config).
            log_exceptions: Log exceptions (overrides config).
            default_message: Default error message (overrides config).
            custom_logger: Custom logger instance.
            exclude_paths: Paths to exclude from error handling.
            exclude_methods: HTTP methods to exclude from error handling.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        self.config = config or ErrorConfig()
        self._logger = custom_logger or logger

        if include_traceback is not None:
            self.config.include_traceback = include_traceback
        if include_exception_type is not None:
            self.config.include_exception_type = include_exception_type
        if log_exceptions is not None:
            self.config.log_exceptions = log_exceptions
        if default_message is not None:
            self.config.default_message = default_message

    def _get_error_response(
        self,
        request: Request,
        exc: Exception,
    ) -> tuple[int, dict[str, Any]]:
        """Build error response data."""
        # Check for custom handler
        exc_type = type(exc)
        if exc_type in self.config.error_handlers:
            status_code, message = self.config.error_handlers[exc_type]
        else:
            status_code = self.config.status_code
            message = self.config.default_message

        # Build response body
        body: dict[str, Any] = {
            "error": True,
            "message": message,
            "status_code": status_code,
        }

        # Add request ID if available
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            body["request_id"] = request_id

        # Add exception type if configured
        if self.config.include_exception_type:
            body["type"] = exc_type.__name__
            body["detail"] = str(exc)

        # Add traceback if configured
        if self.config.include_traceback:
            body["traceback"] = traceback.format_exc().split("\n")

        return status_code, body

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and handle any exceptions.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response, or an error response if an exception occurred.
        """
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the exception
            if self.config.log_exceptions:
                request_id = getattr(request.state, "request_id", None)
                self._logger.log(
                    self.config.log_level,
                    f"Unhandled exception in {request.method} {request.url.path}",
                    exc_info=exc,
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "exception_type": type(exc).__name__,
                    },
                )

            # Build error response
            status_code, body = self._get_error_response(request, exc)

            return JSONResponse(
                content=body,
                status_code=status_code,
            )
