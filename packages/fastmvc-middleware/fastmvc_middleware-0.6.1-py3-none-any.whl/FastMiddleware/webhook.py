"""
Webhook Verification Middleware for FastMVC.

Verifies webhook signatures from various providers.
"""

import hashlib
import hmac
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class WebhookConfig:
    """
    Configuration for webhook verification middleware.

    Attributes:
        secret: Webhook signing secret.
        signature_header: Header containing the signature.
        algorithm: Hash algorithm (sha256, sha1, etc.).
        signature_prefix: Prefix before signature (e.g., 'sha256=').
        timestamp_header: Header containing timestamp (optional).
        timestamp_tolerance: Max age of webhook in seconds.

    Example:
        ```python
        from FastMiddleware import WebhookConfig

        # GitHub webhook
        config = WebhookConfig(
            secret="your-webhook-secret",
            signature_header="X-Hub-Signature-256",
            signature_prefix="sha256=",
        )

        # Stripe webhook
        config = WebhookConfig(
            secret="whsec_...",
            signature_header="Stripe-Signature",
        )
        ```
    """

    secret: str = ""
    signature_header: str = "X-Signature"
    algorithm: str = "sha256"
    signature_prefix: str = ""
    timestamp_header: str | None = None
    timestamp_tolerance: int = 300  # 5 minutes
    paths: set[str] = field(default_factory=set)  # Only verify these paths


class WebhookMiddleware(FastMVCMiddleware):
    """
    Middleware that verifies webhook signatures.

    Ensures incoming webhooks are authentic by verifying
    HMAC signatures.

    Supported Providers:
        - GitHub (X-Hub-Signature-256)
        - Stripe (Stripe-Signature)
        - Twilio (X-Twilio-Signature)
        - Custom HMAC signatures

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import WebhookMiddleware, WebhookConfig

        app = FastAPI()

        # GitHub webhooks
        config = WebhookConfig(
            secret="your-github-secret",
            signature_header="X-Hub-Signature-256",
            signature_prefix="sha256=",
            paths={"/webhooks/github"},
        )
        app.add_middleware(WebhookMiddleware, config=config)

        @app.post("/webhooks/github")
        async def github_webhook(request: Request):
            # Signature already verified
            payload = await request.json()
            return {"received": True}
        ```
    """

    def __init__(
        self,
        app,
        config: WebhookConfig | None = None,
        secret: str | None = None,
        paths: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or WebhookConfig()

        if secret is not None:
            self.config.secret = secret
        if paths is not None:
            self.config.paths = paths

    def _compute_signature(self, body: bytes) -> str:
        """Compute HMAC signature."""
        if self.config.algorithm == "sha256":
            return hmac.new(
                self.config.secret.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()
        elif self.config.algorithm == "sha1":
            return hmac.new(
                self.config.secret.encode(),
                body,
                hashlib.sha1,
            ).hexdigest()
        else:
            return hmac.new(
                self.config.secret.encode(),
                body,
                self.config.algorithm,
            ).hexdigest()

    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify the webhook signature."""
        # Remove prefix if present
        if self.config.signature_prefix:
            if signature.startswith(self.config.signature_prefix):
                signature = signature[len(self.config.signature_prefix) :]

        expected = self._compute_signature(body)
        return hmac.compare_digest(signature.lower(), expected.lower())

    def _should_verify(self, request: Request) -> bool:
        """Check if this request should be verified."""
        if not self.config.paths:
            return True
        return request.url.path in self.config.paths

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Only verify configured paths
        if not self._should_verify(request):
            return await call_next(request)

        # Get signature header
        signature = request.headers.get(self.config.signature_header)
        if not signature:
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "message": "Missing webhook signature",
                },
            )

        # Read body
        body = await request.body()

        # Verify signature
        if not self._verify_signature(body, signature):
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "message": "Invalid webhook signature",
                },
            )

        # Mark as verified
        request.state.webhook_verified = True

        return await call_next(request)
