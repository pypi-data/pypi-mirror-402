"""
HATEOAS Middleware for FastMVC.

Adds hypermedia links to API responses.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, List, Any

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class Link:
    """Hypermedia link."""
    rel: str
    href: str
    method: str = "GET"
    title: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        d = {"rel": self.rel, "href": self.href, "method": self.method}
        if self.title:
            d["title"] = self.title
        return d


@dataclass
class HATEOASConfig:
    """
    Configuration for HATEOAS middleware.
    
    Attributes:
        links: Dict of path patterns to link generators.
        link_key: Key for links in response.
        self_link: Include self link.
    """
    link_generators: Dict[str, List[Link]] = field(default_factory=dict)
    link_key: str = "_links"
    self_link: bool = True


class HATEOASMiddleware(FastMVCMiddleware):
    """
    Middleware that adds hypermedia links to responses.
    
    Implements HATEOAS (Hypermedia as the Engine of 
    Application State) for REST APIs.
    
    Example:
        ```python
        from FastMiddleware import HATEOASMiddleware, Link
        
        app.add_middleware(
            HATEOASMiddleware,
            link_generators={
                "/api/users": [
                    Link(rel="create", href="/api/users", method="POST"),
                ],
            },
        )
        
        # Responses will include:
        # { "data": {...}, "_links": [...] }
        ```
    """
    
    def __init__(
        self,
        app,
        config: HATEOASConfig | None = None,
        link_generators: Dict[str, List[Link]] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or HATEOASConfig()
        
        if link_generators:
            self.config.link_generators = link_generators
    
    def _get_links(self, path: str, base_url: str) -> List[Dict[str, str]]:
        """Get links for path."""
        links = []
        
        # Add self link
        if self.config.self_link:
            links.append({
                "rel": "self",
                "href": f"{base_url}{path}",
                "method": "GET",
            })
        
        # Get configured links
        for pattern, pattern_links in self.config.link_generators.items():
            if path.startswith(pattern.rstrip("*")):
                for link in pattern_links:
                    link_dict = link.to_dict()
                    # Make href absolute if relative
                    if not link_dict["href"].startswith("http"):
                        link_dict["href"] = f"{base_url}{link_dict['href']}"
                    links.append(link_dict)
        
        return links
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # Only process JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response
        
        if response.status_code >= 400:
            return response
        
        # Get response body
        if hasattr(response, "body"):
            body = response.body
        else:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
        
        if not body:
            return response
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return response
        
        # Add links
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        links = self._get_links(request.url.path, base_url)
        
        if isinstance(data, dict):
            data[self.config.link_key] = links
        elif isinstance(data, list):
            data = {"items": data, self.config.link_key: links}
        
        return JSONResponse(
            content=data,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

