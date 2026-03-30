"""Activation wizard domain logic.

Pure Python models for the step-by-step activation process that brings
a pool out of hibernation. No Home Assistant dependencies.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ActivationStep(StrEnum):
    """Steps in the activation wizard.

    Ordered from first to last in the activation process.
    Manual steps require explicit user confirmation via a service call.
    Auto-detectable steps are confirmed automatically when the corresponding
    system event occurs (e.g., shock treatment recorded, filtration cycle
    completed).
    """

    REMOVE_COVER = "remove_cover"
    RAISE_WATER_LEVEL = "raise_water_level"
    CLEAN_POOL_AND_FILTER = "clean_pool_and_filter"
    SHOCK_TREATMENT = "shock_treatment"
    INTENSIVE_FILTRATION = "intensive_filtration"


# Chemical product values that auto-confirm the shock_treatment step.
# Defined as plain strings to avoid a circular import with model.py.
# These must match ChemicalProduct enum values.
SHOCK_PRODUCT_VALUES: frozenset[str] = frozenset(
    {
        "chlore_choc",
        "bromine_shock",
        "active_oxygen_activator",
    }
)

# Ordered list of all activation steps for iteration
ACTIVATION_STEPS: tuple[ActivationStep, ...] = tuple(ActivationStep)


class ActivationChecklist(BaseModel):
    """Tracks progress through the activation wizard.

    Each step starts as incomplete (False) and is marked as complete (True)
    either by the user via a service call or automatically by the system
    when the corresponding event is detected.

    Attributes:
        started_at: When the activation process was started.
        steps: Mapping of each step to its completion status.
    """

    started_at: datetime
    steps: dict[ActivationStep, bool] = Field(
        default_factory=lambda: dict.fromkeys(ActivationStep, False),
    )

    @property
    def completed_steps(self) -> list[ActivationStep]:
        """Return the list of completed steps in order."""
        return [step for step in ACTIVATION_STEPS if self.steps.get(step, False)]

    @property
    def pending_steps(self) -> list[ActivationStep]:
        """Return the list of pending (incomplete) steps in order."""
        return [step for step in ACTIVATION_STEPS if not self.steps.get(step, False)]

    @property
    def current_step(self) -> ActivationStep | None:
        """Return the first pending step, or None if all steps are complete."""
        pending = self.pending_steps
        return pending[0] if pending else None

    @property
    def is_complete(self) -> bool:
        """Return True if all activation steps have been completed."""
        return all(self.steps.values())

    @property
    def progress(self) -> tuple[int, int]:
        """Return the number of completed steps and total steps.

        Returns:
            Tuple of (completed_count, total_count).
        """
        total = len(ACTIVATION_STEPS)
        completed = sum(1 for v in self.steps.values() if v)
        return completed, total

    def confirm(self, step: ActivationStep) -> None:
        """Mark an activation step as completed.

        Args:
            step: The step to confirm.

        Raises:
            ValueError: If the step has already been confirmed.
        """
        if self.steps.get(step, False):
            msg = f"Activation step '{step}' is already confirmed"
            raise ValueError(msg)
        self.steps[step] = True
