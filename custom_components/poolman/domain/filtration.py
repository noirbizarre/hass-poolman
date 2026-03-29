"""Pool filtration duration calculations.

Pure domain logic for computing optimal filtration time.
No Home Assistant dependencies.
"""

from __future__ import annotations

from .model import FiltrationKind, Pool, PoolMode, PoolReading

# Minimum filtration hours by mode
MIN_FILTRATION_HOURS: float = 2.0
MAX_FILTRATION_HOURS: float = 24.0

# Winter mode filtration settings
WINTER_ACTIVE_HOURS: float = 4.0
WINTER_PASSIVE_HOURS: float = 0.0

# Filtration efficiency coefficients by filter type.
# A lower value means the filter is more efficient (finer micron rating),
# resulting in shorter required filtration time.
# Source: filter micron ratings from industry data
#   - Sand: 20-40 microns (baseline)
#   - Cartridge: 10-20 microns
#   - Glass media: 3-10 microns
#   - Diatomaceous earth: 2-5 microns
FILTRATION_EFFICIENCY: dict[FiltrationKind, float] = {
    FiltrationKind.SAND: 1.0,
    FiltrationKind.CARTRIDGE: 0.95,
    FiltrationKind.GLASS: 0.9,
    FiltrationKind.DIATOMACEOUS_EARTH: 0.85,
}

# Outdoor temperature heat stress constants.
# Above this threshold, each additional degree increases filtration need
# to compensate for accelerated algae growth and chlorine degradation.
OUTDOOR_TEMP_THRESHOLD: float = 28.0
OUTDOOR_TEMP_FACTOR: float = 0.05  # +5% per degree above threshold


def compute_filtration_duration(
    pool: Pool,
    reading: PoolReading,
    mode: PoolMode,
) -> float | None:
    """Compute recommended daily filtration duration in hours.

    Uses a multi-factor algorithm:

    1. **Base rule**: water temperature / 2 (classic French pool industry rule)
    2. **Filter efficiency**: coefficient based on filter type (finer = shorter)
    3. **Heat stress**: outdoor temperature above 28 °C increases duration
    4. **Turnover guarantee**: ensures at least one full water volume cycle
    5. **Clamping**: result bounded between 2 h and 24 h

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.
        mode: Current operational mode.

    Returns:
        Recommended filtration hours, or None if computation is not possible.
    """
    if mode == PoolMode.WINTER_PASSIVE:
        return WINTER_PASSIVE_HOURS

    if mode == PoolMode.WINTER_ACTIVE:
        return WINTER_ACTIVE_HOURS

    if reading.temp_c is None:
        return None

    # 1. Classic rule: temperature / 2
    base_hours = reading.temp_c / 2

    # 2. Adjust for filter type efficiency
    base_hours *= FILTRATION_EFFICIENCY[pool.filtration_kind]

    # 3. Adjust for outdoor temperature heat stress
    if reading.outdoor_temp_c is not None and reading.outdoor_temp_c > OUTDOOR_TEMP_THRESHOLD:
        heat_factor = 1 + (reading.outdoor_temp_c - OUTDOOR_TEMP_THRESHOLD) * OUTDOOR_TEMP_FACTOR
        base_hours *= heat_factor

    # 4. Adjust for pump capacity: if pump can't turn over the full volume
    # in the base hours, increase filtration time
    if pool.pump_flow_m3h > 0:
        turnover_hours = pool.volume_m3 / pool.pump_flow_m3h
        # Ensure at least one full turnover
        base_hours = max(base_hours, turnover_hours)

    # 5. Clamp to reasonable bounds
    return max(MIN_FILTRATION_HOURS, min(base_hours, MAX_FILTRATION_HOURS))
