"""Shared fixtures and helpers for rule tests."""

from __future__ import annotations

from custom_components.poolman.domain.model import (
    ManualMeasure,
    MeasureParameter,
    Pool,
    PoolMode,
    PoolReading,
    PoolState,
)


def make_state(
    pool: Pool | None = None,
    reading: PoolReading | None = None,
    mode: PoolMode = PoolMode.ACTIVE,
    manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    raw_sensor_reading: PoolReading | None = None,
) -> PoolState:
    """Build a minimal PoolState for rule evaluation tests.

    Args:
        pool: Pool physical configuration. Defaults to a 50 m³ chlorine pool.
        reading: Pool sensor readings. Defaults to an empty PoolReading.
        mode: Pool operational mode. Defaults to ACTIVE.
        manual_measures: Manual measurement overrides, used by CalibrationRule.
        raw_sensor_reading: Raw sensor reading (pre-fallback). When provided,
            used for calibration comparison. When None, defaults to reading.

    Returns:
        A PoolState ready for rule evaluation.
    """
    if pool is None:
        pool = Pool(name="Test Pool", volume_m3=50.0, pump_flow_m3h=10.0)
    if reading is None:
        reading = PoolReading()
    return PoolState(
        mode=mode,
        pool=pool,
        reading=reading,
        raw_sensor_reading=raw_sensor_reading if raw_sensor_reading is not None else reading,
        manual_measures=manual_measures or {},
    )
