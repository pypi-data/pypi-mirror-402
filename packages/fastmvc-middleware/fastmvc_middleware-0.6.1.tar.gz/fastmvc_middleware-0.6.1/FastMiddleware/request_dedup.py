"""
Request Deduplication Middleware for FastMVC.

Deduplicates identical concurrent requests.
"""

import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class RequestDedupConfig:
    """
    Configuration for request deduplication middleware.

    Attributes:
        window: Time window for deduplication in seconds.
        include_body: Include body in request hash.
        include_headers: Headers to include in hash.
    """

    window: float = 1.0
    include_body: bool = False
    include_headers: set[str] = None

    def __post_init__(self):
        if self.include_headers is None:
            self.include_headers = set()


class RequestDedupMiddleware(FastMVCMiddleware):
    """
    Middleware that deduplicates concurrent requests.

    If identical requests arrive within a time window,
    only one is processed and the response is shared.

    Example:
        ```python
        from FastMiddleware import RequestDedupMiddleware

        app.add_middleware(
            RequestDedupMiddleware,
            window=1.0,  # 1 second window
        )

        # Duplicate requests within 1 second share the same response
        ```
    """

    def __init__(
        self,
        app,
        config: RequestDedupConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestDedupConfig()
        self._pending: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def _get_request_hash(self, request: Request) -> str:
        """Generate unique hash for request."""
        parts = [
            request.method,
            str(request.url),
            self.get_client_ip(request),
        ]

        for header in self.config.include_headers:
            parts.append(request.headers.get(header, ""))

        if self.config.include_body and request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            parts.append(body.decode("utf-8", errors="ignore"))

        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Only dedupe safe methods by default
        if request.method not in {"GET", "HEAD"}:
            return await call_next(request)

        request_hash = await self._get_request_hash(request)

        async with self._lock:
            if request_hash in self._pending:
                # Wait for existing request
                future = self._pending[request_hash]
                try:
                    response_data = await asyncio.wait_for(
                        asyncio.shield(future),
                        timeout=30.0,
                    )
                    return response_data
                except asyncio.TimeoutError:
                    return await call_next(request)

            # Create future for this request
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending[request_hash] = future

        try:
            response = await call_next(request)

            # Resolve pending requests
            async with self._lock:
                if request_hash in self._pending:
                    self._pending[request_hash].set_result(response)
                    del self._pending[request_hash]

            return response
        except Exception as e:
            async with self._lock:
                if request_hash in self._pending:
                    self._pending[request_hash].set_exception(e)
                    del self._pending[request_hash]
            raise
