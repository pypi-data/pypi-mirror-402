"""Thermal-related models for /redfish/v1/Chassis/1/Thermal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status


@dataclass(kw_only=True)
class Temperature(BaseModel):
    """Temperature sensor data from Thermal endpoint."""

    member_id: str = ""
    name: str = "Unknown"
    reading_celsius: float | None = None
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    upper_threshold_critical: float | None = None
    upper_threshold_fatal: float | None = None
    upper_threshold_non_critical: float | None = None
    lower_threshold_critical: float | None = None
    lower_threshold_fatal: float | None = None
    lower_threshold_non_critical: float | None = None
    physical_context: str = ""
    sensor_number: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Temperature:
        """Parse from Temperatures array item."""
        instance = cls(
            member_id=data.get("MemberId", ""),
            name=data.get("Name", "Unknown"),
            reading_celsius=data.get("ReadingCelsius"),
            status=Status.from_dict(data.get("Status", {})),
            upper_threshold_critical=data.get("UpperThresholdCritical"),
            upper_threshold_fatal=data.get("UpperThresholdFatal"),
            upper_threshold_non_critical=data.get("UpperThresholdNonCritical"),
            lower_threshold_critical=data.get("LowerThresholdCritical"),
            lower_threshold_fatal=data.get("LowerThresholdFatal"),
            lower_threshold_non_critical=data.get("LowerThresholdNonCritical"),
            physical_context=data.get("PhysicalContext", ""),
            sensor_number=data.get("SensorNumber"),
        )
        instance._is_valid = instance.status.is_enabled
        return instance

    @property
    def is_available(self) -> bool:
        """Check if sensor is available (enabled and has reading)."""
        return self.status.is_enabled and self.reading_celsius is not None


@dataclass(kw_only=True)
class Fan(BaseModel):
    """Fan sensor data from Thermal endpoint."""

    member_id: str = ""
    name: str = "Unknown"
    reading_rpm: int | None = None
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    lower_threshold_critical: int | None = None
    lower_threshold_fatal: int | None = None
    lower_threshold_non_critical: int | None = None
    min_reading_range: int | None = None
    max_reading_range: int | None = None
    physical_context: str = "Fan"
    sensor_number: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fan:
        """Parse from Fans array item."""
        instance = cls(
            member_id=data.get("MemberId", ""),
            name=data.get("Name", "Unknown"),
            reading_rpm=data.get("Reading"),
            status=Status.from_dict(data.get("Status", {})),
            lower_threshold_critical=data.get("LowerThresholdCritical"),
            lower_threshold_fatal=data.get("LowerThresholdFatal"),
            lower_threshold_non_critical=data.get("LowerThresholdNonCritical"),
            min_reading_range=data.get("MinReadingRange"),
            max_reading_range=data.get("MaxReadingRange"),
            physical_context=data.get("PhysicalContext", "Fan"),
            sensor_number=data.get("SensorNumber"),
        )
        instance._is_valid = instance.status.is_enabled
        return instance

    @property
    def is_available(self) -> bool:
        """Check if fan is available (enabled)."""
        return self.status.is_enabled


@dataclass(kw_only=True)
class Thermal(BaseModel):
    """Thermal data from /redfish/v1/Chassis/1/Thermal."""

    id: str = ""
    name: str = ""
    temperatures: list[Temperature] = field(default_factory=list)
    fans: list[Fan] = field(default_factory=list)

    # O(1) lookup dicts
    _temperatures_by_id: dict[str, Temperature] = field(
        default_factory=dict, repr=False, compare=False
    )
    _fans_by_id: dict[str, Fan] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Build lookup indexes after initialization."""
        self._temperatures_by_id = {t.member_id: t for t in self.temperatures}
        self._fans_by_id = {f.member_id: f for f in self.fans}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Thermal:
        """Parse from API response."""
        temperatures = [
            Temperature.from_dict(t) for t in data.get("Temperatures", [])
        ]
        fans = [Fan.from_dict(f) for f in data.get("Fans", [])]

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            temperatures=temperatures,
            fans=fans,
        )
        instance._is_valid = len(temperatures) > 0 or len(fans) > 0
        return instance

    def get_temperature(self, member_id: str) -> Temperature | None:
        """Get temperature sensor by member ID in O(1) time."""
        return self._temperatures_by_id.get(member_id)

    def get_fan(self, member_id: str) -> Fan | None:
        """Get fan sensor by member ID in O(1) time."""
        return self._fans_by_id.get(member_id)

    @property
    def available_temperatures(self) -> list[Temperature]:
        """Get only available temperature sensors."""
        return [t for t in self.temperatures if t.is_available]

    @property
    def available_fans(self) -> list[Fan]:
        """Get only available fans."""
        return [f for f in self.fans if f.is_available]
