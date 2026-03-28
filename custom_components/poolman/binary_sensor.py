"""Binary sensor platform for Pool Manager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.model import PoolState
from .entity import PoolmanEntity


@dataclass(kw_only=True, frozen=True)
class PoolmanBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Pool Manager binary sensor."""

    is_on_fn: Callable[[PoolState], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[PoolmanBinarySensorDescription, ...] = (
    PoolmanBinarySensorDescription(
        key="water_ok",
        translation_key="water_ok",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda state: state.water_ok,
    ),
    PoolmanBinarySensorDescription(
        key="action_required",
        translation_key="action_required",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda state: state.action_required,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager binary sensors."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    async_add_entities(
        PoolmanBinarySensor(coordinator, description) for description in BINARY_SENSOR_DESCRIPTIONS
    )


class PoolmanBinarySensor(PoolmanEntity, BinarySensorEntity):
    """Representation of a Pool Manager binary sensor."""

    entity_description: PoolmanBinarySensorDescription

    def __init__(
        self,
        coordinator: PoolmanCoordinator,
        description: PoolmanBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.entity_description.is_on_fn(self.pool_state)
