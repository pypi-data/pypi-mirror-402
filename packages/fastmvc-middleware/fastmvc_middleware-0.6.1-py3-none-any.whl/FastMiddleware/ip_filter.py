"""
IP Filter Middleware for FastMVC.

Provides IP-based access control with whitelist and blacklist support.
"""

import ipaddress
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


@dataclass
class IPFilterConfig:
    """
    Configuration for IP filter middleware.

    Attributes:
        whitelist: Set of allowed IP addresses/ranges.
        blacklist: Set of blocked IP addresses/ranges.
        whitelist_only: If True, only whitelist IPs are allowed.
        block_response_code: HTTP status code for blocked requests.
        block_message: Message returned for blocked requests.
        trust_proxy: Trust X-Forwarded-For header.

    Example:
        ```python
        from FastMiddleware import IPFilterConfig

        # Whitelist mode
        config = IPFilterConfig(
            whitelist={"192.168.1.0/24", "10.0.0.1"},
            whitelist_only=True,
        )

        # Blacklist mode
        config = IPFilterConfig(
            blacklist={"1.2.3.4", "5.6.7.0/24"},
        )
        ```
    """

    whitelist: set[str] = field(default_factory=set)
    blacklist: set[str] = field(default_factory=set)
    whitelist_only: bool = False
    block_response_code: int = 403
    block_message: str = "Access denied"
    trust_proxy: bool = True


class IPFilterMiddleware(FastMVCMiddleware):
    """
    Middleware that filters requests based on client IP address.

    Supports both whitelist (allow only listed) and blacklist (block listed)
    modes with CIDR range support.

    Features:
        - IP whitelist and blacklist
        - CIDR range support (e.g., 192.168.1.0/24)
        - Proxy-aware IP detection
        - IPv4 and IPv6 support

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import IPFilterMiddleware, IPFilterConfig

        app = FastAPI()

        # Block specific IPs
        config = IPFilterConfig(
            blacklist={"1.2.3.4", "5.6.7.0/24"},
        )
        app.add_middleware(IPFilterMiddleware, config=config)

        # Allow only specific IPs
        config = IPFilterConfig(
            whitelist={"10.0.0.0/8", "192.168.0.0/16"},
            whitelist_only=True,
        )
        app.add_middleware(IPFilterMiddleware, config=config)
        ```
    """

    def __init__(
        self,
        app,
        config: IPFilterConfig | None = None,
        whitelist: set[str] | None = None,
        blacklist: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the IP filter middleware.

        Args:
            app: The ASGI application.
            config: IP filter configuration.
            whitelist: IPs to allow (overrides config).
            blacklist: IPs to block (overrides config).
            exclude_paths: Paths to exclude from filtering.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or IPFilterConfig()

        if whitelist is not None:
            self.config.whitelist = whitelist
            self.config.whitelist_only = True
        if blacklist is not None:
            self.config.blacklist = blacklist

        # Parse IP networks
        self._whitelist_networks = self._parse_networks(self.config.whitelist)
        self._blacklist_networks = self._parse_networks(self.config.blacklist)

    def _parse_networks(
        self, ip_set: set[str]
    ) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        """Parse IP strings into network objects."""
        networks = []
        for ip_str in ip_set:
            try:
                # Try as network first
                networks.append(ipaddress.ip_network(ip_str, strict=False))
            except ValueError:
                try:
                    # Try as single address
                    addr = ipaddress.ip_address(ip_str)
                    if isinstance(addr, ipaddress.IPv4Address):
                        networks.append(ipaddress.ip_network(f"{ip_str}/32"))
                    else:
                        networks.append(ipaddress.ip_network(f"{ip_str}/128"))
                except ValueError:
                    pass  # Invalid IP, skip
        return networks

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if self.config.trust_proxy:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()

            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip

        return request.client.host if request.client else "0.0.0.0"

    def _is_ip_in_networks(
        self, ip_str: str, networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]
    ) -> bool:
        """Check if IP is in any of the networks."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in network for network in networks)
        except ValueError:
            return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with IP filtering.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The HTTP response or 403 if blocked.
        """
        if self.should_skip(request):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Check blacklist first
        if self._is_ip_in_networks(client_ip, self._blacklist_networks):
            return JSONResponse(
                status_code=self.config.block_response_code,
                content={
                    "error": True,
                    "message": self.config.block_message,
                },
            )

        # Check whitelist if in whitelist-only mode
        if self.config.whitelist_only:
            if not self._is_ip_in_networks(client_ip, self._whitelist_networks):
                return JSONResponse(
                    status_code=self.config.block_response_code,
                    content={
                        "error": True,
                        "message": self.config.block_message,
                    },
                )

        return await call_next(request)
