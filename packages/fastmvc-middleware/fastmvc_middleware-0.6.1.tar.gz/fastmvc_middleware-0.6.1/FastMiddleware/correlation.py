"""
Correlation ID Middleware for FastMVC.

Provides distributed tracing support with correlation IDs.
"""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


# Context variable for correlation ID
_correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """
    Get the current correlation ID.

    Returns:
        The correlation ID or None if not set.

    Example:
        ```python
        from FastMiddleware import get_correlation_id

        @app.get("/")
        async def root():
            correlation_id = get_correlation_id()
            logger.info(f"Processing request", extra={"correlation_id": correlation_id})
        ```
    """
    return _correlation_id_ctx.get()


@dataclass
class CorrelationConfig:
    """
    Configuration for correlation ID middleware.

    Attributes:
        header_name: Header name for correlation ID.
        response_header: Whether to include in response headers.
        generate_if_missing: Generate ID if not in request.
        validate_format: Validate UUID format.
        id_generator: Custom ID generator function.

    Example:
        ```python
        from FastMiddleware import CorrelationConfig

        config = CorrelationConfig(
            header_name="X-Correlation-ID",
            response_header=True,
        )
        ```
    """

    header_name: str = "X-Correlation-ID"
    response_header: bool = True
    generate_if_missing: bool = True
    validate_format: bool = False
    id_generator: Callable[[], str] | None = None


class CorrelationMiddleware(FastMVCMiddleware):
    """
    Middleware that manages correlation IDs for distributed tracing.

    Correlation IDs help track requests across multiple services
    in a microservices architecture.

    Features:
        - Extract or generate correlation ID
        - Store in context variable
        - Include in response headers
        - Optional UUID validation

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import CorrelationMiddleware, get_correlation_id

        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/")
        async def root():
            # Access correlation ID anywhere
            corr_id = get_correlation_id()

            # Pass to downstream services
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://other-service/api",
                    headers={"X-Correlation-ID": corr_id}
                )
        ```

    Logging Integration:
        ```python
        import logging
        from FastMiddleware import get_correlation_id

        class CorrelationFilter(logging.Filter):
            def filter(self, record):
                record.correlation_id = get_correlation_id() or "-"
                return True

        handler.addFilter(CorrelationFilter())
        formatter = logging.Formatter(
            '%(asctime)s [%(correlation_id)s] %(message)s'
        )
        ```
    """

    def __init__(
        self,
        app,
        config: CorrelationConfig | None = None,
        header_name: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the correlation middleware.

        Args:
            app: The ASGI application.
            config: Correlation configuration.
            header_name: Header name (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CorrelationConfig()

        if header_name is not None:
            self.config.header_name = header_name

    def _generate_id(self) -> str:
        """Generate a new correlation ID."""
        if self.config.id_generator:
            return self.config.id_generator()
        return str(uuid.uuid4())

    def _validate_id(self, correlation_id: str) -> bool:
        """Validate correlation ID format."""
        if not self.config.validate_format:
            return True

        try:
            uuid.UUID(correlation_id)
            return True
        except ValueError:
            return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with correlation ID management.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with correlation ID.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Get or generate correlation ID
        correlation_id = request.headers.get(self.config.header_name)

        if correlation_id:
            if self.config.validate_format and not self._validate_id(correlation_id):
                correlation_id = None

        if not correlation_id and self.config.generate_if_missing:
            correlation_id = self._generate_id()

        # Set context variable
        token = _correlation_id_ctx.set(correlation_id)

        # Store in request state
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)

            # Add to response headers
            if self.config.response_header and correlation_id:
                response.headers[self.config.header_name] = correlation_id

            return response
        finally:
            _correlation_id_ctx.reset(token)
