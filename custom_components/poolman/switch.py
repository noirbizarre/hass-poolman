"""Switch platform for Pool Manager filtration control."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .entity import PoolmanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager switch entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    if coordinator.scheduler is not None:
        async_add_entities([PoolmanFiltrationControlSwitch(coordinator)])


class PoolmanFiltrationControlSwitch(PoolmanEntity, SwitchEntity, RestoreEntity):
    """Switch entity to enable or disable automatic filtration scheduling.

    When turned on, the scheduler will turn the configured pump switch on
    at the scheduled start time and off after the configured duration,
    every day. When turned off, the pump is turned off immediately and
    all scheduled triggers are cancelled.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "filtration_control"
    _attr_icon = "mdi:pump"

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration control switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration_control"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Restore last known state and re-enable scheduling if needed."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON
            if self._attr_is_on and self.coordinator.scheduler is not None:
                await self.coordinator.scheduler.async_enable()

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable automatic filtration scheduling."""
        self._attr_is_on = True
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_enable()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable automatic filtration scheduling and turn off the pump."""
        self._attr_is_on = False
        if self.coordinator.scheduler is not None:
            await self.coordinator.scheduler.async_disable()
        self.async_write_ha_state()
