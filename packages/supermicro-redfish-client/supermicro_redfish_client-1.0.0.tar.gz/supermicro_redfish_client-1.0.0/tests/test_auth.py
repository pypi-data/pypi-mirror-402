"""Tests for authentication module."""

from __future__ import annotations

import time

import pytest
from aiohttp import ClientSession, ClientTimeout
from aioresponses import aioresponses

from aiosupermicro.auth import SessionAuth, SessionState
from aiosupermicro.exceptions import AuthenticationError


class TestSessionState:
    """Tests for SessionState dataclass."""

    def test_initial_state(self) -> None:
        """Test initial state is invalid."""
        state = SessionState()

        assert state.token is None
        assert state.session_uri is None
        assert state.is_valid is False
        assert state.needs_refresh is True

    def test_valid_session(self) -> None:
        """Test valid session state."""
        state = SessionState(
            token="test-token",
            session_uri="/redfish/v1/SessionService/Sessions/1",
            created_at=time.monotonic(),
            timeout_seconds=300,
        )

        assert state.is_valid is True
        assert state.needs_refresh is False

    def test_expired_session(self) -> None:
        """Test expired session state."""
        state = SessionState(
            token="test-token",
            session_uri="/redfish/v1/SessionService/Sessions/1",
            created_at=time.monotonic() - 300,  # 5 minutes ago
            timeout_seconds=300,
        )

        assert state.is_valid is False
        assert state.needs_refresh is True

    def test_needs_refresh_at_80_percent(self) -> None:
        """Test needs_refresh at 80% of timeout."""
        state = SessionState(
            token="test-token",
            session_uri="/redfish/v1/SessionService/Sessions/1",
            created_at=time.monotonic() - 245,  # 81% of 300s
            timeout_seconds=300,
        )

        assert state.is_valid is True  # Still valid (< timeout - margin)
        assert state.needs_refresh is True  # Needs refresh (> 80%)


class TestSessionAuth:
    """Tests for SessionAuth class."""

    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        """Test successful login."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={"SessionTimeout": 300},
                headers={
                    "X-Auth-Token": "test-token",
                    "Location": "/redfish/v1/SessionService/Sessions/1",
                },
            )

            async with ClientSession() as session:
                auth = SessionAuth(
                    session=session,
                    base_url="https://192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                    ssl=False,
                    timeout=ClientTimeout(total=30),
                )

                result = await auth.async_login()

                assert result is True
                assert auth.has_valid_session() is True
                assert auth.state.token == "test-token"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                status=401,
            )

            async with ClientSession() as session:
                auth = SessionAuth(
                    session=session,
                    base_url="https://192.168.1.100",
                    username="ADMIN",
                    password="wrong",
                    ssl=False,
                )

                with pytest.raises(AuthenticationError):
                    await auth.async_login()

    @pytest.mark.asyncio
    async def test_login_no_token_fallback(self) -> None:
        """Test fallback when no token in response."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={},  # No X-Auth-Token
            )

            async with ClientSession() as session:
                auth = SessionAuth(
                    session=session,
                    base_url="https://192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                    ssl=False,
                )

                result = await auth.async_login()

                assert result is False  # Fallback to BasicAuth
                assert auth.has_valid_session() is False

    @pytest.mark.asyncio
    async def test_logout(self) -> None:
        """Test logout."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={
                    "X-Auth-Token": "test-token",
                    "Location": "/redfish/v1/SessionService/Sessions/1",
                },
            )
            m.delete(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions/1",
                status=200,
            )

            async with ClientSession() as session:
                auth = SessionAuth(
                    session=session,
                    base_url="https://192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                    ssl=False,
                )

                await auth.async_login()
                assert auth.has_valid_session() is True

                await auth.async_logout()
                assert auth.has_valid_session() is False

    @pytest.mark.asyncio
    async def test_get_headers_with_session(self) -> None:
        """Test getting headers with valid session."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )

            async with ClientSession() as session:
                auth = SessionAuth(
                    session=session,
                    base_url="https://192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                    ssl=False,
                )

                await auth.async_login()
                headers = await auth.async_get_headers()

                assert "X-Auth-Token" in headers
                assert headers["X-Auth-Token"] == "test-token"

    @pytest.mark.asyncio
    async def test_get_headers_without_session(self) -> None:
        """Test getting headers without session."""
        async with ClientSession() as session:
            auth = SessionAuth(
                session=session,
                base_url="https://192.168.1.100",
                username="ADMIN",
                password="ADMIN",
                ssl=False,
            )

            headers = await auth.async_get_headers()

            assert headers == {}

    def test_invalidate(self) -> None:
        """Test session invalidation."""
        auth = SessionAuth.__new__(SessionAuth)
        auth._state = SessionState(
            token="test-token",
            session_uri="/session/1",
            created_at=time.monotonic(),
        )

        auth.invalidate()

        assert auth.has_valid_session() is False

    @pytest.mark.asyncio
    async def test_get_basic_auth(self) -> None:
        """Test getting BasicAuth."""
        async with ClientSession() as session:
            auth = SessionAuth(
                session=session,
                base_url="https://192.168.1.100",
                username="ADMIN",
                password="SECRET",
                ssl=False,
            )

            basic_auth = auth.get_basic_auth()

            assert basic_auth.login == "ADMIN"
            assert basic_auth.password == "SECRET"
