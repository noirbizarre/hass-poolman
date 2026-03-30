"""Number platform for Pool Manager filtration duration."""

from __future__ import annotations

import contextlib

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import PoolmanConfigEntry
from .const import DEFAULT_FILTRATION_DURATION_HOURS
from .coordinator import PoolmanCoordinator
from .domain.model import FiltrationDurationMode
from .entity import PoolmanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager number entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    if coordinator.scheduler is not None:
        async_add_entities([PoolmanFiltrationDuration(coordinator)])


class PoolmanFiltrationDuration(PoolmanEntity, NumberEntity, RestoreEntity):
    """Number entity for configuring the daily filtration duration in hours.

    The value is persisted across restarts via RestoreEntity. Changes
    immediately recalculate the scheduler triggers.

    In dynamic mode, the displayed value is automatically updated to
    match the computed recommended filtration duration on each
    coordinator refresh.
    """

    _attr_translation_key = "filtration_duration_setting"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_native_min_value = 1.0
    _attr_native_max_value = 24.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration duration entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration_duration_setting"
        self._attr_native_value: float = DEFAULT_FILTRATION_DURATION_HOURS

    async def async_added_to_hass(self) -> None:
        """Restore the last known duration value."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) is not None and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            with contextlib.suppress(ValueError, TypeError):
                self._attr_native_value = float(last_state.state)
        # Sync the scheduler with the restored (or default) value
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_update_schedule(
                duration_hours=self._attr_native_value,
            )

    async def async_set_native_value(self, value: float) -> None:
        """Set a new filtration duration.

        Args:
            value: The new duration in hours.
        """
        self._attr_native_value = value
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_update_schedule(duration_hours=value)
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        """Update displayed value when dynamic mode syncs the scheduler.

        In dynamic mode, the coordinator auto-syncs the scheduler duration
        from the computed recommendation. This method mirrors that value
        into the number entity so the UI reflects the active duration.
        """
        if (
            self.coordinator.filtration_duration_mode == FiltrationDurationMode.DYNAMIC
            and self.coordinator.data is not None
            and self.coordinator.data.filtration_hours is not None
        ):
            self._attr_native_value = self.coordinator.data.filtration_hours
        super()._handle_coordinator_update()
