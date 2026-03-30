"""The Pool Manager integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_FILTRATION_KIND,
    CONF_TREATMENT,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_TREATMENT,
    SERVICE_RECORD_MEASURE,
)
from .coordinator import PoolmanCoordinator
from .domain.model import ChemicalProduct, MeasureParameter

_LOGGER = logging.getLogger(__name__)

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]

SERVICE_ADD_TREATMENT_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("product"): vol.In([p.value for p in ChemicalProduct]),
        vol.Optional("quantity_g"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("notes"): str,
    }
)

SERVICE_RECORD_MEASURE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("parameter"): vol.In([p.value for p in MeasureParameter]),
        vol.Required("value"): vol.Coerce(float),
        vol.Optional("notes"): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Set up Pool Manager from a config entry."""
    coordinator = PoolmanCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Unload a config entry."""
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Unregister services if no more config entries remain
    entries = hass.config_entries.async_entries(DOMAIN)
    if not any(e.entry_id != entry.entry_id for e in entries):
        hass.services.async_remove(DOMAIN, SERVICE_ADD_TREATMENT)
        hass.services.async_remove(DOMAIN, SERVICE_RECORD_MEASURE)

    return result


async def _async_update_listener(hass: HomeAssistant, entry: PoolmanConfigEntry) -> None:
    """Handle options update by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Migrate config entry to a newer version.

    Handles migration from v1.1 to v1.2: adds filtration_kind with a default value.
    Handles migration from v1.2 to v1.3: adds treatment with a default value.
    """
    if entry.version == 1 and entry.minor_version < 2:
        new_data = {**entry.data}
        if CONF_FILTRATION_KIND not in new_data:
            new_data[CONF_FILTRATION_KIND] = DEFAULT_FILTRATION_KIND
        hass.config_entries.async_update_entry(entry, data=new_data, minor_version=2)

    if entry.version == 1 and entry.minor_version < 3:
        new_data = {**entry.data}
        if CONF_TREATMENT not in new_data:
            new_data[CONF_TREATMENT] = DEFAULT_TREATMENT
        hass.config_entries.async_update_entry(entry, data=new_data, minor_version=3)

    return True


def _async_register_services(hass: HomeAssistant) -> None:
    """Register Pool Manager services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT):
        return

    async def async_handle_add_treatment(call: ServiceCall) -> None:
        """Handle the add_treatment service call.

        Resolves the target device to find the corresponding coordinator,
        then records the treatment on the appropriate event entity.
        """
        product = ChemicalProduct(call.data["product"])
        quantity_g: float | None = call.data.get("quantity_g")
        notes: str | None = call.data.get("notes")
        device_id: str = call.data["device_id"]

        device_reg = dr.async_get(hass)
        device = device_reg.async_get(device_id)
        if device is None:
            _LOGGER.warning("Device %s not found", device_id)
            return

        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry and entry.domain == DOMAIN:
                coordinator: PoolmanCoordinator = entry.runtime_data
                await coordinator.async_add_treatment(product, quantity_g, notes)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TREATMENT,
        async_handle_add_treatment,
        schema=SERVICE_ADD_TREATMENT_SCHEMA,
    )

    async def async_handle_record_measure(call: ServiceCall) -> None:
        """Handle the record_measure service call.

        Resolves the target device to find the corresponding coordinator,
        then records the manual measurement on the appropriate event entity.
        """
        parameter = MeasureParameter(call.data["parameter"])
        value: float = call.data["value"]
        notes: str | None = call.data.get("notes")
        device_id: str = call.data["device_id"]

        device_reg = dr.async_get(hass)
        device = device_reg.async_get(device_id)
        if device is None:
            _LOGGER.warning("Device %s not found", device_id)
            return

        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry and entry.domain == DOMAIN:
                coordinator: PoolmanCoordinator = entry.runtime_data
                await coordinator.async_record_measure(parameter, value, notes)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_MEASURE,
        async_handle_record_measure,
        schema=SERVICE_RECORD_MEASURE_SCHEMA,
    )
