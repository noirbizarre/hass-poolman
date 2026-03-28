"""Constants for the Pool Manager integration."""

from typing import Final

DOMAIN: Final = "poolman"

PLATFORMS: Final = ["sensor", "binary_sensor", "select"]

# Config entry keys
CONF_POOL_NAME: Final = "pool_name"
CONF_VOLUME_M3: Final = "volume_m3"
CONF_SHAPE: Final = "shape"
CONF_PUMP_FLOW_M3H: Final = "pump_flow_m3h"

# Sensor entity config keys
CONF_PH_ENTITY: Final = "ph_entity"
CONF_ORP_ENTITY: Final = "orp_entity"
CONF_TEMPERATURE_ENTITY: Final = "temperature_entity"
CONF_TAC_ENTITY: Final = "tac_entity"
CONF_CYA_ENTITY: Final = "cya_entity"
CONF_HARDNESS_ENTITY: Final = "hardness_entity"

# Actuator entity config keys
CONF_PUMP_ENTITY: Final = "pump_entity"

# Pool shapes
SHAPE_RECTANGULAR: Final = "rectangular"
SHAPE_ROUND: Final = "round"
SHAPE_FREEFORM: Final = "freeform"
SHAPES: Final = [SHAPE_RECTANGULAR, SHAPE_ROUND, SHAPE_FREEFORM]

# Pool modes
MODE_RUNNING: Final = "running"
MODE_WINTER_ACTIVE: Final = "winter_active"
MODE_WINTER_PASSIVE: Final = "winter_passive"
MODES: Final = [MODE_RUNNING, MODE_WINTER_ACTIVE, MODE_WINTER_PASSIVE]

# Default values
DEFAULT_VOLUME_M3: Final = 50.0
DEFAULT_PUMP_FLOW_M3H: Final = 10.0
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5
