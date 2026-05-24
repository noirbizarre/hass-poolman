"""Binary sensor platform for Pool Manager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.inventory import Product
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
    PoolmanBinarySensorDescription(
        key="swimming_safe",
        translation_key="swimming_safe",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda state: state.swimming_safe,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager binary sensors."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        PoolmanBinarySensor(coordinator, description) for description in BINARY_SENSOR_DESCRIPTIONS
    ]

    known_inventory_ids: set[str] = set()

    def _add_inventory_entities(product_ids: set[str]) -> None:
        new_entities: list[BinarySensorEntity] = []
        for product_id in product_ids:
            product = coordinator.inventory.products.get(product_id)
            if product is None or product_id in known_inventory_ids:
                continue
            known_inventory_ids.add(product_id)
            new_entities.append(PoolmanLowStockBinarySensor(coordinator, product))
        if new_entities:
            async_add_entities(new_entities)

    for product_id, product in coordinator.inventory.products.items():
        known_inventory_ids.add(product_id)
        entities.append(PoolmanLowStockBinarySensor(coordinator, product))

    async_add_entities(entities)

    @callback
    def _on_inventory_change(added: set[str], _removed: set[str]) -> None:
        if added:
            _add_inventory_entities(added)

    entry.async_on_unload(coordinator.on_inventory_change(_on_inventory_change))


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


class PoolmanLowStockBinarySensor(PoolmanEntity, BinarySensorEntity):
    """Binary sensor flagging when a product's stock falls below threshold."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:package-variant-closed-remove"

    def __init__(self, coordinator: PoolmanCoordinator, product: Product) -> None:
        """Initialize the low-stock binary sensor."""
        super().__init__(coordinator)
        self._product_id = product.id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_inventory_{product.id}_low_stock"
        )
        self._attr_translation_key = "inventory_low_stock"
        self._attr_translation_placeholders = {"product_name": product.name}
        self._attr_name = f"{product.name} low stock"

    @property
    def available(self) -> bool:
        """Return whether the product is still in the inventory catalog."""
        return super().available and self._product_id in self.coordinator.inventory.products

    @property
    def is_on(self) -> bool | None:
        """Return whether the product's stock is at or below the threshold."""
        item = self.coordinator.inventory.get(self._product_id)
        if item is None or item.low_stock_threshold is None:
            return False
        return self.coordinator.inventory.is_low(self._product_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return product metadata and current stock figures."""
        product = self.coordinator.inventory.products.get(self._product_id)
        item = self.coordinator.inventory.get(self._product_id)
        if product is None:
            return {}
        return {
            "product_id": product.id,
            "product_name": product.name,
            "unit": product.unit,
            "chemical": product.chemical.value if product.chemical else None,
            "quantity": item.quantity if item is not None else None,
            "low_stock_threshold": item.low_stock_threshold if item is not None else None,
        }
