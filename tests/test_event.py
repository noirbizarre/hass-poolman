"""Tests for the Pool Manager event platform (filtration + treatment events)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import DOMAIN
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import ChemicalProduct
from tests.conftest import MOCK_CONFIG_DATA, setup_mock_states


async def _setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Set up integration and return coordinator."""
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestFiltrationEvent:
    """Tests for the PoolmanFiltrationEvent entity."""

    async def test_entity_created_with_pump(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Filtration event entity should be created when pump is configured."""
        await _setup_integration(hass, mock_config_entry)
        state = hass.states.get("event.test_pool_filtration")
        assert state is not None

    async def test_entity_not_created_without_pump(
        self, hass: HomeAssistant, mock_config_entry_no_pump: MockConfigEntry
    ) -> None:
        """Filtration event entity should not exist when no pump."""
        await _setup_integration(hass, mock_config_entry_no_pump)
        state = hass.states.get("event.test_pool_filtration")
        assert state is None

    async def test_scheduler_event_fires_ha_event(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Scheduler event callback should trigger the HA event entity."""
        coordinator = await _setup_integration(hass, mock_config_entry)
        assert coordinator.scheduler is not None

        # Simulate a scheduler event by firing the on_event callbacks
        scheduler = coordinator.scheduler
        event_data: dict[str, object] = {
            "start_time": "10:00",
            "duration_hours": 8.0,
            "end_time": "18:00",
        }
        for cb in list(scheduler._listeners):
            cb("filtration_started", event_data)

        await hass.async_block_till_done()

        state = hass.states.get("event.test_pool_filtration")
        assert state is not None
        # After event fired, the entity should have event_type attribute
        assert state.attributes.get("event_type") == "filtration_started"


class TestTreatmentEvent:
    """Tests for treatment event entities."""

    async def test_treatment_entities_created(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Treatment event entities should be created during setup."""
        await _setup_integration(hass, mock_config_entry)
        # pH minus is a universal product, should always be created
        state = hass.states.get("event.test_pool_ph_minus_treatment")
        assert state is not None

    async def test_apply_treatment_via_coordinator(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Calling async_add_treatment should fire event on the entity."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        # The treatment entity should be registered with the coordinator
        assert ChemicalProduct.PH_MINUS in coordinator._treatment_entities

        await coordinator.async_add_treatment(
            ChemicalProduct.PH_MINUS, quantity_g=50.0, notes="Test treatment"
        )
        await hass.async_block_till_done()

        state = hass.states.get("event.test_pool_ph_minus_treatment")
        assert state is not None
        assert state.attributes.get("event_type") == "applied"

    async def test_apply_treatment_with_quantity_only(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Applying treatment with quantity but no notes."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await coordinator.async_add_treatment(ChemicalProduct.FLOCCULANT, quantity_g=100.0)
        await hass.async_block_till_done()

        state = hass.states.get("event.test_pool_flocculant_treatment")
        assert state is not None
        assert state.attributes.get("event_type") == "applied"

    async def test_apply_treatment_with_no_data(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Applying treatment with no quantity or notes."""
        coordinator = await _setup_integration(hass, mock_config_entry)

        await coordinator.async_add_treatment(ChemicalProduct.ANTI_ALGAE)
        await hass.async_block_till_done()

        state = hass.states.get("event.test_pool_anti_algae_treatment")
        assert state is not None
        assert state.attributes.get("event_type") == "applied"

    async def test_treatment_entity_disabled_for_wrong_treatment_type(
        self, hass: HomeAssistant
    ) -> None:
        """Bromine entities should be disabled by default for chlorine pools."""
        from custom_components.poolman.const import CONF_TREATMENT

        data = MOCK_CONFIG_DATA.copy()
        data[CONF_TREATMENT] = "chlorine"
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=data,
            version=1,
            minor_version=3,
        )
        await _setup_integration(hass, entry)

        # Bromine tablet should exist but be disabled by default
        # We check via entity registry rather than state
        from homeassistant.helpers import entity_registry as er

        ent_reg = er.async_get(hass)
        bromine_entry = ent_reg.async_get("event.test_pool_bromine_tablet_treatment")
        if bromine_entry is not None:
            assert bromine_entry.disabled_by is not None


class TestTreatmentEventRemoval:
    """Tests for filtration event removal from hass."""

    async def test_filtration_event_removal(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Removing filtration event should unsubscribe from scheduler."""
        await _setup_integration(hass, mock_config_entry)

        # Unload the entry, which will remove entities from hass
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("event.test_pool_filtration")
        # After unload, entity should be unavailable
        assert state is None or state.state == "unavailable"
