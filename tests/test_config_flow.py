"""Tests for the Pool Manager config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    CONF_COMPLETED_AT,
    CONF_FILTRATION_KIND,
    CONF_ORP_ENTITY,
    CONF_PH_ENTITY,
    CONF_POOL_NAME,
    CONF_PUMP_FLOW_M3H,
    CONF_SHAPE,
    CONF_STARTED_AT,
    CONF_STEPS,
    CONF_TARGET_MODE,
    CONF_TEMPERATURE_ENTITY,
    CONF_TREATMENT,
    CONF_VOLUME_M3,
    DOMAIN,
    MODE_WINTER_ACTIVE,
    MODE_WINTER_PASSIVE,
    SUBENTRY_ACTIVATION,
    SUBENTRY_HIBERNATION,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.activation import ActivationStep
from custom_components.poolman.domain.model import PoolMode
from tests.conftest import MOCK_CONFIG_DATA, setup_mock_states

POOL_INPUT: dict[str, Any] = {
    CONF_POOL_NAME: "My Pool",
    CONF_VOLUME_M3: 40.0,
    CONF_SHAPE: "round",
}

CHEMISTRY_INPUT: dict[str, Any] = {
    CONF_TREATMENT: "chlorine",
    CONF_PH_ENTITY: "sensor.pool_ph",
    CONF_ORP_ENTITY: "sensor.pool_orp",
}

FILTRATION_INPUT: dict[str, Any] = {
    CONF_FILTRATION_KIND: "sand",
    CONF_PUMP_FLOW_M3H: 10.0,
    CONF_TEMPERATURE_ENTITY: "sensor.pool_temp",
}


class TestConfigFlow:
    """Tests for the initial config flow (user step -> chemistry -> filtration)."""

    async def test_user_step_shows_form(self, hass: HomeAssistant) -> None:
        """First step should show the pool basics form."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_chemistry_step_shows_form(self, hass: HomeAssistant) -> None:
        """After pool step, chemistry form should be shown."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "chemistry"

    async def test_filtration_step_shows_form(self, hass: HomeAssistant) -> None:
        """After chemistry step, filtration form should be shown."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "filtration"

    async def test_full_flow_creates_entry(self, hass: HomeAssistant) -> None:
        """Completing all steps should create a config entry."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)

        with patch("custom_components.poolman.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], FILTRATION_INPUT
            )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Pool"
        assert result["data"][CONF_VOLUME_M3] == 40.0
        assert result["data"][CONF_SHAPE] == "round"
        assert result["data"][CONF_TREATMENT] == "chlorine"
        assert result["data"][CONF_FILTRATION_KIND] == "sand"

    async def test_duplicate_unique_id_aborts(self, hass: HomeAssistant) -> None:
        """Setting up a pool with the same name should abort."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="My Pool",
            data={},
            unique_id="My Pool",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], POOL_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CHEMISTRY_INPUT)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], FILTRATION_INPUT)
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestOptionsFlow:
    """Tests for the options flow (chemistry -> filtration)."""

    async def test_options_flow_init_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Options flow init step should show chemistry form."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_filtration_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """After init step, filtration form should be shown."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], CHEMISTRY_INPUT
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "filtration"

    async def test_options_flow_creates_entry(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Completing options flow should create entry with merged options."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], CHEMISTRY_INPUT
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], FILTRATION_INPUT
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_TREATMENT] == "chlorine"
        assert result["data"][CONF_FILTRATION_KIND] == "sand"


async def _setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> PoolmanCoordinator:
    """Add a config entry to hass, set up mock states, and load the integration.

    Args:
        hass: The Home Assistant instance.
        entry: The mock config entry to set up.

    Returns:
        The coordinator from the loaded config entry.
    """
    entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


class TestHibernationWizard:
    """Tests for the hibernation wizard subentry flow."""

    async def test_user_step_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting the hibernation wizard should show the target mode form."""
        await _setup_entry(hass, mock_config_entry)

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_user_step_creates_subentry_and_sets_hibernating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Choosing a target mode should create a subentry and set HIBERNATING mode."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        assert coordinator.mode == PoolMode.ACTIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {CONF_TARGET_MODE: MODE_WINTER_PASSIVE},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert coordinator.mode == PoolMode.HIBERNATING

        # Verify the subentry was created with the right data
        subentries = list(mock_config_entry.subentries.values())
        assert len(subentries) == 1
        subentry = subentries[0]
        assert subentry.subentry_type == SUBENTRY_HIBERNATION
        assert subentry.data[CONF_TARGET_MODE] == MODE_WINTER_PASSIVE
        assert subentry.data[CONF_STARTED_AT] is not None
        assert subentry.data[CONF_COMPLETED_AT] is None
        assert "winter_passive" in subentry.title.lower()

    async def test_user_step_target_active_wintering(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Choosing active wintering should create a subentry with winter_active target."""
        coordinator = await _setup_entry(hass, mock_config_entry)

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {CONF_TARGET_MODE: MODE_WINTER_ACTIVE},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert coordinator.mode == PoolMode.HIBERNATING

        subentry = next(iter(mock_config_entry.subentries.values()))
        assert subentry.data[CONF_TARGET_MODE] == MODE_WINTER_ACTIVE
        assert "winter_active" in subentry.title.lower()

    async def test_guard_already_wintering_hibernating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting hibernation when already HIBERNATING should abort."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.HIBERNATING

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_wintering"

    async def test_guard_already_wintering_winter_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting hibernation when in WINTER_ACTIVE should abort."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_ACTIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_wintering"

    async def test_guard_already_wintering_winter_passive(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting hibernation when in WINTER_PASSIVE should abort."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_wintering"

    async def test_guard_hibernation_in_progress(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Starting a new hibernation when one is in progress should abort.

        When a subentry exists with no completed_at, the mode was restored
        to HIBERNATING by async_setup_entry, so the already_wintering guard
        fires first. If the user manually switched back to ACTIVE, the
        in-progress guard catches it instead.
        """
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive)",
                    "unique_id": None,
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)
        # Simulate user manually switching mode back to ACTIVE
        # while an uncompleted subentry still exists
        coordinator.mode = PoolMode.ACTIVE

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "hibernation_in_progress"

    async def test_guard_allows_new_after_completed(
        self,
        hass: HomeAssistant,
    ) -> None:
        """A completed hibernation subentry should not block starting a new one."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-11-15T10:00:00+00:00",
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive) - completed",
                    "unique_id": None,
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "user"},
        )
        # Should show form, not abort
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_reconfigure_shows_form(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring an in-progress hibernation should show the confirm form."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive)",
                    "unique_id": None,
                    "subentry_id": "test_sub_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "reconfigure", "subentry_id": "test_sub_id"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_confirm_completes_hibernation(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Confirming the reconfigure step should transition to the target mode."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive)",
                    "unique_id": None,
                    "subentry_id": "test_sub_id",
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)
        assert coordinator.mode == PoolMode.HIBERNATING  # restored from subentry

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "reconfigure", "subentry_id": "test_sub_id"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": True},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert coordinator.mode == PoolMode.WINTER_PASSIVE

        # Verify subentry was updated with completed_at
        subentry = entry.subentries["test_sub_id"]
        assert subentry.data[CONF_COMPLETED_AT] is not None
        assert "completed" in subentry.title.lower()

    async def test_reconfigure_confirm_active_wintering(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Completing hibernation targeting active wintering should transition correctly."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_ACTIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_active)",
                    "unique_id": None,
                    "subentry_id": "test_sub_id",
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "reconfigure", "subentry_id": "test_sub_id"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": True},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert coordinator.mode == PoolMode.WINTER_ACTIVE

    async def test_reconfigure_without_confirm_shows_error(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Submitting the reconfigure form without confirming should show an error."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive)",
                    "unique_id": None,
                    "subentry_id": "test_sub_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "reconfigure", "subentry_id": "test_sub_id"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        assert result["errors"] == {"confirm": "must_confirm"}

    async def test_reconfigure_already_completed_aborts(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring an already completed hibernation should abort."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_TARGET_MODE: MODE_WINTER_PASSIVE,
                        CONF_STARTED_AT: "2025-11-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-11-15T10:00:00+00:00",
                    },
                    "subentry_type": SUBENTRY_HIBERNATION,
                    "title": "Hibernation (winter_passive) - completed",
                    "unique_id": None,
                    "subentry_id": "test_sub_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_HIBERNATION),
            context={"source": "reconfigure", "subentry_id": "test_sub_id"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_completed"


def _all_steps_false() -> dict[str, bool]:
    """Return activation steps dict with all steps set to False."""
    return {step.value: False for step in ActivationStep}


def _all_steps_true() -> dict[str, bool]:
    """Return activation steps dict with all steps set to True."""
    return {step.value: True for step in ActivationStep}


class TestActivationWizard:
    """Tests for the activation wizard subentry flow."""

    async def test_user_step_shows_form(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting the activation wizard from a winter mode should show confirm form."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_user_step_creates_subentry_and_sets_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Confirming the user step should create a subentry and set ACTIVATING mode."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE
        assert coordinator.activation is None

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": True},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert coordinator.mode == PoolMode.ACTIVATING

        # Verify the subentry was created with correct data
        subentries = list(mock_config_entry.subentries.values())
        assert len(subentries) == 1
        subentry = subentries[0]
        assert subentry.subentry_type == SUBENTRY_ACTIVATION
        assert subentry.data[CONF_STARTED_AT] is not None
        assert subentry.data[CONF_COMPLETED_AT] is None
        assert subentry.data[CONF_STEPS] == _all_steps_false()
        assert subentry.title == "Activation"

    async def test_user_step_from_hibernating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting activation from HIBERNATING mode should succeed."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.HIBERNATING

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": True},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert coordinator.mode == PoolMode.ACTIVATING

    async def test_user_step_from_winter_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting activation from WINTER_ACTIVE mode should succeed."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_ACTIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": True},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert coordinator.mode == PoolMode.ACTIVATING

    async def test_user_step_without_confirm_shows_error(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Submitting the user form without confirming should show an error."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {"confirm": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"confirm": "must_confirm"}

    async def test_guard_not_wintering_active(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting activation when in ACTIVE mode should abort."""
        await _setup_entry(hass, mock_config_entry)
        # Default mode is ACTIVE

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "not_wintering"

    async def test_guard_not_wintering_activating(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ) -> None:
        """Starting activation when already in ACTIVATING mode should abort."""
        coordinator = await _setup_entry(hass, mock_config_entry)
        coordinator.mode = PoolMode.ACTIVATING

        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "not_wintering"

    async def test_guard_activation_in_progress(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Starting a new activation when one is in progress should abort.

        When the user manually switches back to a winter mode while an
        uncompleted activation subentry exists, the in-progress guard
        catches it.
        """
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: _all_steps_false(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)
        # Simulate user manually switching back to winter mode
        coordinator.mode = PoolMode.WINTER_PASSIVE

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "activation_in_progress"

    async def test_guard_allows_new_after_completed(
        self,
        hass: HomeAssistant,
    ) -> None:
        """A completed activation subentry should not block starting a new one."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-04-05T10:00:00+00:00",
                        CONF_STEPS: _all_steps_true(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation - completed",
                    "unique_id": None,
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)
        coordinator.mode = PoolMode.WINTER_PASSIVE

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "user"},
        )
        # Should show form, not abort
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_reconfigure_incomplete_aborts(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring an incomplete activation should abort with activation_incomplete."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: _all_steps_false(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                    "subentry_id": "test_act_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "reconfigure", "subentry_id": "test_act_id"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "activation_incomplete"

    async def test_reconfigure_partially_complete_aborts(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring a partially complete activation should abort."""
        steps = _all_steps_false()
        steps["remove_cover"] = True
        steps["raise_water_level"] = True

        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: steps,
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                    "subentry_id": "test_act_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "reconfigure", "subentry_id": "test_act_id"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "activation_incomplete"

    async def test_reconfigure_all_done_shows_form(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring a fully complete activation should show the finalization form."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: _all_steps_true(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                    "subentry_id": "test_act_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "reconfigure", "subentry_id": "test_act_id"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_confirm_completes_activation(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Confirming reconfigure with all steps done should complete the activation."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: None,
                        CONF_STEPS: _all_steps_true(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation",
                    "unique_id": None,
                    "subentry_id": "test_act_id",
                },
            ],
        )
        coordinator = await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "reconfigure", "subentry_id": "test_act_id"},
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert coordinator.mode == PoolMode.ACTIVE

        # Verify subentry was updated with completed_at
        subentry = entry.subentries["test_act_id"]
        assert subentry.data[CONF_COMPLETED_AT] is not None
        assert "completed" in subentry.title.lower()

    async def test_reconfigure_already_completed_aborts(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Reconfiguring an already completed activation should abort."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Pool",
            data=MOCK_CONFIG_DATA.copy(),
            version=1,
            minor_version=3,
            subentries_data=[
                {
                    "data": {
                        CONF_STARTED_AT: "2025-04-01T10:00:00+00:00",
                        CONF_COMPLETED_AT: "2025-04-05T10:00:00+00:00",
                        CONF_STEPS: _all_steps_true(),
                    },
                    "subentry_type": SUBENTRY_ACTIVATION,
                    "title": "Activation - completed",
                    "unique_id": None,
                    "subentry_id": "test_act_id",
                },
            ],
        )
        await _setup_entry(hass, entry)

        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, SUBENTRY_ACTIVATION),
            context={"source": "reconfigure", "subentry_id": "test_act_id"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_completed"
