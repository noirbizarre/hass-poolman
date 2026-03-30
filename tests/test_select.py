"""Tests for the Pool Manager select platform (pool mode and filtration duration mode)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import FiltrationDurationMode, PoolMode
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


class TestFiltrationDurationModeSelect:
    """Tests for the PoolmanFiltrationDurationModeSelect entity."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Filtration duration mode select should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_filtration_duration_mode")
        assert state is not None
        assert state.state == FiltrationDurationMode.DYNAMIC.value

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Filtration duration mode select should not be created without pump."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("select.test_pool_filtration_duration_mode")
        assert state is None

    async def test_options_include_all_modes(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Options list should contain all filtration duration modes including split."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_filtration_duration_mode")
        assert state is not None
        options = state.attributes.get("options")
        assert options is not None
        assert set(options) == {m.value for m in FiltrationDurationMode}

    async def test_select_manual(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting manual should update the coordinator."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_duration_mode",
                "option": FiltrationDurationMode.MANUAL.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.filtration_duration_mode == FiltrationDurationMode.MANUAL

    async def test_select_split_static(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting split_static should update the coordinator."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_duration_mode",
                "option": FiltrationDurationMode.SPLIT_STATIC.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.filtration_duration_mode == FiltrationDurationMode.SPLIT_STATIC

    async def test_select_split_dynamic(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting split_dynamic should update the coordinator."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_duration_mode",
                "option": FiltrationDurationMode.SPLIT_DYNAMIC.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.filtration_duration_mode == FiltrationDurationMode.SPLIT_DYNAMIC

    async def test_restore_split_static_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore split_static mode from previous state."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("select.test_pool_filtration_duration_mode", "split_static")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.SPLIT_STATIC

    async def test_restore_split_dynamic_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore split_dynamic mode from previous state."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("select.test_pool_filtration_duration_mode", "split_dynamic")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.SPLIT_DYNAMIC

    async def test_restore_invalid_mode_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should fall back to default when restored mode is invalid."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("select.test_pool_filtration_duration_mode", "invalid_mode")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.DYNAMIC
