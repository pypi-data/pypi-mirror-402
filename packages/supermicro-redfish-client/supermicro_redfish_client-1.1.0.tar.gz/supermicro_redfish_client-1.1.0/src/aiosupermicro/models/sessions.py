"""Session-related models for /redfish/v1/SessionService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import BaseModel


@dataclass(kw_only=True)
class SessionService(BaseModel):
    """Session service configuration."""

    id: str = ""
    name: str = ""
    service_enabled: bool = True
    session_timeout: int = 300

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionService:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            service_enabled=data.get("ServiceEnabled", True),
            session_timeout=data.get("SessionTimeout", 300),
        )
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class Session(BaseModel):
    """Active session from /redfish/v1/SessionService/Sessions/x."""

    id: str = ""
    name: str = ""
    user_name: str = ""
    session_type: str | None = None
    created_time: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            user_name=data.get("UserName", ""),
            session_type=data.get("SessionType"),
            created_time=data.get("CreatedTime"),
        )
        instance._is_valid = bool(instance.id)
        return instance
