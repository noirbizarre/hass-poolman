"""Event platform for Pool Manager filtration events."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PoolmanConfigEntry
from .const import EVENT_FILTRATION_STARTED, EVENT_FILTRATION_STOPPED
from .coordinator import PoolmanCoordinator
from .entity import PoolmanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager event entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    if coordinator.scheduler is not None:
        async_add_entities([PoolmanFiltrationEvent(coordinator)])


class PoolmanFiltrationEvent(PoolmanEntity, EventEntity):
    """Event entity that fires when filtration starts or stops.

    Listens to the FiltrationScheduler via its on_event() callback
    and triggers HA event entity updates with schedule details.
    """

    _attr_translation_key = "filtration"
    _attr_icon = "mdi:pump"
    _attr_event_types: ClassVar[list[str]] = [EVENT_FILTRATION_STARTED, EVENT_FILTRATION_STOPPED]

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration"
        self._unsub_scheduler: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register scheduler event listener when added to HA."""
        await super().async_added_to_hass()
        if self.coordinator.scheduler is not None:
            self._unsub_scheduler = self.coordinator.scheduler.on_event(self._on_scheduler_event)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister scheduler event listener when removed from HA."""
        if self._unsub_scheduler is not None:
            self._unsub_scheduler()
            self._unsub_scheduler = None
        await super().async_will_remove_from_hass()

    def _on_scheduler_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Handle a scheduler event by triggering the HA event entity.

        Args:
            event_type: The event type (filtration_started or filtration_stopped).
            event_data: Schedule details (start_time, duration_hours, end_time).
        """
        self._trigger_event(event_type, event_data)
        self.async_write_ha_state()
