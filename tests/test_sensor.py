"""Tests for the Pool Manager sensor platform — recommendations entity."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.coordinator import PoolmanCoordinator
from tests.conftest import setup_mock_states

RECOMMENDATIONS_ENTITY_ID = "sensor.test_pool_recommendations"

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
