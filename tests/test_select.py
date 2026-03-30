"""Tests for the Pool Manager select platform (pool mode, filtration duration mode, and boost)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import BOOST_PRESET_NONE, BOOST_PRESETS
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
        assert state.state == PoolMode.ACTIVE.value

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

    async def test_select_hibernating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting hibernating should update mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_pool_mode",
                "option": PoolMode.HIBERNATING.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.mode == PoolMode.HIBERNATING
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        assert state.state == PoolMode.HIBERNATING.value

    async def test_select_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting activating should update mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_pool_mode",
                "option": PoolMode.ACTIVATING.value,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.mode == PoolMode.ACTIVATING
        state = hass.states.get("select.test_pool_pool_mode")
        assert state is not None
        assert state.state == PoolMode.ACTIVATING.value

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


class TestFiltrationBoostSelect:
    """Tests for the PoolmanFiltrationBoostSelect entity."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Filtration boost select should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_filtration_boost")
        assert state is not None
        assert state.state == BOOST_PRESET_NONE

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Filtration boost select should not be created without pump."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("select.test_pool_filtration_boost")
        assert state is None

    async def test_options_match_presets(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Options list should contain all boost presets."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_filtration_boost")
        assert state is not None
        options = state.attributes.get("options")
        assert options == BOOST_PRESETS

    async def test_select_preset_activates_boost(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting a preset should activate a boost on the scheduler."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_boost",
                "option": "4",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert coordinator.scheduler is not None
        assert coordinator.scheduler.boost_active is True

    async def test_select_none_cancels_boost(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Selecting 'none' should cancel any active boost."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        # First activate a boost
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_boost",
                "option": "4",
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        assert coordinator.scheduler is not None
        assert coordinator.scheduler.boost_active is True

        # Then cancel it
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": "select.test_pool_filtration_boost",
                "option": BOOST_PRESET_NONE,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        assert coordinator.scheduler.boost_active is False

    async def test_boost_end_in_extra_attributes(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Extra state attributes should contain boost_end for persistence."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("select.test_pool_filtration_boost")
        assert state is not None
        # Before boost, boost_end should be None
        assert state.attributes.get("boost_end") is None

    async def test_restore_boost_from_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore boost from persisted boost_end attribute."""
        from datetime import timedelta

        from homeassistant.util import dt as dt_util
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        future = dt_util.now() + timedelta(hours=3)
        mock_restore_cache(
            hass,
            [
                State(
                    "select.test_pool_filtration_boost",
                    "4",
                    {"boost_end": future.isoformat()},
                )
            ],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        assert coordinator.scheduler is not None
        assert coordinator.scheduler.boost_active is True
