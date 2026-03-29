"""Pool water chemistry calculations.

Pure domain logic for computing chemical adjustments.
No Home Assistant dependencies.
"""

from __future__ import annotations

from .model import (
    ChemicalProduct,
    DosageAdjustment,
    Pool,
    PoolReading,
    SanitizerStatus,
    Severity,
    TreatmentType,
)

# Target ranges for pool chemistry
PH_TARGET: float = 7.2
PH_TOLERANCE: float = 0.1
PH_MIN: float = 6.8
PH_MAX: float = 7.8

ORP_MIN_CRITICAL: int = 650
ORP_MIN_ACCEPTABLE: int = 720
ORP_TARGET: int = 750
ORP_MAX: int = 900

TAC_MIN: float = 80.0
TAC_TARGET: float = 120.0
TAC_MAX: float = 150.0

CYA_MIN: float = 20.0
CYA_TARGET: float = 40.0
CYA_MAX: float = 75.0

HARDNESS_MIN: float = 150.0
HARDNESS_TARGET: float = 250.0
HARDNESS_MAX: float = 400.0

# Dosage constants (grams per 10m3 for 0.2 pH change)
PH_DOSAGE_PER_10M3: float = 150.0
PH_DOSAGE_STEP: float = 0.2

# Mapping from treatment type to sanitizer products
_SANITIZER_PRODUCTS: dict[TreatmentType, dict[str, ChemicalProduct]] = {
    TreatmentType.CHLORINE: {
        "shock": ChemicalProduct.CHLORE_CHOC,
        "regular": ChemicalProduct.GALET_CHLORE,
        "excess": ChemicalProduct.NEUTRALIZER,
    },
    TreatmentType.SALT_ELECTROLYSIS: {
        "shock": ChemicalProduct.CHLORE_CHOC,
        "regular": ChemicalProduct.SALT,
        "excess": ChemicalProduct.NEUTRALIZER,
    },
    TreatmentType.BROMINE: {
        "shock": ChemicalProduct.BROMINE_SHOCK,
        "regular": ChemicalProduct.BROMINE_TABLET,
        "excess": ChemicalProduct.NEUTRALIZER,
    },
    TreatmentType.ACTIVE_OXYGEN: {
        "shock": ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR,
        "regular": ChemicalProduct.ACTIVE_OXYGEN_TABLET,
        "excess": ChemicalProduct.NEUTRALIZER,
    },
}


def compute_ph_adjustment(pool: Pool, reading: PoolReading) -> DosageAdjustment | None:
    """Compute pH adjustment recommendation.

    Returns a dosage adjustment with product type and quantity, or None if pH is in range.

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product and quantity, or None if no adjustment needed.
    """
    if reading.ph is None:
        return None

    delta = reading.ph - PH_TARGET

    if abs(delta) < PH_TOLERANCE:
        return None

    quantity = abs(delta / PH_DOSAGE_STEP) * PH_DOSAGE_PER_10M3 * (pool.volume_m3 / 10)
    product = ChemicalProduct.PH_MINUS if delta > 0 else ChemicalProduct.PH_PLUS

    return DosageAdjustment(product=product, quantity_g=round(quantity, 0))


def compute_sanitizer_status(
    reading: PoolReading,
    treatment: TreatmentType = TreatmentType.CHLORINE,
) -> SanitizerStatus | None:
    """Evaluate sanitizer status from ORP reading, adapted to the treatment type.

    Args:
        reading: Current sensor readings.
        treatment: Water treatment method used in the pool.

    Returns:
        SanitizerStatus with product and severity, or None if ORP is acceptable.
    """
    if reading.orp is None:
        return None

    products = _SANITIZER_PRODUCTS[treatment]

    if reading.orp < ORP_MIN_CRITICAL:
        return SanitizerStatus(product=products["shock"], severity=Severity.CRITICAL)
    if reading.orp < ORP_MIN_ACCEPTABLE:
        return SanitizerStatus(product=products["regular"], severity=Severity.MEDIUM)
    if reading.orp > ORP_MAX:
        return SanitizerStatus(product=products["excess"], severity=Severity.MEDIUM)

    return None


def compute_tac_adjustment(pool: Pool, reading: PoolReading) -> DosageAdjustment | None:
    """Compute total alkalinity adjustment recommendation.

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product and quantity, or None if TAC is in range.
    """
    if reading.tac is None:
        return None

    if reading.tac < TAC_MIN:
        # Roughly 18g of sodium bicarbonate per m3 to raise TAC by 10 ppm
        delta_ppm = TAC_TARGET - reading.tac
        quantity = (delta_ppm / 10) * 18 * pool.volume_m3
        return DosageAdjustment(product=ChemicalProduct.TAC_PLUS, quantity_g=round(quantity, 0))

    if reading.tac > TAC_MAX:
        # pH- lowers TAC indirectly, no specific dosage
        return DosageAdjustment(product=ChemicalProduct.PH_MINUS)

    return None


def compute_water_quality_score(reading: PoolReading) -> int | None:
    """Compute an overall water quality score from 0 to 100.

    Each parameter contributes to the score proportionally.
    Returns None if no readings are available.

    Args:
        reading: Current sensor readings.

    Returns:
        Score from 0 (poor) to 100 (perfect), or None.
    """
    scores: list[float] = []

    if reading.ph is not None:
        scores.append(_score_range(reading.ph, PH_MIN, PH_TARGET, PH_MAX))

    if reading.orp is not None:
        scores.append(_score_range(reading.orp, ORP_MIN_CRITICAL, ORP_TARGET, ORP_MAX))

    if reading.tac is not None:
        scores.append(_score_range(reading.tac, TAC_MIN, TAC_TARGET, TAC_MAX))

    if reading.cya is not None:
        scores.append(_score_range(reading.cya, CYA_MIN, CYA_TARGET, CYA_MAX))

    if reading.hardness is not None:
        scores.append(_score_range(reading.hardness, HARDNESS_MIN, HARDNESS_TARGET, HARDNESS_MAX))

    if not scores:
        return None

    return round(sum(scores) / len(scores))


def _score_range(value: float, minimum: float, target: float, maximum: float) -> float:
    """Score a value against an ideal range.

    Returns 100 if at target, decreasing linearly towards min/max,
    and 0 if outside the acceptable range.

    Args:
        value: The measured value.
        minimum: Lower bound of acceptable range.
        target: Ideal value.
        maximum: Upper bound of acceptable range.

    Returns:
        Score from 0 to 100.
    """
    if value < minimum or value > maximum:
        return 0.0

    if value <= target:
        return 100.0 * (value - minimum) / (target - minimum) if target != minimum else 100.0

    return 100.0 * (maximum - value) / (maximum - target) if maximum != target else 100.0
