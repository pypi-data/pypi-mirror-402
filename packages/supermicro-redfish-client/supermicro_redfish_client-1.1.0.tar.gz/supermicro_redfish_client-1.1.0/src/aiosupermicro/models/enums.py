"""Enum definitions for Redfish API values."""

from __future__ import annotations

from enum import StrEnum


class PowerState(StrEnum):
    """System power states."""

    ON = "On"
    OFF = "Off"
    POWERING_ON = "PoweringOn"
    POWERING_OFF = "PoweringOff"


class Health(StrEnum):
    """Health status values."""

    OK = "OK"
    WARNING = "Warning"
    CRITICAL = "Critical"


class State(StrEnum):
    """Resource state values."""

    ENABLED = "Enabled"
    DISABLED = "Disabled"
    ABSENT = "Absent"
    STANDBY_OFFLINE = "StandbyOffline"
    STANDBY_SPARE = "StandbySpare"
    IN_TEST = "InTest"
    STARTING = "Starting"
    UNAVAILABLE_OFFLINE = "UnavailableOffline"
    DEFERRING = "Deferring"
    QUIESCED = "Quiesced"
    UPDATING = "Updating"


class ResetType(StrEnum):
    """System reset types."""

    ON = "On"
    FORCE_OFF = "ForceOff"
    GRACEFUL_SHUTDOWN = "GracefulShutdown"
    GRACEFUL_RESTART = "GracefulRestart"
    FORCE_RESTART = "ForceRestart"
    NMI = "Nmi"
    FORCE_ON = "ForceOn"
    PUSH_POWER_BUTTON = "PushPowerButton"
    POWER_CYCLE = "PowerCycle"


class IndicatorLED(StrEnum):
    """Indicator LED states."""

    OFF = "Off"
    LIT = "Lit"
    BLINKING = "Blinking"
    UNKNOWN = "Unknown"


class BootSource(StrEnum):
    """Boot source targets."""

    NONE = "None"
    PXE = "Pxe"
    HDD = "Hdd"
    CD = "Cd"
    USB = "Usb"
    BIOS_SETUP = "BiosSetup"
    UEFI_TARGET = "UefiTarget"
    UEFI_BOOT_NEXT = "UefiBootNext"
    FLOPPY = "Floppy"
    SD_CARD = "SDCard"
    UEFI_HTTP = "UefiHttp"
    REMOTE_DRIVE = "RemoteDrive"
    DIAGS = "Diags"
    UTILITIES = "Utilities"


class BootSourceEnabled(StrEnum):
    """Boot source override enabled states."""

    DISABLED = "Disabled"
    ONCE = "Once"
    CONTINUOUS = "Continuous"


class IntrusionSensor(StrEnum):
    """Intrusion sensor states."""

    NORMAL = "Normal"
    HARDWARE_INTRUSION = "HardwareIntrusion"
    TAMPERING_DETECTED = "TamperingDetected"


class ChassisType(StrEnum):
    """Chassis type values."""

    RACK = "Rack"
    BLADE = "Blade"
    ENCLOSURE = "Enclosure"
    STAND_ALONE = "StandAlone"
    RACK_MOUNT = "RackMount"
    CARD = "Card"
    CARTRIDGE = "Cartridge"
    ROW = "Row"
    POD = "Pod"
    EXPANSION = "Expansion"
    SIDECAR = "Sidecar"
    ZONE = "Zone"
    SLED = "Sled"
    SHELF = "Shelf"
    DRAWER = "Drawer"
    MODULE = "Module"
    COMPONENT = "Component"
    IP_BASED_DRIVE = "IPBasedDrive"
    RACK_GROUP = "RackGroup"
    STORAGE_ENCLOSURE = "StorageEnclosure"
    OTHER = "Other"


class ManagerType(StrEnum):
    """BMC manager type values."""

    MANAGEMENT_CONTROLLER = "ManagementController"
    ENCLOSURE_MANAGER = "EnclosureManager"
    BMC = "BMC"
    RACK_MANAGER = "RackManager"
    AUXILIARY_CONTROLLER = "AuxiliaryController"
    SERVICE = "Service"


class FanModeType(StrEnum):
    """OEM Fan mode types (Supermicro-specific)."""

    STANDARD = "Standard"
    FULL_SPEED = "FullSpeed"
    OPTIMAL = "Optimal"
    HEAVY_IO = "HeavyIO"
    PUE_OPTIMAL = "PUEOptimal"


class Privilege(StrEnum):
    """Account privilege levels."""

    ADMINISTRATOR = "Administrator"
    OPERATOR = "Operator"
    READ_ONLY = "ReadOnly"
    NO_ACCESS = "NoAccess"


class TransferProtocolType(StrEnum):
    """Firmware update transfer protocols."""

    CIFS = "CIFS"
    FTP = "FTP"
    SFTP = "SFTP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SCP = "SCP"
    TFTP = "TFTP"
    OEM = "OEM"
    NFS = "NFS"


class EventFormatType(StrEnum):
    """Event format types."""

    EVENT = "Event"
    METRIC_REPORT = "MetricReport"


class SubscriptionType(StrEnum):
    """Event subscription types."""

    REDFISH_EVENT = "RedfishEvent"
    SSE = "SSE"
    SNMPTrap = "SNMPTrap"
    SNMPInform = "SNMPInform"
