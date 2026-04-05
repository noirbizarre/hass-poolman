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
CONF_FREE_CHLORINE_ENTITY: Final = "free_chlorine_entity"
CONF_EC_ENTITY: Final = "ec_entity"
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
MODE_ACTIVE: Final = "active"
MODE_HIBERNATING: Final = "hibernating"
MODE_WINTER_ACTIVE: Final = "winter_active"
MODE_WINTER_PASSIVE: Final = "winter_passive"
MODE_ACTIVATING: Final = "activating"
MODES: Final = [
    MODE_ACTIVE,
    MODE_HIBERNATING,
    MODE_WINTER_ACTIVE,
    MODE_WINTER_PASSIVE,
    MODE_ACTIVATING,
]

# Filtration duration modes
FILTRATION_DURATION_MODE_MANUAL: Final = "manual"
FILTRATION_DURATION_MODE_DYNAMIC: Final = "dynamic"
FILTRATION_DURATION_MODE_SPLIT_STATIC: Final = "split_static"
FILTRATION_DURATION_MODE_SPLIT_DYNAMIC: Final = "split_dynamic"
FILTRATION_DURATION_MODES: Final = [
    FILTRATION_DURATION_MODE_MANUAL,
    FILTRATION_DURATION_MODE_DYNAMIC,
    FILTRATION_DURATION_MODE_SPLIT_STATIC,
    FILTRATION_DURATION_MODE_SPLIT_DYNAMIC,
]

# Filtration control event types
EVENT_FILTRATION_STARTED: Final = "filtration_started"
EVENT_FILTRATION_STOPPED: Final = "filtration_stopped"

# Boost event types
EVENT_BOOST_STARTED: Final = "boost_started"
EVENT_BOOST_CONSUMED: Final = "boost_consumed"
EVENT_BOOST_CANCELLED: Final = "boost_cancelled"

# Boost presets (hours) exposed by the select entity
BOOST_PRESET_NONE: Final = "none"
BOOST_PRESETS: Final = [BOOST_PRESET_NONE, "2", "4", "8", "24"]

# Default values
DEFAULT_VOLUME_M3: Final = 50.0
DEFAULT_TREATMENT: Final = TREATMENT_CHLORINE
DEFAULT_FILTRATION_KIND: Final = FILTRATION_KIND_SAND
DEFAULT_PUMP_FLOW_M3H: Final = 10.0
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5
DEFAULT_FILTRATION_START_TIME: Final = time(10, 0)
DEFAULT_FILTRATION_DURATION_HOURS: Final = 8.0
DEFAULT_FILTRATION_DURATION_MODE: Final = FILTRATION_DURATION_MODE_DYNAMIC
DEFAULT_FILTRATION_START_TIME_2: Final = time(16, 0)
DEFAULT_FILTRATION_DURATION_HOURS_2: Final = 4.0
DEFAULT_MIN_DYNAMIC_DURATION_HOURS: Final = 0.0

# Wizard subentry types
SUBENTRY_HIBERNATION: Final = "hibernation"
SUBENTRY_ACTIVATION: Final = "activation"

# Wizard subentry data keys
CONF_TARGET_MODE: Final = "target_mode"
CONF_STARTED_AT: Final = "started_at"
CONF_COMPLETED_AT: Final = "completed_at"
CONF_STEPS: Final = "steps"

# Hibernation wizard
HIBERNATION_TARGET_MODES: Final = [MODE_WINTER_PASSIVE, MODE_WINTER_ACTIVE]

# Activation wizard: modes from which activation can be started
ACTIVATION_SOURCE_MODES: Final = [
    MODE_HIBERNATING,
    MODE_WINTER_ACTIVE,
    MODE_WINTER_PASSIVE,
]

# Service names
SERVICE_ADD_TREATMENT: Final = "add_treatment"
SERVICE_RECORD_MEASURE: Final = "record_measure"
SERVICE_BOOST_FILTRATION: Final = "boost_filtration"
SERVICE_CONFIRM_ACTIVATION_STEP: Final = "confirm_activation_step"
