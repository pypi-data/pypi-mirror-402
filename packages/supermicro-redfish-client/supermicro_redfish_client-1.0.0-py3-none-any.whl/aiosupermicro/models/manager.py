"""Manager-related models for /redfish/v1/Managers/1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseModel
from .common import Status
from .enums import ManagerType


@dataclass(kw_only=True)
class ProtocolSettings:
    """Network protocol settings."""

    protocol_enabled: bool = False
    port: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProtocolSettings:
        """Parse protocol settings."""
        return cls(
            protocol_enabled=data.get("ProtocolEnabled", False),
            port=data.get("Port", 0),
        )


@dataclass(kw_only=True)
class NetworkProtocol(BaseModel):
    """Network protocol settings from /redfish/v1/Managers/1/NetworkProtocol."""

    id: str = ""
    name: str = ""
    hostname: str = ""
    fqdn: str = ""
    http: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    https: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    ssh: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    ipmi: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    snmp: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    kvmip: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    virtual_media: ProtocolSettings = field(
        default_factory=lambda: ProtocolSettings.from_dict({})
    )
    ssdp: ProtocolSettings | None = None
    telnet: ProtocolSettings | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkProtocol:
        """Parse from API response."""
        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            hostname=data.get("HostName", ""),
            fqdn=data.get("FQDN", ""),
            http=ProtocolSettings.from_dict(data.get("HTTP", {})),
            https=ProtocolSettings.from_dict(data.get("HTTPS", {})),
            ssh=ProtocolSettings.from_dict(data.get("SSH", {})),
            ipmi=ProtocolSettings.from_dict(data.get("IPMI", {})),
            snmp=ProtocolSettings.from_dict(data.get("SNMP", {})),
            kvmip=ProtocolSettings.from_dict(data.get("KVMIP", {})),
            virtual_media=ProtocolSettings.from_dict(data.get("VirtualMedia", {})),
            ssdp=(
                ProtocolSettings.from_dict(data["SSDP"]) if "SSDP" in data else None
            ),
            telnet=(
                ProtocolSettings.from_dict(data["Telnet"])
                if "Telnet" in data
                else None
            ),
        )
        # Valid if HTTPS port is set (always enabled on BMC)
        instance._is_valid = instance.https.port > 0
        return instance


@dataclass(kw_only=True)
class EthernetInterfaceIPv4Address:
    """IPv4 address configuration."""

    address: str = ""
    subnet_mask: str = ""
    gateway: str = ""
    address_origin: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EthernetInterfaceIPv4Address:
        """Parse IPv4 address."""
        return cls(
            address=data.get("Address", ""),
            subnet_mask=data.get("SubnetMask", ""),
            gateway=data.get("Gateway", ""),
            address_origin=data.get("AddressOrigin", ""),
        )


@dataclass(kw_only=True)
class EthernetInterfaceIPv6Address:
    """IPv6 address configuration."""

    address: str = ""
    prefix_length: int = 0
    address_origin: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EthernetInterfaceIPv6Address:
        """Parse IPv6 address."""
        return cls(
            address=data.get("Address", ""),
            prefix_length=data.get("PrefixLength", 0),
            address_origin=data.get("AddressOrigin", ""),
        )


@dataclass(kw_only=True)
class EthernetInterface(BaseModel):
    """Ethernet interface from /redfish/v1/Managers/1/EthernetInterfaces/x."""

    id: str = ""
    name: str = ""
    mac_address: str = ""
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    ipv4_addresses: list[EthernetInterfaceIPv4Address] = field(default_factory=list)
    ipv6_addresses: list[EthernetInterfaceIPv6Address] = field(default_factory=list)
    speed_mbps: int | None = None
    auto_neg: bool | None = None
    full_duplex: bool | None = None
    hostname: str = ""
    fqdn: str = ""
    vlan_enabled: bool | None = None
    vlan_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EthernetInterface:
        """Parse from API response."""
        ipv4_addresses = [
            EthernetInterfaceIPv4Address.from_dict(addr)
            for addr in data.get("IPv4Addresses", [])
        ]
        ipv6_addresses = [
            EthernetInterfaceIPv6Address.from_dict(addr)
            for addr in data.get("IPv6Addresses", [])
        ]

        vlan = data.get("VLAN", {})

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            mac_address=data.get("MACAddress", ""),
            status=Status.from_dict(data.get("Status", {})),
            ipv4_addresses=ipv4_addresses,
            ipv6_addresses=ipv6_addresses,
            speed_mbps=data.get("SpeedMbps"),
            auto_neg=data.get("AutoNeg"),
            full_duplex=data.get("FullDuplex"),
            hostname=data.get("HostName", ""),
            fqdn=data.get("FQDN", ""),
            vlan_enabled=vlan.get("VLANEnable") if vlan else None,
            vlan_id=vlan.get("VLANId") if vlan else None,
        )
        instance._is_valid = bool(instance.mac_address)
        return instance


@dataclass(kw_only=True)
class Manager(BaseModel):
    """BMC Manager information from /redfish/v1/Managers/1."""

    id: str = ""
    name: str = ""
    manager_type: ManagerType | str = ManagerType.BMC
    uuid: str = ""
    firmware_version: str = "Unknown"
    model: str = "Unknown"
    status: Status = field(default_factory=lambda: Status.from_dict({}))
    date_time: str = ""
    date_time_local_offset: str = ""
    last_reset_time: str = ""
    power_state: str = ""
    service_entry_point_uuid: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manager:
        """Parse from API response."""
        # Parse manager type
        type_val = data.get("ManagerType", "BMC")
        try:
            manager_type: ManagerType | str = ManagerType(type_val)
        except ValueError:
            manager_type = type_val

        instance = cls(
            id=data.get("Id", ""),
            name=data.get("Name", ""),
            manager_type=manager_type,
            uuid=data.get("UUID", ""),
            firmware_version=data.get("FirmwareVersion", "Unknown"),
            model=data.get("Model", "Unknown"),
            status=Status.from_dict(data.get("Status", {})),
            date_time=data.get("DateTime", ""),
            date_time_local_offset=data.get("DateTimeLocalOffset", ""),
            last_reset_time=data.get("LastResetTime", ""),
            power_state=data.get("PowerState", ""),
            service_entry_point_uuid=data.get("ServiceEntryPointUUID"),
        )

        # Valid if we have UUID and firmware version
        instance._is_valid = (
            instance.firmware_version != "Unknown" and bool(instance.uuid)
        )
        return instance

    @property
    def is_healthy(self) -> bool:
        """Check if manager health is OK."""
        return self.status.is_healthy
