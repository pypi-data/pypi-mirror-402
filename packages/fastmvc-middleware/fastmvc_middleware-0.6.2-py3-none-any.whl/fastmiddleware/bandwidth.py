"""
Bandwidth Throttling Middleware for FastMVC.

Limits response bandwidth for clients.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class BandwidthConfig:
    """
    Configuration for bandwidth middleware.

    Attributes:
        bytes_per_second: Max bytes per second.
        chunk_size: Streaming chunk size.
        per_client: Apply limits per client.
    """

    bytes_per_second: int = 1024 * 1024  # 1 MB/s
    chunk_size: int = 8192
    per_client: bool = False


class BandwidthMiddleware(FastMVCMiddleware):
    """
    Middleware that throttles response bandwidth.

    Limits the rate at which responses are sent to clients,
    useful for fair resource allocation.

    Example:
        ```python
        from fastmiddleware import BandwidthMiddleware

        app.add_middleware(
            BandwidthMiddleware,
            bytes_per_second=512 * 1024,  # 512 KB/s
        )
        ```
    """

    def __init__(
        self,
        app,
        config: BandwidthConfig | None = None,
        bytes_per_second: int | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or BandwidthConfig()

        if bytes_per_second:
            self.config.bytes_per_second = bytes_per_second

        self._client_bytes: dict[str, dict] = {}

    async def _throttled_iterator(self, body: bytes, client_id: str) -> AsyncIterator[bytes]:
        """Yield body chunks with throttling."""
        chunk_size = self.config.chunk_size
        bytes_per_second = self.config.bytes_per_second
        chunk_delay = chunk_size / bytes_per_second

        for i in range(0, len(body), chunk_size):
            chunk = body[i : i + chunk_size]
            yield chunk
            await asyncio.sleep(chunk_delay)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        response = await call_next(request)

        # Get response body
        if hasattr(response, "body"):
            body = response.body
        else:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

        # Small responses don't need throttling
        if len(body) < self.config.chunk_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        client_id = self.get_client_ip(request)

        return StreamingResponse(
            self._throttled_iterator(body, client_id),
            status_code=response.status_code,
            headers=dict(response.headers),
        )
