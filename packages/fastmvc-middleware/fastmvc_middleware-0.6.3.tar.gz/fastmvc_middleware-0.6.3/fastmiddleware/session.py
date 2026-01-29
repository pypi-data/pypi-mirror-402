"""
Session Middleware for FastMVC.

Provides server-side session management.
"""

import secrets
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from fastmiddleware.base import FastMVCMiddleware


@dataclass
class SessionConfig:
    """
    Configuration for session middleware.

    Attributes:
        cookie_name: Name of the session cookie.
        max_age: Session max age in seconds.
        cookie_secure: Set Secure flag on cookie.
        cookie_httponly: Set HttpOnly flag on cookie.
        cookie_samesite: SameSite cookie attribute.
        cookie_path: Cookie path.
        cookie_domain: Cookie domain (None for current domain).

    Example:
        ```python
        from fastmiddleware import SessionConfig

        config = SessionConfig(
            max_age=86400,  # 24 hours
            cookie_secure=True,
        )
        ```
    """

    cookie_name: str = "session_id"
    max_age: int = 3600  # 1 hour
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    cookie_path: str = "/"
    cookie_domain: str | None = None


class SessionStore(ABC):
    """
    Abstract base class for session storage backends.

    Implement this to create custom storage (Redis, database, etc.)
    """

    @abstractmethod
    async def get(self, session_id: str) -> dict[str, Any] | None:
        """Get session data by ID."""
        pass

    @abstractmethod
    async def set(self, session_id: str, data: dict[str, Any], max_age: int) -> None:
        """Store session data."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up expired sessions."""
        pass


class InMemorySessionStore(SessionStore):
    """
    In-memory session storage.

    Suitable for development and single-instance deployments.
    For production, use Redis or database storage.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, tuple[dict[str, Any], float]] = {}

    async def get(self, session_id: str) -> dict[str, Any] | None:
        """Get session data."""
        if session_id not in self._sessions:
            return None

        data, expires_at = self._sessions[session_id]

        if time.time() > expires_at:
            del self._sessions[session_id]
            return None

        return data

    async def set(self, session_id: str, data: dict[str, Any], max_age: int) -> None:
        """Store session data."""
        expires_at = time.time() + max_age
        self._sessions[session_id] = (data, expires_at)

    async def delete(self, session_id: str) -> None:
        """Delete session."""
        self._sessions.pop(session_id, None)

    async def cleanup(self) -> None:
        """Clean up expired sessions."""
        now = time.time()
        expired = [sid for sid, (_, expires_at) in self._sessions.items() if now > expires_at]
        for sid in expired:
            del self._sessions[sid]


class Session:
    """
    Session object providing dict-like access to session data.

    Example:
        ```python
        @app.get("/")
        async def root(request: Request):
            session = request.state.session
            session["user_id"] = 123
            username = session.get("username", "Guest")
        ```
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}
        self._modified = False
        self._deleted = False

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._modified = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._modified = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        self._modified = True
        return self._data.pop(key, default)

    def clear(self) -> None:
        """Clear all session data."""
        self._data.clear()
        self._modified = True

    def delete(self) -> None:
        """Mark session for deletion."""
        self._deleted = True
        self._modified = True

    @property
    def data(self) -> dict[str, Any]:
        """Get raw session data."""
        return self._data

    @property
    def modified(self) -> bool:
        """Check if session was modified."""
        return self._modified

    @property
    def deleted(self) -> bool:
        """Check if session was deleted."""
        return self._deleted


class SessionMiddleware(FastMVCMiddleware):
    """
    Middleware that provides server-side session management.

    Sessions are stored server-side with only a session ID in the cookie.

    Features:
        - Server-side session storage
        - Configurable cookie settings
        - Automatic session cleanup
        - Dict-like session access

    Example:
        ```python
        from fastapi import FastAPI, Request
        from fastmiddleware import SessionMiddleware, SessionConfig

        app = FastAPI()

        config = SessionConfig(
            max_age=86400,
            cookie_secure=True,
        )
        app.add_middleware(SessionMiddleware, config=config)

        @app.get("/login")
        async def login(request: Request):
            request.state.session["user_id"] = 123
            return {"logged_in": True}

        @app.get("/profile")
        async def profile(request: Request):
            user_id = request.state.session.get("user_id")
            return {"user_id": user_id}
        ```
    """

    def __init__(
        self,
        app,
        config: SessionConfig | None = None,
        store: SessionStore | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        """
        Initialize the session middleware.

        Args:
            app: The ASGI application.
            config: Session configuration.
            store: Session storage backend.
            exclude_paths: Paths to exclude from sessions.
        """
        super().__init__(app, exclude_paths=exclude_paths)
        self.config = config or SessionConfig()
        self.store = store or InMemorySessionStore()

    def _generate_session_id(self) -> str:
        """Generate a cryptographically secure session ID."""
        return secrets.token_urlsafe(32)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with session management.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware.

        Returns:
            The response with session handling.
        """
        if self.should_skip(request):
            return await call_next(request)

        # Get or create session ID
        session_id = request.cookies.get(self.config.cookie_name)
        is_new_session = False

        # Load existing session or create new
        session_data = None
        if session_id:
            session_data = await self.store.get(session_id)

        if session_data is None:
            session_id = self._generate_session_id()
            session_data = {}
            is_new_session = True

        # Create session object
        session = Session(session_data)
        request.state.session = session

        # Process request
        response = await call_next(request)

        # Handle session after request
        if session.deleted:
            # Delete session
            await self.store.delete(session_id)
            response.delete_cookie(
                key=self.config.cookie_name,
                path=self.config.cookie_path,
                domain=self.config.cookie_domain,
            )
        elif session.modified or is_new_session:
            # Save session
            await self.store.set(session_id, session.data, self.config.max_age)

            # Set cookie
            response.set_cookie(
                key=self.config.cookie_name,
                value=session_id,
                max_age=self.config.max_age,
                httponly=self.config.cookie_httponly,
                secure=self.config.cookie_secure,
                samesite=self.config.cookie_samesite,
                path=self.config.cookie_path,
                domain=self.config.cookie_domain,
            )

        return response
