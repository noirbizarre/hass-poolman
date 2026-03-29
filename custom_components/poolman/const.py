"""Constants for the Pool Manager integration."""

from datetime import time
from typing import Final

DOMAIN: Final = "poolman"
EVENT_POOLMAN: Final = "poolman_event"

PLATFORMS: Final = ["sensor", "binary_sensor", "select", "switch", "time", "number", "event"]

# Config entry keys
CONF_POOL_NAME: Final = "pool_name"
CONF_VOLUME_M3: Final = "volume_m3"
CONF_SHAPE: Final = "shape"
CONF_TREATMENT: Final = "treatment"
CONF_FILTRATION_KIND: Final = "filtration_kind"
CONF_PUMP_FLOW_M3H: Final = "pump_flow_m3h"

# Sensor entity config keys
CONF_PH_ENTITY: Final = "ph_entity"
CONF_ORP_ENTITY: Final = "orp_entity"
CONF_TEMPERATURE_ENTITY: Final = "temperature_entity"
CONF_TAC_ENTITY: Final = "tac_entity"
CONF_CYA_ENTITY: Final = "cya_entity"
CONF_HARDNESS_ENTITY: Final = "hardness_entity"

# Meteo entity config keys
CONF_OUTDOOR_TEMPERATURE_ENTITY: Final = "outdoor_temperature_entity"
CONF_WEATHER_ENTITY: Final = "weather_entity"

# Actuator entity config keys
CONF_PUMP_ENTITY: Final = "pump_entity"

# Pool shapes
SHAPE_RECTANGULAR: Final = "rectangular"
SHAPE_ROUND: Final = "round"
SHAPE_FREEFORM: Final = "freeform"
SHAPES: Final = [SHAPE_RECTANGULAR, SHAPE_ROUND, SHAPE_FREEFORM]

# Treatment types
TREATMENT_CHLORINE: Final = "chlorine"
TREATMENT_SALT_ELECTROLYSIS: Final = "salt_electrolysis"
TREATMENT_BROMINE: Final = "bromine"
TREATMENT_ACTIVE_OXYGEN: Final = "active_oxygen"
TREATMENTS: Final = [
    TREATMENT_CHLORINE,
    TREATMENT_SALT_ELECTROLYSIS,
    TREATMENT_BROMINE,
    TREATMENT_ACTIVE_OXYGEN,
]

# Filtration kinds
FILTRATION_KIND_SAND: Final = "sand"
FILTRATION_KIND_CARTRIDGE: Final = "cartridge"
FILTRATION_KIND_DIATOMACEOUS_EARTH: Final = "diatomaceous_earth"
FILTRATION_KIND_GLASS: Final = "glass"
FILTRATION_KINDS: Final = [
    FILTRATION_KIND_SAND,
    FILTRATION_KIND_CARTRIDGE,
    FILTRATION_KIND_DIATOMACEOUS_EARTH,
    FILTRATION_KIND_GLASS,
]

# Pool modes
MODE_RUNNING: Final = "running"
MODE_WINTER_ACTIVE: Final = "winter_active"
MODE_WINTER_PASSIVE: Final = "winter_passive"
MODES: Final = [MODE_RUNNING, MODE_WINTER_ACTIVE, MODE_WINTER_PASSIVE]

# Filtration control event types
EVENT_FILTRATION_STARTED: Final = "filtration_started"
EVENT_FILTRATION_STOPPED: Final = "filtration_stopped"

# Default values
DEFAULT_VOLUME_M3: Final = 50.0
DEFAULT_TREATMENT: Final = TREATMENT_CHLORINE
DEFAULT_FILTRATION_KIND: Final = FILTRATION_KIND_SAND
DEFAULT_PUMP_FLOW_M3H: Final = 10.0
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5
DEFAULT_FILTRATION_START_TIME: Final = time(10, 0)
DEFAULT_FILTRATION_DURATION_HOURS: Final = 8.0

# Service names
SERVICE_ADD_TREATMENT: Final = "add_treatment"
