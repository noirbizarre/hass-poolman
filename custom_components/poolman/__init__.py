"""The Pool Manager integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import PoolmanCoordinator

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Set up Pool Manager from a config entry."""
    coordinator = PoolmanCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
