"""
Redirect Middleware for FastMVC.

Handles URL redirects and rewrites.
"""

from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, List
import re

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class RedirectRule:
    """A redirect rule."""
    
    source: str  # Path or pattern
    destination: str  # Target URL
    code: int = 301  # Redirect status code
    is_regex: bool = False  # Whether source is a regex
    preserve_query: bool = True  # Preserve query string


@dataclass
class RedirectConfig:
    """
    Configuration for redirect middleware.
    
    Attributes:
        rules: List of redirect rules.
        permanent_redirects: Simple path -> path permanent redirects.
        temporary_redirects: Simple path -> path temporary redirects.
    
    Example:
        ```python
        from FastMiddleware import RedirectConfig, RedirectRule
        
        config = RedirectConfig(
            rules=[
                RedirectRule("/old-page", "/new-page"),
                RedirectRule(r"/blog/(\\d+)", "/posts/\\1", is_regex=True),
            ],
            permanent_redirects={
                "/about-us": "/about",
            },
        )
        ```
    """
    
    rules: List[RedirectRule] = field(default_factory=list)
    permanent_redirects: Dict[str, str] = field(default_factory=dict)
    temporary_redirects: Dict[str, str] = field(default_factory=dict)


class RedirectMiddleware(FastMVCMiddleware):
    """
    Middleware that handles URL redirects.
    
    Redirects requests based on configured rules, supporting
    both simple path matching and regex patterns.
    
    Features:
        - Simple path redirects
        - Regex-based redirects
        - Permanent (301) and temporary (302) redirects
        - Query string preservation
        - Capture group substitution
    
    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import RedirectMiddleware, RedirectRule
        
        app = FastAPI()
        
        app.add_middleware(
            RedirectMiddleware,
            rules=[
                # Simple redirect
                RedirectRule("/old", "/new"),
                
                # Regex with capture group
                RedirectRule(
                    r"/users/(\\d+)/profile",
                    "/profiles/\\1",
                    is_regex=True,
                ),
                
                # Temporary redirect
                RedirectRule("/promo", "/sale", code=302),
            ],
        )
        ```
    """
    
    def __init__(
        self,
        app,
        config: RedirectConfig | None = None,
        rules: List[RedirectRule] | None = None,
        permanent_redirects: Dict[str, str] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or RedirectConfig()
        
        if rules is not None:
            self.config.rules = rules
        if permanent_redirects is not None:
            self.config.permanent_redirects = permanent_redirects
        
        # Compile regex patterns
        self._compiled_rules = []
        for rule in self.config.rules:
            if rule.is_regex:
                self._compiled_rules.append((re.compile(rule.source), rule))
            else:
                self._compiled_rules.append((None, rule))
    
    def _find_redirect(self, path: str) -> tuple[str, int] | None:
        """Find redirect destination for path."""
        # Check simple permanent redirects
        if path in self.config.permanent_redirects:
            return self.config.permanent_redirects[path], 301
        
        # Check simple temporary redirects
        if path in self.config.temporary_redirects:
            return self.config.temporary_redirects[path], 302
        
        # Check rules
        for pattern, rule in self._compiled_rules:
            if pattern:  # Regex rule
                match = pattern.match(path)
                if match:
                    # Substitute capture groups
                    destination = rule.destination
                    for i, group in enumerate(match.groups(), 1):
                        destination = destination.replace(f"\\{i}", group or "")
                    return destination, rule.code
            else:  # Simple path rule
                if path == rule.source:
                    return rule.destination, rule.code
        
        return None
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        path = request.url.path
        redirect = self._find_redirect(path)
        
        if redirect:
            destination, code = redirect
            
            # Preserve query string
            if request.url.query:
                if "?" in destination:
                    destination = f"{destination}&{request.url.query}"
                else:
                    destination = f"{destination}?{request.url.query}"
            
            return RedirectResponse(url=destination, status_code=code)
        
        return await call_next(request)

