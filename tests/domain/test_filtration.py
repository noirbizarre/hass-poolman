"""Tests for filtration duration calculations."""

from __future__ import annotations

from custom_components.poolman.domain.filtration import (
    WINTER_ACTIVE_HOURS,
    WINTER_PASSIVE_HOURS,
    compute_filtration_duration,
)
from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading


class TestFiltrationDuration:
    """Tests for filtration duration computation."""

    def test_basic_temperature_rule(self, pool: Pool) -> None:
        """Temperature / 2 rule: 26C -> ~13h (clamped if needed)."""
        reading = PoolReading(temp_c=26.0)
        result = compute_filtration_duration(pool, reading, PoolMode.RUNNING)
        assert result is not None
        assert result >= 13.0

    def test_cold_water_minimum_filtration(self, pool: Pool) -> None:
        """Very cold water should still have minimum filtration."""
        reading = PoolReading(temp_c=2.0)
        result = compute_filtration_duration(pool, reading, PoolMode.RUNNING)
        assert result is not None
        assert result >= 2.0

    def test_hot_water_caps_at_max(self, pool: Pool) -> None:
        """Very hot water should cap at 24 hours."""
        reading = PoolReading(temp_c=50.0)
        result = compute_filtration_duration(pool, reading, PoolMode.RUNNING)
        assert result is not None
        assert result <= 24.0

    def test_winter_passive_zero(self, pool: Pool, good_reading: PoolReading) -> None:
        """Passive wintering should return zero filtration."""
        result = compute_filtration_duration(pool, good_reading, PoolMode.WINTER_PASSIVE)
        assert result == WINTER_PASSIVE_HOURS

    def test_winter_active_fixed(self, pool: Pool, good_reading: PoolReading) -> None:
        """Active wintering should return fixed filtration hours."""
        result = compute_filtration_duration(pool, good_reading, PoolMode.WINTER_ACTIVE)
        assert result == WINTER_ACTIVE_HOURS

    def test_no_temperature_returns_none(self, pool: Pool) -> None:
        """No temperature reading should return None."""
        reading = PoolReading()
        result = compute_filtration_duration(pool, reading, PoolMode.RUNNING)
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
        result = compute_filtration_duration(slow_pool, reading, PoolMode.RUNNING)
        assert result is not None
        assert result >= 20.0
