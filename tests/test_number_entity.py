"""Tests for the Pool Manager number platform (filtration duration)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import DEFAULT_FILTRATION_DURATION_HOURS
from custom_components.poolman.coordinator import PoolmanCoordinator
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
