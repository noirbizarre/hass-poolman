"""Base entity for Pool Manager."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolmanCoordinator
from .domain.model import PoolState


class PoolmanEntity(CoordinatorEntity[PoolmanCoordinator]):
    """Base class for Pool Manager entities.

    Provides shared device info and coordinator access.
    """

    _attr_has_entity_name = True
    coordinator: PoolmanCoordinator

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="Pool Manager",
            model=f"{coordinator.pool.shape.value.capitalize()} pool",
            sw_version="0.1.0",
        )

    @property
    def pool_state(self) -> PoolState:
        """Return the current pool state from coordinator data."""
        return self.coordinator.data
