"""Tests for the Pool Manager integration setup."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_FILTRATION_KIND,
    CONF_TREATMENT,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DOMAIN,
    SERVICE_ADD_TREATMENT,
    SERVICE_BOOST_FILTRATION,
    SERVICE_RECORD_MEASURE,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from tests.conftest import MOCK_CONFIG_DATA, setup_mock_states


class TestSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_creates_coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting up the entry should store a coordinator in runtime_data."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert isinstance(mock_config_entry.runtime_data, PoolmanCoordinator)

    async def test_setup_registers_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting up should register the add_treatment and record_measure services."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT)
        assert hass.services.has_service(DOMAIN, SERVICE_RECORD_MEASURE)

    async def test_setup_registers_boost_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting up should register the boost_filtration service."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_BOOST_FILTRATION)

    async def test_service_registration_idempotent(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Calling _async_register_services twice should not fail."""
        from custom_components.poolman import _async_register_services

        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT)

        # Call again -- should be a no-op, not raise
        _async_register_services(hass)
        assert hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT)


class TestUnloadEntry:
    """Tests for async_unload_entry."""

    async def test_unload_entry(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Unloading should succeed and return True."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.async_unload(mock_config_entry.entry_id)
        assert result is True

    async def test_unload_last_entry_removes_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Unloading the last entry should remove both services."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT)
        assert hass.services.has_service(DOMAIN, SERVICE_RECORD_MEASURE)

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert not hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT)
        assert not hass.services.has_service(DOMAIN, SERVICE_RECORD_MEASURE)

    async def test_unload_last_entry_removes_boost_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Unloading the last entry should remove the boost service."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_BOOST_FILTRATION)

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert not hass.services.has_service(DOMAIN, SERVICE_BOOST_FILTRATION)


class TestMigrateEntry:
    """Tests for async_migrate_entry."""

    async def test_migrate_v1_1_to_v1_2_adds_filtration_kind(self, hass: HomeAssistant) -> None:
        """Migration from v1.1 should add filtration_kind."""
        data = MOCK_CONFIG_DATA.copy()
        data.pop(CONF_FILTRATION_KIND, None)
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old Pool",
            data=data,
            version=1,
            minor_version=1,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.data[CONF_FILTRATION_KIND] == DEFAULT_FILTRATION_KIND
        assert entry.minor_version >= 2

    async def test_migrate_v1_2_to_v1_3_adds_treatment(self, hass: HomeAssistant) -> None:
        """Migration from v1.2 should add treatment."""
        data = MOCK_CONFIG_DATA.copy()
        data.pop(CONF_TREATMENT, None)
        data[CONF_FILTRATION_KIND] = "sand"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old Pool",
            data=data,
            version=1,
            minor_version=2,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.data[CONF_TREATMENT] == DEFAULT_TREATMENT
        assert entry.minor_version >= 3

    async def test_migrate_v1_1_adds_both(self, hass: HomeAssistant) -> None:
        """Migration from v1.1 should add both filtration_kind and treatment."""
        data = MOCK_CONFIG_DATA.copy()
        data.pop(CONF_FILTRATION_KIND, None)
        data.pop(CONF_TREATMENT, None)
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old Pool",
            data=data,
            version=1,
            minor_version=1,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.data[CONF_FILTRATION_KIND] == DEFAULT_FILTRATION_KIND
        assert entry.data[CONF_TREATMENT] == DEFAULT_TREATMENT

    async def test_current_version_no_migration(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Current version (v1.3) should not trigger any migration."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.data == MOCK_CONFIG_DATA


class TestServiceHandler:
    """Tests for the add_treatment service handler."""

    async def test_add_treatment_service_with_valid_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with a valid device should invoke the coordinator."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Get the device ID from the registry
        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TREATMENT,
            {
                "device_id": device.id,
                "product": "ph_minus",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_add_treatment_service_with_unknown_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with unknown device_id should log warning and not crash."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TREATMENT,
            {
                "device_id": "nonexistent_device_id",
                "product": "ph_minus",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_add_treatment_service_with_quantity_and_notes(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with quantity and notes should pass them through."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TREATMENT,
            {
                "device_id": device.id,
                "product": "flocculant",
                "quantity_g": 50.0,
                "notes": "Test note",
            },
            blocking=True,
        )
        await hass.async_block_till_done()


class TestUpdateListener:
    """Tests for _async_update_listener."""

    async def test_options_change_triggers_reload(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Changing options should trigger a reload via the update listener."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Update options, which should trigger the listener and reload
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={"pump_flow_m3h": 15.0},
        )
        await hass.async_block_till_done()

        # After reload, the coordinator should reflect the new value
        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.pool.pump_flow_m3h == 15.0


class TestRecordMeasureServiceHandler:
    """Tests for the record_measure service handler."""

    async def test_record_measure_service_with_valid_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with a valid device should invoke the coordinator."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_MEASURE,
            {
                "device_id": device.id,
                "parameter": "ph",
                "value": 7.2,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_record_measure_service_with_notes(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with notes should pass them through."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_MEASURE,
            {
                "device_id": device.id,
                "parameter": "orp",
                "value": 750.0,
                "notes": "Test measurement",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_record_measure_service_with_unknown_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with unknown device_id should not crash."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_MEASURE,
            {
                "device_id": "nonexistent_device_id",
                "parameter": "ph",
                "value": 7.0,
            },
            blocking=True,
        )
        await hass.async_block_till_done()


class TestBoostServiceHandler:
    """Tests for the boost_filtration service handler."""

    async def test_boost_service_with_valid_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with a valid device should activate boost on the coordinator."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_BOOST_FILTRATION,
            {
                "device_id": device.id,
                "hours": 4.0,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.scheduler is not None
        assert coordinator.scheduler.boost_active is True

    async def test_boost_service_zero_hours_cancels(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with hours=0 should cancel any active boost."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        # Activate a boost first
        await hass.services.async_call(
            DOMAIN,
            SERVICE_BOOST_FILTRATION,
            {"device_id": device.id, "hours": 4.0},
            blocking=True,
        )
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.scheduler is not None
        assert coordinator.scheduler.boost_active is True

        # Cancel with hours=0
        await hass.services.async_call(
            DOMAIN,
            SERVICE_BOOST_FILTRATION,
            {"device_id": device.id, "hours": 0},
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.scheduler.boost_active is False

    async def test_boost_service_with_unknown_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with unknown device_id should log warning and not crash."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_BOOST_FILTRATION,
            {
                "device_id": "nonexistent_device_id",
                "hours": 4.0,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
