"""System-related models for /redfish/v1/Systems/1."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status
from .enums import BootSource, BootSourceEnabled, IndicatorLED, PowerState, ResetType


def _parse_bios_version(raw_version: str) -> str:
    """Parse BIOS version from Supermicro format.

    Supermicro returns: "BIOS Date: MM/DD/YYYY Ver X.X"
    We extract just: "X.X"

    Args:
        raw_version: Raw BIOS version string from API

    Returns:
        Parsed version string (e.g., "2.1") or original if parsing fails
    """
    if match := re.search(r"Ver\s+(\d+(?:\.\d+)*)", raw_version):
        return match.group(1)
    return raw_version


@dataclass(kw_only=True)
class ProcessorSummary:
    """Processor summary information."""

    count: int = 0
    model: str = "Unknown"
    status: Status = field(default_factory=lambda: Status.from_dict({}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessorSummary:
        """Parse from ProcessorSummary object."""
        return cls(
            count=data.get("Count", 0),
            model=data.get("Model", "Unknown"),
            status=Status.from_dict(data.get("Status", {})),
        )


@dataclass(kw_only=True)
class MemorySummary:
    """Memory summary information."""

    total_system_memory_gib: int = 0
    status: Status = field(default_factory=lambda: Status.from_dict({}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemorySummary:
        """Parse from MemorySummary object."""
        return cls(
            total_system_memory_gib=data.get("TotalSystemMemoryGiB", 0),
            status=Status.from_dict(data.get("Status", {})),
        )


@dataclass(kw_only=True)
class Boot:
    """Boot configuration."""

    boot_source_override_target: BootSource | str | None = None
    boot_source_override_enabled: BootSourceEnabled | str = BootSourceEnabled.DISABLED
    boot_source_options: list[str] = field(default_factory=list)
    uefi_target_boot_source_override: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Boot:
        """Parse from Boot object."""
        target_val = data.get("BootSourceOverrideTarget")
        enabled_val = data.get("BootSourceOverrideEnabled", "Disabled")

        # Try to convert to enums
        target: BootSource | str | None = None
        if target_val:
            try:
                target = BootSource(target_val)
            except ValueError:
                target = target_val

        try:
            enabled: BootSourceEnabled | str = BootSourceEnabled(enabled_val)
        except ValueError:
            enabled = enabled_val

        return cls(
            boot_source_override_target=target,
            boot_source_override_enabled=enabled,
            boot_source_options=data.get(
                "BootSourceOverrideTarget@Redfish.AllowableValues", []
            ),
            uefi_target_boot_source_override=data.get("UefiTargetBootSourceOverride"),
        )


@dataclass(kw_only=True)
class System(BaseModel):
    """Computer system information from /redfish/v1/Systems/1."""

    id: str = ""
    name: str = ""
    uuid: str = ""
    manufacturer: str = "Supermicro"
    model: str = "Unknown"
    serial_number: str | None = None
    power_state: PowerState | str = PowerState.OFF
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    bios_version: str = "Unknown"
    indicator_led: IndicatorLED | str = IndicatorLED.OFF
    processor_summary: ProcessorSummary = field(
        default_factory=lambda: ProcessorSummary.from_dict({})
    )
    memory_summary: MemorySummary = field(
        default_factory=lambda: MemorySummary.from_dict({})
    )
    boot: Boot = field(default_factory=lambda: Boot.from_dict({}))
    reset_types: list[ResetType | str] = field(default_factory=list)
    power_on_delay_seconds: int | None = None
    power_off_delay_seconds: int | None = None
    power_cycle_delay_seconds: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> System:
        """Parse from API response."""
        # Parse power state
        power_state_val = data.get("PowerState", "Off")
        try:
            power_state: PowerState | str = PowerState(power_state_val)
        except ValueError:
            power_state = power_state_val

        # Parse indicator LED
        led_val = data.get("IndicatorLED", "Off")
        try:
            indicator_led: IndicatorLED | str = IndicatorLED(led_val)
        except ValueError:
            indicator_led = led_val

        # Parse reset types
        actions = data.get("Actions", {})
        reset_action = actions.get("#ComputerSystem.Reset", {})
        reset_types_raw = reset_action.get("ResetType@Redfish.AllowableValues", [])
        reset_types: list[ResetType | str] = []
        for rt in reset_types_raw:
            try:
                reset_types.append(ResetType(rt))
            except ValueError:
                reset_types.append(rt)

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            uuid=data.get("UUID", ""),
            manufacturer=data.get("Manufacturer", "Supermicro"),
            model=data.get("Model", "Unknown"),
            serial_number=data.get("SerialNumber"),
            power_state=power_state,
            status=Status.from_dict(data.get("Status", {})),
            bios_version=_parse_bios_version(data.get("BiosVersion", "Unknown")),
            indicator_led=indicator_led,
            processor_summary=ProcessorSummary.from_dict(
                data.get("ProcessorSummary", {})
            ),
            memory_summary=MemorySummary.from_dict(data.get("MemorySummary", {})),
            boot=Boot.from_dict(data.get("Boot", {})),
            reset_types=reset_types,
            power_on_delay_seconds=data.get("PowerOnDelaySeconds"),
            power_off_delay_seconds=data.get("PowerOffDelaySeconds"),
            power_cycle_delay_seconds=data.get("PowerCycleDelaySeconds"),
        )

        # Valid if we have UUID and power state
        instance._is_valid = bool(instance.uuid) and instance.power_state != "Unknown"
        return instance

    @property
    def is_on(self) -> bool:
        """Check if system is powered on."""
        return self.power_state == PowerState.ON

    @property
    def is_healthy(self) -> bool:
        """Check if system health is OK."""
        return self.status.is_healthy

    @property
    def total_memory_gib(self) -> int:
        """Get total system memory in GiB."""
        return self.memory_summary.total_system_memory_gib

    @property
    def processor_count(self) -> int:
        """Get processor count."""
        return self.processor_summary.count


@dataclass(kw_only=True)
class ProcessorId:
    """Processor identification information."""

    vendor_id: str = ""
    effective_family: str = ""
    effective_model: str = ""
    step: str = ""
    microcode_info: str = ""
    identification_registers: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessorId:
        """Parse from ProcessorId object."""
        return cls(
            vendor_id=data.get("VendorId", ""),
            effective_family=data.get("EffectiveFamily", ""),
            effective_model=data.get("EffectiveModel", ""),
            step=data.get("Step", ""),
            microcode_info=data.get("MicrocodeInfo", ""),
            identification_registers=data.get("IdentificationRegisters", ""),
        )


@dataclass(kw_only=True)
class ProcessorCache:
    """Processor cache information."""

    cache_type: str = ""
    capacity_mib: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessorCache:
        """Parse from ProcessorMemory object."""
        return cls(
            cache_type=data.get("MemoryType", ""),
            capacity_mib=data.get("CapacityMiB", 0),
        )


@dataclass(kw_only=True)
class Processor(BaseModel):
    """Processor information from /redfish/v1/Systems/1/Processors/x."""

    id: str = ""
    name: str = ""
    socket: str = ""
    model: str = ""
    manufacturer: str = ""
    family: str = ""
    version: str = ""
    part_number: str | None = None
    serial_number: str | None = None

    # Architecture
    processor_type: str = ""
    processor_architecture: str = ""
    instruction_set: str = ""

    # Cores and threads
    total_cores: int = 0
    total_enabled_cores: int = 0
    total_threads: int = 0

    # Speed
    max_speed_mhz: int = 0
    operating_speed_mhz: int = 0

    # Power
    max_tdp_watts: int | None = None

    # Status
    status: Status = field(default_factory=lambda: Status.from_dict({}))

    # Identification
    processor_id: ProcessorId = field(
        default_factory=lambda: ProcessorId.from_dict({})
    )

    # Cache
    caches: list[ProcessorCache] = field(default_factory=list)
    total_cache_mib: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Processor:
        """Parse from API response."""
        # Parse caches
        caches_raw = data.get("ProcessorMemory", [])
        caches = [ProcessorCache.from_dict(c) for c in caches_raw]
        total_cache = sum(c.capacity_mib for c in caches)

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            socket=data.get("Socket", ""),
            model=data.get("Model", ""),
            manufacturer=data.get("Manufacturer", ""),
            family=data.get("Family", ""),
            version=data.get("Version", ""),
            part_number=data.get("PartNumber"),
            serial_number=data.get("SerialNumber"),
            processor_type=data.get("ProcessorType", ""),
            processor_architecture=data.get("ProcessorArchitecture", ""),
            instruction_set=data.get("InstructionSet", ""),
            total_cores=data.get("TotalCores", 0),
            total_enabled_cores=data.get("TotalEnabledCores", 0),
            total_threads=data.get("TotalThreads", 0),
            max_speed_mhz=data.get("MaxSpeedMHz", 0),
            operating_speed_mhz=data.get("OperatingSpeedMHz", 0),
            max_tdp_watts=data.get("MaxTDPWatts"),
            status=Status.from_dict(data.get("Status", {})),
            processor_id=ProcessorId.from_dict(data.get("ProcessorId", {})),
            caches=caches,
            total_cache_mib=total_cache,
        )

        # Valid if we have model and cores
        instance._is_valid = bool(instance.model) and instance.total_cores > 0
        return instance

    @property
    def is_enabled(self) -> bool:
        """Check if processor is enabled."""
        return self.status.is_enabled

    @property
    def is_healthy(self) -> bool:
        """Check if processor health is OK."""
        return self.status.is_healthy


@dataclass(kw_only=True)
class MemoryLocation:
    """Memory DIMM location information."""

    socket: int = 0
    controller: int = 0
    channel: int = 0
    slot: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryLocation:
        """Parse from MemoryLocation object."""
        return cls(
            socket=data.get("Socket", 0),
            controller=data.get("MemoryController", 0),
            channel=data.get("Channel", 0),
            slot=data.get("Slot", 0),
        )


@dataclass(kw_only=True)
class Memory(BaseModel):
    """Memory DIMM information from /redfish/v1/Systems/1/Memory/x."""

    id: str = ""
    name: str = ""
    device_locator: str = ""
    capacity_mib: int = 0
    manufacturer: str = ""
    part_number: str = ""
    serial_number: str = ""

    # Type
    memory_type: str = ""
    memory_device_type: str = ""
    base_module_type: str = ""

    # Speed
    operating_speed_mhz: int = 0
    allowed_speeds_mhz: list[int] = field(default_factory=list)

    # Configuration
    data_width_bits: int = 0
    bus_width_bits: int = 0
    rank_count: int = 0
    error_correction: str = ""

    # Location
    location: MemoryLocation = field(
        default_factory=lambda: MemoryLocation.from_dict({})
    )

    # Status
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            device_locator=data.get("DeviceLocator", ""),
            capacity_mib=data.get("CapacityMiB", 0),
            manufacturer=data.get("Manufacturer", ""),
            part_number=data.get("PartNumber", ""),
            serial_number=data.get("SerialNumber", ""),
            memory_type=data.get("MemoryType", ""),
            memory_device_type=data.get("MemoryDeviceType", ""),
            base_module_type=data.get("BaseModuleType", ""),
            operating_speed_mhz=data.get("OperatingSpeedMhz", 0),
            allowed_speeds_mhz=data.get("AllowedSpeedsMHz", []),
            data_width_bits=data.get("DataWidthBits", 0),
            bus_width_bits=data.get("BusWidthBits", 0),
            rank_count=data.get("RankCount", 0),
            error_correction=data.get("ErrorCorrection", ""),
            location=MemoryLocation.from_dict(data.get("MemoryLocation", {})),
            status=Status.from_dict(data.get("Status", {})),
            enabled=data.get("Enabled", True),
        )

        # Valid if we have capacity
        instance._is_valid = instance.capacity_mib > 0
        return instance

    @property
    def capacity_gib(self) -> int:
        """Get capacity in GiB."""
        return self.capacity_mib // 1024

    @property
    def is_healthy(self) -> bool:
        """Check if memory health is OK."""
        return self.status.is_healthy


@dataclass(kw_only=True)
class ServiceRoot(BaseModel):
    """Redfish Service Root from /redfish/v1."""

    redfish_version: str = ""
    uuid: str = ""
    product: str | None = None
    vendor: str | None = None
    name: str = "Root Service"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceRoot:
        """Parse from API response."""
        instance = cls(
            redfish_version=data.get("RedfishVersion", ""),
            uuid=data.get("UUID", ""),
            product=data.get("Product"),
            vendor=data.get("Vendor"),
            name=data.get("Name", "Root Service"),
        )
        instance._is_valid = bool(instance.redfish_version)
        return instance
