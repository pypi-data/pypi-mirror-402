"""
Response Signing Middleware for FastMVC.

Signs responses for client verification.
"""

import hashlib
import hmac
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ResponseSignatureConfig:
    """
    Configuration for response signature middleware.

    Attributes:
        secret_key: Secret key for signing.
        signature_header: Header for signature.
        timestamp_header: Header for timestamp.
        algorithm: Hash algorithm.
        include_status: Include status in signature.
    """

    secret_key: str = ""
    signature_header: str = "X-Response-Signature"
    timestamp_header: str = "X-Response-Timestamp"
    algorithm: str = "sha256"
    include_status: bool = True


class ResponseSignatureMiddleware(FastMVCMiddleware):
    """
    Middleware that signs responses.

    Adds HMAC signature to responses so clients can
    verify response integrity.

    Example:
        ```python
        from FastMiddleware import ResponseSignatureMiddleware

        app.add_middleware(
            ResponseSignatureMiddleware,
            secret_key="your-shared-secret",
        )

        # Responses include:
        # X-Response-Signature: {hmac}
        # X-Response-Timestamp: {timestamp}
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
        config: ResponseSignatureConfig | None = None,
        secret_key: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ResponseSignatureConfig()

        if secret_key:
            self.config.secret_key = secret_key

        if not self.config.secret_key:
            raise ValueError("secret_key is required")

    def _compute_signature(self, payload: str) -> str:
        """Compute HMAC signature."""
        algo = self.ALGORITHMS.get(self.config.algorithm, hashlib.sha256)
        return hmac.new(
            self.config.secret_key.encode(),
            payload.encode(),
            algo,
        ).hexdigest()

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
            response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        timestamp = str(int(time.time()))

        # Build payload for signature
        parts = [timestamp, body.decode("utf-8", errors="ignore")]
        if self.config.include_status:
            parts.insert(0, str(response.status_code))

        payload = ".".join(parts)
        signature = self._compute_signature(payload)

        response.headers[self.config.timestamp_header] = timestamp
        response.headers[self.config.signature_header] = signature

        return response
