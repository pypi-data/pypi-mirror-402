"""
Basic Authentication Middleware for FastMVC.

Simple HTTP Basic Authentication.
"""

import base64
import secrets
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class BasicAuthConfig:
    """
    Configuration for basic auth middleware.
    
    Attributes:
        users: Dict of username -> password.
        realm: Authentication realm.
        exclude_methods: Methods that don't require auth.
    """
    users: Dict[str, str] = field(default_factory=dict)
    realm: str = "Restricted"
    exclude_methods: Set[str] = field(default_factory=lambda: {"OPTIONS"})


class BasicAuthMiddleware(FastMVCMiddleware):
    """
    Middleware for HTTP Basic Authentication.
    
    Simple username/password authentication using
    the Authorization header.
    
    Example:
        ```python
        from FastMiddleware import BasicAuthMiddleware
        
        app.add_middleware(
            BasicAuthMiddleware,
            users={"admin": "secret123", "user": "password"},
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: BasicAuthConfig | None = None,
        users: Dict[str, str] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or BasicAuthConfig()
        
        if users:
            self.config.users = users
    
    def _parse_auth(self, auth_header: str) -> tuple[str, str] | None:
        """Parse Authorization header."""
        if not auth_header.startswith("Basic "):
            return None
        
        try:
            encoded = auth_header[6:]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            return username, password
        except Exception:
            return None
    
    def _verify(self, username: str, password: str) -> bool:
        """Verify credentials."""
        if username not in self.config.users:
            return False
        
        stored = self.config.users[username]
        return secrets.compare_digest(password, stored)
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        if request.method in self.config.exclude_methods:
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": f'Basic realm="{self.config.realm}"'},
            )
        
        credentials = self._parse_auth(auth_header)
        
        if not credentials:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": f'Basic realm="{self.config.realm}"'},
            )
        
        username, password = credentials
        
        if not self._verify(username, password):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": f'Basic realm="{self.config.realm}"'},
            )
        
        request.state.user = username
        return await call_next(request)

