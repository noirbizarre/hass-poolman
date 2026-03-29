"""Filtration scheduler for daily pump on/off control.

Manages time-based triggers to automatically turn a pump switch on and off
according to a user-defined start time and duration.
"""

from __future__ import annotations

import logging

from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_FILTRATION_DURATION_HOURS,
    DEFAULT_FILTRATION_START_TIME,
    EVENT_FILTRATION_STARTED,
    EVENT_FILTRATION_STOPPED,
)

_LOGGER = logging.getLogger(__name__)

type EventCallback = Callable[[str, dict[str, object]], None]


class FiltrationScheduler:
    """Manages daily filtration pump on/off scheduling.

    Registers time-based triggers with Home Assistant to turn a pump switch
    on at a configured start time and off after a configured duration.
    Supports cross-midnight schedules and restart recovery.
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
        self._start_time: time = DEFAULT_FILTRATION_START_TIME
        self._duration_hours: float = DEFAULT_FILTRATION_DURATION_HOURS
        self._unsub_start: CALLBACK_TYPE | None = None
        self._unsub_stop: CALLBACK_TYPE | None = None
        self._listeners: list[EventCallback] = []

    @property
    def enabled(self) -> bool:
        """Return whether the scheduler is currently active."""
        return self._enabled

    @property
    def start_time(self) -> time:
        """Return the configured daily start time."""
        return self._start_time

    @property
    def duration_hours(self) -> float:
        """Return the configured filtration duration in hours."""
        return self._duration_hours

    @property
    def end_time(self) -> time:
        """Compute the end time from start time and duration.

        Handles cross-midnight wrap-around naturally via timedelta.

        Returns:
            The time at which filtration should stop.
        """
        start_dt = datetime.combine(date.today(), self._start_time)
        end_dt = start_dt + timedelta(hours=self._duration_hours)
        return end_dt.time()

    @property
    def pump_entity_id(self) -> str:
        """Return the pump entity ID being controlled."""
        return self._pump_entity_id

    def is_in_active_window(self, now: datetime | None = None) -> bool:
        """Check if a given time falls within the active filtration window.

        Handles both same-day (e.g., 10:00-18:00) and cross-midnight
        (e.g., 22:00-06:00) windows. The start boundary is inclusive,
        the end boundary is exclusive.

        Args:
            now: The time to check. Defaults to the current HA-aware time.

        Returns:
            True if the time is within the active window.
        """
        if now is None:
            now = dt_util.now()
        now_time = now.time()
        start = self._start_time
        end = self.end_time

        if end > start:
            # Same-day window (e.g., 10:00-18:00)
            return start <= now_time < end
        # Cross-midnight window (e.g., 22:00-06:00)
        return now_time >= start or now_time < end

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

    def _event_data(self) -> dict[str, object]:
        """Build the event data payload with current schedule details.

        Returns:
            Dictionary with start_time, duration_hours, and end_time.
        """
        return {
            "start_time": self._start_time.isoformat(),
            "duration_hours": self._duration_hours,
            "end_time": self.end_time.isoformat(),
        }

    @callback
    def _notify(self, event_type: str) -> None:
        """Notify all registered listeners of a scheduler event.

        Args:
            event_type: The event type (e.g., filtration_started).
        """
        data = self._event_data()
        for listener in self._listeners:
            listener(event_type, data)

    async def async_enable(self) -> None:
        """Enable the filtration schedule.

        Sets up daily time triggers for pump start and stop. If the current
        time falls within the active window, the pump is turned on immediately.
        """
        self._enabled = True
        self._setup_triggers()

        if self.is_in_active_window():
            await self._async_start_pump()
        _LOGGER.debug(
            "Filtration control enabled: %s for %.1fh (pump: %s)",
            self._start_time,
            self._duration_hours,
            self._pump_entity_id,
        )

    async def async_disable(self) -> None:
        """Disable the filtration schedule and turn off the pump.

        Cancels all time triggers and immediately turns the pump off.
        """
        self._enabled = False
        self._cancel_triggers()
        await self._async_stop_pump()
        _LOGGER.debug("Filtration control disabled (pump: %s)", self._pump_entity_id)

    async def async_update_schedule(
        self,
        start_time: time | None = None,
        duration_hours: float | None = None,
    ) -> None:
        """Update schedule parameters and recalculate triggers.

        If the scheduler is enabled, triggers are re-registered and the
        pump state is immediately adjusted based on the new active window.

        Args:
            start_time: New start time, or None to keep current.
            duration_hours: New duration in hours, or None to keep current.
        """
        if start_time is not None:
            self._start_time = start_time
        if duration_hours is not None:
            self._duration_hours = duration_hours

        if not self._enabled:
            return

        self._cancel_triggers()
        self._setup_triggers()

        # Immediately adjust pump state to the new window
        if self.is_in_active_window():
            await self._async_start_pump()
        else:
            await self._async_stop_pump()

        _LOGGER.debug(
            "Filtration schedule updated: %s for %.1fh",
            self._start_time,
            self._duration_hours,
        )

    def _setup_triggers(self) -> None:
        """Register time-based triggers for pump start and stop."""
        end = self.end_time

        self._unsub_start = async_track_time_change(
            self._hass,
            self._on_start_time,
            hour=self._start_time.hour,
            minute=self._start_time.minute,
            second=0,
        )
        self._unsub_stop = async_track_time_change(
            self._hass,
            self._on_stop_time,
            hour=end.hour,
            minute=end.minute,
            second=0,
        )

    def _cancel_triggers(self) -> None:
        """Cancel all registered time triggers."""
        if self._unsub_start is not None:
            self._unsub_start()
            self._unsub_start = None
        if self._unsub_stop is not None:
            self._unsub_stop()
            self._unsub_stop = None

    async def _on_start_time(self, _now: datetime) -> None:
        """Handle the daily start time trigger."""
        if self._enabled:
            await self._async_start_pump()

    async def _on_stop_time(self, _now: datetime) -> None:
        """Handle the daily stop time trigger."""
        if self._enabled:
            await self._async_stop_pump()

    async def _async_start_pump(self) -> None:
        """Turn on the pump switch and notify listeners."""
        _LOGGER.info("Starting filtration pump: %s", self._pump_entity_id)
        await self._hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": self._pump_entity_id},
        )
        self._notify(EVENT_FILTRATION_STARTED)

    async def _async_stop_pump(self) -> None:
        """Turn off the pump switch and notify listeners."""
        _LOGGER.info("Stopping filtration pump: %s", self._pump_entity_id)
        await self._hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self._pump_entity_id},
        )
        self._notify(EVENT_FILTRATION_STOPPED)

    @callback
    def async_cancel(self) -> None:
        """Cancel all triggers and clear listeners.

        Called during integration unload to clean up resources.
        """
        self._cancel_triggers()
        self._listeners.clear()
