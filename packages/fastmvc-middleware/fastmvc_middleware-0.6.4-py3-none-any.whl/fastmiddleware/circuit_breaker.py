"""
Circuit Breaker Middleware for FastMVC.

Implements the circuit breaker pattern to prevent cascade failures.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker middleware.

    Attributes:
        failure_threshold: Number of failures before opening circuit.
        success_threshold: Successes needed to close circuit.
        timeout: Seconds before trying half-open state.
        failure_status_codes: Status codes considered failures.
        excluded_status_codes: Status codes not considered failures.
        per_endpoint: Whether to track circuits per endpoint.

    Example:
        ```python
        from fastmiddleware import CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=60,
            failure_status_codes={500, 502, 503, 504},
        )
        ```
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    failure_status_codes: set[int] = field(default_factory=lambda: {500, 502, 503, 504})
    excluded_status_codes: set[int] = field(default_factory=lambda: {400, 401, 403, 404, 422})
    per_endpoint: bool = True


@dataclass
class CircuitStats:
    """Statistics for a circuit."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    total_failures: int = 0
    total_requests: int = 0


class CircuitBreakerMiddleware(FastMVCMiddleware):
    """
    Middleware that implements the circuit breaker pattern.

    Prevents cascade failures by temporarily rejecting requests
    when error rates exceed thresholds.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Failure threshold exceeded, requests rejected
        - HALF_OPEN: Testing recovery, limited requests allowed

    Features:
        - Configurable failure thresholds
        - Automatic recovery attempts
        - Per-endpoint or global circuits
        - Detailed status endpoint

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import CircuitBreakerMiddleware, CircuitBreakerConfig

        app = FastAPI()

        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=60,
        )
        app.add_middleware(CircuitBreakerMiddleware, config=config)

        # When failures exceed threshold, circuit opens
        # Requests return 503 until timeout
        # After timeout, half-open state tests recovery
        # Successes close the circuit
        ```
    """

    def __init__(
        self,
        app,
        config: CircuitBreakerConfig | None = None,
        failure_threshold: int | None = None,
        timeout: float | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the circuit breaker middleware.

        Args:
            app: The ASGI application.
            config: Circuit breaker configuration.
            failure_threshold: Failure count (overrides config).
            timeout: Recovery timeout (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or CircuitBreakerConfig()

        if failure_threshold is not None:
            self.config.failure_threshold = failure_threshold
        if timeout is not None:
            self.config.timeout = timeout

        # Circuit state storage
        self._circuits: dict[str, CircuitStats] = {}
        self._lock = asyncio.Lock()

    def _get_circuit_key(self, request: Request) -> str:
        """Get circuit key for request."""
        if self.config.per_endpoint:
            return f"{request.method}:{request.url.path}"
        return "global"

    def _get_circuit(self, key: str) -> CircuitStats:
        """Get or create circuit stats."""
        if key not in self._circuits:
            self._circuits[key] = CircuitStats()
        return self._circuits[key]

    def _is_failure(self, response: Response) -> bool:
        """Check if response is considered a failure."""
        if response.status_code in self.config.excluded_status_codes:
            return False
        return response.status_code in self.config.failure_status_codes

    async def _handle_open_circuit(self, circuit: CircuitStats) -> Response | None:
        """Handle open circuit state."""
        now = time.time()
        elapsed = now - circuit.last_failure_time

        if elapsed >= self.config.timeout:
            # Transition to half-open
            circuit.state = CircuitState.HALF_OPEN
            circuit.success_count = 0
            return None  # Allow request

        # Still open, reject
        return JSONResponse(
            status_code=503,
            content={
                "error": True,
                "message": "Service temporarily unavailable",
                "circuit": "open",
                "retry_after": int(self.config.timeout - elapsed),
            },
            headers={
                "Retry-After": str(int(self.config.timeout - elapsed)),
                "X-Circuit-State": "open",
            },
        )

    async def _record_success(self, circuit: CircuitStats) -> None:
        """Record a successful request."""
        async with self._lock:
            circuit.total_requests += 1

            if circuit.state == CircuitState.HALF_OPEN:
                circuit.success_count += 1
                if circuit.success_count >= self.config.success_threshold:
                    # Close circuit
                    circuit.state = CircuitState.CLOSED
                    circuit.failure_count = 0
                    circuit.success_count = 0
            elif circuit.state == CircuitState.CLOSED:
                # Reset failure count on success
                circuit.failure_count = 0

    async def _record_failure(self, circuit: CircuitStats) -> None:
        """Record a failed request."""
        async with self._lock:
            circuit.total_requests += 1
            circuit.total_failures += 1
            circuit.failure_count += 1
            circuit.last_failure_time = time.time()

            if circuit.state == CircuitState.HALF_OPEN:
                # Failure in half-open, back to open
                circuit.state = CircuitState.OPEN
                circuit.failure_count = self.config.failure_threshold
            elif circuit.state == CircuitState.CLOSED:
                if circuit.failure_count >= self.config.failure_threshold:
                    # Open circuit
                    circuit.state = CircuitState.OPEN

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with circuit breaker logic.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response or 503 if circuit is open.
        """
        if self.should_skip(request):
            return await call_next(request)

        key = self._get_circuit_key(request)
        circuit = self._get_circuit(key)

        # Check circuit state
        if circuit.state == CircuitState.OPEN:
            reject_response = await self._handle_open_circuit(circuit)
            if reject_response:
                return reject_response

        # Store circuit state in request
        request.state.circuit_state = circuit.state.value

        try:
            response = await call_next(request)

            # Record result
            if self._is_failure(response):
                await self._record_failure(circuit)
            else:
                await self._record_success(circuit)

            # Add circuit state header
            response.headers["X-Circuit-State"] = circuit.state.value

            return response

        except Exception:
            # Exception counts as failure
            await self._record_failure(circuit)
            raise
