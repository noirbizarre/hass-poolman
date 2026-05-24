"""Tests for the inventory domain module."""

from __future__ import annotations

import logging

from dataclasses import FrozenInstanceError

import pytest

from custom_components.poolman.domain.inventory import Inventory, InventoryItem, Product
from custom_components.poolman.domain.model import ChemicalProduct


def _item(inventory: Inventory, product_id: str) -> InventoryItem:
    """Return the stored ``InventoryItem`` or fail the test if missing."""
    item = inventory.get(product_id)
    assert item is not None, f"Inventory item {product_id!r} not found"
    return item


class TestProduct:
    """Tests for the Product frozen dataclass."""

    def test_creation_minimal(self) -> None:
        product = Product(id="ph_minus", name="pH Minus", unit="g")
        assert product.id == "ph_minus"
        assert product.name == "pH Minus"
        assert product.unit == "g"
        assert product.chemical is None

    def test_creation_with_chemical_tag(self) -> None:
        product = Product(
            id="brand_x_ph_minus",
            name="Brand X pH Minus 1.5kg",
            unit="g",
            chemical=ChemicalProduct.PH_MINUS,
        )
        assert product.chemical is ChemicalProduct.PH_MINUS

    def test_frozen(self) -> None:
        product = Product(id="x", name="X", unit="g")
        with pytest.raises(FrozenInstanceError):
            # ``setattr`` keeps the type-checker quiet while still
            # exercising the runtime FrozenInstanceError guard.
            setattr(product, "name", "Y")  # noqa: B010

    def test_equality(self) -> None:
        a = Product(id="x", name="X", unit="g")
        b = Product(id="x", name="X", unit="g")
        assert a == b


class TestInventoryItem:
    """Tests for the InventoryItem dataclass."""

    def test_defaults(self) -> None:
        item = InventoryItem(product_id="x", quantity=10.0)
        assert item.low_stock_threshold is None

    def test_mutable_quantity(self) -> None:
        item = InventoryItem(product_id="x", quantity=10.0)
        item.quantity = 5.0
        assert item.quantity == 5.0


class TestInventoryCatalog:
    """Tests for catalog mutations on Inventory."""

    def _product(self) -> Product:
        return Product(id="ph_minus", name="pH Minus", unit="g")

    def test_add_product(self) -> None:
        inventory = Inventory()
        product = self._product()
        inventory.add_product(product)
        assert inventory.products == {"ph_minus": product}

    def test_remove_product_drops_item(self) -> None:
        inventory = Inventory()
        inventory.add_product(self._product())
        inventory.add_stock("ph_minus", 100.0)
        inventory.remove_product("ph_minus")
        assert inventory.products == {}
        assert inventory.items == {}

    def test_remove_unknown_is_noop(self) -> None:
        inventory = Inventory()
        inventory.remove_product("nope")  # no error


class TestInventoryStock:
    """Tests for stock mutation and queries."""

    def _inventory(self, *, threshold: float | None = None) -> Inventory:
        inventory = Inventory()
        inventory.add_product(Product(id="ph_minus", name="pH Minus", unit="g"))
        if threshold is not None:
            inventory.set_stock("ph_minus", 0.0, low_stock_threshold=threshold)
        return inventory

    def test_get_unknown_returns_none(self) -> None:
        inventory = self._inventory()
        assert inventory.get("nope") is None

    def test_add_stock_creates_item(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        item = inventory.get("ph_minus")
        assert item is not None
        assert item.quantity == 100.0

    def test_add_stock_accumulates(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        inventory.add_stock("ph_minus", 50.0)
        assert _item(inventory, "ph_minus").quantity == 150.0

    def test_add_stock_unknown_product_raises(self) -> None:
        inventory = Inventory()
        with pytest.raises(KeyError):
            inventory.add_stock("nope", 10.0)

    def test_set_stock_unknown_product_raises(self) -> None:
        inventory = Inventory()
        with pytest.raises(KeyError):
            inventory.set_stock("nope", 10.0)

    def test_set_stock_overrides_quantity(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        inventory.set_stock("ph_minus", 42.0)
        assert _item(inventory, "ph_minus").quantity == 42.0

    def test_set_stock_updates_threshold(self) -> None:
        inventory = self._inventory(threshold=10.0)
        inventory.set_stock("ph_minus", 50.0, low_stock_threshold=25.0)
        assert _item(inventory, "ph_minus").low_stock_threshold == 25.0

    def test_consume_decrements(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        inventory.consume("ph_minus", 30.0)
        assert _item(inventory, "ph_minus").quantity == 70.0

    def test_consume_unknown_product_logs_and_skips(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        inventory = self._inventory()
        with caplog.at_level(logging.WARNING):
            inventory.consume("unknown", 10.0)
        assert any("Unknown product" in r.message for r in caplog.records)
        assert inventory.get("unknown") is None

    def test_consume_unit_mismatch_logs_and_skips(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        with caplog.at_level(logging.ERROR):
            inventory.consume("ph_minus", 50.0, unit="mL")
        assert any("Unit mismatch" in r.message for r in caplog.records)
        assert _item(inventory, "ph_minus").quantity == 100.0

    def test_consume_unit_match_decrements(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        inventory.consume("ph_minus", 30.0, unit="g")
        assert _item(inventory, "ph_minus").quantity == 70.0

    def test_consume_below_zero_logs_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 10.0)
        with caplog.at_level(logging.WARNING):
            inventory.consume("ph_minus", 50.0)
        assert any("Negative stock" in r.message for r in caplog.records)
        assert _item(inventory, "ph_minus").quantity == -40.0


class TestIsLow:
    """Tests for the is_low predicate."""

    def _inventory(self) -> Inventory:
        inventory = Inventory()
        inventory.add_product(Product(id="ph_minus", name="pH Minus", unit="g"))
        return inventory

    def test_unknown_product_returns_false(self) -> None:
        assert Inventory().is_low("nope") is False

    def test_no_threshold_returns_false(self) -> None:
        inventory = self._inventory()
        inventory.add_stock("ph_minus", 100.0)
        assert inventory.is_low("ph_minus") is False

    def test_above_threshold_returns_false(self) -> None:
        inventory = self._inventory()
        inventory.set_stock("ph_minus", 100.0, low_stock_threshold=50.0)
        assert inventory.is_low("ph_minus") is False

    def test_at_or_below_threshold_returns_true(self) -> None:
        inventory = self._inventory()
        inventory.set_stock("ph_minus", 50.0, low_stock_threshold=50.0)
        assert inventory.is_low("ph_minus") is True
        inventory.set_stock("ph_minus", 25.0)
        assert inventory.is_low("ph_minus") is True


class TestSerialization:
    """Tests for round-trip JSON serialization via to_dict / from_dict."""

    def test_round_trip_minimal(self) -> None:
        inventory = Inventory()
        inventory.add_product(Product(id="ph_minus", name="pH Minus", unit="g"))
        inventory.add_stock("ph_minus", 1500.0)
        rebuilt = Inventory.from_dict(inventory.to_dict())
        assert rebuilt.products == inventory.products
        assert rebuilt.items["ph_minus"].quantity == 1500.0

    def test_round_trip_with_chemical_and_threshold(self) -> None:
        inventory = Inventory()
        inventory.add_product(
            Product(
                id="brand_x_ph_minus",
                name="Brand X pH Minus 1.5kg",
                unit="g",
                chemical=ChemicalProduct.PH_MINUS,
            )
        )
        inventory.set_stock("brand_x_ph_minus", 1500.0, low_stock_threshold=300.0)
        rebuilt = Inventory.from_dict(inventory.to_dict())
        product = rebuilt.products["brand_x_ph_minus"]
        assert product.chemical is ChemicalProduct.PH_MINUS
        assert rebuilt.items["brand_x_ph_minus"].low_stock_threshold == 300.0

    def test_from_dict_drops_unknown_chemical_tag(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        data = {
            "products": [
                {"id": "x", "name": "X", "unit": "g", "chemical": "not_a_real_product"},
            ],
            "items": [],
        }
        with caplog.at_level(logging.WARNING):
            rebuilt = Inventory.from_dict(data)
        assert rebuilt.products["x"].chemical is None
        assert any("unknown chemical tag" in r.message for r in caplog.records)

    def test_from_dict_drops_dangling_items(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        data = {
            "products": [],
            "items": [{"product_id": "ghost", "quantity": 1.0, "low_stock_threshold": None}],
        }
        with caplog.at_level(logging.WARNING):
            rebuilt = Inventory.from_dict(data)
        assert rebuilt.items == {}
        assert any("unknown product" in r.message for r in caplog.records)

    def test_from_dict_empty(self) -> None:
        rebuilt = Inventory.from_dict({})
        assert rebuilt.products == {}
        assert rebuilt.items == {}
