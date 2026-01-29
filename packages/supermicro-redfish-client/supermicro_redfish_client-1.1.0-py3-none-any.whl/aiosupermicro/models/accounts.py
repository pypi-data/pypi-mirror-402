"""Account-related models for /redfish/v1/AccountService."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import parse_enum
from .enums import Privilege


def _parse_enum_list(enum_class: type, values: list[str]) -> list[Any]:
    """Parse list of enum values with fallback to strings."""
    return [parse_enum(enum_class, v) for v in values]


@dataclass(kw_only=True)
class AccountService(BaseModel):
    """Account service configuration."""

    id: str = ""
    name: str = ""
    service_enabled: bool = True
    auth_failure_logging_threshold: int = 3
    min_password_length: int = 1
    max_password_length: int | None = None
    account_lockout_threshold: int = 0
    account_lockout_duration: int = 0
    account_lockout_counter_reset_after: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountService:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            service_enabled=data.get("ServiceEnabled", True),
            auth_failure_logging_threshold=data.get(
                "AuthFailureLoggingThreshold", 3
            ),
            min_password_length=data.get("MinPasswordLength", 1),
            max_password_length=data.get("MaxPasswordLength"),
            account_lockout_threshold=data.get("AccountLockoutThreshold", 0),
            account_lockout_duration=data.get("AccountLockoutDuration", 0),
            account_lockout_counter_reset_after=data.get(
                "AccountLockoutCounterResetAfter", 0
            ),
        )
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class Account(BaseModel):
    """User account from /redfish/v1/AccountService/Accounts/x."""

    id: str = ""
    name: str = ""
    user_name: str = ""
    enabled: bool = False
    locked: bool = False
    role_id: str = ""
    password_change_required: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Account:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            user_name=data.get("UserName", ""),
            enabled=data.get("Enabled", False),
            locked=data.get("Locked", False),
            role_id=data.get("RoleId", ""),
            password_change_required=data.get("PasswordChangeRequired"),
        )
        instance._is_valid = bool(instance.user_name)
        return instance


@dataclass(kw_only=True)
class Role(BaseModel):
    """Account role from /redfish/v1/AccountService/Roles/x."""

    id: str = ""
    name: str = ""
    is_predefined: bool = False
    assigned_privileges: list[Privilege | str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Role:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            is_predefined=data.get("IsPredefined", False),
            assigned_privileges=_parse_enum_list(
                Privilege, data.get("AssignedPrivileges", [])
            ),
        )
        instance._is_valid = bool(instance.id)
        return instance
