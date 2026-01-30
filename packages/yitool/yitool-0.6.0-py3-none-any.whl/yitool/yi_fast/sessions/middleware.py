"""Session middleware for FastAPI."""

from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from yitool.yi_fast.sessions.session import SessionManager


class YiSessionMiddleware(BaseHTTPMiddleware):
    """Session middleware for FastAPI."""

    def __init__(
        self,
        app: ASGIApp,
        session_manager: SessionManager | None = None,
        session_cookie_name: str = "session",
        session_max_age: int = 3600,
    ):
        super().__init__(app)
        self._session_manager = session_manager or SessionManager()
        self._session_cookie_name = session_cookie_name
        self._session_max_age = session_max_age

    async def dispatch(self, request: Request, call_next):
        """Process request and add session."""
        session_id = request.cookies.get(self._session_cookie_name)

        if session_id:
            session = await self._session_manager.get_session(session_id)
        else:
            session = {}

        request.state.session = session
        request.state.session_id = session_id

        response = await call_next(request)

        if session_id:
            await self._session_manager.update_session(session_id, session)
        else:
            new_session_id = await self._session_manager.create_session(session)
            response.set_cookie(
                key=self._session_cookie_name,
                value=new_session_id,
                max_age=self._session_max_age,
                httponly=True,
            )

        return response


yi_session_manager = SessionManager()


def yi_get_session(request: Request) -> dict[str, Any]:
    """Get session from request state.

    Args:
        request: FastAPI request

    Returns:
        Session dictionary
    """
    return getattr(request.state, "session", {})


def yi_get_session_id(request: Request) -> str:
    """Get session ID from request state.

    Args:
        request: FastAPI request

    Returns:
        Session ID
    """
    return getattr(request.state, "session_id", "")
