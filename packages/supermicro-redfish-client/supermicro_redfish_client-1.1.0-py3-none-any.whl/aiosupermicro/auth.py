"""Authentication handling for Supermicro Redfish API."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import BasicAuth

from .const import (
    AUTH_TOKEN_HEADER,
    ENDPOINT_SESSIONS,
    SESSION_DEFAULT_TIMEOUT,
    SESSION_REFRESH_MARGIN,
    SESSION_REFRESH_THRESHOLD,
)
from .exceptions import AuthenticationError

if TYPE_CHECKING:
    from aiohttp import ClientSession, ClientTimeout


@dataclass
class SessionState:
    """Session authentication state.

    Tracks the current session token and its validity.
    """

    token: str | None = None
    session_uri: str | None = None
    created_at: float = 0.0
    timeout_seconds: int = SESSION_DEFAULT_TIMEOUT

    @property
    def is_valid(self) -> bool:
        """Check if session is still valid.

        Returns True if token exists and hasn't expired.
        """
        if not self.token:
            return False
        elapsed = time.monotonic() - self.created_at
        return elapsed < (self.timeout_seconds - SESSION_REFRESH_MARGIN)

    @property
    def needs_refresh(self) -> bool:
        """Check if session needs proactive refresh.

        Returns True if no token or at 80% of timeout.
        """
        if not self.token:
            return True
        elapsed = time.monotonic() - self.created_at
        # Refresh when 80% of timeout has passed
        return elapsed > (self.timeout_seconds * SESSION_REFRESH_THRESHOLD)


class SessionAuth:
    """Session-based authentication handler.

    Manages Redfish session lifecycle with automatic refresh.
    Uses X-Auth-Token header for authentication.
    """

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        username: str,
        password: str,
        *,
        ssl: bool = False,
        timeout: ClientTimeout | None = None,
    ) -> None:
        """Initialize session authentication.

        Args:
            session: aiohttp ClientSession (injected, not owned)
            base_url: Base URL of the BMC (e.g., "https://192.168.1.100")
            username: BMC username
            password: BMC password
            ssl: Whether to verify SSL certificates
            timeout: Request timeout
        """
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._ssl = ssl
        self._timeout = timeout

        # Session state
        self._state = SessionState()
        self._lock = asyncio.Lock()

        # BasicAuth fallback
        self._basic_auth = BasicAuth(username, password)

    @property
    def state(self) -> SessionState:
        """Get current session state (for diagnostics)."""
        return self._state

    async def async_get_headers(self) -> dict[str, str]:
        """Get authentication headers.

        Returns headers with X-Auth-Token if session is valid,
        otherwise returns empty headers (caller uses BasicAuth).
        """
        if self._state.is_valid and self._state.token:
            return {AUTH_TOKEN_HEADER: self._state.token}
        return {}

    def get_basic_auth(self) -> BasicAuth:
        """Get BasicAuth for fallback authentication."""
        return self._basic_auth

    def has_valid_session(self) -> bool:
        """Check if a valid session exists."""
        return self._state.is_valid

    async def async_login(self) -> bool:
        """Create a new session with the BMC.

        Returns:
            True if session was created, False if fallback to BasicAuth needed

        Raises:
            AuthenticationError: If credentials are invalid
        """
        async with self._lock:
            if self._state.is_valid:
                return True

            url = f"{self._base_url}{ENDPOINT_SESSIONS}"
            payload = {
                "UserName": self._username,
                "Password": self._password,
            }

            try:
                async with self._session.post(
                    url,
                    json=payload,
                    ssl=self._ssl,
                    timeout=self._timeout,
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid credentials for session")
                    response.raise_for_status()

                    token = response.headers.get(AUTH_TOKEN_HEADER)
                    location = response.headers.get("Location")

                    if not token:
                        # BMC doesn't support session auth, use BasicAuth
                        return False

                    # Try to get session timeout from response
                    try:
                        data = await response.json()
                        timeout = int(
                            data.get("SessionTimeout", SESSION_DEFAULT_TIMEOUT)
                        )
                    except Exception:
                        timeout = SESSION_DEFAULT_TIMEOUT

                    self._state = SessionState(
                        token=token,
                        session_uri=location,
                        created_at=time.monotonic(),
                        timeout_seconds=timeout,
                    )
                    return True

            except AuthenticationError:
                raise
            except Exception:
                # Session creation failed, caller should use BasicAuth
                return False

    async def async_logout(self) -> None:
        """Delete the current session."""
        async with self._lock:
            if not self._state.session_uri or not self._state.token:
                self._state = SessionState()
                return

            try:
                url = f"{self._base_url}{self._state.session_uri}"
                headers = {AUTH_TOKEN_HEADER: self._state.token}
                async with self._session.delete(
                    url,
                    headers=headers,
                    ssl=self._ssl,
                    timeout=self._timeout,
                ):
                    pass  # Best effort cleanup
            except Exception:
                pass  # Session may be expired
            finally:
                self._state = SessionState()

    def invalidate(self) -> None:
        """Invalidate the current session.

        Call this when receiving 401 to force re-authentication.
        """
        self._state = SessionState()

    async def async_ensure_session(self) -> None:
        """Ensure a valid session exists, creating or refreshing as needed."""
        if self._state.needs_refresh:
            await self.async_login()
