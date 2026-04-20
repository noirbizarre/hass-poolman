"""Tests for domain action types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.poolman.domain.action import Action, ActionSource, ActionType


class TestActionType:
    """Tests for ActionType StrEnum."""

    def test_values(self) -> None:
        assert ActionType.CHEMICAL == "chemical"
        assert ActionType.CLEANING == "cleaning"
        assert ActionType.MAINTENANCE == "maintenance"

    def test_construction_from_string(self) -> None:
        assert ActionType("chemical") == ActionType.CHEMICAL
        assert ActionType("cleaning") == ActionType.CLEANING
        assert ActionType("maintenance") == ActionType.MAINTENANCE

    def test_all_members(self) -> None:
        values = {m.value for m in ActionType}
        assert values == {"chemical", "cleaning", "maintenance"}

    def test_is_str(self) -> None:
        assert isinstance(ActionType.CHEMICAL, str)


class TestActionSource:
    """Tests for ActionSource StrEnum."""

    def test_values(self) -> None:
        assert ActionSource.USER == "user"
        assert ActionSource.RECOMMENDATION == "recommendation"
        assert ActionSource.AUTOMATION == "automation"

    def test_construction_from_string(self) -> None:
        assert ActionSource("user") == ActionSource.USER
        assert ActionSource("recommendation") == ActionSource.RECOMMENDATION
        assert ActionSource("automation") == ActionSource.AUTOMATION

    def test_all_members(self) -> None:
        values = {m.value for m in ActionSource}
        assert values == {"user", "recommendation", "automation"}

    def test_is_str(self) -> None:
        assert isinstance(ActionSource.USER, str)


class TestAction:
    """Tests for Action frozen dataclass."""

    _TS = datetime(2026, 4, 19, 10, 0, tzinfo=UTC)

    def _make_action(
        self,
        *,
        action_id: str = "act_20260419_ph_minus",
        action_type: ActionType = ActionType.CHEMICAL,
        source: ActionSource = ActionSource.USER,
        treatment_id: str = "ph_minus_300g",
        quantity: float = 300.0,
        unit: str = "g",
        timestamp: datetime | None = None,
        recommendation_id: str | None = None,
        product_id: str | None = None,
        duration: timedelta | None = None,
    ) -> Action:
        return Action(
            id=action_id,
            type=action_type,
            source=source,
            treatment_id=treatment_id,
            quantity=quantity,
            unit=unit,
            timestamp=timestamp or self._TS,
            recommendation_id=recommendation_id,
            product_id=product_id,
            duration=duration,
        )

    def test_creation_minimal(self) -> None:
        action = self._make_action()
        assert action.id == "act_20260419_ph_minus"
        assert action.type == ActionType.CHEMICAL
        assert action.source == ActionSource.USER
        assert action.treatment_id == "ph_minus_300g"
        assert action.quantity == 300.0
        assert action.unit == "g"
        assert action.timestamp == self._TS
        assert action.recommendation_id is None
        assert action.product_id is None
        assert action.duration is None

    def test_creation_with_optional_fields(self) -> None:
        action = self._make_action(
            recommendation_id="rec_ph_too_high",
            product_id="ph_minus",
            duration=timedelta(minutes=30),
        )
        assert action.recommendation_id == "rec_ph_too_high"
        assert action.product_id == "ph_minus"
        assert action.duration == timedelta(minutes=30)

    def test_frozen(self) -> None:
        """Action should be immutable."""
        action = self._make_action()
        with pytest.raises(FrozenInstanceError):
            action.quantity = 200.0  # type: ignore[misc]  # ty: ignore[invalid-assignment]

    def test_equality(self) -> None:
        a1 = self._make_action()
        a2 = self._make_action()
        assert a1 == a2

    def test_inequality_different_quantity(self) -> None:
        a1 = self._make_action(quantity=100.0)
        a2 = self._make_action(quantity=200.0)
        assert a1 != a2

    def test_source_recommendation_with_id(self) -> None:
        """Actions from a recommendation should carry the recommendation_id."""
        action = self._make_action(
            source=ActionSource.RECOMMENDATION,
            recommendation_id="rec_ph_too_high",
        )
        assert action.source == ActionSource.RECOMMENDATION
        assert action.recommendation_id == "rec_ph_too_high"

    def test_non_chemical_action(self) -> None:
        """Cleaning actions may have no product_id."""
        action = self._make_action(
            action_type=ActionType.CLEANING,
            treatment_id="vacuum_floor",
            quantity=45.0,
            unit="min",
        )
        assert action.type == ActionType.CLEANING
        assert action.product_id is None
