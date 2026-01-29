"""
ETag Middleware for FastMVC.

Automatic ETag generation and conditional request handling.
"""

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class ETagConfig:
    """
    Configuration for ETag middleware.

    Attributes:
        weak_etag: Generate weak ETags.
        hash_algorithm: Hash algorithm for ETag generation.
        cacheable_methods: Methods that get ETags.
        handle_if_match: Handle If-Match header (precondition).
        handle_if_none_match: Handle If-None-Match (caching).

    Example:
        ```python
        from fastmiddleware import ETagConfig

        config = ETagConfig(
            weak_etag=False,
            handle_if_none_match=True,
        )
        ```
    """

    weak_etag: bool = False
    hash_algorithm: str = "md5"
    cacheable_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD"})
    handle_if_match: bool = True
    handle_if_none_match: bool = True


class ETagMiddleware(FastMVCMiddleware):
    """
    Middleware that generates ETags and handles conditional requests.

    Automatically generates ETags for responses and handles
    If-None-Match/If-Match headers for caching and concurrency.

    Features:
        - Automatic ETag generation
        - 304 Not Modified responses
        - 412 Precondition Failed responses
        - Weak and strong ETags

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import ETagMiddleware

        app = FastAPI()

        app.add_middleware(ETagMiddleware)

        @app.get("/data")
        async def get_data():
            return {"value": 42}

        # Response includes: ETag: "abc123..."
        # If client sends: If-None-Match: "abc123..."
        # Returns: 304 Not Modified
        ```
    """

    def __init__(
        self,
        app,
        config: ETagConfig | None = None,
        weak_etag: bool | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ETagConfig()

        if weak_etag is not None:
            self.config.weak_etag = weak_etag

    def _generate_etag(self, body: bytes) -> str:
        """Generate ETag from response body."""
        if self.config.hash_algorithm == "md5":
            hash_value = hashlib.md5(body).hexdigest()
        elif self.config.hash_algorithm == "sha1":
            hash_value = hashlib.sha1(body).hexdigest()
        elif self.config.hash_algorithm == "sha256":
            hash_value = hashlib.sha256(body).hexdigest()
        else:
            hash_value = hashlib.md5(body).hexdigest()

        if self.config.weak_etag:
            return f'W/"{hash_value}"'
        return f'"{hash_value}"'

    def _etag_matches(self, etag: str, header_value: str) -> bool:
        """Check if ETag matches header value."""
        if header_value == "*":
            return True

        # Parse header value (comma-separated ETags)
        etags = [e.strip() for e in header_value.split(",")]

        for e in etags:
            # Handle weak comparison
            e_normalized = e.lstrip("W/")
            etag_normalized = etag.lstrip("W/")

            if e_normalized == etag_normalized:
                return True

        return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Only process cacheable methods
        if request.method not in self.config.cacheable_methods:
            return await call_next(request)

        # Get conditional headers
        if_none_match = request.headers.get("If-None-Match")
        if_match = request.headers.get("If-Match")

        response = await call_next(request)

        # Only process successful responses
        if not (200 <= response.status_code < 300):
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Generate ETag
        etag = self._generate_etag(body)

        # Handle If-None-Match (304 Not Modified)
        if self.config.handle_if_none_match and if_none_match:
            if self._etag_matches(etag, if_none_match):
                return Response(
                    status_code=304,
                    headers={"ETag": etag},
                )

        # Handle If-Match (412 Precondition Failed)
        if self.config.handle_if_match and if_match:
            if not self._etag_matches(etag, if_match):
                return Response(
                    status_code=412,
                    headers={"ETag": etag},
                )

        # Return response with ETag
        headers = dict(response.headers)
        headers["ETag"] = etag

        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
