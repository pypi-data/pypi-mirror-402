"""Tests for data models."""

from __future__ import annotations

import pytest

from aiosupermicro.models import (
    Chassis,
    FanMode,
    License,
    LLDP,
    Manager,
    NetworkProtocol,
    NTP,
    Power,
    ServiceRoot,
    Snooping,
    System,
    Thermal,
)
from aiosupermicro.models.enums import (
    ChassisType,
    FanModeType,
    Health,
    IndicatorLED,
    IntrusionSensor,
    ManagerType,
    PowerState,
    State,
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


class TestSystemModel:
    """Tests for System model."""

    def test_from_dict(self) -> None:
        """Test System.from_dict()."""
        system = System.from_dict(SYSTEM_RESPONSE)

        assert system.id == "1"
        assert system.name == "System"
        assert system.uuid == "12345678-1234-1234-1234-123456789012"
        assert system.manufacturer == "Supermicro"
        assert system.model == "X12STH-SYS"
        assert system.serial_number == "S123456789"
        assert system.power_state == PowerState.ON
        assert system.bios_version == "2.1"  # Parsed from Supermicro format
        assert system.indicator_led == IndicatorLED.OFF
        assert system.is_valid is True
        assert system.is_on is True
        assert system.is_healthy is True

    def test_processor_summary(self) -> None:
        """Test ProcessorSummary parsing."""
        system = System.from_dict(SYSTEM_RESPONSE)

        assert system.processor_count == 1
        assert system.processor_summary.model == "Intel Xeon W-1290"
        assert system.processor_summary.status.is_healthy

    def test_memory_summary(self) -> None:
        """Test MemorySummary parsing."""
        system = System.from_dict(SYSTEM_RESPONSE)

        assert system.total_memory_gib == 128
        assert system.memory_summary.status.is_healthy

    def test_boot_options(self) -> None:
        """Test Boot configuration parsing."""
        system = System.from_dict(SYSTEM_RESPONSE)

        assert system.boot.boot_source_override_target is not None
        assert len(system.boot.boot_source_options) == 5
        assert "Pxe" in system.boot.boot_source_options

    def test_reset_types(self) -> None:
        """Test reset types parsing."""
        system = System.from_dict(SYSTEM_RESPONSE)

        assert len(system.reset_types) == 5

    def test_empty_dict(self) -> None:
        """Test with empty dict."""
        system = System.from_dict({})

        assert system.is_valid is False
        assert system.power_state == PowerState.OFF


class TestChassisModel:
    """Tests for Chassis model."""

    def test_from_dict(self) -> None:
        """Test Chassis.from_dict()."""
        chassis = Chassis.from_dict(CHASSIS_RESPONSE)

        assert chassis.id == "1"
        assert chassis.chassis_type == ChassisType.RACK_MOUNT
        assert chassis.manufacturer == "Supermicro"
        assert chassis.model == "CSE-815TQ-1MR"
        assert chassis.power_state == PowerState.ON
        assert chassis.indicator_led == IndicatorLED.OFF
        assert chassis.is_valid is True
        assert chassis.is_healthy is True

    def test_physical_security(self) -> None:
        """Test PhysicalSecurity parsing."""
        chassis = Chassis.from_dict(CHASSIS_RESPONSE)

        assert chassis.physical_security.intrusion_sensor == IntrusionSensor.NORMAL
        assert chassis.physical_security.intrusion_sensor_number == 170
        assert chassis.is_intruded is False

    def test_oem_data(self) -> None:
        """Test OEM data parsing."""
        chassis = Chassis.from_dict(CHASSIS_RESPONSE)

        assert chassis.oem.board_serial_number == "BM123456789"
        assert chassis.oem.board_id == "0x0A1B"


class TestThermalModel:
    """Tests for Thermal model."""

    def test_from_dict(self) -> None:
        """Test Thermal.from_dict()."""
        thermal = Thermal.from_dict(THERMAL_RESPONSE)

        assert thermal.id == "Thermal"
        assert len(thermal.temperatures) == 2
        assert len(thermal.fans) == 2
        assert thermal.is_valid is True

    def test_temperature_sensors(self) -> None:
        """Test temperature sensor parsing."""
        thermal = Thermal.from_dict(THERMAL_RESPONSE)

        cpu_temp = thermal.get_temperature("0")
        assert cpu_temp is not None
        assert cpu_temp.name == "CPU Temp"
        assert cpu_temp.reading_celsius == 45
        assert cpu_temp.upper_threshold_critical == 95
        assert cpu_temp.is_available is True

    def test_fan_sensors(self) -> None:
        """Test fan sensor parsing."""
        thermal = Thermal.from_dict(THERMAL_RESPONSE)

        fan1 = thermal.get_fan("0")
        assert fan1 is not None
        assert fan1.name == "FAN1"
        assert fan1.reading_rpm == 3500
        assert fan1.is_available is True

    def test_available_sensors(self) -> None:
        """Test available sensor filtering."""
        thermal = Thermal.from_dict(THERMAL_RESPONSE)

        assert len(thermal.available_temperatures) == 2
        assert len(thermal.available_fans) == 2


class TestPowerModel:
    """Tests for Power model."""

    def test_from_dict(self) -> None:
        """Test Power.from_dict()."""
        power = Power.from_dict(POWER_RESPONSE)

        assert power.id == "Power"
        assert len(power.power_control) == 1
        assert len(power.voltages) == 2
        assert len(power.power_supplies) == 1
        assert power.is_valid is True

    def test_power_consumption(self) -> None:
        """Test power consumption."""
        power = Power.from_dict(POWER_RESPONSE)

        assert power.total_power_consumed_watts == 150
        assert power.power_control[0].power_capacity_watts == 400

    def test_power_metrics(self) -> None:
        """Test power metrics."""
        power = Power.from_dict(POWER_RESPONSE)

        metrics = power.power_control[0].power_metrics
        assert metrics.min_consumed_watts == 120
        assert metrics.max_consumed_watts == 200
        assert metrics.average_consumed_watts == 155

    def test_voltages(self) -> None:
        """Test voltage sensor parsing."""
        power = Power.from_dict(POWER_RESPONSE)

        v12 = power.get_voltage("0")
        assert v12 is not None
        assert v12.name == "12V"
        assert v12.reading_volts == 12.1
        assert v12.is_available is True

    def test_battery(self) -> None:
        """Test battery parsing."""
        power = Power.from_dict(POWER_RESPONSE)

        assert power.battery is not None
        assert power.battery.name == "VBAT"
        assert power.battery.is_healthy is True


class TestManagerModel:
    """Tests for Manager model."""

    def test_from_dict(self) -> None:
        """Test Manager.from_dict()."""
        manager = Manager.from_dict(MANAGER_RESPONSE)

        assert manager.id == "1"
        assert manager.manager_type == ManagerType.BMC
        assert manager.firmware_version == "1.0.0"
        assert manager.model == "ASPEED"
        assert manager.is_valid is True
        assert manager.is_healthy is True


class TestNetworkProtocolModel:
    """Tests for NetworkProtocol model."""

    def test_from_dict(self) -> None:
        """Test NetworkProtocol.from_dict()."""
        np = NetworkProtocol.from_dict(NETWORK_PROTOCOL_RESPONSE)

        assert np.id == "NetworkProtocol"
        assert np.hostname == "bmc"
        assert np.fqdn == "bmc.local"
        assert np.https.protocol_enabled is True
        assert np.https.port == 443
        assert np.ssh.protocol_enabled is True
        assert np.http.protocol_enabled is False
        assert np.is_valid is True


class TestOemModels:
    """Tests for OEM models."""

    def test_fan_mode(self) -> None:
        """Test FanMode parsing."""
        fan_mode = FanMode.from_dict(FAN_MODE_RESPONSE)

        assert fan_mode.mode == FanModeType.OPTIMAL
        assert len(fan_mode.available_modes) == 4
        assert fan_mode.is_valid is True

    def test_ntp(self) -> None:
        """Test NTP parsing."""
        ntp = NTP.from_dict(NTP_RESPONSE)

        assert ntp.enabled is True
        assert ntp.primary_server == "pool.ntp.org"
        assert ntp.secondary_server == ""
        assert ntp.is_valid is True

    def test_lldp(self) -> None:
        """Test LLDP parsing."""
        lldp = LLDP.from_dict(LLDP_RESPONSE)

        assert lldp.enabled is True
        assert lldp.is_valid is True

    def test_snooping(self) -> None:
        """Test Snooping parsing."""
        snooping = Snooping.from_dict(SNOOPING_RESPONSE)

        assert snooping.post_code == "0x00"
        assert snooping.is_valid is True

    def test_license(self) -> None:
        """Test License parsing."""
        license_info = License.from_dict(LICENSE_RESPONSE)

        assert license_info.is_licensed is True
        assert len(license_info.licenses) == 1
        assert license_info.licenses[0].license_id == "SFT-OOB-LIC"
        assert license_info.is_valid is True


class TestServiceRootModel:
    """Tests for ServiceRoot model."""

    def test_from_dict(self) -> None:
        """Test ServiceRoot.from_dict()."""
        root = ServiceRoot.from_dict(SERVICE_ROOT_RESPONSE)

        assert root.redfish_version == "1.8.0"
        assert root.uuid == "12345678-1234-1234-1234-123456789012"
        assert root.product == "Supermicro Redfish Service"
        assert root.vendor == "Supermicro"
        assert root.is_valid is True


class TestEnums:
    """Tests for enum types."""

    def test_power_state(self) -> None:
        """Test PowerState enum."""
        assert PowerState.ON == "On"
        assert PowerState.OFF == "Off"

    def test_health(self) -> None:
        """Test Health enum."""
        assert Health.OK == "OK"
        assert Health.WARNING == "Warning"
        assert Health.CRITICAL == "Critical"

    def test_state(self) -> None:
        """Test State enum."""
        assert State.ENABLED == "Enabled"
        assert State.DISABLED == "Disabled"
        assert State.ABSENT == "Absent"

    def test_fan_mode_type(self) -> None:
        """Test FanModeType enum."""
        assert FanModeType.STANDARD == "Standard"
        assert FanModeType.FULL_SPEED == "FullSpeed"
        assert FanModeType.OPTIMAL == "Optimal"
        assert FanModeType.HEAVY_IO == "HeavyIO"
