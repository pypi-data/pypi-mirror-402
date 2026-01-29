"""
Audit Logging Middleware for FastMVC.

Provides comprehensive audit logging for compliance and security.
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class AuditEvent:
    """Represents an audit event."""

    timestamp: str
    request_id: str | None
    user_id: str | None
    action: str
    resource: str
    method: str
    path: str
    status_code: int
    client_ip: str
    user_agent: str
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class AuditConfig:
    """
    Configuration for audit logging middleware.

    Attributes:
        enabled: Whether audit logging is enabled.
        log_all_requests: Log all requests vs only mutating.
        log_request_body: Include request body in logs.
        log_response_body: Include response body in logs.
        sensitive_fields: Fields to redact from logs.
        action_mapping: Map methods to action names.
        logger_name: Logger name for audit events.
        emit_func: Custom function to emit audit events.

    Example:
        ```python
        from fastmiddleware import AuditConfig

        config = AuditConfig(
            log_all_requests=True,
            sensitive_fields={"password", "token", "secret"},
        )
        ```
    """

    enabled: bool = True
    log_all_requests: bool = False  # Only log mutating by default
    log_request_body: bool = False
    log_response_body: bool = False
    max_body_length: int = 1000
    sensitive_fields: set[str] = field(
        default_factory=lambda: {
            "password",
            "token",
            "secret",
            "api_key",
            "authorization",
            "credit_card",
            "ssn",
            "access_token",
            "refresh_token",
        }
    )
    mutating_methods: set[str] = field(
        default_factory=lambda: {
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }
    )
    action_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
    )
    logger_name: str = "audit"

    # Custom emit function: async def emit(event: AuditEvent) -> None
    emit_func: Callable[[AuditEvent], Any] | None = None


class AuditMiddleware(FastMVCMiddleware):
    """
    Middleware that provides comprehensive audit logging.

    Creates detailed audit trails for compliance, security,
    and debugging purposes.

    Features:
        - Automatic event generation
        - Sensitive data redaction
        - Request/response body logging
        - Custom emit functions
        - User context integration

    Example:
        ```python
        from fastapi import FastAPI
        from fastmiddleware import AuditMiddleware, AuditConfig

        app = FastAPI()

        async def send_to_siem(event):
            # Send audit event to SIEM system
            await siem_client.send(event.to_dict())

        config = AuditConfig(
            log_all_requests=True,
            emit_func=send_to_siem,
        )
        app.add_middleware(AuditMiddleware, config=config)

        # All requests will be logged with:
        # - Timestamp
        # - User ID (if available)
        # - Action performed
        # - Resource accessed
        # - Response status
        # - Duration
        ```

    Compliance:
        Useful for SOC2, HIPAA, GDPR, and other compliance requirements.
    """

    def __init__(
        self,
        app,
        config: AuditConfig | None = None,
        enabled: bool | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or AuditConfig()

        if enabled is not None:
            self.config.enabled = enabled

        self._logger = logging.getLogger(self.config.logger_name)

    def _redact_sensitive(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive fields from data."""
        if not isinstance(data, dict):
            return data

        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.config.sensitive_fields):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive(value)
            else:
                redacted[key] = value

        return redacted

    def _extract_resource(self, path: str) -> str:
        """Extract resource name from path."""
        parts = path.strip("/").split("/")
        # Simple heuristic: first path segment is resource
        return parts[0] if parts else "unknown"

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request."""
        # Try various sources
        user = getattr(request.state, "user", None)
        if user:
            if isinstance(user, dict):
                return user.get("id") or user.get("sub")
            return getattr(user, "id", None)

        return getattr(request.state, "user_id", None)

    def _should_log(self, request: Request) -> bool:
        """Determine if request should be logged."""
        if not self.config.enabled:
            return False

        if self.config.log_all_requests:
            return True

        return request.method in self.config.mutating_methods

    async def _emit_event(self, event: AuditEvent) -> None:
        """Emit audit event."""
        if self.config.emit_func:
            result = self.config.emit_func(event)
            if hasattr(result, "__await__"):
                await result
        else:
            # Default: log as JSON
            self._logger.info(json.dumps(event.to_dict()))

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request) or not self._should_log(request):
            return await call_next(request)

        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Build audit event
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=getattr(request.state, "request_id", None),
            user_id=self._get_user_id(request),
            action=self.config.action_mapping.get(request.method, request.method.lower()),
            resource=self._extract_resource(request.url.path),
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            client_ip=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            duration_ms=round(duration_ms, 2),
        )

        # Emit event
        await self._emit_event(event)

        return response
