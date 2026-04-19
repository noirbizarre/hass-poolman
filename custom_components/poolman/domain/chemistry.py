"""Pool water chemistry calculations.

Pure domain logic for computing chemical adjustments.
No Home Assistant dependencies.
"""

from __future__ import annotations

from .model import (
    ChemicalProduct,
    ChemistryReport,
    ChemistryStatus,
    DosageAdjustment,
    MetricName,
    ParameterReport,
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

FREE_CHLORINE_MIN: float = 1.0
FREE_CHLORINE_TARGET: float = 2.0
FREE_CHLORINE_MAX: float = 3.0

SALT_MIN: float = 2700.0
SALT_TARGET: float = 3200.0
SALT_MAX: float = 3400.0

# TDS (Total Dissolved Solids) target ranges for freshwater pools (ppm).
# Salt electrolysis pools are excluded from TDS evaluation because dissolved
# salt naturally raises TDS well above these thresholds.
TDS_MIN: float = 250.0
TDS_TARGET: float = 500.0
TDS_MAX: float = 1500.0

# Default EC-to-TDS conversion factor (configurable per pool)
EC_TO_TDS_DEFAULT_FACTOR: float = 0.5

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


# CYA dosage: 1g of cyanuric acid per 1 m3 raises CYA by 1 ppm
CYA_DOSAGE_PER_M3_PER_PPM: float = 1.0

# Hardness dosage: ~1.5g of CaCl2 per 1 m3 raises hardness by 1 ppm
HARDNESS_DOSAGE_PER_M3_PER_PPM: float = 1.5

# Salt dosage: ~3 kg of salt per 1 m3 raises salt by 1000 ppm
SALT_DOSAGE_PER_M3_PER_1000PPM: float = 3000.0


def compute_cya_adjustment(pool: Pool, reading: PoolReading) -> DosageAdjustment | None:
    """Compute cyanuric acid (stabilizer) adjustment recommendation.

    Uses 1 g of cyanuric acid per m3 to raise CYA by 1 ppm.
    Returns None when CYA is within range or above maximum (no chemical fix
    for excess CYA -- partial drain is the only option).

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product and quantity, or None if CYA is in range
        or no chemical fix is available.
    """
    if reading.cya is None:
        return None

    if reading.cya < CYA_MIN:
        delta_ppm = CYA_TARGET - reading.cya
        quantity = delta_ppm * CYA_DOSAGE_PER_M3_PER_PPM * pool.volume_m3
        return DosageAdjustment(product=ChemicalProduct.STABILIZER, quantity_g=round(quantity, 0))

    # CYA above max: no chemical product can lower it
    return None


def compute_hardness_adjustment(pool: Pool, reading: PoolReading) -> DosageAdjustment | None:
    """Compute calcium hardness adjustment recommendation.

    Uses ~1.5 g of CaCl2 per m3 to raise hardness by 1 ppm.
    Returns None when hardness is within range or above maximum (no chemical
    fix for excess hardness -- partial drain is the only option).

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product and quantity, or None if hardness is in
        range or no chemical fix is available.
    """
    if reading.hardness is None:
        return None

    if reading.hardness < HARDNESS_MIN:
        delta_ppm = HARDNESS_TARGET - reading.hardness
        quantity = delta_ppm * HARDNESS_DOSAGE_PER_M3_PER_PPM * pool.volume_m3
        return DosageAdjustment(
            product=ChemicalProduct.CALCIUM_HARDNESS_INCREASER,
            quantity_g=round(quantity, 0),
        )

    # Hardness above max: no chemical product can lower it
    return None


def compute_free_chlorine_adjustment(reading: PoolReading) -> DosageAdjustment | None:
    """Evaluate free chlorine level and return a dosage adjustment if out of range.

    Unlike other chemistry adjustments, no precise dosage can be calculated for
    free chlorine because the effect depends on many factors (CYA level, UV
    exposure, bather load). The recommendation points to the appropriate product
    without a specific gram amount.

    Args:
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product (no quantity), or None if free chlorine
        is within range.
    """
    if reading.free_chlorine is None:
        return None

    if reading.free_chlorine < FREE_CHLORINE_MIN:
        return DosageAdjustment(product=ChemicalProduct.CHLORE_CHOC)

    if reading.free_chlorine > FREE_CHLORINE_MAX:
        return DosageAdjustment(product=ChemicalProduct.NEUTRALIZER)

    return None


def compute_salt_adjustment(pool: Pool, reading: PoolReading) -> DosageAdjustment | None:
    """Compute salt level adjustment recommendation.

    Uses ~3 kg of salt per m3 to raise salt by 1000 ppm.
    Returns None when salt is within range or above maximum (no chemical
    fix for excess salt -- partial drain is the only option).

    Args:
        pool: Pool physical characteristics.
        reading: Current sensor readings.

    Returns:
        DosageAdjustment with product and quantity, or None if salt is in
        range or no chemical fix is available.
    """
    if reading.salt is None:
        return None

    if reading.salt < SALT_MIN:
        delta_ppm = SALT_TARGET - reading.salt
        quantity = (delta_ppm / 1000) * SALT_DOSAGE_PER_M3_PER_1000PPM * pool.volume_m3
        return DosageAdjustment(product=ChemicalProduct.SALT, quantity_g=round(quantity, 0))

    # Salt above max: no chemical product can lower it
    return None


def compute_tds(ec: float | None, factor: float = EC_TO_TDS_DEFAULT_FACTOR) -> float | None:
    """Compute Total Dissolved Solids (TDS) from Electrical Conductivity (EC).

    TDS is derived from EC using a linear conversion factor. The default
    factor of 0.5 is standard for freshwater pool applications. The factor
    is configurable per pool to accommodate different water compositions.

    Args:
        ec: Electrical conductivity reading in µS/cm, or None if unavailable.
        factor: Conversion factor (typically 0.4--0.8, default 0.5).

    Returns:
        TDS value in ppm, or None if EC is unavailable.
    """
    if ec is None:
        return None
    return ec * factor


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

    if reading.free_chlorine is not None:
        scores.append(
            _score_range(
                reading.free_chlorine, FREE_CHLORINE_MIN, FREE_CHLORINE_TARGET, FREE_CHLORINE_MAX
            )
        )

    if reading.tac is not None:
        scores.append(_score_range(reading.tac, TAC_MIN, TAC_TARGET, TAC_MAX))

    if reading.cya is not None:
        scores.append(_score_range(reading.cya, CYA_MIN, CYA_TARGET, CYA_MAX))

    if reading.hardness is not None:
        scores.append(_score_range(reading.hardness, HARDNESS_MIN, HARDNESS_TARGET, HARDNESS_MAX))

    if reading.salt is not None:
        scores.append(_score_range(reading.salt, SALT_MIN, SALT_TARGET, SALT_MAX))

    if reading.tds is not None:
        scores.append(_score_range(reading.tds, TDS_MIN, TDS_TARGET, TDS_MAX))

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


# Threshold for good vs warning status (score out of 100)
_STATUS_GOOD_THRESHOLD: float = 50.0


def compute_parameter_status(
    metric: MetricName, value: float, minimum: float, target: float, maximum: float
) -> ParameterReport:
    """Compute chemistry status for a single parameter value.

    Classification logic:
        - **good**: score >= 50 (inner half of acceptable range, closer to target)
        - **warning**: 0 < score < 50, or value at boundary (outer half, near boundary)
        - **bad**: value outside the acceptable min--max range

    Args:
        metric: The canonical metric name for this parameter.
        value: The measured value.
        minimum: Lower bound of acceptable range.
        target: Ideal value.
        maximum: Upper bound of acceptable range.

    Returns:
        ParameterReport with metric, status, value, range, and score.
    """
    score = _score_range(value, minimum, target, maximum)

    if value < minimum or value > maximum:
        status = ChemistryStatus.BAD
    elif score >= _STATUS_GOOD_THRESHOLD:
        status = ChemistryStatus.GOOD
    else:
        status = ChemistryStatus.WARNING

    return ParameterReport(
        metric=metric,
        status=status,
        value=value,
        target=target,
        minimum=minimum,
        maximum=maximum,
        score=round(score),
    )


def compute_chemistry_report(reading: PoolReading) -> ChemistryReport:
    """Compute chemistry status report for all available parameters.

    Only parameters with a valid reading are evaluated. Parameters without
    a sensor reading are left as None.

    Args:
        reading: Current sensor readings.

    Returns:
        ChemistryReport with per-parameter status reports.
    """
    return ChemistryReport(
        ph=(
            compute_parameter_status(MetricName.PH, reading.ph, PH_MIN, PH_TARGET, PH_MAX)
            if reading.ph is not None
            else None
        ),
        orp=(
            compute_parameter_status(
                MetricName.ORP, reading.orp, ORP_MIN_CRITICAL, ORP_TARGET, ORP_MAX
            )
            if reading.orp is not None
            else None
        ),
        free_chlorine=(
            compute_parameter_status(
                MetricName.CHLORINE,
                reading.free_chlorine,
                FREE_CHLORINE_MIN,
                FREE_CHLORINE_TARGET,
                FREE_CHLORINE_MAX,
            )
            if reading.free_chlorine is not None
            else None
        ),
        tds=(
            compute_parameter_status(MetricName.TDS, reading.tds, TDS_MIN, TDS_TARGET, TDS_MAX)
            if reading.tds is not None
            else None
        ),
        salt=(
            compute_parameter_status(MetricName.SALT, reading.salt, SALT_MIN, SALT_TARGET, SALT_MAX)
            if reading.salt is not None
            else None
        ),
        tac=(
            compute_parameter_status(
                MetricName.ALKALINITY, reading.tac, TAC_MIN, TAC_TARGET, TAC_MAX
            )
            if reading.tac is not None
            else None
        ),
        cya=(
            compute_parameter_status(MetricName.CYA, reading.cya, CYA_MIN, CYA_TARGET, CYA_MAX)
            if reading.cya is not None
            else None
        ),
        hardness=(
            compute_parameter_status(
                MetricName.HARDNESS, reading.hardness, HARDNESS_MIN, HARDNESS_TARGET, HARDNESS_MAX
            )
            if reading.hardness is not None
            else None
        ),
    )
