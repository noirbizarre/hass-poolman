"""The Fake Pool Sensor integration."""

from __future__ import annotations

import logging
import random

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN, PLATFORMS, SENSOR_SPECS

_LOGGER = logging.getLogger(__name__)

type FakePoolSensorConfigEntry = ConfigEntry[FakePoolSensorCoordinator]


class FakePoolSensorCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator that produces fake pool sensor readings with drift."""

    config_entry: FakePoolSensorConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: FakePoolSensorConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )
        # Target values (adjustable via number entities)
        self.targets: dict[str, float] = {spec.key: spec.default for spec in SENSOR_SPECS}
        # Current simulated values
        self.current: dict[str, float] = dict(self.targets)

    async def _async_update_data(self) -> dict[str, float]:
        """Compute new sensor values with drift toward targets."""
        for spec in SENSOR_SPECS:
            target = self.targets[spec.key]
            current = self.current[spec.key]
            # Drift toward target + random noise
            drift = (target - current) * 0.3
            noise = random.gauss(0, spec.noise)
            new_value = current + drift + noise
            # Clamp to valid range
            self.current[spec.key] = max(spec.min_value, min(spec.max_value, round(new_value, 4)))
        return dict(self.current)


async def async_setup_entry(hass: HomeAssistant, entry: FakePoolSensorConfigEntry) -> bool:
    """Set up Fake Pool Sensor from a config entry."""
    coordinator = FakePoolSensorCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FakePoolSensorConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
