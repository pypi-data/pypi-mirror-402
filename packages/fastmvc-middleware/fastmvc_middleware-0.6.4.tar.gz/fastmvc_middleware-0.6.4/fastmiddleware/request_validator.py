"""
Request Validator Middleware for FastMVC.

Validates request structure and content.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class ValidationRule:
    """Request validation rule."""

    path: str
    method: str = "*"
    required_headers: list[str] = field(default_factory=list)
    required_query: list[str] = field(default_factory=list)
    content_types: list[str] = field(default_factory=list)
    max_body_size: int | None = None


@dataclass
class RequestValidatorConfig:
    """
    Configuration for request validator middleware.

    Attributes:
        rules: Validation rules.
        strict: Return error on validation failure.
    """

    rules: list[ValidationRule] = field(default_factory=list)
    strict: bool = True


class RequestValidatorMiddleware(FastMVCMiddleware):
    """
    Middleware that validates request structure.

    Checks required headers, query parameters, content types,
    and body size based on configured rules.

    Example:
        ```python
        from fastmiddleware import RequestValidatorMiddleware, ValidationRule

        app.add_middleware(
            RequestValidatorMiddleware,
            rules=[
                ValidationRule(
                    path="/api/upload",
                    method="POST",
                    required_headers=["Content-Type"],
                    content_types=["multipart/form-data"],
                    max_body_size=10 * 1024 * 1024,  # 10MB
                ),
            ],
        )
        ```
    """

    def __init__(
        self,
        app,
        config: RequestValidatorConfig | None = None,
        rules: list[ValidationRule] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RequestValidatorConfig()

        if rules:
            self.config.rules = rules

    def _find_rules(self, path: str, method: str) -> list[ValidationRule]:
        """Find applicable rules for path/method."""
        matching = []
        for rule in self.config.rules:
            if not path.startswith(rule.path):
                continue
            if rule.method != "*" and rule.method.upper() != method:
                continue
            matching.append(rule)
        return matching

    def _validate(self, request: Request, rules: list[ValidationRule]) -> list[str]:
        """Validate request against rules."""
        errors = []

        for rule in rules:
            # Check required headers
            for header in rule.required_headers:
                if header not in request.headers:
                    errors.append(f"Missing required header: {header}")

            # Check required query params
            for param in rule.required_query:
                if param not in request.query_params:
                    errors.append(f"Missing required query parameter: {param}")

            # Check content type
            if rule.content_types:
                content_type = request.headers.get("Content-Type", "")
                if not any(ct in content_type for ct in rule.content_types):
                    errors.append(f"Invalid Content-Type. Expected one of: {rule.content_types}")

            # Check content length
            if rule.max_body_size is not None:
                content_length = request.headers.get("Content-Length")
                if content_length:
                    try:
                        size = int(content_length)
                        if size > rule.max_body_size:
                            errors.append(f"Body too large. Max: {rule.max_body_size} bytes")
                    except ValueError:
                        pass

        return errors

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        rules = self._find_rules(request.url.path, request.method)

        if not rules:
            return await call_next(request)

        errors = self._validate(request, rules)

        if errors and self.config.strict:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Request validation failed",
                    "errors": errors,
                },
            )

        request.state.validation_errors = errors
        return await call_next(request)
