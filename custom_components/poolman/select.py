"""Select platform for Pool Manager."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.model import PoolMode
from .entity import PoolmanEntity

SELECT_DESCRIPTION = SelectEntityDescription(
    key="mode",
    translation_key="mode",
    icon="mdi:pool",
    options=[mode.value for mode in PoolMode],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager select entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    async_add_entities([PoolmanModeSelect(coordinator)])


class PoolmanModeSelect(PoolmanEntity, SelectEntity):
    """Select entity for pool operating mode."""

    entity_description: SelectEntityDescription

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the mode select."""
        super().__init__(coordinator)
        self.entity_description = SELECT_DESCRIPTION
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_mode"

    @property
    def current_option(self) -> str:
        """Return the current pool mode."""
        return self.coordinator.mode.value

    async def async_select_option(self, option: str) -> None:
        """Change the pool mode."""
        self.coordinator.mode = PoolMode(option)
        await self.coordinator.async_request_refresh()
