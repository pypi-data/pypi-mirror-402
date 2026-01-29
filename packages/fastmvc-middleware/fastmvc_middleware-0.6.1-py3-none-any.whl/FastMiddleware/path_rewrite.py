"""
Path Rewriting Middleware for FastMVC.

Rewrites request paths based on rules.
"""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class RewriteRule:
    """Path rewrite rule."""

    pattern: str
    replacement: str
    is_regex: bool = False

    def __post_init__(self):
        if self.is_regex:
            self._compiled = re.compile(self.pattern)
        else:
            self._compiled = None

    def apply(self, path: str) -> str | None:
        """Apply rule to path. Returns new path or None if no match."""
        if self.is_regex:
            new_path, count = self._compiled.subn(self.replacement, path)
            return new_path if count > 0 else None
        else:
            if path.startswith(self.pattern):
                return self.replacement + path[len(self.pattern) :]
            return None


@dataclass
class PathRewriteConfig:
    """
    Configuration for path rewrite middleware.

    Attributes:
        rules: List of rewrite rules.
        add_header: Add header with original path.
    """

    rules: list[RewriteRule] = field(default_factory=list)
    add_header: bool = True
    header_name: str = "X-Original-Path"


class PathRewriteMiddleware(FastMVCMiddleware):
    r"""
    Middleware that rewrites request paths.

    Transforms request paths based on configured rules
    before routing.

    Example:
        ```python
        from FastMiddleware import PathRewriteMiddleware, RewriteRule

        app.add_middleware(
            PathRewriteMiddleware,
            rules=[
                RewriteRule("/old-api", "/api/v1"),
                RewriteRule(r"/users/(\d+)", r"/api/users/\1", is_regex=True),
            ],
        )
        ```
    """

    def __init__(
        self,
        app,
        config: PathRewriteConfig | None = None,
        rules: list[RewriteRule] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or PathRewriteConfig()

        if rules:
            self.config.rules = rules

    def _rewrite_path(self, path: str) -> tuple[str, bool]:
        """Apply rewrite rules to path."""
        for rule in self.config.rules:
            new_path = rule.apply(path)
            if new_path is not None:
                return new_path, True
        return path, False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        original_path = request.url.path
        new_path, rewritten = self._rewrite_path(original_path)

        if rewritten:
            # Update scope with new path
            request.scope["path"] = new_path
            request.state.original_path = original_path

        response = await call_next(request)

        if rewritten and self.config.add_header:
            response.headers[self.config.header_name] = original_path

        return response
