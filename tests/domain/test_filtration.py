"""Tests for filtration duration calculations."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.filtration import (
    FILTRATION_EFFICIENCY,
    MAX_FILTRATION_HOURS,
    MIN_FILTRATION_HOURS,
    OUTDOOR_TEMP_THRESHOLD,
    WINTER_ACTIVE_HOURS,
    WINTER_PASSIVE_HOURS,
    compute_filtration_duration,
)
from custom_components.poolman.domain.model import (
    FiltrationKind,
    Pool,
    PoolMode,
    PoolReading,
)


class TestFiltrationDuration:
    """Tests for filtration duration computation."""

    def test_basic_temperature_rule(self, pool: Pool) -> None:
        """Temperature / 2 rule: 26C -> ~13h (clamped if needed)."""
        reading = PoolReading(temp_c=26.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        assert result >= 13.0

    def test_cold_water_minimum_filtration(self, pool: Pool) -> None:
        """Very cold water should still have minimum filtration."""
        reading = PoolReading(temp_c=2.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        assert result >= MIN_FILTRATION_HOURS

    def test_hot_water_caps_at_max(self, pool: Pool) -> None:
        """Very hot water should cap at 24 hours."""
        reading = PoolReading(temp_c=50.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        assert result <= MAX_FILTRATION_HOURS

    def test_winter_passive_zero(self, pool: Pool, good_reading: PoolReading) -> None:
        """Passive wintering should return zero filtration."""
        result = compute_filtration_duration(pool, good_reading, PoolMode.WINTER_PASSIVE)
        assert result == WINTER_PASSIVE_HOURS

    def test_winter_active_fixed(self, pool: Pool, good_reading: PoolReading) -> None:
        """Active wintering should return fixed filtration hours."""
        result = compute_filtration_duration(pool, good_reading, PoolMode.WINTER_ACTIVE)
        assert result == WINTER_ACTIVE_HOURS

    def test_hibernating_fixed(self, pool: Pool, good_reading: PoolReading) -> None:
        """Hibernating mode should return fixed filtration hours (same as active wintering)."""
        result = compute_filtration_duration(pool, good_reading, PoolMode.HIBERNATING)
        assert result == WINTER_ACTIVE_HOURS

    def test_activating_uses_dynamic_computation(self, pool: Pool) -> None:
        """Activating mode should use the full dynamic computation (same as active)."""
        reading = PoolReading(temp_c=26.0)
        result_activating = compute_filtration_duration(pool, reading, PoolMode.ACTIVATING)
        result_active = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result_activating == result_active

    def test_no_temperature_returns_none(self, pool: Pool) -> None:
        """No temperature reading should return None."""
        reading = PoolReading()
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is None

    def test_ensures_full_turnover(self) -> None:
        """Filtration should be at least long enough for a full water turnover."""
        # Pool with slow pump: 100m3 / 5 m3/h = 20h turnover
        slow_pool = Pool(
            name="Slow",
            volume_m3=100.0,
            pump_flow_m3h=5.0,
        )
        reading = PoolReading(temp_c=20.0)  # temp/2 = 10h, but turnover = 20h
        result = compute_filtration_duration(slow_pool, reading, PoolMode.ACTIVE)
        assert result is not None
        assert result >= 20.0


class TestFiltrationKindEfficiency:
    """Tests for filtration type efficiency coefficients."""

    def test_sand_filter_baseline(self) -> None:
        """Sand filter (coefficient 1.0) should not modify the base duration."""
        pool = Pool(
            name="Sand", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.SAND
        )
        reading = PoolReading(temp_c=24.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        # 24/2 * 1.0 = 12.0, turnover = 50/10 = 5h -> 12.0
        assert result == pytest.approx(12.0)

    def test_cartridge_reduces_duration(self) -> None:
        """Cartridge filter (0.95) should reduce duration compared to sand."""
        sand_pool = Pool(
            name="Sand", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.SAND
        )
        cart_pool = Pool(
            name="Cart",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            filtration_kind=FiltrationKind.CARTRIDGE,
        )
        reading = PoolReading(temp_c=24.0)
        sand_result = compute_filtration_duration(sand_pool, reading, PoolMode.ACTIVE)
        cart_result = compute_filtration_duration(cart_pool, reading, PoolMode.ACTIVE)
        assert sand_result is not None
        assert cart_result is not None
        assert cart_result < sand_result

    def test_glass_reduces_duration(self) -> None:
        """Glass filter (0.90) should reduce duration compared to sand."""
        sand_pool = Pool(
            name="Sand", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.SAND
        )
        glass_pool = Pool(
            name="Glass", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.GLASS
        )
        reading = PoolReading(temp_c=24.0)
        sand_result = compute_filtration_duration(sand_pool, reading, PoolMode.ACTIVE)
        glass_result = compute_filtration_duration(glass_pool, reading, PoolMode.ACTIVE)
        assert sand_result is not None
        assert glass_result is not None
        assert glass_result < sand_result

    def test_de_reduces_duration_most(self) -> None:
        """Diatomaceous earth (0.85) should reduce duration the most."""
        sand_pool = Pool(
            name="Sand", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.SAND
        )
        de_pool = Pool(
            name="DE",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            filtration_kind=FiltrationKind.DIATOMACEOUS_EARTH,
        )
        reading = PoolReading(temp_c=24.0)
        sand_result = compute_filtration_duration(sand_pool, reading, PoolMode.ACTIVE)
        de_result = compute_filtration_duration(de_pool, reading, PoolMode.ACTIVE)
        assert sand_result is not None
        assert de_result is not None
        assert de_result < sand_result
        # DE (0.85) should save more than glass (0.90)
        glass_pool = Pool(
            name="Glass", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=FiltrationKind.GLASS
        )
        glass_result = compute_filtration_duration(glass_pool, reading, PoolMode.ACTIVE)
        assert glass_result is not None
        assert de_result < glass_result

    def test_exact_efficiency_coefficients(self) -> None:
        """Verify the exact coefficient values applied to the base duration."""
        reading = PoolReading(temp_c=20.0)
        base = 20.0 / 2  # 10.0 hours

        for kind, coefficient in FILTRATION_EFFICIENCY.items():
            pool = Pool(name="Test", volume_m3=50.0, pump_flow_m3h=10.0, filtration_kind=kind)
            result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
            assert result is not None
            expected = max(MIN_FILTRATION_HOURS, min(base * coefficient, MAX_FILTRATION_HOURS))
            # Account for turnover (50/10 = 5h, always below base*coeff here)
            expected = max(expected, 50.0 / 10.0)
            assert result == pytest.approx(expected)

    def test_efficiency_does_not_affect_winter_modes(self, pool: Pool) -> None:
        """Filter efficiency should not affect winter mode fixed durations."""
        reading = PoolReading(temp_c=26.0)
        de_pool = Pool(
            name="DE",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            filtration_kind=FiltrationKind.DIATOMACEOUS_EARTH,
        )
        assert (
            compute_filtration_duration(de_pool, reading, PoolMode.WINTER_PASSIVE)
            == WINTER_PASSIVE_HOURS
        )
        assert (
            compute_filtration_duration(de_pool, reading, PoolMode.WINTER_ACTIVE)
            == WINTER_ACTIVE_HOURS
        )


class TestOutdoorTemperatureAdjustment:
    """Tests for outdoor temperature heat stress factor."""

    def test_outdoor_temp_none_no_effect(self, pool: Pool) -> None:
        """No outdoor temperature should not affect the result."""
        reading_without = PoolReading(temp_c=24.0, outdoor_temp_c=None)
        reading_with_normal = PoolReading(temp_c=24.0, outdoor_temp_c=25.0)
        result_without = compute_filtration_duration(pool, reading_without, PoolMode.ACTIVE)
        result_normal = compute_filtration_duration(pool, reading_with_normal, PoolMode.ACTIVE)
        assert result_without is not None
        assert result_normal is not None
        # Both should be equal since 25 < 28 threshold
        assert result_without == result_normal

    def test_outdoor_temp_below_threshold_no_effect(self, pool: Pool) -> None:
        """Outdoor temp at or below 28 C should not increase filtration."""
        reading_no_outdoor = PoolReading(temp_c=24.0)
        reading_at_threshold = PoolReading(temp_c=24.0, outdoor_temp_c=OUTDOOR_TEMP_THRESHOLD)
        result_base = compute_filtration_duration(pool, reading_no_outdoor, PoolMode.ACTIVE)
        result_threshold = compute_filtration_duration(pool, reading_at_threshold, PoolMode.ACTIVE)
        assert result_base is not None
        assert result_threshold is not None
        assert result_base == result_threshold

    def test_outdoor_temp_above_threshold_increases(self, pool: Pool) -> None:
        """Outdoor temp above 28 C should increase filtration duration."""
        reading_cool = PoolReading(temp_c=24.0, outdoor_temp_c=25.0)
        reading_hot = PoolReading(temp_c=24.0, outdoor_temp_c=35.0)
        result_cool = compute_filtration_duration(pool, reading_cool, PoolMode.ACTIVE)
        result_hot = compute_filtration_duration(pool, reading_hot, PoolMode.ACTIVE)
        assert result_cool is not None
        assert result_hot is not None
        assert result_hot > result_cool

    def test_outdoor_temp_exact_factor(self, pool: Pool) -> None:
        """Verify the exact heat stress calculation: +5% per degree above 28 C."""
        reading = PoolReading(temp_c=24.0, outdoor_temp_c=33.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        # base = 24/2 = 12.0
        # heat_factor = 1 + (33-28)*0.05 = 1.25
        # adjusted = 12.0 * 1.25 = 15.0
        # turnover = 50/10 = 5h < 15.0
        assert result == pytest.approx(15.0)

    def test_outdoor_temp_high_clamped_at_max(self) -> None:
        """Even with extreme heat stress, result should be clamped at 24h."""
        pool = Pool(name="Hot", volume_m3=50.0, pump_flow_m3h=10.0)
        reading = PoolReading(temp_c=40.0, outdoor_temp_c=50.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        assert result == MAX_FILTRATION_HOURS

    def test_outdoor_temp_does_not_affect_winter_modes(self) -> None:
        """Outdoor temperature should not affect winter mode fixed durations."""
        pool = Pool(name="Test", volume_m3=50.0, pump_flow_m3h=10.0)
        reading = PoolReading(temp_c=26.0, outdoor_temp_c=40.0)
        assert (
            compute_filtration_duration(pool, reading, PoolMode.WINTER_PASSIVE)
            == WINTER_PASSIVE_HOURS
        )
        assert (
            compute_filtration_duration(pool, reading, PoolMode.WINTER_ACTIVE)
            == WINTER_ACTIVE_HOURS
        )


class TestCombinedFactors:
    """Tests for combined filtration kind and outdoor temperature effects."""

    def test_combined_filter_efficiency_and_heat_stress(self) -> None:
        """Both factors should apply multiplicatively."""
        pool = Pool(
            name="Combined",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            filtration_kind=FiltrationKind.GLASS,
        )
        reading = PoolReading(temp_c=24.0, outdoor_temp_c=33.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        # base = 24/2 = 12.0
        # glass efficiency = 0.9 -> 12.0 * 0.9 = 10.8
        # heat = 1 + (33-28)*0.05 = 1.25 -> 10.8 * 1.25 = 13.5
        # turnover = 50/10 = 5h < 13.5
        assert result == pytest.approx(13.5)

    def test_de_filter_with_moderate_heat(self) -> None:
        """DE filter with moderate heat stress."""
        pool = Pool(
            name="DE+Heat",
            volume_m3=50.0,
            pump_flow_m3h=10.0,
            filtration_kind=FiltrationKind.DIATOMACEOUS_EARTH,
        )
        reading = PoolReading(temp_c=24.0, outdoor_temp_c=30.0)
        result = compute_filtration_duration(pool, reading, PoolMode.ACTIVE)
        assert result is not None
        # base = 24/2 = 12.0
        # DE efficiency = 0.85 -> 12.0 * 0.85 = 10.2
        # heat = 1 + (30-28)*0.05 = 1.10 -> 10.2 * 1.10 = 11.22
        # turnover = 50/10 = 5h < 11.22
        assert result == pytest.approx(11.22)

    def test_turnover_wins_over_adjusted_base(self) -> None:
        """Turnover requirement should still win when adjusted base is low."""
        slow_pool = Pool(
            name="Slow+DE",
            volume_m3=100.0,
            pump_flow_m3h=5.0,
            filtration_kind=FiltrationKind.DIATOMACEOUS_EARTH,
        )
        reading = PoolReading(temp_c=20.0, outdoor_temp_c=25.0)
        result = compute_filtration_duration(slow_pool, reading, PoolMode.ACTIVE)
        assert result is not None
        # base = 20/2 = 10.0
        # DE efficiency = 0.85 -> 10.0 * 0.85 = 8.5
        # no heat stress (25 < 28)
        # turnover = 100/5 = 20h > 8.5 -> 20.0
        assert result == pytest.approx(20.0)
