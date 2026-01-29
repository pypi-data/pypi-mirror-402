"""OEM (Supermicro-specific) models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .enums import FanModeType


@dataclass(kw_only=True)
class FanMode(BaseModel):
    """Fan mode configuration from OEM endpoint."""

    mode: FanModeType | str = ""
    available_modes: list[FanModeType | str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FanMode:
        """Parse from API response."""
        # Parse current mode
        mode_val = data.get("Mode", "")
        try:
            mode: FanModeType | str = FanModeType(mode_val)
        except ValueError:
            mode = mode_val

        # Parse available modes
        modes_raw = data.get("Mode@Redfish.AllowableValues", [])
        modes: list[FanModeType | str] = []
        for m in modes_raw:
            try:
                modes.append(FanModeType(m))
            except ValueError:
                modes.append(m)

        instance = cls(
            mode=mode,
            available_modes=modes,
        )
        # Valid if we have a mode and available options
        instance._is_valid = bool(mode) and len(modes) > 0
        return instance


@dataclass(kw_only=True)
class NTP(BaseModel):
    """NTP configuration from OEM endpoint."""

    enabled: bool = False
    primary_server: str = ""
    secondary_server: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NTP:
        """Parse from API response."""
        instance = cls(
            enabled=data.get("NTPEnable", False),
            primary_server=data.get("PrimaryNTPServer", ""),
            secondary_server=data.get("SecondaryNTPServer", ""),
        )
        # Always valid - disabled NTP is still valid response
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class LLDP(BaseModel):
    """LLDP configuration from OEM endpoint."""

    enabled: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LLDP:
        """Parse from API response."""
        instance = cls(
            enabled=data.get("LLDPEnabled", False),
        )
        # Always valid
        instance._is_valid = True
        return instance


@dataclass(kw_only=True)
class Snooping(BaseModel):
    """POST code snooping information from OEM endpoint."""

    post_code: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Snooping:
        """Parse from API response."""
        instance = cls(
            post_code=data.get("PostCode", ""),
        )
        # Valid if we have a post code
        instance._is_valid = bool(instance.post_code)
        return instance


@dataclass
class LicenseEntry:
    """Individual license entry."""

    license_id: str = ""
    license_type: str = ""
    license_status: str = ""
    description: str | None = None
    expiration: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LicenseEntry:
        """Parse license entry."""
        return cls(
            license_id=data.get("LicenseID", ""),
            license_type=data.get("LicenseType", ""),
            license_status=data.get("LicenseStatus", ""),
            description=data.get("Description"),
            expiration=data.get("Expiration"),
        )


@dataclass(kw_only=True)
class License(BaseModel):
    """License information from LicenseManager endpoint."""

    is_licensed: bool = False
    licenses: list[LicenseEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> License:
        """Parse from API response."""
        licenses_raw = data.get("Licenses", [])
        licenses = [LicenseEntry.from_dict(lic) for lic in licenses_raw]

        instance = cls(
            is_licensed=len(licenses) > 0,
            licenses=licenses,
        )
        # Always valid - empty list means unlicensed but successful response
        instance._is_valid = True
        return instance
