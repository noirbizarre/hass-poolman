"""Tests for RuleEngine orchestration."""

from __future__ import annotations

from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading
from custom_components.poolman.domain.problem import Problem, Severity
from custom_components.poolman.domain.rules import ALL_RULES, PhRule, RuleEngine

from .conftest import make_state


class TestRuleEngine:
    """Tests for the rule engine orchestration."""

    def test_all_rules_loaded(self) -> None:
        assert len(ALL_RULES) == 11

    def test_engine_takes_rule_list(self) -> None:
        engine = RuleEngine(ALL_RULES)
        assert len(engine.rules) == 11

    def test_good_readings_produce_filtration_only(
        self, pool: Pool, good_reading: PoolReading
    ) -> None:
        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(make_state(pool, good_reading))
        codes = {p.code for p in problems}
        assert "filtration_required" in codes
        # No chemical problems
        assert not any(
            p.code in ("ph_too_high", "ph_too_low", "orp_too_low", "orp_too_high") for p in problems
        )

    def test_bad_readings_produce_multiple_problems(
        self, pool: Pool, bad_reading: PoolReading
    ) -> None:
        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(make_state(pool, bad_reading))
        assert len(problems) > 1

    def test_results_sorted_by_severity(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(make_state(pool, bad_reading))
        severity_order = {Severity.CRITICAL: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
        numeric = [severity_order[p.severity] for p in problems]
        assert numeric == sorted(numeric)

    def test_winter_passive_minimal_problems(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(make_state(pool, bad_reading, PoolMode.WINTER_PASSIVE))
        for p in problems:
            assert p.code in ("filtration_required", "ph_too_high", "ph_too_low")

    def test_empty_readings_no_problems(self, pool: Pool) -> None:
        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(make_state(pool, PoolReading()))
        assert problems == []

    def test_custom_rules(self, pool: Pool) -> None:
        engine = RuleEngine(rules=[PhRule()])
        problems = engine.evaluate(make_state(pool, PoolReading(ph=8.0, orp=600.0)))
        # Only pH rule should fire, not sanitizer
        assert all(p.code in ("ph_too_high", "ph_too_low") for p in problems)

    def test_returns_list_of_problem_instances(self, pool: Pool) -> None:
        engine = RuleEngine(rules=[PhRule()])
        problems = engine.evaluate(make_state(pool, PoolReading(ph=8.5)))
        assert all(isinstance(p, Problem) for p in problems)
