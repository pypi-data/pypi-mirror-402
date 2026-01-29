"""
Referrer-Policy Middleware for FastMVC.

Sets Referrer-Policy header for privacy control.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class ReferrerPolicyConfig:
    """
    Configuration for referrer policy middleware.

    Attributes:
        policy: Referrer policy value.

    Valid policies:
        - no-referrer
        - no-referrer-when-downgrade
        - origin
        - origin-when-cross-origin
        - same-origin
        - strict-origin
        - strict-origin-when-cross-origin
        - unsafe-url
    """

    policy: str = "strict-origin-when-cross-origin"


class ReferrerPolicyMiddleware(FastMVCMiddleware):
    """
    Middleware that sets Referrer-Policy header.

    Controls how much referrer information should be
    included with requests.

    Example:
        ```python
        from FastMiddleware import ReferrerPolicyMiddleware

        app.add_middleware(
            ReferrerPolicyMiddleware,
            policy="strict-origin-when-cross-origin",
        )
        ```
    """

    VALID_POLICIES = {
        "no-referrer",
        "no-referrer-when-downgrade",
        "origin",
        "origin-when-cross-origin",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "unsafe-url",
    }

    def __init__(
        self,
        app,
        config: ReferrerPolicyConfig | None = None,
        policy: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or ReferrerPolicyConfig()

        if policy:
            self.config.policy = policy

        if self.config.policy not in self.VALID_POLICIES:
            raise ValueError(f"Invalid policy: {self.config.policy}")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)

        response = await call_next(request)
        response.headers["Referrer-Policy"] = self.config.policy

        return response
