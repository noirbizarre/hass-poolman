"""Tests for dynamic filtration duration mode in the coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import FiltrationDurationMode


@pytest.fixture
def hass() -> MagicMock:
    """Return a mock Home Assistant instance."""
    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()
    mock_hass.states.get.return_value = None
    mock_hass.bus.async_fire = MagicMock()
    return mock_hass


@pytest.fixture
def config_entry() -> MagicMock:
    """Return a mock config entry with pool data."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "pool_name": "Test Pool",
        "volume_m3": 50.0,
        "shape": "rectangular",
        "pump_flow_m3h": 10.0,
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_scheduler() -> MagicMock:
    """Return a mock FiltrationScheduler."""
    scheduler = MagicMock()
    scheduler.async_update_schedule = AsyncMock()
    return scheduler


@pytest.fixture
def coordinator(
    hass: MagicMock, config_entry: MagicMock, mock_scheduler: MagicMock
) -> PoolmanCoordinator:
    """Return a PoolmanCoordinator with a mock scheduler."""
    with patch("custom_components.poolman.coordinator.FiltrationScheduler") as mock_sched_cls:
        mock_sched_cls.return_value = mock_scheduler

        # Set up pump entity so scheduler is created
        config_entry.options = {"pump_entity": "switch.pool_pump"}

        coord = PoolmanCoordinator(hass, config_entry)
        coord.scheduler = mock_scheduler
        return coord


@pytest.fixture
def coordinator_no_pump(hass: MagicMock, config_entry: MagicMock) -> PoolmanCoordinator:
    """Return a PoolmanCoordinator without a pump entity (no scheduler)."""
    coord = PoolmanCoordinator(hass, config_entry)
    assert coord.scheduler is None
    return coord


class TestFiltrationDurationModeProperty:
    """Tests for the filtration_duration_mode property."""

    def test_default_mode_is_dynamic(self, coordinator: PoolmanCoordinator) -> None:
        """The default filtration duration mode should be dynamic."""
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.DYNAMIC

    def test_set_mode_to_manual(self, coordinator: PoolmanCoordinator) -> None:
        """Setting the mode to manual should be stored."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.MANUAL

    def test_set_mode_to_dynamic(self, coordinator: PoolmanCoordinator) -> None:
        """Setting the mode back to dynamic should be stored."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC
        assert coordinator.filtration_duration_mode == FiltrationDurationMode.DYNAMIC


class TestDynamicModeAutoSync:
    """Tests for auto-sync of scheduler duration in dynamic mode."""

    @pytest.mark.asyncio
    async def test_dynamic_mode_syncs_scheduler(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """In dynamic mode, computed filtration_hours should sync to the scheduler."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        state = await coordinator._async_update_data()

        # If filtration_hours is not None, scheduler should have been called
        if state.filtration_hours is not None:
            mock_scheduler.async_update_schedule.assert_called_with(
                duration_hours=state.filtration_hours
            )

    @pytest.mark.asyncio
    async def test_manual_mode_does_not_sync_scheduler(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """In manual mode, computed filtration_hours should NOT sync to the scheduler."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL

        await coordinator._async_update_data()

        mock_scheduler.async_update_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_dynamic_mode_skips_sync_when_filtration_hours_is_none(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """In dynamic mode, scheduler should not be updated when filtration_hours is None."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=None,
        ):
            await coordinator._async_update_data()

        mock_scheduler.async_update_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_dynamic_mode_syncs_with_computed_value(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """In dynamic mode, scheduler should receive the exact computed value."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=6.5,
        ):
            await coordinator._async_update_data()

        mock_scheduler.async_update_schedule.assert_called_once_with(duration_hours=6.5)

    @pytest.mark.asyncio
    async def test_no_scheduler_does_not_crash_in_dynamic_mode(
        self, coordinator_no_pump: PoolmanCoordinator
    ) -> None:
        """Dynamic mode with no scheduler should not raise an error."""
        coordinator_no_pump.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        # Should not raise
        await coordinator_no_pump._async_update_data()


class TestModeTransitions:
    """Tests for switching between manual and dynamic modes."""

    @pytest.mark.asyncio
    async def test_switch_manual_to_dynamic_syncs_on_next_update(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """Switching from manual to dynamic should sync on the next coordinator update."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator._async_update_data()

        # Manual mode: no sync
        mock_scheduler.async_update_schedule.assert_not_called()

        # Switch to dynamic
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator._async_update_data()

        # Dynamic mode: should sync
        mock_scheduler.async_update_schedule.assert_called_once_with(duration_hours=10.0)

    @pytest.mark.asyncio
    async def test_switch_dynamic_to_manual_stops_syncing(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """Switching from dynamic to manual should stop syncing."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=7.0,
        ):
            await coordinator._async_update_data()

        mock_scheduler.async_update_schedule.assert_called_once_with(duration_hours=7.0)
        mock_scheduler.async_update_schedule.reset_mock()

        # Switch to manual
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=9.0,
        ):
            await coordinator._async_update_data()

        mock_scheduler.async_update_schedule.assert_not_called()
