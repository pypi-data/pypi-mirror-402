"""
CORS (Cross-Origin Resource Sharing) Middleware for FastMVC.

Provides configurable CORS headers with sensible defaults for API development.
"""

from collections.abc import Sequence

from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware


class CORSMiddleware(StarletteCORSMiddleware):
    """
    CORS middleware with sensible defaults for FastMVC applications.

    This is a thin wrapper around Starlette's CORSMiddleware with
    commonly used defaults for API development.

    Features:
        - Configurable allowed origins, methods, and headers
        - Support for credentials
        - Origin regex matching
        - Preflight response caching

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import CORSMiddleware

        app = FastAPI()

        # Allow specific origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://example.com", "https://app.example.com"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Allow all origins (development)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # Must be False when using "*"
        )
        ```

    Note:
        When `allow_origins` is set to `["*"]`, `allow_credentials` must be
        set to `False` for security reasons.
    """

    def __init__(
        self,
        app,
        allow_origins: Sequence[str] = (),
        allow_methods: Sequence[str] = ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"),
        allow_headers: Sequence[str] = ("*",),
        allow_credentials: bool = True,
        allow_origin_regex: str | None = None,
        expose_headers: Sequence[str] = (),
        max_age: int = 600,
    ) -> None:
        """
        Initialize the CORS middleware.

        Args:
            app: The ASGI application.
            allow_origins: List of allowed origins. Use ["*"] to allow all.
            allow_methods: List of allowed HTTP methods.
            allow_headers: List of allowed headers. Use ["*"] to allow all.
            allow_credentials: Whether to allow credentials (cookies, auth headers).
            allow_origin_regex: Regex pattern for matching allowed origins.
            expose_headers: Headers to expose to the browser.
            max_age: Maximum time (seconds) for browsers to cache preflight responses.
        """
        super().__init__(
            app,
            allow_origins=allow_origins,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            allow_credentials=allow_credentials,
            allow_origin_regex=allow_origin_regex,
            expose_headers=expose_headers,
            max_age=max_age,
        )
