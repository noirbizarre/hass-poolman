"""Tests for CalibrationRule."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.poolman.domain.model import (
    ManualMeasure,
    MeasureParameter,
    Pool,
    PoolMode,
    PoolReading,
)
from custom_components.poolman.domain.problem import Severity
from custom_components.poolman.domain.rules import CalibrationRule

from ..conftest import make_state


def _ts() -> datetime:
    """Return a fixed timestamp for test measures."""
    return datetime(2025, 7, 15, 10, 0, tzinfo=UTC)


class TestCalibrationRule:
    """Tests for CalibrationRule deviation detection."""

    def test_no_manual_measures_no_problem(self, pool: Pool) -> None:
        result = CalibrationRule().evaluate(make_state(pool, PoolReading(ph=7.2, orp=750.0)))
        assert result.problems == []

    def test_no_deviation_no_problem(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.1, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.2), manual_measures=measures)
        )
        assert result.problems == []

    def test_ph_deviation_generates_problem(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.8), manual_measures=measures)
        )
        assert len(result.problems) == 1
        assert result.problems[0].code == "calibration_ph"
        assert result.problems[0].severity == Severity.LOW
        assert result.problems[0].metric is None
        assert "pH" in result.problems[0].message
        assert "7.8" in result.problems[0].message
        assert "7.2" in result.problems[0].message

    def test_orp_deviation_generates_problem(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.ORP: ManualMeasure(
                parameter=MeasureParameter.ORP, value=750.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(orp=810.0), manual_measures=measures)
        )
        assert len(result.problems) == 1
        assert result.problems[0].code == "calibration_orp"
        assert "ORP" in result.problems[0].message

    def test_temperature_deviation_generates_problem(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.TEMPERATURE: ManualMeasure(
                parameter=MeasureParameter.TEMPERATURE, value=26.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=28.5), manual_measures=measures)
        )
        assert len(result.problems) == 1
        assert "temperature" in result.problems[0].message

    def test_sensor_none_skipped(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=None), manual_measures=measures)
        )
        assert result.problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=8.0), PoolMode.WINTER_PASSIVE, manual_measures=measures)
        )
        assert result.problems == []

    def test_multiple_deviations(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
            MeasureParameter.ORP: ManualMeasure(
                parameter=MeasureParameter.ORP, value=750.0, measured_at=_ts()
            ),
            MeasureParameter.TEMPERATURE: ManualMeasure(
                parameter=MeasureParameter.TEMPERATURE, value=26.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.8, orp=810.0, temp_c=30.0), manual_measures=measures)
        )
        assert len(result.problems) == 3

    def test_deviation_at_threshold_no_problem(self, pool: Pool) -> None:
        """Deviation exactly at threshold should NOT generate a problem."""
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.5), manual_measures=measures)
        )
        # 0.3 == threshold, not > threshold
        assert result.problems == []

    def test_tac_deviation(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.TAC: ManualMeasure(
                parameter=MeasureParameter.TAC, value=120.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(tac=145.0), manual_measures=measures)
        )
        assert len(result.problems) == 1
        assert "TAC" in result.problems[0].message

    def test_salt_deviation(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.SALT: ManualMeasure(
                parameter=MeasureParameter.SALT, value=3200.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(salt=3400.0), manual_measures=measures)
        )
        assert len(result.problems) == 1
        assert "salt" in result.problems[0].message

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.8), PoolMode.WINTER_ACTIVE, manual_measures=measures)
        )
        assert len(result.problems) == 1

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            make_state(pool, PoolReading(ph=7.8), PoolMode.HIBERNATING, manual_measures=measures)
        )
        assert len(result.problems) == 1
