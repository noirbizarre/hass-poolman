"""Shared test fixtures for Pool Manager tests."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import Pool, PoolReading, PoolShape


@pytest.fixture
def pool() -> Pool:
    """Return a standard test pool."""
    return Pool(
        name="Test Pool",
        volume_m3=50.0,
        shape=PoolShape.RECTANGULAR,
        pump_flow_m3h=10.0,
    )


@pytest.fixture
def good_reading() -> PoolReading:
    """Return a reading with all parameters in acceptable range."""
    return PoolReading(
        ph=7.2,
        orp=750.0,
        temp_c=26.0,
        tac=120.0,
        cya=40.0,
        hardness=250.0,
    )


@pytest.fixture
def bad_reading() -> PoolReading:
    """Return a reading with parameters out of range."""
    return PoolReading(
        ph=8.2,
        orp=600.0,
        temp_c=30.0,
        tac=60.0,
        cya=10.0,
        hardness=500.0,
    )


@pytest.fixture
def empty_reading() -> PoolReading:
    """Return a reading with no sensor data."""
    return PoolReading()
