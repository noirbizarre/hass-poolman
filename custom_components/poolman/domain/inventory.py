"""Inventory model for user-tracked pool products.

This module defines the types used to track the user's stock of chemical
products available for treatment. It is the canonical home for:

- :class:`Product` -- a user-defined product entry (brand, name, unit,
  optional tag mapping to a :class:`~.model.ChemicalProduct` kind).
- :class:`InventoryItem` -- current stock for a product, with an optional
  low-stock threshold.
- :class:`Inventory` -- mutable container with the catalog of products and
  their stock items.

The inventory is **decoupled** from the analysis pipeline: rules and
recommendations MUST NOT mutate it. Stock is only modified by user input
(via Home Assistant services) or by recording an :class:`~.action.Action`
(see #94).

Units are plain Home Assistant-compatible strings (``"g"``, ``"mL"``,
``"tablet"``), matching the convention used by :class:`~.action.Action`
and :class:`~.recommendation.Treatment`. No Home Assistant dependency is
present in this module.

Example::

    from custom_components.poolman.domain.inventory import (
        Inventory,
        InventoryItem,
        Product,
    )
    from custom_components.poolman.domain.model import ChemicalProduct

    inventory = Inventory()
    inventory.add_product(
        Product(
            id="brand_x_ph_minus_1_5kg",
            name="Brand X pH Minus 1.5kg",
            unit="g",
            chemical=ChemicalProduct.PH_MINUS,
        )
    )
    inventory.add_stock("brand_x_ph_minus_1_5kg", 1500.0)
    inventory.consume("brand_x_ph_minus_1_5kg", 300.0, unit="g")
    assert inventory.get("brand_x_ph_minus_1_5kg").quantity == 1200.0
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field
from typing import Any

from .model import ChemicalProduct

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Product:
    """A user-defined product available in the inventory.

    Products are user-configured to represent the actual branded items
    purchased by the user (e.g. *Brand X pH Minus 1.5kg*). The optional
    :attr:`chemical` tag links the branded product back to one of the
    well-known :class:`~.model.ChemicalProduct` kinds used by rules and
    treatments, so that consumption can be correlated with recommended
    treatments.

    Attributes:
        id: Stable identifier for the product, used as the key in the
            inventory and as ``product_id`` reference in actions.
        name: Human-readable label shown in the UI.
        unit: Unit for the product's quantity. MUST be a Home
            Assistant-compatible unit string, e.g. ``"g"``, ``"mL"``,
            or ``"tablet"``. Must match the unit used by any
            :class:`~.action.Action` that consumes this product.
        chemical: Optional tag identifying which
            :class:`~.model.ChemicalProduct` kind this branded product
            corresponds to. ``None`` for products outside the known
            catalog (e.g. custom or proprietary blends).
    """

    id: str
    name: str
    unit: str  # HA-compatible: "g" | "mL" | "tablet"
    chemical: ChemicalProduct | None = None


@dataclass
class InventoryItem:
    """Current stock for a product in the inventory.

    Items are mutable: quantity is updated by :meth:`Inventory.add_stock`,
    :meth:`Inventory.set_stock`, and :meth:`Inventory.consume`. A negative
    quantity is allowed (and logged as a warning) so over-consumption is
    visible rather than silently clamped.

    Attributes:
        product_id: Identifier of the related :class:`Product`.
        quantity: Current amount in stock, expressed in the product's unit.
        low_stock_threshold: Optional threshold; when set, ``quantity``
            falling below this value flags the item as low (see
            :meth:`Inventory.is_low`).
    """

    product_id: str
    quantity: float
    low_stock_threshold: float | None = None


@dataclass
class Inventory:
    """Mutable catalog of products and their current stock.

    The inventory holds two maps keyed by ``product_id``:

    - :attr:`products` -- the catalog of known products.
    - :attr:`items` -- the current stock per product.

    An item is created lazily by :meth:`add_stock` the first time a
    product receives stock. Consumption of an unknown product is logged
    and silently skipped (matching the contract expected by #94).

    Attributes:
        products: Catalog of known products, keyed by product id.
        items: Current stock items, keyed by product id.
    """

    products: dict[str, Product] = field(default_factory=dict)
    items: dict[str, InventoryItem] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------
    def add_product(self, product: Product) -> None:
        """Add (or replace) a product in the catalog.

        Existing stock for the same ``product_id`` is preserved.

        Args:
            product: The product to add or replace.
        """
        self.products[product.id] = product

    def remove_product(self, product_id: str) -> None:
        """Remove a product from the catalog and drop its stock item.

        Args:
            product_id: Identifier of the product to remove.
        """
        self.products.pop(product_id, None)
        self.items.pop(product_id, None)

    # ------------------------------------------------------------------
    # Stock access
    # ------------------------------------------------------------------
    def get(self, product_id: str) -> InventoryItem | None:
        """Return the stock item for a product, or ``None`` if absent."""
        return self.items.get(product_id)

    def add_stock(self, product_id: str, quantity: float) -> None:
        """Increase the stock for a product.

        Creates the stock item on first call. Raises :class:`KeyError`
        when the product is not in the catalog so callers can surface a
        user-facing error.

        Args:
            product_id: Identifier of the product to credit.
            quantity: Positive amount to add (in the product's unit).

        Raises:
            KeyError: If ``product_id`` is not registered in the catalog.
        """
        if product_id not in self.products:
            raise KeyError(product_id)
        item = self.items.get(product_id)
        if item is None:
            self.items[product_id] = InventoryItem(
                product_id=product_id,
                quantity=quantity,
            )
        else:
            item.quantity += quantity

    def set_stock(
        self,
        product_id: str,
        quantity: float,
        low_stock_threshold: float | None = None,
    ) -> None:
        """Set the absolute stock and optionally the low-stock threshold.

        Args:
            product_id: Identifier of the product to update.
            quantity: New absolute quantity (in the product's unit).
            low_stock_threshold: Optional new threshold. When ``None``,
                the existing threshold is preserved.

        Raises:
            KeyError: If ``product_id`` is not registered in the catalog.
        """
        if product_id not in self.products:
            raise KeyError(product_id)
        item = self.items.get(product_id)
        if item is None:
            self.items[product_id] = InventoryItem(
                product_id=product_id,
                quantity=quantity,
                low_stock_threshold=low_stock_threshold,
            )
        else:
            item.quantity = quantity
            if low_stock_threshold is not None:
                item.low_stock_threshold = low_stock_threshold

    def consume(
        self,
        product_id: str,
        quantity: float,
        unit: str | None = None,
    ) -> None:
        """Decrement the stock for a product.

        Designed to be called from the action-recording pipeline (#94):

        - Unknown products are logged as a warning and skipped, never
          raised, so action recording is not blocked.
        - When ``unit`` is given and differs from the product's unit, an
          error is logged and the stock is left unchanged (no silent
          unit conversion).
        - Negative resulting stock is allowed but logged as a warning.

        Args:
            product_id: Identifier of the product to debit.
            quantity: Positive amount to consume (in the product's unit).
            unit: Optional unit guard. When provided, MUST match the
                product's unit, otherwise the consumption is skipped.
        """
        product = self.products.get(product_id)
        item = self.items.get(product_id)
        if product is None or item is None:
            _LOGGER.warning(
                "Unknown product %s — action recorded but inventory not updated",
                product_id,
            )
            return

        if unit is not None and unit != product.unit:
            _LOGGER.error(
                "Unit mismatch for product %s: inventory=%s action=%s — skipping inventory update",
                product_id,
                product.unit,
                unit,
            )
            return

        item.quantity -= quantity
        if item.quantity < 0:
            _LOGGER.warning(
                "Negative stock for product %s (%.2f)",
                product_id,
                item.quantity,
            )

    def is_low(self, product_id: str) -> bool:
        """Return ``True`` when the product's stock is at or below threshold.

        Returns ``False`` when the product is unknown, has no stock item,
        or has no configured threshold.

        Args:
            product_id: Identifier of the product to check.
        """
        item = self.items.get(product_id)
        if item is None or item.low_stock_threshold is None:
            return False
        return item.quantity <= item.low_stock_threshold

    # ------------------------------------------------------------------
    # Serialization (used by helpers.storage.Store)
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the inventory."""
        return {
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "unit": product.unit,
                    "chemical": product.chemical.value if product.chemical else None,
                }
                for product in self.products.values()
            ],
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "low_stock_threshold": item.low_stock_threshold,
                }
                for item in self.items.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Inventory:
        """Rebuild an :class:`Inventory` from its JSON representation.

        Unknown chemical tags are dropped (set to ``None``) rather than
        causing the load to fail, so an inventory persisted with a newer
        version of the integration remains loadable after a downgrade.

        Args:
            data: A dictionary previously produced by :meth:`to_dict`.
        """
        inventory = cls()
        for raw_product in data.get("products", []):
            chemical_raw = raw_product.get("chemical")
            chemical: ChemicalProduct | None
            if chemical_raw is None:
                chemical = None
            else:
                try:
                    chemical = ChemicalProduct(chemical_raw)
                except ValueError:
                    _LOGGER.warning(
                        "Dropping unknown chemical tag %s for product %s",
                        chemical_raw,
                        raw_product.get("id"),
                    )
                    chemical = None
            product = Product(
                id=raw_product["id"],
                name=raw_product["name"],
                unit=raw_product["unit"],
                chemical=chemical,
            )
            inventory.products[product.id] = product

        for raw_item in data.get("items", []):
            product_id = raw_item["product_id"]
            if product_id not in inventory.products:
                # Drop dangling items without a matching product to keep
                # the inventory consistent.
                _LOGGER.warning(
                    "Dropping inventory item for unknown product %s",
                    product_id,
                )
                continue
            inventory.items[product_id] = InventoryItem(
                product_id=product_id,
                quantity=float(raw_item["quantity"]),
                low_stock_threshold=(
                    float(raw_item["low_stock_threshold"])
                    if raw_item.get("low_stock_threshold") is not None
                    else None
                ),
            )
        return inventory
