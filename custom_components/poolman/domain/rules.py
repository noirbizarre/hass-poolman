"""Extensible rule engine for pool management.

Provides a base Rule class and built-in rules for pH, sanitizer, and filtration.
New rules can be added by subclassing Rule and registering in the engine.
No Home Assistant dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .chemistry import (
    CYA_MAX,
    CYA_MIN,
    HARDNESS_MAX,
    HARDNESS_MIN,
    ORP_MAX,
    ORP_MIN_ACCEPTABLE,
    PH_MAX,
    PH_MIN,
    PH_TARGET,
    PH_TOLERANCE,
    TAC_MAX,
    TAC_MIN,
    compute_cya_adjustment,
    compute_hardness_adjustment,
    compute_ph_adjustment,
    compute_sanitizer_status,
    compute_tac_adjustment,
)
from .filtration import compute_filtration_duration
from .model import (
    ActionKind,
    Pool,
    PoolMode,
    PoolReading,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    Severity,
    TreatmentType,
)

# Human-readable labels for sanitizer products by treatment type and action
_SANITIZER_MESSAGES: dict[TreatmentType, dict[str, str]] = {
    TreatmentType.CHLORINE: {
        "shock": "Shock chlorination required (ORP critically low)",
        "regular": "Add chlorine tablets (ORP below {orp_min} mV)",
        "excess": "ORP too high, reduce chlorine dosage",
    },
    TreatmentType.SALT_ELECTROLYSIS: {
        "shock": "Shock chlorination required (ORP critically low)",
        "regular": "Check salt level and electrolysis cell (ORP below {orp_min} mV)",
        "excess": "ORP too high, reduce electrolysis output",
    },
    TreatmentType.BROMINE: {
        "shock": "Bromine shock required (ORP critically low)",
        "regular": "Add bromine tablets (ORP below {orp_min} mV)",
        "excess": "ORP too high, reduce bromine dosage",
    },
    TreatmentType.ACTIVE_OXYGEN: {
        "shock": "Active oxygen shock required (ORP critically low)",
        "regular": "Add active oxygen tablets (ORP below {orp_min} mV)",
        "excess": "ORP too high, reduce active oxygen dosage",
    },
}


class Rule(ABC):
    """Base class for pool management rules.

    Each rule evaluates the current pool state and returns zero or more
    recommendations. Rules should be stateless and side-effect free.
    """

    @abstractmethod
    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate the rule and return recommendations.

        Args:
            pool: Pool physical characteristics.
            reading: Current sensor readings.
            mode: Current operational mode.

        Returns:
            List of recommendations (empty if the rule doesn't apply).
        """


class PhRule(Rule):
    """Rule for pH level adjustments."""

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate pH level and recommend adjustments."""
        if mode == PoolMode.WINTER_PASSIVE or reading.ph is None:
            return []

        result = compute_ph_adjustment(pool, reading)
        if result is None:
            return []

        # Determine priority and kind based on how far from target
        delta = abs(reading.ph - PH_TARGET)
        if reading.ph < PH_MIN or reading.ph > PH_MAX:
            priority = RecommendationPriority.HIGH
            kind = ActionKind.REQUIREMENT
        elif delta > PH_TOLERANCE * 3:
            priority = RecommendationPriority.MEDIUM
            kind = ActionKind.SUGGESTION
        else:
            priority = RecommendationPriority.LOW
            kind = ActionKind.SUGGESTION

        return [
            Recommendation(
                type=RecommendationType.CHEMICAL,
                priority=priority,
                kind=kind,
                message=f"Add {result.quantity_g:.0f}g of {result.product}",
                product=result.product,
                quantity_g=result.quantity_g,
            )
        ]


class SanitizerRule(Rule):
    """Rule for sanitizer level evaluation based on ORP and treatment type."""

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate sanitizer via ORP and recommend treatment adapted to treatment type."""
        if mode == PoolMode.WINTER_PASSIVE or reading.orp is None:
            return []

        result = compute_sanitizer_status(reading, pool.treatment)
        if result is None:
            return []

        messages = _SANITIZER_MESSAGES[pool.treatment]

        if result.severity == Severity.CRITICAL:
            priority = RecommendationPriority.CRITICAL
            kind = ActionKind.REQUIREMENT
            message = messages["shock"]
        elif reading.orp > ORP_MAX:
            priority = RecommendationPriority.MEDIUM
            kind = ActionKind.REQUIREMENT
            message = messages["excess"]
        else:
            priority = RecommendationPriority.MEDIUM
            kind = ActionKind.SUGGESTION
            message = messages["regular"].format(orp_min=ORP_MIN_ACCEPTABLE)

        return [
            Recommendation(
                type=RecommendationType.CHEMICAL,
                priority=priority,
                kind=kind,
                message=message,
                product=result.product,
            )
        ]


class FiltrationRule(Rule):
    """Rule for filtration duration recommendation."""

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Recommend filtration duration."""
        hours = compute_filtration_duration(pool, reading, mode)
        if hours is None:
            return []

        if mode in (PoolMode.WINTER_ACTIVE, PoolMode.WINTER_PASSIVE):
            priority = RecommendationPriority.LOW
        elif hours >= 12:
            priority = RecommendationPriority.MEDIUM
        else:
            priority = RecommendationPriority.LOW

        return [
            Recommendation(
                type=RecommendationType.FILTRATION,
                priority=priority,
                kind=ActionKind.SUGGESTION,
                message=f"Run filtration for {hours:.1f} hours today",
            )
        ]


class TacRule(Rule):
    """Rule for total alkalinity (TAC) adjustment."""

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate TAC and recommend adjustments."""
        if mode == PoolMode.WINTER_PASSIVE or reading.tac is None:
            return []

        result = compute_tac_adjustment(pool, reading)
        if result is None:
            return []

        if reading.tac < TAC_MIN:
            priority = RecommendationPriority.MEDIUM
            kind = ActionKind.REQUIREMENT
            message = f"Add {result.quantity_g:.0f}g of TAC+ (alkalinity too low)"
        elif reading.tac > TAC_MAX:
            priority = RecommendationPriority.LOW
            kind = ActionKind.SUGGESTION
            message = "Alkalinity too high, pH- treatments will help lower it"
        else:
            return []

        return [
            Recommendation(
                type=RecommendationType.CHEMICAL,
                priority=priority,
                kind=kind,
                message=message,
                product=result.product,
                quantity_g=result.quantity_g,
            )
        ]


class AlgaeRiskRule(Rule):
    """Rule for algae risk detection based on temperature and ORP."""

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate algae risk from warm water and low ORP."""
        if mode == PoolMode.WINTER_PASSIVE:
            return []

        if reading.temp_c is None or reading.orp is None:
            return []

        if reading.temp_c > 28 and reading.orp < ORP_MIN_ACCEPTABLE:
            return [
                Recommendation(
                    type=RecommendationType.ALERT,
                    priority=RecommendationPriority.HIGH,
                    kind=ActionKind.REQUIREMENT,
                    message="High algae risk (warm water + low ORP)",
                )
            ]

        return []


class CyaRule(Rule):
    """Rule for cyanuric acid (stabilizer) level adjustment.

    CYA below minimum requires adding stabilizer (with dosage).
    CYA above maximum has no chemical fix -- recommends partial drain.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate CYA level and recommend adjustments."""
        if mode == PoolMode.WINTER_PASSIVE or reading.cya is None:
            return []

        if reading.cya < CYA_MIN:
            result = compute_cya_adjustment(pool, reading)
            if result is None:
                return []
            return [
                Recommendation(
                    type=RecommendationType.CHEMICAL,
                    priority=RecommendationPriority.MEDIUM,
                    kind=ActionKind.REQUIREMENT,
                    message=f"Add {result.quantity_g:.0f}g of stabilizer (CYA too low)",
                    product=result.product,
                    quantity_g=result.quantity_g,
                )
            ]

        if reading.cya > CYA_MAX:
            return [
                Recommendation(
                    type=RecommendationType.ALERT,
                    priority=RecommendationPriority.LOW,
                    kind=ActionKind.REQUIREMENT,
                    message="CYA too high, consider partial water drain",
                )
            ]

        return []


class HardnessRule(Rule):
    """Rule for calcium hardness level adjustment.

    Hardness below minimum requires adding calcium hardness increaser
    (with dosage). Hardness above maximum has no chemical fix -- recommends
    partial drain.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Evaluate calcium hardness and recommend adjustments."""
        if mode == PoolMode.WINTER_PASSIVE or reading.hardness is None:
            return []

        if reading.hardness < HARDNESS_MIN:
            result = compute_hardness_adjustment(pool, reading)
            if result is None:
                return []
            return [
                Recommendation(
                    type=RecommendationType.CHEMICAL,
                    priority=RecommendationPriority.MEDIUM,
                    kind=ActionKind.REQUIREMENT,
                    message=(
                        f"Add {result.quantity_g:.0f}g of calcium hardness"
                        " increaser (hardness too low)"
                    ),
                    product=result.product,
                    quantity_g=result.quantity_g,
                )
            ]

        if reading.hardness > HARDNESS_MAX:
            return [
                Recommendation(
                    type=RecommendationType.ALERT,
                    priority=RecommendationPriority.LOW,
                    kind=ActionKind.REQUIREMENT,
                    message="Calcium hardness too high, consider partial water drain",
                )
            ]

        return []


class RuleEngine:
    """Engine that evaluates all registered rules against pool state.

    Rules are evaluated in registration order. All applicable recommendations
    are collected and returned.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        """Initialize the rule engine with optional rules.

        Args:
            rules: List of rules to register. If None, uses default rules.
        """
        self.rules = rules if rules is not None else self._default_rules()

    @staticmethod
    def _default_rules() -> list[Rule]:
        """Return the default set of built-in rules."""
        return [
            PhRule(),
            SanitizerRule(),
            FiltrationRule(),
            TacRule(),
            AlgaeRiskRule(),
            CyaRule(),
            HardnessRule(),
        ]

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
    ) -> list[Recommendation]:
        """Run all rules and collect recommendations.

        Args:
            pool: Pool physical characteristics.
            reading: Current sensor readings.
            mode: Current operational mode.

        Returns:
            All recommendations from all rules, sorted by priority (highest first).
        """
        recommendations: list[Recommendation] = []
        for rule in self.rules:
            recommendations.extend(rule.evaluate(pool, reading, mode))

        # Sort by priority (critical first)
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations
