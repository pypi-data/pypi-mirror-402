"""
Health Check Middleware for FastMVC.

Provides built-in health, readiness, and liveness endpoints.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class HealthConfig:
    """
    Configuration for health check middleware.

    Attributes:
        health_path: Path for health check endpoint.
        ready_path: Path for readiness check endpoint.
        live_path: Path for liveness check endpoint.
        include_details: Include detailed information in health response.
        version: Application version to include in health response.
        custom_checks: Custom health check functions.

    Example:
        ```python
        from FastMiddleware import HealthConfig

        async def check_database():
            # Return True if healthy, False otherwise
            return await db.ping()

        config = HealthConfig(
            version="1.0.0",
            custom_checks={"database": check_database},
        )
        ```
    """

    health_path: str = "/health"
    ready_path: str = "/ready"
    live_path: str = "/live"
    include_details: bool = True
    version: str | None = None
    service_name: str | None = None

    # Custom health check functions: {name: async_check_function}
    # Each function should return True for healthy, False for unhealthy
    custom_checks: dict[str, Callable[[], Awaitable[bool]]] = field(default_factory=dict)


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides built-in health check endpoints.

    Automatically responds to health, readiness, and liveness check
    requests without passing them to your application routes.

    Endpoints:
        - /health: Overall health status with optional details
        - /ready: Readiness check (ready to receive traffic)
        - /live: Liveness check (application is running)

    Features:
        - Zero-config health endpoints
        - Custom health check functions
        - Kubernetes-compatible responses
        - Uptime and version tracking
        - Detailed health status

    Response Format:
        ```json
        {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "uptime_seconds": 3600,
            "version": "1.0.0",
            "checks": {
                "database": "healthy",
                "cache": "healthy"
            }
        }
        ```

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import HealthCheckMiddleware, HealthConfig

        app = FastAPI()

        # Basic usage
        app.add_middleware(HealthCheckMiddleware)

        # With custom checks
        async def check_db():
            return await database.is_connected()

        async def check_redis():
            return await redis.ping()

        config = HealthConfig(
            version="1.0.0",
            service_name="my-api",
            custom_checks={
                "database": check_db,
                "cache": check_redis,
            },
        )
        app.add_middleware(HealthCheckMiddleware, config=config)
        ```

    Kubernetes:
        Use these endpoints in your pod spec:
        ```yaml
        livenessProbe:
          httpGet:
            path: /live
            port: 8000
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
        ```
    """

    def __init__(
        self,
        app,
        config: HealthConfig | None = None,
        health_path: str | None = None,
        ready_path: str | None = None,
        live_path: str | None = None,
        version: str | None = None,
        service_name: str | None = None,
    ) -> None:
        """
        Initialize the health check middleware.

        Args:
            app: The ASGI application.
            config: Health check configuration.
            health_path: Path for health endpoint (overrides config).
            ready_path: Path for readiness endpoint (overrides config).
            live_path: Path for liveness endpoint (overrides config).
            version: Application version (overrides config).
            service_name: Service name (overrides config).
        """
        super().__init__(app)

        self.config = config or HealthConfig()
        self._start_time = datetime.now(timezone.utc)

        if health_path is not None:
            self.config.health_path = health_path
        if ready_path is not None:
            self.config.ready_path = ready_path
        if live_path is not None:
            self.config.live_path = live_path
        if version is not None:
            self.config.version = version
        if service_name is not None:
            self.config.service_name = service_name

    def _get_uptime(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

    async def _run_checks(self) -> dict[str, str]:
        """Run all custom health checks."""
        results = {}

        for name, check_func in self.config.custom_checks.items():
            try:
                is_healthy = await check_func()
                results[name] = "healthy" if is_healthy else "unhealthy"
            except Exception:
                results[name] = "unhealthy"

        return results

    async def _health_response(self, request: Request) -> Response:
        """Generate health check response."""
        checks = await self._run_checks()
        all_healthy = all(status == "healthy" for status in checks.values())

        body: dict[str, Any] = {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if self.config.include_details:
            body["uptime_seconds"] = round(self._get_uptime(), 2)

            if self.config.version:
                body["version"] = self.config.version

            if self.config.service_name:
                body["service"] = self.config.service_name

            if checks:
                body["checks"] = checks

        status_code = 200 if all_healthy else 503

        return JSONResponse(content=body, status_code=status_code)

    async def _ready_response(self, request: Request) -> Response:
        """Generate readiness check response."""
        checks = await self._run_checks()
        all_healthy = all(status == "healthy" for status in checks.values())

        body = {
            "ready": all_healthy,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if checks:
            body["checks"] = checks

        status_code = 200 if all_healthy else 503

        return JSONResponse(content=body, status_code=status_code)

    async def _live_response(self, request: Request) -> Response:
        """Generate liveness check response."""
        return JSONResponse(
            content={
                "alive": True,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            status_code=200,
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Handle health check requests or pass through to application.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            Health check response or the application response.
        """
        path = request.url.path

        if path == self.config.health_path:
            return await self._health_response(request)
        elif path == self.config.ready_path:
            return await self._ready_response(request)
        elif path == self.config.live_path:
            return await self._live_response(request)

        return await call_next(request)
