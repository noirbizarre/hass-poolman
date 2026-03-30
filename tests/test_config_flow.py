"""Tests for the Pool Manager config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_FILTRATION_KIND,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    DOMAIN,
)

POOL_INPUT: dict[str, Any] = {
    CONF_POOL_NAME: "My Pool",
    CONF_VOLUME_M3: 40.0,
    CONF_SHAPE: "round",
}

CHEMISTRY_INPUT: dict[str, Any] = {
    CONF_TREATMENT: "chlorine",
    CONF_PH_ENTITY: "sensor.pool_ph",
    CONF_ORP_ENTITY: "sensor.pool_orp",
}

FILTRATION_INPUT: dict[str, Any] = {
    CONF_FILTRATION_KIND: "sand",
    CONF_PUMP_FLOW_M3H: 10.0,
    CONF_TEMPERATURE_ENTITY: "sensor.pool_temp",
}


class TestConfigFlow:
    """Tests for the initial config flow (user step -> chemistry -> filtration)."""

    async def test_user_step_shows_form(self, hass: HomeAssistant) -> None:
        """First step should show the pool basics form."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_chemistry_step_shows_form(self, hass: HomeAssistant) -> None:
        """After pool step, chemistry form should be shown."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "chemistry"

    async def test_filtration_step_shows_form(self, hass: HomeAssistant) -> None:
        """After chemistry step, filtration form should be shown."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "filtration"

    async def test_full_flow_creates_entry(self, hass: HomeAssistant) -> None:
        """Completing all steps should create a config entry."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)

        with patch("custom_components.poolman.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], FILTRATION_INPUT
            )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Pool"
        assert result["data"][CONF_VOLUME_M3] == 40.0
        assert result["data"][CONF_SHAPE] == "round"
        assert result["data"][CONF_TREATMENT] == "chlorine"
        assert result["data"][CONF_FILTRATION_KIND] == "sand"

    async def test_duplicate_unique_id_aborts(self, hass: HomeAssistant) -> None:
        """Setting up a pool with the same name should abort."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="My Pool",
            data={},
            unique_id="My Pool",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], FILTRATION_INPUT)
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestOptionsFlow:
    """Tests for the options flow (chemistry -> filtration)."""

    async def test_options_flow_init_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Options flow init step should show chemistry form."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_filtration_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """After init step, filtration form should be shown."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], CHEMISTRY_INPUT
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "filtration"

    async def test_options_flow_creates_entry(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Completing options flow should create entry with merged options."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], CHEMISTRY_INPUT
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], FILTRATION_INPUT
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_TREATMENT] == "chlorine"
        assert result["data"][CONF_FILTRATION_KIND] == "sand"
