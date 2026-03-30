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
    CONF_COMPLETED_AT,
    CONF_CYA_ENTITY,
    CONF_FILTRATION_KIND,
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_PH_ENTITY,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_STEPS,
    CONF_TAC_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    CONF_WEATHER_ENTITY,
    DEFAULT_FILTRATION_DURATION_MODE,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_MIN_DYNAMIC_DURATION_HOURS,
    DEFAULT_TREATMENT,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_FILTRATION_STOPPED,
    EVENT_POOLMAN,
    SUBENTRY_ACTIVATION,
)
from .domain.activation import SHOCK_PRODUCT_VALUES, ActivationChecklist, ActivationStep
from .domain.chemistry import compute_chemistry_report, compute_water_quality_score
from .domain.filtration import compute_filtration_duration
from .domain.model import (
    ChemicalProduct,
    FiltrationDurationMode,
    FiltrationKind,
    ManualMeasure,
    MeasureParameter,
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
    from .event import PoolmanMeasureEvent, PoolmanTreatmentEvent

_LOGGER = logging.getLogger(__name__)

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]

# Mapping from MeasureParameter to the config key for the corresponding sensor entity
_MEASURE_SENSOR_KEY: dict[MeasureParameter, str] = {
    MeasureParameter.PH: CONF_PH_ENTITY,
    MeasureParameter.ORP: CONF_ORP_ENTITY,
    MeasureParameter.TAC: CONF_TAC_ENTITY,
    MeasureParameter.CYA: CONF_CYA_ENTITY,
    MeasureParameter.HARDNESS: CONF_HARDNESS_ENTITY,
    MeasureParameter.TEMPERATURE: CONF_TEMPERATURE_ENTITY,
}


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
        self._mode = PoolMode.ACTIVE
        self._filtration_duration_mode = FiltrationDurationMode(DEFAULT_FILTRATION_DURATION_MODE)
        self._min_dynamic_period_duration = DEFAULT_MIN_DYNAMIC_DURATION_HOURS
        self._treatment_entities: dict[ChemicalProduct, PoolmanTreatmentEvent] = {}
        self._measure_entities: dict[MeasureParameter, PoolmanMeasureEvent] = {}
        self._activation: ActivationChecklist | None = None

        # Filtration scheduler: only created when a pump entity is configured
        pump_entity_id = self._get_config(CONF_PUMP_ENTITY)
        self.scheduler: FiltrationScheduler | None = (
            FiltrationScheduler(hass, pump_entity_id) if pump_entity_id else None
        )

        # Listen for filtration events to auto-confirm activation steps
        if self.scheduler is not None:
            self.scheduler.on_event(self._on_scheduler_event)

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
        """Set the pool mode.

        When switching to ACTIVATING, a new activation checklist is created
        (unless one already exists). When switching away from ACTIVATING,
        the checklist is cleared.

        For mode changes that require side effects (e.g. pausing the
        scheduler), use :meth:`async_set_mode` instead.
        """
        previous = self._mode
        self._mode = value
        if value == PoolMode.ACTIVATING and previous != PoolMode.ACTIVATING:
            self._activation = ActivationChecklist(started_at=utcnow())
        elif value != PoolMode.ACTIVATING:
            self._activation = None

    @property
    def activation(self) -> ActivationChecklist | None:
        """Return the current activation checklist, if any."""
        return self._activation

    @activation.setter
    def activation(self, value: ActivationChecklist | None) -> None:
        """Set or clear the activation checklist (used for state restoration)."""
        self._activation = value

    async def async_set_mode(self, mode: PoolMode) -> None:
        """Set the pool mode with transition side effects.

        Handles scheduler pause/resume when entering or leaving
        ``WINTER_PASSIVE`` mode and activation checklist lifecycle
        when entering or leaving ``ACTIVATING`` mode.

        Args:
            mode: The new pool mode to set.
        """
        old_mode = self._mode
        self._mode = mode

        # Manage activation checklist lifecycle
        if mode == PoolMode.ACTIVATING and old_mode != PoolMode.ACTIVATING:
            self._activation = ActivationChecklist(started_at=utcnow())
        elif mode != PoolMode.ACTIVATING:
            self._activation = None

        if (
            mode == PoolMode.WINTER_PASSIVE
            and old_mode != PoolMode.WINTER_PASSIVE
            and self.scheduler is not None
        ):
            # Entering passive wintering: pause the scheduler
            await self.scheduler.async_pause()
        elif (
            mode != PoolMode.WINTER_PASSIVE
            and old_mode == PoolMode.WINTER_PASSIVE
            and self.scheduler is not None
        ):
            # Leaving passive wintering: resume the scheduler
            await self.scheduler.async_resume()

    @property
    def min_dynamic_period_duration(self) -> float:
        """Return the minimum duration for a dynamically computed period.

        When the recommendation is less than period 1's duration, the
        dynamic period 2 duration will use this floor value.  Defaults
        to 0.0 (effectively skipping period 2).
        """
        return self._min_dynamic_period_duration

    @property
    def filtration_duration_mode(self) -> FiltrationDurationMode:
        """Return the current filtration duration control mode."""
        return self._filtration_duration_mode

    @filtration_duration_mode.setter
    def filtration_duration_mode(self, value: FiltrationDurationMode) -> None:
        """Set the filtration duration control mode and sync scheduler split state."""
        self._filtration_duration_mode = value
        if self.scheduler is not None:
            self.hass.async_create_task(self.scheduler.async_set_split(value.is_split))

    async def async_boost_filtration(self, hours: float) -> None:
        """Activate a filtration boost for the given number of extra hours.

        Delegates to the scheduler.  Has no effect if no pump is configured.

        Args:
            hours: Extra filtration hours to add.
        """
        if self.scheduler is not None:
            await self.scheduler.async_boost(hours)
            await self.async_request_refresh()

    async def async_cancel_boost(self) -> None:
        """Cancel any active filtration boost.

        Delegates to the scheduler.  Has no effect if no pump is configured.
        """
        if self.scheduler is not None:
            await self.scheduler.async_cancel_boost()
            await self.async_request_refresh()

    async def async_confirm_activation_step(self, step: ActivationStep) -> None:
        """Confirm completion of an activation wizard step.

        Updates both the in-memory activation checklist and the persisted
        activation subentry data. When all steps are complete, transitions
        the pool to ACTIVE mode and records the completion timestamp.

        Args:
            step: The activation step to mark as completed.

        Raises:
            ValueError: If the pool is not in activating mode or the step
                has already been confirmed.
        """
        if self._mode != PoolMode.ACTIVATING or self._activation is None:
            msg = "Cannot confirm activation step: pool is not in activating mode"
            raise ValueError(msg)
        self._activation.confirm(step)

        if self._activation.is_complete:
            self._mode = PoolMode.ACTIVE
            self._activation = None
            self._persist_activation_completion()
        else:
            self._persist_activation_steps()

        await self.async_request_refresh()

    def _on_scheduler_event(self, event_type: str, _data: dict[str, object]) -> None:
        """Handle scheduler events to auto-confirm activation steps.

        When a filtration cycle completes (filtration_stopped) during
        activating mode, the intensive_filtration step is auto-confirmed.

        Args:
            event_type: The scheduler event type.
            _data: Event data payload (unused).
        """
        if event_type != EVENT_FILTRATION_STOPPED:
            return
        if self._mode != PoolMode.ACTIVATING or self._activation is None:
            return
        if ActivationStep.INTENSIVE_FILTRATION in self._activation.pending_steps:
            self._activation.confirm(ActivationStep.INTENSIVE_FILTRATION)
            if self._activation.is_complete:
                self._mode = PoolMode.ACTIVE
                self._activation = None
                self._persist_activation_completion()
            else:
                self._persist_activation_steps()
            self.hass.async_create_task(self.async_request_refresh())

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

        When in activating mode, recording a shock product automatically
        confirms the shock_treatment activation step.

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

        # Auto-confirm shock_treatment step during activation
        if (
            self._mode == PoolMode.ACTIVATING
            and self._activation is not None
            and product in SHOCK_PRODUCT_VALUES
            and ActivationStep.SHOCK_TREATMENT in self._activation.pending_steps
        ):
            self._activation.confirm(ActivationStep.SHOCK_TREATMENT)
            if self._activation.is_complete:
                self._mode = PoolMode.ACTIVE
                self._activation = None
                self._persist_activation_completion()
            else:
                self._persist_activation_steps()

        await self.async_request_refresh()

    def _find_activation_subentry(self) -> tuple[Any, Any] | None:
        """Find the in-progress activation subentry.

        Returns:
            Tuple of (config_entry, subentry) or None if not found.
        """
        entry = self.config_entry
        for subentry in entry.subentries.values():
            if (
                subentry.subentry_type == SUBENTRY_ACTIVATION
                and subentry.data.get(CONF_COMPLETED_AT) is None
            ):
                return entry, subentry
        return None

    def _persist_activation_steps(self) -> None:
        """Persist current activation step state to the subentry.

        Updates the subentry data with the current checklist steps.
        Does nothing if no in-progress activation subentry exists.
        """
        if self._activation is None:
            return
        result = self._find_activation_subentry()
        if result is None:
            return
        entry, subentry = result
        steps = {step.value: completed for step, completed in self._activation.steps.items()}
        self.hass.config_entries.async_update_subentry(
            entry,
            subentry,
            data={
                **dict(subentry.data),
                CONF_STEPS: steps,
            },
        )

    def _persist_activation_completion(self) -> None:
        """Mark the activation subentry as completed.

        Sets ``completed_at`` and updates all steps to True.
        Transitions the subentry title to indicate completion.
        Does nothing if no in-progress activation subentry exists.
        """
        result = self._find_activation_subentry()
        if result is None:
            return
        entry, subentry = result
        now = utcnow().isoformat()
        steps = {step.value: True for step in ActivationStep}
        self.hass.config_entries.async_update_subentry(
            entry,
            subentry,
            data={
                **dict(subentry.data),
                CONF_COMPLETED_AT: now,
                CONF_STEPS: steps,
            },
            title="Activation - completed",
        )

    def register_measure_entity(
        self,
        parameter: MeasureParameter,
        entity: PoolmanMeasureEvent,
    ) -> None:
        """Register a measure event entity for manual measurement tracking.

        Called by each measure event entity during async_added_to_hass.

        Args:
            parameter: The pool parameter this entity tracks.
            entity: The measure event entity instance.
        """
        self._measure_entities[parameter] = entity

    async def async_record_measure(
        self,
        parameter: MeasureParameter,
        value: float,
        notes: str | None = None,
    ) -> None:
        """Record a manual measurement.

        Fires the event on the corresponding measure event entity and
        triggers a coordinator refresh to update derived sensors.

        Args:
            parameter: The pool parameter being measured.
            value: The measured value.
            notes: Optional free-text note about the measurement.
        """
        entity = self._measure_entities.get(parameter)
        if entity is None:
            _LOGGER.warning("No measure entity registered for parameter %s", parameter)
            return
        entity.record_measure(value=value, notes=notes)
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

    def _read_with_fallback(
        self,
        sensor_key: str,
        parameter: MeasureParameter,
        manual_measures: dict[MeasureParameter, ManualMeasure],
    ) -> tuple[float | None, str | None]:
        """Read a sensor value with fallback to manual measurement.

        Tries the configured sensor entity first. If unavailable, falls
        back to the last manual measurement for the same parameter.

        Args:
            sensor_key: Config entry key for the sensor entity ID.
            parameter: The corresponding measure parameter.
            manual_measures: Current manual measurements.

        Returns:
            Tuple of (value, source) where source is "sensor", "manual",
            or None if both are unavailable.
        """
        sensor_value = self._read_sensor(sensor_key)
        if sensor_value is not None:
            return sensor_value, "sensor"

        measure = manual_measures.get(parameter)
        if measure is not None:
            return measure.value, "manual"

        return None, None

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
            attrs = entity.state_attributes
            if attrs and "quantity_g" in attrs:
                with contextlib.suppress(ValueError, TypeError):
                    quantity_g = float(attrs["quantity_g"])

            entries.append((product, applied_at, quantity_g))
        return entries

    def _read_measure_entries(self) -> dict[MeasureParameter, ManualMeasure]:
        """Read manual measurement data from registered measure event entities.

        Collects the last measurement value and timestamp from each measure
        event entity that has been triggered at least once.

        Returns:
            Dict mapping parameter to the last recorded ManualMeasure.
        """
        measures: dict[MeasureParameter, ManualMeasure] = {}
        for parameter, entity in self._measure_entities.items():
            state_value = entity.state
            if state_value is None:
                continue
            try:
                measured_at = datetime.fromisoformat(state_value)
            except (ValueError, TypeError):
                _LOGGER.debug("Cannot parse event timestamp '%s' for %s", state_value, parameter)
                continue

            attrs = entity.state_attributes
            if not attrs or "value" not in attrs:
                continue

            try:
                value = float(attrs["value"])
            except (ValueError, TypeError):
                _LOGGER.debug(
                    "Cannot parse measure value '%s' for %s", attrs.get("value"), parameter
                )
                continue

            measures[parameter] = ManualMeasure(
                parameter=parameter,
                value=value,
                measured_at=measured_at,
            )
        return measures

    async def _async_update_data(self) -> PoolState:
        """Fetch sensor data and compute pool state.

        Reads sensor values with fallback to manual measurements when
        sensors are unavailable. Tracks which source provided each value
        in ``reading_sources``.
        """
        # Read manual measures from event entities
        manual_measures = self._read_measure_entries()

        # Read each parameter with sensor-first, manual-fallback strategy
        reading_sources: dict[str, str] = {}

        ph, ph_src = self._read_with_fallback(CONF_PH_ENTITY, MeasureParameter.PH, manual_measures)
        if ph_src:
            reading_sources["ph"] = ph_src

        orp, orp_src = self._read_with_fallback(
            CONF_ORP_ENTITY, MeasureParameter.ORP, manual_measures
        )
        if orp_src:
            reading_sources["orp"] = orp_src

        temp_c, temp_src = self._read_with_fallback(
            CONF_TEMPERATURE_ENTITY, MeasureParameter.TEMPERATURE, manual_measures
        )
        if temp_src:
            reading_sources["temperature"] = temp_src

        # Outdoor temperature has its own fallback chain (sensor -> weather entity)
        # and does not support manual measurement
        outdoor_temp_c = self._read_outdoor_temperature()

        tac, tac_src = self._read_with_fallback(
            CONF_TAC_ENTITY, MeasureParameter.TAC, manual_measures
        )
        if tac_src:
            reading_sources["tac"] = tac_src

        cya, cya_src = self._read_with_fallback(
            CONF_CYA_ENTITY, MeasureParameter.CYA, manual_measures
        )
        if cya_src:
            reading_sources["cya"] = cya_src

        hardness, hardness_src = self._read_with_fallback(
            CONF_HARDNESS_ENTITY, MeasureParameter.HARDNESS, manual_measures
        )
        if hardness_src:
            reading_sources["hardness"] = hardness_src

        reading = PoolReading(
            ph=ph,
            orp=orp,
            temp_c=temp_c,
            outdoor_temp_c=outdoor_temp_c,
            tac=tac,
            cya=cya,
            hardness=hardness,
        )

        # Build sensor-only reading for calibration rule comparison.
        # The CalibrationRule needs to know the raw sensor values to compare
        # against manual measures, even when the effective reading uses
        # manual values as fallback.
        sensor_reading = PoolReading(
            ph=self._read_sensor(CONF_PH_ENTITY),
            orp=self._read_sensor(CONF_ORP_ENTITY),
            temp_c=self._read_sensor(CONF_TEMPERATURE_ENTITY),
            outdoor_temp_c=outdoor_temp_c,
            tac=self._read_sensor(CONF_TAC_ENTITY),
            cya=self._read_sensor(CONF_CYA_ENTITY),
            hardness=self._read_sensor(CONF_HARDNESS_ENTITY),
        )

        recommendations = self.engine.evaluate(
            self.pool, sensor_reading, self._mode, manual_measures=manual_measures
        )
        filtration_hours = compute_filtration_duration(self.pool, reading, self._mode)
        water_quality_score = compute_water_quality_score(reading)
        chemistry_report = compute_chemistry_report(reading)

        # Compute treatment safety state from event entities
        now = utcnow()
        treatment_entries = self._read_treatment_entries(now)
        active_treatments = compute_active_treatments(treatment_entries, now)
        treatment_safe = compute_swimming_safe(active_treatments, now)
        # Swimming is only safe in ACTIVE mode and when no treatment safety period is active
        swimming_safe = self._mode == PoolMode.ACTIVE and treatment_safe
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
            manual_measures=manual_measures,
            reading_sources=reading_sources,
            boost_remaining=(self.scheduler.boost_remaining if self.scheduler is not None else 0.0),
            activation=self._activation,
        )

        self._fire_status_change_events(new_state)

        # Auto-sync scheduler duration in dynamic mode
        if (
            self._filtration_duration_mode == FiltrationDurationMode.DYNAMIC
            and self.scheduler is not None
            and filtration_hours is not None
        ):
            await self.scheduler.async_update_schedule(duration_hours=filtration_hours)

        # Auto-sync period 2 duration in split_dynamic mode
        if (
            self._filtration_duration_mode == FiltrationDurationMode.SPLIT_DYNAMIC
            and self.scheduler is not None
            and filtration_hours is not None
            and len(self.scheduler.periods) > 1
        ):
            period1_duration = self.scheduler.periods[0].duration_hours
            remaining = filtration_hours - period1_duration
            period2_duration = max(self._min_dynamic_period_duration, remaining)
            await self.scheduler.async_update_schedule(
                duration_hours=period2_duration,
                period_index=1,
            )

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
