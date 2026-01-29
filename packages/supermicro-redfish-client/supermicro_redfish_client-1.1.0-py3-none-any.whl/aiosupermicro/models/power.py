"""Power-related models for /redfish/v1/Chassis/1/Power."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status


@dataclass(kw_only=True)
class Voltage(BaseModel):
    """Voltage sensor data from Power endpoint."""

    member_id: str = ""
    name: str = "Unknown"
    reading_volts: float | None = None
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    upper_threshold_critical: float | None = None
    upper_threshold_fatal: float | None = None
    upper_threshold_non_critical: float | None = None
    lower_threshold_critical: float | None = None
    lower_threshold_fatal: float | None = None
    lower_threshold_non_critical: float | None = None
    physical_context: str = "VoltageRegulator"
    sensor_number: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Voltage:
        """Parse from Voltages array item."""
        instance = cls(
            member_id=data.get("MemberId", ""),
            name=data.get("Name", "Unknown"),
            reading_volts=data.get("ReadingVolts"),
            status=Status.from_dict(data.get("Status", {})),
            upper_threshold_critical=data.get("UpperThresholdCritical"),
            upper_threshold_fatal=data.get("UpperThresholdFatal"),
            upper_threshold_non_critical=data.get("UpperThresholdNonCritical"),
            lower_threshold_critical=data.get("LowerThresholdCritical"),
            lower_threshold_fatal=data.get("LowerThresholdFatal"),
            lower_threshold_non_critical=data.get("LowerThresholdNonCritical"),
            physical_context=data.get("PhysicalContext", "VoltageRegulator"),
            sensor_number=data.get("SensorNumber"),
        )
        instance._is_valid = instance.status.is_enabled
        return instance

    @property
    def is_available(self) -> bool:
        """Check if voltage sensor is available."""
        return self.status.is_enabled


@dataclass(kw_only=True)
class PowerMetrics:
    """Power metrics from PowerControl."""

    min_consumed_watts: float | None = None
    max_consumed_watts: float | None = None
    average_consumed_watts: float | None = None
    interval_in_min: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PowerMetrics:
        """Parse from PowerMetrics object."""
        return cls(
            min_consumed_watts=data.get("MinConsumedWatts"),
            max_consumed_watts=data.get("MaxConsumedWatts"),
            average_consumed_watts=data.get("AverageConsumedWatts"),
            interval_in_min=data.get("IntervalInMin"),
        )


@dataclass(kw_only=True)
class PowerLimit:
    """Power limit configuration."""

    limit_in_watts: float | None = None
    limit_exception: str | None = None
    correction_in_ms: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PowerLimit:
        """Parse from PowerLimit object."""
        return cls(
            limit_in_watts=data.get("LimitInWatts"),
            limit_exception=data.get("LimitException"),
            correction_in_ms=data.get("CorrectionInMs"),
        )


@dataclass(kw_only=True)
class PowerControl(BaseModel):
    """Power control data from Power endpoint."""

    member_id: str = "0"
    name: str = "Server Power Control"
    power_consumed_watts: float | None = None
    power_capacity_watts: float | None = None
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    power_metrics: PowerMetrics = field(
        default_factory=lambda: PowerMetrics.from_dict({})
    )
    power_limit: PowerLimit = field(default_factory=lambda: PowerLimit.from_dict({}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PowerControl:
        """Parse from PowerControl array item."""
        instance = cls(
            member_id=data.get("MemberId", "0"),
            name=data.get("Name", "Server Power Control"),
            power_consumed_watts=data.get("PowerConsumedWatts"),
            power_capacity_watts=data.get("PowerCapacityWatts"),
            status=Status.from_dict(data.get("Status", {})),
            power_metrics=PowerMetrics.from_dict(data.get("PowerMetrics", {})),
            power_limit=PowerLimit.from_dict(data.get("PowerLimit", {})),
        )
        instance._is_valid = instance.power_consumed_watts is not None
        return instance


@dataclass(kw_only=True)
class PowerSupply(BaseModel):
    """Power supply unit data."""

    member_id: str = ""
    name: str = "Unknown"
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    power_supply_type: str | None = None
    line_input_voltage: float | None = None
    power_capacity_watts: float | None = None
    last_power_output_watts: float | None = None
    model: str | None = None
    manufacturer: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    part_number: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PowerSupply:
        """Parse from PowerSupplies array item."""
        instance = cls(
            member_id=data.get("MemberId", ""),
            name=data.get("Name", "Unknown"),
            status=Status.from_dict(data.get("Status", {})),
            power_supply_type=data.get("PowerSupplyType"),
            line_input_voltage=data.get("LineInputVoltage"),
            power_capacity_watts=data.get("PowerCapacityWatts"),
            last_power_output_watts=data.get("LastPowerOutputWatts"),
            model=data.get("Model"),
            manufacturer=data.get("Manufacturer"),
            firmware_version=data.get("FirmwareVersion"),
            serial_number=data.get("SerialNumber"),
            part_number=data.get("PartNumber"),
        )
        instance._is_valid = instance.status.is_enabled
        return instance

    @property
    def is_available(self) -> bool:
        """Check if PSU is available."""
        return self.status.is_enabled


@dataclass(kw_only=True)
class Battery(BaseModel):
    """CMOS battery information from Power OEM endpoint."""

    name: str = "VBAT"
    health: str = "Unknown"
    state: str = "Unknown"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Battery:
        """Parse from Oem.Supermicro.Battery object."""
        status = data.get("Status", {})
        instance = cls(
            name=data.get("Name", "VBAT"),
            health=status.get("Health", "Unknown"),
            state=status.get("State", "Unknown"),
        )
        instance._is_valid = instance.state != "Unknown"
        return instance

    @property
    def is_healthy(self) -> bool:
        """Check if battery is healthy."""
        return self.health == "OK"


@dataclass(kw_only=True)
class Power(BaseModel):
    """Power data from /redfish/v1/Chassis/1/Power."""

    id: str = ""
    name: str = ""
    power_control: list[PowerControl] = field(default_factory=list)
    voltages: list[Voltage] = field(default_factory=list)
    power_supplies: list[PowerSupply] = field(default_factory=list)
    battery: Battery | None = None

    # O(1) lookup dicts
    _voltages_by_id: dict[str, Voltage] = field(
        default_factory=dict, repr=False, compare=False
    )
    _power_supplies_by_id: dict[str, PowerSupply] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Build lookup indexes after initialization."""
        self._voltages_by_id = {v.member_id: v for v in self.voltages}
        self._power_supplies_by_id = {p.member_id: p for p in self.power_supplies}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Power:
        """Parse from API response."""
        power_control = [
            PowerControl.from_dict(pc) for pc in data.get("PowerControl", [])
        ]
        voltages = [Voltage.from_dict(v) for v in data.get("Voltages", [])]
        power_supplies = [
            PowerSupply.from_dict(ps) for ps in data.get("PowerSupplies", [])
        ]

        # Parse battery from OEM section
        battery_data = data.get("Oem", {}).get("Supermicro", {}).get("Battery", {})
        battery = Battery.from_dict(battery_data) if battery_data else None

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            power_control=power_control,
            voltages=voltages,
            power_supplies=power_supplies,
            battery=battery,
        )
        instance._is_valid = len(power_control) > 0 or len(voltages) > 0
        return instance

    def get_voltage(self, member_id: str) -> Voltage | None:
        """Get voltage sensor by member ID in O(1) time."""
        return self._voltages_by_id.get(member_id)

    def get_power_supply(self, member_id: str) -> PowerSupply | None:
        """Get power supply by member ID in O(1) time."""
        return self._power_supplies_by_id.get(member_id)

    @property
    def available_voltages(self) -> list[Voltage]:
        """Get only available voltage sensors."""
        return [v for v in self.voltages if v.is_available]

    @property
    def available_power_supplies(self) -> list[PowerSupply]:
        """Get only available power supplies."""
        return [ps for ps in self.power_supplies if ps.is_available]

    @property
    def total_power_consumed_watts(self) -> float | None:
        """Get total power consumption in watts."""
        if self.power_control:
            return self.power_control[0].power_consumed_watts
        return None
