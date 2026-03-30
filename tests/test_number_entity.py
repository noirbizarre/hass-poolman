"""Tests for the Pool Manager number platform (filtration duration)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    DEFAULT_FILTRATION_DURATION_HOURS,
    DEFAULT_FILTRATION_DURATION_HOURS_2,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import FiltrationDurationMode
from tests.conftest import setup_mock_states


async def _setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up integration and return coordinator."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestFiltrationDuration:
    """Tests for the PoolmanFiltrationDuration entity."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Number entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Number entity should not be created when no pump is configured."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is None

    async def test_set_value(self, hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
        """Setting a value should update the entity and scheduler."""
        await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.test_pool_filtration_duration", "value": 12.0},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == 12.0

    async def test_restore_valid_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore a previously saved duration value."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration", "6.5")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == 6.5

    async def test_restore_unknown_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unknown'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration", "unknown")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS

    async def test_restore_unavailable_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unavailable'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration", "unavailable")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS

    async def test_restore_invalid_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state can't be parsed as float."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration", "bad_value")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("number.test_pool_filtration_duration")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS


class TestFiltrationDuration2:
    """Tests for the PoolmanFiltrationDuration2 entity (period 2)."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("number.test_pool_filtration_duration_2")
        # Entity exists but is unavailable in default (dynamic) mode
        assert state is not None
        assert state.state == "unavailable"

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Period 2 number entity should not be created when no pump is configured."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is None

    async def test_unavailable_in_manual_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should be unavailable in manual mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert state.state == "unavailable"

    async def test_unavailable_in_dynamic_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should be unavailable in dynamic mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert state.state == "unavailable"

    async def test_available_in_split_static_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should be available in split_static mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await hass.async_block_till_done()
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS_2

    async def test_available_in_split_dynamic_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should be available in split_dynamic mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC
        await hass.async_block_till_done()
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert state.state != "unavailable"

    async def test_min_value_is_zero(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 number entity should accept 0.0 as minimum value."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert float(state.attributes["min"]) == 0.0

    async def test_restore_valid_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore a previously saved duration value."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration_2", "3.5")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert float(state.state) == 3.5

    async def test_restore_unknown_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unknown'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("number.test_pool_filtration_duration_2", "unknown")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("number.test_pool_filtration_duration_2")
        assert state is not None
        assert float(state.state) == DEFAULT_FILTRATION_DURATION_HOURS_2
