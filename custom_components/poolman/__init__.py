"""The Pool Manager integration."""

from __future__ import annotations

import json
import logging

from datetime import UTC, datetime
from pathlib import Path

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
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
    EVENT_POOLMAN_ACTION_RECORDED,
    FRONTEND_DIR,
    FRONTEND_FILENAME,
    FRONTEND_URL_PATH,
    INVENTORY_UNITS,
    PLATFORMS,
    SERVICE_ADD_TREATMENT,
    SERVICE_ANALYZE,
    SERVICE_APPLY_RECOMMENDATION,
    SERVICE_BOOST_FILTRATION,
    SERVICE_CONFIRM_ACTIVATION_STEP,
    SERVICE_INVENTORY_ADD_PRODUCT,
    SERVICE_INVENTORY_ADD_STOCK,
    SERVICE_INVENTORY_REMOVE_PRODUCT,
    SERVICE_INVENTORY_SET_STOCK,
    SERVICE_RECORD_ACTION,
    SERVICE_RECORD_MEASURE,
    SUBENTRY_ACTIVATION,
    SUBENTRY_HIBERNATION,
)
from .coordinator import PoolmanCoordinator
from .domain.action import Action, ActionSource, ActionType
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

SERVICE_APPLY_RECOMMENDATION_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("recommendation_id"): vol.All(str, vol.Length(min=1)),
    }
)

SERVICE_RECORD_ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("type"): vol.In([t.value for t in ActionType]),
        vol.Optional("product_id"): vol.All(str, vol.Length(min=1)),
        vol.Optional("quantity"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("unit"): vol.All(str, vol.Length(min=1)),
        vol.Optional("note"): str,
    }
)

SERVICE_ANALYZE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
    }
)


_FRONTEND_REGISTERED_KEY = "frontend_registered"


def _integration_version() -> str:
    """Return the integration version from manifest.json for cache busting."""
    try:
        manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
        return str(manifest.get("version", "0"))
    except (OSError, ValueError):  # pragma: no cover - defensive
        return "0"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the pool overview Lovelace card as a frontend resource.

    Serves the bundled JS file from the integration package and adds it to
    the Lovelace extra JS URL list so the custom card type is available on
    every dashboard without manual resource setup.

    Idempotent: only the first call per HA instance performs the work.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_FRONTEND_REGISTERED_KEY):
        return

    bundle = Path(__file__).parent / FRONTEND_DIR / FRONTEND_FILENAME
    if not bundle.is_file():
        _LOGGER.warning(
            "Pool overview card bundle missing at %s; the custom card will not be available",
            bundle,
        )
        return

    http = getattr(hass, "http", None)
    if http is None or not hasattr(http, "async_register_static_paths"):
        # http component is not (yet) available — typically only in unit tests.
        _LOGGER.debug("HTTP component unavailable; skipping pool overview card registration")
        return

    await http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL_PATH, str(bundle), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL_PATH}?v={_integration_version()}")
    domain_data[_FRONTEND_REGISTERED_KEY] = True


async def async_setup_entry(hass: HomeAssistant, entry: PoolmanConfigEntry) -> bool:
    """Set up Pool Manager from a config entry."""
    await _async_register_frontend(hass)
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
        hass.services.async_remove(DOMAIN, SERVICE_APPLY_RECOMMENDATION)
        hass.services.async_remove(DOMAIN, SERVICE_RECORD_ACTION)
        hass.services.async_remove(DOMAIN, SERVICE_ANALYZE)

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

    def _resolve_device_coordinator(device_id: str) -> PoolmanCoordinator:
        """Resolve the Pool Manager coordinator owning the given device.

        Raises:
            ServiceValidationError: If the device id is unknown or does not
                belong to a Pool Manager config entry.
        """
        device_reg = dr.async_get(hass)
        device = device_reg.async_get(device_id)
        if device is None:
            raise ServiceValidationError(f"Unknown device: {device_id}")
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry and entry.domain == DOMAIN:
                return entry.runtime_data
        raise ServiceValidationError(
            f"Device {device_id} is not a Pool Manager device",
        )

    def _fire_action_recorded(device_id: str, action: Action) -> None:
        """Fire the ``poolman_action_recorded`` event for ``action``."""
        hass.bus.async_fire(
            EVENT_POOLMAN_ACTION_RECORDED,
            {
                "device_id": device_id,
                "action_id": action.id,
                "type": action.type.value,
                "source": action.source.value,
                "recommendation_id": action.recommendation_id,
                "product_id": action.product_id,
                "quantity": action.quantity,
                "unit": action.unit,
            },
        )

    async def async_handle_apply_recommendation(call: ServiceCall) -> None:
        """Handle the ``apply_recommendation`` service call.

        Resolves the recommendation by id in the current
        :class:`AnalysisResult` and records one :class:`Action` per
        :class:`Treatment` step (or a single placeholder action when the
        recommendation has no treatments).  Each recorded action triggers
        inventory decrement (#94) and fires
        :data:`EVENT_POOLMAN_ACTION_RECORDED`.
        """
        device_id: str = call.data["device_id"]
        recommendation_id: str = call.data["recommendation_id"]
        coordinator = _resolve_device_coordinator(device_id)

        result = coordinator.analysis_result
        if result is None:
            raise ServiceValidationError(
                "No pool analysis is available yet. Wait for the first refresh.",
            )

        rec = next(
            (r for r in result.recommendations if r.id == recommendation_id),
            None,
        )
        if rec is None:
            known = ", ".join(r.id for r in result.recommendations) or "(none)"
            raise ServiceValidationError(
                f"Unknown recommendation_id {recommendation_id!r}. Known: {known}",
            )

        now = datetime.now(UTC)
        ts_token = now.strftime("%Y%m%dT%H%M%S%f")
        if rec.treatments:
            actions = [
                Action(
                    id=f"act_{ts_token}_{rec.id}_{idx}",
                    type=ActionType.CHEMICAL,
                    source=ActionSource.RECOMMENDATION,
                    treatment_id=treatment.id,
                    quantity=treatment.quantity,
                    unit=treatment.unit,
                    timestamp=now,
                    recommendation_id=rec.id,
                    product_id=treatment.product_id,
                    duration=treatment.duration,
                )
                for idx, treatment in enumerate(rec.treatments)
            ]
        else:
            actions = [
                Action(
                    id=f"act_{ts_token}_{rec.id}",
                    type=ActionType.MAINTENANCE,
                    source=ActionSource.RECOMMENDATION,
                    treatment_id="",
                    quantity=0.0,
                    unit="min",
                    timestamp=now,
                    recommendation_id=rec.id,
                )
            ]

        for action in actions:
            try:
                await coordinator.async_record_action(action)
            except ValueError as exc:
                raise ServiceValidationError(str(exc)) from exc
            _fire_action_recorded(device_id, action)

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_RECOMMENDATION,
        async_handle_apply_recommendation,
        schema=SERVICE_APPLY_RECOMMENDATION_SCHEMA,
    )

    async def async_handle_record_action(call: ServiceCall) -> None:
        """Handle the ``record_action`` service call.

        Records a user-initiated :class:`Action` (treatment, cleaning, or
        maintenance).  When ``product_id`` is provided, both ``quantity``
        and ``unit`` are required so that inventory decrement (#94) can be
        applied unambiguously.  Fires :data:`EVENT_POOLMAN_ACTION_RECORDED`.
        """
        device_id: str = call.data["device_id"]
        coordinator = _resolve_device_coordinator(device_id)

        product_id: str | None = call.data.get("product_id")
        quantity: float | None = call.data.get("quantity")
        unit: str | None = call.data.get("unit")
        note: str | None = call.data.get("note")

        if product_id is not None and (quantity is None or unit is None):
            raise ServiceValidationError(
                "quantity and unit are required when product_id is set",
            )

        now = datetime.now(UTC)
        ts_token = now.strftime("%Y%m%dT%H%M%S%f")
        action = Action(
            id=f"act_{ts_token}_manual",
            type=ActionType(call.data["type"]),
            source=ActionSource.USER,
            treatment_id=f"manual_{ts_token}",
            quantity=quantity if quantity is not None else 0.0,
            unit=unit if unit is not None else "min",
            timestamp=now,
            product_id=product_id,
        )

        if note:
            # Action has no notes field today (#19); log it so context isn't
            # silently lost. A future PR may extend Action.
            _LOGGER.debug("record_action note for %s: %s", action.id, note)

        try:
            await coordinator.async_record_action(action)
        except ValueError as exc:
            raise ServiceValidationError(str(exc)) from exc
        _fire_action_recorded(device_id, action)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_ACTION,
        async_handle_record_action,
        schema=SERVICE_RECORD_ACTION_SCHEMA,
    )

    async def async_handle_analyze(call: ServiceCall) -> None:
        """Handle the ``analyze`` service call.

        Triggers an immediate, non-debounced coordinator refresh, which
        re-runs :func:`analyze_pool` (#97) and pushes the updated
        :class:`AnalysisResult` to all listening entities (#98, #99, #102).
        """
        coordinator = _resolve_device_coordinator(call.data["device_id"])
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_ANALYZE,
        async_handle_analyze,
        schema=SERVICE_ANALYZE_SCHEMA,
    )
