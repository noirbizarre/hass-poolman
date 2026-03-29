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
from .domain.model import ChemistryStatus, ParameterReport, PoolState
from .entity import PoolmanEntity


@dataclass(kw_only=True, frozen=True)
class PoolmanSensorEntityDescription(SensorEntityDescription):
    """Describes a Pool Manager sensor entity."""

    value_fn: Callable[[PoolState], StateType]
    extra_attrs_fn: Callable[[PoolState], dict[str, Any]] | None = None


def _parameter_report_attrs(report: ParameterReport | None) -> dict[str, Any]:
    """Extract extra state attributes from a parameter report.

    Args:
        report: The parameter report, or None if the reading is unavailable.

    Returns:
        Dictionary with value, target, range, and score; empty if report is None.
    """
    if report is None:
        return {}
    return {
        "value": report.value,
        "target": report.target,
        "minimum": report.minimum,
        "maximum": report.maximum,
        "score": report.score,
    }


_CHEMISTRY_STATUS_OPTIONS: list[str] = list(ChemistryStatus)


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
    PoolmanSensorEntityDescription(
        key="ph_status",
        translation_key="ph_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:ph",
        value_fn=lambda state: (
            state.chemistry_report.ph.status if state.chemistry_report.ph else None
        ),
        extra_attrs_fn=lambda state: _parameter_report_attrs(state.chemistry_report.ph),
    ),
    PoolmanSensorEntityDescription(
        key="orp_status",
        translation_key="orp_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:flash-triangle-outline",
        value_fn=lambda state: (
            state.chemistry_report.orp.status if state.chemistry_report.orp else None
        ),
        extra_attrs_fn=lambda state: _parameter_report_attrs(state.chemistry_report.orp),
    ),
    PoolmanSensorEntityDescription(
        key="tac_status",
        translation_key="tac_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:water-opacity",
        value_fn=lambda state: (
            state.chemistry_report.tac.status if state.chemistry_report.tac else None
        ),
        extra_attrs_fn=lambda state: _parameter_report_attrs(state.chemistry_report.tac),
    ),
    PoolmanSensorEntityDescription(
        key="cya_status",
        translation_key="cya_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:shield-sun-outline",
        value_fn=lambda state: (
            state.chemistry_report.cya.status if state.chemistry_report.cya else None
        ),
        extra_attrs_fn=lambda state: _parameter_report_attrs(state.chemistry_report.cya),
    ),
    PoolmanSensorEntityDescription(
        key="hardness_status",
        translation_key="hardness_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:water-percent",
        value_fn=lambda state: (
            state.chemistry_report.hardness.status if state.chemistry_report.hardness else None
        ),
        extra_attrs_fn=lambda state: _parameter_report_attrs(state.chemistry_report.hardness),
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
