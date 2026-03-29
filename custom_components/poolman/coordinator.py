"""DataUpdateCoordinator for Pool Manager."""

from __future__ import annotations

import logging

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CYA_ENTITY,
    CONF_FILTRATION_KIND,
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TAC_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from .domain.chemistry import compute_water_quality_score
from .domain.filtration import compute_filtration_duration
from .domain.model import (
    FiltrationKind,
    Pool,
    PoolMode,
    PoolReading,
    PoolShape,
    PoolState,
    TreatmentType,
)
from .domain.rules import RuleEngine

_LOGGER = logging.getLogger(__name__)

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]


class PoolmanCoordinator(DataUpdateCoordinator[PoolState]):
    """Coordinator to manage pool data updates.

    Reads sensor states from Home Assistant, builds a PoolReading,
    runs the rule engine, and produces a PoolState consumed by all entities.
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

    async def _async_update_data(self) -> PoolState:
        """Fetch sensor data and compute pool state."""
        reading = PoolReading(
            ph=self._read_sensor(CONF_PH_ENTITY),
            orp=self._read_sensor(CONF_ORP_ENTITY),
            temp_c=self._read_sensor(CONF_TEMPERATURE_ENTITY),
            tac=self._read_sensor(CONF_TAC_ENTITY),
            cya=self._read_sensor(CONF_CYA_ENTITY),
            hardness=self._read_sensor(CONF_HARDNESS_ENTITY),
        )

        recommendations = self.engine.evaluate(self.pool, reading, self._mode)
        filtration_hours = compute_filtration_duration(self.pool, reading, self._mode)
        water_quality_score = compute_water_quality_score(reading)

        return PoolState(
            mode=self._mode,
            reading=reading,
            recommendations=recommendations,
            filtration_hours=filtration_hours,
            water_quality_score=water_quality_score,
        )

    def get_entity_id(self, key: str) -> str | None:
        """Get configured entity ID for a sensor key.

        Args:
            key: Config entry data key.

        Returns:
            The entity ID string or None.
        """
        value: Any = self._get_config(key)
        return str(value) if value else None
