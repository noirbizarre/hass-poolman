"""Tests for the Pool Manager switch platform (filtration control)."""

from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from tests.conftest import setup_mock_states


async def _setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up integration and return coordinator."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestFiltrationControlSwitch:
    """Tests for the PoolmanFiltrationControlSwitch entity."""

    async def test_switch_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switch entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is not None
        assert state.state == STATE_OFF

    async def test_switch_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Switch should not be created when no pump entity is configured."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is None

    async def test_turn_on(self, hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
        """Turning on should enable the scheduler."""
        await _setup_integration(hass, mock_config_entry)
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.test_pool_filtration_control"},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is not None
        assert state.state == STATE_ON

    async def test_turn_off(self, hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
        """Turning off should disable the scheduler."""
        await _setup_integration(hass, mock_config_entry)

        # Turn on first
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.test_pool_filtration_control"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Now turn off
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.test_pool_filtration_control"},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is not None
        assert state.state == STATE_OFF

    async def test_restore_on_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switch should restore 'on' state and re-enable scheduler."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("switch.test_pool_filtration_control", STATE_ON)],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is not None
        assert state.state == STATE_ON

    async def test_restore_off_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Switch should restore 'off' state."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("switch.test_pool_filtration_control", STATE_OFF)],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("switch.test_pool_filtration_control")
        assert state is not None
        assert state.state == STATE_OFF
