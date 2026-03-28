"""Sensor platform for Pool Manager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.model import PoolState
from .entity import PoolmanEntity


@dataclass(kw_only=True, frozen=True)
class PoolmanSensorEntityDescription(SensorEntityDescription):
    """Describes a Pool Manager sensor entity."""

    value_fn: Callable[[PoolState], StateType]
    extra_attrs_fn: Callable[[PoolState], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[PoolmanSensorEntityDescription, ...] = (
    PoolmanSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda state: state.reading.temp_c,
    ),
    PoolmanSensorEntityDescription(
        key="ph",
        translation_key="ph",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda state: state.reading.ph,
    ),
    PoolmanSensorEntityDescription(
        key="orp",
        translation_key="orp",
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda state: state.reading.orp,
    ),
    PoolmanSensorEntityDescription(
        key="filtration_duration",
        translation_key="filtration_duration",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pump",
        value_fn=lambda state: state.filtration_hours,
    ),
    PoolmanSensorEntityDescription(
        key="water_quality_score",
        translation_key="water_quality_score",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:water-check",
        value_fn=lambda state: state.water_quality_score,
    ),
    PoolmanSensorEntityDescription(
        key="recommendations",
        translation_key="recommendations",
        icon="mdi:clipboard-list",
        value_fn=lambda state: len(state.recommendations),
        extra_attrs_fn=lambda state: {
            "actions": [str(r) for r in state.recommendations],
            "critical_count": len(state.critical_recommendations),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager sensors."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    async_add_entities(
        PoolmanSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class PoolmanSensor(PoolmanEntity, SensorEntity):
    """Representation of a Pool Manager sensor."""

    entity_description: PoolmanSensorEntityDescription

    def __init__(
        self,
        coordinator: PoolmanCoordinator,
        description: PoolmanSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.pool_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.extra_attrs_fn is not None:
            return self.entity_description.extra_attrs_fn(self.pool_state)
        return None
