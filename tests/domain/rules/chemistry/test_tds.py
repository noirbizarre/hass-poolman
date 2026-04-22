"""Tests for TdsRule."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading, TreatmentType
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import TdsRule

from ..conftest import make_state


class TestTdsRule:
    """Tests for TDS (Total Dissolved Solids) rule evaluation."""

    def test_tds_in_range_no_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=500.0)))
        assert result.problems == []

    def test_tds_too_high_returns_medium_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=2000.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "tds_too_high"
        assert result.problems[0].metric == MetricName.TDS
        assert result.problems[0].severity == Severity.MEDIUM

    def test_tds_too_low_returns_low_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=100.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "tds_too_low"
        assert result.problems[0].severity == Severity.LOW

    def test_tds_none_no_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=None)))
        assert result.problems == []

    def test_salt_electrolysis_skips(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=2000.0)))
        assert result.problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        result = TdsRule().evaluate(
            make_state(pool, PoolReading(tds=2000.0), PoolMode.WINTER_PASSIVE)
        )
        assert result.problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        result = TdsRule().evaluate(
            make_state(pool, PoolReading(tds=2000.0), PoolMode.WINTER_ACTIVE)
        )
        assert result.problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=2000.0), PoolMode.HIBERNATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "tds_too_high"

    def test_activating_evaluates(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=2000.0), PoolMode.ACTIVATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "tds_too_high"

    def test_tds_at_min_no_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=250.0)))
        assert result.problems == []

    def test_tds_at_max_no_problem(self, pool: Pool) -> None:
        result = TdsRule().evaluate(make_state(pool, PoolReading(tds=1500.0)))
        assert result.problems == []
