"""
Middleware Factory for fastmiddleware.

Provides utilities for creating custom middleware with minimal boilerplate.
Includes duplicate detection to avoid wrapping the same middleware twice.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


if TYPE_CHECKING:
    from starlette.types import ASGIApp


# Type for middleware dispatch function
DispatchFunc = Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]

# Registry of added middleware to prevent duplicates
_middleware_registry: dict[int, set[str]] = {}

T = TypeVar("T")


def get_app_id(app: ASGIApp) -> int:
    """Get unique identifier for an app instance."""
    # Walk up to find the root app
    current = app
    while hasattr(current, "app"):
        current = current.app
    return id(current)


def is_middleware_registered(app: ASGIApp, middleware_name: str) -> bool:
    """Check if a middleware is already registered for this app."""
    app_id = get_app_id(app)
    return middleware_name in _middleware_registry.get(app_id, set())


def register_middleware(app: ASGIApp, middleware_name: str) -> None:
    """Register a middleware as added to this app."""
    app_id = get_app_id(app)
    if app_id not in _middleware_registry:
        _middleware_registry[app_id] = set()
    _middleware_registry[app_id].add(middleware_name)


def clear_registry(app: ASGIApp | None = None) -> None:
    """Clear the middleware registry. Useful for testing."""
    if app is None:
        _middleware_registry.clear()
    else:
        app_id = get_app_id(app)
        _middleware_registry.pop(app_id, None)


@dataclass
class MiddlewareConfig:
    """
    Base configuration for custom middleware.

    Attributes:
        exclude_paths: Paths to skip middleware processing.
        exclude_methods: HTTP methods to skip.
        enabled: Whether the middleware is enabled.
    """

    exclude_paths: set[str] = field(default_factory=set)
    exclude_methods: set[str] = field(default_factory=set)
    enabled: bool = True


def create_middleware(
    name: str,
    dispatch_func: DispatchFunc,
    *,
    skip_if_exists: bool = True,
    config_class: type | None = None,
) -> type[FastMVCMiddleware]:
    """
    Create a new middleware class from a dispatch function.

    This is the simplest way to create custom middleware without
    writing a full class.

    Args:
        name: Unique name for the middleware.
        dispatch_func: Async function that processes requests.
        skip_if_exists: If True, skip adding if already registered.
        config_class: Optional configuration dataclass.

    Returns:
        A new middleware class.

    Example:
        ```python
        from fastmiddleware.factory import create_middleware

        async def my_dispatch(request, call_next):
            # Add custom header
            response = await call_next(request)
            response.headers["X-Custom"] = "value"
            return response

        MyMiddleware = create_middleware("my_middleware", my_dispatch)

        app.add_middleware(MyMiddleware)
        ```
    """

    class CustomMiddleware(FastMVCMiddleware):
        __middleware_name__ = name
        __skip_if_exists__ = skip_if_exists

        def __init__(
            self,
            app: ASGIApp,
            config: Any | None = None,
            exclude_paths: set[str] | None = None,
            **kwargs: Any,
        ) -> None:
            # Check if already registered
            if self.__skip_if_exists__ and is_middleware_registered(app, self.__middleware_name__):
                # Create a passthrough - just wrap the app without processing
                self._passthrough = True
                self.app = app
            else:
                self._passthrough = False
                super().__init__(app, exclude_paths=exclude_paths)
                self.config = config or (config_class() if config_class else MiddlewareConfig())
                self._extra_kwargs = kwargs
                register_middleware(app, self.__middleware_name__)

        async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
            if getattr(self, "_passthrough", False):
                await self.app(scope, receive, send)
            else:
                await super().__call__(scope, receive, send)

        async def dispatch(
            self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            if hasattr(self, "config") and hasattr(self.config, "enabled"):
                if not self.config.enabled:
                    return await call_next(request)
            return await dispatch_func(request, call_next)

    CustomMiddleware.__name__ = f"{name.title().replace('_', '')}Middleware"
    CustomMiddleware.__qualname__ = CustomMiddleware.__name__

    return CustomMiddleware


def middleware(
    name: str | None = None,
    *,
    skip_if_exists: bool = True,
) -> Callable[[DispatchFunc], type[FastMVCMiddleware]]:
    """
    Decorator to create middleware from a function.

    Args:
        name: Middleware name (defaults to function name).
        skip_if_exists: Skip if already registered.

    Example:
        ```python
        from fastmiddleware.factory import middleware

        @middleware("request_timer")
        async def request_timer(request, call_next):
            import time
            start = time.time()
            response = await call_next(request)
            response.headers["X-Time"] = str(time.time() - start)
            return response

        app.add_middleware(request_timer)
        ```
    """

    def decorator(func: DispatchFunc) -> type[FastMVCMiddleware]:
        middleware_name = name or func.__name__
        return create_middleware(
            middleware_name,
            func,
            skip_if_exists=skip_if_exists,
        )

    return decorator


class MiddlewareBuilder:
    """
    Builder pattern for creating middleware with more options.

    Example:
        ```python
        from fastmiddleware.factory import MiddlewareBuilder

        MyMiddleware = (
            MiddlewareBuilder("my_middleware")
            .on_request(lambda req: req.state.start_time = time.time())
            .on_response(lambda req, res: res.headers.update({"X-Time": "..."}))
            .skip_paths({"/health", "/metrics"})
            .build()
        )

        app.add_middleware(MyMiddleware)
        ```
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._on_request: Callable[[Request], Awaitable[None] | None] | None = None
        self._on_response: Callable[[Request, Response], Awaitable[Response] | Response] | None = (
            None
        )
        self._on_error: Callable[[Request, Exception], Awaitable[Response] | Response] | None = None
        self._skip_paths: set[str] = set()
        self._skip_methods: set[str] = set()
        self._skip_if_exists: bool = True

    def on_request(self, handler: Callable[[Request], Awaitable[None] | None]) -> MiddlewareBuilder:
        """Add a request handler called before processing."""
        self._on_request = handler
        return self

    def on_response(
        self, handler: Callable[[Request, Response], Awaitable[Response] | Response]
    ) -> MiddlewareBuilder:
        """Add a response handler called after processing."""
        self._on_response = handler
        return self

    def on_error(
        self, handler: Callable[[Request, Exception], Awaitable[Response] | Response]
    ) -> MiddlewareBuilder:
        """Add an error handler for exceptions."""
        self._on_error = handler
        return self

    def skip_paths(self, paths: set[str]) -> MiddlewareBuilder:
        """Set paths to skip."""
        self._skip_paths = paths
        return self

    def skip_methods(self, methods: set[str]) -> MiddlewareBuilder:
        """Set methods to skip."""
        self._skip_methods = methods
        return self

    def allow_duplicates(self) -> MiddlewareBuilder:
        """Allow this middleware to be added multiple times."""
        self._skip_if_exists = False
        return self

    def build(self) -> type[FastMVCMiddleware]:
        """Build the middleware class."""
        on_request = self._on_request
        on_response = self._on_response
        on_error = self._on_error
        skip_paths = self._skip_paths

        async def dispatch(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            # Skip if path matches
            if request.url.path in skip_paths:
                return await call_next(request)

            # Call on_request handler
            if on_request:
                result = on_request(request)
                if hasattr(result, "__await__"):
                    await result

            try:
                response = await call_next(request)
            except Exception as e:
                if on_error:
                    result = on_error(request, e)
                    if hasattr(result, "__await__"):
                        return await result
                    return result
                raise

            # Call on_response handler
            if on_response:
                result = on_response(request, response)
                if hasattr(result, "__await__"):
                    response = await result
                else:
                    response = result

            return response

        return create_middleware(
            self.name,
            dispatch,
            skip_if_exists=self._skip_if_exists,
        )


def add_middleware_once(
    app: Any,
    middleware_class: type,
    *args: Any,
    **kwargs: Any,
) -> bool:
    """
    Add middleware to app only if not already added.

    Args:
        app: FastAPI or Starlette app.
        middleware_class: Middleware class to add.
        *args: Positional arguments for middleware.
        **kwargs: Keyword arguments for middleware.

    Returns:
        True if middleware was added, False if skipped.

    Example:
        ```python
        from fastmiddleware import CORSMiddleware
        from fastmiddleware.factory import add_middleware_once

        # First call adds the middleware
        added = add_middleware_once(app, CORSMiddleware, allow_origins=["*"])
        print(added)  # True

        # Second call skips (already added)
        added = add_middleware_once(app, CORSMiddleware, allow_origins=["*"])
        print(added)  # False
        ```
    """
    middleware_name = getattr(
        middleware_class,
        "__middleware_name__",
        middleware_class.__name__,
    )

    if is_middleware_registered(app, middleware_name):
        return False

    app.add_middleware(middleware_class, *args, **kwargs)
    register_middleware(app, middleware_name)
    return True


# Convenience function for quick middleware creation
def quick_middleware(
    before: Callable[[Request], Any] | None = None,
    after: Callable[[Request, Response], Response] | None = None,
    name: str = "quick_middleware",
) -> type[FastMVCMiddleware]:
    """
    Create a simple middleware with before/after hooks.

    Args:
        before: Called before request processing.
        after: Called after request processing, must return response.
        name: Middleware name.

    Example:
        ```python
        from fastmiddleware.factory import quick_middleware

        # Add timing header
        TimingMiddleware = quick_middleware(
            before=lambda req: setattr(req.state, 'start', time.time()),
            after=lambda req, res: (
                res.headers.__setitem__('X-Time', str(time.time() - req.state.start)),
                res
            )[1],
            name="timing"
        )

        app.add_middleware(TimingMiddleware)
        ```
    """

    async def dispatch(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if before:
            result = before(request)
            if hasattr(result, "__await__"):
                await result

        response = await call_next(request)

        if after:
            result = after(request, response)
            if hasattr(result, "__await__"):
                response = await result
            else:
                response = result

        return response

    return create_middleware(name, dispatch)
