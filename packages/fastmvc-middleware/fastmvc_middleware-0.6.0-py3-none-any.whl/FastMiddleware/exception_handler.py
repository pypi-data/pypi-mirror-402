"""
Exception Handler Middleware for FastMVC.

Catches and handles uncaught exceptions.
"""

import traceback
import logging
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any, Type

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ExceptionHandlerConfig:
    """
    Configuration for exception handler middleware.
    
    Attributes:
        debug: Include traceback in response.
        log_exceptions: Log exceptions.
        default_status: Default error status code.
        custom_handlers: Exception type to handler mapping.
    """
    debug: bool = False
    log_exceptions: bool = True
    default_status: int = 500
    logger_name: str = "exceptions"


class ExceptionHandlerMiddleware(FastMVCMiddleware):
    """
    Middleware that handles uncaught exceptions.
    
    Catches all exceptions and returns appropriate
    error responses.
    
    Example:
        ```python
        from FastMiddleware import ExceptionHandlerMiddleware
        
        handler = ExceptionHandlerMiddleware(
            app,
            debug=os.getenv("DEBUG") == "true",
        )
        
        @handler.register(ValueError)
        def handle_value_error(exc):
            return JSONResponse(
                status_code=400,
                content={"error": str(exc)},
            )
        ```
    """
    
    def __init__(
        self,
        app,
        config: ExceptionHandlerConfig | None = None,
        debug: bool = False,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ExceptionHandlerConfig()
        
        if debug:
            self.config.debug = True
        
        self._logger = logging.getLogger(self.config.logger_name)
        self._handlers: Dict[Type[Exception], Callable] = {}
    
    def register(self, exc_type: Type[Exception]):
        """Decorator to register exception handler."""
        def decorator(func):
            self._handlers[exc_type] = func
            return func
        return decorator
    
    def _find_handler(self, exc: Exception) -> Callable | None:
        """Find handler for exception type."""
        for exc_type, handler in self._handlers.items():
            if isinstance(exc, exc_type):
                return handler
        return None
    
    def _build_error_response(self, exc: Exception, request: Request) -> JSONResponse:
        """Build error response."""
        content: Dict[str, Any] = {
            "error": True,
            "message": str(exc) if self.config.debug else "Internal server error",
            "type": type(exc).__name__,
        }
        
        if self.config.debug:
            content["traceback"] = traceback.format_exc()
            content["path"] = request.url.path
            content["method"] = request.method
        
        return JSONResponse(
            status_code=self.config.default_status,
            content=content,
        )
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # Log exception
            if self.config.log_exceptions:
                self._logger.exception(
                    f"Unhandled exception: {type(exc).__name__}: {exc}"
                )
            
            # Try custom handler
            handler = self._find_handler(exc)
            if handler:
                return handler(exc)
            
            # Default response
            return self._build_error_response(exc, request)

