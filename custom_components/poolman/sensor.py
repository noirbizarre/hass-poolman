"""Sensor platform for Pool Manager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.activation import ActivationChecklist, ActivationStep
from .domain.model import ActionKind, ChemistryStatus, ParameterReport, PoolMode, PoolState
from .entity import PoolmanEntity


@dataclass(kw_only=True, frozen=True)
class PoolmanSensorEntityDescription(SensorEntityDescription):
    """Describes a Pool Manager sensor entity."""

    value_fn: Callable[[PoolState], StateType | datetime | None]
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


def _source_attr(state: PoolState, parameter: str) -> dict[str, Any]:
    """Build extra attributes including the measurement source.

    Args:
        state: The current pool state.
        parameter: The reading parameter key (e.g. "ph", "orp", "temperature").

    Returns:
        Dictionary with ``measurement_source`` set to "sensor", "manual",
        or absent if the parameter has no value.
    """
    source = state.reading_sources.get(parameter)
    if source is None:
        return {}
    return {"measurement_source": source}


def _status_with_source(
    state: PoolState, report: ParameterReport | None, parameter: str
) -> dict[str, Any]:
    """Merge parameter-report attributes with the measurement source.

    Args:
        state: The current pool state.
        report: The parameter report, or None if the reading is unavailable.
        parameter: The reading parameter key for source lookup.

    Returns:
        Combined dictionary of report attributes and measurement source.
    """
    attrs = _parameter_report_attrs(report)
    source = state.reading_sources.get(parameter)
    if source is not None:
        attrs["measurement_source"] = source
    return attrs


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
        extra_attrs_fn=lambda state: _source_attr(state, "temperature"),
    ),
    PoolmanSensorEntityDescription(
        key="ph",
        translation_key="ph",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda state: state.reading.ph,
        extra_attrs_fn=lambda state: _source_attr(state, "ph"),
    ),
    PoolmanSensorEntityDescription(
        key="orp",
        translation_key="orp",
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda state: state.reading.orp,
        extra_attrs_fn=lambda state: _source_attr(state, "orp"),
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
        key="chemistry_actions",
        translation_key="chemistry_actions",
        icon="mdi:flask-outline",
        value_fn=lambda state: len(state.chemistry_actions),
        extra_attrs_fn=lambda state: {
            "actions": [
                {
                    "kind": r.kind,
                    "message": r.message,
                    "product": r.product,
                    "quantity_g": r.quantity_g,
                }
                for r in state.chemistry_actions
            ],
            "suggestion_count": len(
                [r for r in state.chemistry_actions if r.kind == ActionKind.SUGGESTION]
            ),
            "requirement_count": len(
                [r for r in state.chemistry_actions if r.kind == ActionKind.REQUIREMENT]
            ),
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
        extra_attrs_fn=lambda state: _status_with_source(state, state.chemistry_report.ph, "ph"),
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
        extra_attrs_fn=lambda state: _status_with_source(state, state.chemistry_report.orp, "orp"),
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
        extra_attrs_fn=lambda state: _status_with_source(state, state.chemistry_report.tac, "tac"),
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
        extra_attrs_fn=lambda state: _status_with_source(state, state.chemistry_report.cya, "cya"),
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
        extra_attrs_fn=lambda state: _status_with_source(
            state, state.chemistry_report.hardness, "hardness"
        ),
    ),
    PoolmanSensorEntityDescription(
        key="active_treatments",
        translation_key="active_treatments",
        icon="mdi:flask",
        value_fn=lambda state: len(state.active_treatments),
        extra_attrs_fn=lambda state: {
            "treatments": [
                {
                    "product": t.product.value,
                    "applied_at": t.applied_at.isoformat(),
                    "safe_at": t.safe_at.isoformat(),
                    "quantity_g": t.quantity_g,
                }
                for t in state.active_treatments
            ],
        },
    ),
    PoolmanSensorEntityDescription(
        key="safe_at",
        translation_key="safe_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:shield-check",
        value_fn=lambda state: state.safe_at,
    ),
)

FILTRATION_SENSOR_DESCRIPTIONS: tuple[PoolmanSensorEntityDescription, ...] = (
    PoolmanSensorEntityDescription(
        key="filtration_boost_remaining",
        translation_key="filtration_boost_remaining",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pump",
        value_fn=lambda state: state.boost_remaining,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager sensors."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    descriptions = list(SENSOR_DESCRIPTIONS)
    if coordinator.scheduler is not None:
        descriptions.extend(FILTRATION_SENSOR_DESCRIPTIONS)
    entities: list[SensorEntity] = [
        PoolmanSensor(coordinator, description) for description in descriptions
    ]
    entities.append(PoolmanActivationStepSensor(coordinator))
    async_add_entities(entities)


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
    def native_value(self) -> StateType | datetime | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.pool_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.extra_attrs_fn is not None:
            return self.entity_description.extra_attrs_fn(self.pool_state)
        return None


class PoolmanActivationStepSensor(PoolmanEntity, SensorEntity, RestoreEntity):
    """Sensor showing the current activation wizard step.

    Displays the next pending activation step or None when the pool is
    not in activating mode. Persists the activation checklist state
    across HA restarts via RestoreEntity.
    """

    _attr_translation_key = "activation_step"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options: ClassVar[list[str]] = [step.value for step in ActivationStep]
    _attr_icon = "mdi:wizard-hat"

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the activation step sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_activation_step"

    @property
    def native_value(self) -> str | None:
        """Return the current (next pending) activation step."""
        activation = self.pool_state.activation
        if activation is None:
            return None
        return activation.current_step

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return activation progress details for persistence and display.

        Returns:
            Dictionary with completed_steps, pending_steps, progress,
            and started_at. Empty dict when not in activating mode.
        """
        activation = self.pool_state.activation
        if activation is None:
            return {}
        completed, total = activation.progress
        return {
            "completed_steps": [s.value for s in activation.completed_steps],
            "pending_steps": [s.value for s in activation.pending_steps],
            "progress": f"{completed}/{total}",
            "started_at": activation.started_at.isoformat(),
        }

    async def async_added_to_hass(self) -> None:
        """Restore activation checklist from persisted state after HA restart."""
        await super().async_added_to_hass()
        if self.coordinator.mode != PoolMode.ACTIVATING:
            return

        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        # Restore the activation checklist from persisted attributes
        attrs = last_state.attributes
        completed_steps_raw = attrs.get("completed_steps", [])
        started_at_raw = attrs.get("started_at")

        if started_at_raw is None:
            return

        try:
            started_at = datetime.fromisoformat(started_at_raw)
        except (ValueError, TypeError):
            return

        # Rebuild the checklist with restored completion status
        steps = dict.fromkeys(ActivationStep, False)
        for step_value in completed_steps_raw:
            try:
                step = ActivationStep(step_value)
                steps[step] = True
            except ValueError:
                continue

        self.coordinator.activation = ActivationChecklist(
            started_at=started_at,
            steps=steps,
        )
