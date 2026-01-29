"""Async Redfish API client for Supermicro BMC."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from aiohttp import ClientResponseError, ClientTimeout

from .auth import SessionAuth
from .const import (
    DEFAULT_TIMEOUT,
    ENDPOINT_ACCOUNT_SERVICE,
    ENDPOINT_CHASSIS,
    ENDPOINT_EVENT_SERVICE,
    ENDPOINT_LICENSE_QUERY,
    ENDPOINT_LOG_SERVICES,
    ENDPOINT_MANAGERS,
    ENDPOINT_MEMORY,
    ENDPOINT_NETWORK_PROTOCOL,
    ENDPOINT_OEM_FAN_MODE,
    ENDPOINT_OEM_LLDP,
    ENDPOINT_OEM_NTP,
    ENDPOINT_OEM_SNOOPING,
    ENDPOINT_PCIE_DEVICES,
    ENDPOINT_POWER,
    ENDPOINT_PROCESSORS,
    ENDPOINT_SESSION_SERVICE,
    ENDPOINT_SYSTEM_ETHERNET,
    ENDPOINT_SYSTEMS,
    ENDPOINT_THERMAL,
    ENDPOINT_UPDATE_SERVICE,
    REDFISH_ROOT,
)
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InvalidResponseError,
    SupermicroRedfishError,
    raise_for_status,
)
from .models import (
    LLDP,
    NTP,
    AccountService,
    Chassis,
    EthernetInterface,
    EventService,
    FanMode,
    License,
    LogEntry,
    Manager,
    Memory,
    NetworkProtocol,
    PCIeDevice,
    Power,
    Processor,
    ServiceRoot,
    SessionService,
    Snooping,
    System,
    Thermal,
    UpdateService,
)

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass
class ETagCache:
    """ETag caching for conditional requests."""

    etags: dict[str, str] = field(default_factory=dict)
    cached_data: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get_etag(self, path: str) -> str | None:
        """Get ETag for a path."""
        return self.etags.get(path)

    def store(self, path: str, etag: str, data: dict[str, Any]) -> None:
        """Store ETag and data for a path."""
        self.etags[path] = etag
        self.cached_data[path] = data

    def get_cached(self, path: str) -> dict[str, Any] | None:
        """Get cached data for a path."""
        return self.cached_data.get(path)

    def invalidate(self, path: str) -> None:
        """Invalidate cache for a path."""
        self.etags.pop(path, None)
        self.cached_data.pop(path, None)

    def invalidate_all(self) -> None:
        """Invalidate all cached data."""
        self.etags.clear()
        self.cached_data.clear()


@dataclass
class RequestStats:
    """Statistics for API requests."""

    total_requests: int = 0
    cache_hits: int = 0
    errors: int = 0
    _response_times: deque[float] = field(
        default_factory=lambda: deque(maxlen=10)
    )

    def record_response_time(self, elapsed: float) -> None:
        """Record a response time."""
        self._response_times.append(elapsed)

    @property
    def avg_response_time_ms(self) -> float:
        """Get average response time in milliseconds."""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times) * 1000

    @property
    def cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests * 100

    @property
    def recent_response_times_ms(self) -> list[float]:
        """Get recent response times in milliseconds."""
        return [t * 1000 for t in self._response_times]


@dataclass
class RedfishData:
    """Complete Redfish data from all endpoints."""

    system: System
    chassis: Chassis
    thermal: Thermal
    power: Power
    manager: Manager
    fan_mode: FanMode
    network_protocol: NetworkProtocol
    license: License
    snooping: Snooping
    ntp: NTP
    lldp: LLDP


@dataclass
class StaticData:
    """Static data that changes rarely."""

    system: System
    chassis: Chassis
    manager: Manager
    license: License


@dataclass
class DynamicData:
    """Dynamic data that changes frequently."""

    thermal: Thermal
    power: Power
    fan_mode: FanMode
    snooping: Snooping


class SupermicroRedfishClient:
    """Async Redfish API Client for Supermicro BMC.

    Features:
    - Session-based authentication with automatic refresh
    - ETag caching for conditional requests
    - Request throttling
    - Request statistics

    Example:
        async with aiohttp.ClientSession() as session:
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
            finally:
                await client.async_disconnect()
    """

    def __init__(
        self,
        session: ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        verify_ssl: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Redfish client.

        Args:
            session: aiohttp ClientSession (injected, caller owns lifecycle)
            host: BMC hostname or IP address
            username: BMC username
            password: BMC password
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self._session = session
        self._host = host.rstrip("/")
        self._base_url = f"https://{self._host}"
        self._timeout = ClientTimeout(total=timeout)
        self._ssl = verify_ssl

        # Session-based authentication
        self._auth = SessionAuth(
            session=session,
            base_url=self._base_url,
            username=username,
            password=password,
            ssl=verify_ssl,
            timeout=self._timeout,
        )

        # ETag caching
        self._etag_cache = ETagCache()

        # Request throttling
        self._request_semaphore: asyncio.Semaphore | None = None

        # Statistics
        self._stats = RequestStats()

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def set_max_concurrent_requests(self, max_requests: int) -> None:
        """Configure request throttling.

        Args:
            max_requests: Maximum concurrent requests (1-10)
        """
        self._request_semaphore = asyncio.Semaphore(
            min(max(max_requests, 1), 10)
        )

    @property
    def stats(self) -> RequestStats:
        """Get request statistics."""
        return self._stats

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    async def async_connect(self) -> None:
        """Establish connection and authenticate."""
        await self._auth.async_login()

    async def async_disconnect(self) -> None:
        """Clean up connection resources."""
        await self._auth.async_logout()

    async def async_test_connection(self) -> ServiceRoot:
        """Test connection and return service root.

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails

        Returns:
            ServiceRoot information
        """
        data = await self._async_get(REDFISH_ROOT)
        return ServiceRoot.from_dict(data)

    async def __aenter__(self) -> SupermicroRedfishClient:
        """Async context manager entry - connect."""
        await self.async_connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit - disconnect."""
        await self.async_disconnect()

    # -------------------------------------------------------------------------
    # Service Root
    # -------------------------------------------------------------------------

    async def async_get_service_root(self) -> ServiceRoot:
        """Get Redfish service root."""
        data = await self._async_get(REDFISH_ROOT)
        return ServiceRoot.from_dict(data)

    # -------------------------------------------------------------------------
    # Systems
    # -------------------------------------------------------------------------

    async def async_get_system(self) -> System:
        """Get computer system information."""
        data = await self._async_get(ENDPOINT_SYSTEMS)
        return System.from_dict(data)

    async def async_get_processors(self) -> list[Processor]:
        """Get detailed processor information.

        Returns a list of Processor objects with full details including
        model name, cores, threads, cache, and speed information.

        Returns:
            List of Processor objects (typically one per CPU socket)
        """
        processors: list[Processor] = []

        # Get processor collection
        collection = await self._async_get(ENDPOINT_PROCESSORS)
        members = collection.get("Members", [])

        # Fetch each processor's details
        for member in members:
            proc_uri = member.get("@odata.id")
            if proc_uri:
                proc_data = await self._async_get(proc_uri)
                processors.append(Processor.from_dict(proc_data))

        return processors

    async def async_get_memory(self) -> list[Memory]:
        """Get detailed memory DIMM information.

        Returns a list of Memory objects with full details including
        capacity, manufacturer, speed, and location.

        Returns:
            List of Memory objects (one per DIMM slot with installed memory)
        """
        memory_list: list[Memory] = []

        # Get memory collection
        collection = await self._async_get(ENDPOINT_MEMORY)
        members = collection.get("Members", [])

        # Fetch each DIMM's details
        for member in members:
            mem_uri = member.get("@odata.id")
            if mem_uri:
                mem_data = await self._async_get(mem_uri)
                memory = Memory.from_dict(mem_data)
                # Only include valid (installed) DIMMs
                if memory.is_valid:
                    memory_list.append(memory)

        return memory_list

    async def async_get_system_ethernet_interfaces(self) -> list[EthernetInterface]:
        """Get system-level ethernet interfaces.

        These are the ethernet interfaces of the host system, not the BMC.

        Returns:
            List of EthernetInterface objects
        """
        interfaces: list[EthernetInterface] = []

        # Get interface collection
        collection = await self._async_get(ENDPOINT_SYSTEM_ETHERNET)
        members = collection.get("Members", [])

        # Fetch each interface's details
        for member in members:
            iface_uri = member.get("@odata.id")
            if iface_uri:
                iface_data = await self._async_get(iface_uri)
                interfaces.append(EthernetInterface.from_dict(iface_data))

        return interfaces

    async def async_set_indicator_led(self, state: str) -> None:
        """Set system indicator LED state.

        Args:
            state: LED state ("Off", "Lit", "Blinking")
        """
        await self._async_patch(ENDPOINT_SYSTEMS, {"IndicatorLED": state})

    async def async_set_boot_source(
        self,
        target: str,
        enabled: str = "Once",
    ) -> None:
        """Set boot source override.

        Args:
            target: Boot target (e.g., "Pxe", "Hdd", "Cd")
            enabled: Override mode ("Once", "Continuous", "Disabled")
        """
        await self._async_patch(
            ENDPOINT_SYSTEMS,
            {
                "Boot": {
                    "BootSourceOverrideTarget": target,
                    "BootSourceOverrideEnabled": enabled,
                }
            },
        )

    async def async_system_reset(self, reset_type: str) -> None:
        """Perform system reset action.

        Args:
            reset_type: Reset type (e.g., "On", "ForceOff", "GracefulShutdown")
        """
        await self._async_post(
            f"{ENDPOINT_SYSTEMS}/Actions/ComputerSystem.Reset",
            {"ResetType": reset_type},
        )

    async def async_set_power_on_delay(self, seconds: int) -> None:
        """Set the power on delay in seconds.

        Args:
            seconds: Delay in seconds (3-254)
        """
        await self._async_patch(
            ENDPOINT_SYSTEMS, {"PowerOnDelaySeconds": seconds}
        )

    async def async_set_power_off_delay(self, seconds: int) -> None:
        """Set the power off delay in seconds.

        Args:
            seconds: Delay in seconds (3-254)
        """
        await self._async_patch(
            ENDPOINT_SYSTEMS, {"PowerOffDelaySeconds": seconds}
        )

    async def async_set_power_cycle_delay(self, seconds: int) -> None:
        """Set the power cycle delay in seconds.

        Args:
            seconds: Delay in seconds (5-254)
        """
        await self._async_patch(
            ENDPOINT_SYSTEMS, {"PowerCycleDelaySeconds": seconds}
        )

    # -------------------------------------------------------------------------
    # Chassis
    # -------------------------------------------------------------------------

    async def async_get_chassis(self) -> Chassis:
        """Get chassis information."""
        data = await self._async_get(ENDPOINT_CHASSIS)
        return Chassis.from_dict(data)

    async def async_reset_intrusion_sensor(self) -> None:
        """Reset the chassis intrusion sensor.

        Re-arms the intrusion sensor after it has been triggered.
        """
        await self._async_patch(
            ENDPOINT_CHASSIS,
            {"PhysicalSecurity": {"IntrusionSensor": "Normal"}},
        )

    async def async_get_thermal(self) -> Thermal:
        """Get thermal data (temperatures and fans)."""
        data = await self._async_get(ENDPOINT_THERMAL)
        return Thermal.from_dict(data)

    async def async_get_power(self) -> Power:
        """Get power data (voltages and power control)."""
        data = await self._async_get(ENDPOINT_POWER)
        return Power.from_dict(data)

    async def async_get_pcie_devices(self) -> list[PCIeDevice]:
        """Get PCIe device information.

        Returns a list of PCIeDevice objects with details including
        manufacturer, model, firmware version, and PCIe interface info.

        Returns:
            List of PCIeDevice objects
        """
        devices: list[PCIeDevice] = []

        # Get device collection
        collection = await self._async_get(ENDPOINT_PCIE_DEVICES)
        members = collection.get("Members", [])

        # Fetch each device's details
        for member in members:
            dev_uri = member.get("@odata.id")
            if dev_uri:
                dev_data = await self._async_get(dev_uri)
                devices.append(PCIeDevice.from_dict(dev_data))

        return devices

    # -------------------------------------------------------------------------
    # Managers (BMC)
    # -------------------------------------------------------------------------

    async def async_get_manager(self) -> Manager:
        """Get BMC manager information."""
        data = await self._async_get(ENDPOINT_MANAGERS)
        return Manager.from_dict(data)

    async def async_manager_reset(self, reset_type: str = "GracefulRestart") -> None:
        """Perform BMC manager reset.

        Args:
            reset_type: Reset type ("GracefulRestart" or "ForceRestart")
        """
        await self._async_post(
            f"{ENDPOINT_MANAGERS}/Actions/Manager.Reset",
            {"ResetType": reset_type},
        )

    async def async_get_network_protocol(self) -> NetworkProtocol:
        """Get network protocol settings."""
        data = await self._async_get(ENDPOINT_NETWORK_PROTOCOL)
        return NetworkProtocol.from_dict(data)

    async def async_set_protocol_enabled(
        self,
        protocol: str,
        enabled: bool,
    ) -> None:
        """Enable or disable a network protocol.

        Args:
            protocol: Protocol name (e.g., "HTTP", "SSH", "IPMI")
            enabled: Whether to enable the protocol
        """
        await self._async_patch(
            ENDPOINT_NETWORK_PROTOCOL,
            {protocol: {"ProtocolEnabled": enabled}},
        )

    # -------------------------------------------------------------------------
    # OEM (Supermicro-specific)
    # -------------------------------------------------------------------------

    async def async_get_fan_mode(self) -> FanMode:
        """Get OEM fan mode configuration."""
        try:
            data = await self._async_get(ENDPOINT_OEM_FAN_MODE)
            return FanMode.from_dict(data)
        except SupermicroRedfishError:
            # OEM endpoint may not be available on all BMC versions
            return FanMode.from_dict({})

    async def async_set_fan_mode(self, mode: str) -> None:
        """Set OEM fan mode.

        Args:
            mode: Fan mode ("Standard", "FullSpeed", "Optimal", "HeavyIO")
        """
        await self._async_patch(ENDPOINT_OEM_FAN_MODE, {"Mode": mode})

    async def async_get_snooping(self) -> Snooping:
        """Get POST code snooping information."""
        try:
            data = await self._async_get(ENDPOINT_OEM_SNOOPING)
            return Snooping.from_dict(data)
        except SupermicroRedfishError:
            # OEM endpoint may not be available on all BMC versions
            return Snooping.from_dict({})

    async def async_get_ntp(self) -> NTP:
        """Get OEM NTP configuration."""
        try:
            data = await self._async_get(ENDPOINT_OEM_NTP)
            return NTP.from_dict(data)
        except SupermicroRedfishError:
            # OEM endpoint may not be available on all BMC versions
            return NTP.from_dict({})

    async def async_set_ntp_enabled(self, enabled: bool) -> None:
        """Enable or disable NTP.

        Args:
            enabled: Whether to enable NTP
        """
        await self._async_patch(ENDPOINT_OEM_NTP, {"NTPEnable": enabled})

    async def async_set_ntp_servers(
        self, primary: str, secondary: str = ""
    ) -> None:
        """Set NTP servers.

        Args:
            primary: Primary NTP server hostname or IP
            secondary: Secondary NTP server hostname or IP
        """
        payload: dict[str, str] = {"PrimaryNTPServer": primary}
        if secondary:
            payload["SecondaryNTPServer"] = secondary
        await self._async_patch(ENDPOINT_OEM_NTP, payload)

    async def async_get_lldp(self) -> LLDP:
        """Get OEM LLDP configuration."""
        try:
            data = await self._async_get(ENDPOINT_OEM_LLDP)
            return LLDP.from_dict(data)
        except SupermicroRedfishError:
            # OEM endpoint may not be available on all BMC versions
            return LLDP.from_dict({})

    async def async_set_lldp_enabled(self, enabled: bool) -> None:
        """Enable or disable LLDP.

        Args:
            enabled: Whether to enable LLDP
        """
        await self._async_patch(ENDPOINT_OEM_LLDP, {"LLDPEnabled": enabled})

    # -------------------------------------------------------------------------
    # License
    # -------------------------------------------------------------------------

    async def async_get_license(self) -> License:
        """Get license information."""
        try:
            data = await self._async_get(ENDPOINT_LICENSE_QUERY)
            return License.from_dict(data)
        except SupermicroRedfishError:
            # License endpoint may not be available on all BMC versions
            return License.from_dict({})

    # -------------------------------------------------------------------------
    # Event Service
    # -------------------------------------------------------------------------

    async def async_get_event_service(self) -> EventService:
        """Get event service information."""
        data = await self._async_get(ENDPOINT_EVENT_SERVICE)
        return EventService.from_dict(data)

    async def async_get_account_service(self) -> AccountService:
        """Get account service configuration."""
        data = await self._async_get(ENDPOINT_ACCOUNT_SERVICE)
        return AccountService.from_dict(data)

    async def async_get_session_service(self) -> SessionService:
        """Get session service configuration."""
        data = await self._async_get(ENDPOINT_SESSION_SERVICE)
        return SessionService.from_dict(data)

    async def async_get_update_service(self) -> UpdateService:
        """Get update service configuration."""
        data = await self._async_get(ENDPOINT_UPDATE_SERVICE)
        return UpdateService.from_dict(data)

    # -------------------------------------------------------------------------
    # Log Services
    # -------------------------------------------------------------------------

    async def async_get_log_entries(
        self, log_service: str = "Log1"
    ) -> list[LogEntry]:
        """Get log entries from BMC log service.

        Args:
            log_service: Log service name (default: "Log1")

        Returns:
            List of LogEntry objects ordered by creation time (newest first)
        """
        entries: list[LogEntry] = []

        # Get log service to find entries collection
        log_uri = f"{ENDPOINT_LOG_SERVICES}/{log_service}"
        log_data = await self._async_get(log_uri)

        entries_link = log_data.get("Entries", {}).get("@odata.id")
        if not entries_link:
            return entries

        # Get entries collection
        collection = await self._async_get(entries_link)
        members = collection.get("Members", [])

        # Fetch each entry's details
        for member in members:
            entry_uri = member.get("@odata.id")
            if entry_uri:
                entry_data = await self._async_get(entry_uri)
                entries.append(LogEntry.from_dict(entry_data))

        return entries

    # -------------------------------------------------------------------------
    # Bulk Data Fetch
    # -------------------------------------------------------------------------

    async def _async_gather_endpoints(
        self,
        coroutines: list[Any],
        keys: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Execute multiple endpoint requests in parallel.

        Args:
            coroutines: List of coroutines to execute
            keys: List of keys for the results

        Returns:
            Dictionary mapping keys to endpoint responses
        """
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        data: dict[str, dict[str, Any]] = {}
        for key, result in zip(keys, results, strict=True):
            if isinstance(result, BaseException):
                data[key] = {}
            else:
                data[key] = result if result else {}
        return data

    async def async_get_all_data(self) -> RedfishData:
        """Fetch all data in parallel for efficient polling.

        Returns:
            RedfishData with all endpoint responses
        """
        raw = await self._async_gather_endpoints(
            coroutines=[
                self._async_get(ENDPOINT_SYSTEMS),
                self._async_get(ENDPOINT_CHASSIS),
                self._async_get(ENDPOINT_THERMAL),
                self._async_get(ENDPOINT_POWER),
                self._async_get(ENDPOINT_MANAGERS),
                self._async_get(ENDPOINT_OEM_FAN_MODE),
                self._async_get(ENDPOINT_NETWORK_PROTOCOL),
                self._async_get(ENDPOINT_LICENSE_QUERY),
                self._async_get(ENDPOINT_OEM_SNOOPING),
                self._async_get(ENDPOINT_OEM_NTP),
                self._async_get(ENDPOINT_OEM_LLDP),
            ],
            keys=[
                "system",
                "chassis",
                "thermal",
                "power",
                "manager",
                "fan_mode",
                "network_protocol",
                "license",
                "snooping",
                "ntp",
                "lldp",
            ],
        )

        return RedfishData(
            system=System.from_dict(raw["system"]),
            chassis=Chassis.from_dict(raw["chassis"]),
            thermal=Thermal.from_dict(raw["thermal"]),
            power=Power.from_dict(raw["power"]),
            manager=Manager.from_dict(raw["manager"]),
            fan_mode=FanMode.from_dict(raw["fan_mode"]),
            network_protocol=NetworkProtocol.from_dict(raw["network_protocol"]),
            license=License.from_dict(raw["license"]),
            snooping=Snooping.from_dict(raw["snooping"]),
            ntp=NTP.from_dict(raw["ntp"]),
            lldp=LLDP.from_dict(raw["lldp"]),
        )

    async def async_get_static_data(self) -> StaticData:
        """Fetch static data with ETag caching.

        Static data changes rarely (system info, config settings).

        Returns:
            StaticData with static endpoint responses
        """
        raw = await self._async_gather_endpoints(
            coroutines=[
                self._async_get(ENDPOINT_SYSTEMS, use_etag=True),
                self._async_get(ENDPOINT_CHASSIS, use_etag=True),
                self._async_get(ENDPOINT_MANAGERS, use_etag=True),
                self._async_get(ENDPOINT_LICENSE_QUERY),
            ],
            keys=["system", "chassis", "manager", "license"],
        )

        return StaticData(
            system=System.from_dict(raw["system"]),
            chassis=Chassis.from_dict(raw["chassis"]),
            manager=Manager.from_dict(raw["manager"]),
            license=License.from_dict(raw["license"]),
        )

    async def async_get_dynamic_data(self) -> DynamicData:
        """Fetch dynamic data without ETag.

        Dynamic data changes frequently (sensor readings).

        Returns:
            DynamicData with dynamic endpoint responses
        """
        raw = await self._async_gather_endpoints(
            coroutines=[
                self._async_get(ENDPOINT_THERMAL),
                self._async_get(ENDPOINT_POWER),
                self._async_get(ENDPOINT_OEM_FAN_MODE),
                self._async_get(ENDPOINT_OEM_SNOOPING),
            ],
            keys=["thermal", "power", "fan_mode", "snooping"],
        )

        return DynamicData(
            thermal=Thermal.from_dict(raw["thermal"]),
            power=Power.from_dict(raw["power"]),
            fan_mode=FanMode.from_dict(raw["fan_mode"]),
            snooping=Snooping.from_dict(raw["snooping"]),
        )

    # -------------------------------------------------------------------------
    # HTTP Methods
    # -------------------------------------------------------------------------

    async def _async_request(
        self,
        method: Literal["GET", "PATCH", "POST", "DELETE"],
        path: str,
        data: dict[str, Any] | None = None,
        use_etag: bool = False,
    ) -> tuple[dict[str, Any] | None, bool]:
        """Perform async HTTP request with session auth.

        Args:
            method: HTTP method
            path: API endpoint path
            data: JSON data to send
            use_etag: Whether to use ETag caching

        Returns:
            Tuple of (response_data, was_cached)

        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        # Apply request throttling if configured
        if self._request_semaphore:
            await self._request_semaphore.acquire()

        start_time = time.monotonic()

        try:
            self._stats.total_requests += 1

            # Ensure session is valid
            await self._auth.async_ensure_session()

            url = f"{self._base_url}{path}"
            headers = await self._auth.async_get_headers()

            # Add ETag header for conditional GET
            if use_etag and method == "GET":
                etag = self._etag_cache.get_etag(path)
                if etag:
                    headers["If-None-Match"] = etag

            # Build request kwargs
            request_kwargs: dict[str, Any] = {
                "headers": headers,
                "ssl": self._ssl,
                "timeout": self._timeout,
            }

            # Use BasicAuth if no session token
            if not self._auth.has_valid_session():
                request_kwargs["auth"] = self._auth.get_basic_auth()

            if data is not None:
                request_kwargs["json"] = data

            async with self._session.request(
                method, url, **request_kwargs
            ) as response:
                # Handle 304 Not Modified (ETag cache hit)
                if response.status == 304:
                    self._stats.cache_hits += 1
                    cached = self._etag_cache.get_cached(path)
                    return (cached if cached else {}, True)

                # Handle 401 - invalidate session and retry
                if response.status == 401:
                    self._auth.invalidate()
                    if await self._auth.async_login():
                        headers = await self._auth.async_get_headers()
                        request_kwargs["headers"] = headers
                        request_kwargs.pop("auth", None)
                        async with self._session.request(
                            method, url, **request_kwargs
                        ) as retry_response:
                            if retry_response.status == 401:
                                raise AuthenticationError(
                                    "Authentication failed after re-login"
                                )
                            retry_response.raise_for_status()
                            try:
                                result: dict[str, Any] = (
                                    await retry_response.json()
                                )
                                return (result, False)
                            except Exception:
                                return ({} if method == "PATCH" else None, False)
                    raise AuthenticationError("Invalid authentication credentials")

                raise_for_status(response.status)

                result_data: dict[str, Any] | None = None
                # Read JSON response if available
                # Note: content_length may be None for chunked responses
                try:
                    result_data = await response.json()
                except Exception:
                    result_data = None

                # Store ETag for future conditional requests
                if use_etag and method == "GET" and result_data:
                    etag = response.headers.get("ETag")
                    if etag:
                        self._etag_cache.store(path, etag, result_data)

                # Invalidate cache on write operations
                if method in ("PATCH", "POST"):
                    self._etag_cache.invalidate(path)

                return (
                    result_data if result_data else ({} if method == "PATCH" else None),
                    False,
                )

        except ClientResponseError as err:
            self._stats.errors += 1
            if err.status == 401:
                raise AuthenticationError(
                    "Invalid authentication credentials"
                ) from err
            raise ConnectionError(f"API request failed: {err}") from err
        except TimeoutError as err:
            self._stats.errors += 1
            raise ConnectionError(f"Request timeout: {path}") from err
        except (AuthenticationError, ConnectionError, InvalidResponseError):
            raise
        except Exception as err:
            self._stats.errors += 1
            raise ConnectionError(f"Connection error: {err}") from err
        finally:
            elapsed = time.monotonic() - start_time
            self._stats.record_response_time(elapsed)
            if self._request_semaphore:
                self._request_semaphore.release()

    async def _async_get(
        self, path: str, use_etag: bool = False
    ) -> dict[str, Any]:
        """Perform async GET request."""
        result, _ = await self._async_request("GET", path, use_etag=use_etag)
        return result if result is not None else {}

    async def _async_patch(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform async PATCH request."""
        result, _ = await self._async_request("PATCH", path, data)
        return result if result is not None else {}

    async def _async_post(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Perform async POST request."""
        result, _ = await self._async_request("POST", path, data)
        return result
