"""Config flow for Pool Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util.dt import utcnow

from .const import (
    ACTIVATION_SOURCE_MODES,
    CONF_COMPLETED_AT,
    CONF_CYA_ENTITY,
    CONF_FILTRATION_KIND,
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_STARTED_AT,
    CONF_STEPS,
    CONF_TAC_ENTITY,
    CONF_TARGET_MODE,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    CONF_WEATHER_ENTITY,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_PUMP_FLOW_M3H,
    DEFAULT_TREATMENT,
    DEFAULT_VOLUME_M3,
    DOMAIN,
    FILTRATION_KINDS,
    HIBERNATION_TARGET_MODES,
    SHAPES,
    SUBENTRY_ACTIVATION,
    SUBENTRY_HIBERNATION,
    TREATMENTS,
)
from .domain.activation import ActivationStep
from .domain.model import PoolMode


def _pool_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the schema for pool basics.

    Args:
        defaults: Optional default values to pre-populate the form.

    Returns:
        A voluptuous schema for the pool step.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_POOL_NAME, default=defaults.get(CONF_POOL_NAME, "My Pool")): str,
            vol.Required(
                CONF_VOLUME_M3, default=defaults.get(CONF_VOLUME_M3, DEFAULT_VOLUME_M3)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=500,
                    step=0.5,
                    unit_of_measurement="m\u00b3",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SHAPE, default=defaults.get(CONF_SHAPE, "rectangular")
            ): SelectSelector(
                SelectSelectorConfig(
                    options=SHAPES,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="pool_shape",
                )
            ),
        }
    )


def _chemistry_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the schema for chemistry settings and sensors.

    Args:
        defaults: Optional default values to pre-populate the form.

    Returns:
        A voluptuous schema for the chemistry step.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_TREATMENT,
                default=defaults.get(CONF_TREATMENT, DEFAULT_TREATMENT),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=TREATMENTS,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="treatment_type",
                )
            ),
            vol.Required(
                CONF_PH_ENTITY,
                default=defaults.get(CONF_PH_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_ORP_ENTITY,
                default=defaults.get(CONF_ORP_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_TAC_ENTITY,
                default=defaults.get(CONF_TAC_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_CYA_ENTITY,
                default=defaults.get(CONF_CYA_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_HARDNESS_ENTITY,
                default=defaults.get(CONF_HARDNESS_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
        }
    )


def _filtration_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the schema for filtration settings.

    Args:
        defaults: Optional default values to pre-populate the form.

    Returns:
        A voluptuous schema for the filtration step.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_FILTRATION_KIND,
                default=defaults.get(CONF_FILTRATION_KIND, DEFAULT_FILTRATION_KIND),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=FILTRATION_KINDS,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="filtration_kind",
                )
            ),
            vol.Required(
                CONF_PUMP_FLOW_M3H,
                default=defaults.get(CONF_PUMP_FLOW_M3H, DEFAULT_PUMP_FLOW_M3H),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=50,
                    step=0.5,
                    unit_of_measurement="m\u00b3/h",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_TEMPERATURE_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_PUMP_ENTITY,
                default=defaults.get(CONF_PUMP_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="switch")),
            vol.Optional(
                CONF_OUTDOOR_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_WEATHER_ENTITY,
                default=defaults.get(CONF_WEATHER_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="weather")),
        }
    )


class PoolmanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pool Manager."""

    VERSION = 1
    MINOR_VERSION = 3

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow handler."""
        return PoolmanOptionsFlowHandler(config_entry)

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentry types supported for this config entry."""
        return {
            SUBENTRY_HIBERNATION: HibernationSubentryFlowHandler,
            SUBENTRY_ACTIVATION: ActivationSubentryFlowHandler,
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the pool configuration step (pool basics)."""
        if user_input is not None:
            self._user_input = user_input
            return await self.async_step_chemistry()

        return self.async_show_form(
            step_id="user",
            data_schema=_pool_schema(),
        )

    async def async_step_chemistry(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the chemistry configuration step (treatment + sensors)."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_filtration()

        return self.async_show_form(
            step_id="chemistry",
            data_schema=_chemistry_schema(),
        )

    async def async_step_filtration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the filtration configuration step."""
        if user_input is not None:
            merged = {**self._user_input, **user_input}

            await self.async_set_unique_id(merged[CONF_POOL_NAME])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=merged[CONF_POOL_NAME],
                data=merged,
            )

        return self.async_show_form(
            step_id="filtration",
            data_schema=_filtration_schema(),
        )


class PoolmanOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle options flow for Pool Manager."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow handler."""
        super().__init__(config_entry)
        self._options: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the options flow init step (chemistry settings)."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_filtration()

        # Pre-populate with current values from options (fallback to data)
        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=_chemistry_schema(defaults=current),
        )

    async def async_step_filtration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the filtration options step."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(data=self._options)

        # Pre-populate with current values from options (fallback to data)
        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="filtration",
            data_schema=_filtration_schema(defaults=current),
        )


def _hibernation_type_schema() -> vol.Schema:
    """Build the schema for hibernation type selection.

    Returns:
        A voluptuous schema for the hibernation wizard user step.
    """
    return vol.Schema(
        {
            vol.Required(CONF_TARGET_MODE): SelectSelector(
                SelectSelectorConfig(
                    options=HIBERNATION_TARGET_MODES,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="hibernation_target_mode",
                )
            ),
        }
    )


def _hibernation_confirm_schema() -> vol.Schema:
    """Build the schema for hibernation completion confirmation.

    Returns:
        A voluptuous schema for the hibernation wizard reconfigure step.
    """
    return vol.Schema(
        {
            vol.Required("confirm", default=False): BooleanSelector(),
        }
    )


class HibernationSubentryFlowHandler(ConfigSubentryFlow):
    """Handle the hibernation wizard subentry flow.

    Session 1 (user): choose target winter mode, create subentry,
    set pool to HIBERNATING.

    Session 2 (reconfigure): confirm winterizing actions completed,
    transition to target winter mode, record completion timestamp.
    """

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle step 1: choose the target winter mode.

        Guards against starting a new hibernation when the pool is
        already in a winter or hibernating mode, or when an
        uncompleted hibernation subentry exists.

        Args:
            user_input: Form data submitted by the user, or None
                to display the form.

        Returns:
            The next flow step result.
        """
        entry = self._get_entry()
        coordinator = entry.runtime_data

        # Guard: pool already in a winter or hibernating mode
        if coordinator.mode in (
            PoolMode.HIBERNATING,
            PoolMode.WINTER_ACTIVE,
            PoolMode.WINTER_PASSIVE,
        ):
            return self.async_abort(reason="already_wintering")

        # Guard: an in-progress hibernation subentry already exists
        for subentry in entry.subentries.values():
            if (
                subentry.subentry_type == SUBENTRY_HIBERNATION
                and subentry.data.get(CONF_COMPLETED_AT) is None
            ):
                return self.async_abort(reason="hibernation_in_progress")

        if user_input is not None:
            target_mode = user_input[CONF_TARGET_MODE]
            now = utcnow().isoformat()

            # Transition to HIBERNATING mode
            await coordinator.async_set_mode(PoolMode.HIBERNATING)
            await coordinator.async_request_refresh()

            target_label = PoolMode(target_mode).value
            return self.async_create_entry(
                title=f"Hibernation ({target_label})",
                data={
                    CONF_TARGET_MODE: target_mode,
                    CONF_STARTED_AT: now,
                    CONF_COMPLETED_AT: None,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_hibernation_type_schema(),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle step 2: confirm winterizing actions and complete hibernation.

        Displays the list of recommended winterizing actions and asks
        the user to confirm completion. On confirmation, transitions the
        pool to the chosen winter mode and records the completion timestamp.

        Args:
            user_input: Form data submitted by the user, or None
                to display the form.

        Returns:
            The next flow step result.
        """
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()

        # Already completed: nothing to do
        if subentry.data.get(CONF_COMPLETED_AT) is not None:
            return self.async_abort(reason="already_completed")

        if user_input is not None:
            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=_hibernation_confirm_schema(),
                    errors={"confirm": "must_confirm"},
                )

            target_mode = subentry.data[CONF_TARGET_MODE]
            now = utcnow().isoformat()

            # Transition to target winter mode
            coordinator = entry.runtime_data
            await coordinator.async_set_mode(PoolMode(target_mode))
            await coordinator.async_request_refresh()

            target_label = PoolMode(target_mode).value
            return self.async_update_and_abort(
                entry,
                subentry,
                data={
                    **dict(subentry.data),
                    CONF_COMPLETED_AT: now,
                },
                title=f"Hibernation ({target_label}) - completed",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_hibernation_confirm_schema(),
        )


def _activation_confirm_schema() -> vol.Schema:
    """Build the schema for activation completion confirmation.

    Returns:
        A voluptuous schema for the activation wizard reconfigure step.
    """
    return vol.Schema(
        {
            vol.Required("confirm", default=False): BooleanSelector(),
        }
    )


class ActivationSubentryFlowHandler(ConfigSubentryFlow):
    """Handle the activation wizard subentry flow.

    Session 1 (user): start the activation process from a winter or
    hibernating mode. Creates a subentry with all activation steps
    set to incomplete, and transitions the pool to ACTIVATING.

    Session 2 (reconfigure): view activation progress or confirm
    completion when all steps are done.

    Step confirmations happen outside this flow via the
    ``confirm_activation_step`` service and auto-detection events.
    """

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle step 1: start the activation process.

        Guards against starting activation from an inappropriate mode
        or when an uncompleted activation subentry already exists.

        Args:
            user_input: Form data submitted by the user, or None
                to display the form.

        Returns:
            The next flow step result.
        """
        entry = self._get_entry()
        coordinator = entry.runtime_data

        # Guard: pool must be in a winter or hibernating mode to start activation
        if coordinator.mode.value not in ACTIVATION_SOURCE_MODES:
            return self.async_abort(reason="not_wintering")

        # Guard: an in-progress activation subentry already exists
        for subentry in entry.subentries.values():
            if (
                subentry.subentry_type == SUBENTRY_ACTIVATION
                and subentry.data.get(CONF_COMPLETED_AT) is None
            ):
                return self.async_abort(reason="activation_in_progress")

        if user_input is not None:
            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="user",
                    data_schema=_activation_confirm_schema(),
                    errors={"confirm": "must_confirm"},
                )

            now = utcnow().isoformat()

            # Build initial steps dict (all False)
            steps = {step.value: False for step in ActivationStep}

            # Transition to ACTIVATING mode
            await coordinator.async_set_mode(PoolMode.ACTIVATING)
            await coordinator.async_request_refresh()

            return self.async_create_entry(
                title="Activation",
                data={
                    CONF_STARTED_AT: now,
                    CONF_COMPLETED_AT: None,
                    CONF_STEPS: steps,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_activation_confirm_schema(),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle step 2: view activation progress.

        Shows the current activation progress. If all steps are
        already completed, the user can finalize the activation here.

        Args:
            user_input: Form data submitted by the user, or None
                to display the form.

        Returns:
            The next flow step result.
        """
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()

        # Already completed: nothing to do
        if subentry.data.get(CONF_COMPLETED_AT) is not None:
            return self.async_abort(reason="already_completed")

        # Check if all steps are done
        steps = subentry.data.get(CONF_STEPS, {})
        all_done = all(steps.values()) and len(steps) > 0

        if not all_done:
            return self.async_abort(reason="activation_incomplete")

        # All steps done - show confirmation to finalize
        if user_input is not None:
            now = utcnow().isoformat()

            # Transition to ACTIVE mode
            coordinator = entry.runtime_data
            await coordinator.async_set_mode(PoolMode.ACTIVE)
            await coordinator.async_request_refresh()

            return self.async_update_and_abort(
                entry,
                subentry,
                data={
                    **dict(subentry.data),
                    CONF_COMPLETED_AT: now,
                },
                title="Activation - completed",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({}),
        )
