"""Update-related models for /redfish/v1/UpdateService."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status, parse_enum
from .enums import TransferProtocolType


def _parse_enum_list(enum_class: type, values: list[str]) -> list[Any]:
    """Parse list of enum values with fallback to strings."""
    return [parse_enum(enum_class, v) for v in values]


@dataclass(kw_only=True)
class UpdateService(BaseModel):
    """Update service configuration."""

    id: str = ""
    name: str = ""
    service_enabled: bool = True
    http_push_uri: str = ""
    max_image_size_bytes: int | None = None
    transfer_protocol_types: list[TransferProtocolType | str] = field(
        default_factory=list
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UpdateService:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            service_enabled=data.get("ServiceEnabled", True),
            http_push_uri=data.get("HttpPushUri", ""),
            max_image_size_bytes=data.get("MaxImageSizeBytes"),
            transfer_protocol_types=_parse_enum_list(
                TransferProtocolType,
                data.get("TransferProtocol@Redfish.AllowableValues", []),
            ),
        )
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class FirmwareInventory(BaseModel):
    """Firmware inventory item from /redfish/v1/UpdateService/FirmwareInventory/x."""

    id: str = ""
    name: str = ""
    version: str = ""
    updateable: bool = False
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    manufacturer: str | None = None
    release_date: str | None = None
    software_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirmwareInventory:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            version=data.get("Version", ""),
            updateable=data.get("Updateable", False),
            status=Status.from_dict(data.get("Status", {})),
            manufacturer=data.get("Manufacturer"),
            release_date=data.get("ReleaseDate"),
            software_id=data.get("SoftwareId"),
        )
        instance._is_valid = bool(instance.version)
        return instance
