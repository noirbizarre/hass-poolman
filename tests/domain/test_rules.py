"""Tests for the rule engine."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import (
    ActionKind,
    Pool,
    PoolMode,
    PoolReading,
    RecommendationPriority,
    RecommendationType,
    TreatmentType,
)
from custom_components.poolman.domain.rules import (
    AlgaeRiskRule,
    CyaRule,
    FiltrationRule,
    HardnessRule,
    PhRule,
    RuleEngine,
    SanitizerRule,
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
        assert result[0].kind == ActionKind.SUGGESTION

    def test_low_ph_returns_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(ph=6.6)
        result = PhRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "ph_plus"
        assert result[0].priority == RecommendationPriority.HIGH
        assert result[0].kind == ActionKind.REQUIREMENT

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(ph=8.5)
        result = PhRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_slightly_off_ph_returns_low_priority(self, pool: Pool) -> None:
        """pH slightly off target (within min/max, delta <= tolerance*3) -> LOW."""
        # PH_TARGET=7.2, PH_TOLERANCE=0.1, so delta <= 0.3 and within 6.8-7.8
        reading = PoolReading(ph=7.4)  # delta=0.2
        result = PhRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.LOW


class TestSanitizerRule:
    """Tests for sanitizer rule evaluation across treatment types."""

    def test_good_orp_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(orp=750.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_chlorine_critical_orp_shock(self, pool: Pool) -> None:
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.CRITICAL
        assert result[0].product == "chlore_choc"
        assert result[0].kind == ActionKind.REQUIREMENT

    def test_chlorine_low_orp_galet(self, pool: Pool) -> None:
        reading = PoolReading(orp=700.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "galet_chlore"
        assert result[0].kind == ActionKind.SUGGESTION

    def test_salt_low_orp_recommends_salt(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        reading = PoolReading(orp=700.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "salt"
        assert "salt level" in result[0].message.lower()

    def test_salt_critical_orp_shock(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.CRITICAL
        # Salt pools still use shock chlorination in emergencies
        assert result[0].product == "chlore_choc"

    def test_bromine_low_orp_recommends_bromine_tablet(self) -> None:
        pool = Pool(
            name="Bromine Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.BROMINE,
        )
        reading = PoolReading(orp=700.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "bromine_tablet"

    def test_bromine_critical_orp_shock(self) -> None:
        pool = Pool(
            name="Bromine Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.BROMINE,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "bromine_shock"

    def test_active_oxygen_low_orp_recommends_tablet(self) -> None:
        pool = Pool(
            name="O2 Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.ACTIVE_OXYGEN,
        )
        reading = PoolReading(orp=700.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "active_oxygen_tablet"

    def test_active_oxygen_critical_orp_shock(self) -> None:
        pool = Pool(
            name="O2 Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.ACTIVE_OXYGEN,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "active_oxygen_activator"

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    @pytest.mark.parametrize("treatment", list(TreatmentType))
    def test_high_orp_returns_neutralizer_for_all_treatments(
        self, treatment: TreatmentType
    ) -> None:
        pool = Pool(
            name="Test Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=treatment,
        )
        reading = PoolReading(orp=950.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "neutralizer"


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

    def test_low_filtration_hours_returns_low_priority(self, pool: Pool) -> None:
        """When filtration hours < 12 in running mode, priority should be LOW."""
        reading = PoolReading(temp_c=20.0)  # 20/2 = 10h < 12
        result = FiltrationRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.LOW


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

    def test_high_tac_recommends_ph_minus(self, pool: Pool) -> None:
        """TAC above max should recommend using pH- to lower alkalinity."""
        reading = PoolReading(tac=160.0)  # TAC_MAX = 150
        result = TacRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.LOW
        assert "too high" in result[0].message.lower()


class TestAlgaeRiskRule:
    """Tests for algae risk detection."""

    def test_warm_and_low_orp_triggers(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].priority == RecommendationPriority.HIGH
        assert result[0].kind == ActionKind.REQUIREMENT

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
        assert len(engine.rules) == 7

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
        # Only pH rule should fire, not sanitizer
        assert all(r.product in ("ph_minus", "ph_plus") for r in results)


class TestCyaRule:
    """Tests for CYA (cyanuric acid) rule evaluation."""

    def test_cya_in_range_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(cya=40.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_cya_too_low_recommends_stabilizer(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "stabilizer"
        assert result[0].type == RecommendationType.CHEMICAL
        assert result[0].priority == RecommendationPriority.MEDIUM
        assert result[0].kind == ActionKind.REQUIREMENT
        assert result[0].quantity_g is not None
        assert result[0].quantity_g > 0

    def test_cya_too_high_recommends_drain(self, pool: Pool) -> None:
        reading = PoolReading(cya=100.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].type == RecommendationType.ALERT
        assert result[0].priority == RecommendationPriority.LOW
        assert result[0].kind == ActionKind.REQUIREMENT
        assert result[0].product is None
        assert "drain" in result[0].message.lower()

    def test_cya_none_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(cya=None)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_cya_at_min_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(cya=20.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_cya_at_max_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(cya=75.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []


class TestHardnessRule:
    """Tests for calcium hardness rule evaluation."""

    def test_hardness_in_range_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(hardness=250.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_hardness_too_low_recommends_increaser(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].product == "calcium_hardness_increaser"
        assert result[0].type == RecommendationType.CHEMICAL
        assert result[0].priority == RecommendationPriority.MEDIUM
        assert result[0].kind == ActionKind.REQUIREMENT
        assert result[0].quantity_g is not None
        assert result[0].quantity_g > 0

    def test_hardness_too_high_recommends_drain(self, pool: Pool) -> None:
        reading = PoolReading(hardness=500.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert len(result) == 1
        assert result[0].type == RecommendationType.ALERT
        assert result[0].priority == RecommendationPriority.LOW
        assert result[0].kind == ActionKind.REQUIREMENT
        assert result[0].product is None
        assert "drain" in result[0].message.lower()

    def test_hardness_none_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(hardness=None)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_hardness_at_min_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(hardness=150.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []

    def test_hardness_at_max_no_recommendation(self, pool: Pool) -> None:
        reading = PoolReading(hardness=400.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.RUNNING)
        assert result == []
