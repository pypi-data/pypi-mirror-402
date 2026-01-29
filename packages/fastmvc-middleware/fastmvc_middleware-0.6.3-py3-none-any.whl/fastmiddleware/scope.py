"""
Scope/Permission Middleware for FastMVC.

Validates OAuth scopes and permissions.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class ScopeConfig:
    """
    Configuration for scope middleware.

    Attributes:
        scope_header: Header containing scopes.
        scope_separator: Character separating scopes.
        route_scopes: Required scopes per route.
        require_all: Require all scopes (True) or any (False).
    """

    scope_header: str = "X-Scopes"
    scope_separator: str = " "
    route_scopes: dict[str, list[str]] = field(default_factory=dict)
    require_all: bool = False


class ScopeMiddleware(FastMVCMiddleware):
    """
    Middleware that validates OAuth/permission scopes.

    Checks that requests have required scopes/permissions
    for the requested endpoint.

    Example:
        ```python
        from fastmiddleware import ScopeMiddleware

        app.add_middleware(
            ScopeMiddleware,
            route_scopes={
                "/api/users": ["users:read"],
                "/api/admin": ["admin:all"],
            },
        )

        # Requests must have required scopes in X-Scopes header
        ```
    """

    def __init__(
        self,
        app,
        config: ScopeConfig | None = None,
        route_scopes: dict[str, list[str]] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ScopeConfig()

        if route_scopes:
            self.config.route_scopes = route_scopes

    def _get_scopes(self, request: Request) -> set[str]:
        """Extract scopes from request."""
        scope_str = request.headers.get(self.config.scope_header, "")
        if not scope_str:
            # Try from state (set by auth middleware)
            if hasattr(request.state, "scopes"):
                return set(request.state.scopes)
            return set()

        return set(scope_str.split(self.config.scope_separator))

    def _get_required_scopes(self, path: str) -> set[str]:
        """Get required scopes for path."""
        # Exact match
        if path in self.config.route_scopes:
            return set(self.config.route_scopes[path])

        # Prefix match
        for route, scopes in self.config.route_scopes.items():
            if path.startswith(route):
                return set(scopes)

        return set()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        required = self._get_required_scopes(request.url.path)

        if not required:
            return await call_next(request)

        user_scopes = self._get_scopes(request)

        if self.config.require_all:
            has_access = required.issubset(user_scopes)
        else:
            has_access = bool(required & user_scopes)

        if not has_access:
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "Insufficient permissions",
                    "required_scopes": list(required),
                },
            )

        request.state.scopes = user_scopes
        return await call_next(request)
