"""Tests for FreeChlorineRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import FreeChlorineRule

from ..conftest import make_state


class TestFreeChlorineRule:
    """Tests for free chlorine rule evaluation."""

    def test_in_range_no_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=2.0)))
        assert problems == []

    def test_too_low_returns_critical_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=0.5)))
        assert len(problems) == 1
        assert problems[0].code == "chlorine_too_low"
        assert problems[0].severity == Severity.CRITICAL
        assert problems[0].metric == MetricName.CHLORINE
        assert problems[0].value == pytest.approx(0.5)

    def test_too_high_returns_low_severity_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=4.0)))
        assert len(problems) == 1
        assert problems[0].code == "chlorine_too_high"
        assert problems[0].severity == Severity.LOW
        assert problems[0].metric == MetricName.CHLORINE

    def test_none_no_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=None)))
        assert problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(
            make_state(pool, PoolReading(free_chlorine=0.5), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(
            make_state(pool, PoolReading(free_chlorine=0.5), PoolMode.WINTER_ACTIVE)
        )
        assert problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(
            make_state(pool, PoolReading(free_chlorine=0.5), PoolMode.HIBERNATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "chlorine_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(
            make_state(pool, PoolReading(free_chlorine=0.5), PoolMode.ACTIVATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "chlorine_too_low"

    def test_at_min_no_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=1.0)))
        assert problems == []

    def test_at_max_no_problem(self, pool: Pool) -> None:
        problems = FreeChlorineRule().evaluate(make_state(pool, PoolReading(free_chlorine=3.0)))
        assert problems == []
