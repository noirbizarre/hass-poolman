"""Tests for FiltrationRule."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import Severity
from custom_components.poolman.domain.rules import FiltrationRule

from ..conftest import make_state


class TestFiltrationRule:
    """Tests for filtration rule evaluation."""

    def test_produces_problem(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=26.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "filtration_required"
        assert result.problems[0].metric is None
        assert result.problems[0].value is not None

    def test_no_temp_no_problem(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(make_state(pool, PoolReading()))
        assert result.problems == []

    def test_low_filtration_hours_returns_low_severity(self, pool: Pool) -> None:
        """When filtration hours < 12 in running mode, severity should be LOW."""
        result = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=20.0)))
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.LOW

    def test_high_filtration_hours_returns_medium_severity(self, pool: Pool) -> None:
        """When filtration hours >= 12, severity should be MEDIUM."""
        result = FiltrationRule().evaluate(make_state(pool, PoolReading(temp_c=26.0)))
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.MEDIUM

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=15.0), PoolMode.WINTER_ACTIVE)
        )
        assert len(result.problems) == 1
        assert result.problems[0].code == "filtration_required"

    def test_hibernating_produces_problem(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.HIBERNATING)
        )
        assert len(result.problems) == 1
        assert result.problems[0].code == "filtration_required"

    def test_activating_produces_problem(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.ACTIVATING)
        )
        assert len(result.problems) == 1
        assert result.problems[0].code == "filtration_required"

    def test_winter_passive_skips(self, pool: Pool) -> None:
        result = FiltrationRule().evaluate(
            make_state(pool, PoolReading(temp_c=26.0), PoolMode.WINTER_PASSIVE)
        )
        assert result.problems == []
