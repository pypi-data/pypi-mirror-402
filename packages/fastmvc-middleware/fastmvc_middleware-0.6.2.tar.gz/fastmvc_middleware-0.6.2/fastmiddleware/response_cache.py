"""
In-Memory Response Cache Middleware for FastMVC.

Simple in-memory response caching.
"""

import hashlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class CacheEntry:
    """Cache entry."""

    body: bytes
    status_code: int
    headers: dict[str, str]
    created_at: float
    ttl: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl


@dataclass
class ResponseCacheConfig:
    """
    Configuration for response cache middleware.

    Attributes:
        default_ttl: Default TTL in seconds.
        max_size: Maximum cache entries.
        cache_methods: Methods to cache.
        cache_status_codes: Status codes to cache.
        path_ttls: Path-specific TTLs.
        vary_headers: Headers to include in cache key.
    """

    default_ttl: float = 60.0
    max_size: int = 1000
    cache_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD"})
    cache_status_codes: set[int] = field(default_factory=lambda: {200})
    path_ttls: dict[str, float] = field(default_factory=dict)
    vary_headers: list[str] = field(default_factory=lambda: ["Accept"])


class ResponseCacheMiddleware(FastMVCMiddleware):
    """
    Middleware for in-memory response caching.

    Caches responses for specified methods and status codes
    to reduce backend load.

    Example:
        ```python
        from fastmiddleware import ResponseCacheMiddleware

        app.add_middleware(
            ResponseCacheMiddleware,
            default_ttl=60,
            path_ttls={
                "/api/static": 3600,
                "/api/dynamic": 10,
            },
        )
        ```
    """

    def __init__(
        self,
        app,
        config: ResponseCacheConfig | None = None,
        default_ttl: float | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ResponseCacheConfig()

        if default_ttl:
            self.config.default_ttl = default_ttl

        self._cache: dict[str, CacheEntry] = {}

    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key."""
        parts = [
            request.method,
            str(request.url),
        ]

        for header in self.config.vary_headers:
            parts.append(request.headers.get(header, ""))

        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def _get_ttl(self, path: str) -> float:
        """Get TTL for path."""
        for pattern, ttl in self.config.path_ttls.items():
            if path.startswith(pattern):
                return ttl
        return self.config.default_ttl

    def _cleanup(self) -> None:
        """Remove expired entries and enforce size limit."""
        # Remove expired
        expired = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired:
            del self._cache[key]

        # Enforce size limit
        if len(self._cache) > self.config.max_size:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].created_at,
            )
            to_remove = len(self._cache) - self.config.max_size + 100
            for key, _ in sorted_entries[:to_remove]:
                del self._cache[key]

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()

    def invalidate(self, path: str) -> int:
        """Invalidate cache entries matching path."""
        to_remove = [k for k in self._cache if path in k]
        for key in to_remove:
            del self._cache[key]
        return len(to_remove)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Check if method is cacheable
        if request.method not in self.config.cache_methods:
            return await call_next(request)

        cache_key = self._get_cache_key(request)

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired:
                headers = dict(entry.headers)
                headers["X-Cache"] = "HIT"
                headers["Age"] = str(int(time.time() - entry.created_at))

                return Response(
                    content=entry.body,
                    status_code=entry.status_code,
                    headers=headers,
                )

        # Call backend
        response = await call_next(request)

        # Cache if appropriate
        if response.status_code in self.config.cache_status_codes:
            # Get response body
            if hasattr(response, "body"):
                body = response.body
            else:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # Store in cache
            ttl = self._get_ttl(request.url.path)
            self._cache[cache_key] = CacheEntry(
                body=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                created_at=time.time(),
                ttl=ttl,
            )

            self._cleanup()
            response.headers["X-Cache"] = "MISS"

        return response
