"""Event-related models for /redfish/v1/EventService."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .enums import EventFormatType, SubscriptionType


@dataclass(kw_only=True)
class EventService(BaseModel):
    """Event service configuration."""

    id: str = ""
    name: str = ""
    service_enabled: bool = True
    delivery_retry_attempts: int = 3
    delivery_retry_interval_seconds: int = 60
    event_format_types: list[EventFormatType | str] = field(default_factory=list)
    subscription_types: list[SubscriptionType | str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventService:
        """Parse from API response."""
        # Parse event format types
        format_types_raw = data.get("EventFormatTypes", [])
        format_types: list[EventFormatType | str] = []
        for fmt in format_types_raw:
            try:
                format_types.append(EventFormatType(fmt))
            except ValueError:
                format_types.append(fmt)

        # Parse subscription types
        sub_types_raw = data.get("SubscriptionTypes", [])
        sub_types: list[SubscriptionType | str] = []
        for sub in sub_types_raw:
            try:
                sub_types.append(SubscriptionType(sub))
            except ValueError:
                sub_types.append(sub)

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            service_enabled=data.get("ServiceEnabled", True),
            delivery_retry_attempts=data.get("DeliveryRetryAttempts", 3),
            delivery_retry_interval_seconds=data.get(
                "DeliveryRetryIntervalSeconds", 60
            ),
            event_format_types=format_types,
            subscription_types=sub_types,
        )
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class EventDestination(BaseModel):
    """Event subscription from /redfish/v1/EventService/Subscriptions/x."""

    id: str = ""
    name: str = ""
    destination: str = ""
    protocol: str = ""
    subscription_type: SubscriptionType | str = SubscriptionType.REDFISH_EVENT
    context: str = ""
    event_types: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventDestination:
        """Parse from API response."""
        # Parse subscription type
        sub_type_val = data.get("SubscriptionType", "RedfishEvent")
        try:
            sub_type: SubscriptionType | str = SubscriptionType(sub_type_val)
        except ValueError:
            sub_type = sub_type_val

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            destination=data.get("Destination", ""),
            protocol=data.get("Protocol", ""),
            subscription_type=sub_type,
            context=data.get("Context", ""),
            event_types=data.get("EventTypes", []),
        )
        instance._is_valid = bool(instance.destination)
        return instance
