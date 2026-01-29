"""
Permissions-Policy Middleware for FastMVC.

Sets Permissions-Policy header for feature control.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class PermissionsPolicyConfig:
    """
    Configuration for permissions policy middleware.

    Attributes:
        policies: Dict of feature to allowed origins.

    Features include:
        - accelerometer, camera, geolocation, gyroscope
        - magnetometer, microphone, payment, usb
        - fullscreen, autoplay, display-capture, etc.

    Origins can be:
        - self: Same origin
        - *: All origins
        - "https://example.com": Specific origin
        - (): No origins (disabled)
    """

    policies: dict[str, list[str]] = field(
        default_factory=lambda: {
            "accelerometer": [],
            "camera": [],
            "geolocation": [],
            "gyroscope": [],
            "magnetometer": [],
            "microphone": [],
            "payment": [],
            "usb": [],
        }
    )


class PermissionsPolicyMiddleware(FastMVCMiddleware):
    """
    Middleware that sets Permissions-Policy header.

    Controls which browser features and APIs can be
    used in the document.

    Example:
        ```python
        from FastMiddleware import PermissionsPolicyMiddleware

        app.add_middleware(
            PermissionsPolicyMiddleware,
            policies={
                "camera": ["self"],
                "microphone": [],
                "geolocation": ["self", "https://maps.example.com"],
            },
        )
        ```
    """

    def __init__(
        self,
        app,
        config: PermissionsPolicyConfig | None = None,
        policies: dict[str, list[str]] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or PermissionsPolicyConfig()

        if policies:
            self.config.policies.update(policies)

    def _build_header(self) -> str:
        """Build Permissions-Policy header value."""
        parts = []

        for feature, origins in self.config.policies.items():
            if not origins:
                # Disabled
                parts.append(f"{feature}=()")
            elif origins == ["*"]:
                # All origins
                parts.append(f"{feature}=*")
            else:
                # Specific origins
                origin_list = " ".join("self" if o == "self" else f'"{o}"' for o in origins)
                parts.append(f"{feature}=({origin_list})")

        return ", ".join(parts)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        response = await call_next(request)

        policy_header = self._build_header()
        if policy_header:
            response.headers["Permissions-Policy"] = policy_header

        return response
