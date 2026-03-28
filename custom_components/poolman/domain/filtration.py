"""Pool filtration duration calculations.

Pure domain logic for computing optimal filtration time.
No Home Assistant dependencies.
"""

from __future__ import annotations

from .model import Pool, PoolMode, PoolReading

# Minimum filtration hours by mode
MIN_FILTRATION_HOURS: float = 2.0
MAX_FILTRATION_HOURS: float = 24.0

# Winter mode filtration settings
WINTER_ACTIVE_HOURS: float = 4.0
WINTER_PASSIVE_HOURS: float = 0.0


def compute_filtration_duration(
    pool: Pool,
    reading: PoolReading,
    mode: PoolMode,
) -> float | None:
    """Compute recommended daily filtration duration in hours.

    Uses the classic rule: temperature / 2 for running mode,
    with adjustments based on pump flow rate and pool volume.

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

    # Classic rule: temperature / 2
    base_hours = reading.temp_c / 2

    # Adjust for pump capacity: if pump can't turn over the full volume
    # in the base hours, increase filtration time
    if pool.pump_flow_m3h > 0:
        turnover_hours = pool.volume_m3 / pool.pump_flow_m3h
        # Ensure at least one full turnover
        base_hours = max(base_hours, turnover_hours)

    # Clamp to reasonable bounds
    return max(MIN_FILTRATION_HOURS, min(base_hours, MAX_FILTRATION_HOURS))
