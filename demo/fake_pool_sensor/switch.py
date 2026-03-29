"""Switch platform for Fake Pool Sensor (pool pump simulator)."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FakePoolSensorConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FakePoolSensorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the fake pool pump switch."""
    async_add_entities([FakePoolPumpSwitch(entry)])


class FakePoolPumpSwitch(SwitchEntity):
    """Simulated pool pump switch for demo and testing.

    A simple on/off switch that represents a pool pump. No actual
    hardware is controlled.
    """

    _attr_has_entity_name = True
    _attr_name = "Pump"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:pump"

    def __init__(self, entry: FakePoolSensorConfigEntry) -> None:
        """Initialize the fake pump switch."""
        self._attr_unique_id = f"{entry.entry_id}_pump"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Fake Pool Sensor",
            model="Simulator",
        )

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the pump on."""
        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.debug("Fake pool pump turned ON")

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the pump off."""
        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.debug("Fake pool pump turned OFF")
