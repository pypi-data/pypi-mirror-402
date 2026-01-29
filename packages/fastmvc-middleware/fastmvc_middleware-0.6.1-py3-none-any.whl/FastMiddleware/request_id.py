"""
Request ID Middleware for FastMVC.

Generates and manages unique request identifiers for distributed tracing and logging.
"""

import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


class RequestIDMiddleware(FastMVCMiddleware):
    """
    Middleware that generates and attaches unique request IDs to requests and responses.

    This middleware is essential for distributed tracing and debugging. It generates
    a unique identifier for each request and:
    - Stores it in `request.state.request_id`
    - Adds it to the response headers
    - Respects existing request IDs from incoming headers (for distributed systems)

    Features:
        - UUID-based unique identifiers (configurable generator)
        - Header passthrough for distributed tracing
        - Configurable header names
        - Integration with logging middleware

    Example:
        ```python
        from fastapi import FastAPI, Request
        from FastMiddleware import RequestIDMiddleware

        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/")
        async def root(request: Request):
            # Access the request ID
            request_id = request.state.request_id
            return {"request_id": request_id}
        ```

    Response Headers:
        ```
        X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
        ```
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generator: Callable[[], str] | None = None,
        trust_incoming: bool = True,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the request ID middleware.

        Args:
            app: The ASGI application.
            header_name: Name of the request/response header for the ID.
            generator: Custom function to generate request IDs.
            trust_incoming: Whether to trust and reuse incoming request IDs.
            exclude_paths: Paths to exclude from request ID generation.
            exclude_methods: HTTP methods to exclude from request ID generation.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)
        self.header_name = header_name
        self.generator = generator or self._default_generator
        self.trust_incoming = trust_incoming

    @staticmethod
    def _default_generator() -> str:
        """Generate a UUID4 as the default request ID."""
        return str(uuid.uuid4())

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request, generating or forwarding a request ID.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response with request ID header.
        """
        # Check for existing request ID in headers
        request_id = None
        if self.trust_incoming:
            request_id = request.headers.get(self.header_name)

        # Generate new ID if not present
        if not request_id:
            request_id = self.generator()

        # Store in request state for access by route handlers
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.header_name] = request_id

        return response
