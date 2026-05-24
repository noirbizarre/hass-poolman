"""The Pool Manager integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_COMPLETED_AT,
    CONF_FILTRATION_KIND,
    CONF_SPOON_SIZES,
    CONF_STARTED_AT,
    CONF_STEPS,
    CONF_TREATMENT,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_TREATMENT,
    DOMAIN,
    INVENTORY_UNITS,
    PLATFORMS,
    SERVICE_ADD_TREATMENT,
    SERVICE_BOOST_FILTRATION,
    SERVICE_CONFIRM_ACTIVATION_STEP,
    SERVICE_INVENTORY_ADD_PRODUCT,
    SERVICE_INVENTORY_ADD_STOCK,
    SERVICE_INVENTORY_REMOVE_PRODUCT,
    SERVICE_INVENTORY_SET_STOCK,
    SERVICE_RECORD_MEASURE,
    SUBENTRY_ACTIVATION,
    SUBENTRY_HIBERNATION,
)
from .coordinator import PoolmanCoordinator
from .domain.activation import ActivationChecklist, ActivationStep
from .domain.inventory import Product
from .domain.model import PRODUCT_DENSITY_G_PER_ML, ChemicalProduct, MeasureParameter, PoolMode

_LOGGER = logging.getLogger(__name__)

type PoolmanConfigEntry = ConfigEntry[PoolmanCoordinator]

SERVICE_ADD_TREATMENT_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("product"): vol.In([p.value for p in ChemicalProduct]),
        vol.Optional("quantity_g"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("spoons"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("spoon_name"): str,
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

SERVICE_BOOST_FILTRATION_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("hours"): vol.All(vol.Coerce(float), vol.Range(min=0, max=48)),
    }
)

SERVICE_CONFIRM_ACTIVATION_STEP_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("step"): vol.In([s.value for s in ActivationStep]),
    }
)

SERVICE_INVENTORY_ADD_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required("product_id"): vol.All(str, vol.Length(min=1)),
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Required("unit"): vol.In(INVENTORY_UNITS),
        vol.Optional("chemical"): vol.In([p.value for p in ChemicalProduct]),
        vol.Optional("initial_quantity"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("low_stock_threshold"): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)

SERVICE_INVENTORY_REMOVE_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required("product_id"): vol.All(str, vol.Length(min=1)),
    }
)

SERVICE_INVENTORY_ADD_STOCK_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required("product_id"): vol.All(str, vol.Length(min=1)),
        vol.Required("quantity"): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)

SERVICE_INVENTORY_SET_STOCK_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required("product_id"): vol.All(str, vol.Length(min=1)),
        vol.Required("quantity"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("low_stock_threshold"): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Set up Pool Manager from a config entry."""
    coordinator = PoolmanCoordinator(hass, entry)

    # Restore HIBERNATING mode from any in-progress hibernation subentry
    for subentry in entry.subentries.values():
        if (
            subentry.subentry_type == SUBENTRY_HIBERNATION
            and subentry.data.get(CONF_COMPLETED_AT) is None
        ):
            await coordinator.async_set_mode(PoolMode.HIBERNATING)
            break

    # Restore ACTIVATING mode and checklist from any in-progress activation subentry
    for subentry in entry.subentries.values():
        if (
            subentry.subentry_type == SUBENTRY_ACTIVATION
            and subentry.data.get(CONF_COMPLETED_AT) is None
        ):
            await coordinator.async_set_mode(PoolMode.ACTIVATING)
            # Rebuild checklist from persisted step data
            steps_data = subentry.data.get(CONF_STEPS, {})
            started_at_raw = subentry.data.get(CONF_STARTED_AT)
            if started_at_raw is not None and coordinator.activation is not None:
                from datetime import datetime

                try:
                    started_at = datetime.fromisoformat(started_at_raw)
                except (ValueError, TypeError):
                    break
                steps = dict.fromkeys(ActivationStep, False)
                for step_value, completed in steps_data.items():
                    try:
                        step = ActivationStep(step_value)
                        steps[step] = bool(completed)
                    except ValueError:
                        continue
                coordinator.activation = ActivationChecklist(
                    started_at=started_at,
                    steps=steps,
                )
            break

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
        hass.services.async_remove(DOMAIN, SERVICE_BOOST_FILTRATION)
        hass.services.async_remove(DOMAIN, SERVICE_CONFIRM_ACTIVATION_STEP)
        hass.services.async_remove(DOMAIN, SERVICE_INVENTORY_ADD_PRODUCT)
        hass.services.async_remove(DOMAIN, SERVICE_INVENTORY_REMOVE_PRODUCT)
        hass.services.async_remove(DOMAIN, SERVICE_INVENTORY_ADD_STOCK)
        hass.services.async_remove(DOMAIN, SERVICE_INVENTORY_SET_STOCK)

    return result


async def _async_update_listener(hass: HomeAssistant, entry: PoolmanConfigEntry) -> None:
    """Handle options update by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Migrate config entry to a newer version.

    Handles migration from v1.1 to v1.2: adds filtration_kind with a default value.
    Handles migration from v1.2 to v1.3: adds treatment with a default value.
    Handles migration from v1.3 to v1.4: adds spoon_sizes with an empty default.
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

    if entry.version == 1 and entry.minor_version < 4:
        new_data = {**entry.data}
        if CONF_SPOON_SIZES not in new_data:
            new_data[CONF_SPOON_SIZES] = []
        hass.config_entries.async_update_entry(entry, data=new_data, minor_version=4)

    return True


def _resolve_spoon_quantity(
    coordinator: PoolmanCoordinator,
    product: ChemicalProduct,
    spoons: float,
    spoon_name: str,
) -> float | None:
    """Convert a spoon-based quantity to grams.

    Looks up the named spoon in the coordinator's pool configuration,
    computes the volume in mL, then converts to grams using the product's
    bulk density.

    Args:
        coordinator: The pool coordinator with pool configuration.
        product: Chemical product being applied.
        spoons: Number of spoons.
        spoon_name: Name of the spoon size to use.

    Returns:
        Quantity in grams, or ``None`` if the spoon name is not found
        or the product has no known density.
    """
    pool = coordinator.pool
    matching = [s for s in pool.spoon_sizes if s.name == spoon_name]
    if not matching:
        _LOGGER.warning("Spoon name '%s' not found in pool configuration", spoon_name)
        return None

    spoon = matching[0]
    density = PRODUCT_DENSITY_G_PER_ML.get(product)
    if density is None or density <= 0:
        _LOGGER.warning("No density defined for product %s", product)
        return None

    volume_ml = spoons * spoon.size_ml
    return volume_ml * density


def _async_register_services(hass: HomeAssistant) -> None:
    """Register Pool Manager services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_ADD_TREATMENT):
        return

    async def async_handle_add_treatment(call: ServiceCall) -> None:
        """Handle the add_treatment service call.

        Resolves the target device to find the corresponding coordinator,
        then records the treatment on the appropriate event entity.

        When ``spoons`` and ``spoon_name`` are provided instead of
        ``quantity_g``, the spoon count is converted to grams using the
        configured spoon volume and the product's bulk density.
        """
        product = ChemicalProduct(call.data["product"])
        quantity_g: float | None = call.data.get("quantity_g")
        spoons: float | None = call.data.get("spoons")
        spoon_name: str | None = call.data.get("spoon_name")
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

                # Resolve spoon-based input to quantity_g
                if quantity_g is None and spoons is not None and spoon_name is not None:
                    quantity_g = _resolve_spoon_quantity(coordinator, product, spoons, spoon_name)

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

    async def async_handle_boost_filtration(call: ServiceCall) -> None:
        """Handle the boost_filtration service call.

        Resolves the target device to find the corresponding coordinator,
        then activates or cancels a filtration boost.
        """
        hours: float = call.data["hours"]
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
                if hours <= 0:
                    await coordinator.async_cancel_boost()
                else:
                    await coordinator.async_boost_filtration(hours)

    hass.services.async_register(
        DOMAIN,
        SERVICE_BOOST_FILTRATION,
        async_handle_boost_filtration,
        schema=SERVICE_BOOST_FILTRATION_SCHEMA,
    )

    async def async_handle_confirm_activation_step(call: ServiceCall) -> None:
        """Handle the confirm_activation_step service call.

        Resolves the target device to find the corresponding coordinator,
        then confirms the specified activation step.
        """
        step = ActivationStep(call.data["step"])
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
                await coordinator.async_confirm_activation_step(step)

    hass.services.async_register(
        DOMAIN,
        SERVICE_CONFIRM_ACTIVATION_STEP,
        async_handle_confirm_activation_step,
        schema=SERVICE_CONFIRM_ACTIVATION_STEP_SCHEMA,
    )

    def _resolve_coordinator(entry_id: str) -> PoolmanCoordinator:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(f"Unknown Pool Manager config entry: {entry_id}")
        return entry.runtime_data

    async def async_handle_inventory_add_product(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(call.data["entry_id"])
        chemical_raw: str | None = call.data.get("chemical")
        product = Product(
            id=call.data["product_id"],
            name=call.data["name"],
            unit=call.data["unit"],
            chemical=ChemicalProduct(chemical_raw) if chemical_raw else None,
        )
        await coordinator.async_inventory_add_product(
            product,
            initial_quantity=call.data.get("initial_quantity"),
            low_stock_threshold=call.data.get("low_stock_threshold"),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_INVENTORY_ADD_PRODUCT,
        async_handle_inventory_add_product,
        schema=SERVICE_INVENTORY_ADD_PRODUCT_SCHEMA,
    )

    async def async_handle_inventory_remove_product(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(call.data["entry_id"])
        await coordinator.async_inventory_remove_product(call.data["product_id"])

    hass.services.async_register(
        DOMAIN,
        SERVICE_INVENTORY_REMOVE_PRODUCT,
        async_handle_inventory_remove_product,
        schema=SERVICE_INVENTORY_REMOVE_PRODUCT_SCHEMA,
    )

    async def async_handle_inventory_add_stock(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(call.data["entry_id"])
        product_id = call.data["product_id"]
        try:
            await coordinator.async_inventory_add_stock(product_id, call.data["quantity"])
        except KeyError as exc:
            raise ServiceValidationError(f"Unknown inventory product: {product_id}") from exc

    hass.services.async_register(
        DOMAIN,
        SERVICE_INVENTORY_ADD_STOCK,
        async_handle_inventory_add_stock,
        schema=SERVICE_INVENTORY_ADD_STOCK_SCHEMA,
    )

    async def async_handle_inventory_set_stock(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(call.data["entry_id"])
        product_id = call.data["product_id"]
        try:
            await coordinator.async_inventory_set_stock(
                product_id,
                call.data["quantity"],
                low_stock_threshold=call.data.get("low_stock_threshold"),
            )
        except KeyError as exc:
            raise ServiceValidationError(f"Unknown inventory product: {product_id}") from exc

    hass.services.async_register(
        DOMAIN,
        SERVICE_INVENTORY_SET_STOCK,
        async_handle_inventory_set_stock,
        schema=SERVICE_INVENTORY_SET_STOCK_SCHEMA,
    )
