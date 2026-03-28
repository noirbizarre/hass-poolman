"""Tests for the rule engine."""

from __future__ import annotations

from custom_components.poolman.domain.model import (
    Pool,
    PoolMode,
    PoolReading,
    RecommendationPriority,
    RecommendationType,
)
from custom_components.poolman.domain.rules import (
    AlgaeRiskRule,
    ChlorineRule,
    FiltrationRule,
    PhRule,
    RuleEngine,
    TacRule,
)


class TestPhRule:
    """Tests for pH rule evaluation."""

    def test_good_ph_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.2)
        result = PhRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_high_ph_returns_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8)
        result = PhRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "ph_minus"
        assert result[0].type == RecommendationType.CHEMICAL

    def test_low_ph_returns_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(ph=6.6)
        result = PhRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "ph_plus"
        assert result[0].priority == RecommendationPriority.HIGH

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(ph=8.5)
        result = PhRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []


class TestChlorineRule:
    """Tests for chlorine rule evaluation."""

    def test_good_orp_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(orp=750.0)
        result = ChlorineRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_critical_orp_shock(self, pool: Pool) -> None:
        reading = PoolReading(orp=600.0)
        result = ChlorineRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.CRITICAL
        assert result[0].product == "chlore_choc"

    def test_low_orp_galet(self, pool: Pool) -> None:
        reading = PoolReading(orp=700.0)
        result = ChlorineRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "galet_chlore"


class TestFiltrationRule:
    """Tests for filtration rule evaluation."""

    def test_produces_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=26.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].type == RecommendationType.FILTRATION

    def test_no_temp_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading()
        result = FiltrationRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []


class TestTacRule:
    """Tests for TAC rule evaluation."""

    def test_tac_in_range_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(tac=120.0)
        result = TacRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_low_tac_recommends_tac_plus(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "tac_plus"


class TestAlgaeRiskRule:
    """Tests for algae risk detection."""

    def test_warm_and_low_orp_triggers(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.HIGH

    def test_cool_water_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=22.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_warm_but_good_orp_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=750.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_missing_data_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []


class TestRuleEngine:
    """Tests for the rule engine orchestration."""

    def test_default_rules_loaded(self) -> None:
        engine = RuleEngine()
        assert len(engine.rules) == 5

    def test_good_readings_produce_filtration_only(
        self, pool: Pool, good_reading: PoolReading
    ) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, good_reading, PoolMode.RUNNING)
        # Good readings should only produce filtration recommendation
        types = {r.type for r in results}
        assert RecommendationType.FILTRATION in types
        # No chemical or alert recommendations
        assert all(
            r.priority in (RecommendationPriority.LOW, RecommendationPriority.MEDIUM)
            for r in results
        )

    def test_bad_readings_produce_multiple(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.RUNNING)
        assert len(results) > 1

    def test_results_sorted_by_priority(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.RUNNING)
        priorities = [r.priority for r in results]
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }
        numeric = [priority_order[p] for p in priorities]
        assert numeric == sorted(numeric)

    def test_winter_passive_no_recommendations(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.WINTER_PASSIVE)
        # Only filtration rule produces output in passive winter
        assert all(r.type == RecommendationType.FILTRATION for r in results)

    def test_empty_readings_minimal_output(self, pool: Pool) -> None:
        engine = RuleEngine()
        reading = PoolReading()
        results = engine.evaluate(pool, reading, PoolMode.RUNNING)
        # No sensor data -> no recommendations
        assert results == []

    def test_custom_rules(self, pool: Pool) -> None:
        engine = RuleEngine(rules=[PhRule()])
        reading = PoolReading(ph=8.0, orp=600.0)
        results = engine.evaluate(pool, reading, PoolMode.RUNNING)
        # Only pH rule should fire, not chlorine
        assert all(r.product in ("ph_minus", "ph_plus") for r in results)
