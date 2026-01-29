"""Tests for SupermicroRedfishClient."""

from __future__ import annotations

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from aiosupermicro import (
    AuthenticationError,
    PowerState,
    SupermicroRedfishClient,
)

from .conftest import (
    CHASSIS_RESPONSE,
    FAN_MODE_RESPONSE,
    LICENSE_RESPONSE,
    LLDP_RESPONSE,
    MANAGER_RESPONSE,
    NETWORK_PROTOCOL_RESPONSE,
    NTP_RESPONSE,
    POWER_RESPONSE,
    SERVICE_ROOT_RESPONSE,
    SNOOPING_RESPONSE,
    SYSTEM_RESPONSE,
    THERMAL_RESPONSE,
)


class TestClientConnection:
    """Tests for client connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        """Test successful connection."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={"SessionTimeout": 300},
                headers={"X-Auth-Token": "test-token"},
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                # No exception means success

    @pytest.mark.asyncio
    async def test_connect_auth_failure(self) -> None:
        """Test connection with invalid credentials."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                status=401,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="wrong",
                )
                with pytest.raises(AuthenticationError):
                    await client.async_connect()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={"SessionTimeout": 300},
                headers={"X-Auth-Token": "test-token"},
            )
            m.delete(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions/1",
                status=200,
            )

            async with ClientSession() as session:
                async with SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                ) as client:
                    assert client is not None


class TestClientRead:
    """Tests for client read operations."""

    @pytest.mark.asyncio
    async def test_get_service_root(self) -> None:
        """Test getting service root."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1",
                payload=SERVICE_ROOT_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                root = await client.async_get_service_root()

                assert root.redfish_version == "1.8.0"
                assert root.vendor == "Supermicro"

    @pytest.mark.asyncio
    async def test_get_system(self) -> None:
        """Test getting system information."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Systems/1",
                payload=SYSTEM_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                system = await client.async_get_system()

                assert system.power_state == PowerState.ON
                assert system.is_on is True
                assert system.manufacturer == "Supermicro"

    @pytest.mark.asyncio
    async def test_get_thermal(self) -> None:
        """Test getting thermal information."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Chassis/1/Thermal",
                payload=THERMAL_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                thermal = await client.async_get_thermal()

                assert len(thermal.temperatures) == 2
                assert len(thermal.fans) == 2
                assert thermal.get_temperature("0").reading_celsius == 45

    @pytest.mark.asyncio
    async def test_get_power(self) -> None:
        """Test getting power information."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Chassis/1/Power",
                payload=POWER_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                power = await client.async_get_power()

                assert power.total_power_consumed_watts == 150
                assert len(power.voltages) == 2


class TestClientWrite:
    """Tests for client write operations."""

    @pytest.mark.asyncio
    async def test_system_reset(self) -> None:
        """Test system reset action."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.post(
                "https://192.168.1.100/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                status=200,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                await client.async_system_reset("GracefulRestart")
                # No exception means success

    @pytest.mark.asyncio
    async def test_set_indicator_led(self) -> None:
        """Test setting indicator LED."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.patch(
                "https://192.168.1.100/redfish/v1/Systems/1",
                status=200,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                await client.async_set_indicator_led("Lit")

    @pytest.mark.asyncio
    async def test_set_fan_mode(self) -> None:
        """Test setting fan mode."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.patch(
                "https://192.168.1.100/redfish/v1/Managers/1/Oem/Supermicro/FanMode",
                status=200,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                await client.async_set_fan_mode("Optimal")


class TestClientBulkOperations:
    """Tests for bulk data operations."""

    @pytest.mark.asyncio
    async def test_get_all_data(self) -> None:
        """Test getting all data in parallel."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Systems/1",
                payload=SYSTEM_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Chassis/1",
                payload=CHASSIS_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Chassis/1/Thermal",
                payload=THERMAL_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Chassis/1/Power",
                payload=POWER_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1",
                payload=MANAGER_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/Oem/Supermicro/FanMode",
                payload=FAN_MODE_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/NetworkProtocol",
                payload=NETWORK_PROTOCOL_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/LicenseManager/QueryLicense",
                payload=LICENSE_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/Oem/Supermicro/Snooping",
                payload=SNOOPING_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/Oem/Supermicro/NTP",
                payload=NTP_RESPONSE,
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Managers/1/Oem/Supermicro/LLDP",
                payload=LLDP_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                data = await client.async_get_all_data()

                assert data.system.is_on
                assert data.chassis.is_valid
                assert len(data.thermal.temperatures) == 2
                assert data.power.total_power_consumed_watts == 150
                assert data.manager.is_valid
                assert data.fan_mode.is_valid
                assert data.network_protocol.is_valid
                assert data.license.is_licensed
                assert data.ntp.enabled
                assert data.lldp.enabled


class TestClientStats:
    """Tests for request statistics."""

    @pytest.mark.asyncio
    async def test_stats_tracking(self) -> None:
        """Test that stats are tracked."""
        with aioresponses() as m:
            m.post(
                "https://192.168.1.100/redfish/v1/SessionService/Sessions",
                payload={},
                headers={"X-Auth-Token": "test-token"},
            )
            m.get(
                "https://192.168.1.100/redfish/v1/Systems/1",
                payload=SYSTEM_RESPONSE,
            )

            async with ClientSession() as session:
                client = SupermicroRedfishClient(
                    session=session,
                    host="192.168.1.100",
                    username="ADMIN",
                    password="ADMIN",
                )
                await client.async_connect()
                await client.async_get_system()

                assert client.stats.total_requests >= 1
                assert client.stats.avg_response_time_ms > 0
