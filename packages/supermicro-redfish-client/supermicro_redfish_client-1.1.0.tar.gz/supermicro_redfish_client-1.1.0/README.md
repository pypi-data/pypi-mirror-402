# supermicro-redfish-client

Async Python client library for the Supermicro Redfish BMC API.

[![PyPI version](https://badge.fury.io/py/supermicro-redfish-client.svg)](https://badge.fury.io/py/supermicro-redfish-client)
[![Python](https://img.shields.io/pypi/pyversions/supermicro-redfish-client.svg)](https://pypi.org/project/supermicro-redfish-client/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Features

- **Async-first**: Built on `aiohttp` for efficient async operations
- **Session Injection**: Accepts external `ClientSession` - never creates its own
- **Session Authentication**: Uses X-Auth-Token with automatic refresh
- **ETag Caching**: Conditional requests with 304 Not Modified support
- **Request Throttling**: Configurable semaphore for concurrent request limiting
- **Request Statistics**: Track total requests, cache hits, errors, and response times
- **Comprehensive Models**: Full type hints, passes `mypy --strict`
- **1:1 API Mapping**: Field names match Redfish API exactly

## Installation

```bash
pip install supermicro-redfish-client
```

## Quick Start

```python
import asyncio
from aiohttp import ClientSession
from aiosupermicro import SupermicroRedfishClient, ResetType, FanModeType

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
            # Get system information
            system = await client.async_get_system()
            print(f"Power State: {system.power_state}")
            print(f"Health: {system.status.health}")
            print(f"BIOS Version: {system.bios_version}")

            # Get thermal data
            thermal = await client.async_get_thermal()
            for temp in thermal.available_temperatures:
                print(f"{temp.name}: {temp.reading_celsius}°C")

            for fan in thermal.available_fans:
                print(f"{fan.name}: {fan.reading_rpm} RPM")

            # Get power data
            power = await client.async_get_power()
            print(f"Power Consumption: {power.total_power_consumed_watts}W")

            # Change fan mode (OEM feature)
            await client.async_set_fan_mode(FanModeType.OPTIMAL)

            # Set boot source
            await client.async_set_boot_source("Pxe", "Once")

            # Power actions
            await client.async_system_reset(ResetType.GRACEFUL_RESTART)
        finally:
            await client.async_disconnect()

asyncio.run(main())
```

## Context Manager Usage

```python
async with ClientSession() as session:
    async with SupermicroRedfishClient(
        session=session,
        host="192.168.1.100",
        username="ADMIN",
        password="ADMIN",
    ) as client:
        system = await client.async_get_system()
        print(f"System is {'on' if system.is_on else 'off'}")
```

## Bulk Data Fetch

Fetch all data efficiently in parallel:

```python
# Get all data at once
data = await client.async_get_all_data()
print(f"System: {data.system.model}")
print(f"Chassis: {data.chassis.chassis_type}")
print(f"BMC: {data.manager.firmware_version}")
print(f"Power: {data.power.total_power_consumed_watts}W")
print(f"Fans: {data.fan_mode.mode}")

# Get static data with ETag caching (changes rarely)
static = await client.async_get_static_data()

# Get dynamic data (sensor readings)
dynamic = await client.async_get_dynamic_data()
```

## Available Methods

### Read Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `async_get_service_root()` | `ServiceRoot` | Redfish service root |
| `async_get_system()` | `System` | System information |
| `async_get_chassis()` | `Chassis` | Chassis information |
| `async_get_thermal()` | `Thermal` | Temperatures and fans |
| `async_get_power()` | `Power` | Power consumption and voltages |
| `async_get_manager()` | `Manager` | BMC manager information |
| `async_get_network_protocol()` | `NetworkProtocol` | Network protocol settings |
| `async_get_event_service()` | `EventService` | Event service info |
| `async_get_account_service()` | `AccountService` | Account service config |
| `async_get_session_service()` | `SessionService` | Session service config |
| `async_get_update_service()` | `UpdateService` | Update service config |

### Detailed Collection Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `async_get_processors()` | `list[Processor]` | Detailed CPU info (model, cores, cache) |
| `async_get_memory()` | `list[Memory]` | DIMM details (capacity, speed, manufacturer) |
| `async_get_pcie_devices()` | `list[PCIeDevice]` | PCIe devices (slot, interface, firmware) |
| `async_get_system_ethernet_interfaces()` | `list[EthernetInterface]` | Host network interfaces |
| `async_get_log_entries(log_service)` | `list[LogEntry]` | BMC event logs |

### OEM Operations (Supermicro-specific)

| Method | Returns | Description |
|--------|---------|-------------|
| `async_get_fan_mode()` | `FanMode` | OEM fan mode |
| `async_get_ntp()` | `NTP` | OEM NTP settings |
| `async_get_lldp()` | `LLDP` | OEM LLDP settings |
| `async_get_snooping()` | `Snooping` | POST code snooping |
| `async_get_license()` | `License` | License information |

### Write Operations

| Method | Description |
|--------|-------------|
| `async_set_indicator_led(state)` | Set system indicator LED |
| `async_set_boot_source(target, enabled)` | Set boot source override |
| `async_set_fan_mode(mode)` | Set OEM fan mode |
| `async_set_ntp_enabled(enabled)` | Enable/disable NTP |
| `async_set_ntp_servers(primary, secondary)` | Set NTP servers |
| `async_set_lldp_enabled(enabled)` | Enable/disable LLDP |
| `async_set_protocol_enabled(protocol, enabled)` | Enable/disable network protocol |
| `async_set_power_on_delay(seconds)` | Set power on delay |
| `async_set_power_off_delay(seconds)` | Set power off delay |
| `async_set_power_cycle_delay(seconds)` | Set power cycle delay |

### Actions

| Method | Description |
|--------|-------------|
| `async_system_reset(reset_type)` | Perform system reset |
| `async_manager_reset(reset_type)` | Perform BMC reset |
| `async_reset_intrusion_sensor()` | Reset intrusion sensor |

### Bulk Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `async_get_all_data()` | `RedfishData` | All endpoints in parallel |
| `async_get_static_data()` | `StaticData` | Static data with ETag |
| `async_get_dynamic_data()` | `DynamicData` | Dynamic sensor data |

## Enums

All API values are available as `StrEnum`:

```python
from aiosupermicro import (
    PowerState,      # On, Off, PoweringOn, PoweringOff
    Health,          # OK, Warning, Critical
    State,           # Enabled, Disabled, Absent, ...
    ResetType,       # On, ForceOff, GracefulShutdown, ...
    IndicatorLED,    # Off, Lit, Blinking
    BootSource,      # None, Pxe, Hdd, Cd, Usb, BiosSetup, ...
    BootSourceEnabled,  # Disabled, Once, Continuous
    FanModeType,     # Standard, FullSpeed, Optimal, HeavyIO
    IntrusionSensor, # Normal, HardwareIntrusion, TamperingDetected
)
```

## Request Statistics

```python
# Enable request throttling
client.set_max_concurrent_requests(3)

# Access statistics
stats = client.stats
print(f"Total requests: {stats.total_requests}")
print(f"Cache hits: {stats.cache_hits}")
print(f"Cache hit rate: {stats.cache_hit_rate:.1f}%")
print(f"Errors: {stats.errors}")
print(f"Avg response time: {stats.avg_response_time_ms:.1f}ms")
```

## Exception Handling

```python
from aiosupermicro import (
    SupermicroRedfishError,  # Base exception
    AuthenticationError,      # 401 - Invalid credentials
    AuthorizationError,       # 403 - Insufficient permissions
    NotFoundError,            # 404 - Resource not found
    InvalidRequestError,      # 400 - Bad request
    RateLimitError,           # 429 - Too many requests
    ServiceUnavailableError,  # 503 - BMC unavailable
    ConnectionError,          # Network issues
    TimeoutError,             # Request timeout
    InvalidResponseError,     # Unexpected response format
)

try:
    system = await client.async_get_system()
except AuthenticationError:
    print("Invalid credentials")
except ConnectionError:
    print("Cannot connect to BMC")
except SupermicroRedfishError as e:
    print(f"API error: {e}")
```

## Configuration

```python
client = SupermicroRedfishClient(
    session=session,
    host="192.168.1.100",
    username="ADMIN",
    password="ADMIN",
    verify_ssl=False,  # Default: False (self-signed certs)
    timeout=30,        # Default: 30 seconds
)
```

## Requirements

- Python 3.11+
- aiohttp >= 3.8.0

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/aiosupermicro --strict

# Linting
ruff check src/aiosupermicro
```

## License

MIT
