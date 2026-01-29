"""
Bot Detection Middleware for FastMVC.

Detects and handles bot/crawler traffic.
"""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from FastMiddleware.base import FastMVCMiddleware


class BotAction(Enum):
    """Action to take when bot is detected."""

    ALLOW = "allow"
    BLOCK = "block"
    TAG = "tag"  # Just tag the request, don't block
    THROTTLE = "throttle"


@dataclass
class BotConfig:
    """
    Configuration for bot detection middleware.

    Attributes:
        action: What to do when bot is detected.
        allowed_bots: Bot patterns to allow (e.g., googlebot).
        blocked_bots: Bot patterns to block.
        block_empty_ua: Block requests with empty User-Agent.
        bot_patterns: Additional patterns to detect bots.

    Example:
        ```python
        from FastMiddleware import BotConfig, BotAction

        config = BotConfig(
            action=BotAction.TAG,  # Just mark bots, don't block
            allowed_bots={"googlebot", "bingbot"},
        )
        ```
    """

    action: BotAction = BotAction.TAG
    allowed_bots: set[str] = field(
        default_factory=lambda: {
            "googlebot",
            "bingbot",
            "slurp",
            "duckduckbot",
            "baiduspider",
            "yandexbot",
            "facebookexternalhit",
            "twitterbot",
            "linkedinbot",
            "whatsapp",
        }
    )
    blocked_bots: set[str] = field(default_factory=set)
    block_empty_ua: bool = False

    # Common bot patterns
    bot_patterns: list[str] = field(
        default_factory=lambda: [
            r"bot",
            r"spider",
            r"crawl",
            r"scrape",
            r"headless",
            r"phantom",
            r"selenium",
            r"puppeteer",
            r"playwright",
            r"curl",
            r"wget",
            r"python-requests",
            r"httpx",
            r"aiohttp",
            r"axios",
            r"java/",
            r"libwww",
            r"apache-httpclient",
        ]
    )


class BotDetectionMiddleware(FastMVCMiddleware):
    """
    Middleware that detects bot and crawler traffic.

    Identifies bots based on User-Agent patterns and allows
    different handling strategies.

    Features:
        - User-Agent pattern matching
        - Good bot allowlist
        - Bad bot blocklist
        - Flexible actions (allow, block, tag, throttle)

    Example:
        ```python
        from fastapi import FastAPI
        from FastMiddleware import BotDetectionMiddleware, BotAction

        app = FastAPI()

        # Just tag bots (mark in request.state)
        app.add_middleware(
            BotDetectionMiddleware,
            action=BotAction.TAG,
        )

        # Block all bots except search engines
        app.add_middleware(
            BotDetectionMiddleware,
            action=BotAction.BLOCK,
            allowed_bots={"googlebot", "bingbot"},
        )

        @app.get("/")
        async def root(request: Request):
            if request.state.is_bot:
                # Handle bot differently
                pass
        ```
    """

    def __init__(
        self,
        app,
        config: BotConfig | None = None,
        action: BotAction | None = None,
        allowed_bots: set[str] | None = None,
        blocked_bots: set[str] | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the bot detection middleware.

        Args:
            app: The ASGI application.
            config: Bot detection configuration.
            action: Bot action (overrides config).
            allowed_bots: Allowed bots (overrides config).
            blocked_bots: Blocked bots (overrides config).
            exclude_paths: Paths to exclude.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or BotConfig()

        if action is not None:
            self.config.action = action
        if allowed_bots is not None:
            self.config.allowed_bots = allowed_bots
        if blocked_bots is not None:
            self.config.blocked_bots = blocked_bots

        # Compile patterns
        self._bot_pattern = re.compile(
            "|".join(self.config.bot_patterns),
            re.IGNORECASE,
        )

    def _is_bot(self, user_agent: str) -> bool:
        """Check if User-Agent indicates a bot."""
        if not user_agent:
            return self.config.block_empty_ua

        ua_lower = user_agent.lower()
        return bool(self._bot_pattern.search(ua_lower))

    def _get_bot_name(self, user_agent: str) -> str | None:
        """Extract bot name from User-Agent."""
        if not user_agent:
            return None

        ua_lower = user_agent.lower()

        # Check known bots
        for bot in self.config.allowed_bots | self.config.blocked_bots:
            if bot.lower() in ua_lower:
                return bot

        # Try to extract from pattern
        match = self._bot_pattern.search(ua_lower)
        if match:
            return match.group(0)

        return "unknown"

    def _is_allowed_bot(self, bot_name: str | None) -> bool:
        """Check if bot is in the allowed list."""
        if not bot_name:
            return False

        bot_lower = bot_name.lower()
        return any(allowed.lower() in bot_lower for allowed in self.config.allowed_bots)

    def _is_blocked_bot(self, bot_name: str | None) -> bool:
        """Check if bot is in the blocked list."""
        if not bot_name:
            return False

        bot_lower = bot_name.lower()
        return any(blocked.lower() in bot_lower for blocked in self.config.blocked_bots)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with bot detection.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with bot handling.
        """
        if self.should_skip(request):
            return await call_next(request)

        user_agent = request.headers.get("User-Agent", "")
        is_bot = self._is_bot(user_agent)
        bot_name = self._get_bot_name(user_agent) if is_bot else None

        # Store in request state
        request.state.is_bot = is_bot
        request.state.bot_name = bot_name

        # Handle based on action
        if is_bot:
            # Check allowed list first
            if self._is_allowed_bot(bot_name):
                return await call_next(request)

            # Check blocked list
            if self._is_blocked_bot(bot_name):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": True,
                        "message": "Bot access denied",
                    },
                )

            # Apply action
            if self.config.action == BotAction.BLOCK:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": True,
                        "message": "Bot access denied",
                    },
                )

        response = await call_next(request)

        # Add bot detection header
        if is_bot:
            response.headers["X-Bot-Detected"] = "true"
            if bot_name:
                response.headers["X-Bot-Name"] = bot_name

        return response
