"""Shared helpers for chemistry rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...recommendation import Treatment

if TYPE_CHECKING:
    from ...model import DosageAdjustment


def treatment_from_dosage(
    code: str, dosage: DosageAdjustment | None, unit: str = "g"
) -> Treatment | None:
    """Convert a :class:`~...model.DosageAdjustment` into a :class:`Treatment`.

    Returns ``None`` when no dosage is provided.  When ``quantity_g`` is
    ``None`` (e.g. when the dosage function only identifies the product but
    has no quantitative recommendation), the resulting Treatment has
    ``quantity = 0.0``.

    Args:
        code: The originating :attr:`~...problem.Problem.code`, used to build
            a unique treatment id (``f"{code}_{product_id}"``).
        dosage: The :class:`~...model.DosageAdjustment` produced by a
            :mod:`...chemistry` ``compute_*_adjustment`` function.
        unit: HA-compatible unit string (default ``"g"``).

    Returns:
        A :class:`Treatment` ready to attach to a
        :class:`~...problem.Problem`, or ``None`` when ``dosage`` is ``None``.
    """
    if dosage is None:
        return None
    product_id = dosage.product.value
    return Treatment(
        id=f"{code}_{product_id}",
        product_id=product_id,
        name=product_id.replace("_", " ").title(),
        quantity=dosage.quantity_g or 0.0,
        unit=unit,
    )
