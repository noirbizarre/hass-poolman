"""Time platform for Pool Manager filtration start time."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import PoolmanConfigEntry
from .const import DEFAULT_FILTRATION_START_TIME
from .coordinator import PoolmanCoordinator
from .entity import PoolmanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager time entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    if coordinator.scheduler is not None:
        async_add_entities([PoolmanFiltrationStartTime(coordinator)])


class PoolmanFiltrationStartTime(PoolmanEntity, TimeEntity, RestoreEntity):
    """Time entity for configuring the daily filtration start time.

    The value is persisted across restarts via RestoreEntity. Changes
    immediately recalculate the scheduler triggers.
    """

    _attr_translation_key = "filtration_start_time"
    _attr_icon = "mdi:clock-start"

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration start time entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration_start_time"
        self._attr_native_value: time = DEFAULT_FILTRATION_START_TIME

    async def async_added_to_hass(self) -> None:
        """Restore the last known start time value."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) is not None and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            restored = dt_util.parse_time(last_state.state)
            if restored is not None:
                self._attr_native_value = restored
        # Sync the scheduler with the restored (or default) value
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_update_schedule(
                start_time=self._attr_native_value,
            )

    async def async_set_value(self, value: time) -> None:
        """Set a new filtration start time.

        Args:
            value: The new start time.
        """
        self._attr_native_value = value
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_update_schedule(start_time=value)
        self.async_write_ha_state()
