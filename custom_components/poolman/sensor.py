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
from homeassistant.const import UnitOfMass, UnitOfTemperature, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import PoolmanConfigEntry
from .coordinator import PoolmanCoordinator
from .domain.action import Action
from .domain.activation import ActivationStep
from .domain.inventory import Product
from .domain.model import (
    ActionKind,
    ChemistryStatus,
    ParameterReport,
    PoolState,
    PoolStatus,
    Severity,
    format_treatment_spoon,
)
from .domain.problem import Problem
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
_POOL_STATUS_OPTIONS: list[str] = list(PoolStatus)


def _chemistry_actions_attrs(state: PoolState) -> dict[str, Any]:
    """Build attributes for the ``chemistry_actions`` sensor.

    Reuses :meth:`Recommendation.to_dict` for the base serialization and
    enriches each treatment with a chemistry-specific ``spoon`` hint when
    pool spoon sizes are configured.
    """
    spoons = state.pool.spoon_sizes if state.pool else None
    actions: list[dict[str, Any]] = []
    for rec in state.chemistry_actions:
        data = rec.to_dict()
        for treatment_dict, treatment in zip(data["treatments"], rec.treatments, strict=True):
            treatment_dict["spoon"] = format_treatment_spoon(treatment, spoons) if spoons else None
        actions.append(data)
    return {
        "actions": actions,
        "suggestion_count": sum(
            1 for r in state.chemistry_actions if r.kind == ActionKind.SUGGESTION
        ),
        "requirement_count": sum(
            1 for r in state.chemistry_actions if r.kind == ActionKind.REQUIREMENT
        ),
    }


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


def _problem_to_dict(problem: Problem) -> dict[str, Any]:
    """Serialize a :class:`Problem` to a JSON-safe dictionary for HA attributes.

    Args:
        problem: The problem to serialize.

    Returns:
        Dictionary with primitive types only, suitable for the Home Assistant
        state machine. Enum values are emitted as plain strings.
    """
    return {
        "code": problem.code,
        "severity": problem.severity.value,
        "metric": problem.metric.value if problem.metric is not None else None,
        "value": problem.value,
        "expected_range": (
            list(problem.expected_range) if problem.expected_range is not None else None
        ),
        "message": problem.message,
    }


def _problems_attrs(state: PoolState) -> dict[str, Any]:
    """Build attributes for the ``problems`` sensor.

    Problems are sorted by severity (highest first); ties keep the order
    produced by the analysis pipeline. ``worst_severity`` is ``"ok"`` when
    no problems are present, otherwise the severity of the first item.

    Args:
        state: The current pool state.

    Returns:
        Dictionary with ``problems`` (list of serialized problems) and
        ``worst_severity`` (``"ok" | "low" | "medium" | "critical"``).
    """
    problems = sorted(
        state.analysis_result.problems,
        key=lambda p: _SEVERITY_ORDER.get(p.severity, 0),
        reverse=True,
    )
    worst = problems[0].severity.value if problems else "ok"
    return {
        "problems": [_problem_to_dict(p) for p in problems],
        "worst_severity": worst,
    }


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
        key="free_chlorine",
        translation_key="free_chlorine",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:flask-outline",
        value_fn=lambda state: state.reading.free_chlorine,
        extra_attrs_fn=lambda state: _source_attr(state, "free_chlorine"),
    ),
    PoolmanSensorEntityDescription(
        key="ec",
        translation_key="ec",
        native_unit_of_measurement="µS/cm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash-outline",
        value_fn=lambda state: state.reading.ec,
        extra_attrs_fn=lambda state: _source_attr(state, "ec"),
    ),
    PoolmanSensorEntityDescription(
        key="tds",
        translation_key="tds",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:water-opacity",
        value_fn=lambda state: state.reading.tds,
        extra_attrs_fn=lambda state: _source_attr(state, "tds"),
    ),
    PoolmanSensorEntityDescription(
        key="salt",
        translation_key="salt_level",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:shaker-outline",
        value_fn=lambda state: state.reading.salt,
        extra_attrs_fn=lambda state: _source_attr(state, "salt"),
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
            "recommendations": [r.to_dict() for r in state.recommendations],
            "critical_count": len(state.critical_recommendations),
        },
    ),
    PoolmanSensorEntityDescription(
        key="problems",
        translation_key="problems",
        icon="mdi:alert-circle-outline",
        value_fn=lambda state: len(state.analysis_result.problems),
        extra_attrs_fn=_problems_attrs,
    ),
    PoolmanSensorEntityDescription(
        key="chemistry_actions",
        translation_key="chemistry_actions",
        icon="mdi:flask-outline",
        value_fn=lambda state: len(state.chemistry_actions),
        extra_attrs_fn=lambda state: _chemistry_actions_attrs(state),
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
        key="free_chlorine_status",
        translation_key="free_chlorine_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:flask-outline",
        value_fn=lambda state: (
            state.chemistry_report.free_chlorine.status
            if state.chemistry_report.free_chlorine
            else None
        ),
        extra_attrs_fn=lambda state: _status_with_source(
            state, state.chemistry_report.free_chlorine, "free_chlorine"
        ),
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
        key="salt_status",
        translation_key="salt_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:shaker-outline",
        value_fn=lambda state: (
            state.chemistry_report.salt.status if state.chemistry_report.salt else None
        ),
        extra_attrs_fn=lambda state: _status_with_source(
            state, state.chemistry_report.salt, "salt"
        ),
    ),
    PoolmanSensorEntityDescription(
        key="tds_status",
        translation_key="tds_status",
        device_class=SensorDeviceClass.ENUM,
        options=_CHEMISTRY_STATUS_OPTIONS,
        icon="mdi:water-opacity",
        value_fn=lambda state: (
            state.chemistry_report.tds.status if state.chemistry_report.tds else None
        ),
        extra_attrs_fn=lambda state: _status_with_source(state, state.chemistry_report.tds, "tds"),
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
    PoolmanSensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=_POOL_STATUS_OPTIONS,
        value_fn=lambda state: state.status,
        extra_attrs_fn=lambda state: {
            "problem_count": len(state.analysis_result.problems),
            "critical_count": sum(
                1 for p in state.analysis_result.problems if p.severity is Severity.CRITICAL
            ),
            "worst_severity": (
                state.analysis_result.problems[0].severity
                if state.analysis_result.problems
                else None
            ),
        },
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
    entities.append(PoolmanActionHistorySensor(coordinator))

    # Inventory: one quantity sensor per configured product, with
    # dynamic discovery of products added later via services.
    known_inventory_ids: set[str] = set()

    def _add_inventory_entities(product_ids: set[str]) -> None:
        new_entities: list[SensorEntity] = []
        for product_id in product_ids:
            product = coordinator.inventory.products.get(product_id)
            if product is None or product_id in known_inventory_ids:
                continue
            known_inventory_ids.add(product_id)
            new_entities.append(PoolmanInventorySensor(coordinator, product))
        if new_entities:
            async_add_entities(new_entities)

    initial_ids = set(coordinator.inventory.products.keys())
    for product_id in initial_ids:
        known_inventory_ids.add(product_id)
        entities.append(
            PoolmanInventorySensor(coordinator, coordinator.inventory.products[product_id])
        )

    async_add_entities(entities)

    @callback
    def _on_inventory_change(added: set[str], _removed: set[str]) -> None:
        if added:
            _add_inventory_entities(added)

    entry.async_on_unload(coordinator.on_inventory_change(_on_inventory_change))


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


class PoolmanActivationStepSensor(PoolmanEntity, SensorEntity):
    """Sensor showing the current activation wizard step.

    Displays the next pending activation step or None when the pool is
    not in activating mode. State persistence is handled by the
    activation subentry; the coordinator restores the checklist on
    startup from subentry data.
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
        """Return activation progress details for display.

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


# Default cap for the action history exposed via the sensor's attributes.
_ACTION_HISTORY_LIMIT = 50


def _serialize_action(action: Action) -> dict[str, Any]:
    """Serialize an :class:`Action` for transport to the frontend.

    Mirrors :meth:`ActionLog.to_dict` for a single entry: timestamps as
    ISO-8601 strings and durations as a number of seconds, both natively
    JSON-serializable by Home Assistant.

    Args:
        action: The action to serialize.

    Returns:
        A JSON-friendly dictionary describing the action.
    """
    return {
        "id": action.id,
        "type": action.type.value,
        "source": action.source.value,
        "treatment_id": action.treatment_id,
        "quantity": action.quantity,
        "unit": action.unit,
        "timestamp": action.timestamp.isoformat(),
        "recommendation_id": action.recommendation_id,
        "product_id": action.product_id,
        "duration": (action.duration.total_seconds() if action.duration is not None else None),
    }


class PoolmanActionHistorySensor(PoolmanEntity, SensorEntity):
    """Sensor exposing the recorded action history to the frontend.

    The state holds the timestamp of the most recently recorded action,
    while ``extra_state_attributes`` carries a JSON-friendly list of the
    last :data:`_ACTION_HISTORY_LIMIT` actions for the action history
    Lovelace card. The coordinator persists the underlying
    :class:`~.domain.action.ActionLog` and notifies its update listeners
    whenever a new action is recorded, so the entity is refreshed
    automatically via :class:`CoordinatorEntity`.
    """

    _attr_translation_key = "action_history"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the action history sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_action_history"

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the most recently recorded action."""
        history = self.coordinator.action_log.history(1)
        if not history:
            return None
        return history[0].timestamp

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the last 50 actions plus the total count for the card."""
        actions = self.coordinator.action_log.history(_ACTION_HISTORY_LIMIT)
        return {
            "actions": [_serialize_action(action) for action in actions],
            "limit": _ACTION_HISTORY_LIMIT,
            "total": len(self.coordinator.action_log.actions),
        }


# Mapping from inventory unit string to (HA unit constant, device class).
_INVENTORY_UNIT_MAP: dict[str, tuple[str | None, SensorDeviceClass | None]] = {
    "g": (UnitOfMass.GRAMS, SensorDeviceClass.WEIGHT),
    "kg": (UnitOfMass.KILOGRAMS, SensorDeviceClass.WEIGHT),
    "mL": (UnitOfVolume.MILLILITERS, SensorDeviceClass.VOLUME_STORAGE),
    "L": (UnitOfVolume.LITERS, SensorDeviceClass.VOLUME_STORAGE),
    "tablet": (None, None),
}


class PoolmanInventorySensor(PoolmanEntity, SensorEntity):
    """Sensor reporting the current stock for a single inventory product."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:package-variant"

    def __init__(self, coordinator: PoolmanCoordinator, product: Product) -> None:
        """Initialize the inventory sensor.

        Args:
            coordinator: The pool coordinator owning the inventory.
            product: The product this sensor reports stock for.
        """
        super().__init__(coordinator)
        self._product_id = product.id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_inventory_{product.id}"
        self._attr_translation_key = "inventory_product"
        self._attr_translation_placeholders = {"product_name": product.name}
        self._attr_name = product.name
        unit, device_class = _INVENTORY_UNIT_MAP.get(product.unit, (product.unit, None))
        self._attr_native_unit_of_measurement = unit
        if device_class is not None:
            self._attr_device_class = device_class

    @property
    def available(self) -> bool:
        """Return whether the product is still in the inventory catalog."""
        return super().available and self._product_id in self.coordinator.inventory.products

    @property
    def native_value(self) -> float | None:
        """Return the current quantity in stock, or ``None`` if unknown."""
        item = self.coordinator.inventory.get(self._product_id)
        return item.quantity if item is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return product metadata and low-stock state as attributes."""
        product = self.coordinator.inventory.products.get(self._product_id)
        item = self.coordinator.inventory.get(self._product_id)
        if product is None:
            return {}
        return {
            "product_id": product.id,
            "product_name": product.name,
            "unit": product.unit,
            "chemical": product.chemical.value if product.chemical else None,
            "low_stock_threshold": item.low_stock_threshold if item is not None else None,
            "is_low": self.coordinator.inventory.is_low(self._product_id),
        }
