"""Chassis-related models for /redfish/v1/Chassis/1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status
from .enums import ChassisType, IndicatorLED, IntrusionSensor, PowerState


@dataclass(kw_only=True)
class PhysicalSecurity:
    """Physical security (intrusion sensor) information."""

    intrusion_sensor: IntrusionSensor | str = IntrusionSensor.NORMAL
    intrusion_sensor_number: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhysicalSecurity:
        """Parse from PhysicalSecurity object."""
        sensor_val = data.get("IntrusionSensor", "Normal")
        try:
            intrusion_sensor: IntrusionSensor | str = IntrusionSensor(sensor_val)
        except ValueError:
            intrusion_sensor = sensor_val

        return cls(
            intrusion_sensor=intrusion_sensor,
            intrusion_sensor_number=data.get("IntrusionSensorNumber"),
        )

    @property
    def is_intruded(self) -> bool:
        """Check if intrusion is detected."""
        return self.intrusion_sensor != IntrusionSensor.NORMAL


@dataclass(kw_only=True)
class ChassisOem:
    """OEM (Supermicro-specific) chassis information."""

    board_serial_number: str | None = None
    board_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChassisOem:
        """Parse from Oem.Supermicro object."""
        supermicro = data.get("Supermicro", {})
        return cls(
            board_serial_number=supermicro.get("BoardSerialNumber"),
            board_id=supermicro.get("BoardID"),
        )


@dataclass(kw_only=True)
class Chassis(BaseModel):
    """Chassis information from /redfish/v1/Chassis/1."""

    id: str = ""
    name: str = ""
    chassis_type: ChassisType | str = ChassisType.OTHER
    manufacturer: str = "Supermicro"
    model: str | None = None
    serial_number: str | None = None
    power_state: PowerState | str = PowerState.OFF
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    indicator_led: IndicatorLED | str = IndicatorLED.OFF
    physical_security: PhysicalSecurity = field(
        default_factory=lambda: PhysicalSecurity.from_dict({})
    )
    oem: ChassisOem = field(default_factory=lambda: ChassisOem.from_dict({}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chassis:
        """Parse from API response."""
        # Parse chassis type
        type_val = data.get("ChassisType", "Other")
        try:
            chassis_type: ChassisType | str = ChassisType(type_val)
        except ValueError:
            chassis_type = type_val

        # Parse power state
        power_val = data.get("PowerState", "Off")
        try:
            power_state: PowerState | str = PowerState(power_val)
        except ValueError:
            power_state = power_val

        # Parse indicator LED
        led_val = data.get("IndicatorLED", "Off")
        try:
            indicator_led: IndicatorLED | str = IndicatorLED(led_val)
        except ValueError:
            indicator_led = led_val

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            chassis_type=chassis_type,
            manufacturer=data.get("Manufacturer", "Supermicro"),
            model=data.get("Model"),
            serial_number=data.get("SerialNumber"),
            power_state=power_state,
            status=Status.from_dict(data.get("Status", {})),
            indicator_led=indicator_led,
            physical_security=PhysicalSecurity.from_dict(
                data.get("PhysicalSecurity", {})
            ),
            oem=ChassisOem.from_dict(data.get("Oem", {})),
        )

        # Valid if we have chassis type and health
        instance._is_valid = (
            chassis_type != "Unknown" and instance.status.health is not None
        )
        return instance

    @property
    def is_intruded(self) -> bool:
        """Check if chassis intrusion is detected."""
        return self.physical_security.is_intruded

    @property
    def is_healthy(self) -> bool:
        """Check if chassis health is OK."""
        return self.status.is_healthy


@dataclass(kw_only=True)
class PCIeInterface:
    """PCIe interface information."""

    pcie_type: str = ""
    max_pcie_type: str = ""
    lanes_in_use: int = 0
    max_lanes: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PCIeInterface:
        """Parse from PCIeInterface object."""
        return cls(
            pcie_type=data.get("PCIeType", ""),
            max_pcie_type=data.get("MaxPCIeType", ""),
            lanes_in_use=data.get("LanesInUse", 0),
            max_lanes=data.get("MaxLanes", 0),
        )


@dataclass(kw_only=True)
class PCIeSlot:
    """PCIe slot information."""

    slot_type: str = ""
    pcie_type: str = ""
    lanes: int = 0
    location: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PCIeSlot:
        """Parse from Slot object."""
        location = data.get("Location", {}).get("PartLocation", {})
        return cls(
            slot_type=data.get("SlotType", ""),
            pcie_type=data.get("PCIeType", ""),
            lanes=data.get("Lanes", 0),
            location=location.get("ServiceLabel", ""),
        )


@dataclass(kw_only=True)
class PCIeDevice(BaseModel):
    """PCIe device from /redfish/v1/Chassis/1/PCIeDevices/x."""

    id: str = ""
    name: str = ""
    description: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    part_number: str = ""
    device_type: str = ""
    firmware_version: str = ""

    # Status
    status: Status = field(default_factory=lambda: Status.from_dict({}))

    # PCIe Info
    pcie_interface: PCIeInterface = field(
        default_factory=lambda: PCIeInterface.from_dict({})
    )
    slot: PCIeSlot = field(default_factory=lambda: PCIeSlot.from_dict({}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PCIeDevice:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            description=data.get("Description", ""),
            manufacturer=data.get("Manufacturer", ""),
            model=data.get("Model", ""),
            serial_number=data.get("SerialNumber", ""),
            part_number=data.get("PartNumber", ""),
            device_type=data.get("DeviceType", ""),
            firmware_version=data.get("FirmwareVersion", ""),
            status=Status.from_dict(data.get("Status", {})),
            pcie_interface=PCIeInterface.from_dict(data.get("PCIeInterface", {})),
            slot=PCIeSlot.from_dict(data.get("Slot", {})),
        )

        # Valid if we have model
        instance._is_valid = bool(instance.model)
        return instance

    @property
    def is_healthy(self) -> bool:
        """Check if device health is OK."""
        return self.status.is_healthy
