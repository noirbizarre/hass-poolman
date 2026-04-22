"""Sensor calibration deviation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...model import MeasureParameter, PoolMode
from ...problem import Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState

# Deviation thresholds per parameter.
# When the absolute difference between a sensor reading and the last manual
# measurement exceeds these values, a calibration problem is generated.
_CALIBRATION_THRESHOLDS: dict[MeasureParameter, float] = {
    MeasureParameter.PH: 0.3,
    MeasureParameter.ORP: 50.0,
    MeasureParameter.FREE_CHLORINE: 0.5,
    MeasureParameter.EC: 100.0,
    MeasureParameter.TDS: 50.0,
    MeasureParameter.SALT: 100.0,
    MeasureParameter.TAC: 20.0,
    MeasureParameter.CYA: 10.0,
    MeasureParameter.HARDNESS: 50.0,
    MeasureParameter.TEMPERATURE: 2.0,
}

# Mapping from MeasureParameter to the corresponding PoolReading field name
_MEASURE_TO_READING_FIELD: dict[MeasureParameter, str] = {
    MeasureParameter.PH: "ph",
    MeasureParameter.ORP: "orp",
    MeasureParameter.FREE_CHLORINE: "free_chlorine",
    MeasureParameter.EC: "ec",
    MeasureParameter.TDS: "tds",
    MeasureParameter.SALT: "salt",
    MeasureParameter.TAC: "tac",
    MeasureParameter.CYA: "cya",
    MeasureParameter.HARDNESS: "hardness",
    MeasureParameter.TEMPERATURE: "temp_c",
}

# Human-readable labels for measure parameters
_MEASURE_LABELS: dict[MeasureParameter, str] = {
    MeasureParameter.PH: "pH",
    MeasureParameter.ORP: "ORP",
    MeasureParameter.FREE_CHLORINE: "free chlorine",
    MeasureParameter.EC: "EC",
    MeasureParameter.TDS: "TDS",
    MeasureParameter.SALT: "salt",
    MeasureParameter.TAC: "TAC",
    MeasureParameter.CYA: "CYA",
    MeasureParameter.HARDNESS: "hardness",
    MeasureParameter.TEMPERATURE: "temperature",
}


class CalibrationRule(Rule):
    """Detect deviation between sensor readings and manual measurements.

    Compares raw sensor values (:attr:`~...model.PoolState.raw_sensor_reading`)
    against the latest manual measurements
    (:attr:`~...model.PoolState.manual_measures`).  Generates a
    :attr:`~...problem.Severity.LOW` problem for each parameter whose
    deviation exceeds the per-parameter threshold.

    Requires :attr:`~...model.PoolState.raw_sensor_reading` to be set;
    returns empty result when ``None``.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` mode.
    """

    id = "calibration"
    description = "Detect sensor vs. manual measurement deviation"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Compare sensor readings against manual measures and flag deviations."""
        if state.mode == PoolMode.WINTER_PASSIVE:
            return RuleResult()
        if state.raw_sensor_reading is None or not state.manual_measures:
            return RuleResult()

        problems: list[Problem] = []
        for param, measure in state.manual_measures.items():
            threshold = _CALIBRATION_THRESHOLDS.get(param)
            if threshold is None:
                continue

            field_name = _MEASURE_TO_READING_FIELD.get(param)
            if field_name is None:
                continue

            sensor_value = getattr(state.raw_sensor_reading, field_name, None)
            if sensor_value is None:
                continue

            deviation = abs(sensor_value - measure.value)
            if deviation > threshold:
                label = _MEASURE_LABELS.get(param, param.value)
                problems.append(
                    Problem(
                        code=f"calibration_{param.value}",
                        message=(
                            f"{label} sensor reading ({sensor_value:.1f}) deviates from"
                            f" manual measure ({measure.value:.1f}) by {deviation:.1f}"
                            f" (threshold {threshold})."
                            " Consider sensor recalibration or a new manual measurement."
                        ),
                        severity=Severity.LOW,
                        metric=None,
                        value=sensor_value,
                        expected_range=None,
                    )
                )

        return RuleResult(problems=problems)
