"""
User Agent Parser Middleware for FastMVC.

Parses and normalizes User-Agent headers.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, Any
from contextvars import ContextVar

from starlette.requests import Request
from starlette.responses import Response

from FastMiddleware.base import FastMVCMiddleware


_ua_ctx: ContextVar[Dict[str, Any] | None] = ContextVar("user_agent", default=None)


def get_user_agent() -> Dict[str, Any] | None:
    """Get parsed user agent data."""
    return _ua_ctx.get()


@dataclass
class UserAgentInfo:
    """Parsed user agent information."""
    raw: str
    browser: str = "Unknown"
    browser_version: str = ""
    os: str = "Unknown"
    os_version: str = ""
    device: str = "Unknown"
    is_mobile: bool = False
    is_tablet: bool = False
    is_desktop: bool = True
    is_bot: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.raw,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os": self.os,
            "os_version": self.os_version,
            "device": self.device,
            "is_mobile": self.is_mobile,
            "is_tablet": self.is_tablet,
            "is_desktop": self.is_desktop,
            "is_bot": self.is_bot,
        }


@dataclass
class UserAgentConfig:
    """Configuration for user agent middleware."""
    add_headers: bool = False
    cache_results: bool = True


class UserAgentMiddleware(FastMVCMiddleware):
    """
    Middleware that parses User-Agent headers.
    
    Extracts browser, OS, device, and bot information
    from User-Agent strings.
    
    Example:
        ```python
        from FastMiddleware import UserAgentMiddleware, get_user_agent
        
        app.add_middleware(UserAgentMiddleware)
        
        @app.get("/")
        async def root():
            ua = get_user_agent()
            if ua["is_mobile"]:
                return mobile_response()
            return desktop_response()
        ```
    """
    
    BROWSER_PATTERNS = [
        (r"Chrome/(\d+[\.\d]*)", "Chrome"),
        (r"Firefox/(\d+[\.\d]*)", "Firefox"),
        (r"Safari/(\d+[\.\d]*)", "Safari"),
        (r"Edge/(\d+[\.\d]*)", "Edge"),
        (r"MSIE (\d+[\.\d]*)", "Internet Explorer"),
        (r"Trident/.*rv:(\d+[\.\d]*)", "Internet Explorer"),
        (r"Opera/(\d+[\.\d]*)", "Opera"),
        (r"OPR/(\d+[\.\d]*)", "Opera"),
    ]
    
    OS_PATTERNS = [
        (r"Windows NT (\d+[\.\d]*)", "Windows"),
        (r"Mac OS X (\d+[_\.\d]*)", "macOS"),
        (r"iPhone OS (\d+[_\.\d]*)", "iOS"),
        (r"iPad.*OS (\d+[_\.\d]*)", "iOS"),
        (r"Android (\d+[\.\d]*)", "Android"),
        (r"Linux", "Linux"),
        (r"Ubuntu", "Ubuntu"),
        (r"CrOS", "Chrome OS"),
    ]
    
    MOBILE_PATTERNS = [r"Mobile", r"Android", r"iPhone", r"iPod", r"BlackBerry", r"Windows Phone"]
    TABLET_PATTERNS = [r"iPad", r"Android(?!.*Mobile)", r"Tablet"]
    BOT_PATTERNS = [r"bot", r"crawl", r"spider", r"slurp", r"search"]
    
    def __init__(
        self,
        app,
        config: UserAgentConfig | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or UserAgentConfig()
        self._cache: Dict[str, UserAgentInfo] = {}
    
    def _parse_ua(self, ua_string: str) -> UserAgentInfo:
        """Parse user agent string."""
        if not ua_string:
            return UserAgentInfo(raw="")
        
        if self.config.cache_results and ua_string in self._cache:
            return self._cache[ua_string]
        
        info = UserAgentInfo(raw=ua_string)
        
        # Detect browser
        for pattern, name in self.BROWSER_PATTERNS:
            match = re.search(pattern, ua_string)
            if match:
                info.browser = name
                info.browser_version = match.group(1) if match.groups() else ""
                break
        
        # Detect OS
        for pattern, name in self.OS_PATTERNS:
            match = re.search(pattern, ua_string)
            if match:
                info.os = name
                info.os_version = match.group(1).replace("_", ".") if match.groups() else ""
                break
        
        # Detect device type
        is_mobile = any(re.search(p, ua_string, re.I) for p in self.MOBILE_PATTERNS)
        is_tablet = any(re.search(p, ua_string, re.I) for p in self.TABLET_PATTERNS)
        is_bot = any(re.search(p, ua_string, re.I) for p in self.BOT_PATTERNS)
        
        info.is_mobile = is_mobile and not is_tablet
        info.is_tablet = is_tablet
        info.is_desktop = not is_mobile and not is_tablet and not is_bot
        info.is_bot = is_bot
        
        if info.is_mobile:
            info.device = "Mobile"
        elif info.is_tablet:
            info.device = "Tablet"
        elif info.is_bot:
            info.device = "Bot"
        else:
            info.device = "Desktop"
        
        if self.config.cache_results:
            self._cache[ua_string] = info
        
        return info
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self.should_skip(request):
            return await call_next(request)
        
        ua_string = request.headers.get("User-Agent", "")
        ua_info = self._parse_ua(ua_string)
        
        token = _ua_ctx.set(ua_info.to_dict())
        request.state.user_agent = ua_info
        
        try:
            response = await call_next(request)
            
            if self.config.add_headers:
                response.headers["X-Device-Type"] = ua_info.device
                response.headers["X-Browser"] = ua_info.browser
            
            return response
        finally:
            _ua_ctx.reset(token)

