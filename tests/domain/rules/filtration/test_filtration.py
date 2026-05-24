"""Tests for FiltrationRule."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import Severity
from custom_components.poolman.domain.rules import FiltrationRule

from ..conftest import make_state


class TestFiltrationRule:
    """Tests for filtration rule evaluation."""

    def test_produces_problem(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=26.0)))
        assert len(problems) == 1
        assert problems[0].code == "filtration_required"
        assert problems[0].metric is None
        assert problems[0].value is not None

    def test_no_temp_no_problem(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(make_state(pool, PoolReading()))
        assert problems == []

    def test_low_filtration_hours_returns_low_severity(self, pool: Pool) -> None:
        """When filtration hours < 12 in running mode, severity should be LOW."""
        problems = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=20.0)))
        assert len(problems) == 1
        assert problems[0].severity == Severity.LOW

    def test_high_filtration_hours_returns_medium_severity(self, pool: Pool) -> None:
        """When filtration hours >= 12, severity should be MEDIUM."""
        problems = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=26.0)))
        assert len(problems) == 1
        assert problems[0].severity == Severity.MEDIUM

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=15.0), PoolMode.WINTER_ACTIVE)
        )
        assert len(problems) == 1
        assert problems[0].code == "filtration_required"

    def test_hibernating_produces_problem(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.HIBERNATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "filtration_required"

    def test_activating_produces_problem(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.ACTIVATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "filtration_required"

    def test_winter_passive_skips(self, pool: Pool) -> None:
        problems = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []
