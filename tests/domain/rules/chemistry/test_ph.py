"""Tests for the PhRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import PhRule

from ..conftest import make_state


class TestPhRule:
    """Tests for pH rule evaluation."""

    def test_good_ph_no_problem(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.2)))
        assert result.problems == []

    def test_high_ph_returns_problem(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.8)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_high"
        assert result.problems[0].metric == MetricName.PH
        assert result.problems[0].value == pytest.approx(7.8)

    def test_low_ph_returns_critical_problem(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=6.6)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_low"
        assert result.problems[0].severity == Severity.CRITICAL
        assert result.problems[0].metric == MetricName.PH

    def test_winter_passive_skips(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=8.5), PoolMode.WINTER_PASSIVE))
        assert result.problems == []

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        """pH rule should still evaluate in active winter mode (equipment protection)."""
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.8), PoolMode.WINTER_ACTIVE))
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_high"

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.8), PoolMode.HIBERNATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_high"

    def test_activating_evaluates(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.8), PoolMode.ACTIVATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_high"

    def test_slightly_off_ph_returns_low_severity(self, pool: Pool) -> None:
        """pH slightly off target (delta <= tolerance*3) -> LOW severity."""
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.4)))
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.LOW

    def test_ph_outside_range_returns_critical_severity(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=8.2)))
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.CRITICAL

    def test_ph_medium_deviation_returns_medium_severity(self, pool: Pool) -> None:
        """pH delta > 3x tolerance but within range -> MEDIUM severity."""
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=7.6)))
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.MEDIUM

    def test_none_ph_skips(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading()))
        assert result.problems == []

    def test_expected_range_set(self, pool: Pool) -> None:
        result = PhRule().evaluate(make_state(pool, PoolReading(ph=8.5)))
        assert result.problems[0].expected_range is not None
        low, high = result.problems[0].expected_range
        assert low < 7.0
        assert high > 7.5
