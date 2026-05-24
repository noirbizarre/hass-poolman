"""Tests for SanitizerRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading, TreatmentType
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import SanitizerRule

from ..conftest import make_state


class TestSanitizerRule:
    """Tests for sanitizer rule evaluation across treatment types."""

    def test_good_orp_no_problem(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=750.0)))
        assert problems == []

    def test_critical_orp_returns_critical_problem(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=600.0)))
        assert len(problems) == 1
        assert problems[0].code == "orp_too_low"
        assert problems[0].severity == Severity.CRITICAL
        assert problems[0].metric == MetricName.ORP

    def test_medium_low_orp_returns_medium_problem(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=700.0)))
        assert len(problems) == 1
        assert problems[0].code == "orp_too_low"
        assert problems[0].severity == Severity.MEDIUM

    def test_high_orp_returns_orp_too_high_problem(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=950.0)))
        assert len(problems) == 1
        assert problems[0].code == "orp_too_high"
        assert problems[0].metric == MetricName.ORP

    def test_salt_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=600.0)))
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_bromine_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="Bromine Pool", volume_m3=50.0, pump_flow_m3h=10.0, treatment=TreatmentType.BROMINE
        )
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=600.0)))
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_active_oxygen_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="O2 Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.ACTIVE_OXYGEN,
        )
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=600.0)))
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_winter_passive_skips(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(
            make_state(pool, PoolReading(orp=600.0), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(
            make_state(pool, PoolReading(orp=600.0), PoolMode.WINTER_ACTIVE)
        )
        assert problems == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(
            make_state(pool, PoolReading(orp=600.0), PoolMode.HIBERNATING)
        )
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_activating_evaluates(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(
            make_state(pool, PoolReading(orp=600.0), PoolMode.ACTIVATING)
        )
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    @pytest.mark.parametrize("treatment", list(TreatmentType))
    def test_high_orp_returns_too_high_code_for_all_treatments(
        self, treatment: TreatmentType
    ) -> None:
        pool = Pool(name="Test Pool", volume_m3=50.0, pump_flow_m3h=10.0, treatment=treatment)
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading(orp=950.0)))
        assert len(problems) == 1
        assert problems[0].code == "orp_too_high"

    def test_none_orp_skips(self, pool: Pool) -> None:
        problems = SanitizerRule().evaluate(make_state(pool, PoolReading()))
        assert problems == []
