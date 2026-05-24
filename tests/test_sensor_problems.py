"""Tests for the ``problems`` sensor entity."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.analysis import AnalysisResult
from custom_components.poolman.domain.model import Pool, PoolMode, PoolReading, PoolState
from custom_components.poolman.domain.problem import MetricName, Problem, Severity
from custom_components.poolman.sensor import _problem_to_dict, _problems_attrs
from tests.conftest import setup_mock_states

ENTITY_ID = "sensor.test_pool_problems"


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> PoolmanCoordinator:
    """Set up the integration with good (in-range) sensor states."""
    mock_config_entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry.runtime_data


def _set_bad_states(hass: HomeAssistant) -> None:
    """Force chemistry out of range to trigger problem rules."""
    hass.states.async_set("sensor.pool_ph", "8.4")
    hass.states.async_set("sensor.pool_orp", "500.0")
    hass.states.async_set("sensor.pool_temperature", "30.0")


class TestProblemsSensorIntegration:
    """End-to-end coverage through the HA state machine."""

    async def test_entity_registered(
        self, hass: HomeAssistant, setup_entry: PoolmanCoordinator
    ) -> None:
        state = hass.states.get(ENTITY_ID)
        assert state is not None

    async def test_no_problems_with_good_readings(
        self, hass: HomeAssistant, setup_entry: PoolmanCoordinator
    ) -> None:
        state = hass.states.get(ENTITY_ID)
        assert state is not None
        # The state must mirror the analysis pipeline's problem count exactly.
        expected = len(setup_entry.data.analysis_result.problems)
        assert int(state.state) == expected
        assert len(state.attributes["problems"]) == expected
        if expected == 0:
            assert state.attributes["worst_severity"] == "ok"
        else:
            assert state.attributes["worst_severity"] in {"low", "medium", "critical"}

    async def test_problems_exposed_with_bad_readings(
        self, hass: HomeAssistant, setup_entry: PoolmanCoordinator
    ) -> None:
        _set_bad_states(hass)
        await setup_entry.async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get(ENTITY_ID)
        assert state is not None
        count = int(state.state)
        assert count > 0

        problems = state.attributes["problems"]
        assert len(problems) == count
        # Every entry exposes the documented schema with primitive types.
        for entry in problems:
            assert set(entry) == {
                "code",
                "severity",
                "metric",
                "value",
                "expected_range",
                "message",
            }
            assert isinstance(entry["code"], str)
            assert isinstance(entry["severity"], str)
            assert entry["severity"] in {"low", "medium", "critical"}
            assert entry["metric"] is None or isinstance(entry["metric"], str)
            assert entry["expected_range"] is None or isinstance(entry["expected_range"], list)

        # Severity descending order: CRITICAL > MEDIUM > LOW.
        order = {"critical": 3, "medium": 2, "low": 1}
        ranks = [order[p["severity"]] for p in problems]
        assert ranks == sorted(ranks, reverse=True)
        assert state.attributes["worst_severity"] == problems[0]["severity"]


class TestProblemsAttrsHelper:
    """Direct coverage of the pure helper for deterministic ordering."""

    def _state(self, *problems: Problem) -> PoolState:
        return PoolState(
            mode=PoolMode.ACTIVE,
            pool=Pool(name="t", volume_m3=10.0, pump_flow_m3h=5.0),
            reading=PoolReading(),
            analysis_result=AnalysisResult(problems=list(problems)),
        )

    def test_empty_problems_yields_ok(self) -> None:
        attrs = _problems_attrs(self._state())
        assert attrs == {"problems": [], "worst_severity": "ok"}

    def test_orders_by_severity_descending(self) -> None:
        low = Problem(code="a_low", message="m", severity=Severity.LOW)
        medium = Problem(code="b_med", message="m", severity=Severity.MEDIUM)
        critical = Problem(code="c_crit", message="m", severity=Severity.CRITICAL)

        attrs = _problems_attrs(self._state(low, critical, medium))
        codes = [p["code"] for p in attrs["problems"]]
        assert codes == ["c_crit", "b_med", "a_low"]
        assert attrs["worst_severity"] == "critical"

    def test_worst_severity_reflects_highest(self) -> None:
        low = Problem(code="a", message="m", severity=Severity.LOW)
        medium = Problem(code="b", message="m", severity=Severity.MEDIUM)

        assert _problems_attrs(self._state(low))["worst_severity"] == "low"
        assert _problems_attrs(self._state(low, medium))["worst_severity"] == "medium"

    def test_problem_to_dict_serializes_primitives(self) -> None:
        problem = Problem(
            code="ph_too_high",
            message="pH too high",
            severity=Severity.MEDIUM,
            metric=MetricName.PH,
            value=8.4,
            expected_range=(7.0, 7.6),
        )
        assert _problem_to_dict(problem) == {
            "code": "ph_too_high",
            "severity": "medium",
            "metric": "ph",
            "value": 8.4,
            "expected_range": [7.0, 7.6],
            "message": "pH too high",
        }

    def test_problem_to_dict_handles_optional_fields(self) -> None:
        problem = Problem(
            code="generic",
            message="m",
            severity=Severity.LOW,
        )
        result = _problem_to_dict(problem)
        assert result["metric"] is None
        assert result["value"] is None
        assert result["expected_range"] is None
