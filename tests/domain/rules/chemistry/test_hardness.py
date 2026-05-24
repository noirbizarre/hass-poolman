"""Tests for HardnessRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import HardnessRule

from ..conftest import make_state


class TestHardnessRule:
    """Tests for calcium hardness rule evaluation."""

    def test_hardness_in_range_no_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=250.0)))
        assert problems == []

    def test_hardness_too_low_returns_medium_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=100.0)))
        assert len(problems) == 1
        assert problems[0].code == "hardness_too_low"
        assert problems[0].metric == MetricName.HARDNESS
        assert problems[0].severity == Severity.MEDIUM
        assert problems[0].value == pytest.approx(100.0)

    def test_hardness_too_high_returns_low_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=500.0)))
        assert len(problems) == 1
        assert problems[0].code == "hardness_too_high"
        assert problems[0].severity == Severity.LOW

    def test_hardness_none_no_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=None)))
        assert problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(
            make_state(pool, PoolReading(hardness=100.0), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(
            make_state(pool, PoolReading(hardness=100.0), PoolMode.WINTER_ACTIVE)
        )
        assert problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(
            make_state(pool, PoolReading(hardness=100.0), PoolMode.HIBERNATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "hardness_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(
            make_state(pool, PoolReading(hardness=100.0), PoolMode.ACTIVATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "hardness_too_low"

    def test_hardness_at_min_no_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=150.0)))
        assert problems == []

    def test_hardness_at_max_no_problem(self, pool: Pool) -> None:
        problems = HardnessRule().evaluate(make_state(pool, PoolReading(hardness=400.0)))
        assert problems == []
