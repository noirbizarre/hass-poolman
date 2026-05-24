"""Tests for TacRule."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import TacRule

from ..conftest import make_state


class TestTacRule:
    """Tests for TAC rule evaluation."""

    def test_tac_in_range_no_problem(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading(tac=120.0)))
        assert problems == []

    def test_low_tac_returns_problem(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading(tac=50.0)))
        assert len(problems) == 1
        assert problems[0].code == "alkalinity_too_low"
        assert problems[0].metric == MetricName.ALKALINITY
        assert problems[0].severity == Severity.MEDIUM

    def test_high_tac_returns_low_severity_problem(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading(tac=160.0)))
        assert len(problems) == 1
        assert problems[0].code == "alkalinity_too_high"
        assert problems[0].severity == Severity.LOW
        assert "too high" in problems[0].message.lower()

    def test_winter_passive_skips(self, pool: Pool) -> None:
        problems = TacRule().evaluate(
            make_state(pool, PoolReading(tac=50.0), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        problems = TacRule().evaluate(
            make_state(pool, PoolReading(tac=50.0), PoolMode.WINTER_ACTIVE)
        )
        assert problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading(tac=50.0), PoolMode.HIBERNATING))
        assert len(problems) == 1
        assert problems[0].code == "alkalinity_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading(tac=50.0), PoolMode.ACTIVATING))
        assert len(problems) == 1
        assert problems[0].code == "alkalinity_too_low"

    def test_none_tac_skips(self, pool: Pool) -> None:
        problems = TacRule().evaluate(make_state(pool, PoolReading()))
        assert problems == []
