"""Tests for the activation wizard domain logic."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.poolman.domain.activation import (
    ACTIVATION_STEPS,
    SHOCK_PRODUCT_VALUES,
    ActivationChecklist,
    ActivationStep,
)
from custom_components.poolman.domain.model import ChemicalProduct

# Fixed reference time for deterministic tests
NOW = datetime(2025, 3, 15, 10, 0, 0, tzinfo=UTC)


class TestActivationStep:
    """Tests for the ActivationStep enum."""

    def test_has_five_steps(self) -> None:
        """There should be exactly 5 activation steps."""
        assert len(ActivationStep) == 5

    def test_step_values(self) -> None:
        """Each step should have the expected string value."""
        assert ActivationStep.REMOVE_COVER == "remove_cover"
        assert ActivationStep.RAISE_WATER_LEVEL == "raise_water_level"
        assert ActivationStep.CLEAN_POOL_AND_FILTER == "clean_pool_and_filter"
        assert ActivationStep.SHOCK_TREATMENT == "shock_treatment"
        assert ActivationStep.INTENSIVE_FILTRATION == "intensive_filtration"

    def test_activation_steps_tuple_matches_enum(self) -> None:
        """ACTIVATION_STEPS tuple should contain all enum members in order."""
        assert tuple(ActivationStep) == ACTIVATION_STEPS
        assert len(ACTIVATION_STEPS) == 5


class TestShockProducts:
    """Tests for the SHOCK_PRODUCT_VALUES set."""

    def test_contains_expected_products(self) -> None:
        """SHOCK_PRODUCT_VALUES should contain the three shock chemicals."""
        assert ChemicalProduct.CHLORE_CHOC.value in SHOCK_PRODUCT_VALUES
        assert ChemicalProduct.BROMINE_SHOCK.value in SHOCK_PRODUCT_VALUES
        assert ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR.value in SHOCK_PRODUCT_VALUES

    def test_does_not_contain_non_shock_products(self) -> None:
        """Non-shock products should not be in SHOCK_PRODUCT_VALUES."""
        assert ChemicalProduct.PH_MINUS.value not in SHOCK_PRODUCT_VALUES
        assert ChemicalProduct.FLOCCULANT.value not in SHOCK_PRODUCT_VALUES

    def test_exactly_three_products(self) -> None:
        """There should be exactly 3 shock products."""
        assert len(SHOCK_PRODUCT_VALUES) == 3


class TestActivationChecklistInit:
    """Tests for ActivationChecklist initial state."""

    def test_all_steps_start_incomplete(self) -> None:
        """All steps should be False (incomplete) on creation."""
        checklist = ActivationChecklist(started_at=NOW)
        for step in ActivationStep:
            assert checklist.steps[step] is False

    def test_started_at_is_set(self) -> None:
        """started_at should match the provided datetime."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.started_at == NOW

    def test_all_steps_present(self) -> None:
        """Every ActivationStep should have an entry in steps."""
        checklist = ActivationChecklist(started_at=NOW)
        assert set(checklist.steps.keys()) == set(ActivationStep)


class TestActivationChecklistProperties:
    """Tests for ActivationChecklist computed properties."""

    def test_completed_steps_initially_empty(self) -> None:
        """No steps should be completed at the start."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.completed_steps == []

    def test_pending_steps_initially_all(self) -> None:
        """All steps should be pending at the start."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.pending_steps == list(ActivationStep)

    def test_current_step_initially_first(self) -> None:
        """Current step should be the first step initially."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.current_step == ActivationStep.REMOVE_COVER

    def test_is_complete_initially_false(self) -> None:
        """Checklist should not be complete initially."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.is_complete is False

    def test_progress_initially_zero(self) -> None:
        """Progress should be 0/5 initially."""
        checklist = ActivationChecklist(started_at=NOW)
        assert checklist.progress == (0, 5)

    def test_completed_steps_after_confirming(self) -> None:
        """Completed steps should include confirmed steps in order."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        checklist.confirm(ActivationStep.SHOCK_TREATMENT)
        assert checklist.completed_steps == [
            ActivationStep.REMOVE_COVER,
            ActivationStep.SHOCK_TREATMENT,
        ]

    def test_pending_steps_after_confirming(self) -> None:
        """Pending steps should exclude confirmed steps."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        assert ActivationStep.REMOVE_COVER not in checklist.pending_steps
        assert len(checklist.pending_steps) == 4

    def test_current_step_skips_completed(self) -> None:
        """Current step should be the first pending step, skipping completed ones."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        assert checklist.current_step == ActivationStep.RAISE_WATER_LEVEL

    def test_current_step_none_when_all_complete(self) -> None:
        """Current step should be None when all steps are done."""
        checklist = ActivationChecklist(started_at=NOW)
        for step in ActivationStep:
            checklist.confirm(step)
        assert checklist.current_step is None

    def test_progress_increments(self) -> None:
        """Progress should increment as steps are confirmed."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        assert checklist.progress == (1, 5)
        checklist.confirm(ActivationStep.RAISE_WATER_LEVEL)
        assert checklist.progress == (2, 5)

    def test_is_complete_when_all_done(self) -> None:
        """is_complete should be True when all steps are confirmed."""
        checklist = ActivationChecklist(started_at=NOW)
        for step in ActivationStep:
            checklist.confirm(step)
        assert checklist.is_complete is True


class TestActivationChecklistConfirm:
    """Tests for the confirm() method."""

    def test_confirm_marks_step_as_true(self) -> None:
        """Confirming a step should set it to True."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        assert checklist.steps[ActivationStep.REMOVE_COVER] is True

    def test_confirm_out_of_order(self) -> None:
        """Steps can be confirmed out of order."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.SHOCK_TREATMENT)
        assert checklist.steps[ActivationStep.SHOCK_TREATMENT] is True
        assert checklist.steps[ActivationStep.REMOVE_COVER] is False

    def test_confirm_already_confirmed_raises(self) -> None:
        """Confirming an already-confirmed step should raise ValueError."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        with pytest.raises(ValueError, match="already confirmed"):
            checklist.confirm(ActivationStep.REMOVE_COVER)

    def test_confirm_all_steps_sequentially(self) -> None:
        """All steps can be confirmed one by one."""
        checklist = ActivationChecklist(started_at=NOW)
        for step in ActivationStep:
            checklist.confirm(step)
        assert checklist.is_complete is True
        assert checklist.progress == (5, 5)

    def test_confirm_does_not_affect_other_steps(self) -> None:
        """Confirming one step should not change the status of others."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.CLEAN_POOL_AND_FILTER)
        for step in ActivationStep:
            if step == ActivationStep.CLEAN_POOL_AND_FILTER:
                assert checklist.steps[step] is True
            else:
                assert checklist.steps[step] is False


class TestActivationChecklistSerialization:
    """Tests for Pydantic serialization/deserialization."""

    def test_roundtrip_json(self) -> None:
        """Checklist should survive JSON round-trip."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.REMOVE_COVER)
        checklist.confirm(ActivationStep.SHOCK_TREATMENT)

        json_str = checklist.model_dump_json()
        restored = ActivationChecklist.model_validate_json(json_str)

        assert restored.started_at == checklist.started_at
        assert restored.steps == checklist.steps
        assert restored.completed_steps == checklist.completed_steps
        assert restored.pending_steps == checklist.pending_steps

    def test_roundtrip_dict(self) -> None:
        """Checklist should survive dict round-trip."""
        checklist = ActivationChecklist(started_at=NOW)
        checklist.confirm(ActivationStep.INTENSIVE_FILTRATION)

        data = checklist.model_dump()
        restored = ActivationChecklist.model_validate(data)

        assert restored.steps == checklist.steps
        assert restored.is_complete is False
        assert restored.progress == (1, 5)
