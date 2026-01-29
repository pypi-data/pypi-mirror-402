"""
Security Headers Middleware for FastMVC.

Adds comprehensive security headers to protect against common web vulnerabilities.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class SecurityHeadersConfig:
    """
    Configuration for security headers.

    This dataclass provides a structured way to configure all security headers
    with sensible defaults.

    Attributes:
        x_content_type_options: Prevents MIME type sniffing.
        x_frame_options: Controls iframe embedding (DENY, SAMEORIGIN).
        x_xss_protection: Legacy XSS protection (modern browsers ignore this).
        referrer_policy: Controls referrer information in requests.
        enable_hsts: Enable HTTP Strict Transport Security.
        hsts_max_age: HSTS max-age in seconds (default: 1 year).
        hsts_include_subdomains: Include subdomains in HSTS.
        hsts_preload: Enable HSTS preload.
        content_security_policy: Custom CSP string.
        permissions_policy: Custom Permissions-Policy string.
        cross_origin_opener_policy: COOP header value.
        cross_origin_resource_policy: CORP header value.
        cross_origin_embedder_policy: COEP header value.
        remove_server_header: Remove the Server header from responses.

    Example:
        ```python
        from FastMiddleware import SecurityHeadersConfig

        config = SecurityHeadersConfig(
            enable_hsts=True,
            hsts_preload=True,
            content_security_policy="default-src 'self'",
        )
        ```
    """

    # Basic headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"

    # HSTS settings
    enable_hsts: bool = False
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # Content Security Policy
    content_security_policy: str | None = None

    # Permissions Policy
    permissions_policy: str | None = None

    # Cross-Origin policies
    cross_origin_opener_policy: str | None = "same-origin"
    cross_origin_resource_policy: str | None = "same-origin"
    cross_origin_embedder_policy: str | None = None

    # Server header
    remove_server_header: bool = True

    def build_hsts_header(self) -> str:
        """Build the HSTS header value."""
        parts = [f"max-age={self.hsts_max_age}"]
        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")
        if self.hsts_preload:
            parts.append("preload")
        return "; ".join(parts)


class SecurityHeadersMiddleware(FastMVCMiddleware):
    """
    Middleware that adds comprehensive security headers to all responses.

    This middleware protects against common web vulnerabilities by adding
    security headers recommended by OWASP and security best practices.

    Headers Added:
        - X-Content-Type-Options: Prevents MIME type sniffing
        - X-Frame-Options: Protects against clickjacking
        - X-XSS-Protection: Legacy XSS protection
        - Strict-Transport-Security: Forces HTTPS connections
        - Content-Security-Policy: Controls resource loading
        - Referrer-Policy: Controls referrer information
        - Permissions-Policy: Controls browser features
        - Cross-Origin-Opener-Policy: Isolates browsing context
        - Cross-Origin-Resource-Policy: Controls cross-origin access

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import SecurityHeadersMiddleware, SecurityHeadersConfig

        app = FastAPI()

        # Basic usage with defaults
        app.add_middleware(SecurityHeadersMiddleware)

        # With HSTS enabled (for production HTTPS sites)
        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_hsts=True,
            content_security_policy="default-src 'self'",
        )

        # Using config object
        config = SecurityHeadersConfig(
            enable_hsts=True,
            hsts_preload=True,
            content_security_policy="default-src 'self'; script-src 'self' 'unsafe-inline'",
        )
        app.add_middleware(SecurityHeadersMiddleware, config=config)
        ```
    """

    # Default CSP for APIs (restrictive)
    DEFAULT_CSP = "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'"

    # Default Permissions-Policy (disable most features for APIs)
    DEFAULT_PERMISSIONS_POLICY = (
        "accelerometer=(), "
        "camera=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "payment=(), "
        "usb=()"
    )

    def __init__(
        self,
        app,
        config: SecurityHeadersConfig | None = None,
        # Individual settings (override config if provided)
        x_content_type_options: str | None = None,
        x_frame_options: str | None = None,
        x_xss_protection: str | None = None,
        referrer_policy: str | None = None,
        enable_hsts: bool | None = None,
        hsts_max_age: int | None = None,
        hsts_include_subdomains: bool | None = None,
        hsts_preload: bool | None = None,
        content_security_policy: str | None = None,
        permissions_policy: str | None = None,
        cross_origin_opener_policy: str | None = None,
        cross_origin_resource_policy: str | None = None,
        cross_origin_embedder_policy: str | None = None,
        remove_server_header: bool | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the security headers middleware.

        Args:
            app: The ASGI application.
            config: Configuration object for security headers.
            x_content_type_options: X-Content-Type-Options header value.
            x_frame_options: X-Frame-Options header value.
            x_xss_protection: X-XSS-Protection header value.
            referrer_policy: Referrer-Policy header value.
            enable_hsts: Enable HSTS header.
            hsts_max_age: HSTS max-age value.
            hsts_include_subdomains: Include subdomains in HSTS.
            hsts_preload: Enable HSTS preload.
            content_security_policy: Content-Security-Policy header value.
            permissions_policy: Permissions-Policy header value.
            cross_origin_opener_policy: Cross-Origin-Opener-Policy header value.
            cross_origin_resource_policy: Cross-Origin-Resource-Policy header value.
            cross_origin_embedder_policy: Cross-Origin-Embedder-Policy header value.
            remove_server_header: Whether to remove the Server header.
            exclude_paths: Paths to exclude from security headers.
            exclude_methods: HTTP methods to exclude from security headers.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        # Use config or create default
        self.config = config or SecurityHeadersConfig()

        # Override config with individual settings if provided
        if x_content_type_options is not None:
            self.config.x_content_type_options = x_content_type_options
        if x_frame_options is not None:
            self.config.x_frame_options = x_frame_options
        if x_xss_protection is not None:
            self.config.x_xss_protection = x_xss_protection
        if referrer_policy is not None:
            self.config.referrer_policy = referrer_policy
        if enable_hsts is not None:
            self.config.enable_hsts = enable_hsts
        if hsts_max_age is not None:
            self.config.hsts_max_age = hsts_max_age
        if hsts_include_subdomains is not None:
            self.config.hsts_include_subdomains = hsts_include_subdomains
        if hsts_preload is not None:
            self.config.hsts_preload = hsts_preload
        if content_security_policy is not None:
            self.config.content_security_policy = content_security_policy
        if permissions_policy is not None:
            self.config.permissions_policy = permissions_policy
        if cross_origin_opener_policy is not None:
            self.config.cross_origin_opener_policy = cross_origin_opener_policy
        if cross_origin_resource_policy is not None:
            self.config.cross_origin_resource_policy = cross_origin_resource_policy
        if cross_origin_embedder_policy is not None:
            self.config.cross_origin_embedder_policy = cross_origin_embedder_policy
        if remove_server_header is not None:
            self.config.remove_server_header = remove_server_header

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and add security headers to response.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response with security headers.
        """
        response = await call_next(request)

        # Skip if path/method is excluded
        if self.should_skip(request):
            return response

        # Add basic security headers
        if self.config.x_content_type_options:
            response.headers["X-Content-Type-Options"] = self.config.x_content_type_options

        if self.config.x_frame_options:
            response.headers["X-Frame-Options"] = self.config.x_frame_options

        if self.config.x_xss_protection:
            response.headers["X-XSS-Protection"] = self.config.x_xss_protection

        if self.config.referrer_policy:
            response.headers["Referrer-Policy"] = self.config.referrer_policy

        # Add HSTS header (only for HTTPS in production)
        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = self.config.build_hsts_header()

        # Add Content Security Policy
        csp = self.config.content_security_policy or self.DEFAULT_CSP
        response.headers["Content-Security-Policy"] = csp

        # Add Permissions Policy
        permissions = self.config.permissions_policy or self.DEFAULT_PERMISSIONS_POLICY
        response.headers["Permissions-Policy"] = permissions

        # Add Cross-Origin policies
        if self.config.cross_origin_opener_policy:
            response.headers["Cross-Origin-Opener-Policy"] = self.config.cross_origin_opener_policy

        if self.config.cross_origin_resource_policy:
            response.headers["Cross-Origin-Resource-Policy"] = (
                self.config.cross_origin_resource_policy
            )

        if self.config.cross_origin_embedder_policy:
            response.headers["Cross-Origin-Embedder-Policy"] = (
                self.config.cross_origin_embedder_policy
            )

        # Remove Server header if configured
        if self.config.remove_server_header and "Server" in response.headers:
            del response.headers["Server"]

        return response
