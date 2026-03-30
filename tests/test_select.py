"""Tests for the Pool Manager select platform (pool mode)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import PoolMode
from tests.conftest import setup_mock_states


async def _setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up integration and return coordinator."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestPoolModeSelect:
    """Tests for the PoolmanModeSelect entity."""

    async def test_entity_created(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Mode select entity should be created."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        assert state.state == PoolMode.RUNNING.value

    async def test_select_winter_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting winter_active should update mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_pool_mode",
                "option": PoolMode.WINTER_ACTIVE.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.mode == PoolMode.WINTER_ACTIVE
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        assert state.state == PoolMode.WINTER_ACTIVE.value

    async def test_select_winter_passive(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting winter_passive should update mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_pool_mode",
                "option": PoolMode.WINTER_PASSIVE.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.mode == PoolMode.WINTER_PASSIVE
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        assert state.state == PoolMode.WINTER_PASSIVE.value

    async def test_options_list(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Options list should contain all pool modes."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        options = state.attributes.get("options")
        assert options is not None
        assert set(options) == {m.value for m in PoolMode}
