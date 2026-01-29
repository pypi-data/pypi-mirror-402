"""
Metrics Middleware for FastMVC.

Provides request metrics collection with Prometheus-compatible format.
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


@dataclass
class MetricsConfig:
    """
    Configuration for metrics middleware.

    Attributes:
        metrics_path: Path to expose metrics endpoint.
        enable_latency_histogram: Collect latency histogram.
        enable_request_count: Collect request counts.
        enable_response_size: Collect response size metrics.
        histogram_buckets: Latency histogram buckets (in seconds).
        group_paths: Group dynamic path segments (e.g., /users/123 -> /users/{id}).
        path_patterns: Patterns for path grouping.

    Example:
        ```python
        from FastMiddleware import MetricsConfig

        config = MetricsConfig(
            metrics_path="/metrics",
            histogram_buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
        )
        ```
    """

    metrics_path: str = "/metrics"
    enable_latency_histogram: bool = True
    enable_request_count: bool = True
    enable_response_size: bool = True
    histogram_buckets: tuple[float, ...] = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    )

    # Path patterns for grouping: {pattern: replacement}
    # e.g., {r"/users/\d+": "/users/{id}"}
    path_patterns: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores metrics in memory.

    Provides Prometheus-compatible metric formats:
    - Counters (total requests)
    - Histograms (latency distribution)
    - Gauges (current values)
    """

    def __init__(self, config: MetricsConfig) -> None:
        self.config = config
        self._start_time = time.time()

        # Request counters: {(method, path, status): count}
        self._request_count: dict[tuple[str, str, int], int] = defaultdict(int)

        # Latency data: {(method, path): [latencies]}
        self._latencies: dict[tuple[str, str], list[float]] = defaultdict(list)

        # Response sizes: {(method, path): [sizes]}
        self._response_sizes: dict[tuple[str, str], list[int]] = defaultdict(list)

        # Error counts
        self._error_count: dict[tuple[str, str], int] = defaultdict(int)

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        latency: float,
        response_size: int = 0,
    ) -> None:
        """Record metrics for a single request."""
        key = (method, path, status_code)
        self._request_count[key] += 1

        if self.config.enable_latency_histogram:
            self._latencies[(method, path)].append(latency)

        if self.config.enable_response_size:
            self._response_sizes[(method, path)].append(response_size)

        if status_code >= 500:
            self._error_count[(method, path)] += 1

    def _calculate_histogram_buckets(
        self, values: list[float], buckets: tuple[float, ...]
    ) -> dict[str, int]:
        """Calculate histogram bucket counts."""
        result = {}
        for bucket in buckets:
            count = sum(1 for v in values if v <= bucket)
            result[str(bucket)] = count
        result["+Inf"] = len(values)
        return result

    def _format_prometheus(self) -> str:
        """Format metrics in Prometheus exposition format."""
        lines = []

        # Uptime
        uptime = time.time() - self._start_time
        lines.append("# HELP fastmvc_uptime_seconds Time since service start")
        lines.append("# TYPE fastmvc_uptime_seconds gauge")
        lines.append(f"fastmvc_uptime_seconds {uptime:.2f}")
        lines.append("")

        # Request count
        if self.config.enable_request_count:
            lines.append("# HELP fastmvc_http_requests_total Total HTTP requests")
            lines.append("# TYPE fastmvc_http_requests_total counter")
            for (method, path, status), count in sorted(self._request_count.items()):
                lines.append(
                    f'fastmvc_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
                )
            lines.append("")

        # Latency histogram
        if self.config.enable_latency_histogram and self._latencies:
            lines.append("# HELP fastmvc_http_request_duration_seconds HTTP request latency")
            lines.append("# TYPE fastmvc_http_request_duration_seconds histogram")

            for (method, path), latencies in sorted(self._latencies.items()):
                if not latencies:
                    continue

                buckets = self._calculate_histogram_buckets(
                    latencies, self.config.histogram_buckets
                )

                for bucket, count in buckets.items():
                    lines.append(
                        f'fastmvc_http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="{bucket}"}} {count}'
                    )

                total = sum(latencies)
                lines.append(
                    f'fastmvc_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total:.6f}'
                )
                lines.append(
                    f'fastmvc_http_request_duration_seconds_count{{method="{method}",path="{path}"}} {len(latencies)}'
                )
            lines.append("")

        # Response size
        if self.config.enable_response_size and self._response_sizes:
            lines.append("# HELP fastmvc_http_response_size_bytes HTTP response size")
            lines.append("# TYPE fastmvc_http_response_size_bytes summary")

            for (method, path), sizes in sorted(self._response_sizes.items()):
                if not sizes:
                    continue

                total = sum(sizes)
                lines.append(
                    f'fastmvc_http_response_size_bytes_sum{{method="{method}",path="{path}"}} {total}'
                )
                lines.append(
                    f'fastmvc_http_response_size_bytes_count{{method="{method}",path="{path}"}} {len(sizes)}'
                )
            lines.append("")

        # Error count
        if self._error_count:
            lines.append("# HELP fastmvc_http_errors_total Total HTTP 5xx errors")
            lines.append("# TYPE fastmvc_http_errors_total counter")
            for (method, path), count in sorted(self._error_count.items()):
                lines.append(
                    f'fastmvc_http_errors_total{{method="{method}",path="{path}"}} {count}'
                )
            lines.append("")

        return "\n".join(lines)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return self._format_prometheus()

    def get_json_metrics(self) -> dict[str, Any]:
        """Get metrics as JSON-serializable dictionary."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "requests": {
                f"{method} {path} {status}": count
                for (method, path, status), count in self._request_count.items()
            },
            "errors": dict(self._error_count),
            "total_requests": sum(self._request_count.values()),
            "total_errors": sum(self._error_count.values()),
        }


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects request metrics and exposes a Prometheus endpoint.

    Automatically collects metrics for all requests and provides a /metrics
    endpoint compatible with Prometheus scraping.

    Metrics Collected:
        - fastmvc_http_requests_total: Total request count by method/path/status
        - fastmvc_http_request_duration_seconds: Request latency histogram
        - fastmvc_http_response_size_bytes: Response size summary
        - fastmvc_http_errors_total: 5xx error count
        - fastmvc_uptime_seconds: Service uptime

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import MetricsMiddleware, MetricsConfig

        app = FastAPI()

        # Basic usage
        app.add_middleware(MetricsMiddleware)

        # Custom configuration
        config = MetricsConfig(
            metrics_path="/prometheus",
            histogram_buckets=[0.1, 0.5, 1.0, 5.0],
        )
        app.add_middleware(MetricsMiddleware, config=config)
        ```

    Prometheus Scraping:
        Configure Prometheus to scrape the /metrics endpoint:
        ```yaml
        scrape_configs:
          - job_name: 'fastmvc-app'
            static_configs:
              - targets: ['localhost:8000']
        ```
    """

    def __init__(
        self,
        app,
        config: MetricsConfig | None = None,
        metrics_path: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the metrics middleware.

        Args:
            app: The ASGI application.
            config: Metrics configuration.
            metrics_path: Path for metrics endpoint (overrides config).
            exclude_paths: Paths to exclude from metrics collection.
        """
        super().__init__(app)

        self.config = config or MetricsConfig()
        self.exclude_paths = exclude_paths or set()

        if metrics_path is not None:
            self.config.metrics_path = metrics_path

        # Add metrics path to excludes
        self.exclude_paths.add(self.config.metrics_path)

        self.collector = MetricsCollector(self.config)

    def _normalize_path(self, path: str) -> str:
        """Normalize path for grouping (replace IDs with placeholders)."""
        import re

        for pattern, replacement in self.config.path_patterns.items():
            path = re.sub(pattern, replacement, path)

        return path

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware or route handler.

        Returns:
            The HTTP response.
        """
        path = request.url.path

        # Handle metrics endpoint
        if path == self.config.metrics_path:
            return PlainTextResponse(
                content=self.collector.get_metrics(),
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        # Skip excluded paths
        if path in self.exclude_paths:
            return await call_next(request)

        # Record request
        start_time = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start_time

        # Get response size from headers
        response_size = int(response.headers.get("Content-Length", 0))

        # Normalize path for grouping
        normalized_path = self._normalize_path(path)

        # Record metrics
        self.collector.record_request(
            method=request.method,
            path=normalized_path,
            status_code=response.status_code,
            latency=latency,
            response_size=response_size,
        )

        return response
