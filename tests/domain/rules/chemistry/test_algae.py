"""Tests for AlgaeRiskRule."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import AlgaeRiskRule

from ..conftest import make_state


class TestAlgaeRiskRule:
    """Tests for algae risk detection."""

    def test_warm_and_low_orp_triggers_critical(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(make_state(pool, PoolReading(temp_c=30.0, orp=650.0)))
        assert len(result.problems) == 1
        assert result.problems[0].code == "algae_risk"
        assert result.problems[0].severity == Severity.CRITICAL
        assert result.problems[0].metric == MetricName.ORP

    def test_cool_water_no_risk(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(make_state(pool, PoolReading(temp_c=22.0, orp=650.0)))
        assert result.problems == []

    def test_warm_but_good_orp_no_risk(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(make_state(pool, PoolReading(temp_c=30.0, orp=750.0)))
        assert result.problems == []

    def test_missing_data_no_risk(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(make_state(pool, PoolReading(temp_c=30.0)))
        assert result.problems == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(
            make_state(pool, PoolReading(temp_c=30.0, orp=650.0), PoolMode.WINTER_PASSIVE)
        )
        assert result.problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(
            make_state(pool, PoolReading(temp_c=30.0, orp=650.0), PoolMode.WINTER_ACTIVE)
        )
        assert result.problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(
            make_state(pool, PoolReading(temp_c=30.0, orp=650.0), PoolMode.HIBERNATING)
        )
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.CRITICAL

    def test_activating_evaluates(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(
            make_state(pool, PoolReading(temp_c=30.0, orp=650.0), PoolMode.ACTIVATING)
        )
        assert len(result.problems) == 1
        assert result.problems[0].severity == Severity.CRITICAL

    def test_message_includes_temp_and_orp(self, pool: Pool) -> None:
        result = AlgaeRiskRule().evaluate(make_state(pool, PoolReading(temp_c=30.0, orp=650.0)))
        assert "30.0" in result.problems[0].message
        assert "650" in result.problems[0].message
