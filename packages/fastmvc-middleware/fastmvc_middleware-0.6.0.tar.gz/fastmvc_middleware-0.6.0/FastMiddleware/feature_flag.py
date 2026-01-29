"""
Feature Flag Middleware for FastMVC.

Provides feature flag and toggle support.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any
from contextvars import ContextVar

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


# Context variable for feature flags
_flags_ctx: ContextVar[Dict[str, bool] | None] = ContextVar("feature_flags", default=None)


def get_feature_flags() -> Dict[str, bool]:
    """
    Get the current feature flags.
    
    Returns:
        Dict of feature flag states.
    
    Example:
        ```python
        from FastMiddleware import get_feature_flags, is_feature_enabled
        
        @app.get("/")
        async def root():
            if is_feature_enabled("new_dashboard"):
                return redirect_to_new_dashboard()
        ```
    """
    return _flags_ctx.get() or {}


def is_feature_enabled(flag: str) -> bool:
    """
    Check if a feature flag is enabled.
    
    Args:
        flag: Feature flag name.
        
    Returns:
        True if enabled, False otherwise.
    """
    flags = get_feature_flags()
    return flags.get(flag, False)


@dataclass
class FeatureFlagConfig:
    """
    Configuration for feature flag middleware.
    
    Attributes:
        flags: Static feature flag values.
        header_overrides: Allow header overrides (for testing).
        override_header: Header name for overrides.
        user_flag_func: Function to get user-specific flags.
    
    Example:
        ```python
        from FastMiddleware import FeatureFlagConfig
        
        config = FeatureFlagConfig(
            flags={
                "new_ui": True,
                "beta_api": False,
                "dark_mode": True,
            },
            header_overrides=True,  # Enable for testing
        )
        ```
    """
    
    flags: Dict[str, bool] = field(default_factory=dict)
    header_overrides: bool = False
    override_header: str = "X-Feature-Flags"
    
    # Function to get dynamic flags (e.g., from database)
    flag_provider: Callable[[Request], Dict[str, bool]] | None = None


class FeatureFlagMiddleware(FastMVCMiddleware):
    """
    Middleware that provides feature flag support.
    
    Enables feature toggles for gradual rollouts, A/B testing,
    and feature gating.
    
    Features:
        - Static flag configuration
        - Header-based overrides (for testing)
        - Dynamic flag providers
        - Context variable access
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import FeatureFlagMiddleware, is_feature_enabled
        
        app = FastAPI()
        
        app.add_middleware(
            FeatureFlagMiddleware,
            flags={
                "new_checkout": True,
                "experimental_api": False,
            },
        )
        
        @app.get("/checkout")
        async def checkout():
            if is_feature_enabled("new_checkout"):
                return new_checkout_flow()
            return old_checkout_flow()
        ```
    
    Testing Override:
        ```bash
        curl -H "X-Feature-Flags: experimental_api=true" ...
        ```
    """
    
    def __init__(
        self,
        app,
        config: FeatureFlagConfig | None = None,
        flags: Dict[str, bool] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        """
        Initialize the feature flag middleware.
        
        Args:
            app: The ASGI application.
            config: Feature flag configuration.
            flags: Static flags (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or FeatureFlagConfig()
        
        if flags is not None:
            self.config.flags = flags
    
    def _parse_header_overrides(self, header: str) -> Dict[str, bool]:
        """Parse feature flag header overrides."""
        overrides = {}
        
        for pair in header.split(","):
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                key = key.strip()
                value = value.strip().lower()
                overrides[key] = value in ("true", "1", "yes", "on")
        
        return overrides
    
    def _get_flags(self, request: Request) -> Dict[str, bool]:
        """Get all feature flags for request."""
        # Start with static flags
        flags = dict(self.config.flags)
        
        # Apply dynamic provider if set
        if self.config.flag_provider:
            dynamic_flags = self.config.flag_provider(request)
            flags.update(dynamic_flags)
        
        # Apply header overrides if enabled
        if self.config.header_overrides:
            override_header = request.headers.get(self.config.override_header, "")
            if override_header:
                overrides = self._parse_header_overrides(override_header)
                flags.update(overrides)
        
        return flags
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with feature flags.
        
        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.
            
        Returns:
            The response with feature flag handling.
        """
        if self.should_skip(request):
            return await call_next(request)
        
        # Get flags
        flags = self._get_flags(request)
        
        # Set context variable
        token = _flags_ctx.set(flags)
        
        # Store in request state
        request.state.feature_flags = flags
        
        try:
            response = await call_next(request)
            
            # Optionally expose enabled flags in header
            enabled = [k for k, v in flags.items() if v]
            if enabled:
                response.headers["X-Features-Enabled"] = ",".join(enabled)
            
            return response
        finally:
            _flags_ctx.reset(token)

