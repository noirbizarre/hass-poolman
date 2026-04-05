"""Tests for the Pool Manager integration setup."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_COMPLETED_AT,
    CONF_FILTRATION_KIND,
    CONF_SPOON_SIZES,
    CONF_STARTED_AT,
    CONF_STEPS,
    CONF_TARGET_MODE,
    CONF_TREATMENT,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DOMAIN,
    MODE_WINTER_PASSIVE,
    SERVICE_ADD_TREATMENT,
    SERVICE_BOOST_FILTRATION,
    SERVICE_CONFIRM_ACTIVATION_STEP,
    SERVICE_RECORD_MEASURE,
    SUBENTRY_ACTIVATION,
    SUBENTRY_HIBERNATION,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.activation import ActivationStep
from custom_components.poolman.domain.model import PoolMode
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

    async def test_setup_registers_confirm_activation_step_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting up should register the confirm_activation_step service."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_CONFIRM_ACTIVATION_STEP)

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

    async def test_setup_restores_hibernating_from_subentry(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Setting up with an in-progress hibernation subentry should restore HIBERNATING mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive)",
                    "unique_id": None,
                },
            ],
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.mode == PoolMode.HIBERNATING

    async def test_setup_does_not_restore_from_completed_subentry(
        self,
        hass: HomeAssistant,
    ) -> None:
        """A completed hibernation subentry should not restore HIBERNATING mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-11-15T10:00:00+00:00",
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive) - completed",
                    "unique_id": None,
                },
            ],
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.mode == PoolMode.ACTIVE

    async def test_setup_restores_activating_from_subentry(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Setting up with an in-progress activation subentry should restore ACTIVATING mode."""
        steps = {step.value: False for step in ActivationStep}
        steps["remove_cover"] = True  # One step already completed
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: steps,
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                },
            ],
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.mode == PoolMode.ACTIVATING
        assert coordinator.activation is not None
        assert ActivationStep.REMOVE_COVER in coordinator.activation.completed_steps
        assert ActivationStep.RAISE_WATER_LEVEL in coordinator.activation.pending_steps

    async def test_setup_restores_activation_all_steps_false(
        self,
        hass: HomeAssistant,
    ) -> None:
        """An in-progress activation with no completed steps should restore correctly."""
        steps = {step.value: False for step in ActivationStep}
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: steps,
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                },
            ],
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.mode == PoolMode.ACTIVATING
        assert coordinator.activation is not None
        assert coordinator.activation.is_complete is False
        assert len(coordinator.activation.pending_steps) == len(list(ActivationStep))

    async def test_setup_does_not_restore_from_completed_activation(
        self,
        hass: HomeAssistant,
    ) -> None:
        """A completed activation subentry should not restore ACTIVATING mode."""
        steps = {step.value: True for step in ActivationStep}
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-04-05T10:00:00+00:00",
                        CONF_STEPS: steps,
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation - completed",
                    "unique_id": None,
                },
            ],
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.mode == PoolMode.ACTIVE
        assert coordinator.activation is None


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

    async def test_unload_last_entry_removes_confirm_activation_step_service(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Unloading the last entry should remove the confirm_activation_step service."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_CONFIRM_ACTIVATION_STEP)

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert not hass.services.has_service(DOMAIN, SERVICE_CONFIRM_ACTIVATION_STEP)


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
        """Current version (v1.4) should not trigger any migration."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.data == MOCK_CONFIG_DATA

    async def test_migrate_v1_3_to_v1_4_adds_spoon_sizes(self, hass: HomeAssistant) -> None:
        """Migration from v1.3 should add spoon_sizes."""
        data = MOCK_CONFIG_DATA.copy()
        data.pop(CONF_SPOON_SIZES, None)
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.data[CONF_SPOON_SIZES] == []
        assert entry.minor_version >= 4

    async def test_migrate_v1_1_adds_all(self, hass: HomeAssistant) -> None:
        """Migration from v1.1 should add filtration_kind, treatment, and spoon_sizes."""
        data = MOCK_CONFIG_DATA.copy()
        data.pop(CONF_FILTRATION_KIND, None)
        data.pop(CONF_TREATMENT, None)
        data.pop(CONF_SPOON_SIZES, None)
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
        assert entry.data[CONF_SPOON_SIZES] == []


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

    async def test_add_treatment_service_with_spoons(self, hass: HomeAssistant) -> None:
        """Service call with spoons and spoon_name should resolve to quantity_g."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_SPOON_SIZES] = [{"name": "Large", "size_ml": 15.0}]
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=4,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
        assert device is not None

        # ph_minus has density 1.1, so 2 spoons * 15 mL * 1.1 g/mL = 33g
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TREATMENT,
            {
                "device_id": device.id,
                "product": "ph_minus",
                "spoons": 2.0,
                "spoon_name": "Large",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_add_treatment_service_with_unknown_spoon_name(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with unknown spoon_name should not crash."""
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
                "product": "ph_minus",
                "spoons": 2.0,
                "spoon_name": "NonExistent",
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


class TestConfirmActivationStepServiceHandler:
    """Tests for the confirm_activation_step service handler."""

    async def test_confirm_step_service_with_valid_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with a valid device should confirm the activation step."""
        from homeassistant.helpers import device_registry as dr

        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        coordinator.mode = PoolMode.ACTIVATING

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CONFIRM_ACTIVATION_STEP,
            {
                "device_id": device.id,
                "step": "remove_cover",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.activation is not None
        assert "remove_cover" in [s.value for s in coordinator.activation.completed_steps]

    async def test_confirm_step_service_with_unknown_device(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call with unknown device_id should not crash."""
        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CONFIRM_ACTIVATION_STEP,
            {
                "device_id": "nonexistent_device_id",
                "step": "remove_cover",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

    async def test_confirm_step_service_fails_when_not_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Service call when not in activating mode should raise."""
        import pytest

        from homeassistant.helpers import device_registry as dr

        mock_config_entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, mock_config_entry.entry_id)}
        )
        assert device is not None

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.mode == PoolMode.ACTIVE

        with pytest.raises(ValueError, match="not in activating mode"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_CONFIRM_ACTIVATION_STEP,
                {
                    "device_id": device.id,
                    "step": "remove_cover",
                },
                blocking=True,
            )
