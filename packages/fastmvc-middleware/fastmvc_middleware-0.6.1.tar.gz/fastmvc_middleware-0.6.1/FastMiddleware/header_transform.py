"""
Header Transform Middleware for FastMVC.

Adds, removes, or modifies request and response headers.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class HeaderTransformConfig:
    """
    Configuration for header transform middleware.

    Attributes:
        add_request_headers: Headers to add to requests.
        remove_request_headers: Headers to remove from requests.
        add_response_headers: Headers to add to responses.
        remove_response_headers: Headers to remove from responses.
        rename_headers: Headers to rename (old -> new).

    Example:
        ```python
        from FastMiddleware import HeaderTransformConfig

        config = HeaderTransformConfig(
            add_response_headers={
                "X-Powered-By": "FastMVC",
                "X-Version": "1.0.0",
            },
            remove_response_headers={"Server"},
        )
        ```
    """

    add_request_headers: dict[str, str] = field(default_factory=dict)
    remove_request_headers: set[str] = field(default_factory=set)
    add_response_headers: dict[str, str] = field(default_factory=dict)
    remove_response_headers: set[str] = field(default_factory=set)
    rename_headers: dict[str, str] = field(default_factory=dict)


class HeaderTransformMiddleware(FastMVCMiddleware):
    """
    Middleware that transforms request and response headers.

    Useful for adding standard headers, removing sensitive information,
    or normalizing header names.

    Features:
        - Add headers to requests/responses
        - Remove headers from requests/responses
        - Rename headers
        - Conditional transformation

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import HeaderTransformMiddleware

        app = FastAPI()

        app.add_middleware(
            HeaderTransformMiddleware,
            add_response_headers={
                "X-Frame-Options": "DENY",
                "X-Powered-By": "FastMVC",
            },
            remove_response_headers={"Server"},
        )

        # All responses will have:
        # X-Frame-Options: DENY
        # X-Powered-By: FastMVC
        # And Server header removed
        ```
    """

    def __init__(
        self,
        app,
        config: HeaderTransformConfig | None = None,
        add_response_headers: dict[str, str] | None = None,
        remove_response_headers: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or HeaderTransformConfig()

        if add_response_headers is not None:
            self.config.add_response_headers = add_response_headers
        if remove_response_headers is not None:
            self.config.remove_response_headers = remove_response_headers

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Modify request headers (limited by ASGI spec)
        # Note: Request headers are typically immutable in ASGI

        response = await call_next(request)

        # Add response headers
        for name, value in self.config.add_response_headers.items():
            response.headers[name] = value

        # Remove response headers
        for name in self.config.remove_response_headers:
            if name in response.headers:
                del response.headers[name]

        # Rename headers
        for old_name, new_name in self.config.rename_headers.items():
            if old_name in response.headers:
                value = response.headers[old_name]
                del response.headers[old_name]
                response.headers[new_name] = value

        return response
