"""Common model structures shared across Redfish resources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar, overload

from .enums import Health, State

E = TypeVar("E", bound=Enum)


@overload
def parse_enum(enum_class: type[E], value: str) -> E | str: ...


@overload
def parse_enum(enum_class: type[E], value: str | None) -> E | str | None: ...


@overload
def parse_enum(enum_class: type[E], value: str | None, default: E) -> E | str: ...


def parse_enum(
    enum_class: type[E], value: str | None, default: E | None = None
) -> E | str | None:
    """Parse enum value with fallback to string.

    Args:
        enum_class: The enum class to parse into
        value: The string value to parse
        default: Default value if value is None

    Returns:
        Enum member if valid, original string if invalid, or default/None
    """
    if value is None:
        return default
    try:
        return enum_class(value)
    except ValueError:
        return value


@dataclass
class Status:
    """Status object used across Redfish resources.

    This is the common Status structure that appears in
    Systems, Chassis, Managers, and sensor readings.
    """

    state: State | str
    health: Health | str | None
    health_rollup: Health | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Status:
        """Parse from Status object in API response."""
        state = parse_enum(State, data.get("State", "Unknown"))
        health = parse_enum(Health, data.get("Health"))
        health_rollup = parse_enum(Health, data.get("HealthRollup"))

        return cls(
            state=state,
            health=health,
            health_rollup=health_rollup,
        )

    @property
    def is_enabled(self) -> bool:
        """Check if resource is enabled."""
        return self.state == State.ENABLED

    @property
    def is_healthy(self) -> bool:
        """Check if health is OK."""
        return self.health == Health.OK


@dataclass
class OdataResource:
    """Base Redfish resource with @odata fields."""

    odata_id: str
    odata_type: str | None = None
    id: str | None = None
    name: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OdataResource:
        """Parse common @odata fields."""
        return cls(
            odata_id=data.get("@odata.id", ""),
            odata_type=data.get("@odata.type"),
            id=data.get("Id"),
            name=data.get("Name"),
            description=data.get("Description"),
        )
