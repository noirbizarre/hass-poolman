"""Event platform for Pool Manager.

Provides:
- A filtration event entity that fires when the pump starts or stops.
- One event entity per chemical product to track treatment applications.
  Each treatment entity uses RestoreEntity (via EventEntity) for persistence
  across HA restarts. HA's built-in logbook/history serves as the pool
  treatment log.
- One event entity per measurable parameter to track manual measurements.
  These serve as a measurement journal, visible in HA's logbook/history.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PoolmanConfigEntry
from .const import (
    EVENT_BOOST_CANCELLED,
    EVENT_BOOST_CONSUMED,
    EVENT_BOOST_STARTED,
    EVENT_FILTRATION_STARTED,
    EVENT_FILTRATION_STOPPED,
)
from .coordinator import PoolmanCoordinator
from .domain.model import ChemicalProduct, MeasureParameter, TreatmentType
from .entity import PoolmanEntity


@dataclass(kw_only=True, frozen=True)
class PoolmanEventEntityDescription(EventEntityDescription):
    """Describes a Pool Manager treatment event entity.

    Attributes:
        product: The chemical product this entity tracks.
        enabled_for: Set of treatment types for which this entity is enabled
            by default. None means it is universal (always enabled).
    """

    product: ChemicalProduct
    enabled_for: frozenset[TreatmentType] | None = None


# Universal products are available regardless of configured treatment type
_UNIVERSAL: None = None

# Treatment-specific product groups
_CHLORINE_PRODUCTS = frozenset({TreatmentType.CHLORINE, TreatmentType.SALT_ELECTROLYSIS})
_SALT_ONLY = frozenset({TreatmentType.SALT_ELECTROLYSIS})
_BROMINE_PRODUCTS = frozenset({TreatmentType.BROMINE})
_ACTIVE_OXYGEN_PRODUCTS = frozenset({TreatmentType.ACTIVE_OXYGEN})

EVENT_DESCRIPTIONS: tuple[PoolmanEventEntityDescription, ...] = (
    # pH adjustments (universal)
    PoolmanEventEntityDescription(
        key="ph_minus",
        translation_key="ph_minus",
        event_types=["applied"],
        product=ChemicalProduct.PH_MINUS,
        enabled_for=_UNIVERSAL,
    ),
    PoolmanEventEntityDescription(
        key="ph_plus",
        translation_key="ph_plus",
        event_types=["applied"],
        product=ChemicalProduct.PH_PLUS,
        enabled_for=_UNIVERSAL,
    ),
    # Chlorine products
    PoolmanEventEntityDescription(
        key="chlore_choc",
        translation_key="chlore_choc",
        event_types=["applied"],
        product=ChemicalProduct.CHLORE_CHOC,
        enabled_for=_CHLORINE_PRODUCTS,
    ),
    PoolmanEventEntityDescription(
        key="galet_chlore",
        translation_key="galet_chlore",
        event_types=["applied"],
        product=ChemicalProduct.GALET_CHLORE,
        enabled_for=frozenset({TreatmentType.CHLORINE}),
    ),
    # Neutralizer (universal)
    PoolmanEventEntityDescription(
        key="neutralizer",
        translation_key="neutralizer",
        event_types=["applied"],
        product=ChemicalProduct.NEUTRALIZER,
        enabled_for=_UNIVERSAL,
    ),
    # Alkalinity (universal)
    PoolmanEventEntityDescription(
        key="tac_plus",
        translation_key="tac_plus",
        event_types=["applied"],
        product=ChemicalProduct.TAC_PLUS,
        enabled_for=_UNIVERSAL,
    ),
    # Salt (salt electrolysis only)
    PoolmanEventEntityDescription(
        key="salt",
        translation_key="salt",
        event_types=["applied"],
        product=ChemicalProduct.SALT,
        enabled_for=_SALT_ONLY,
    ),
    # Bromine products
    PoolmanEventEntityDescription(
        key="bromine_tablet",
        translation_key="bromine_tablet",
        event_types=["applied"],
        product=ChemicalProduct.BROMINE_TABLET,
        enabled_for=_BROMINE_PRODUCTS,
    ),
    PoolmanEventEntityDescription(
        key="bromine_shock",
        translation_key="bromine_shock",
        event_types=["applied"],
        product=ChemicalProduct.BROMINE_SHOCK,
        enabled_for=_BROMINE_PRODUCTS,
    ),
    # Active oxygen products
    PoolmanEventEntityDescription(
        key="active_oxygen_tablet",
        translation_key="active_oxygen_tablet",
        event_types=["applied"],
        product=ChemicalProduct.ACTIVE_OXYGEN_TABLET,
        enabled_for=_ACTIVE_OXYGEN_PRODUCTS,
    ),
    PoolmanEventEntityDescription(
        key="active_oxygen_activator",
        translation_key="active_oxygen_activator",
        event_types=["applied"],
        product=ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR,
        enabled_for=_ACTIVE_OXYGEN_PRODUCTS,
    ),
    # Flocculant (universal)
    PoolmanEventEntityDescription(
        key="flocculant",
        translation_key="flocculant",
        event_types=["applied"],
        product=ChemicalProduct.FLOCCULANT,
        enabled_for=_UNIVERSAL,
    ),
    # Anti-algae (universal)
    PoolmanEventEntityDescription(
        key="anti_algae",
        translation_key="anti_algae",
        event_types=["applied"],
        product=ChemicalProduct.ANTI_ALGAE,
        enabled_for=_UNIVERSAL,
    ),
    # Stabilizer / CYA (universal)
    PoolmanEventEntityDescription(
        key="stabilizer",
        translation_key="stabilizer",
        event_types=["applied"],
        product=ChemicalProduct.STABILIZER,
        enabled_for=_UNIVERSAL,
    ),
    # Clarifier (universal)
    PoolmanEventEntityDescription(
        key="clarifier",
        translation_key="clarifier",
        event_types=["applied"],
        product=ChemicalProduct.CLARIFIER,
        enabled_for=_UNIVERSAL,
    ),
    # Metal sequestrant (universal)
    PoolmanEventEntityDescription(
        key="metal_sequestrant",
        translation_key="metal_sequestrant",
        event_types=["applied"],
        product=ChemicalProduct.METAL_SEQUESTRANT,
        enabled_for=_UNIVERSAL,
    ),
    # Calcium hardness increaser (universal)
    PoolmanEventEntityDescription(
        key="calcium_hardness_increaser",
        translation_key="calcium_hardness_increaser",
        event_types=["applied"],
        product=ChemicalProduct.CALCIUM_HARDNESS_INCREASER,
        enabled_for=_UNIVERSAL,
    ),
    # Winterizing product (universal)
    PoolmanEventEntityDescription(
        key="winterizing_product",
        translation_key="winterizing_product",
        event_types=["applied"],
        product=ChemicalProduct.WINTERIZING_PRODUCT,
        enabled_for=_UNIVERSAL,
    ),
)


@dataclass(kw_only=True, frozen=True)
class PoolmanMeasureEventEntityDescription(EventEntityDescription):
    """Describes a Pool Manager manual measurement event entity.

    Attributes:
        parameter: The pool parameter this entity tracks.
    """

    parameter: MeasureParameter


MEASURE_EVENT_DESCRIPTIONS: tuple[PoolmanMeasureEventEntityDescription, ...] = (
    PoolmanMeasureEventEntityDescription(
        key="measure_ph",
        translation_key="measure_ph",
        event_types=["measured"],
        parameter=MeasureParameter.PH,
    ),
    PoolmanMeasureEventEntityDescription(
        key="measure_orp",
        translation_key="measure_orp",
        event_types=["measured"],
        parameter=MeasureParameter.ORP,
    ),
    PoolmanMeasureEventEntityDescription(
        key="measure_tac",
        translation_key="measure_tac",
        event_types=["measured"],
        parameter=MeasureParameter.TAC,
    ),
    PoolmanMeasureEventEntityDescription(
        key="measure_cya",
        translation_key="measure_cya",
        event_types=["measured"],
        parameter=MeasureParameter.CYA,
    ),
    PoolmanMeasureEventEntityDescription(
        key="measure_hardness",
        translation_key="measure_hardness",
        event_types=["measured"],
        parameter=MeasureParameter.HARDNESS,
    ),
    PoolmanMeasureEventEntityDescription(
        key="measure_temperature",
        translation_key="measure_temperature",
        event_types=["measured"],
        parameter=MeasureParameter.TEMPERATURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PoolmanConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Pool Manager event entities."""
    coordinator: PoolmanCoordinator = entry.runtime_data
    entities: list[PoolmanEntity] = [
        PoolmanTreatmentEvent(coordinator, description) for description in EVENT_DESCRIPTIONS
    ]
    entities.extend(
        PoolmanMeasureEvent(coordinator, description) for description in MEASURE_EVENT_DESCRIPTIONS
    )
    if coordinator.scheduler is not None:
        entities.append(PoolmanFiltrationEvent(coordinator))
    async_add_entities(entities)


class PoolmanFiltrationEvent(PoolmanEntity, EventEntity):
    """Event entity that fires when filtration starts or stops.

    Listens to the FiltrationScheduler via its on_event() callback
    and triggers HA event entity updates with schedule details.
    """

    _attr_translation_key = "filtration"
    _attr_icon = "mdi:pump"
    _attr_event_types: ClassVar[list[str]] = [
        EVENT_FILTRATION_STARTED,
        EVENT_FILTRATION_STOPPED,
        EVENT_BOOST_STARTED,
        EVENT_BOOST_CONSUMED,
        EVENT_BOOST_CANCELLED,
    ]

    def __init__(self, coordinator: PoolmanCoordinator) -> None:
        """Initialize the filtration event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_filtration"
        self._unsub_scheduler: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register scheduler event listener when added to HA."""
        await super().async_added_to_hass()
        if self.coordinator.scheduler is not None:
            self._unsub_scheduler = self.coordinator.scheduler.on_event(self._on_scheduler_event)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister scheduler event listener when removed from HA."""
        if self._unsub_scheduler is not None:
            self._unsub_scheduler()
            self._unsub_scheduler = None
        await super().async_will_remove_from_hass()

    def _on_scheduler_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Handle a scheduler event by triggering the HA event entity.

        Args:
            event_type: The event type (filtration_started or filtration_stopped).
            event_data: Schedule details (start_time, duration_hours, end_time).
        """
        self._trigger_event(event_type, event_data)
        self.async_write_ha_state()


class PoolmanTreatmentEvent(PoolmanEntity, EventEntity):
    """Event entity tracking a chemical product treatment application.

    Each entity represents one chemical product. When the product is applied
    to the pool (via the add_treatment service), an "applied" event is fired.
    HA's RestoreEntity persistence ensures the last application timestamp
    survives HA restarts.
    """

    entity_description: PoolmanEventEntityDescription

    def __init__(
        self,
        coordinator: PoolmanCoordinator,
        description: PoolmanEventEntityDescription,
    ) -> None:
        """Initialize the treatment event entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

        # Disable by default if the product is not relevant to the configured treatment
        if description.enabled_for is not None:
            self._attr_entity_registry_enabled_default = (
                coordinator.pool.treatment in description.enabled_for
            )

    async def async_added_to_hass(self) -> None:
        """Register this entity with the coordinator when added to HA."""
        await super().async_added_to_hass()
        self.coordinator.register_treatment_entity(self.entity_description.product, self)

    @callback
    def apply_treatment(
        self,
        quantity_g: float | None = None,
        notes: str | None = None,
    ) -> None:
        """Record a treatment application by firing an event.

        Args:
            quantity_g: Amount of product used in grams.
            notes: Optional free-text note about the treatment.
        """
        event_data: dict[str, Any] = {}
        if quantity_g is not None:
            event_data["quantity_g"] = quantity_g
        if notes is not None:
            event_data["notes"] = notes
        self._trigger_event("applied", event_data)
        self.async_write_ha_state()


class PoolmanMeasureEvent(PoolmanEntity, EventEntity):
    """Event entity tracking a manual measurement for a pool parameter.

    Each entity represents one measurable parameter (pH, ORP, TAC, etc.).
    When the user records a measurement (via the record_measure service),
    a "measured" event is fired with the value in the event data.
    HA's RestoreEntity persistence (via EventEntity) ensures the last
    measurement survives HA restarts. HA's logbook/history serves as the
    measurement journal.
    """

    entity_description: PoolmanMeasureEventEntityDescription

    def __init__(
        self,
        coordinator: PoolmanCoordinator,
        description: PoolmanMeasureEventEntityDescription,
    ) -> None:
        """Initialize the measure event entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_icon = "mdi:test-tube"

    async def async_added_to_hass(self) -> None:
        """Register this entity with the coordinator when added to HA."""
        await super().async_added_to_hass()
        self.coordinator.register_measure_entity(self.entity_description.parameter, self)

    @callback
    def record_measure(
        self,
        value: float,
        notes: str | None = None,
    ) -> None:
        """Record a manual measurement by firing an event.

        Args:
            value: The measured value.
            notes: Optional free-text note about the measurement.
        """
        event_data: dict[str, Any] = {"value": value}
        if notes is not None:
            event_data["notes"] = notes
        self._trigger_event("measured", event_data)
        self.async_write_ha_state()
