"""Tests for SaltRule."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading, TreatmentType
from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.rules import SaltRule

from ..conftest import make_state


def _make_salt_pool() -> Pool:
    return Pool(
        name="Salt Pool",
        volume_m3=50.0,
        pump_flow_m3h=10.0,
        treatment=TreatmentType.SALT_ELECTROLYSIS,
    )


class TestSaltRule:
    """Tests for salt level rule evaluation."""

    def test_salt_in_range_no_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=3200.0)))
        assert problems == []

    def test_salt_too_low_returns_medium_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=2000.0)))
        assert len(problems) == 1
        assert problems[0].code == "salt_too_low"
        assert problems[0].metric == MetricName.SALT
        assert problems[0].severity == Severity.MEDIUM
        assert problems[0].value == pytest.approx(2000.0)

    def test_salt_too_high_returns_low_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=4000.0)))
        assert len(problems) == 1
        assert problems[0].code == "salt_too_high"
        assert problems[0].severity == Severity.LOW

    def test_salt_none_no_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=None)))
        assert problems == []

    def test_non_salt_treatment_skips(self, pool: Pool) -> None:
        """SaltRule should skip for non-salt-electrolysis treatment types."""
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=2000.0)))
        assert problems == []

    def test_winter_passive_skips(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(
            make_state(pool, PoolReading(salt=2000.0), PoolMode.WINTER_PASSIVE)
        )
        assert problems == []

    def test_winter_active_skips(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(
            make_state(pool, PoolReading(salt=2000.0), PoolMode.WINTER_ACTIVE)
        )
        assert problems == []

    def test_hibernating_evaluates(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(
            make_state(pool, PoolReading(salt=2000.0), PoolMode.HIBERNATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "salt_too_low"

    def test_activating_evaluates(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(
            make_state(pool, PoolReading(salt=2000.0), PoolMode.ACTIVATING)
        )
        assert len(problems) == 1
        assert problems[0].code == "salt_too_low"

    def test_salt_at_min_no_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=2700.0)))
        assert problems == []

    def test_salt_at_max_no_problem(self) -> None:
        pool = _make_salt_pool()
        problems = SaltRule().evaluate(make_state(pool, PoolReading(salt=3400.0)))
        assert problems == []
