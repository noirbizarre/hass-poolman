"""Tests for the FiltrationScheduler and FiltrationPeriod."""

from __future__ import annotations

from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.poolman.const import (
    DEFAULT_FILTRATION_DURATION_HOURS,
    DEFAULT_FILTRATION_DURATION_HOURS_2,
    DEFAULT_FILTRATION_START_TIME,
    DEFAULT_FILTRATION_START_TIME_2,
    EVENT_FILTRATION_STARTED,
    EVENT_FILTRATION_STOPPED,
)
from custom_components.poolman.scheduler import FiltrationPeriod, FiltrationScheduler


@pytest.fixture
def hass() -> MagicMock:
    """Return a mock Home Assistant instance."""
    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()
    return mock_hass


@pytest.fixture
def scheduler(hass: MagicMock) -> FiltrationScheduler:
    """Return a FiltrationScheduler with default settings."""
    return FiltrationScheduler(hass, "switch.pool_pump")


# ---------- FiltrationPeriod ----------


class TestFiltrationPeriod:
    """Tests for the FiltrationPeriod dataclass."""

    def test_default_values(self) -> None:
        """Period should use default start time and duration."""
        period = FiltrationPeriod()
        assert period.start_time == DEFAULT_FILTRATION_START_TIME
        assert period.duration_hours == DEFAULT_FILTRATION_DURATION_HOURS

    def test_custom_values(self) -> None:
        """Period should accept custom start time and duration."""
        period = FiltrationPeriod(start_time=time(14, 0), duration_hours=4.0)
        assert period.start_time == time(14, 0)
        assert period.duration_hours == 4.0

    def test_end_time_same_day(self) -> None:
        """10:00 + 8h = 18:00."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.end_time == time(18, 0)

    def test_end_time_cross_midnight(self) -> None:
        """22:00 + 8h = 06:00 next day."""
        period = FiltrationPeriod(start_time=time(22, 0), duration_hours=8.0)
        assert period.end_time == time(6, 0)

    def test_end_time_half_hour(self) -> None:
        """10:00 + 4.5h = 14:30."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=4.5)
        assert period.end_time == time(14, 30)

    def test_contains_inside_same_day(self) -> None:
        """Time within same-day period should return True."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.contains(time(14, 0)) is True

    def test_contains_before_same_day(self) -> None:
        """Time before same-day period should return False."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.contains(time(9, 0)) is False

    def test_contains_after_same_day(self) -> None:
        """Time after same-day period should return False."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.contains(time(19, 0)) is False

    def test_contains_at_start_boundary(self) -> None:
        """Start boundary is inclusive."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.contains(time(10, 0)) is True

    def test_contains_at_end_boundary(self) -> None:
        """End boundary is exclusive."""
        period = FiltrationPeriod(start_time=time(10, 0), duration_hours=8.0)
        assert period.contains(time(18, 0)) is False

    def test_contains_cross_midnight_evening(self) -> None:
        """Evening side of cross-midnight period should return True."""
        period = FiltrationPeriod(start_time=time(22, 0), duration_hours=8.0)
        assert period.contains(time(23, 30)) is True

    def test_contains_cross_midnight_morning(self) -> None:
        """Morning side of cross-midnight period should return True."""
        period = FiltrationPeriod(start_time=time(22, 0), duration_hours=8.0)
        assert period.contains(time(4, 0)) is True

    def test_contains_cross_midnight_outside(self) -> None:
        """Time outside cross-midnight period should return False."""
        period = FiltrationPeriod(start_time=time(22, 0), duration_hours=8.0)
        assert period.contains(time(12, 0)) is False


# ---------- FiltrationScheduler: single-period tests ----------


class TestIsInActiveWindow:
    """Tests for is_in_active_window with same-day and cross-midnight windows."""

    def test_same_day_inside_window(self, scheduler: FiltrationScheduler) -> None:
        """Time within a same-day window should return True."""
        # Default: 10:00 start, 8h duration -> 10:00-18:00
        now = datetime(2025, 7, 15, 14, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_same_day_before_window(self, scheduler: FiltrationScheduler) -> None:
        """Time before a same-day window should return False."""
        now = datetime(2025, 7, 15, 9, 0, 0)
        assert scheduler.is_in_active_window(now) is False

    def test_same_day_after_window(self, scheduler: FiltrationScheduler) -> None:
        """Time after a same-day window should return False."""
        now = datetime(2025, 7, 15, 19, 0, 0)
        assert scheduler.is_in_active_window(now) is False

    def test_same_day_at_start_boundary(self, scheduler: FiltrationScheduler) -> None:
        """Start time boundary is inclusive."""
        now = datetime(2025, 7, 15, 10, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_same_day_at_end_boundary(self, scheduler: FiltrationScheduler) -> None:
        """End time boundary is exclusive."""
        now = datetime(2025, 7, 15, 18, 0, 0)
        assert scheduler.is_in_active_window(now) is False

    def test_cross_midnight_evening_side(self, hass: MagicMock) -> None:
        """Time in the evening part of a cross-midnight window should return True."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._periods[0].start_time = time(22, 0)
        scheduler._periods[0].duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 15, 23, 30, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_cross_midnight_morning_side(self, hass: MagicMock) -> None:
        """Time in the morning part of a cross-midnight window should return True."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._periods[0].start_time = time(22, 0)
        scheduler._periods[0].duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 16, 4, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_cross_midnight_outside_window(self, hass: MagicMock) -> None:
        """Time outside a cross-midnight window should return False."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._periods[0].start_time = time(22, 0)
        scheduler._periods[0].duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 16, 12, 0, 0)
        assert scheduler.is_in_active_window(now) is False


class TestEndTime:
    """Tests for end_time computation (backward-compatible property)."""

    def test_same_day_end_time(self, scheduler: FiltrationScheduler) -> None:
        """10:00 + 8h = 18:00."""
        assert scheduler.end_time == time(18, 0)

    def test_cross_midnight_end_time(self, hass: MagicMock) -> None:
        """22:00 + 8h = 06:00 next day."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._periods[0].start_time = time(22, 0)
        scheduler._periods[0].duration_hours = 8.0
        assert scheduler.end_time == time(6, 0)

    def test_half_hour_duration(self, hass: MagicMock) -> None:
        """10:00 + 4.5h = 14:30."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._periods[0].start_time = time(10, 0)
        scheduler._periods[0].duration_hours = 4.5
        assert scheduler.end_time == time(14, 30)


class TestEnableDisable:
    """Tests for enable/disable scheduling behavior."""

    @pytest.mark.asyncio
    async def test_enable_sets_enabled_flag(self, scheduler: FiltrationScheduler) -> None:
        """Enabling the scheduler should set the enabled property."""
        with patch.object(scheduler, "_setup_triggers"):
            await scheduler.async_enable()
        assert scheduler.enabled is True

    @pytest.mark.asyncio
    async def test_disable_clears_enabled_flag(self, scheduler: FiltrationScheduler) -> None:
        """Disabling the scheduler should clear the enabled property."""
        with patch.object(scheduler, "_setup_triggers"):
            await scheduler.async_enable()
        await scheduler.async_disable()
        assert scheduler.enabled is False

    @pytest.mark.asyncio
    async def test_enable_starts_pump_when_in_window(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Pump should turn on immediately if enabled during the active window."""
        with (
            patch.object(scheduler, "_setup_triggers"),
            patch.object(scheduler, "is_in_active_window", return_value=True),
        ):
            await scheduler.async_enable()
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_enable_does_not_start_pump_outside_window(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Pump should NOT turn on if enabled outside the active window."""
        with (
            patch.object(scheduler, "_setup_triggers"),
            patch.object(scheduler, "is_in_active_window", return_value=False),
        ):
            await scheduler.async_enable()
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_disable_turns_off_pump(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Disabling should always turn the pump off."""
        with patch.object(scheduler, "_setup_triggers"):
            await scheduler.async_enable()
        hass.services.async_call.reset_mock()
        await scheduler.async_disable()
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_disable_cancels_triggers(self, scheduler: FiltrationScheduler) -> None:
        """Disabling should cancel any registered time triggers."""
        unsub1 = MagicMock()
        unsub2 = MagicMock()
        scheduler._unsub_triggers = [unsub1, unsub2]
        await scheduler.async_disable()
        unsub1.assert_called_once()
        unsub2.assert_called_once()
        assert len(scheduler._unsub_triggers) == 0


class TestUpdateSchedule:
    """Tests for async_update_schedule mid-cycle recalculation."""

    @pytest.mark.asyncio
    async def test_update_start_time(self, scheduler: FiltrationScheduler) -> None:
        """Updating start_time should store the new value."""
        await scheduler.async_update_schedule(start_time=time(14, 0))
        assert scheduler.start_time == time(14, 0)

    @pytest.mark.asyncio
    async def test_update_duration(self, scheduler: FiltrationScheduler) -> None:
        """Updating duration_hours should store the new value."""
        await scheduler.async_update_schedule(duration_hours=12.0)
        assert scheduler.duration_hours == 12.0

    @pytest.mark.asyncio
    async def test_update_when_disabled_does_not_touch_pump(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Updating schedule when disabled should not call any services."""
        await scheduler.async_update_schedule(start_time=time(14, 0))
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_when_enabled_recalculates(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Updating schedule when enabled should recalculate pump state."""
        scheduler._enabled = True
        with patch.object(scheduler, "is_in_active_window", return_value=True):
            await scheduler.async_update_schedule(start_time=time(14, 0))
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_update_when_enabled_outside_window_stops_pump(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Updating schedule when enabled but outside window should stop pump."""
        scheduler._enabled = True
        with patch.object(scheduler, "is_in_active_window", return_value=False):
            await scheduler.async_update_schedule(duration_hours=2.0)
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_update_invalid_period_index_is_ignored(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Updating a period index that doesn't exist should be ignored."""
        await scheduler.async_update_schedule(start_time=time(14, 0), period_index=5)
        # Original schedule unchanged
        assert scheduler.start_time == DEFAULT_FILTRATION_START_TIME
        hass.services.async_call.assert_not_called()


class TestEventListeners:
    """Tests for the event listener registry."""

    def test_on_event_registers_listener(self, scheduler: FiltrationScheduler) -> None:
        """on_event() should add a listener."""
        listener = MagicMock()
        scheduler.on_event(listener)
        assert listener in scheduler._listeners

    def test_unsubscribe_removes_listener(self, scheduler: FiltrationScheduler) -> None:
        """Calling the unsubscribe function should remove the listener."""
        listener = MagicMock()
        unsub = scheduler.on_event(listener)
        unsub()
        assert listener not in scheduler._listeners

    @pytest.mark.asyncio
    async def test_start_pump_notifies_listeners(self, scheduler: FiltrationScheduler) -> None:
        """Starting the pump should notify all registered listeners."""
        listener = MagicMock()
        scheduler.on_event(listener)
        await scheduler._async_start_pump()
        listener.assert_called_once()
        event_type, event_data = listener.call_args[0]
        assert event_type == EVENT_FILTRATION_STARTED
        assert "start_time" in event_data
        assert "duration_hours" in event_data
        assert "end_time" in event_data
        assert event_data["period_index"] == 0

    @pytest.mark.asyncio
    async def test_stop_pump_notifies_listeners(self, scheduler: FiltrationScheduler) -> None:
        """Stopping the pump should notify all registered listeners."""
        listener = MagicMock()
        scheduler.on_event(listener)
        await scheduler._async_stop_pump()
        listener.assert_called_once()
        event_type, event_data = listener.call_args[0]
        assert event_type == EVENT_FILTRATION_STOPPED
        assert "start_time" in event_data
        assert "duration_hours" in event_data
        assert "end_time" in event_data
        assert event_data["period_index"] == 0


class TestEventData:
    """Tests for event data payload."""

    def test_event_data_contains_schedule_details(self, scheduler: FiltrationScheduler) -> None:
        """Event data should contain start_time, duration_hours, end_time, and period_index."""
        data = scheduler._event_data()
        assert data["start_time"] == DEFAULT_FILTRATION_START_TIME.isoformat()
        assert data["duration_hours"] == DEFAULT_FILTRATION_DURATION_HOURS
        assert data["end_time"] == time(18, 0).isoformat()
        assert data["period_index"] == 0

    def test_event_data_reflects_updated_schedule(self, scheduler: FiltrationScheduler) -> None:
        """Event data should reflect schedule changes."""
        scheduler._periods[0].start_time = time(22, 0)
        scheduler._periods[0].duration_hours = 10.0
        data = scheduler._event_data()
        assert data["start_time"] == "22:00:00"
        assert data["duration_hours"] == 10.0
        assert data["end_time"] == "08:00:00"

    def test_event_data_for_period_index(self, scheduler: FiltrationScheduler) -> None:
        """Event data should reflect the specified period index."""
        scheduler._periods.append(FiltrationPeriod(start_time=time(16, 0), duration_hours=3.0))
        data = scheduler._event_data(period_index=1)
        assert data["start_time"] == "16:00:00"
        assert data["duration_hours"] == 3.0
        assert data["end_time"] == "19:00:00"
        assert data["period_index"] == 1


class TestAsyncCancel:
    """Tests for cleanup via async_cancel."""

    def test_cancel_clears_listeners(self, scheduler: FiltrationScheduler) -> None:
        """async_cancel should clear all listeners."""
        scheduler.on_event(MagicMock())
        scheduler.on_event(MagicMock())
        scheduler.async_cancel()
        assert len(scheduler._listeners) == 0

    def test_cancel_cancels_triggers(self, scheduler: FiltrationScheduler) -> None:
        """async_cancel should cancel any active triggers."""
        unsub1 = MagicMock()
        unsub2 = MagicMock()
        scheduler._unsub_triggers = [unsub1, unsub2]
        scheduler.async_cancel()
        unsub1.assert_called_once()
        unsub2.assert_called_once()
        assert len(scheduler._unsub_triggers) == 0


class TestDefaults:
    """Tests for default scheduler configuration."""

    def test_default_start_time(self, scheduler: FiltrationScheduler) -> None:
        """Default start time should be 10:00."""
        assert scheduler.start_time == time(10, 0)

    def test_default_duration(self, scheduler: FiltrationScheduler) -> None:
        """Default duration should be 8 hours."""
        assert scheduler.duration_hours == 8.0

    def test_default_not_enabled(self, scheduler: FiltrationScheduler) -> None:
        """Scheduler should be disabled by default."""
        assert scheduler.enabled is False

    def test_pump_entity_id(self, scheduler: FiltrationScheduler) -> None:
        """Pump entity ID should match the one provided."""
        assert scheduler.pump_entity_id == "switch.pool_pump"

    def test_default_single_period(self, scheduler: FiltrationScheduler) -> None:
        """Scheduler should have exactly one period by default."""
        assert len(scheduler.periods) == 1
        assert scheduler.split is False

    def test_periods_returns_copy(self, scheduler: FiltrationScheduler) -> None:
        """The periods property should return a copy, not the internal list."""
        periods = scheduler.periods
        periods.append(FiltrationPeriod())
        assert len(scheduler.periods) == 1


class TestTimeCallbacks:
    """Tests for period start/stop callbacks."""

    @pytest.mark.asyncio
    async def test_start_callback_when_enabled(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Start callback should start pump when scheduler is enabled."""
        scheduler._enabled = True
        cb = scheduler._make_start_callback(0)
        await cb(datetime.now())
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_start_callback_when_disabled(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Start callback should do nothing when scheduler is disabled."""
        scheduler._enabled = False
        cb = scheduler._make_start_callback(0)
        await cb(datetime.now())
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_callback_when_enabled(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Stop callback should stop pump when scheduler is enabled."""
        scheduler._enabled = True
        cb = scheduler._make_stop_callback(0)
        await cb(datetime.now())
        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {"entity_id": "switch.pool_pump"}
        )

    @pytest.mark.asyncio
    async def test_stop_callback_when_disabled(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Stop callback should do nothing when scheduler is disabled."""
        scheduler._enabled = False
        cb = scheduler._make_stop_callback(0)
        await cb(datetime.now())
        hass.services.async_call.assert_not_called()


# ---------- Multi-period (split) tests ----------


class TestSplitSchedule:
    """Tests for enabling/disabling split filtration (second period)."""

    @pytest.mark.asyncio
    async def test_enable_split_adds_second_period(self, scheduler: FiltrationScheduler) -> None:
        """Enabling split should add a second period with defaults."""
        await scheduler.async_set_split(enabled=True)
        assert len(scheduler.periods) == 2
        assert scheduler.split is True
        assert scheduler.periods[1].start_time == DEFAULT_FILTRATION_START_TIME_2
        assert scheduler.periods[1].duration_hours == DEFAULT_FILTRATION_DURATION_HOURS_2

    @pytest.mark.asyncio
    async def test_enable_split_with_custom_values(self, scheduler: FiltrationScheduler) -> None:
        """Enabling split with custom values should use those values."""
        await scheduler.async_set_split(enabled=True, start_time=time(18, 0), duration_hours=3.0)
        assert scheduler.periods[1].start_time == time(18, 0)
        assert scheduler.periods[1].duration_hours == 3.0

    @pytest.mark.asyncio
    async def test_disable_split_removes_second_period(
        self, scheduler: FiltrationScheduler
    ) -> None:
        """Disabling split should remove the second period."""
        await scheduler.async_set_split(enabled=True)
        assert len(scheduler.periods) == 2
        await scheduler.async_set_split(enabled=False)
        assert len(scheduler.periods) == 1
        assert scheduler.split is False

    @pytest.mark.asyncio
    async def test_enable_split_idempotent(self, scheduler: FiltrationScheduler) -> None:
        """Enabling split twice should not add a third period."""
        await scheduler.async_set_split(enabled=True)
        await scheduler.async_set_split(enabled=True, start_time=time(20, 0))
        assert len(scheduler.periods) == 2
        # Second call should not override the existing second period
        assert scheduler.periods[1].start_time == DEFAULT_FILTRATION_START_TIME_2

    @pytest.mark.asyncio
    async def test_disable_split_idempotent(self, scheduler: FiltrationScheduler) -> None:
        """Disabling split when already single should be a no-op."""
        await scheduler.async_set_split(enabled=False)
        assert len(scheduler.periods) == 1

    @pytest.mark.asyncio
    async def test_split_preserves_first_period(self, scheduler: FiltrationScheduler) -> None:
        """Enabling/disabling split should not change the first period."""
        await scheduler.async_update_schedule(start_time=time(8, 0), duration_hours=6.0)
        await scheduler.async_set_split(enabled=True)
        assert scheduler.start_time == time(8, 0)
        assert scheduler.duration_hours == 6.0
        await scheduler.async_set_split(enabled=False)
        assert scheduler.start_time == time(8, 0)
        assert scheduler.duration_hours == 6.0

    @pytest.mark.asyncio
    async def test_split_enabled_recalculates_triggers(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Enabling split when scheduler is active should recalculate triggers."""
        scheduler._enabled = True
        with patch.object(scheduler, "is_in_active_window", return_value=False):
            await scheduler.async_set_split(enabled=True)
        # Should have called services (stop pump since outside window)
        hass.services.async_call.assert_called()

    @pytest.mark.asyncio
    async def test_split_disabled_does_not_touch_pump(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Enabling split when scheduler is not active should not touch the pump."""
        await scheduler.async_set_split(enabled=True)
        hass.services.async_call.assert_not_called()


class TestMultiPeriodActiveWindow:
    """Tests for is_in_active_window with two periods."""

    @pytest.mark.asyncio
    async def test_in_first_period(self, scheduler: FiltrationScheduler) -> None:
        """Time in the first period should return True."""
        await scheduler.async_set_split(enabled=True)
        # Period 1: 10:00-18:00 (default)
        now = datetime(2025, 7, 15, 12, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    @pytest.mark.asyncio
    async def test_in_second_period(self, scheduler: FiltrationScheduler) -> None:
        """Time in the second period should return True."""
        await scheduler.async_set_split(enabled=True)
        # Period 2: 16:00-20:00 (default: 16:00 + 4h)
        now = datetime(2025, 7, 15, 19, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    @pytest.mark.asyncio
    async def test_between_periods(self, scheduler: FiltrationScheduler) -> None:
        """Time between non-overlapping periods should return False."""
        # Configure non-overlapping periods: 08:00-10:00 and 14:00-16:00
        scheduler._periods[0].start_time = time(8, 0)
        scheduler._periods[0].duration_hours = 2.0
        await scheduler.async_set_split(enabled=True, start_time=time(14, 0), duration_hours=2.0)
        now = datetime(2025, 7, 15, 12, 0, 0)
        assert scheduler.is_in_active_window(now) is False

    @pytest.mark.asyncio
    async def test_outside_all_periods(self, scheduler: FiltrationScheduler) -> None:
        """Time outside all periods should return False."""
        await scheduler.async_set_split(enabled=True)
        now = datetime(2025, 7, 15, 22, 0, 0)
        assert scheduler.is_in_active_window(now) is False


class TestMultiPeriodUpdateSchedule:
    """Tests for updating individual periods in split mode."""

    @pytest.mark.asyncio
    async def test_update_period_0(self, scheduler: FiltrationScheduler) -> None:
        """Updating period 0 should change the first period only."""
        await scheduler.async_set_split(enabled=True)
        await scheduler.async_update_schedule(start_time=time(9, 0), period_index=0)
        assert scheduler.periods[0].start_time == time(9, 0)
        assert scheduler.periods[1].start_time == DEFAULT_FILTRATION_START_TIME_2

    @pytest.mark.asyncio
    async def test_update_period_1(self, scheduler: FiltrationScheduler) -> None:
        """Updating period 1 should change the second period only."""
        await scheduler.async_set_split(enabled=True)
        await scheduler.async_update_schedule(
            start_time=time(18, 0), duration_hours=3.0, period_index=1
        )
        assert scheduler.periods[0].start_time == DEFAULT_FILTRATION_START_TIME
        assert scheduler.periods[1].start_time == time(18, 0)
        assert scheduler.periods[1].duration_hours == 3.0


class TestMultiPeriodEvents:
    """Tests for event notifications with period index."""

    @pytest.mark.asyncio
    async def test_start_pump_with_period_index(self, scheduler: FiltrationScheduler) -> None:
        """Start pump for period 1 should include period_index=1 in event data."""
        await scheduler.async_set_split(enabled=True)
        listener = MagicMock()
        scheduler.on_event(listener)
        await scheduler._async_start_pump(period_index=1)
        event_type, event_data = listener.call_args[0]
        assert event_type == EVENT_FILTRATION_STARTED
        assert event_data["period_index"] == 1
        assert event_data["start_time"] == DEFAULT_FILTRATION_START_TIME_2.isoformat()

    @pytest.mark.asyncio
    async def test_stop_pump_with_period_index(self, scheduler: FiltrationScheduler) -> None:
        """Stop pump for period 0 should include period_index=0 in event data."""
        listener = MagicMock()
        scheduler.on_event(listener)
        await scheduler._async_stop_pump(period_index=0)
        event_type, event_data = listener.call_args[0]
        assert event_type == EVENT_FILTRATION_STOPPED
        assert event_data["period_index"] == 0
