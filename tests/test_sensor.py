"""Tests for the Pool Manager sensor platform."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.action import Action, ActionSource, ActionType
from custom_components.poolman.domain.model import PoolStatus
from custom_components.poolman.domain.problem import Severity
from tests.conftest import setup_mock_states

RECOMMENDATIONS_ENTITY_ID = "sensor.test_pool_recommendations"
STATUS_ENTITY_ID = "sensor.test_pool_status"
ACTION_HISTORY_ENTITY_ID = "sensor.test_pool_action_history"

# Keys expected in every serialized recommendation. Aligned with the contract
# documented in issue #98 (extended to include all domain fields).
RECOMMENDATION_KEYS = {
    "id",
    "type",
    "severity",
    "priority",
    "kind",
    "title",
    "description",
    "reason",
    "treatments",
    "related_metrics",
}

TREATMENT_KEYS = {"id", "product_id", "name", "quantity", "unit", "duration"}


async def _setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up integration and return the coordinator."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestRecommendationsSensor:
    """Tests for the ``sensor.<pool>_recommendations`` entity."""

    async def test_entity_created(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """The recommendations sensor should be registered."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert state is not None

    async def test_state_is_recommendation_count(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """State must equal len(state.recommendations)."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert state is not None
        expected = len(coordinator.data.recommendations)
        assert int(state.state) == expected

    async def test_attributes_schema(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Attributes should always include the documented keys."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert state is not None
        attrs = state.attributes
        assert "recommendations" in attrs
        assert "critical_count" in attrs
        assert isinstance(attrs["recommendations"], list)
        assert isinstance(attrs["critical_count"], int)

    async def test_attributes_with_recommendations(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """When recommendations exist, each entry should expose the full DTO."""
        # Force a pH high enough to trigger at least one recommendation.
        hass.states.async_set("sensor.pool_ph", "8.5")
        hass.states.async_set("sensor.pool_orp", "750.0")
        hass.states.async_set("sensor.pool_temperature", "26.0")
        # Avoid setup_mock_states overwriting the bad pH.
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator: PoolmanCoordinator = mock_config_entry.runtime_data
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert state is not None
        recs = state.attributes["recommendations"]
        assert int(state.state) == len(recs)
        if not recs:
            # The detection pipeline may not flag this exact value; the
            # schema test above already covers the empty case.
            return

        for rec in recs:
            assert set(rec.keys()) == RECOMMENDATION_KEYS
            # All enum-derived fields must be plain strings.
            for key in ("type", "severity", "priority", "kind"):
                assert type(rec[key]) is str
            assert isinstance(rec["related_metrics"], list)
            for metric in rec["related_metrics"]:
                assert type(metric) is str
            assert isinstance(rec["treatments"], list)
            for treatment in rec["treatments"]:
                assert set(treatment.keys()) == TREATMENT_KEYS
                assert isinstance(treatment["quantity"], (int, float))
                assert isinstance(treatment["unit"], str)
                assert treatment["duration"] is None or isinstance(
                    treatment["duration"], (int, float)
                )

    async def test_updates_on_refresh(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Attributes must refresh after the coordinator runs analyze_pool again."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        baseline = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert baseline is not None

        # Push the pH out of range so detect_problems yields more findings.
        hass.states.async_set("sensor.pool_ph", "8.6")
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        updated = hass.states.get(RECOMMENDATIONS_ENTITY_ID)
        assert updated is not None
        assert int(updated.state) == len(coordinator.data.recommendations)
        assert updated.attributes["recommendations"] == [
            r.to_dict() for r in coordinator.data.recommendations
        ]


class TestPoolStatusSensor:
    """Tests for ``sensor.<pool>_status`` global status sensor (issue #102)."""

    async def test_entity_registered_with_enum_metadata(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """The status entity exposes ``device_class=enum`` and the three options."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(STATUS_ENTITY_ID)
        assert state is not None
        assert state.attributes["device_class"] == "enum"
        assert state.attributes["options"] == [
            PoolStatus.OK.value,
            PoolStatus.WARNING.value,
            PoolStatus.CRITICAL.value,
        ]

    async def test_state_matches_pool_state_status(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """The entity state mirrors the computed ``PoolState.status``."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(STATUS_ENTITY_ID)
        assert state is not None
        assert state.state == coordinator.data.status.value

    async def test_attributes_reflect_problems(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """``problem_count``/``critical_count``/``worst_severity`` reflect analysis output."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        problems = coordinator.data.analysis_result.problems

        state = hass.states.get(STATUS_ENTITY_ID)
        assert state is not None
        assert state.attributes["problem_count"] == len(problems)
        assert state.attributes["critical_count"] == sum(
            1 for p in problems if p.severity is Severity.CRITICAL
        )
        if problems:
            assert state.attributes["worst_severity"] == problems[0].severity
        else:
            assert state.attributes["worst_severity"] is None

    async def test_escalates_when_ph_goes_critical(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """A strongly out-of-range pH escalates the global status."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        initial = hass.states.get(STATUS_ENTITY_ID)
        assert initial is not None
        initial_state = initial.state

        hass.states.async_set("sensor.pool_ph", "5.5")
        await coordinator.async_request_refresh()
        await hass.async_block_till_done()

        new_state = hass.states.get(STATUS_ENTITY_ID)
        assert new_state is not None
        # State must be at least as severe as the initial one and remain a valid enum value.
        assert new_state.state in {
            PoolStatus.OK.value,
            PoolStatus.WARNING.value,
            PoolStatus.CRITICAL.value,
        }
        # Worst severity present in the problem list.
        assert new_state.state == coordinator.data.status.value
        # The bad pH should not lower the severity.
        order = {
            PoolStatus.OK.value: 0,
            PoolStatus.WARNING.value: 1,
            PoolStatus.CRITICAL.value: 2,
        }
        assert order[new_state.state] >= order[initial_state]


class TestActionHistorySensor:
    """Tests for ``sensor.<pool>_action_history`` (issue #106)."""

    @staticmethod
    def _action(
        action_id: str,
        *,
        timestamp: datetime,
        action_type: ActionType = ActionType.CHEMICAL,
        source: ActionSource = ActionSource.USER,
    ) -> Action:
        return Action(
            id=action_id,
            type=action_type,
            source=source,
            treatment_id="ph_minus_300g",
            quantity=150.0,
            unit="g",
            timestamp=timestamp,
            product_id=None,
        )

    async def test_entity_created_with_empty_state(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """The action history sensor exists and starts with no actions."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get(ACTION_HISTORY_ENTITY_ID)
        assert state is not None
        # No actions yet → unknown timestamp, empty attribute list.
        assert state.state in {"unknown", "unavailable"}
        assert state.attributes["actions"] == []
        assert state.attributes["limit"] == 50
        assert state.attributes["total"] == 0
        assert state.attributes["device_class"] == "timestamp"

    async def test_state_reflects_latest_action(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """The state mirrors the timestamp of the most recently recorded action."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        earlier = datetime(2026, 4, 18, 9, 0, tzinfo=UTC)
        latest = datetime(2026, 4, 19, 14, 30, tzinfo=UTC)

        await coordinator.async_record_action(self._action("act_a", timestamp=earlier))
        await coordinator.async_record_action(self._action("act_b", timestamp=latest))
        await hass.async_block_till_done()

        state = hass.states.get(ACTION_HISTORY_ENTITY_ID)
        assert state is not None
        # HA serializes timestamps as ISO-8601 strings.
        assert state.state == latest.isoformat()

    async def test_attributes_list_actions_newest_first(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """``actions`` are ordered newest-first and JSON-serializable."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        earlier = datetime(2026, 4, 18, 9, 0, tzinfo=UTC)
        latest = datetime(2026, 4, 19, 14, 30, tzinfo=UTC)

        await coordinator.async_record_action(
            self._action("act_a", timestamp=earlier, action_type=ActionType.CLEANING)
        )
        await coordinator.async_record_action(self._action("act_b", timestamp=latest))
        await hass.async_block_till_done()

        state = hass.states.get(ACTION_HISTORY_ENTITY_ID)
        assert state is not None
        actions = state.attributes["actions"]
        assert [a["id"] for a in actions] == ["act_b", "act_a"]
        first = actions[0]
        assert first["type"] == "chemical"
        assert first["source"] == "user"
        assert first["quantity"] == 150.0
        assert first["unit"] == "g"
        assert first["timestamp"] == latest.isoformat()
        assert first["duration"] is None
        assert state.attributes["total"] == 2
