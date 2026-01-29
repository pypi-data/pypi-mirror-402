"""
Bearer Token Authentication Middleware for FastMVC.

Token-based authentication using Bearer tokens.
"""

import secrets
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class BearerAuthConfig:
    """
    Configuration for bearer auth middleware.
    
    Attributes:
        tokens: Dict of token -> user info.
        validate_func: Custom validation function.
        header_name: Authorization header name.
        realm: Authentication realm.
    """
    tokens: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    header_name: str = "Authorization"
    realm: str = "API"
    return_error_detail: bool = False


class BearerAuthMiddleware(FastMVCMiddleware):
    """
    Middleware for Bearer Token Authentication.
    
    Validates Bearer tokens from Authorization header
    and attaches user info to request.
    
    Example:
        ```python
        from FastMiddleware import BearerAuthMiddleware
        
        app.add_middleware(
            BearerAuthMiddleware,
            tokens={
                "token123": {"user_id": 1, "role": "admin"},
                "token456": {"user_id": 2, "role": "user"},
            },
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: BearerAuthConfig | None = None,
        tokens: Dict[str, Dict[str, Any]] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or BearerAuthConfig()
        
        if tokens:
            self.config.tokens = tokens
        
        self._validate_func = None
    
    def set_validate_func(self, func: Callable[[str], Dict[str, Any] | None]) -> None:
        """Set custom token validation function."""
        self._validate_func = func
    
    def _extract_token(self, request: Request) -> str | None:
        """Extract bearer token from request."""
        auth = request.headers.get(self.config.header_name)
        
        if not auth:
            return None
        
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def _validate_token(self, token: str) -> Dict[str, Any] | None:
        """Validate token and return user info."""
        if self._validate_func:
            return self._validate_func(token)
        
        return self.config.tokens.get(token)
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        if request.method == "OPTIONS":
            return await call_next(request)
        
        token = self._extract_token(request)
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Missing authentication token"},
                headers={"WWW-Authenticate": f'Bearer realm="{self.config.realm}"'},
            )
        
        user_info = self._validate_token(token)
        
        if not user_info:
            content = {"error": True, "message": "Invalid token"}
            if self.config.return_error_detail:
                content["detail"] = "Token not found or expired"
            
            return JSONResponse(
                status_code=401,
                content=content,
                headers={"WWW-Authenticate": f'Bearer realm="{self.config.realm}"'},
            )
        
        request.state.user = user_info
        request.state.token = token
        
        return await call_next(request)

