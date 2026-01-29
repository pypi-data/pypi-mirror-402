"""
Input Sanitization Middleware for FastMVC.

Sanitizes request data to prevent injection attacks.
"""

import html
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class SanitizationConfig:
    """
    Configuration for sanitization middleware.

    Attributes:
        sanitize_query: Sanitize query parameters.
        sanitize_headers: Sanitize specific headers.
        escape_html: Escape HTML entities.
        strip_tags: Remove HTML tags.
        remove_null_bytes: Remove null bytes.
        trim_whitespace: Trim leading/trailing whitespace.
        max_string_length: Max length for string values.
        blocked_patterns: Regex patterns to block.
    """

    sanitize_query: bool = True
    sanitize_headers: set[str] = field(default_factory=set)
    escape_html: bool = True
    strip_tags: bool = True
    remove_null_bytes: bool = True
    trim_whitespace: bool = True
    max_string_length: int = 10000
    blocked_patterns: list[str] = field(
        default_factory=lambda: [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]
    )


class SanitizationMiddleware(FastMVCMiddleware):
    """
    Middleware that sanitizes input data.

    Cleans and validates input to prevent XSS, injection,
    and other attacks.

    Example:
        ```python
        from fastmiddleware import SanitizationMiddleware

        app.add_middleware(
            SanitizationMiddleware,
            strip_tags=True,
            escape_html=True,
        )

        # All query params will be sanitized
        # <script>alert('xss')</script> becomes safe text
        ```
    """

    TAG_PATTERN = re.compile(r"<[^>]+>")

    def __init__(
        self,
        app,
        config: SanitizationConfig | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or SanitizationConfig()

        self._blocked_patterns = [
            re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.config.blocked_patterns
        ]

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return value

        # Remove null bytes
        if self.config.remove_null_bytes:
            value = value.replace("\x00", "")

        # Trim whitespace
        if self.config.trim_whitespace:
            value = value.strip()

        # Truncate long strings
        if len(value) > self.config.max_string_length:
            value = value[: self.config.max_string_length]

        # Strip HTML tags
        if self.config.strip_tags:
            value = self.TAG_PATTERN.sub("", value)

        # Escape HTML
        if self.config.escape_html:
            value = html.escape(value)

        # Remove blocked patterns
        for pattern in self._blocked_patterns:
            value = pattern.sub("", value)

        return value

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize dictionary values."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_string(v) if isinstance(v, str) else v for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        # Sanitize query params (stored for access)
        if self.config.sanitize_query:
            sanitized_query = {}
            for key, value in request.query_params.items():
                sanitized_query[key] = self._sanitize_string(value)
            request.state.sanitized_query = sanitized_query

        return await call_next(request)
