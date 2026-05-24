"""Tests for inventory persistence via :class:`InventoryStore`."""

from __future__ import annotations

import logging

from datetime import UTC, datetime, timedelta

import pytest

from homeassistant.core import HomeAssistant

from custom_components.poolman.domain.action import (
    Action,
    ActionLog,
    ActionSource,
    ActionType,
)
from custom_components.poolman.domain.inventory import Inventory, Product
from custom_components.poolman.domain.model import ChemicalProduct
from custom_components.poolman.storage import ActionStore, InventoryStore


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


# ---------------------------------------------------------------------------
# ActionStore (issue #19)
# ---------------------------------------------------------------------------


async def test_action_store_load_returns_empty_when_no_data(hass: HomeAssistant) -> None:
    store = ActionStore(hass, "entry_empty_actions")
    log = await store.async_load()
    assert isinstance(log, ActionLog)
    assert log.actions == []


async def test_action_store_save_then_load_round_trip(hass: HomeAssistant) -> None:
    store = ActionStore(hass, "entry_actions_round_trip")
    log = ActionLog()
    log.record(
        Action(
            id="act_1",
            type=ActionType.CHEMICAL,
            source=ActionSource.USER,
            treatment_id="ph_minus_300g",
            quantity=300.0,
            unit="g",
            timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=UTC),
            product_id="ph_minus",
            duration=timedelta(minutes=30),
        )
    )
    log.record(
        Action(
            id="act_2",
            type=ActionType.CHEMICAL,
            source=ActionSource.RECOMMENDATION,
            treatment_id="chlore_choc_500g",
            quantity=500.0,
            unit="g",
            timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=UTC),
            recommendation_id="rec_chlorine_low",
            product_id="chlore_choc",
        )
    )

    await store.async_save(log)

    # Reload using a fresh store instance to bypass internal caching.
    rebuilt_store = ActionStore(hass, "entry_actions_round_trip")
    rebuilt = await rebuilt_store.async_load()
    assert rebuilt.actions == log.actions


async def test_action_store_load_malformed_payload_returns_empty(
    hass: HomeAssistant,
    hass_storage: dict[str, dict],
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Pre-populate the storage backing with a payload that breaks the
    # outer container shape (data is not a dict).
    hass_storage["poolman.actions.entry_bad"] = {
        "version": 1,
        "key": "poolman.actions.entry_bad",
        "data": "not-a-dict",
    }
    store = ActionStore(hass, "entry_bad")
    with caplog.at_level(logging.WARNING):
        log = await store.async_load()
    assert isinstance(log, ActionLog)
    assert log.actions == []
    assert any("Malformed action payload" in r.message for r in caplog.records)
