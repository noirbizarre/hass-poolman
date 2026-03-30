"""Tests for the Pool Manager time platform (filtration start time)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    DEFAULT_FILTRATION_START_TIME,
    DEFAULT_FILTRATION_START_TIME_2,
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


class TestFiltrationStartTime:
    """Tests for the PoolmanFiltrationStartTime entity."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Time entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is not None
        assert state.state == "10:00:00"

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Time entity should not be created when no pump is configured."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is None

    async def test_set_value(self, hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
        """Setting a value should update the entity and scheduler."""
        await _setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": "time.test_pool_filtration_start_time", "time": "14:30:00"},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is not None
        assert state.state == "14:30:00"

    async def test_restore_valid_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore a previously saved time value."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("time.test_pool_filtration_start_time", "08:15:00")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is not None
        assert state.state == "08:15:00"

    async def test_restore_unknown_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unknown'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("time.test_pool_filtration_start_time", "unknown")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is not None
        assert state.state == str(DEFAULT_FILTRATION_START_TIME)

    async def test_restore_unavailable_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unavailable'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("time.test_pool_filtration_start_time", "unavailable")],
        )
        await _setup_integration(hass, mock_config_entry)

        state = hass.states.get("time.test_pool_filtration_start_time")
        assert state is not None
        assert state.state == str(DEFAULT_FILTRATION_START_TIME)


class TestFiltrationStartTime2:
    """Tests for the PoolmanFiltrationStartTime2 entity (period 2)."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 time entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("time.test_pool_filtration_start_time_2")
        # Entity exists but is unavailable in default (dynamic) mode
        assert state is not None
        assert state.state == "unavailable"

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Period 2 time entity should not be created when no pump is configured."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is None

    async def test_unavailable_in_manual_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 time entity should be unavailable in manual mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == "unavailable"

    async def test_unavailable_in_dynamic_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 time entity should be unavailable in dynamic mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == "unavailable"

    async def test_available_in_split_static_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 time entity should be available in split_static mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await hass.async_block_till_done()
        # Trigger a coordinator update to propagate availability
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == str(DEFAULT_FILTRATION_START_TIME_2)

    async def test_available_in_split_dynamic_mode(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Period 2 time entity should be available in split_dynamic mode."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC
        await hass.async_block_till_done()
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == str(DEFAULT_FILTRATION_START_TIME_2)

    async def test_restore_valid_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should restore a previously saved time value."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("time.test_pool_filtration_start_time_2", "14:30:00")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == "14:30:00"

    async def test_restore_unknown_uses_default(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Should use default when restored state is 'unknown'."""
        from pytest_homeassistant_custom_component.common import mock_restore_cache

        mock_restore_cache(
            hass,
            [State("time.test_pool_filtration_start_time_2", "unknown")],
        )
        coordinator = await _setup_integration(hass, mock_config_entry)
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("time.test_pool_filtration_start_time_2")
        assert state is not None
        assert state.state == str(DEFAULT_FILTRATION_START_TIME_2)
