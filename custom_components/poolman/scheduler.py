"""Filtration scheduler for daily pump on/off control.

Manages time-based triggers to automatically turn a pump switch on and off
according to one or more filtration periods, each defined by a start time
and duration.  Supports a manual *boost* that extends filtration beyond the
normal schedule.
"""

from __future__ import annotations

import logging

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time, async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_FILTRATION_DURATION_HOURS,
    DEFAULT_FILTRATION_DURATION_HOURS_2,
    DEFAULT_FILTRATION_START_TIME,
    DEFAULT_FILTRATION_START_TIME_2,
    EVENT_BOOST_CANCELLED,
    EVENT_BOOST_CONSUMED,
    EVENT_BOOST_STARTED,
    EVENT_FILTRATION_STARTED,
    EVENT_FILTRATION_STOPPED,
)

_LOGGER = logging.getLogger(__name__)

type EventCallback = Callable[[str, dict[str, object]], None]


@dataclass
class FiltrationPeriod:
    """A single filtration time window with a start time and duration.

    Attributes:
        start_time: The time at which filtration starts.
        duration_hours: How long filtration runs, in hours.
    """

    start_time: time = field(default_factory=lambda: DEFAULT_FILTRATION_START_TIME)
    duration_hours: float = DEFAULT_FILTRATION_DURATION_HOURS

    @property
    def end_time(self) -> time:
        """Compute the end time from start time and duration.

        Handles cross-midnight wrap-around naturally via timedelta.

        Returns:
            The time at which filtration should stop.
        """
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = start_dt + timedelta(hours=self.duration_hours)
        return end_dt.time()

    def contains(self, t: time) -> bool:
        """Check if a given time falls within this period.

        The start boundary is inclusive, the end boundary is exclusive.
        Handles both same-day (e.g., 10:00-18:00) and cross-midnight
        (e.g., 22:00-06:00) windows.

        Args:
            t: The time to check.

        Returns:
            True if the time is within this period.
        """
        end = self.end_time
        if end > self.start_time:
            # Same-day window (e.g., 10:00-18:00)
            return self.start_time <= t < end
        # Cross-midnight window (e.g., 22:00-06:00)
        return t >= self.start_time or t < end


class FiltrationScheduler:
    """Manages daily filtration pump on/off scheduling.

    Registers time-based triggers with Home Assistant to turn a pump switch
    on at configured start times and off after configured durations.
    Supports multiple periods, cross-midnight schedules, restart recovery,
    and manual boost extensions.
    """

    def __init__(self, hass: HomeAssistant, pump_entity_id: str) -> None:
        """Initialize the filtration scheduler.

        Args:
            hass: Home Assistant instance.
            pump_entity_id: Entity ID of the pump switch to control.
        """
        self._hass = hass
        self._pump_entity_id = pump_entity_id
        self._enabled = False
        self._periods: list[FiltrationPeriod] = [FiltrationPeriod()]
        self._unsub_triggers: list[CALLBACK_TYPE] = []
        self._listeners: list[EventCallback] = []

        # Boost state
        self._boost_hours: float = 0.0
        self._boost_end: datetime | None = None
        self._unsub_boost_stop: CALLBACK_TYPE | None = None

    # ── Properties ──────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        """Return whether the scheduler is currently active."""
        return self._enabled

    @property
    def periods(self) -> list[FiltrationPeriod]:
        """Return a copy of the configured filtration periods."""
        return list(self._periods)

    @property
    def split(self) -> bool:
        """Return whether the scheduler operates with multiple periods."""
        return len(self._periods) > 1

    @property
    def start_time(self) -> time:
        """Return the first period's start time.

        Backward-compatible shortcut for single-period access.
        """
        return self._periods[0].start_time

    @property
    def duration_hours(self) -> float:
        """Return the first period's duration in hours.

        Backward-compatible shortcut for single-period access.
        """
        return self._periods[0].duration_hours

    @property
    def end_time(self) -> time:
        """Return the first period's end time.

        Backward-compatible shortcut for single-period access.
        """
        return self._periods[0].end_time

    @property
    def pump_entity_id(self) -> str:
        """Return the pump entity ID being controlled."""
        return self._pump_entity_id

    @property
    def boost_active(self) -> bool:
        """Return whether a filtration boost is currently active."""
        return self._boost_hours > 0

    @property
    def boost_end(self) -> datetime | None:
        """Return the datetime when the current boost expires.

        None if no boost is active or the boost has not yet started
        being consumed (pump is still within a scheduled period).
        """
        return self._boost_end

    @property
    def boost_remaining(self) -> float:
        """Return remaining boost hours.

        If the boost end time has been set (consumption started),
        the remaining time is computed from *now*. Otherwise the
        full requested boost hours are returned.

        Returns:
            Remaining boost hours, 0.0 if no boost is active.
        """
        if self._boost_hours <= 0:
            return 0.0
        if self._boost_end is None:
            # Boost requested but not yet consuming (pump still in-window)
            return self._boost_hours
        remaining = (self._boost_end - dt_util.now()).total_seconds() / 3600
        return max(0.0, remaining)

    # ── Active window ───────────────────────────────────────────

    def is_in_active_window(self, now: datetime | None = None) -> bool:
        """Check if a given time falls within any active filtration period.

        Handles both same-day (e.g., 10:00-18:00) and cross-midnight
        (e.g., 22:00-06:00) windows for each period.

        Args:
            now: The time to check. Defaults to the current HA-aware time.

        Returns:
            True if the time is within any active period.
        """
        if now is None:
            now = dt_util.now()
        now_time = now.time()
        return any(period.contains(now_time) for period in self._periods)

    # ── Event listeners ─────────────────────────────────────────

    def on_event(self, callback_fn: EventCallback) -> Callable[[], None]:
        """Register a listener for scheduler events.

        Args:
            callback_fn: Called with (event_type, event_data) when events occur.

        Returns:
            An unsubscribe function to remove the listener.
        """
        self._listeners.append(callback_fn)

        def _unsubscribe() -> None:
            self._listeners.remove(callback_fn)

        return _unsubscribe

    def _event_data(self, period_index: int = 0) -> dict[str, object]:
        """Build the event data payload with schedule details for a period.

        Args:
            period_index: Index of the period that triggered the event.

        Returns:
            Dictionary with start_time, duration_hours, end_time,
            and period_index.
        """
        period = self._periods[period_index]
        return {
            "start_time": period.start_time.isoformat(),
            "duration_hours": period.duration_hours,
            "end_time": period.end_time.isoformat(),
            "period_index": period_index,
        }

    def _boost_event_data(self) -> dict[str, object]:
        """Build the event data payload for a boost event.

        Returns:
            Dictionary with boost_hours and boost_end (if set).
        """
        data: dict[str, object] = {"boost_hours": self._boost_hours}
        if self._boost_end is not None:
            data["boost_end"] = self._boost_end.isoformat()
        return data

    @callback
    def _notify(self, event_type: str, period_index: int = 0) -> None:
        """Notify all registered listeners of a scheduler event.

        Args:
            event_type: The event type (e.g., filtration_started).
            period_index: Index of the period that triggered the event.
        """
        data = self._event_data(period_index)
        for listener in self._listeners:
            listener(event_type, data)

    @callback
    def _notify_boost(self, event_type: str) -> None:
        """Notify all registered listeners of a boost event.

        Args:
            event_type: The boost event type (e.g., boost_started).
        """
        data = self._boost_event_data()
        for listener in self._listeners:
            listener(event_type, data)

    # ── Enable / Disable ────────────────────────────────────────

    async def async_enable(self) -> None:
        """Enable the filtration schedule.

        Sets up daily time triggers for pump start and stop for all periods.
        If the current time falls within any active window, the pump is
        turned on immediately.
        """
        self._enabled = True
        self._setup_triggers()

        if self.is_in_active_window():
            await self._async_start_pump()
        _LOGGER.debug(
            "Filtration control enabled: %d period(s) (pump: %s)",
            len(self._periods),
            self._pump_entity_id,
        )

    async def async_disable(self) -> None:
        """Disable the filtration schedule and turn off the pump.

        Cancels all time triggers, any active boost, and immediately
        turns the pump off.
        """
        self._enabled = False
        self._cancel_triggers()
        self._clear_boost()
        await self._async_stop_pump()
        _LOGGER.debug("Filtration control disabled (pump: %s)", self._pump_entity_id)

    # ── Schedule management ─────────────────────────────────────

    async def async_update_schedule(
        self,
        start_time: time | None = None,
        duration_hours: float | None = None,
        period_index: int = 0,
    ) -> None:
        """Update schedule parameters for a specific period and recalculate triggers.

        If the scheduler is enabled, triggers are re-registered and the
        pump state is immediately adjusted based on the new active windows.

        Args:
            start_time: New start time, or None to keep current.
            duration_hours: New duration in hours, or None to keep current.
            period_index: Index of the period to update (default 0).
        """
        if period_index >= len(self._periods):
            _LOGGER.warning(
                "Cannot update period %d: only %d period(s) configured",
                period_index,
                len(self._periods),
            )
            return

        period = self._periods[period_index]
        if start_time is not None:
            period.start_time = start_time
        if duration_hours is not None:
            period.duration_hours = duration_hours

        if not self._enabled:
            return

        self._cancel_triggers()
        self._setup_triggers()

        # Immediately adjust pump state to the new windows
        if self.is_in_active_window() or self.boost_active:
            await self._async_start_pump()
        else:
            await self._async_stop_pump()

        _LOGGER.debug(
            "Filtration schedule updated: period %d -> %s for %.1fh",
            period_index,
            period.start_time,
            period.duration_hours,
        )

    async def async_set_split(
        self,
        enabled: bool,
        start_time: time | None = None,
        duration_hours: float | None = None,
    ) -> None:
        """Enable or disable split filtration (second period).

        When enabling, a second period is added with the given or default
        start time and duration. When disabling, the second period is
        removed and only the first period remains active.

        Args:
            enabled: True to enable split (add period 2), False to disable.
            start_time: Start time for period 2 (default: 16:00).
            duration_hours: Duration for period 2 (default: 4.0h).
        """
        if enabled:
            if len(self._periods) < 2:
                self._periods.append(
                    FiltrationPeriod(
                        start_time=start_time or DEFAULT_FILTRATION_START_TIME_2,
                        duration_hours=duration_hours or DEFAULT_FILTRATION_DURATION_HOURS_2,
                    )
                )
        elif len(self._periods) > 1:
            self._periods = self._periods[:1]

        if not self._enabled:
            return

        self._cancel_triggers()
        self._setup_triggers()

        # Immediately adjust pump state to the new windows
        if self.is_in_active_window() or self.boost_active:
            await self._async_start_pump()
        else:
            await self._async_stop_pump()

        _LOGGER.debug(
            "Filtration split %s: %d period(s) active",
            "enabled" if enabled else "disabled",
            len(self._periods),
        )

    # ── Boost ───────────────────────────────────────────────────

    async def async_boost(self, hours: float) -> None:
        """Activate a filtration boost.

        Adds extra continuous filtration time on top of the normal
        schedule.  If the pump is currently running (inside a scheduled
        window), the boost extends past the next natural stop.  If the
        pump is idle (outside any window), the pump starts immediately
        and a one-shot stop is scheduled after *hours*.

        A new boost replaces any previously active boost.

        Args:
            hours: Number of extra filtration hours (must be > 0).
        """
        if hours <= 0:
            await self.async_cancel_boost()
            return

        # Clear any previous boost timer
        self._cancel_boost_timer()

        self._boost_hours = hours

        if self.is_in_active_window():
            # Pump is already running; boost extends past the next stop.
            # _boost_end will be set when the first stop fires.
            self._boost_end = None
            _LOGGER.info(
                "Filtration boost activated: +%.1fh (extends current period)",
                hours,
            )
        else:
            # Pump is idle; start immediately and schedule one-shot stop.
            now = dt_util.now()
            self._boost_end = now + timedelta(hours=hours)
            await self._async_start_pump()
            self._schedule_boost_stop()
            _LOGGER.info(
                "Filtration boost activated: +%.1fh (pump started, ends %s)",
                hours,
                self._boost_end.isoformat(),
            )

        self._notify_boost(EVENT_BOOST_STARTED)

    async def async_cancel_boost(self) -> None:
        """Cancel any active filtration boost.

        If the pump is running outside the normal schedule window
        (i.e. only because of the boost), it is turned off.
        """
        if not self.boost_active:
            return

        _LOGGER.info("Filtration boost cancelled")
        self._clear_boost()
        self._notify_boost(EVENT_BOOST_CANCELLED)

        # Stop the pump if we're outside the normal schedule
        if not self.is_in_active_window():
            await self._async_stop_pump()

    async def async_restore_boost(self, boost_end: datetime) -> None:
        """Restore a boost from a persisted end time (e.g. after HA restart).

        If the boost end is still in the future, the boost is reactivated
        with the remaining time.  Otherwise the boost is silently discarded.

        Args:
            boost_end: The persisted boost expiry datetime.
        """
        now = dt_util.now()
        remaining_seconds = (boost_end - now).total_seconds()
        if remaining_seconds <= 0:
            return

        remaining_hours = remaining_seconds / 3600
        self._boost_hours = remaining_hours
        self._boost_end = boost_end

        # If pump is outside a scheduled window, start it and schedule stop
        if not self.is_in_active_window():
            await self._async_start_pump()

        self._schedule_boost_stop()
        _LOGGER.info(
            "Filtration boost restored: %.1fh remaining (ends %s)",
            remaining_hours,
            boost_end.isoformat(),
        )

    def _schedule_boost_stop(self) -> None:
        """Register a one-shot timer to stop the pump when the boost expires."""
        if self._boost_end is None:
            return

        self._cancel_boost_timer()

        @callback
        def _on_boost_end(_now: datetime) -> None:
            """Handle boost expiry."""
            self._hass.async_create_task(self._async_on_boost_consumed())

        self._unsub_boost_stop = async_track_point_in_time(
            self._hass,
            _on_boost_end,
            self._boost_end,
        )

    async def _async_on_boost_consumed(self) -> None:
        """Handle natural boost expiry.

        Stops the pump (if outside the normal schedule), clears boost
        state, and notifies listeners.
        """
        _LOGGER.info("Filtration boost consumed")
        self._boost_hours = 0.0
        self._boost_end = None
        self._unsub_boost_stop = None

        self._notify_boost(EVENT_BOOST_CONSUMED)

        # Only stop if we're outside a normal window
        if not self.is_in_active_window():
            await self._async_stop_pump()

    def _clear_boost(self) -> None:
        """Reset boost state and cancel any pending boost timer."""
        self._boost_hours = 0.0
        self._boost_end = None
        self._cancel_boost_timer()

    def _cancel_boost_timer(self) -> None:
        """Cancel the one-shot boost stop timer if registered."""
        if self._unsub_boost_stop is not None:
            self._unsub_boost_stop()
            self._unsub_boost_stop = None

    # ── Time triggers ───────────────────────────────────────────

    def _setup_triggers(self) -> None:
        """Register time-based triggers for pump start and stop for all periods."""
        for idx, period in enumerate(self._periods):
            end = period.end_time

            unsub_start = async_track_time_change(
                self._hass,
                self._make_start_callback(idx),
                hour=period.start_time.hour,
                minute=period.start_time.minute,
                second=0,
            )
            unsub_stop = async_track_time_change(
                self._hass,
                self._make_stop_callback(idx),
                hour=end.hour,
                minute=end.minute,
                second=0,
            )
            self._unsub_triggers.extend([unsub_start, unsub_stop])

    def _cancel_triggers(self) -> None:
        """Cancel all registered time triggers."""
        for unsub in self._unsub_triggers:
            unsub()
        self._unsub_triggers.clear()

    def _make_start_callback(
        self, period_index: int
    ) -> Callable[[datetime], Coroutine[Any, Any, None]]:
        """Create a start-time callback for a specific period.

        Args:
            period_index: Index of the period this callback belongs to.

        Returns:
            An async callback for the time trigger.
        """

        async def _on_start_time(_now: datetime) -> None:
            if self._enabled:
                await self._async_start_pump(period_index)

        return _on_start_time

    def _make_stop_callback(
        self, period_index: int
    ) -> Callable[[datetime], Coroutine[Any, Any, None]]:
        """Create a stop-time callback for a specific period.

        When a boost is active, the stop is suppressed. On the first
        suppressed stop, the boost end time is calculated and a
        one-shot timer is scheduled.

        Args:
            period_index: Index of the period this callback belongs to.

        Returns:
            An async callback for the time trigger.
        """

        async def _on_stop_time(now: datetime) -> None:
            if not self._enabled:
                return

            if self.boost_active:
                # Suppress the normal stop; the boost keeps the pump running
                if self._boost_end is None:
                    # First suppressed stop: calculate boost end from now
                    self._boost_end = now + timedelta(hours=self._boost_hours)
                    self._schedule_boost_stop()
                    _LOGGER.debug(
                        "Period %d stop suppressed by boost (ends %s)",
                        period_index,
                        self._boost_end.isoformat(),
                    )
                else:
                    _LOGGER.debug(
                        "Period %d stop suppressed by boost (already consuming)",
                        period_index,
                    )
                return

            await self._async_stop_pump(period_index)

        return _on_stop_time

    # ── Pump control ────────────────────────────────────────────

    async def _async_start_pump(self, period_index: int = 0) -> None:
        """Turn on the pump switch and notify listeners.

        Args:
            period_index: Index of the period triggering the start.
        """
        _LOGGER.info("Starting filtration pump: %s", self._pump_entity_id)
        await self._hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": self._pump_entity_id},
        )
        self._notify(EVENT_FILTRATION_STARTED, period_index)

    async def _async_stop_pump(self, period_index: int = 0) -> None:
        """Turn off the pump switch and notify listeners.

        Args:
            period_index: Index of the period triggering the stop.
        """
        _LOGGER.info("Stopping filtration pump: %s", self._pump_entity_id)
        await self._hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self._pump_entity_id},
        )
        self._notify(EVENT_FILTRATION_STOPPED, period_index)

    # ── Cleanup ─────────────────────────────────────────────────

    @callback
    def async_cancel(self) -> None:
        """Cancel all triggers and clear listeners.

        Called during integration unload to clean up resources.
        """
        self._cancel_triggers()
        self._clear_boost()
        self._listeners.clear()
