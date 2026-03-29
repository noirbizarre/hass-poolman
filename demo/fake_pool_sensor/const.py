"""Constants for the Fake Pool Sensor integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DOMAIN: Final = "fake_pool_sensor"

PLATFORMS: Final = ["sensor", "number", "switch"]

CONF_DEVICE_NAME: Final = "device_name"

DEFAULT_DEVICE_NAME: Final = "Fake Pool Sensor"
DEFAULT_UPDATE_INTERVAL_SECONDS: Final = 30


@dataclass(frozen=True, kw_only=True)
class FakeSensorSpec:
    """Specification for a fake pool sensor channel."""

    key: str
    name: str
    default: float
    min_value: float
    max_value: float
    step: float
    noise: float
    unit: str | None
    icon: str


SENSOR_SPECS: Final[tuple[FakeSensorSpec, ...]] = (
    FakeSensorSpec(
        key="temperature",
        name="Water temperature",
        default=26.0,
        min_value=0.0,
        max_value=45.0,
        step=0.1,
        noise=0.3,
        unit="\u00b0C",
        icon="mdi:thermometer-water",
    ),
    FakeSensorSpec(
        key="ph",
        name="pH",
        default=7.2,
        min_value=0.0,
        max_value=14.0,
        step=0.01,
        noise=0.05,
        unit=None,
        icon="mdi:ph",
    ),
    FakeSensorSpec(
        key="orp",
        name="ORP",
        default=750.0,
        min_value=0.0,
        max_value=1000.0,
        step=1.0,
        noise=15.0,
        unit="mV",
        icon="mdi:flash-triangle-outline",
    ),
    FakeSensorSpec(
        key="tac",
        name="Total alkalinity",
        default=120.0,
        min_value=0.0,
        max_value=500.0,
        step=1.0,
        noise=5.0,
        unit="mg/L",
        icon="mdi:beaker-outline",
    ),
    FakeSensorSpec(
        key="cya",
        name="Cyanuric acid",
        default=40.0,
        min_value=0.0,
        max_value=300.0,
        step=1.0,
        noise=2.0,
        unit="mg/L",
        icon="mdi:shield-sun-outline",
    ),
    FakeSensorSpec(
        key="hardness",
        name="Calcium hardness",
        default=250.0,
        min_value=0.0,
        max_value=1000.0,
        step=1.0,
        noise=10.0,
        unit="mg/L",
        icon="mdi:water-opacity",
    ),
    FakeSensorSpec(
        key="outdoor_temperature",
        name="Outdoor temperature",
        default=25.0,
        min_value=-10.0,
        max_value=50.0,
        step=0.1,
        noise=0.5,
        unit="\u00b0C",
        icon="mdi:thermometer",
    ),
)
