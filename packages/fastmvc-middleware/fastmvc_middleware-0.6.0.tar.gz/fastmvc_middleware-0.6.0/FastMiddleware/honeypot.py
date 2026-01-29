"""
Honeypot Middleware for FastMVC.

Creates honeypot endpoints to detect and trap malicious requests.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Set, Dict, List
from collections import defaultdict
import logging

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class HoneypotConfig:
    """
    Configuration for honeypot middleware.
    
    Attributes:
        honeypot_paths: Paths that act as honeypots.
        block_on_access: Block IPs that access honeypots.
        block_duration: How long to block in seconds.
        log_access: Log honeypot access.
        fake_response: Response to return for honeypots.
    """
    honeypot_paths: Set[str] = field(default_factory=lambda: {
        "/admin.php",
        "/wp-admin",
        "/wp-login.php",
        "/.env",
        "/config.php",
        "/phpinfo.php",
        "/.git/config",
        "/backup.sql",
        "/db.sql",
        "/api/v1/admin/debug",
    })
    block_on_access: bool = True
    block_duration: int = 3600  # 1 hour
    log_access: bool = True
    fake_delay: float = 2.0  # Delay to waste attacker time
    logger_name: str = "honeypot"


class HoneypotMiddleware(FastMVCMiddleware):
    """
    Middleware that creates honeypot traps for attackers.
    
    Monitors access to fake sensitive endpoints and optionally
    blocks IPs that access them.
    
    Example:
        ```python
        from FastMiddleware import HoneypotMiddleware
        
        app.add_middleware(
            HoneypotMiddleware,
            honeypot_paths={"/admin.php", "/.env", "/wp-admin"},
            block_on_access=True,
        )
        
        # Attackers accessing these paths will be:
        # 1. Logged
        # 2. Delayed (waste their time)
        # 3. Blocked from future requests
        ```
    """
    
    def __init__(
        self,
        app,
        config: HoneypotConfig | None = None,
        honeypot_paths: Set[str] | None = None,
        exclude_paths: Set[str] | None = None,
    ) -> None:
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or HoneypotConfig()
        
        if honeypot_paths:
            self.config.honeypot_paths = honeypot_paths
        
        self._blocked_ips: Dict[str, float] = {}
        self._access_log: List[Dict] = []
        self._logger = logging.getLogger(self.config.logger_name)
    
    def _is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if ip not in self._blocked_ips:
            return False
        
        block_until = self._blocked_ips[ip]
        if time.time() > block_until:
            del self._blocked_ips[ip]
            return False
        
        return True
    
    def _block_ip(self, ip: str) -> None:
        """Block an IP address."""
        self._blocked_ips[ip] = time.time() + self.config.block_duration
    
    def _is_honeypot(self, path: str) -> bool:
        """Check if path is a honeypot."""
        return path in self.config.honeypot_paths or any(
            path.startswith(hp) for hp in self.config.honeypot_paths
        )
    
    def _log_access(self, request: Request) -> None:
        """Log honeypot access."""
        entry = {
            "timestamp": time.time(),
            "ip": self.get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("User-Agent", ""),
        }
        self._access_log.append(entry)
        
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]
        
        self._logger.warning(
            f"Honeypot accessed: {entry['path']} from {entry['ip']}"
        )
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if self._is_blocked(client_ip):
            return JSONResponse(
                status_code=403,
                content={"error": True, "message": "Access denied"},
            )
        
        # Check if this is a honeypot path
        if self._is_honeypot(request.url.path):
            if self.config.log_access:
                self._log_access(request)
            
            if self.config.block_on_access:
                self._block_ip(client_ip)
            
            # Waste attacker's time
            if self.config.fake_delay > 0:
                import asyncio
                await asyncio.sleep(self.config.fake_delay)
            
            # Return fake response
            return JSONResponse(
                status_code=404,
                content={"error": True, "message": "Not found"},
            )
        
        if self.should_skip(request):
            return await call_next(request)
        
        return await call_next(request)

