"""Tests for the FiltrationScheduler."""

from __future__ import annotations

from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.poolman.const import (
    DEFAULT_FILTRATION_DURATION_HOURS,
    DEFAULT_FILTRATION_START_TIME,
    EVENT_FILTRATION_STARTED,
    EVENT_FILTRATION_STOPPED,
)
from custom_components.poolman.scheduler import FiltrationScheduler


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

    def test_cross_midnight_evening_side(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Time in the evening part of a cross-midnight window should return True."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._start_time = time(22, 0)
        scheduler._duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 15, 23, 30, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_cross_midnight_morning_side(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Time in the morning part of a cross-midnight window should return True."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._start_time = time(22, 0)
        scheduler._duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 16, 4, 0, 0)
        assert scheduler.is_in_active_window(now) is True

    def test_cross_midnight_outside_window(
        self, scheduler: FiltrationScheduler, hass: MagicMock
    ) -> None:
        """Time outside a cross-midnight window should return False."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._start_time = time(22, 0)
        scheduler._duration_hours = 8.0  # 22:00-06:00
        now = datetime(2025, 7, 16, 12, 0, 0)
        assert scheduler.is_in_active_window(now) is False


class TestEndTime:
    """Tests for end_time computation."""

    def test_same_day_end_time(self, scheduler: FiltrationScheduler) -> None:
        """10:00 + 8h = 18:00."""
        assert scheduler.end_time == time(18, 0)

    def test_cross_midnight_end_time(self, hass: MagicMock) -> None:
        """22:00 + 8h = 06:00 next day."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._start_time = time(22, 0)
        scheduler._duration_hours = 8.0
        assert scheduler.end_time == time(6, 0)

    def test_half_hour_duration(self, hass: MagicMock) -> None:
        """10:00 + 4.5h = 14:30."""
        scheduler = FiltrationScheduler(hass, "switch.pool_pump")
        scheduler._start_time = time(10, 0)
        scheduler._duration_hours = 4.5
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
        unsub_start = MagicMock()
        unsub_stop = MagicMock()
        scheduler._unsub_start = unsub_start
        scheduler._unsub_stop = unsub_stop
        await scheduler.async_disable()
        unsub_start.assert_called_once()
        unsub_stop.assert_called_once()
        assert scheduler._unsub_start is None
        assert scheduler._unsub_stop is None


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


class TestEventData:
    """Tests for event data payload."""

    def test_event_data_contains_schedule_details(self, scheduler: FiltrationScheduler) -> None:
        """Event data should contain start_time, duration_hours, and end_time."""
        data = scheduler._event_data()
        assert data["start_time"] == DEFAULT_FILTRATION_START_TIME.isoformat()
        assert data["duration_hours"] == DEFAULT_FILTRATION_DURATION_HOURS
        assert data["end_time"] == time(18, 0).isoformat()

    def test_event_data_reflects_updated_schedule(self, scheduler: FiltrationScheduler) -> None:
        """Event data should reflect schedule changes."""
        scheduler._start_time = time(22, 0)
        scheduler._duration_hours = 10.0
        data = scheduler._event_data()
        assert data["start_time"] == "22:00:00"
        assert data["duration_hours"] == 10.0
        assert data["end_time"] == "08:00:00"


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
        unsub_start = MagicMock()
        unsub_stop = MagicMock()
        scheduler._unsub_start = unsub_start
        scheduler._unsub_stop = unsub_stop
        scheduler.async_cancel()
        unsub_start.assert_called_once()
        unsub_stop.assert_called_once()


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
