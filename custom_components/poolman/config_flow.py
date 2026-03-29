"""Config flow for Pool Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_CYA_ENTITY,
    CONF_FILTRATION_KIND,
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TAC_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    DEFAULT_FILTRATION_KIND,
    DEFAULT_PUMP_FLOW_M3H,
    DEFAULT_TREATMENT,
    DEFAULT_VOLUME_M3,
    DOMAIN,
    FILTRATION_KINDS,
    SHAPES,
    TREATMENTS,
)


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
