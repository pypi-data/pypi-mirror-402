"""Async Python client for Supermicro Redfish BMC API.

This library provides an async interface to interact with Supermicro BMC
via the Redfish API. It supports session-based authentication, ETag caching,
request throttling, and comprehensive data models.

Example:
    import asyncio
    from aiohttp import ClientSession
    from aiosupermicro import SupermicroRedfishClient, ResetType

    async def main():
        async with ClientSession() as session:
            client = SupermicroRedfishClient(
                session=session,
                host="192.168.1.100",
                username="ADMIN",
                password="ADMIN",
            )

            await client.async_connect()
            try:
                system = await client.async_get_system()
                print(f"Power: {system.power_state}")

                thermal = await client.async_get_thermal()
                for temp in thermal.available_temperatures:
                    print(f"{temp.name}: {temp.reading_celsius}C")
            finally:
                await client.async_disconnect()

    asyncio.run(main())
"""

from __future__ import annotations

from .client import (
    DynamicData,
    ETagCache,
    RedfishData,
    RequestStats,
    StaticData,
    SupermicroRedfishClient,
)
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    InvalidRequestError,
    InvalidResponseError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    SupermicroRedfishError,
    TimeoutError,
)
from .models import (
    LLDP,
    NTP,
    # Accounts
    Account,
    AccountService,
    # Power
    Battery,
    # System
    Boot,
    # Enums
    BootSource,
    BootSourceEnabled,
    # Chassis
    Chassis,
    ChassisType,
    # Manager
    EthernetInterface,
    # Events
    EventDestination,
    EventFormatType,
    EventService,
    # Thermal
    Fan,
    # OEM
    FanMode,
    FanModeType,
    # Update
    FirmwareInventory,
    Health,
    IndicatorLED,
    IntrusionSensor,
    License,
    Manager,
    ManagerType,
    MemorySummary,
    NetworkProtocol,
    PhysicalSecurity,
    Power,
    PowerControl,
    PowerState,
    PowerSupply,
    Privilege,
    ProcessorSummary,
    ProtocolSettings,
    ResetType,
    Role,
    ServiceRoot,
    # Sessions
    Session,
    SessionService,
    Snooping,
    State,
    # Common
    Status,
    SubscriptionType,
    System,
    Temperature,
    Thermal,
    TransferProtocolType,
    UpdateService,
    Voltage,
)

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Client
    "SupermicroRedfishClient",
    "ETagCache",
    "RequestStats",
    "RedfishData",
    "StaticData",
    "DynamicData",
    # Exceptions
    "SupermicroRedfishError",
    "AuthenticationError",
    "AuthorizationError",
    "ConnectionError",
    "InvalidRequestError",
    "InvalidResponseError",
    "NotFoundError",
    "RateLimitError",
    "ServiceUnavailableError",
    "TimeoutError",
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
    # Common
    "Status",
    # System
    "Boot",
    "MemorySummary",
    "ProcessorSummary",
    "ServiceRoot",
    "System",
    # Chassis
    "Chassis",
    "PhysicalSecurity",
    # Thermal
    "Fan",
    "Temperature",
    "Thermal",
    # Power
    "Battery",
    "Power",
    "PowerControl",
    "PowerSupply",
    "Voltage",
    # Manager
    "EthernetInterface",
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
    # OEM
    "FanMode",
    "License",
    "LLDP",
    "NTP",
    "Snooping",
]
