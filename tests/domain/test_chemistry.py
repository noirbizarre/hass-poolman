"""Tests for pool chemistry calculations."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.chemistry import (
    CYA_MAX,
    CYA_MIN,
    CYA_TARGET,
    FREE_CHLORINE_MAX,
    FREE_CHLORINE_MIN,
    FREE_CHLORINE_TARGET,
    HARDNESS_MAX,
    HARDNESS_MIN,
    HARDNESS_TARGET,
    ORP_MAX,
    ORP_MIN_CRITICAL,
    ORP_TARGET,
    PH_MAX,
    PH_MIN,
    PH_TARGET,
    TAC_MAX,
    TAC_MIN,
    TAC_TARGET,
    compute_chemistry_report,
    compute_cya_adjustment,
    compute_free_chlorine_adjustment,
    compute_hardness_adjustment,
    compute_parameter_status,
    compute_ph_adjustment,
    compute_sanitizer_status,
    compute_tac_adjustment,
    compute_water_quality_score,
)
from custom_components.poolman.domain.model import (
    ChemicalProduct,
    ChemistryStatus,
    Pool,
    PoolReading,
    Severity,
    TreatmentType,
)


class TestPhAdjustment:
    """Tests for pH adjustment calculation."""

    def test_ph_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.2)
        assert compute_ph_adjustment(pool, reading) is None

    def test_ph_slightly_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.25)
        assert compute_ph_adjustment(pool, reading) is None

    def test_ph_too_high_recommends_ph_minus(self, pool: Pool) -> None:
        reading = PoolReading(ph=7.8)
        result = compute_ph_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.PH_MINUS
        assert result.quantity_g is not None
        assert result.quantity_g > 0

    def test_ph_too_low_recommends_ph_plus(self, pool: Pool) -> None:
        reading = PoolReading(ph=6.8)
        result = compute_ph_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.PH_PLUS
        assert result.quantity_g is not None
        assert result.quantity_g > 0

    def test_ph_none_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(ph=None)
        assert compute_ph_adjustment(pool, reading) is None

    def test_quantity_scales_with_volume(self) -> None:
        small_pool = Pool(name="Small", volume_m3=20.0, pump_flow_m3h=5.0)
        large_pool = Pool(name="Large", volume_m3=100.0, pump_flow_m3h=20.0)
        reading = PoolReading(ph=7.8)

        small_result = compute_ph_adjustment(small_pool, reading)
        large_result = compute_ph_adjustment(large_pool, reading)

        assert small_result is not None
        assert large_result is not None
        assert large_result.quantity_g is not None
        assert small_result.quantity_g is not None
        assert large_result.quantity_g > small_result.quantity_g

    def test_quantity_scales_with_delta(self, pool: Pool) -> None:
        slight = PoolReading(ph=PH_TARGET + 0.2)
        severe = PoolReading(ph=PH_TARGET + 0.6)

        slight_result = compute_ph_adjustment(pool, slight)
        severe_result = compute_ph_adjustment(pool, severe)

        assert slight_result is not None
        assert severe_result is not None
        assert severe_result.quantity_g is not None
        assert slight_result.quantity_g is not None
        assert severe_result.quantity_g > slight_result.quantity_g


class TestSanitizerStatus:
    """Tests for sanitizer/ORP evaluation across treatment types."""

    def test_orp_in_range_returns_none(self) -> None:
        reading = PoolReading(orp=750.0)
        assert compute_sanitizer_status(reading) is None

    def test_orp_none_returns_none(self) -> None:
        reading = PoolReading(orp=None)
        assert compute_sanitizer_status(reading) is None

    # Chlorine treatment (default)
    def test_chlorine_orp_critically_low(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_sanitizer_status(reading, TreatmentType.CHLORINE)
        assert result is not None
        assert result.product == ChemicalProduct.CHLORE_CHOC
        assert result.severity == Severity.CRITICAL

    def test_chlorine_orp_low(self) -> None:
        reading = PoolReading(orp=700.0)
        result = compute_sanitizer_status(reading, TreatmentType.CHLORINE)
        assert result is not None
        assert result.product == ChemicalProduct.GALET_CHLORE
        assert result.severity == Severity.MEDIUM

    def test_chlorine_orp_too_high(self) -> None:
        reading = PoolReading(orp=950.0)
        result = compute_sanitizer_status(reading, TreatmentType.CHLORINE)
        assert result is not None
        assert result.product == ChemicalProduct.NEUTRALIZER

    # Salt electrolysis treatment
    def test_salt_orp_critically_low(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_sanitizer_status(reading, TreatmentType.SALT_ELECTROLYSIS)
        assert result is not None
        assert result.product == ChemicalProduct.CHLORE_CHOC
        assert result.severity == Severity.CRITICAL

    def test_salt_orp_low(self) -> None:
        reading = PoolReading(orp=700.0)
        result = compute_sanitizer_status(reading, TreatmentType.SALT_ELECTROLYSIS)
        assert result is not None
        assert result.product == ChemicalProduct.SALT
        assert result.severity == Severity.MEDIUM

    # Bromine treatment
    def test_bromine_orp_critically_low(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_sanitizer_status(reading, TreatmentType.BROMINE)
        assert result is not None
        assert result.product == ChemicalProduct.BROMINE_SHOCK
        assert result.severity == Severity.CRITICAL

    def test_bromine_orp_low(self) -> None:
        reading = PoolReading(orp=700.0)
        result = compute_sanitizer_status(reading, TreatmentType.BROMINE)
        assert result is not None
        assert result.product == ChemicalProduct.BROMINE_TABLET
        assert result.severity == Severity.MEDIUM

    # Active oxygen treatment
    def test_active_oxygen_orp_critically_low(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_sanitizer_status(reading, TreatmentType.ACTIVE_OXYGEN)
        assert result is not None
        assert result.product == ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR
        assert result.severity == Severity.CRITICAL

    def test_active_oxygen_orp_low(self) -> None:
        reading = PoolReading(orp=700.0)
        result = compute_sanitizer_status(reading, TreatmentType.ACTIVE_OXYGEN)
        assert result is not None
        assert result.product == ChemicalProduct.ACTIVE_OXYGEN_TABLET
        assert result.severity == Severity.MEDIUM

    # Default treatment is chlorine
    def test_default_treatment_is_chlorine(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_sanitizer_status(reading)
        assert result is not None
        assert result.product == ChemicalProduct.CHLORE_CHOC

    # All treatments return neutralizer for high ORP
    @pytest.mark.parametrize("treatment", list(TreatmentType))
    def test_all_treatments_return_neutralizer_for_high_orp(self, treatment: TreatmentType) -> None:
        reading = PoolReading(orp=950.0)
        result = compute_sanitizer_status(reading, treatment)
        assert result is not None
        assert result.product == ChemicalProduct.NEUTRALIZER


class TestTacAdjustment:
    """Tests for TAC adjustment calculation."""

    def test_tac_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(tac=120.0)
        assert compute_tac_adjustment(pool, reading) is None

    def test_tac_too_low_recommends_tac_plus(self, pool: Pool) -> None:
        reading = PoolReading(tac=60.0)
        result = compute_tac_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.TAC_PLUS
        assert result.quantity_g is not None
        assert result.quantity_g > 0

    def test_tac_too_high_recommends_ph_minus(self, pool: Pool) -> None:
        reading = PoolReading(tac=180.0)
        result = compute_tac_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.PH_MINUS

    def test_tac_none_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(tac=None)
        assert compute_tac_adjustment(pool, reading) is None


class TestWaterQualityScore:
    """Tests for overall water quality score."""

    def test_perfect_readings(self, good_reading: PoolReading) -> None:
        score = compute_water_quality_score(good_reading)
        assert score is not None
        assert score >= 80

    def test_bad_readings(self, bad_reading: PoolReading) -> None:
        score = compute_water_quality_score(bad_reading)
        assert score is not None
        assert score < 50

    def test_no_readings(self, empty_reading: PoolReading) -> None:
        assert compute_water_quality_score(empty_reading) is None

    def test_partial_readings(self) -> None:
        reading = PoolReading(ph=7.2)
        score = compute_water_quality_score(reading)
        assert score is not None
        assert 0 <= score <= 100

    @pytest.mark.parametrize(
        ("ph", "expected_min", "expected_max"),
        [
            (7.2, 90, 100),  # At target
            (7.0, 50, 90),  # Slightly off
            (6.5, 0, 10),  # Out of range
        ],
    )
    def test_score_varies_with_ph(self, ph: float, expected_min: int, expected_max: int) -> None:
        reading = PoolReading(ph=ph)
        score = compute_water_quality_score(reading)
        assert score is not None
        assert expected_min <= score <= expected_max


class TestParameterStatus:
    """Tests for individual parameter status computation."""

    def test_at_target_returns_good(self) -> None:
        report = compute_parameter_status(PH_TARGET, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.GOOD
        assert report.score == 100

    def test_inner_half_returns_good(self) -> None:
        # pH 7.0 is midpoint between min (6.8) and target (7.2) -> score = 50
        report = compute_parameter_status(7.0, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.GOOD
        assert report.score >= 50

    def test_outer_half_returns_warning(self) -> None:
        # pH 6.9 is in range but closer to boundary than target
        report = compute_parameter_status(6.9, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.WARNING
        assert 0 < report.score < 50

    def test_at_min_boundary_returns_warning(self) -> None:
        # At exact minimum, score is 0 but still within range
        report = compute_parameter_status(PH_MIN, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.WARNING
        assert report.score == 0

    def test_at_max_boundary_returns_warning(self) -> None:
        # At exact maximum, score is 0 but still within range
        report = compute_parameter_status(PH_MAX, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.WARNING
        assert report.score == 0

    def test_below_min_returns_bad(self) -> None:
        report = compute_parameter_status(6.5, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.BAD
        assert report.score == 0

    def test_above_max_returns_bad(self) -> None:
        report = compute_parameter_status(8.5, PH_MIN, PH_TARGET, PH_MAX)
        assert report.status == ChemistryStatus.BAD
        assert report.score == 0

    def test_report_contains_range_info(self) -> None:
        report = compute_parameter_status(7.2, PH_MIN, PH_TARGET, PH_MAX)
        assert report.value == 7.2
        assert report.target == PH_TARGET
        assert report.minimum == PH_MIN
        assert report.maximum == PH_MAX

    @pytest.mark.parametrize(
        ("value", "minimum", "target", "maximum", "expected_status"),
        [
            # ORP ranges
            (ORP_TARGET, ORP_MIN_CRITICAL, ORP_TARGET, ORP_MAX, ChemistryStatus.GOOD),
            (600, ORP_MIN_CRITICAL, ORP_TARGET, ORP_MAX, ChemistryStatus.BAD),
            (950, ORP_MIN_CRITICAL, ORP_TARGET, ORP_MAX, ChemistryStatus.BAD),
            # TAC ranges
            (TAC_TARGET, TAC_MIN, TAC_TARGET, TAC_MAX, ChemistryStatus.GOOD),
            (60, TAC_MIN, TAC_TARGET, TAC_MAX, ChemistryStatus.BAD),
            # CYA ranges
            (CYA_TARGET, CYA_MIN, CYA_TARGET, CYA_MAX, ChemistryStatus.GOOD),
            (10, CYA_MIN, CYA_TARGET, CYA_MAX, ChemistryStatus.BAD),
            # Hardness ranges
            (HARDNESS_TARGET, HARDNESS_MIN, HARDNESS_TARGET, HARDNESS_MAX, ChemistryStatus.GOOD),
            (100, HARDNESS_MIN, HARDNESS_TARGET, HARDNESS_MAX, ChemistryStatus.BAD),
            # Free chlorine ranges
            (
                FREE_CHLORINE_TARGET,
                FREE_CHLORINE_MIN,
                FREE_CHLORINE_TARGET,
                FREE_CHLORINE_MAX,
                ChemistryStatus.GOOD,
            ),
            (0.5, FREE_CHLORINE_MIN, FREE_CHLORINE_TARGET, FREE_CHLORINE_MAX, ChemistryStatus.BAD),
        ],
    )
    def test_status_across_parameters(
        self,
        value: float,
        minimum: float,
        target: float,
        maximum: float,
        expected_status: ChemistryStatus,
    ) -> None:
        report = compute_parameter_status(value, minimum, target, maximum)
        assert report.status == expected_status


class TestChemistryReport:
    """Tests for the full chemistry status report."""

    def test_good_reading_all_good(self, good_reading: PoolReading) -> None:
        report = compute_chemistry_report(good_reading)
        assert report.ph is not None
        assert report.ph.status == ChemistryStatus.GOOD
        assert report.orp is not None
        assert report.orp.status == ChemistryStatus.GOOD
        assert report.free_chlorine is not None
        assert report.free_chlorine.status == ChemistryStatus.GOOD
        assert report.tac is not None
        assert report.tac.status == ChemistryStatus.GOOD
        assert report.cya is not None
        assert report.cya.status == ChemistryStatus.GOOD
        assert report.hardness is not None
        assert report.hardness.status == ChemistryStatus.GOOD

    def test_bad_reading_all_bad(self, bad_reading: PoolReading) -> None:
        report = compute_chemistry_report(bad_reading)
        assert report.ph is not None
        assert report.ph.status == ChemistryStatus.BAD
        assert report.orp is not None
        assert report.orp.status == ChemistryStatus.BAD
        assert report.free_chlorine is not None
        assert report.free_chlorine.status == ChemistryStatus.BAD
        assert report.tac is not None
        assert report.tac.status == ChemistryStatus.BAD
        assert report.hardness is not None
        assert report.hardness.status == ChemistryStatus.BAD

    def test_empty_reading_all_none(self, empty_reading: PoolReading) -> None:
        report = compute_chemistry_report(empty_reading)
        assert report.ph is None
        assert report.orp is None
        assert report.free_chlorine is None
        assert report.tac is None
        assert report.cya is None
        assert report.hardness is None

    def test_partial_reading(self) -> None:
        reading = PoolReading(ph=7.2, orp=750.0)
        report = compute_chemistry_report(reading)
        assert report.ph is not None
        assert report.ph.status == ChemistryStatus.GOOD
        assert report.orp is not None
        assert report.orp.status == ChemistryStatus.GOOD
        assert report.tac is None
        assert report.cya is None
        assert report.hardness is None

    def test_report_contains_range_attributes(self) -> None:
        reading = PoolReading(ph=7.2)
        report = compute_chemistry_report(reading)
        assert report.ph is not None
        assert report.ph.value == 7.2
        assert report.ph.target == PH_TARGET
        assert report.ph.minimum == PH_MIN
        assert report.ph.maximum == PH_MAX
        assert report.ph.score == 100


class TestCyaAdjustment:
    """Tests for CYA (cyanuric acid / stabilizer) adjustment calculation."""

    def test_cya_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(cya=40.0)
        assert compute_cya_adjustment(pool, reading) is None

    def test_cya_at_min_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(cya=CYA_MIN)
        assert compute_cya_adjustment(pool, reading) is None

    def test_cya_at_max_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(cya=CYA_MAX)
        assert compute_cya_adjustment(pool, reading) is None

    def test_cya_none_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(cya=None)
        assert compute_cya_adjustment(pool, reading) is None

    def test_cya_too_low_recommends_stabilizer(self, pool: Pool) -> None:
        reading = PoolReading(cya=10.0)
        result = compute_cya_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.STABILIZER
        assert result.quantity_g is not None
        assert result.quantity_g > 0

    def test_cya_too_low_dosage_formula(self, pool: Pool) -> None:
        """1g per m3 per ppm: (40 - 10) * 1 * 50 = 1500g."""
        reading = PoolReading(cya=10.0)
        result = compute_cya_adjustment(pool, reading)
        assert result is not None
        assert result.quantity_g == pytest.approx(1500.0)

    def test_cya_above_max_returns_none(self, pool: Pool) -> None:
        """No chemical can lower CYA -- returns None (alert handled by rule)."""
        reading = PoolReading(cya=100.0)
        assert compute_cya_adjustment(pool, reading) is None

    def test_cya_quantity_scales_with_volume(self) -> None:
        small_pool = Pool(name="Small", volume_m3=20.0, pump_flow_m3h=5.0)
        large_pool = Pool(name="Large", volume_m3=100.0, pump_flow_m3h=20.0)
        reading = PoolReading(cya=10.0)

        small_result = compute_cya_adjustment(small_pool, reading)
        large_result = compute_cya_adjustment(large_pool, reading)

        assert small_result is not None
        assert large_result is not None
        assert large_result.quantity_g is not None
        assert small_result.quantity_g is not None
        assert large_result.quantity_g > small_result.quantity_g


class TestHardnessAdjustment:
    """Tests for calcium hardness adjustment calculation."""

    def test_hardness_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(hardness=250.0)
        assert compute_hardness_adjustment(pool, reading) is None

    def test_hardness_at_min_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(hardness=HARDNESS_MIN)
        assert compute_hardness_adjustment(pool, reading) is None

    def test_hardness_at_max_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(hardness=HARDNESS_MAX)
        assert compute_hardness_adjustment(pool, reading) is None

    def test_hardness_none_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(hardness=None)
        assert compute_hardness_adjustment(pool, reading) is None

    def test_hardness_too_low_recommends_increaser(self, pool: Pool) -> None:
        reading = PoolReading(hardness=100.0)
        result = compute_hardness_adjustment(pool, reading)
        assert result is not None
        assert result.product == ChemicalProduct.CALCIUM_HARDNESS_INCREASER
        assert result.quantity_g is not None
        assert result.quantity_g > 0

    def test_hardness_too_low_dosage_formula(self, pool: Pool) -> None:
        """1.5g per m3 per ppm: (250 - 100) * 1.5 * 50 = 11250g."""
        reading = PoolReading(hardness=100.0)
        result = compute_hardness_adjustment(pool, reading)
        assert result is not None
        assert result.quantity_g == pytest.approx(11250.0)

    def test_hardness_above_max_returns_none(self, pool: Pool) -> None:
        """No chemical can lower hardness -- returns None (alert handled by rule)."""
        reading = PoolReading(hardness=500.0)
        assert compute_hardness_adjustment(pool, reading) is None

    def test_hardness_quantity_scales_with_volume(self) -> None:
        small_pool = Pool(name="Small", volume_m3=20.0, pump_flow_m3h=5.0)
        large_pool = Pool(name="Large", volume_m3=100.0, pump_flow_m3h=20.0)
        reading = PoolReading(hardness=100.0)

        small_result = compute_hardness_adjustment(small_pool, reading)
        large_result = compute_hardness_adjustment(large_pool, reading)

        assert small_result is not None
        assert large_result is not None
        assert large_result.quantity_g is not None
        assert small_result.quantity_g is not None
        assert large_result.quantity_g > small_result.quantity_g


class TestFreeChlorineAdjustment:
    """Tests for free chlorine adjustment calculation."""

    def test_in_range_returns_none(self) -> None:
        reading = PoolReading(free_chlorine=2.0)
        assert compute_free_chlorine_adjustment(reading) is None

    def test_at_min_returns_none(self) -> None:
        reading = PoolReading(free_chlorine=FREE_CHLORINE_MIN)
        assert compute_free_chlorine_adjustment(reading) is None

    def test_at_max_returns_none(self) -> None:
        reading = PoolReading(free_chlorine=FREE_CHLORINE_MAX)
        assert compute_free_chlorine_adjustment(reading) is None

    def test_none_returns_none(self) -> None:
        reading = PoolReading(free_chlorine=None)
        assert compute_free_chlorine_adjustment(reading) is None

    def test_too_low_recommends_shock(self) -> None:
        reading = PoolReading(free_chlorine=0.5)
        result = compute_free_chlorine_adjustment(reading)
        assert result is not None
        assert result.product == ChemicalProduct.CHLORE_CHOC
        # No quantity -- depends on many factors
        assert result.quantity_g is None

    def test_too_high_recommends_neutralizer(self) -> None:
        reading = PoolReading(free_chlorine=4.0)
        result = compute_free_chlorine_adjustment(reading)
        assert result is not None
        assert result.product == ChemicalProduct.NEUTRALIZER
        assert result.quantity_g is None
