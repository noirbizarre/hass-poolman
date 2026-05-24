"""Tests for inventory HA services and dynamic entity discovery."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman.const import (
    DOMAIN,
    SERVICE_INVENTORY_ADD_PRODUCT,
    SERVICE_INVENTORY_ADD_STOCK,
    SERVICE_INVENTORY_REMOVE_PRODUCT,
    SERVICE_INVENTORY_SET_STOCK,
)
from custom_components.poolman.coordinator import PoolmanCoordinator
from custom_components.poolman.domain.model import ChemicalProduct
from tests.conftest import setup_mock_states


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> PoolmanCoordinator:
    """Set up the integration and return the coordinator."""
    mock_config_entry.add_to_hass(hass)
    setup_mock_states(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry.runtime_data


class TestInventoryServices:
    """Tests for inventory service handlers."""

    async def test_services_are_registered(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
    ) -> None:
        assert hass.services.has_service(DOMAIN, SERVICE_INVENTORY_ADD_PRODUCT)
        assert hass.services.has_service(DOMAIN, SERVICE_INVENTORY_REMOVE_PRODUCT)
        assert hass.services.has_service(DOMAIN, SERVICE_INVENTORY_ADD_STOCK)
        assert hass.services.has_service(DOMAIN, SERVICE_INVENTORY_SET_STOCK)

    async def test_add_product_with_initial_stock_and_threshold(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_ADD_PRODUCT,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "brand_x_ph_minus",
                "name": "Brand X pH Minus 1.5kg",
                "unit": "g",
                "chemical": "ph_minus",
                "initial_quantity": 1500.0,
                "low_stock_threshold": 300.0,
            },
            blocking=True,
        )

        product = setup_entry.inventory.products["brand_x_ph_minus"]
        assert product.chemical is ChemicalProduct.PH_MINUS
        item = setup_entry.inventory.get("brand_x_ph_minus")
        assert item is not None
        assert item.quantity == 1500.0
        assert item.low_stock_threshold == 300.0

        # Quantity sensor was created dynamically.
        state = hass.states.get("sensor.test_pool_brand_x_ph_minus_1_5kg")
        assert state is not None
        assert float(state.state) == 1500.0
        assert state.attributes["is_low"] is False

        binary_state = hass.states.get("binary_sensor.test_pool_brand_x_ph_minus_1_5kg_low_stock")
        assert binary_state is not None
        assert binary_state.state == "off"

    async def test_add_stock_then_set_stock(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_ADD_PRODUCT,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "ph_minus",
                "name": "pH Minus",
                "unit": "g",
            },
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_ADD_STOCK,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "ph_minus",
                "quantity": 500.0,
            },
            blocking=True,
        )
        item = setup_entry.inventory.get("ph_minus")
        assert item is not None
        assert item.quantity == 500.0

        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_SET_STOCK,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "ph_minus",
                "quantity": 50.0,
                "low_stock_threshold": 100.0,
            },
            blocking=True,
        )
        item = setup_entry.inventory.get("ph_minus")
        assert item is not None
        assert item.quantity == 50.0
        assert item.low_stock_threshold == 100.0
        assert setup_entry.inventory.is_low("ph_minus") is True

        binary_state = hass.states.get("binary_sensor.test_pool_ph_minus_low_stock")
        assert binary_state is not None
        assert binary_state.state == "on"

    async def test_add_stock_unknown_product_raises_validation_error(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_INVENTORY_ADD_STOCK,
                {
                    "entry_id": mock_config_entry.entry_id,
                    "product_id": "ghost",
                    "quantity": 1.0,
                },
                blocking=True,
            )

    async def test_remove_product_clears_stock(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_ADD_PRODUCT,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "ph_minus",
                "name": "pH Minus",
                "unit": "g",
                "initial_quantity": 500.0,
            },
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVENTORY_REMOVE_PRODUCT,
            {
                "entry_id": mock_config_entry.entry_id,
                "product_id": "ph_minus",
            },
            blocking=True,
        )
        assert "ph_minus" not in setup_entry.inventory.products
        assert setup_entry.inventory.get("ph_minus") is None

    async def test_unknown_entry_id_raises_validation_error(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
    ) -> None:
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_INVENTORY_REMOVE_PRODUCT,
                {"entry_id": "not_a_real_entry", "product_id": "x"},
                blocking=True,
            )

    async def test_set_stock_unknown_product_raises_validation_error(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_INVENTORY_SET_STOCK,
                {
                    "entry_id": mock_config_entry.entry_id,
                    "product_id": "ghost",
                    "quantity": 1.0,
                },
                blocking=True,
            )


class TestCoordinatorInventoryAPI:
    """Direct tests for the coordinator's inventory helpers."""

    async def test_consume_decrements_persisted_stock(
        self,
        setup_entry: PoolmanCoordinator,
    ) -> None:
        from custom_components.poolman.domain.inventory import Product

        await setup_entry.async_inventory_add_product(
            Product(id="ph_minus", name="pH Minus", unit="g"),
            initial_quantity=100.0,
        )
        await setup_entry.async_inventory_consume("ph_minus", 30.0, unit="g")
        item = setup_entry.inventory.get("ph_minus")
        assert item is not None
        assert item.quantity == 70.0

    async def test_inventory_listener_exception_is_swallowed(
        self,
        setup_entry: PoolmanCoordinator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        from custom_components.poolman.domain.inventory import Product

        def _boom(_added: set[str], _removed: set[str]) -> None:
            raise RuntimeError("listener exploded")

        unsubscribe = setup_entry.on_inventory_change(_boom)
        try:
            with caplog.at_level("ERROR"):
                await setup_entry.async_inventory_add_product(
                    Product(id="ph_minus", name="pH Minus", unit="g"),
                )
        finally:
            unsubscribe()

        assert any("Inventory listener raised" in r.message for r in caplog.records)

    async def test_inventory_entities_seeded_from_storage(
        self,
        hass: HomeAssistant,
        hass_storage: dict[str, dict],
    ) -> None:
        """Entities are created from inventory persisted before setup."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from tests.conftest import MOCK_CONFIG_DATA, setup_mock_states

        entry = MockConfigEntry(
            domain=DOMAIN,
            data=MOCK_CONFIG_DATA,
            entry_id="seeded_entry",
            title="Seeded Pool",
        )
        entry.add_to_hass(hass)
        # Pre-populate storage with one product BEFORE setup so that
        # initial entity discovery (sync path in async_setup_entry) runs.
        hass_storage[f"poolman.inventory.{entry.entry_id}"] = {
            "version": 1,
            "key": f"poolman.inventory.{entry.entry_id}",
            "data": {
                "products": [
                    {"id": "ph_minus", "name": "pH Minus", "unit": "g"},
                ],
                "items": [
                    {
                        "product_id": "ph_minus",
                        "quantity": 200.0,
                        "low_stock_threshold": 100.0,
                    }
                ],
            },
        }
        setup_mock_states(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Both entities were created without a service call.
        sensor_state = hass.states.get("sensor.seeded_pool_ph_minus")
        assert sensor_state is not None
        assert float(sensor_state.state) == 200.0

        binary_state = hass.states.get("binary_sensor.seeded_pool_ph_minus_low_stock")
        assert binary_state is not None
        assert binary_state.state == "off"

    async def test_inventory_entities_when_product_removed(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        """Stock entities return None/empty attrs once product is gone."""
        from custom_components.poolman.binary_sensor import PoolmanLowStockBinarySensor
        from custom_components.poolman.domain.inventory import Product
        from custom_components.poolman.sensor import PoolmanInventorySensor

        product = Product(id="ph_minus", name="pH Minus", unit="g")
        await setup_entry.async_inventory_add_product(product, initial_quantity=50.0)

        sensor = PoolmanInventorySensor(setup_entry, product)
        binary = PoolmanLowStockBinarySensor(setup_entry, product)
        assert sensor.native_value == 50.0
        assert sensor.extra_state_attributes["product_id"] == "ph_minus"
        assert binary.is_on is False
        assert binary.extra_state_attributes["product_id"] == "ph_minus"

        await setup_entry.async_inventory_remove_product("ph_minus")

        # After removal, the underlying entity helpers gracefully degrade.
        assert sensor.native_value is None
        assert sensor.extra_state_attributes == {}
        assert binary.is_on is False
        assert binary.extra_state_attributes == {}

    async def test_add_product_idempotent_ignores_duplicate_listener_call(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
        mock_config_entry: MockConfigEntry,
    ) -> None:
        """Re-adding a known product does not create a duplicate entity."""
        for _ in range(2):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_INVENTORY_ADD_PRODUCT,
                {
                    "entry_id": mock_config_entry.entry_id,
                    "product_id": "ph_minus",
                    "name": "pH Minus",
                    "unit": "g",
                    "initial_quantity": 100.0,
                },
                blocking=True,
            )
        # Exactly one entity each.
        matches = [s for s in hass.states.async_all() if s.entity_id == "sensor.test_pool_ph_minus"]
        assert len(matches) == 1

    async def test_listener_notified_with_unknown_id_is_ignored(
        self,
        hass: HomeAssistant,
        setup_entry: PoolmanCoordinator,
    ) -> None:
        """A spurious listener notification for a missing product is a no-op."""
        before = len(hass.states.async_all())
        # Directly notify listeners with an id absent from the catalog;
        # the platform callbacks should skip it without creating entities
        # or raising.
        setup_entry._notify_inventory_listeners({"phantom_id"}, set())
        await hass.async_block_till_done()
        assert len(hass.states.async_all()) == before
        assert hass.states.get("sensor.test_pool_phantom_id") is None
        assert hass.states.get("binary_sensor.test_pool_phantom_id_low_stock") is None

    async def test_tablet_unit_has_no_device_class(
        self,
        setup_entry: PoolmanCoordinator,
    ) -> None:
        """Tablet products carry no Home Assistant device_class."""
        from custom_components.poolman.domain.inventory import Product
        from custom_components.poolman.sensor import PoolmanInventorySensor

        product = Product(id="tabs", name="Multi Tabs", unit="tablet")
        await setup_entry.async_inventory_add_product(product, initial_quantity=10.0)
        sensor = PoolmanInventorySensor(setup_entry, product)
        # ``tablet`` intentionally maps to (None, None): a raw count
        # without a Home Assistant unit-of-measurement or device class.
        assert sensor._attr_native_unit_of_measurement is None
        assert getattr(sensor, "_attr_device_class", None) is None
