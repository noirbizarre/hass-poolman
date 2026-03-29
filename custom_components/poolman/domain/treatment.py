"""Pool chemistry treatment tracking.

Pure domain logic for tracking chemical treatments, computing activity status,
and determining swimming safety based on product-specific wait times.
No Home Assistant dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from .model import ActiveTreatment, ChemicalProduct


class TreatmentProfile(BaseModel, frozen=True):
    """Safety and activity profile for a chemical product.

    Attributes:
        activity_hours: How long the product is actively working after application.
        safety_hours: Swim wait time after application before the pool is safe.
    """

    activity_hours: float = Field(ge=0, description="Hours the product remains active")
    safety_hours: float = Field(ge=0, description="Hours to wait before swimming")


# Safety and activity profiles for each chemical product.
# Sources: standard pool chemistry guidelines and manufacturer recommendations.
TREATMENT_PROFILES: dict[ChemicalProduct, TreatmentProfile] = {
    # pH adjustments: allow full water circulation (6h)
    ChemicalProduct.PH_MINUS: TreatmentProfile(activity_hours=6, safety_hours=6),
    ChemicalProduct.PH_PLUS: TreatmentProfile(activity_hours=6, safety_hours=6),
    # Chlorine: shock requires 24h wait; tablets are continuous (no wait)
    ChemicalProduct.CHLORE_CHOC: TreatmentProfile(activity_hours=48, safety_hours=24),
    ChemicalProduct.GALET_CHLORE: TreatmentProfile(activity_hours=0, safety_hours=0),
    # Neutralizer: fast-acting (4h)
    ChemicalProduct.NEUTRALIZER: TreatmentProfile(activity_hours=4, safety_hours=4),
    # Alkalinity: allow circulation (6h)
    ChemicalProduct.TAC_PLUS: TreatmentProfile(activity_hours=6, safety_hours=6),
    # Salt: dissolution time (24h)
    ChemicalProduct.SALT: TreatmentProfile(activity_hours=24, safety_hours=24),
    # Bromine: shock requires 24h wait; tablets are continuous (no wait)
    ChemicalProduct.BROMINE_TABLET: TreatmentProfile(activity_hours=0, safety_hours=0),
    ChemicalProduct.BROMINE_SHOCK: TreatmentProfile(activity_hours=48, safety_hours=24),
    # Active oxygen: shock requires 24h wait; tablets are continuous (no wait)
    ChemicalProduct.ACTIVE_OXYGEN_TABLET: TreatmentProfile(activity_hours=0, safety_hours=0),
    ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR: TreatmentProfile(activity_hours=48, safety_hours=24),
    # Flocculant: must settle and vacuum (48h activity, 24h swim wait)
    ChemicalProduct.FLOCCULANT: TreatmentProfile(activity_hours=48, safety_hours=24),
    # Anti-algae: algicide treatment (24h)
    ChemicalProduct.ANTI_ALGAE: TreatmentProfile(activity_hours=24, safety_hours=24),
    # Stabilizer (CYA): dissolution time (24h)
    ChemicalProduct.STABILIZER: TreatmentProfile(activity_hours=24, safety_hours=24),
    # Clarifier: swimming-compatible, no wait
    ChemicalProduct.CLARIFIER: TreatmentProfile(activity_hours=0, safety_hours=0),
    # Metal sequestrant: swimming-compatible, no wait
    ChemicalProduct.METAL_SEQUESTRANT: TreatmentProfile(activity_hours=0, safety_hours=0),
    # Calcium hardness increaser: allow circulation (6h)
    ChemicalProduct.CALCIUM_HARDNESS_INCREASER: TreatmentProfile(activity_hours=6, safety_hours=6),
    # Winterizing product: pool is closed, no swim wait
    ChemicalProduct.WINTERIZING_PRODUCT: TreatmentProfile(activity_hours=0, safety_hours=0),
}


def compute_active_treatments(
    entries: list[tuple[ChemicalProduct, datetime, float | None]],
    now: datetime,
) -> list[ActiveTreatment]:
    """Compute which treatments are still active or within their safety window.

    A treatment is considered active if either its activity period or its safety
    period has not yet elapsed.

    Args:
        entries: List of (product, applied_at, quantity_g) tuples from event entities.
        now: Current time for comparison.

    Returns:
        List of ActiveTreatment for treatments still active or within safety window.
    """
    active: list[ActiveTreatment] = []
    for product, applied_at, quantity_g in entries:
        profile = TREATMENT_PROFILES[product]
        active_until = applied_at + timedelta(hours=profile.activity_hours)
        safe_at = applied_at + timedelta(hours=profile.safety_hours)

        if now < active_until or now < safe_at:
            active.append(
                ActiveTreatment(
                    product=product,
                    applied_at=applied_at,
                    active_until=active_until,
                    safe_at=safe_at,
                    quantity_g=quantity_g,
                )
            )

    return active


def compute_swimming_safe(active_treatments: list[ActiveTreatment], now: datetime) -> bool:
    """Determine if the pool is safe for swimming.

    The pool is safe when all active treatment safety periods have elapsed.

    Args:
        active_treatments: List of currently active treatments.
        now: Current time for comparison.

    Returns:
        True if all safety periods have elapsed and swimming is safe.
    """
    return all(now >= t.safe_at for t in active_treatments)


def compute_safe_at(active_treatments: list[ActiveTreatment]) -> datetime | None:
    """Compute when the pool will next be safe for swimming.

    Args:
        active_treatments: List of currently active treatments.

    Returns:
        The latest safe_at time across all active treatments,
        or None if the pool is already safe (no active safety periods).
    """
    unsafe = [t for t in active_treatments if t.safe_at > t.applied_at]
    if not unsafe:
        return None
    return max(t.safe_at for t in unsafe)
