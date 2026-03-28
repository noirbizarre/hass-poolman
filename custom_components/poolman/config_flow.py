"""Config flow for Pool Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
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
    CONF_HARDNESS_ENTITY,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TAC_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_VOLUME_M3,
    DEFAULT_PUMP_FLOW_M3H,
    DEFAULT_VOLUME_M3,
    DOMAIN,
    SHAPES,
)


class PoolmanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pool Manager."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the pool configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_POOL_NAME])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_POOL_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POOL_NAME, default="My Pool"): str,
                    vol.Required(CONF_VOLUME_M3, default=DEFAULT_VOLUME_M3): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=500,
                            step=0.5,
                            unit_of_measurement="m\u00b3",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(CONF_SHAPE, default="rectangular"): SelectSelector(
                        SelectSelectorConfig(
                            options=SHAPES,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="pool_shape",
                        )
                    ),
                    vol.Required(CONF_PUMP_FLOW_M3H, default=DEFAULT_PUMP_FLOW_M3H): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=50,
                            step=0.5,
                            unit_of_measurement="m\u00b3/h",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(CONF_TEMPERATURE_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PH_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_ORP_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_TAC_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_CYA_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_HARDNESS_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_PUMP_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="switch")
                    ),
                }
            ),
            errors=errors,
        )
