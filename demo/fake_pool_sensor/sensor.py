"""Sensor platform for Fake Pool Sensor."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FakePoolSensorConfigEntry, FakePoolSensorCoordinator
from .const import DOMAIN, SENSOR_SPECS, FakeSensorSpec

# Map sensor keys to HA device classes where applicable
_DEVICE_CLASSES: dict[str, SensorDeviceClass] = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "outdoor_temperature": SensorDeviceClass.TEMPERATURE,
    "ph": SensorDeviceClass.PH,
}

_DISPLAY_PRECISION: dict[str, int] = {
    "temperature": 1,
    "ph": 2,
    "orp": 0,
    "tac": 0,
    "cya": 0,
    "hardness": 0,
    "outdoor_temperature": 1,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FakePoolSensorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Fake Pool Sensor sensors."""
    coordinator = entry.runtime_data
    async_add_entities(FakePoolSensorEntity(coordinator, spec) for spec in SENSOR_SPECS)


class FakePoolSensorEntity(CoordinatorEntity[FakePoolSensorCoordinator], SensorEntity):
    """A fake pool sensor entity that reports simulated values."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: FakePoolSensorCoordinator,
        spec: FakeSensorSpec,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._spec = spec
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{spec.key}"
        self._attr_name = spec.name
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_icon = spec.icon
        self._attr_suggested_display_precision = _DISPLAY_PRECISION.get(spec.key, 1)
        if spec.key in _DEVICE_CLASSES:
            self._attr_device_class = _DEVICE_CLASSES[spec.key]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="Fake Pool Sensor",
            model="Simulator",
        )

    @property
    def native_value(self) -> StateType:
        """Return the current simulated value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._spec.key)
