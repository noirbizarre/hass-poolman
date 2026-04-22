"""Tests for CyaRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import CyaRule

from ..conftest import make_state


class TestCyaRule:
    """Tests for CYA (cyanuric acid) rule evaluation."""

    def test_cya_in_range_no_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=40.0)))
        assert result.problems == []

    def test_cya_too_low_returns_medium_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=10.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "cya_too_low"
        assert result.problems[0].metric == MetricName.CYA
        assert result.problems[0].severity == Severity.MEDIUM
        assert result.problems[0].value == pytest.approx(10.0)

    def test_cya_too_high_returns_low_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=100.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "cya_too_high"
        assert result.problems[0].severity == Severity.LOW
        assert (
            "drain" in result.problems[0].message.lower()
            or "too high" in result.problems[0].message.lower()
        )

    def test_cya_none_no_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=None)))
        assert result.problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        result = CyaRule().evaluate(
            make_state(pool, PoolReading(cya=10.0), PoolMode.WINTER_PASSIVE)
        )
        assert result.problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=10.0), PoolMode.WINTER_ACTIVE))
        assert result.problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=10.0), PoolMode.HIBERNATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "cya_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=10.0), PoolMode.ACTIVATING))
        assert len(result.problems) == 1
        assert result.problems[0].code == "cya_too_low"

    def test_cya_at_min_no_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=20.0)))
        assert result.problems == []

    def test_cya_at_max_no_problem(self, pool: Pool) -> None:
        result = CyaRule().evaluate(make_state(pool, PoolReading(cya=75.0)))
        assert result.problems == []
