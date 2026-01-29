"""
CSRF Protection Middleware for FastMVC.

Provides Cross-Site Request Forgery protection.
"""

import hashlib
import hmac
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class CSRFConfig:
    """
    Configuration for CSRF protection middleware.

    Attributes:
        secret: Secret key for token generation.
        token_header: Header name for CSRF token.
        cookie_name: Cookie name for CSRF token.
        safe_methods: HTTP methods that don't require CSRF validation.
        cookie_secure: Set Secure flag on cookie.
        cookie_httponly: Set HttpOnly flag on cookie.
        cookie_samesite: SameSite cookie attribute.
        cookie_max_age: Cookie max age in seconds.

    Example:
        ```python
        from FastMiddleware import CSRFConfig

        config = CSRFConfig(
            secret="your-secret-key",
            cookie_secure=True,
        )
        ```
    """

    secret: str = ""
    token_header: str = "X-CSRF-Token"
    cookie_name: str = "csrf_token"
    safe_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD", "OPTIONS", "TRACE"})
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "strict"
    cookie_max_age: int = 3600

    def __post_init__(self):
        if not self.secret:
            self.secret = secrets.token_urlsafe(32)


class CSRFMiddleware(FastMVCMiddleware):
    """
    Middleware that provides CSRF protection.

    Generates and validates CSRF tokens to prevent cross-site
    request forgery attacks.

    Features:
        - Token-based CSRF protection
        - Double-submit cookie pattern
        - Configurable safe methods
        - Secure cookie settings

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import CSRFMiddleware, CSRFConfig

        app = FastAPI()

        config = CSRFConfig(
            secret="your-secret-key",
            cookie_secure=True,  # Use in production
        )
        app.add_middleware(CSRFMiddleware, config=config)
        ```

    Usage:
        1. GET request sets a CSRF cookie
        2. Client includes cookie value in X-CSRF-Token header
        3. POST/PUT/DELETE requests are validated

    Note:
        For API-only applications, consider using SameSite cookies
        and Origin/Referer validation instead.
    """

    def __init__(
        self,
        app,
        config: CSRFConfig | None = None,
        secret: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the CSRF middleware.

        Args:
            app: The ASGI application.
            config: CSRF configuration.
            secret: Secret key (overrides config).
            exclude_paths: Paths to exclude from protection.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CSRFConfig()

        if secret is not None:
            self.config.secret = secret

    def _generate_token(self) -> str:
        """Generate a new CSRF token."""
        random_bytes = secrets.token_bytes(32)
        signature = hmac.new(
            self.config.secret.encode(),
            random_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"{random_bytes.hex()}.{signature}"

    def _validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return False

            random_hex, signature = parts
            random_bytes = bytes.fromhex(random_hex)
            expected_signature = hmac.new(
                self.config.secret.encode(),
                random_bytes,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, TypeError):
            return False

    def _is_safe_method(self, method: str) -> bool:
        """Check if method is safe (doesn't require CSRF validation)."""
        return method.upper() in self.config.safe_methods

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with CSRF protection.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with CSRF handling.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Safe methods - just ensure token cookie exists
        if self._is_safe_method(request.method):
            response = await call_next(request)

            # Set CSRF cookie if not present
            if self.config.cookie_name not in request.cookies:
                token = self._generate_token()
                response.set_cookie(
                    key=self.config.cookie_name,
                    value=token,
                    max_age=self.config.cookie_max_age,
                    httponly=self.config.cookie_httponly,
                    secure=self.config.cookie_secure,
                    samesite=self.config.cookie_samesite,
                )

            return response

        # Unsafe methods - validate token
        cookie_token = request.cookies.get(self.config.cookie_name)
        header_token = request.headers.get(self.config.token_header)

        # Both must be present and match
        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "CSRF token missing",
                },
            )

        if cookie_token != header_token:
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "CSRF token mismatch",
                },
            )

        # Validate token signature
        if not self._validate_token(cookie_token):
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "Invalid CSRF token",
                },
            )

        return await call_next(request)
