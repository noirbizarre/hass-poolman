"""Tests for inventory persistence via :class:`InventoryStore`."""

from __future__ import annotations

import logging

import pytest

from homeassistant.core import HomeAssistant

from custom_components.poolman.domain.inventory import Inventory, Product
from custom_components.poolman.domain.model import ChemicalProduct
from custom_components.poolman.storage import InventoryStore


async def test_load_returns_empty_when_no_data(hass: HomeAssistant) -> None:
    store = InventoryStore(hass, "entry_empty")
    inventory = await store.async_load()
    assert isinstance(inventory, Inventory)
    assert inventory.products == {}
    assert inventory.items == {}


async def test_save_then_load_round_trip(hass: HomeAssistant) -> None:
    store = InventoryStore(hass, "entry_round_trip")
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

    await store.async_save(inventory)

    # Reload using a fresh store instance to bypass internal caching.
    rebuilt_store = InventoryStore(hass, "entry_round_trip")
    rebuilt = await rebuilt_store.async_load()
    product = rebuilt.products["brand_x_ph_minus"]
    assert product.chemical is ChemicalProduct.PH_MINUS
    item = rebuilt.items["brand_x_ph_minus"]
    assert item.quantity == 1500.0
    assert item.low_stock_threshold == 300.0


async def test_load_malformed_payload_returns_empty(
    hass: HomeAssistant,
    hass_storage: dict[str, dict],
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Pre-populate the storage backing with a malformed payload.
    hass_storage["poolman.inventory.entry_bad"] = {
        "version": 1,
        "key": "poolman.inventory.entry_bad",
        "data": {"products": [{"id": "x"}]},  # missing required fields
    }
    store = InventoryStore(hass, "entry_bad")
    with caplog.at_level(logging.WARNING):
        inventory = await store.async_load()
    assert isinstance(inventory, Inventory)
    assert inventory.products == {}
    assert any("Malformed inventory payload" in r.message for r in caplog.records)
