"""DataUpdateCoordinator for Pool Manager."""

from __future__ import annotations

import contextlib
import logging

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import utcnow

from .const import (
    CONF_CYA_ENTITY,
    CONF_FILTRATION_KIND,
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_PH_ENTITY,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TAC_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    CONF_WEATHER_ENTITY,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_POOLMAN,
)
from .domain.chemistry import compute_chemistry_report, compute_water_quality_score
from .domain.filtration import compute_filtration_duration
from .domain.model import (
    ChemicalProduct,
    FiltrationKind,
    Pool,
    PoolMode,
    PoolReading,
    PoolShape,
    PoolState,
    TreatmentType,
    compute_status_changes,
)
from .domain.rules import RuleEngine
from .domain.treatment import (
    compute_active_treatments,
    compute_safe_at,
    compute_swimming_safe,
)
from .scheduler import FiltrationScheduler

if TYPE_CHECKING:
    from .event import PoolmanTreatmentEvent

_LOGGER = logging.getLogger(__name__)

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]


class PoolmanCoordinator(DataUpdateCoordinator[PoolState]):
    """Coordinator to manage pool data updates.

    Reads sensor states from Home Assistant, builds a PoolReading,
    runs the rule engine, computes treatment safety, and produces
    a PoolState consumed by all entities.
    """

    config_entry: PoolmanConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: PoolmanConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES),
        )
        self.pool = self._build_pool()
        self.engine = RuleEngine()
        self._mode = PoolMode.RUNNING
        self._treatment_entities: dict[ChemicalProduct, PoolmanTreatmentEvent] = {}

        # Filtration scheduler: only created when a pump entity is configured
        pump_entity_id = self._get_config(CONF_PUMP_ENTITY)
        self.scheduler: FiltrationScheduler | None = (
            FiltrationScheduler(hass, pump_entity_id) if pump_entity_id else None
        )

    def _get_config(self, key: str, default: Any = None) -> Any:
        """Get a config value, checking options first then data.

        Args:
            key: Configuration key to look up.
            default: Fallback value if key is not found in either source.

        Returns:
            The configuration value.
        """
        if key in self.config_entry.options:
            return self.config_entry.options[key]
        return self.config_entry.data.get(key, default)

    def _build_pool(self) -> Pool:
        """Build the Pool model from config entry data and options.

        Returns:
            A Pool instance reflecting the current configuration.
        """
        data = self.config_entry.data
        return Pool(
            volume_m3=data[CONF_VOLUME_M3],
            shape=PoolShape(data[CONF_SHAPE]),
            treatment=TreatmentType(self._get_config(CONF_TREATMENT, DEFAULT_TREATMENT)),
            filtration_kind=FiltrationKind(
                self._get_config(CONF_FILTRATION_KIND, DEFAULT_FILTRATION_KIND)
            ),
            pump_flow_m3h=self._get_config(CONF_PUMP_FLOW_M3H),
        )

    @property
    def mode(self) -> PoolMode:
        """Return the current pool mode."""
        return self._mode

    @mode.setter
    def mode(self, value: PoolMode) -> None:
        """Set the pool mode and trigger a refresh."""
        self._mode = value

    def register_treatment_entity(
        self,
        product: ChemicalProduct,
        entity: PoolmanTreatmentEvent,
    ) -> None:
        """Register a treatment event entity for safety tracking.

        Called by each event entity during async_added_to_hass.

        Args:
            product: The chemical product this entity tracks.
            entity: The event entity instance.
        """
        self._treatment_entities[product] = entity

    async def async_add_treatment(
        self,
        product: ChemicalProduct,
        quantity_g: float | None = None,
        notes: str | None = None,
    ) -> None:
        """Record a chemical treatment application.

        Fires the event on the corresponding event entity and triggers
        a coordinator refresh to update derived sensors.

        Args:
            product: The chemical product applied.
            quantity_g: Amount of product used in grams.
            notes: Optional free-text note about the treatment.
        """
        entity = self._treatment_entities.get(product)
        if entity is None:
            _LOGGER.warning("No treatment entity registered for product %s", product)
            return
        entity.apply_treatment(quantity_g=quantity_g, notes=notes)
        await self.async_request_refresh()

    def _read_sensor(self, entity_key: str) -> float | None:
        """Safely read a float value from a HA sensor entity.

        Args:
            entity_key: Config entry data key for the entity ID.

        Returns:
            Float value or None if unavailable/invalid.
        """
        entity_id = self._get_config(entity_key)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug("Cannot parse state '%s' from %s", state.state, entity_id)
            return None

    def _read_outdoor_temperature(self) -> float | None:
        """Read outdoor temperature from a sensor entity or weather entity.

        Tries the dedicated outdoor temperature sensor first,
        then falls back to the temperature attribute of a weather entity.

        Returns:
            Outdoor temperature in Celsius, or None if unavailable.
        """
        # Try dedicated outdoor temperature sensor
        value = self._read_sensor(CONF_OUTDOOR_TEMPERATURE_ENTITY)
        if value is not None:
            return value

        # Fall back to weather entity's temperature attribute
        weather_id = self._get_config(CONF_WEATHER_ENTITY)
        if not weather_id:
            return None

        state = self.hass.states.get(weather_id)
        if state is None:
            return None

        temp = state.attributes.get("temperature")
        if temp is None:
            return None

        try:
            return float(temp)
        except (ValueError, TypeError):
            _LOGGER.debug("Cannot parse temperature attribute '%s' from %s", temp, weather_id)
            return None

    def _read_treatment_entries(
        self, now: datetime
    ) -> list[tuple[ChemicalProduct, datetime, float | None]]:
        """Read treatment data from registered event entities.

        Collects the last application timestamp and quantity from each
        event entity that has been triggered at least once.

        Args:
            now: Current time (unused but available for future filtering).

        Returns:
            List of (product, applied_at, quantity_g) tuples.
        """
        entries: list[tuple[ChemicalProduct, datetime, float | None]] = []
        for product, entity in self._treatment_entities.items():
            state_value = entity.state
            if state_value is None:
                continue
            try:
                applied_at = datetime.fromisoformat(state_value)
            except (ValueError, TypeError):
                _LOGGER.debug("Cannot parse event timestamp '%s' for %s", state_value, product)
                continue

            quantity_g: float | None = None
            attrs = entity.extra_state_attributes
            if attrs and "quantity_g" in attrs:
                with contextlib.suppress(ValueError, TypeError):
                    quantity_g = float(attrs["quantity_g"])

            entries.append((product, applied_at, quantity_g))
        return entries

    async def _async_update_data(self) -> PoolState:
        """Fetch sensor data and compute pool state."""
        reading = PoolReading(
            ph=self._read_sensor(CONF_PH_ENTITY),
            orp=self._read_sensor(CONF_ORP_ENTITY),
            temp_c=self._read_sensor(CONF_TEMPERATURE_ENTITY),
            outdoor_temp_c=self._read_outdoor_temperature(),
            tac=self._read_sensor(CONF_TAC_ENTITY),
            cya=self._read_sensor(CONF_CYA_ENTITY),
            hardness=self._read_sensor(CONF_HARDNESS_ENTITY),
        )

        recommendations = self.engine.evaluate(self.pool, reading, self._mode)
        filtration_hours = compute_filtration_duration(self.pool, reading, self._mode)
        water_quality_score = compute_water_quality_score(reading)
        chemistry_report = compute_chemistry_report(reading)

        # Compute treatment safety state from event entities
        now = utcnow()
        treatment_entries = self._read_treatment_entries(now)
        active_treatments = compute_active_treatments(treatment_entries, now)
        swimming_safe = compute_swimming_safe(active_treatments, now)
        safe_at = compute_safe_at(active_treatments) if not swimming_safe else None

        new_state = PoolState(
            mode=self._mode,
            reading=reading,
            recommendations=recommendations,
            filtration_hours=filtration_hours,
            water_quality_score=water_quality_score,
            chemistry_report=chemistry_report,
            active_treatments=active_treatments,
            swimming_safe=swimming_safe,
            safe_at=safe_at,
        )

        self._fire_status_change_events(new_state)

        return new_state

    def _fire_status_change_events(self, new_state: PoolState) -> None:
        """Fire bus events for any status changes compared to the previous state.

        Compares the new state against the previously stored state
        (``self.data``) and fires a ``poolman_event`` for each detected
        status transition. Skipped on the first update when no previous
        state exists.

        Args:
            new_state: The newly computed pool state.
        """
        previous = self.data
        if previous is None:
            return

        changes = compute_status_changes(previous, new_state)
        if not changes:
            return

        device_id = self._get_device_id()
        for change in changes:
            self.hass.bus.async_fire(
                EVENT_POOLMAN,
                {
                    "device_id": device_id,
                    "type": change.type,
                    "parameter": change.parameter,
                    "previous_status": change.previous_status,
                    "status": change.status,
                },
            )

    def _get_device_id(self) -> str | None:
        """Look up the device registry ID for this pool.

        Returns:
            The device ID string or None if the device is not yet registered.
        """
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, self.config_entry.entry_id)}
        )
        return device.id if device else None

    def get_entity_id(self, key: str) -> str | None:
        """Get configured entity ID for a sensor key.

        Args:
            key: Config entry data key.

        Returns:
            The entity ID string or None.
        """
        value: Any = self._get_config(key)
        return str(value) if value else None
