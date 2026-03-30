"""Select platform for Pool Manager."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import PoolmanConfigEntry
from .const import DEFAULT_FILTRATION_DURATION_MODE
from .coordinator import PoolmanCoordinator
from .domain.model import FiltrationDurationMode, PoolMode
from .entity import PoolmanEntity

SELECT_DESCRIPTION = SelectEntityDescription(
    key="mode",
    translation_key="mode",
    icon="mdi:pool",
    options=[mode.value for mode in PoolMode],
)

FILTRATION_DURATION_MODE_DESCRIPTION = SelectEntityDescription(
    key="filtration_duration_mode",
    translation_key="filtration_duration_mode",
    icon="mdi:pump",
    options=[mode.value for mode in FiltrationDurationMode],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager select entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    entities: list[SelectEntity] = [PoolmanModeSelect(coordinator)]
    if coordinator.scheduler is not None:
        entities.append(PoolmanFiltrationDurationModeSelect(coordinator))
    async_add_entities(entities)


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


class PoolmanFiltrationDurationModeSelect(PoolmanEntity, SelectEntity, RestoreEntity):
    """Select entity for filtration duration control mode.

    Allows choosing between manual and dynamic filtration duration.
    In dynamic mode, the computed recommended duration is automatically
    applied to the scheduler. In manual mode, the user sets the duration
    via the filtration duration number entity.

    The selected mode is persisted across restarts via RestoreEntity.
    """

    entity_description: SelectEntityDescription

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration duration mode select."""
        super().__init__(coordinator)
        self.entity_description = FILTRATION_DURATION_MODE_DESCRIPTION
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration_duration_mode"

    @property
    def current_option(self) -> str:
        """Return the current filtration duration mode."""
        return self.coordinator.filtration_duration_mode.value

    async def async_added_to_hass(self) -> None:
        """Restore the last known filtration duration mode."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) is not None and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                restored_mode = FiltrationDurationMode(last_state.state)
            except ValueError:
                restored_mode = FiltrationDurationMode(DEFAULT_FILTRATION_DURATION_MODE)
            self.coordinator.filtration_duration_mode = restored_mode

    async def async_select_option(self, option: str) -> None:
        """Change the filtration duration mode."""
        self.coordinator.filtration_duration_mode = FiltrationDurationMode(option)
        await self.coordinator.async_request_refresh()
