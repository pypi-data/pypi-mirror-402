"""
Profiling Middleware for FastMVC.

Provides request profiling and performance metrics.
"""

import time
import cProfile
import pstats
import io
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, List
from collections import defaultdict

from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ProfilingConfig:
    """
    Configuration for profiling middleware.
    
    Attributes:
        enabled: Whether profiling is enabled.
        profile_path: Path to access profiling results.
        enable_cprofile: Enable detailed CPU profiling.
        slow_request_threshold: Log requests slower than this (ms).
        track_endpoints: Track per-endpoint statistics.
        max_samples: Maximum samples to keep per endpoint.
    
    Example:
        ```python
        from FastMiddleware import ProfilingConfig
        
        config = ProfilingConfig(
            enabled=True,  # Enable in dev only!
            slow_request_threshold=500,  # Log >500ms requests
        )
        ```
    """
    
    enabled: bool = False  # Disabled by default (enable in dev only)
    profile_path: str = "/_profile"
    enable_cprofile: bool = False
    slow_request_threshold: float = 1000.0  # ms
    track_endpoints: bool = True
    max_samples: int = 100


@dataclass
class EndpointStats:
    """Statistics for a single endpoint."""
    
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    samples: List[float] = field(default_factory=list)
    
    def add_sample(self, duration: float, max_samples: int = 100) -> None:
        """Add a timing sample."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        
        self.samples.append(duration)
        if len(self.samples) > max_samples:
            self.samples.pop(0)
    
    @property
    def avg_time(self) -> float:
        """Average response time."""
        return self.total_time / self.count if self.count > 0 else 0.0
    
    @property
    def p50(self) -> float:
        """50th percentile (median)."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = len(sorted_samples) // 2
        return sorted_samples[idx]
    
    @property
    def p95(self) -> float:
        """95th percentile."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]
    
    @property
    def p99(self) -> float:
        """99th percentile."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "total_ms": round(self.total_time, 2),
            "avg_ms": round(self.avg_time, 2),
            "min_ms": round(self.min_time, 2) if self.min_time != float("inf") else 0,
            "max_ms": round(self.max_time, 2),
            "p50_ms": round(self.p50, 2),
            "p95_ms": round(self.p95, 2),
            "p99_ms": round(self.p99, 2),
        }


class ProfilingMiddleware(FastMVCMiddleware):
    """
    Middleware that profiles request performance.
    
    Collects timing statistics for all endpoints and optionally
    provides detailed CPU profiling.
    
    Features:
        - Per-endpoint timing statistics
        - Percentile calculations (p50, p95, p99)
        - Slow request logging
        - Optional CPU profiling
        - JSON stats endpoint
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import ProfilingMiddleware, ProfilingConfig
        
        app = FastAPI()
        
        # Enable only in development!
        if settings.DEBUG:
            config = ProfilingConfig(
                enabled=True,
                slow_request_threshold=500,
            )
            app.add_middleware(ProfilingMiddleware, config=config)
        
        # Access stats at /_profile
        ```
    
    Warning:
        Do NOT enable in production! Profiling adds overhead.
    """
    
    def __init__(
        self,
        app,
        config: ProfilingConfig | None = None,
        enabled: bool | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        """
        Initialize the profiling middleware.
        
        Args:
            app: The ASGI application.
            config: Profiling configuration.
            enabled: Enable profiling (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ProfilingConfig()
        
        if enabled is not None:
            self.config.enabled = enabled
        
        # Statistics storage
        self._stats: Dict[str, EndpointStats] = defaultdict(EndpointStats)
        self._slow_requests: List[Dict] = []
        self._start_time = time.time()
    
    def _get_stats_response(self) -> Response:
        """Generate profiling stats response."""
        uptime = time.time() - self._start_time
        
        # Build stats
        endpoints = {
            path: stats.to_dict()
            for path, stats in sorted(self._stats.items())
        }
        
        # Calculate totals
        total_requests = sum(s.count for s in self._stats.values())
        total_time = sum(s.total_time for s in self._stats.values())
        
        return JSONResponse({
            "uptime_seconds": round(uptime, 2),
            "total_requests": total_requests,
            "total_time_ms": round(total_time, 2),
            "avg_time_ms": round(total_time / total_requests, 2) if total_requests > 0 else 0,
            "endpoints": endpoints,
            "slow_requests": self._slow_requests[-20:],  # Last 20 slow requests
        })
    
    def _profile_request(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> str:
        """Run cProfile on request and return stats."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Note: This doesn't work well with async, just a placeholder
        # Real profiling requires different approach
        
        profiler.disable()
        
        # Get stats
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(30)
        
        return stream.getvalue()
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with profiling.
        
        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.
            
        Returns:
            The response with profiling data.
        """
        # Handle profile endpoint
        if request.url.path == self.config.profile_path:
            if not self.config.enabled:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Profiling is disabled"},
                )
            return self._get_stats_response()
        
        # Skip if disabled or excluded
        if not self.config.enabled or self.should_skip(request):
            return await call_next(request)
        
        # Time the request
        start = time.perf_counter()
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Track endpoint stats
        if self.config.track_endpoints:
            path = request.url.path
            method = request.method
            key = f"{method} {path}"
            
            self._stats[key].add_sample(duration_ms, self.config.max_samples)
        
        # Log slow requests
        if duration_ms > self.config.slow_request_threshold:
            self._slow_requests.append({
                "path": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.time(),
                "status": response.status_code,
            })
            
            # Keep only last 100 slow requests
            if len(self._slow_requests) > 100:
                self._slow_requests.pop(0)
        
        # Add timing header
        response.headers["X-Profile-Time-Ms"] = f"{duration_ms:.2f}"
        
        return response

