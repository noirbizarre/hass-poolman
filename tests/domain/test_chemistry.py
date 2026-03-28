"""Tests for pool chemistry calculations."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.chemistry import (
    PH_TARGET,
    compute_chlorine_status,
    compute_ph_adjustment,
    compute_tac_adjustment,
    compute_water_quality_score,
)
from custom_components.poolman.domain.model import Pool, PoolReading


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
        assert result["product"] == "ph_minus"
        assert result["quantity_g"] > 0

    def test_ph_too_low_recommends_ph_plus(self, pool: Pool) -> None:
        reading = PoolReading(ph=6.8)
        result = compute_ph_adjustment(pool, reading)
        assert result is not None
        assert result["product"] == "ph_plus"
        assert result["quantity_g"] > 0

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
        assert large_result["quantity_g"] > small_result["quantity_g"]

    def test_quantity_scales_with_delta(self, pool: Pool) -> None:
        slight = PoolReading(ph=PH_TARGET + 0.2)
        severe = PoolReading(ph=PH_TARGET + 0.6)

        slight_result = compute_ph_adjustment(pool, slight)
        severe_result = compute_ph_adjustment(pool, severe)

        assert slight_result is not None
        assert severe_result is not None
        assert severe_result["quantity_g"] > slight_result["quantity_g"]


class TestChlorineStatus:
    """Tests for chlorine/ORP evaluation."""

    def test_orp_in_range_returns_none(self) -> None:
        reading = PoolReading(orp=750.0)
        assert compute_chlorine_status(reading) is None

    def test_orp_critically_low(self) -> None:
        reading = PoolReading(orp=600.0)
        result = compute_chlorine_status(reading)
        assert result is not None
        assert result["product"] == "chlore_choc"
        assert result["severity"] == "critical"

    def test_orp_low(self) -> None:
        reading = PoolReading(orp=700.0)
        result = compute_chlorine_status(reading)
        assert result is not None
        assert result["product"] == "galet_chlore"
        assert result["severity"] == "medium"

    def test_orp_too_high(self) -> None:
        reading = PoolReading(orp=950.0)
        result = compute_chlorine_status(reading)
        assert result is not None
        assert result["product"] == "neutralizer"

    def test_orp_none_returns_none(self) -> None:
        reading = PoolReading(orp=None)
        assert compute_chlorine_status(reading) is None


class TestTacAdjustment:
    """Tests for TAC adjustment calculation."""

    def test_tac_in_range_returns_none(self, pool: Pool) -> None:
        reading = PoolReading(tac=120.0)
        assert compute_tac_adjustment(pool, reading) is None

    def test_tac_too_low_recommends_tac_plus(self, pool: Pool) -> None:
        reading = PoolReading(tac=60.0)
        result = compute_tac_adjustment(pool, reading)
        assert result is not None
        assert result["product"] == "tac_plus"
        assert result["quantity_g"] > 0

    def test_tac_too_high_recommends_ph_minus(self, pool: Pool) -> None:
        reading = PoolReading(tac=180.0)
        result = compute_tac_adjustment(pool, reading)
        assert result is not None
        assert result["product"] == "ph_minus"

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
