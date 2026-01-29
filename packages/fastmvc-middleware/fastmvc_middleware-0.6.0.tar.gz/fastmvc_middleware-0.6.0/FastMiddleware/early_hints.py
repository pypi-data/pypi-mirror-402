"""
Early Hints (103) Middleware for FastMVC.

Sends HTTP 103 Early Hints for preloading resources.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, List

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class EarlyHint:
    """Early hint resource."""
    url: str
    rel: str = "preload"
    as_type: str | None = None
    crossorigin: bool = False


@dataclass
class EarlyHintsConfig:
    """
    Configuration for early hints middleware.
    
    Attributes:
        hints: Dict of path patterns to hints.
        global_hints: Hints applied to all responses.
    """
    hints: Dict[str, List[EarlyHint]] = field(default_factory=dict)
    global_hints: List[EarlyHint] = field(default_factory=list)


class EarlyHintsMiddleware(FastMVCMiddleware):
    """
    Middleware that adds Link headers for early hints.
    
    While it cannot send 103 responses in ASGI directly,
    it adds Link headers that can be used by proxies/CDNs
    to send early hints.
    
    Example:
        ```python
        from FastMiddleware import EarlyHintsMiddleware, EarlyHint
        
        app.add_middleware(
            EarlyHintsMiddleware,
            global_hints=[
                EarlyHint("/static/css/main.css", as_type="style"),
                EarlyHint("/static/js/app.js", as_type="script"),
            ],
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: EarlyHintsConfig | None = None,
        global_hints: List[EarlyHint] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or EarlyHintsConfig()
        
        if global_hints:
            self.config.global_hints = global_hints
    
    def _build_link_header(self, hints: List[EarlyHint]) -> str:
        """Build Link header value."""
        parts = []
        
        for hint in hints:
            link = f"<{hint.url}>; rel={hint.rel}"
            if hint.as_type:
                link += f"; as={hint.as_type}"
            if hint.crossorigin:
                link += "; crossorigin"
            parts.append(link)
        
        return ", ".join(parts)
    
    def _get_hints(self, path: str) -> List[EarlyHint]:
        """Get hints for path."""
        hints = list(self.config.global_hints)
        
        for pattern, path_hints in self.config.hints.items():
            if path.startswith(pattern):
                hints.extend(path_hints)
        
        return hints
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        hints = self._get_hints(request.url.path)
        
        if hints:
            link_header = self._build_link_header(hints)
            existing = response.headers.get("Link")
            if existing:
                response.headers["Link"] = f"{existing}, {link_header}"
            else:
                response.headers["Link"] = link_header
        
        return response

