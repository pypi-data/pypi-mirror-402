"""
Compression Middleware for FastMVC.

Provides GZip and Brotli compression for HTTP responses.
"""

import gzip
import io
from dataclasses import dataclass
from typing import Callable, Awaitable, Set, Sequence

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.datastructures import MutableHeaders

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class CompressionConfig:
    """
    Configuration for compression middleware.
    
    Attributes:
        minimum_size: Minimum response size (bytes) to compress.
        compression_level: GZip compression level (1-9, 9 = best).
        compressible_types: Content types that should be compressed.
    
    Example:
        ```python
        from FastMiddleware import CompressionConfig
        
        config = CompressionConfig(
            minimum_size=500,
            compression_level=6,
        )
        ```
    """
    
    minimum_size: int = 500
    compression_level: int = 6
    compressible_types: tuple[str, ...] = (
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
        "text/javascript",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/xhtml+xml",
        "image/svg+xml",
    )


class CompressionMiddleware(FastMVCMiddleware):
    """
    Middleware that compresses HTTP responses using GZip.
    
    Automatically compresses responses for clients that support compression,
    reducing bandwidth usage and improving load times.
    
    Features:
        - GZip compression
        - Configurable minimum size threshold
        - Content-type based filtering
        - Respects Accept-Encoding header
        - Configurable compression level
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import CompressionMiddleware, CompressionConfig
        
        app = FastAPI()
        
        # Basic usage
        app.add_middleware(CompressionMiddleware)
        
        # Custom configuration
        config = CompressionConfig(
            minimum_size=1000,
            compression_level=9,
        )
        app.add_middleware(CompressionMiddleware, config=config)
        ```
    
    Response Headers:
        - Content-Encoding: gzip
        - Vary: Accept-Encoding
    """
    
    def __init__(
        self,
        app,
        config: CompressionConfig | None = None,
        minimum_size: int | None = None,
        compression_level: int | None = None,
        exclude_paths: Set[str] | None = None,
        exclude_methods: Set[str] | None = None,
    ) -> None:
        """
        Initialize the compression middleware.
        
        Args:
            app: The ASGI application.
            config: Compression configuration.
            minimum_size: Minimum response size to compress (overrides config).
            compression_level: GZip compression level 1-9 (overrides config).
            exclude_paths: Paths to exclude from compression.
            exclude_methods: HTTP methods to exclude from compression.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)
        
        self.config = config or CompressionConfig()
        
        if minimum_size is not None:
            self.config.minimum_size = minimum_size
        if compression_level is not None:
            self.config.compression_level = compression_level
    
    def _accepts_gzip(self, request: Request) -> bool:
        """Check if client accepts gzip encoding."""
        accept_encoding = request.headers.get("Accept-Encoding", "")
        return "gzip" in accept_encoding.lower()
    
    def _should_compress(self, response: Response, body: bytes) -> bool:
        """Determine if response should be compressed."""
        # Check size threshold
        if len(body) < self.config.minimum_size:
            return False
        
        # Check if already compressed
        if response.headers.get("Content-Encoding"):
            return False
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        base_type = content_type.split(";")[0].strip()
        
        return base_type in self.config.compressible_types
    
    def _compress(self, body: bytes) -> bytes:
        """Compress data using gzip."""
        buffer = io.BytesIO()
        with gzip.GzipFile(
            mode="wb",
            fileobj=buffer,
            compresslevel=self.config.compression_level
        ) as gz:
            gz.write(body)
        return buffer.getvalue()
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and compress response if appropriate.
        
        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.
            
        Returns:
            The HTTP response, possibly compressed.
        """
        # Skip if client doesn't accept gzip
        if not self._accepts_gzip(request):
            return await call_next(request)
        
        # Skip excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Add Vary header for caching
        response.headers["Vary"] = "Accept-Encoding"
        
        # Handle streaming responses differently
        if isinstance(response, StreamingResponse):
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Check if we should compress
        if not self._should_compress(response, body):
            # Return original response with body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Compress the body
        compressed = self._compress(body)
        
        # Only use compression if it actually reduces size
        if len(compressed) >= len(body):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Return compressed response
        headers = MutableHeaders(raw=list(response.headers.raw))
        headers["Content-Encoding"] = "gzip"
        headers["Content-Length"] = str(len(compressed))
        
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=dict(headers),
            media_type=response.media_type,
        )

