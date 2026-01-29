"""
Request Signing Middleware for FastMVC.

Validates HMAC signatures on incoming requests.
"""

import hmac
import hashlib
import time
from dataclasses import dataclass
from typing import Callable, Awaitable, Set, Dict

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class RequestSigningConfig:
    """
    Configuration for request signing middleware.
    
    Attributes:
        secret_key: Secret key for HMAC.
        signature_header: Header containing signature.
        timestamp_header: Header containing timestamp.
        algorithm: Hash algorithm (sha256, sha512).
        max_age: Maximum request age in seconds.
    """
    secret_key: str = ""
    signature_header: str = "X-Signature"
    timestamp_header: str = "X-Timestamp"
    algorithm: str = "sha256"
    max_age: int = 300


class RequestSigningMiddleware(FastMVCMiddleware):
    """
    Middleware that validates HMAC request signatures.
    
    Ensures requests are signed with a shared secret,
    preventing tampering and unauthorized access.
    
    Example:
        ```python
        from FastMiddleware import RequestSigningMiddleware
        
        app.add_middleware(
            RequestSigningMiddleware,
            secret_key="your-secret-key",
        )
        
        # Clients must sign: {timestamp}.{method}.{path}.{body}
        # signature = HMAC-SHA256(secret, payload)
        ```
    """
    
    ALGORITHMS = {
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "sha1": hashlib.sha1,
    }
    
    def __init__(
        self,
        app,
        config: RequestSigningConfig | None = None,
        secret_key: str | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestSigningConfig()
        
        if secret_key:
            self.config.secret_key = secret_key
        
        if not self.config.secret_key:
            raise ValueError("secret_key is required")
        
        if self.config.algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {self.config.algorithm}")
    
    def _compute_signature(self, payload: str) -> str:
        """Compute HMAC signature."""
        algo = self.ALGORITHMS[self.config.algorithm]
        signature = hmac.new(
            self.config.secret_key.encode(),
            payload.encode(),
            algo,
        ).hexdigest()
        return signature
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        # Skip for safe methods if desired
        signature = request.headers.get(self.config.signature_header)
        timestamp = request.headers.get(self.config.timestamp_header)
        
        if not signature:
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Missing signature"},
            )
        
        if not timestamp:
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Missing timestamp"},
            )
        
        # Validate timestamp
        try:
            ts = int(timestamp)
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Invalid timestamp"},
            )
        
        if abs(time.time() - ts) > self.config.max_age:
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Request expired"},
            )
        
        # Build payload for signature
        body = await request.body()
        body_str = body.decode("utf-8", errors="ignore")
        
        payload = f"{timestamp}.{request.method}.{request.url.path}.{body_str}"
        expected_sig = self._compute_signature(payload)
        
        if not hmac.compare_digest(signature, expected_sig):
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Invalid signature"},
            )
        
        return await call_next(request)

