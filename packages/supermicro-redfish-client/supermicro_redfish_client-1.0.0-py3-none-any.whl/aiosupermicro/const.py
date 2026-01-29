"""Constants for the Supermicro Redfish client."""

from __future__ import annotations

from typing import Final

# Default timeouts
DEFAULT_TIMEOUT: Final = 30  # seconds

# API Root
REDFISH_ROOT: Final = "/redfish/v1"

# Core Endpoints
ENDPOINT_SYSTEMS: Final = f"{REDFISH_ROOT}/Systems/1"
ENDPOINT_CHASSIS: Final = f"{REDFISH_ROOT}/Chassis/1"
ENDPOINT_MANAGERS: Final = f"{REDFISH_ROOT}/Managers/1"

# System Sub-endpoints
ENDPOINT_PROCESSORS: Final = f"{ENDPOINT_SYSTEMS}/Processors"
ENDPOINT_MEMORY: Final = f"{ENDPOINT_SYSTEMS}/Memory"
ENDPOINT_SYSTEM_ETHERNET: Final = f"{ENDPOINT_SYSTEMS}/EthernetInterfaces"

# Chassis Sub-endpoints
ENDPOINT_THERMAL: Final = f"{ENDPOINT_CHASSIS}/Thermal"
ENDPOINT_POWER: Final = f"{ENDPOINT_CHASSIS}/Power"
ENDPOINT_PCIE_DEVICES: Final = f"{ENDPOINT_CHASSIS}/PCIeDevices"

# Manager Sub-endpoints
ENDPOINT_NETWORK_PROTOCOL: Final = f"{ENDPOINT_MANAGERS}/NetworkProtocol"
ENDPOINT_ETHERNET_INTERFACES: Final = f"{ENDPOINT_MANAGERS}/EthernetInterfaces"
ENDPOINT_LICENSE_MANAGER: Final = f"{ENDPOINT_MANAGERS}/LicenseManager"
ENDPOINT_LICENSE_QUERY: Final = f"{ENDPOINT_LICENSE_MANAGER}/QueryLicense"
ENDPOINT_LOG_SERVICES: Final = f"{ENDPOINT_MANAGERS}/LogServices"

# Service Endpoints
ENDPOINT_SESSION_SERVICE: Final = f"{REDFISH_ROOT}/SessionService"
ENDPOINT_SESSIONS: Final = f"{ENDPOINT_SESSION_SERVICE}/Sessions"
ENDPOINT_EVENT_SERVICE: Final = f"{REDFISH_ROOT}/EventService"
ENDPOINT_ACCOUNT_SERVICE: Final = f"{REDFISH_ROOT}/AccountService"
ENDPOINT_UPDATE_SERVICE: Final = f"{REDFISH_ROOT}/UpdateService"

# OEM Endpoints (Supermicro-specific)
ENDPOINT_OEM_FAN_MODE: Final = f"{ENDPOINT_MANAGERS}/Oem/Supermicro/FanMode"
ENDPOINT_OEM_SNOOPING: Final = f"{ENDPOINT_MANAGERS}/Oem/Supermicro/Snooping"
ENDPOINT_OEM_NTP: Final = f"{ENDPOINT_MANAGERS}/Oem/Supermicro/NTP"
ENDPOINT_OEM_LLDP: Final = f"{ENDPOINT_MANAGERS}/Oem/Supermicro/LLDP"

# Session Authentication
AUTH_TOKEN_HEADER: Final = "X-Auth-Token"
SESSION_DEFAULT_TIMEOUT: Final = 300  # 5 minutes (Supermicro default)
SESSION_REFRESH_MARGIN: Final = 30  # Refresh 30s before timeout
SESSION_REFRESH_THRESHOLD: Final = 0.8  # Refresh at 80% of timeout

# Request Management
MAX_CONCURRENT_REQUESTS: Final = 5
