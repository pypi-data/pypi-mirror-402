"""
Multi-Tenancy Middleware for FastMVC.

Provides tenant isolation and context for multi-tenant applications.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any
from contextvars import ContextVar

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


# Context variable for tenant
_tenant_ctx: ContextVar[Dict[str, Any] | None] = ContextVar("tenant", default=None)


def get_tenant() -> Dict[str, Any] | None:
    """
    Get the current tenant context.
    
    Returns:
        Tenant data dict or None.
    
    Example:
        ```python
        from FastMiddleware import get_tenant
        
        @app.get("/data")
        async def get_data():
            tenant = get_tenant()
            tenant_id = tenant.get("id")
            # Query data filtered by tenant_id
        ```
    """
    return _tenant_ctx.get()


def get_tenant_id() -> str | None:
    """Get just the tenant ID."""
    tenant = get_tenant()
    return tenant.get("id") if tenant else None


@dataclass
class TenantConfig:
    """
    Configuration for tenant middleware.
    
    Attributes:
        header_name: Header containing tenant identifier.
        query_param: Query parameter for tenant.
        subdomain_mode: Extract tenant from subdomain.
        path_mode: Extract tenant from path prefix.
        require_tenant: Whether tenant is required.
        tenant_resolver: Function to resolve tenant data.
    
    Example:
        ```python
        from FastMiddleware import TenantConfig
        
        # Header-based
        config = TenantConfig(
            header_name="X-Tenant-ID",
            require_tenant=True,
        )
        
        # Subdomain-based
        config = TenantConfig(
            subdomain_mode=True,
        )
        ```
    """
    
    header_name: str = "X-Tenant-ID"
    query_param: str | None = None
    subdomain_mode: bool = False
    path_mode: bool = False
    path_prefix: str = "/t/"
    require_tenant: bool = False
    
    # Async function to resolve tenant: async def(tenant_id: str) -> dict | None
    tenant_resolver: Callable[[str], Any] | None = None


class TenantMiddleware(FastMVCMiddleware):
    """
    Middleware that provides multi-tenancy support.
    
    Identifies tenants from various sources and provides
    tenant context throughout the request lifecycle.
    
    Tenant Identification:
        - Header: X-Tenant-ID
        - Subdomain: tenant.example.com
        - Path: /t/tenant-id/...
        - Query: ?tenant=tenant-id
    
    Features:
        - Multiple identification methods
        - Custom tenant resolver
        - Context variable access
        - Tenant validation
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import TenantMiddleware, get_tenant
        
        app = FastAPI()
        
        # Header-based tenancy
        app.add_middleware(
            TenantMiddleware,
            require_tenant=True,
        )
        
        @app.get("/users")
        async def get_users():
            tenant = get_tenant()
            # Filter users by tenant["id"]
            return get_users_for_tenant(tenant["id"])
        
        # Subdomain-based tenancy
        app.add_middleware(
            TenantMiddleware,
            subdomain_mode=True,
        )
        # acme.example.com -> tenant_id = "acme"
        ```
    """
    
    def __init__(
        self,
        app,
        config: TenantConfig | None = None,
        header_name: str | None = None,
        require_tenant: bool | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or TenantConfig()
        
        if header_name is not None:
            self.config.header_name = header_name
        if require_tenant is not None:
            self.config.require_tenant = require_tenant
    
    def _extract_from_subdomain(self, request: Request) -> str | None:
        """Extract tenant from subdomain."""
        host = request.headers.get("Host", "")
        parts = host.split(".")
        
        # Need at least: tenant.domain.tld
        if len(parts) >= 3:
            return parts[0]
        
        return None
    
    def _extract_from_path(self, request: Request) -> str | None:
        """Extract tenant from path prefix."""
        path = request.url.path
        prefix = self.config.path_prefix
        
        if path.startswith(prefix):
            rest = path[len(prefix):]
            tenant_end = rest.find("/")
            if tenant_end == -1:
                return rest
            return rest[:tenant_end]
        
        return None
    
    def _extract_tenant_id(self, request: Request) -> str | None:
        """Extract tenant ID from request."""
        # 1. Header
        tenant_id = request.headers.get(self.config.header_name)
        if tenant_id:
            return tenant_id
        
        # 2. Query param
        if self.config.query_param:
            tenant_id = request.query_params.get(self.config.query_param)
            if tenant_id:
                return tenant_id
        
        # 3. Subdomain
        if self.config.subdomain_mode:
            tenant_id = self._extract_from_subdomain(request)
            if tenant_id:
                return tenant_id
        
        # 4. Path
        if self.config.path_mode:
            tenant_id = self._extract_from_path(request)
            if tenant_id:
                return tenant_id
        
        return None
    
    async def _resolve_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Resolve tenant ID to tenant data."""
        if self.config.tenant_resolver:
            result = self.config.tenant_resolver(tenant_id)
            # Handle async resolver
            if hasattr(result, "__await__"):
                return await result
            return result
        
        # Default: just return ID
        return {"id": tenant_id}
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        # Extract tenant ID
        tenant_id = self._extract_tenant_id(request)
        
        if not tenant_id:
            if self.config.require_tenant:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": True,
                        "message": "Tenant identifier required",
                    },
                )
            return await call_next(request)
        
        # Resolve tenant
        tenant_data = await self._resolve_tenant(tenant_id)
        
        if not tenant_data and self.config.require_tenant:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "message": "Tenant not found",
                },
            )
        
        # Set context
        token = _tenant_ctx.set(tenant_data)
        request.state.tenant = tenant_data
        request.state.tenant_id = tenant_id
        
        try:
            response = await call_next(request)
            
            # Add tenant header to response
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
            
            return response
        finally:
            _tenant_ctx.reset(token)

