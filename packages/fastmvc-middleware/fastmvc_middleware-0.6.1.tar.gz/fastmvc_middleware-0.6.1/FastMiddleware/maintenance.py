"""
Maintenance Mode Middleware for FastMVC.

Provides a maintenance mode that returns 503 responses.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class MaintenanceConfig:
    """
    Configuration for maintenance mode middleware.

    Attributes:
        enabled: Whether maintenance mode is active.
        message: Message to display during maintenance.
        retry_after: Estimated time until service is restored (seconds).
        allowed_ips: IP addresses that can bypass maintenance mode.
        allowed_paths: Paths that remain accessible during maintenance.
        bypass_header: Header name for bypass token.
        bypass_token: Token value to bypass maintenance mode.
        html_template: Custom HTML template for maintenance page.

    Example:
        ```python
        from FastMiddleware import MaintenanceConfig

        config = MaintenanceConfig(
            enabled=True,
            message="We're upgrading! Back in 30 minutes.",
            retry_after=1800,
            allowed_ips={"10.0.0.1", "192.168.1.1"},
            allowed_paths={"/health", "/status"},
        )
        ```
    """

    enabled: bool = False
    message: str = "Service temporarily unavailable for maintenance"
    retry_after: int = 300  # 5 minutes
    allowed_ips: set[str] | None = None
    allowed_paths: set[str] | None = None
    bypass_header: str = "X-Maintenance-Bypass"
    bypass_token: str | None = None
    html_template: str | None = None
    use_html: bool = False


class MaintenanceMiddleware(FastMVCMiddleware):
    """
    Middleware that enables maintenance mode for your application.

    When enabled, returns 503 Service Unavailable for all requests
    except those from allowed IPs, paths, or with bypass tokens.

    Features:
        - IP-based bypass (for admin access)
        - Path-based bypass (for health checks)
        - Token-based bypass (for testing)
        - Configurable retry time
        - JSON or HTML responses
        - Dynamic enable/disable

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import MaintenanceMiddleware, MaintenanceConfig

        app = FastAPI()

        # Static configuration
        config = MaintenanceConfig(
            enabled=False,  # Toggle to True to enable
            message="We're upgrading our systems. Please try again later.",
            retry_after=1800,
            allowed_paths={"/health", "/status"},
        )

        middleware = MaintenanceMiddleware(app, config=config)
        app.add_middleware(MaintenanceMiddleware, config=config)

        # Enable/disable at runtime
        middleware.enable()
        middleware.disable()
        ```

    Response (JSON):
        ```json
        {
            "error": true,
            "message": "Service temporarily unavailable for maintenance",
            "maintenance": true,
            "retry_after": 300
        }
        ```

    Response Headers:
        - Retry-After: 300
        - X-Maintenance-Mode: true
    """

    DEFAULT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintenance</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
            max-width: 600px;
        }}
        .icon {{
            font-size: 4rem;
            margin-bottom: 1.5rem;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        p {{
            color: #a0a0a0;
            font-size: 1.1rem;
            line-height: 1.6;
        }}
        .retry {{
            margin-top: 2rem;
            padding: 1rem 2rem;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            display: inline-block;
        }}
        .retry span {{
            color: #4ade80;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔧</div>
        <h1>Under Maintenance</h1>
        <p>{message}</p>
        <div class="retry">
            Estimated time: <span>{retry_minutes} minutes</span>
        </div>
    </div>
</body>
</html>
"""

    def __init__(
        self,
        app,
        config: MaintenanceConfig | None = None,
        enabled: bool | None = None,
        message: str | None = None,
        retry_after: int | None = None,
        allowed_ips: set[str] | None = None,
        allowed_paths: set[str] | None = None,
        bypass_token: str | None = None,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
    ) -> None:
        """
        Initialize the maintenance middleware.

        Args:
            app: The ASGI application.
            config: Maintenance configuration.
            enabled: Enable maintenance mode (overrides config).
            message: Maintenance message (overrides config).
            retry_after: Retry time in seconds (overrides config).
            allowed_ips: IPs that bypass maintenance (overrides config).
            allowed_paths: Paths that bypass maintenance (overrides config).
            bypass_token: Token to bypass maintenance (overrides config).
            exclude_paths: Paths to exclude from middleware.
            exclude_methods: HTTP methods to exclude from middleware.
        """
        super().__init__(app, exclude_paths=exclude_paths, exclude_methods=exclude_methods)

        self.config = config or MaintenanceConfig()

        if enabled is not None:
            self.config.enabled = enabled
        if message is not None:
            self.config.message = message
        if retry_after is not None:
            self.config.retry_after = retry_after
        if allowed_ips is not None:
            self.config.allowed_ips = allowed_ips
        if allowed_paths is not None:
            self.config.allowed_paths = allowed_paths
        if bypass_token is not None:
            self.config.bypass_token = bypass_token

    def enable(self, message: str | None = None, retry_after: int | None = None) -> None:
        """Enable maintenance mode."""
        self.config.enabled = True
        if message:
            self.config.message = message
        if retry_after:
            self.config.retry_after = retry_after

    def disable(self) -> None:
        """Disable maintenance mode."""
        self.config.enabled = False

    def is_enabled(self) -> bool:
        """Check if maintenance mode is enabled."""
        return self.config.enabled

    def _should_bypass(self, request: Request) -> bool:
        """Check if request should bypass maintenance mode."""
        # Check allowed paths
        if self.config.allowed_paths and request.url.path in self.config.allowed_paths:
            return True

        # Check allowed IPs
        if self.config.allowed_ips:
            client_ip = self.get_client_ip(request)
            if client_ip in self.config.allowed_ips:
                return True

        # Check bypass token
        if self.config.bypass_token:
            token = request.headers.get(self.config.bypass_header)
            if token == self.config.bypass_token:
                return True

        return False

    def _get_html_response(self) -> str:
        """Generate HTML maintenance page."""
        template = self.config.html_template or self.DEFAULT_HTML
        return template.format(
            message=self.config.message,
            retry_minutes=self.config.retry_after // 60,
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with maintenance mode check.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response or 503 maintenance response.
        """
        # Pass through if maintenance mode is disabled
        if not self.config.enabled:
            return await call_next(request)

        # Check for bypass conditions
        if self._should_bypass(request):
            return await call_next(request)

        # Skip excluded paths/methods
        if self.should_skip(request):
            return await call_next(request)

        # Return maintenance response
        headers = {
            "Retry-After": str(self.config.retry_after),
            "X-Maintenance-Mode": "true",
        }

        if self.config.use_html:
            return HTMLResponse(
                content=self._get_html_response(),
                status_code=503,
                headers=headers,
            )

        return JSONResponse(
            content={
                "error": True,
                "message": self.config.message,
                "maintenance": True,
                "retry_after": self.config.retry_after,
            },
            status_code=503,
            headers=headers,
        )
