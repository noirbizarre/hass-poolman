"""Tests for domain action types."""

from __future__ import annotations

import logging

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.poolman.domain.action import (
    Action,
    ActionLog,
    ActionSource,
    ActionType,
)


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


class TestActionLog:
    """Tests for :class:`ActionLog` container."""

    _BASE = datetime(2026, 4, 19, 10, 0, tzinfo=UTC)

    def _action(
        self,
        action_id: str,
        *,
        offset_minutes: float = 0.0,
        source: ActionSource = ActionSource.USER,
        recommendation_id: str | None = None,
        duration: timedelta | None = None,
    ) -> Action:
        return Action(
            id=action_id,
            type=ActionType.CHEMICAL,
            source=source,
            treatment_id="ph_minus_300g",
            quantity=300.0,
            unit="g",
            timestamp=self._BASE + timedelta(minutes=offset_minutes),
            recommendation_id=recommendation_id,
            duration=duration,
        )

    def test_record_and_get(self) -> None:
        log = ActionLog()
        action = self._action("a1")
        log.record(action)
        assert log.get("a1") is action
        assert log.get("missing") is None

    def test_record_rejects_duplicate_id(self) -> None:
        log = ActionLog()
        log.record(self._action("a1"))
        with pytest.raises(ValueError, match="Duplicate action id"):
            log.record(self._action("a1", offset_minutes=10))

    def test_record_requires_recommendation_id_for_recommendation_source(self) -> None:
        log = ActionLog()
        with pytest.raises(ValueError, match="recommendation_id is required"):
            log.record(self._action("a1", source=ActionSource.RECOMMENDATION))

    def test_record_accepts_recommendation_source_with_id(self) -> None:
        log = ActionLog()
        log.record(
            self._action(
                "a1",
                source=ActionSource.RECOMMENDATION,
                recommendation_id="rec_ph_too_high",
            )
        )
        assert log.actions[0].recommendation_id == "rec_ph_too_high"

    def test_history_newest_first_with_limit(self) -> None:
        log = ActionLog()
        for i in range(5):
            log.record(self._action(f"a{i}", offset_minutes=i))
        history = log.history(limit=3)
        assert [a.id for a in history] == ["a4", "a3", "a2"]

    def test_history_default_limit(self) -> None:
        log = ActionLog()
        log.record(self._action("a1"))
        assert log.history() == [log.actions[0]]

    def test_active_filters_by_duration_window(self) -> None:
        log = ActionLog()
        log.record(self._action("no_dur"))  # no duration -> not active
        log.record(
            self._action("expired", offset_minutes=0, duration=timedelta(minutes=10))
        )  # ends at +10
        log.record(
            self._action("ongoing", offset_minutes=20, duration=timedelta(minutes=30))
        )  # ends at +50

        now = self._BASE + timedelta(minutes=30)
        active = log.active(now)
        assert [a.id for a in active] == ["ongoing"]

    def test_since(self) -> None:
        log = ActionLog()
        log.record(self._action("a0", offset_minutes=0))
        log.record(self._action("a1", offset_minutes=30))
        log.record(self._action("a2", offset_minutes=60))
        result = log.since(self._BASE + timedelta(minutes=30))
        assert [a.id for a in result] == ["a1", "a2"]

    def test_by_recommendation(self) -> None:
        log = ActionLog()
        log.record(self._action("a0"))
        log.record(
            self._action(
                "a1",
                source=ActionSource.RECOMMENDATION,
                recommendation_id="rec_x",
            )
        )
        log.record(
            self._action(
                "a2",
                offset_minutes=5,
                source=ActionSource.RECOMMENDATION,
                recommendation_id="rec_y",
            )
        )
        assert [a.id for a in log.by_recommendation("rec_x")] == ["a1"]

    def test_to_dict_from_dict_round_trip(self) -> None:
        log = ActionLog()
        log.record(self._action("a0", duration=timedelta(minutes=30)))
        log.record(
            self._action(
                "a1",
                offset_minutes=15,
                source=ActionSource.RECOMMENDATION,
                recommendation_id="rec_x",
            )
        )
        rebuilt = ActionLog.from_dict(log.to_dict())
        assert rebuilt.actions == log.actions

    def test_from_dict_drops_malformed_entries(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        payload = {
            "actions": [
                # Valid
                {
                    "id": "good",
                    "type": "chemical",
                    "source": "user",
                    "treatment_id": "t",
                    "quantity": 100.0,
                    "unit": "g",
                    "timestamp": self._BASE.isoformat(),
                    "recommendation_id": None,
                    "product_id": None,
                    "duration": None,
                },
                # Unknown enum value
                {
                    "id": "future",
                    "type": "unknown_type",
                    "source": "user",
                    "treatment_id": "t",
                    "quantity": 1.0,
                    "unit": "g",
                    "timestamp": self._BASE.isoformat(),
                },
                # Missing required field
                {"id": "broken"},
            ],
        }
        with caplog.at_level(logging.WARNING):
            log = ActionLog.from_dict(payload)
        assert [a.id for a in log.actions] == ["good"]
        assert sum(1 for r in caplog.records if "malformed action entry" in r.message) >= 2

    def test_from_dict_empty(self) -> None:
        assert ActionLog.from_dict({}).actions == []
