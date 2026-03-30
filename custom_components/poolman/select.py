"""Select platform for Pool Manager."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import PoolmanConfigEntry
from .const import BOOST_PRESET_NONE, BOOST_PRESETS, DEFAULT_FILTRATION_DURATION_MODE
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

FILTRATION_BOOST_DESCRIPTION = SelectEntityDescription(
    key="filtration_boost",
    translation_key="filtration_boost",
    icon="mdi:pump-off",
    options=BOOST_PRESETS,
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
        entities.append(PoolmanFiltrationBoostSelect(coordinator))
    async_add_entities(entities)


class PoolmanModeSelect(PoolmanEntity, SelectEntity, RestoreEntity):
    """Select entity for pool operating mode.

    The selected mode is persisted across restarts via RestoreEntity.
    When entering ``WINTER_PASSIVE`` mode, the filtration scheduler is
    paused and the pump is stopped immediately.
    """

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

    async def async_added_to_hass(self) -> None:
        """Restore the last known pool mode."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) is not None and last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                restored_mode = PoolMode(last_state.state)
            except ValueError:
                restored_mode = PoolMode.ACTIVE
            await self.coordinator.async_set_mode(restored_mode)

    async def async_select_option(self, option: str) -> None:
        """Change the pool mode."""
        await self.coordinator.async_set_mode(PoolMode(option))
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


class PoolmanFiltrationBoostSelect(PoolmanEntity, SelectEntity, RestoreEntity):
    """Select entity for filtration boost presets.

    Allows triggering a manual filtration boost by selecting a preset
    duration (+2h, +4h, +8h, +24h) or cancelling an active boost
    by selecting "none".

    The boost end time is persisted via extra state attributes so that
    it can be restored after a Home Assistant restart.
    """

    entity_description: SelectEntityDescription

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration boost select."""
        super().__init__(coordinator)
        self.entity_description = FILTRATION_BOOST_DESCRIPTION
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration_boost"
        self._attr_current_option = BOOST_PRESET_NONE

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return extra state attributes for persistence.

        Stores the boost end datetime so it can be restored after
        a Home Assistant restart.

        Returns:
            Dictionary with ``boost_end`` ISO-format string, or None.
        """
        scheduler = self.coordinator.scheduler
        boost_end = scheduler.boost_end if scheduler is not None else None
        return {
            "boost_end": boost_end.isoformat() if boost_end is not None else None,
        }

    async def async_added_to_hass(self) -> None:
        """Restore the boost from persisted state after HA restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        # Restore boost from the persisted boost_end attribute
        boost_end_str = last_state.attributes.get("boost_end")
        if boost_end_str is not None and self.coordinator.scheduler is not None:
            try:
                boost_end = datetime.fromisoformat(boost_end_str)
                await self.coordinator.scheduler.async_restore_boost(boost_end)
                # Set the select to a non-"none" value while boost is active
                if self.coordinator.scheduler.boost_active:
                    self._attr_current_option = last_state.state
            except (ValueError, TypeError):
                pass

    def _handle_coordinator_update(self) -> None:
        """Auto-reset select to "none" when boost expires naturally.

        Called by the coordinator after each data refresh.
        """
        super()._handle_coordinator_update()
        scheduler = self.coordinator.scheduler
        if scheduler is not None and not scheduler.boost_active:
            self._attr_current_option = BOOST_PRESET_NONE

    async def async_select_option(self, option: str) -> None:
        """Handle a boost preset selection.

        Selecting "none" cancels any active boost.  Selecting a numeric
        preset activates a boost for that many hours.

        Args:
            option: The selected preset ("none", "2", "4", "8", or "24").
        """
        self._attr_current_option = option
        if option == BOOST_PRESET_NONE:
            await self.coordinator.async_cancel_boost()
        else:
            hours = float(option)
            await self.coordinator.async_boost_filtration(hours)
        self.async_write_ha_state()
