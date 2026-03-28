"""Number platform for Fake Pool Sensor target controls."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FakePoolSensorConfigEntry, FakePoolSensorCoordinator
from .const import DOMAIN, SENSOR_SPECS, FakeSensorSpec


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FakePoolSensorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Fake Pool Sensor number controls."""
    coordinator = entry.runtime_data
    async_add_entities(FakePoolTargetNumber(coordinator, spec) for spec in SENSOR_SPECS)


class FakePoolTargetNumber(NumberEntity):
    """Number entity to adjust the target value for a fake sensor."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: FakePoolSensorCoordinator,
        spec: FakeSensorSpec,
    ) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._spec = spec
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{spec.key}_target"
        self._attr_name = f"{spec.name} target"
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step
        self._attr_icon = spec.icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="Fake Pool Sensor",
            model="Simulator",
        )

    @property
    def native_value(self) -> float:
        """Return the current target value."""
        return self._coordinator.targets[self._spec.key]

    async def async_set_native_value(self, value: float) -> None:
        """Update the target value."""
        self._coordinator.targets[self._spec.key] = value
        await self._coordinator.async_request_refresh()
