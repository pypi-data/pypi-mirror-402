"""
Replay Attack Prevention Middleware for FastMVC.

Prevents replay attacks using timestamps and nonces.
"""

import time
import hashlib
from dataclasses import dataclass
from typing import Callable, Awaitable, Set, Dict

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ReplayPreventionConfig:
    """
    Configuration for replay prevention middleware.
    
    Attributes:
        timestamp_header: Header containing request timestamp.
        nonce_header: Header containing unique nonce.
        max_age: Maximum age of request in seconds.
        nonce_cache_size: Max number of nonces to cache.
    """
    timestamp_header: str = "X-Timestamp"
    nonce_header: str = "X-Nonce"
    max_age: int = 300  # 5 minutes
    nonce_cache_size: int = 10000


class ReplayPreventionMiddleware(FastMVCMiddleware):
    """
    Middleware that prevents replay attacks.
    
    Validates request timestamps and tracks nonces to prevent
    request replays.
    
    Example:
        ```python
        from FastMiddleware import ReplayPreventionMiddleware
        
        app.add_middleware(
            ReplayPreventionMiddleware,
            max_age=300,  # 5 minutes
        )
        
        # Clients must include:
        # X-Timestamp: 1704067200 (Unix timestamp)
        # X-Nonce: unique-random-string
        ```
    """
    
    def __init__(
        self,
        app,
        config: ReplayPreventionConfig | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ReplayPreventionConfig()
        self._used_nonces: Dict[str, float] = {}
    
    def _cleanup_nonces(self) -> None:
        """Remove expired nonces."""
        now = time.time()
        cutoff = now - self.config.max_age
        
        expired = [n for n, t in self._used_nonces.items() if t < cutoff]
        for n in expired:
            del self._used_nonces[n]
        
        # Limit cache size
        if len(self._used_nonces) > self.config.nonce_cache_size:
            sorted_nonces = sorted(self._used_nonces.items(), key=lambda x: x[1])
            to_remove = sorted_nonces[:len(sorted_nonces) - self.config.nonce_cache_size // 2]
            for n, _ in to_remove:
                del self._used_nonces[n]
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        # Only check for mutating methods
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)
        
        timestamp_str = request.headers.get(self.config.timestamp_header)
        nonce = request.headers.get(self.config.nonce_header)
        
        if not timestamp_str or not nonce:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": f"Missing required headers: {self.config.timestamp_header}, {self.config.nonce_header}",
                },
            )
        
        # Validate timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Invalid timestamp format"},
            )
        
        now = time.time()
        if abs(now - timestamp) > self.config.max_age:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Request timestamp expired or in future"},
            )
        
        # Create unique key from nonce + timestamp
        nonce_key = hashlib.sha256(f"{nonce}:{timestamp}".encode()).hexdigest()
        
        # Check for replay
        if nonce_key in self._used_nonces:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Replay detected: nonce already used"},
            )
        
        # Store nonce
        self._used_nonces[nonce_key] = now
        self._cleanup_nonces()
        
        return await call_next(request)

