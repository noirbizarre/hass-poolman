"""Tests for the Pool Manager coordinator."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_CYA_ENTITY,
    CONF_HARDNESS_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_TAC_ENTITY,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    EVENT_POOLMAN,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import ChemicalProduct, MeasureParameter, PoolMode
from tests.conftest import MOCK_CONFIG_DATA, setup_mock_states


async def _setup_coordinator(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up and return the coordinator from a config entry."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestCoordinatorInit:
    """Tests for coordinator initialization."""

    async def test_builds_pool_from_config(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Coordinator should build Pool model from config data."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.pool.volume_m3 == 50.0
        assert coordinator.pool.shape.value == "rectangular"
        assert coordinator.pool.pump_flow_m3h == 10.0

    async def test_scheduler_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Scheduler should be created when pump entity is configured."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.scheduler is not None

    async def test_scheduler_none_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Scheduler should be None when no pump entity is configured."""
        coordinator = await _setup_coordinator(hass, mock_config_entry_no_pump)
        assert coordinator.scheduler is None


class TestGetConfig:
    """Tests for _get_config precedence."""

    async def test_options_override_data(self, hass: HomeAssistant) -> None:
        """Options should take precedence over data."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            options={"pump_flow_m3h": 15.0},
            version=1,
            minor_version=3,
        )
        coordinator = await _setup_coordinator(hass, entry)
        assert coordinator.pool.pump_flow_m3h == 15.0

    async def test_data_used_when_no_options(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Data values should be used when no options are set."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.pool.pump_flow_m3h == 10.0


class TestReadSensor:
    """Tests for _read_sensor and _read_outdoor_temperature."""

    async def test_reads_valid_sensor(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should read float values from valid sensors."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        data = coordinator.data
        assert data.reading.ph == pytest.approx(7.2)
        assert data.reading.orp == pytest.approx(750.0)
        assert data.reading.temp_c == pytest.approx(26.0)

    async def test_reads_none_for_unconfigured_sensor(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None for sensors not in the config."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        data = coordinator.data
        # No TAC, CYA, or hardness entities configured
        assert data.reading.tac is None
        assert data.reading.cya is None
        assert data.reading.hardness is None

    async def test_reads_none_for_unknown_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None when sensor state is 'unknown'."""
        mock_config_entry.add_to_hass(hass)
        hass.states.async_set("sensor.pool_ph", "unknown")
        hass.states.async_set("sensor.pool_orp", "750.0")
        hass.states.async_set("sensor.pool_temperature", "26.0")
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.data.reading.ph is None

    async def test_reads_none_for_unavailable_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None when sensor state is 'unavailable'."""
        mock_config_entry.add_to_hass(hass)
        hass.states.async_set("sensor.pool_ph", "unavailable")
        hass.states.async_set("sensor.pool_orp", "750.0")
        hass.states.async_set("sensor.pool_temperature", "26.0")
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.data.reading.ph is None

    async def test_reads_none_for_non_numeric_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None when state cannot be parsed as float."""
        mock_config_entry.add_to_hass(hass)
        hass.states.async_set("sensor.pool_ph", "not_a_number")
        hass.states.async_set("sensor.pool_orp", "750.0")
        hass.states.async_set("sensor.pool_temperature", "26.0")
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.data.reading.ph is None

    async def test_reads_none_for_missing_entity(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None when sensor entity doesn't exist in HA."""
        mock_config_entry.add_to_hass(hass)
        # Only set some sensors, leaving pool_ph missing
        hass.states.async_set("sensor.pool_orp", "750.0")
        hass.states.async_set("sensor.pool_temperature", "26.0")
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        assert coordinator.data.reading.ph is None


class TestReadOutdoorTemperature:
    """Tests for outdoor temperature reading with fallback."""

    async def test_reads_from_dedicated_sensor(self, hass: HomeAssistant) -> None:
        """Should read outdoor temp from dedicated sensor entity."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_OUTDOOR_TEMPERATURE_ENTITY] = "sensor.outdoor_temp"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        hass.states.async_set("sensor.outdoor_temp", "30.0")
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.outdoor_temp_c == pytest.approx(30.0)

    async def test_falls_back_to_weather_entity(self, hass: HomeAssistant) -> None:
        """Should fall back to weather entity temperature attribute."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_WEATHER_ENTITY] = "weather.home"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        hass.states.async_set("weather.home", "sunny", {"temperature": 28.0})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.outdoor_temp_c == pytest.approx(28.0)

    async def test_weather_entity_no_temp_attr(self, hass: HomeAssistant) -> None:
        """Should return None if weather entity has no temperature attribute."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_WEATHER_ENTITY] = "weather.home"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        hass.states.async_set("weather.home", "sunny", {})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.outdoor_temp_c is None

    async def test_weather_entity_non_numeric_temp(self, hass: HomeAssistant) -> None:
        """Should return None if weather temp attribute isn't numeric."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_WEATHER_ENTITY] = "weather.home"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        hass.states.async_set("weather.home", "sunny", {"temperature": "N/A"})
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.outdoor_temp_c is None

    async def test_weather_entity_missing(self, hass: HomeAssistant) -> None:
        """Should return None if weather entity doesn't exist."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_WEATHER_ENTITY] = "weather.nonexistent"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.outdoor_temp_c is None


class TestModeProperty:
    """Tests for mode getter/setter."""

    async def test_default_mode_is_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Default mode should be ACTIVE."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE

    async def test_set_mode(self, hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
        """Setting mode should update the property."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_ACTIVE
        assert coordinator.mode == PoolMode.WINTER_ACTIVE


class TestAsyncUpdateData:
    """Tests for _async_update_data."""

    async def test_produces_pool_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Update should produce a valid PoolState."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        state = coordinator.data
        assert state is not None
        assert state.reading.ph == pytest.approx(7.2)
        assert state.filtration_hours is not None
        assert state.water_quality_score is not None
        assert state.chemistry_report is not None
        assert state.swimming_safe is True

    async def test_swimming_safe_true_in_active_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Swimming should be safe in active mode with no treatments."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE
        assert coordinator.data.swimming_safe is True

    async def test_swimming_unsafe_in_winter_active_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Swimming should be unsafe in active winter mode."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_ACTIVE
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()
        assert coordinator.data.swimming_safe is False

    async def test_swimming_unsafe_in_hibernating_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Swimming should be unsafe in hibernating mode."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.HIBERNATING
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()
        assert coordinator.data.swimming_safe is False

    async def test_swimming_unsafe_in_winter_passive_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Swimming should be unsafe in passive winter mode."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()
        assert coordinator.data.swimming_safe is False

    async def test_swimming_unsafe_in_activating_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Swimming should be unsafe in activating mode."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()
        assert coordinator.data.swimming_safe is False

    async def test_state_with_all_sensors(self, hass: HomeAssistant) -> None:
        """State should include all sensor readings when configured."""
        data = MOCK_CONFIG_DATA.copy()
        data[CONF_TAC_ENTITY] = "sensor.pool_tac"
        data[CONF_CYA_ENTITY] = "sensor.pool_cya"
        data[CONF_HARDNESS_ENTITY] = "sensor.pool_hardness"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        entry.add_to_hass(hass)
        setup_mock_states(hass)
        hass.states.async_set("sensor.pool_tac", "120.0")
        hass.states.async_set("sensor.pool_cya", "40.0")
        hass.states.async_set("sensor.pool_hardness", "250.0")
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = entry.runtime_data
        assert coordinator.data.reading.tac == pytest.approx(120.0)
        assert coordinator.data.reading.cya == pytest.approx(40.0)
        assert coordinator.data.reading.hardness == pytest.approx(250.0)


class TestFireStatusChangeEvents:
    """Tests for _fire_status_change_events."""

    async def test_no_events_on_first_update(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """No events should fire on first update (no previous state)."""
        from pytest_homeassistant_custom_component.common import async_capture_events

        events = async_capture_events(hass, EVENT_POOLMAN)
        await _setup_coordinator(hass, mock_config_entry)
        # First update already happened during setup
        assert len(events) == 0

    async def test_fires_event_on_status_change(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Events should fire when water status changes between updates."""
        from pytest_homeassistant_custom_component.common import async_capture_events

        events = async_capture_events(hass, EVENT_POOLMAN)
        coordinator = await _setup_coordinator(hass, mock_config_entry)

        # Change sensor to a bad state that creates a chemistry status change
        hass.states.async_set("sensor.pool_ph", "8.5")
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        # Should have at least one status change event
        assert len(events) > 0


class TestGetEntityId:
    """Tests for get_entity_id."""

    async def test_returns_configured_entity(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return the entity ID for a configured key."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        entity_id = coordinator.get_entity_id("ph_entity")
        assert entity_id == "sensor.pool_ph"

    async def test_returns_none_for_unconfigured(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should return None for a key not in config."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        entity_id = coordinator.get_entity_id("nonexistent_key")
        assert entity_id is None


class TestActivationLifecycle:
    """Tests for activation checklist lifecycle during mode transitions."""

    async def test_activating_mode_creates_checklist(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switching to ACTIVATING should create an activation checklist."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.activation is None
        coordinator.mode = PoolMode.ACTIVATING
        assert coordinator.activation is not None
        assert coordinator.activation.is_complete is False

    async def test_leaving_activating_clears_checklist(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switching away from ACTIVATING should clear the checklist."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        assert coordinator.activation is not None
        coordinator.mode = PoolMode.ACTIVE
        assert coordinator.activation is None

    async def test_activating_to_activating_preserves_checklist(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting ACTIVATING when already ACTIVATING should keep existing checklist."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        checklist = coordinator.activation
        assert checklist is not None
        # Set mode to ACTIVATING again
        coordinator.mode = PoolMode.ACTIVATING
        # Should be the same checklist instance (not recreated)
        assert coordinator.activation is checklist

    async def test_checklist_in_pool_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Activation checklist should be included in PoolState."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()
        assert coordinator.data.activation is not None

    async def test_pool_state_activation_none_when_not_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Activation should be None in PoolState when not in ACTIVATING mode."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.data.activation is None


class TestConfirmActivationStep:
    """Tests for async_confirm_activation_step."""

    async def test_confirm_step(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Confirming a step should mark it as completed."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        await coordinator.async_confirm_activation_step(ActivationStep.REMOVE_COVER)
        await hass.async_block_till_done()
        assert coordinator.activation is not None
        assert ActivationStep.REMOVE_COVER in coordinator.activation.completed_steps

    async def test_confirm_all_steps_switches_to_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Confirming all steps should switch mode to ACTIVE and clear checklist."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        for step in ActivationStep:
            await coordinator.async_confirm_activation_step(step)
            await hass.async_block_till_done()
        assert coordinator.mode == PoolMode.ACTIVE
        assert coordinator.activation is None

    async def test_confirm_fails_when_not_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Confirming a step when not in ACTIVATING mode should raise ValueError."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE
        with pytest.raises(ValueError, match="not in activating mode"):
            await coordinator.async_confirm_activation_step(ActivationStep.REMOVE_COVER)


class TestAutoConfirmShockTreatment:
    """Tests for auto-confirming shock_treatment via add_treatment."""

    async def test_shock_product_auto_confirms(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Recording a shock product during activation should auto-confirm shock_treatment."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        await coordinator.async_add_treatment(ChemicalProduct.CHLORE_CHOC, 200.0)
        await hass.async_block_till_done()
        assert coordinator.activation is not None
        assert ActivationStep.SHOCK_TREATMENT in coordinator.activation.completed_steps

    async def test_non_shock_product_does_not_auto_confirm(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Recording a non-shock product should not auto-confirm shock_treatment."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        await coordinator.async_add_treatment(ChemicalProduct.PH_MINUS, 100.0)
        await hass.async_block_till_done()
        assert coordinator.activation is not None
        assert ActivationStep.SHOCK_TREATMENT not in coordinator.activation.completed_steps

    async def test_shock_outside_activating_does_nothing(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Recording a shock product outside activating mode should not create a checklist."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE
        await coordinator.async_add_treatment(ChemicalProduct.CHLORE_CHOC, 200.0)
        await hass.async_block_till_done()
        assert coordinator.activation is None

    async def test_shock_auto_complete_switches_to_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """If shock_treatment is the last step, auto-confirm should switch to ACTIVE."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        # Confirm all steps except shock_treatment
        for step in ActivationStep:
            if step != ActivationStep.SHOCK_TREATMENT:
                await coordinator.async_confirm_activation_step(step)
                await hass.async_block_till_done()
        assert coordinator.mode == PoolMode.ACTIVATING
        # Auto-confirm via treatment
        await coordinator.async_add_treatment(ChemicalProduct.CHLORE_CHOC, 200.0)
        await hass.async_block_till_done()
        assert coordinator.mode == PoolMode.ACTIVE
        assert coordinator.activation is None


class TestAutoConfirmIntensiveFiltration:
    """Tests for auto-confirming intensive_filtration via scheduler event."""

    async def test_filtration_stopped_auto_confirms(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """A filtration_stopped event during activation should auto-confirm intensive_filtration."""
        from custom_components.poolman.const import EVENT_FILTRATION_STOPPED
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        # Simulate scheduler event
        coordinator._on_scheduler_event(EVENT_FILTRATION_STOPPED, {})
        await hass.async_block_till_done()
        assert coordinator.activation is not None
        assert ActivationStep.INTENSIVE_FILTRATION in coordinator.activation.completed_steps

    async def test_non_filtration_event_does_not_auto_confirm(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Other scheduler events should not auto-confirm intensive_filtration."""
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        coordinator._on_scheduler_event("filtration_started", {})
        await hass.async_block_till_done()
        assert coordinator.activation is not None
        assert ActivationStep.INTENSIVE_FILTRATION not in coordinator.activation.completed_steps

    async def test_filtration_stopped_outside_activating_does_nothing(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """filtration_stopped outside activating mode should not create a checklist."""
        from custom_components.poolman.const import EVENT_FILTRATION_STOPPED

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE
        coordinator._on_scheduler_event(EVENT_FILTRATION_STOPPED, {})
        await hass.async_block_till_done()
        assert coordinator.activation is None

    async def test_filtration_auto_complete_switches_to_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """If intensive_filtration is the last step, auto-confirm should switch to ACTIVE."""
        from custom_components.poolman.const import EVENT_FILTRATION_STOPPED
        from custom_components.poolman.domain.activation import ActivationStep

        coordinator = await _setup_coordinator(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING
        # Confirm all steps except intensive_filtration
        for step in ActivationStep:
            if step != ActivationStep.INTENSIVE_FILTRATION:
                await coordinator.async_confirm_activation_step(step)
                await hass.async_block_till_done()
        assert coordinator.mode == PoolMode.ACTIVATING
        # Auto-confirm via scheduler event
        coordinator._on_scheduler_event(EVENT_FILTRATION_STOPPED, {})
        await hass.async_block_till_done()
        assert coordinator.mode == PoolMode.ACTIVE
        assert coordinator.activation is None


class TestAsyncAddTreatment:
    """Tests for async_add_treatment."""

    async def test_warns_for_unregistered_product(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should log warning when no entity is registered for the product."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        # Unregister all treatment entities
        coordinator._treatment_entities.clear()
        # Should not raise
        await coordinator.async_add_treatment(ChemicalProduct.FLOCCULANT, 100.0)


class TestAsyncRecordMeasure:
    """Tests for async_record_measure."""

    async def test_warns_for_unregistered_parameter(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should log warning when no entity is registered for the parameter."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        # Unregister all measure entities
        coordinator._measure_entities.clear()
        # Should not raise
        await coordinator.async_record_measure(MeasureParameter.PH, 7.2)

    async def test_record_measure_triggers_refresh(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Recording a measure should trigger a coordinator refresh."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)

        # Verify measure entities are registered
        assert MeasureParameter.PH in coordinator._measure_entities

        await coordinator.async_record_measure(MeasureParameter.PH, 7.2)
        await hass.async_block_till_done()

        # After recording, the coordinator should still have valid data
        assert coordinator.data is not None


class TestReadingSourceTracking:
    """Tests for reading_sources tracking in _async_update_data."""

    async def test_sensor_values_tracked_as_sensor(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """When sensor values are available, sources should be 'sensor'."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        sources = coordinator.data.reading_sources
        assert sources.get("ph") == "sensor"
        assert sources.get("orp") == "sensor"
        assert sources.get("temperature") == "sensor"

    async def test_manual_fallback_tracked_as_manual(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """When sensor is unavailable and manual measure exists, source should be 'manual'."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)

        # Make pH sensor unavailable
        hass.states.async_set("sensor.pool_ph", "unavailable")

        # Record a manual pH measurement
        await coordinator.async_record_measure(MeasureParameter.PH, 7.3, notes="Manual test")
        await hass.async_block_till_done()

        # Force refresh
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        sources = coordinator.data.reading_sources
        assert sources.get("ph") == "manual"
        assert coordinator.data.reading.ph == pytest.approx(7.3)

    async def test_unconfigured_param_no_source(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Unconfigured parameters without manual measures should have no source."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        sources = coordinator.data.reading_sources
        # TAC is not configured in the mock config
        assert "tac" not in sources

    async def test_manual_measures_populated_after_recording(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """PoolState.manual_measures should contain the recorded measures."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)

        await coordinator.async_record_measure(MeasureParameter.PH, 7.1)
        await hass.async_block_till_done()

        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        assert MeasureParameter.PH in coordinator.data.manual_measures
        assert coordinator.data.manual_measures[MeasureParameter.PH].value == pytest.approx(7.1)


class TestAsyncSetMode:
    """Tests for async_set_mode transition side effects."""

    async def test_set_mode_updates_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting mode via async_set_mode should update the mode property."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        await coordinator.async_set_mode(PoolMode.WINTER_ACTIVE)
        assert coordinator.mode == PoolMode.WINTER_ACTIVE

    async def test_entering_winter_passive_pauses_scheduler(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Entering WINTER_PASSIVE should pause the scheduler."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.scheduler is not None
        assert coordinator.scheduler.paused is False

        await coordinator.async_set_mode(PoolMode.WINTER_PASSIVE)
        assert coordinator.scheduler.paused is True

    async def test_leaving_winter_passive_resumes_scheduler(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Leaving WINTER_PASSIVE should resume the scheduler."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.scheduler is not None

        await coordinator.async_set_mode(PoolMode.WINTER_PASSIVE)
        assert coordinator.scheduler.paused is True

        await coordinator.async_set_mode(PoolMode.ACTIVE)
        assert coordinator.scheduler.paused is False

    async def test_non_passive_to_non_passive_no_pause(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switching between non-WINTER_PASSIVE modes should not pause."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.scheduler is not None

        await coordinator.async_set_mode(PoolMode.HIBERNATING)
        assert coordinator.scheduler.paused is False

        await coordinator.async_set_mode(PoolMode.WINTER_ACTIVE)
        assert coordinator.scheduler.paused is False

    async def test_winter_passive_no_scheduler(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Entering WINTER_PASSIVE with no scheduler should not raise."""
        coordinator = await _setup_coordinator(hass, mock_config_entry_no_pump)
        assert coordinator.scheduler is None
        await coordinator.async_set_mode(PoolMode.WINTER_PASSIVE)
        assert coordinator.mode == PoolMode.WINTER_PASSIVE

    async def test_passive_to_passive_noop(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Setting WINTER_PASSIVE when already in WINTER_PASSIVE should be idempotent."""
        coordinator = await _setup_coordinator(hass, mock_config_entry)
        assert coordinator.scheduler is not None

        await coordinator.async_set_mode(PoolMode.WINTER_PASSIVE)
        assert coordinator.scheduler.paused is True

        # Second call should not error
        await coordinator.async_set_mode(PoolMode.WINTER_PASSIVE)
        assert coordinator.scheduler.paused is True
