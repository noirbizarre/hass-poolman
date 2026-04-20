"""Tests for the rule engine.

Rules now return :class:`~custom_components.poolman.domain.problem.Problem`
objects instead of legacy ``Recommendation`` objects.  Each test verifies
the problem ``code``, ``severity``, ``metric``, ``value``, and ``message``
fields.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.poolman.domain.model import (
    ManualMeasure,
    MeasureParameter,
    Pool,
    PoolMode,
    PoolReading,
    TreatmentType,
)
from custom_components.poolman.domain.problem import MetricName, Problem, Severity
from custom_components.poolman.domain.rules import (
    AlgaeRiskRule,
    CalibrationRule,
    CyaRule,
    FiltrationRule,
    FreeChlorineRule,
    HardnessRule,
    PhRule,
    RuleEngine,
    SaltRule,
    SanitizerRule,
    TacRule,
    TdsRule,
)


class TestPhRule:
    """Tests for pH rule evaluation."""

    def test_good_ph_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.2)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_high_ph_returns_problem(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "ph_too_high"
        assert result[0].metric == MetricName.PH
        assert result[0].value == pytest.approx(7.8)

    def test_low_ph_returns_critical_problem(self, pool: Pool) -> None:
        reading = PoolReading(ph=6.6)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "ph_too_low"
        assert result[0].severity == Severity.CRITICAL
        assert result[0].metric == MetricName.PH

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(ph=8.5)
        result = PhRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        """pH rule should still evaluate in active winter mode (equipment protection)."""
        reading = PoolReading(ph=7.8)
        result = PhRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert len(result) == 1
        assert result[0].code == "ph_too_high"

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        """pH rule should still evaluate in hibernating mode."""
        reading = PoolReading(ph=7.8)
        result = PhRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "ph_too_high"

    def test_activating_evaluates(self, pool: Pool) -> None:
        """pH rule should still evaluate in activating mode."""
        reading = PoolReading(ph=7.8)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "ph_too_high"

    def test_slightly_off_ph_returns_low_severity(self, pool: Pool) -> None:
        """pH slightly off target (within min/max, delta <= tolerance*3) -> LOW severity."""
        # PH_TARGET=7.2, PH_TOLERANCE=0.1, so delta <= 0.3 and within 6.8-7.8
        reading = PoolReading(ph=7.4)  # delta=0.2
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.LOW

    def test_ph_outside_range_returns_critical_severity(self, pool: Pool) -> None:
        """pH outside min-max range -> CRITICAL severity."""
        reading = PoolReading(ph=8.2)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_ph_medium_deviation_returns_medium_severity(self, pool: Pool) -> None:
        """pH delta > 3x tolerance but within range -> MEDIUM severity."""
        # PH_TARGET=7.2, tolerance=0.1, 3x=0.3, max=7.8
        # reading 7.6 -> delta=0.4 > 0.3, still within 6.8-7.8
        reading = PoolReading(ph=7.6)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_none_ph_skips(self, pool: Pool) -> None:
        reading = PoolReading()
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_expected_range_set(self, pool: Pool) -> None:
        reading = PoolReading(ph=8.5)
        result = PhRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result[0].expected_range is not None
        low, high = result[0].expected_range
        assert low < 7.0
        assert high > 7.5


class TestSanitizerRule:
    """Tests for sanitizer rule evaluation across treatment types."""

    def test_good_orp_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(orp=750.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_critical_orp_returns_critical_problem(self, pool: Pool) -> None:
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "orp_too_low"
        assert result[0].severity == Severity.CRITICAL
        assert result[0].metric == MetricName.ORP

    def test_medium_low_orp_returns_medium_problem(self, pool: Pool) -> None:
        reading = PoolReading(orp=700.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "orp_too_low"
        assert result[0].severity == Severity.MEDIUM

    def test_high_orp_returns_orp_too_high_problem(self, pool: Pool) -> None:
        reading = PoolReading(orp=950.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "orp_too_high"
        assert result[0].metric == MetricName.ORP

    def test_salt_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_bromine_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="Bromine Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.BROMINE,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_active_oxygen_critical_orp_returns_critical_problem(self) -> None:
        pool = Pool(
            name="O2 Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.ACTIVE_OXYGEN,
        )
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        """Sanitizer rule should skip in active winter mode."""
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        """Sanitizer rule should still evaluate in hibernating mode."""
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_activating_evaluates(self, pool: Pool) -> None:
        """Sanitizer rule should still evaluate in activating mode."""
        reading = PoolReading(orp=600.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    @pytest.mark.parametrize("treatment", list(TreatmentType))
    def test_high_orp_returns_too_high_code_for_all_treatments(
        self, treatment: TreatmentType
    ) -> None:
        pool = Pool(
            name="Test Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=treatment,
        )
        reading = PoolReading(orp=950.0)
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "orp_too_high"

    def test_none_orp_skips(self, pool: Pool) -> None:
        reading = PoolReading()
        result = SanitizerRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestFiltrationRule:
    """Tests for filtration rule evaluation."""

    def test_produces_problem(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=26.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "filtration_required"
        assert result[0].metric is None
        assert result[0].value is not None

    def test_no_temp_no_problem(self, pool: Pool) -> None:
        reading = PoolReading()
        result = FiltrationRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_low_filtration_hours_returns_low_severity(self, pool: Pool) -> None:
        """When filtration hours < 12 in running mode, severity should be LOW."""
        reading = PoolReading(temp_c=20.0)  # 20/2 = 10h < 12
        result = FiltrationRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.LOW

    def test_high_filtration_hours_returns_medium_severity(self, pool: Pool) -> None:
        """When filtration hours >= 12, severity should be MEDIUM."""
        reading = PoolReading(temp_c=26.0)  # 26/2 = 13h >= 12
        result = FiltrationRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        """Filtration rule should still evaluate in active winter mode."""
        reading = PoolReading(temp_c=15.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert len(result) == 1
        assert result[0].code == "filtration_required"

    def test_hibernating_produces_problem(self, pool: Pool) -> None:
        """Hibernating mode should produce a filtration problem."""
        reading = PoolReading(temp_c=26.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "filtration_required"

    def test_activating_produces_problem(self, pool: Pool) -> None:
        """Activating mode should produce a filtration problem."""
        reading = PoolReading(temp_c=26.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "filtration_required"

    def test_winter_passive_skips(self, pool: Pool) -> None:
        """WINTER_PASSIVE mode should produce no filtration problem."""
        reading = PoolReading(temp_c=26.0)
        result = FiltrationRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []


class TestTacRule:
    """Tests for TAC rule evaluation."""

    def test_tac_in_range_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(tac=120.0)
        result = TacRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_low_tac_returns_problem(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "alkalinity_too_low"
        assert result[0].metric == MetricName.ALKALINITY
        assert result[0].severity == Severity.MEDIUM

    def test_high_tac_returns_low_severity_problem(self, pool: Pool) -> None:
        """TAC above max should return a LOW severity problem."""
        reading = PoolReading(tac=160.0)
        result = TacRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "alkalinity_too_high"
        assert result[0].severity == Severity.LOW
        assert "too high" in result[0].message.lower()

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "alkalinity_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(tac=50.0)
        result = TacRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "alkalinity_too_low"

    def test_none_tac_skips(self, pool: Pool) -> None:
        reading = PoolReading()
        result = TacRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestAlgaeRiskRule:
    """Tests for algae risk detection."""

    def test_warm_and_low_orp_triggers_critical(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "algae_risk"
        assert result[0].severity == Severity.CRITICAL
        assert result[0].metric == MetricName.ORP

    def test_cool_water_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=22.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_warm_but_good_orp_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=750.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_missing_data_no_risk(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL

    def test_message_includes_temp_and_orp(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=30.0, orp=650.0)
        result = AlgaeRiskRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert "30.0" in result[0].message
        assert "650" in result[0].message


class TestFreeChlorineRule:
    """Tests for free chlorine rule evaluation."""

    def test_in_range_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=2.0)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_too_low_returns_critical_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "chlorine_too_low"
        assert result[0].severity == Severity.CRITICAL
        assert result[0].metric == MetricName.CHLORINE
        assert result[0].value == pytest.approx(0.5)

    def test_too_high_returns_low_severity_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=4.0)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "chlorine_too_high"
        assert result[0].severity == Severity.LOW
        assert result[0].metric == MetricName.CHLORINE

    def test_none_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=None)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "chlorine_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "chlorine_too_low"

    def test_at_min_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=1.0)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_at_max_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(free_chlorine=3.0)
        result = FreeChlorineRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestCyaRule:
    """Tests for CYA (cyanuric acid) rule evaluation."""

    def test_cya_in_range_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=40.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_cya_too_low_returns_medium_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "cya_too_low"
        assert result[0].metric == MetricName.CYA
        assert result[0].severity == Severity.MEDIUM
        assert result[0].value == pytest.approx(10.0)

    def test_cya_too_high_returns_low_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=100.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "cya_too_high"
        assert result[0].severity == Severity.LOW
        assert "drain" in result[0].message.lower() or "too high" in result[0].message.lower()

    def test_cya_none_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=None)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "cya_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "cya_too_low"

    def test_cya_at_min_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=20.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_cya_at_max_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(cya=75.0)
        result = CyaRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestHardnessRule:
    """Tests for calcium hardness rule evaluation."""

    def test_hardness_in_range_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=250.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_hardness_too_low_returns_medium_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "hardness_too_low"
        assert result[0].metric == MetricName.HARDNESS
        assert result[0].severity == Severity.MEDIUM
        assert result[0].value == pytest.approx(100.0)

    def test_hardness_too_high_returns_low_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=500.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "hardness_too_high"
        assert result[0].severity == Severity.LOW

    def test_hardness_none_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=None)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "hardness_too_low"

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "hardness_too_low"

    def test_hardness_at_min_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=150.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_hardness_at_max_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(hardness=400.0)
        result = HardnessRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestSaltRule:
    """Tests for salt level rule evaluation."""

    def _make_salt_pool(self) -> Pool:
        return Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )

    def test_salt_in_range_no_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=3200.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_salt_too_low_returns_medium_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "salt_too_low"
        assert result[0].metric == MetricName.SALT
        assert result[0].severity == Severity.MEDIUM
        assert result[0].value == pytest.approx(2000.0)

    def test_salt_too_high_returns_low_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=4000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "salt_too_high"
        assert result[0].severity == Severity.LOW

    def test_salt_none_no_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=None)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_non_salt_treatment_skips(self, pool: Pool) -> None:
        """SaltRule should skip for non-salt-electrolysis treatment types."""
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "salt_too_low"

    def test_activating_evaluates(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2000.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "salt_too_low"

    def test_salt_at_min_no_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=2700.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_salt_at_max_no_problem(self) -> None:
        pool = self._make_salt_pool()
        reading = PoolReading(salt=3400.0)
        result = SaltRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


class TestTdsRule:
    """Tests for TDS (Total Dissolved Solids) rule evaluation."""

    def test_tds_in_range_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=500.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_tds_too_high_returns_medium_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "tds_too_high"
        assert result[0].metric == MetricName.TDS
        assert result[0].severity == Severity.MEDIUM

    def test_tds_too_low_returns_low_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=100.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert len(result) == 1
        assert result[0].code == "tds_too_low"
        assert result[0].severity == Severity.LOW

    def test_tds_none_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=None)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_salt_electrolysis_skips(self) -> None:
        pool = Pool(
            name="Salt Pool",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            treatment=TreatmentType.SALT_ELECTROLYSIS,
        )
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.WINTER_PASSIVE)
        assert result == []

    def test_winter_active_skips(self, pool: Pool) -> None:
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.WINTER_ACTIVE)
        assert result == []

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.HIBERNATING)
        assert len(result) == 1
        assert result[0].code == "tds_too_high"

    def test_activating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(tds=2000.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVATING)
        assert len(result) == 1
        assert result[0].code == "tds_too_high"

    def test_tds_at_min_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=250.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_tds_at_max_no_problem(self, pool: Pool) -> None:
        reading = PoolReading(tds=1500.0)
        result = TdsRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []


def _ts() -> datetime:
    """Return a fixed timestamp for test measures."""
    return datetime(2025, 7, 15, 10, 0, tzinfo=UTC)


class TestCalibrationRule:
    """Tests for CalibrationRule deviation detection."""

    def test_no_manual_measures_no_problem(self, pool: Pool) -> None:
        """No problems when there are no manual measures."""
        reading = PoolReading(ph=7.2, orp=750.0)
        result = CalibrationRule().evaluate(pool, reading, PoolMode.ACTIVE)
        assert result == []

    def test_no_deviation_no_problem(self, pool: Pool) -> None:
        """No problem when sensor and manual values are close."""
        reading = PoolReading(ph=7.2)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.1, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert result == []

    def test_ph_deviation_generates_problem(self, pool: Pool) -> None:
        """pH deviation exceeding threshold should generate a calibration problem."""
        reading = PoolReading(ph=7.8)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 1
        assert result[0].code == "calibration_ph"
        assert result[0].severity == Severity.LOW
        assert result[0].metric is None  # calibration problems don't map to a specific metric
        assert "pH" in result[0].message
        assert "7.8" in result[0].message
        assert "7.2" in result[0].message

    def test_orp_deviation_generates_problem(self, pool: Pool) -> None:
        reading = PoolReading(orp=810.0)
        measures = {
            MeasureParameter.ORP: ManualMeasure(
                parameter=MeasureParameter.ORP, value=750.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 1
        assert result[0].code == "calibration_orp"
        assert "ORP" in result[0].message

    def test_temperature_deviation_generates_problem(self, pool: Pool) -> None:
        reading = PoolReading(temp_c=28.5)
        measures = {
            MeasureParameter.TEMPERATURE: ManualMeasure(
                parameter=MeasureParameter.TEMPERATURE, value=26.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 1
        assert "temperature" in result[0].message

    def test_sensor_none_skipped(self, pool: Pool) -> None:
        reading = PoolReading(ph=None)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert result == []

    def test_winter_passive_skips(self, pool: Pool) -> None:
        reading = PoolReading(ph=8.0)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.WINTER_PASSIVE, manual_measures=measures
        )
        assert result == []

    def test_multiple_deviations(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8, orp=810.0, temp_c=30.0)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
            MeasureParameter.ORP: ManualMeasure(
                parameter=MeasureParameter.ORP, value=750.0, measured_at=_ts()
            ),
            MeasureParameter.TEMPERATURE: ManualMeasure(
                parameter=MeasureParameter.TEMPERATURE, value=26.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 3

    def test_deviation_at_threshold_no_problem(self, pool: Pool) -> None:
        """Deviation exactly at threshold should NOT generate a problem."""
        reading = PoolReading(ph=7.5)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        # 0.3 == threshold, not > threshold
        assert result == []

    def test_tac_deviation(self, pool: Pool) -> None:
        reading = PoolReading(tac=145.0)
        measures = {
            MeasureParameter.TAC: ManualMeasure(
                parameter=MeasureParameter.TAC, value=120.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 1
        assert "TAC" in result[0].message

    def test_salt_deviation(self, pool: Pool) -> None:
        reading = PoolReading(salt=3400.0)
        measures = {
            MeasureParameter.SALT: ManualMeasure(
                parameter=MeasureParameter.SALT, value=3200.0, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.ACTIVE, manual_measures=measures
        )
        assert len(result) == 1
        assert "salt" in result[0].message

    def test_winter_active_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.WINTER_ACTIVE, manual_measures=measures
        )
        assert len(result) == 1

    def test_hibernating_evaluates(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=_ts()
            ),
        }
        result = CalibrationRule().evaluate(
            pool, reading, PoolMode.HIBERNATING, manual_measures=measures
        )
        assert len(result) == 1


class TestRuleEngine:
    """Tests for the rule engine orchestration."""

    def test_default_rules_loaded(self) -> None:
        engine = RuleEngine()
        assert len(engine.rules) == 11

    def test_good_readings_produce_filtration_only(
        self, pool: Pool, good_reading: PoolReading
    ) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, good_reading, PoolMode.ACTIVE)
        # Good readings should only produce filtration problem
        codes = {r.code for r in results}
        assert "filtration_required" in codes
        # No chemical problems
        assert not any(
            r.code in ("ph_too_high", "ph_too_low", "orp_too_low", "orp_too_high") for r in results
        )

    def test_bad_readings_produce_multiple_problems(
        self, pool: Pool, bad_reading: PoolReading
    ) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.ACTIVE)
        assert len(results) > 1

    def test_results_sorted_by_severity(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.ACTIVE)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.MEDIUM: 1,
            Severity.LOW: 2,
        }
        numeric = [severity_order[r.severity] for r in results]
        assert numeric == sorted(numeric)

    def test_winter_passive_minimal_problems(self, pool: Pool, bad_reading: PoolReading) -> None:
        engine = RuleEngine()
        results = engine.evaluate(pool, bad_reading, PoolMode.WINTER_PASSIVE)
        # Only filtration and pH rules produce output in passive winter
        for r in results:
            assert r.code in ("filtration_required", "ph_too_high", "ph_too_low")

    def test_empty_readings_no_problems(self, pool: Pool) -> None:
        engine = RuleEngine()
        reading = PoolReading()
        results = engine.evaluate(pool, reading, PoolMode.ACTIVE)
        assert results == []

    def test_custom_rules(self, pool: Pool) -> None:
        engine = RuleEngine(rules=[PhRule()])
        reading = PoolReading(ph=8.0, orp=600.0)
        results = engine.evaluate(pool, reading, PoolMode.ACTIVE)
        # Only pH rule should fire, not sanitizer
        assert all(r.code in ("ph_too_high", "ph_too_low") for r in results)

    def test_returns_list_of_problem_instances(self, pool: Pool) -> None:
        engine = RuleEngine(rules=[PhRule()])
        reading = PoolReading(ph=8.5)
        results = engine.evaluate(pool, reading, PoolMode.ACTIVE)
        assert all(isinstance(r, Problem) for r in results)
