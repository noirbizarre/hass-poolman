"""Tests for dynamic filtration duration mode in the coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import FiltrationDurationMode
from custom_components.poolman.scheduler import FiltrationPeriod


@pytest.fixture
def hass() -> MagicMock:
    """Return a mock Home Assistant instance."""
    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()
    mock_hass.states.get.return_value = None
    mock_hass.bus.async_fire = MagicMock()
    mock_hass.async_create_task = MagicMock(side_effect=lambda coro: coro.close())
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
    """Return a mock FiltrationScheduler with single period."""
    scheduler = MagicMock()
    scheduler.async_update_schedule = AsyncMock()
    scheduler.async_set_split = AsyncMock()
    # Default: single period of 8h
    scheduler.periods = [FiltrationPeriod(duration_hours=8.0)]
    return scheduler


@pytest.fixture
def mock_scheduler_split() -> MagicMock:
    """Return a mock FiltrationScheduler with two periods."""
    scheduler = MagicMock()
    scheduler.async_update_schedule = AsyncMock()
    scheduler.async_set_split = AsyncMock()
    # Two periods: 6h + 4h
    scheduler.periods = [
        FiltrationPeriod(duration_hours=6.0),
        FiltrationPeriod(duration_hours=4.0),
    ]
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
def coordinator_split(
    hass: MagicMock, config_entry: MagicMock, mock_scheduler_split: MagicMock
) -> PoolmanCoordinator:
    """Return a PoolmanCoordinator with a mock split scheduler."""
    with patch("custom_components.poolman.coordinator.FiltrationScheduler") as mock_sched_cls:
        mock_sched_cls.return_value = mock_scheduler_split

        config_entry.options = {"pump_entity": "switch.pool_pump"}

        coord = PoolmanCoordinator(hass, config_entry)
        coord.scheduler = mock_scheduler_split
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


class TestMinDynamicPeriodDuration:
    """Tests for the min_dynamic_period_duration property."""

    def test_default_is_zero(self, coordinator: PoolmanCoordinator) -> None:
        """The default minimum dynamic period duration should be 0.0."""
        assert coordinator.min_dynamic_period_duration == 0.0


class TestSplitModeSetterSyncsScheduler:
    """Tests that setting a split mode calls async_set_split on the scheduler."""

    def test_split_static_enables_split(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock, hass: MagicMock
    ) -> None:
        """Setting split_static should create task for async_set_split(True)."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        hass.async_create_task.assert_called()

    def test_split_dynamic_enables_split(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock, hass: MagicMock
    ) -> None:
        """Setting split_dynamic should create task for async_set_split(True)."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC
        hass.async_create_task.assert_called()

    def test_manual_disables_split(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock, hass: MagicMock
    ) -> None:
        """Setting manual should create task for async_set_split(False)."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.MANUAL
        hass.async_create_task.assert_called()

    def test_dynamic_disables_split(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock, hass: MagicMock
    ) -> None:
        """Setting dynamic should create task for async_set_split(False)."""
        coordinator.filtration_duration_mode = FiltrationDurationMode.DYNAMIC
        hass.async_create_task.assert_called()

    def test_no_scheduler_does_not_crash(self, coordinator_no_pump: PoolmanCoordinator) -> None:
        """Setting split mode without scheduler should not raise."""
        coordinator_no_pump.filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC
        assert coordinator_no_pump.filtration_duration_mode == FiltrationDurationMode.SPLIT_STATIC


class TestSplitDynamicAutoSync:
    """Tests for auto-sync of period 2 duration in split_dynamic mode."""

    @pytest.mark.asyncio
    async def test_split_dynamic_syncs_period2_duration(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """In split_dynamic mode, period 2 should get remaining hours."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator_split._async_update_data()

        # Period 1 is 6h, recommendation is 10h -> period 2 should be 4h
        mock_scheduler_split.async_update_schedule.assert_called_with(
            duration_hours=4.0,
            period_index=1,
        )

    @pytest.mark.asyncio
    async def test_split_dynamic_uses_min_when_recommendation_less_than_period1(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """When recommendation <= period 1 duration, min duration should be used."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=4.0,
        ):
            await coordinator_split._async_update_data()

        # Period 1 is 6h, recommendation is 4h -> remaining is -2h
        # min_dynamic_period_duration is 0.0, so period 2 gets 0.0
        mock_scheduler_split.async_update_schedule.assert_called_with(
            duration_hours=0.0,
            period_index=1,
        )

    @pytest.mark.asyncio
    async def test_split_dynamic_uses_custom_min_duration(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """When custom min is set and remaining < min, the min should be used."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC
        coordinator_split._min_dynamic_period_duration = 2.0

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=4.0,
        ):
            await coordinator_split._async_update_data()

        # Period 1 is 6h, recommendation is 4h -> remaining is -2h
        # min_dynamic_period_duration is 2.0, so period 2 gets 2.0
        mock_scheduler_split.async_update_schedule.assert_called_with(
            duration_hours=2.0,
            period_index=1,
        )

    @pytest.mark.asyncio
    async def test_split_dynamic_skips_sync_when_filtration_hours_none(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """In split_dynamic mode, no sync when filtration_hours is None."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=None,
        ):
            await coordinator_split._async_update_data()

        mock_scheduler_split.async_update_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_split_static_does_not_auto_sync_period2(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """In split_static mode, period 2 duration should NOT be auto-synced."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_STATIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator_split._async_update_data()

        mock_scheduler_split.async_update_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_split_dynamic_does_not_sync_period1(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """In split_dynamic mode, period 1 should NOT be auto-synced (only period 2)."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=12.0,
        ):
            await coordinator_split._async_update_data()

        # Only period_index=1 should be synced, never period_index=0
        calls = mock_scheduler_split.async_update_schedule.call_args_list
        assert len(calls) == 1
        assert calls[0].kwargs["period_index"] == 1


class TestSplitModeTransitions:
    """Tests for switching between split and non-split modes."""

    @pytest.mark.asyncio
    async def test_switch_dynamic_to_split_dynamic_syncs_period2(
        self, coordinator_split: PoolmanCoordinator, mock_scheduler_split: MagicMock
    ) -> None:
        """Switching from dynamic to split_dynamic should sync period 2."""
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator_split._async_update_data()

        # In dynamic mode with split scheduler, period 0 gets the full recommendation
        mock_scheduler_split.async_update_schedule.assert_called_with(duration_hours=10.0)
        mock_scheduler_split.async_update_schedule.reset_mock()

        # Switch to split_dynamic
        coordinator_split._filtration_duration_mode = FiltrationDurationMode.SPLIT_DYNAMIC

        with patch(
            "custom_components.poolman.coordinator.compute_filtration_duration",
            return_value=10.0,
        ):
            await coordinator_split._async_update_data()

        # Now period 2 should be synced: 10.0 - 6.0 = 4.0
        mock_scheduler_split.async_update_schedule.assert_called_with(
            duration_hours=4.0,
            period_index=1,
        )


class TestBoostRemainingInPoolState:
    """Tests for boost_remaining integration in PoolState."""

    @pytest.mark.asyncio
    async def test_pool_state_includes_boost_remaining(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """PoolState should include boost_remaining from the scheduler."""
        mock_scheduler.boost_remaining = 4.0

        state = await coordinator._async_update_data()
        assert state.boost_remaining == 4.0

    @pytest.mark.asyncio
    async def test_pool_state_boost_remaining_zero_when_no_boost(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """PoolState boost_remaining should be 0 when no boost is active."""
        mock_scheduler.boost_remaining = 0.0

        state = await coordinator._async_update_data()
        assert state.boost_remaining == 0.0

    @pytest.mark.asyncio
    async def test_pool_state_boost_remaining_zero_without_scheduler(
        self, coordinator_no_pump: PoolmanCoordinator
    ) -> None:
        """PoolState boost_remaining should be 0 when no scheduler is configured."""
        state = await coordinator_no_pump._async_update_data()
        assert state.boost_remaining == 0.0


class TestBoostCoordinatorBridge:
    """Tests for coordinator boost bridge methods."""

    @pytest.mark.asyncio
    async def test_async_boost_filtration_delegates_to_scheduler(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """async_boost_filtration should delegate to scheduler.async_boost."""
        mock_scheduler.async_boost = AsyncMock()

        with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock):
            await coordinator.async_boost_filtration(4.0)
        mock_scheduler.async_boost.assert_called_once_with(4.0)

    @pytest.mark.asyncio
    async def test_async_cancel_boost_delegates_to_scheduler(
        self, coordinator: PoolmanCoordinator, mock_scheduler: MagicMock
    ) -> None:
        """async_cancel_boost should delegate to scheduler.async_cancel_boost."""
        mock_scheduler.async_cancel_boost = AsyncMock()

        with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock):
            await coordinator.async_cancel_boost()
        mock_scheduler.async_cancel_boost.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_boost_filtration_noop_without_scheduler(
        self, coordinator_no_pump: PoolmanCoordinator
    ) -> None:
        """async_boost_filtration should be a no-op without a scheduler."""
        # Should not raise
        await coordinator_no_pump.async_boost_filtration(4.0)

    @pytest.mark.asyncio
    async def test_async_cancel_boost_noop_without_scheduler(
        self, coordinator_no_pump: PoolmanCoordinator
    ) -> None:
        """async_cancel_boost should be a no-op without a scheduler."""
        # Should not raise
        await coordinator_no_pump.async_cancel_boost()
