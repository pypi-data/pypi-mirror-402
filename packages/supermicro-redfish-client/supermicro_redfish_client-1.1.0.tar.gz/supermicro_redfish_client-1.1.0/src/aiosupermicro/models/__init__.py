"""Data models for Supermicro Redfish API responses."""

from __future__ import annotations

from .accounts import Account, AccountService, Role
from .base import BaseModel
from .chassis import (
    Chassis,
    ChassisOem,
    PCIeDevice,
    PCIeInterface,
    PCIeSlot,
    PhysicalSecurity,
)
from .common import OdataResource, Status
from .enums import (
    BootSource,
    BootSourceEnabled,
    ChassisType,
    EventFormatType,
    FanModeType,
    Health,
    IndicatorLED,
    IntrusionSensor,
    ManagerType,
    PowerState,
    Privilege,
    ResetType,
    State,
    SubscriptionType,
    TransferProtocolType,
)
from .events import EventDestination, EventService
from .logs import LogEntry, LogEntryOem
from .manager import (
    EthernetInterface,
    EthernetInterfaceIPv4Address,
    EthernetInterfaceIPv6Address,
    Manager,
    NetworkProtocol,
    ProtocolSettings,
)
from .oem import LLDP, NTP, FanMode, License, LicenseEntry, Snooping
from .power import (
    Battery,
    Power,
    PowerControl,
    PowerLimit,
    PowerMetrics,
    PowerSupply,
    Voltage,
)
from .sessions import Session, SessionService
from .system import (
    Boot,
    Memory,
    MemoryLocation,
    MemorySummary,
    Processor,
    ProcessorCache,
    ProcessorId,
    ProcessorSummary,
    ServiceRoot,
    System,
)
from .thermal import Fan, Temperature, Thermal
from .update import FirmwareInventory, UpdateService

__all__ = [
    # Base
    "BaseModel",
    # Common
    "OdataResource",
    "Status",
    # Enums
    "BootSource",
    "BootSourceEnabled",
    "ChassisType",
    "EventFormatType",
    "FanModeType",
    "Health",
    "IndicatorLED",
    "IntrusionSensor",
    "ManagerType",
    "PowerState",
    "Privilege",
    "ResetType",
    "State",
    "SubscriptionType",
    "TransferProtocolType",
    # System
    "Boot",
    "Memory",
    "MemoryLocation",
    "MemorySummary",
    "Processor",
    "ProcessorCache",
    "ProcessorId",
    "ProcessorSummary",
    "ServiceRoot",
    "System",
    # Chassis
    "Chassis",
    "ChassisOem",
    "PCIeDevice",
    "PCIeInterface",
    "PCIeSlot",
    "PhysicalSecurity",
    # Thermal
    "Fan",
    "Temperature",
    "Thermal",
    # Power
    "Battery",
    "Power",
    "PowerControl",
    "PowerLimit",
    "PowerMetrics",
    "PowerSupply",
    "Voltage",
    # Manager
    "EthernetInterface",
    "EthernetInterfaceIPv4Address",
    "EthernetInterfaceIPv6Address",
    "Manager",
    "NetworkProtocol",
    "ProtocolSettings",
    # Accounts
    "Account",
    "AccountService",
    "Role",
    # Sessions
    "Session",
    "SessionService",
    # Events
    "EventDestination",
    "EventService",
    # Update
    "FirmwareInventory",
    "UpdateService",
    # Logs
    "LogEntry",
    "LogEntryOem",
    # OEM
    "FanMode",
    "License",
    "LicenseEntry",
    "LLDP",
    "NTP",
    "Snooping",
]
