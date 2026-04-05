"""Shared test fixtures for Pool Manager tests."""

from __future__ import annotations

from typing import Any

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_FILTRATION_KIND,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_ENTITY,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    DOMAIN,
)
from custom_components.poolman.domain.model import Pool, PoolReading, PoolShape

MOCK_CONFIG_DATA: dict[str, Any] = {
    CONF_POOL_NAME: "Test Pool",
    CONF_VOLUME_M3: 50.0,
    CONF_SHAPE: "rectangular",
    CONF_TREATMENT: "chlorine",
    CONF_FILTRATION_KIND: "sand",
    CONF_PUMP_FLOW_M3H: 10.0,
    CONF_PH_ENTITY: "sensor.pool_ph",
    CONF_ORP_ENTITY: "sensor.pool_orp",
    CONF_TEMPERATURE_ENTITY: "sensor.pool_temperature",
    CONF_PUMP_ENTITY: "switch.pool_pump",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations for all tests."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for the poolman integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Pool",
        data=MOCK_CONFIG_DATA.copy(),
        version=1,
        minor_version=3,
    )


@pytest.fixture
def mock_config_entry_no_pump() -> MockConfigEntry:
    """Return a MockConfigEntry without a pump entity (no scheduler)."""
    data = MOCK_CONFIG_DATA.copy()
    data.pop(CONF_PUMP_ENTITY)
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Pool",
        data=data,
        version=1,
        minor_version=3,
    )


def setup_mock_states(hass: HomeAssistant) -> None:
    """Set up mock sensor states with good readings."""
    hass.states.async_set("sensor.pool_ph", "7.2")
    hass.states.async_set("sensor.pool_orp", "750.0")
    hass.states.async_set("sensor.pool_temperature", "26.0")


@pytest.fixture
def pool() -> Pool:
    """Return a standard test pool."""
    return Pool(
        name="Test Pool",
        volume_m3=50.0,
        shape=PoolShape.RECTANGULAR,
        pump_flow_m3h=10.0,
    )


@pytest.fixture
def good_reading() -> PoolReading:
    """Return a reading with all parameters in acceptable range."""
    return PoolReading(
        ph=7.2,
        orp=750.0,
        temp_c=26.0,
        outdoor_temp_c=25.0,
        free_chlorine=2.0,
        ec=500.0,
        tac=120.0,
        cya=40.0,
        hardness=250.0,
    )


@pytest.fixture
def bad_reading() -> PoolReading:
    """Return a reading with parameters out of range."""
    return PoolReading(
        ph=8.2,
        orp=600.0,
        temp_c=30.0,
        outdoor_temp_c=35.0,
        free_chlorine=0.5,
        ec=1500.0,
        tac=60.0,
        cya=10.0,
        hardness=500.0,
    )


@pytest.fixture
def empty_reading() -> PoolReading:
    """Return a reading with no sensor data."""
    return PoolReading()
