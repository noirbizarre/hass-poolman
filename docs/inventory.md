---
icon: lucide/package
---

# Inventory

Pool Manager can track the stock of chemical products you keep on hand,
so it can warn you when a product is running low and (in the future)
automatically decrement your stock as you record treatments.

The inventory is **per pool** (per Home Assistant config entry) and is
persisted to local storage, so it survives Home Assistant restarts.

## Concepts

- **Product** -- a user-configured entry representing an actual branded
  item you purchased (e.g. *Brand X pH Minus 1.5kg*). A product is
  identified by a stable `product_id`, has a display name, a unit, and
  an optional `chemical` tag mapping it to a known
  [chemical product kind](rules-and-recommendations.md).
- **Stock** -- the current quantity available for a product, expressed
  in the product's unit.
- **Low-stock threshold** -- an optional value per product; when the
  stock drops at or below it, a dedicated binary sensor turns on.

The inventory is decoupled from the analysis pipeline: rules and
recommendations cannot mutate it. Stock changes only come from:

- Home Assistant services (documented below), or
- Recording an action that carries a `product_id` (see
  [Automatic decrement on action recording](#automatic-decrement-on-action-recording)).

## Supported units

The following unit strings are accepted by the services and exposed as
Home Assistant-compatible units on the stock sensors:

| Unit string | Sensor unit            | Device class      |
| ----------- | ---------------------- | ----------------- |
| `g`         | grams                  | `weight`          |
| `kg`        | kilograms              | `weight`          |
| `mL`        | milliliters            | `volume_storage`  |
| `L`         | liters                 | `volume_storage`  |
| `tablet`    | none (raw count)       | none              |

The product unit must match the unit used by any treatment that consumes
it. Mismatched units are logged as an error and the stock is left
unchanged.

## Entities

For every configured product, Pool Manager creates:

- **`sensor.<pool>_<product_name>`** -- current stock as a measurement.
  Extra state attributes include `product_id`, `product_name`, `unit`,
  `chemical`, `low_stock_threshold`, and `is_low`.
- **`binary_sensor.<pool>_<product_name>_low_stock`** -- `on` when the
  stock has dropped at or below the configured threshold, `off`
  otherwise. Device class `problem`. When no threshold is set the
  binary sensor stays `off`.

Both entities are created dynamically whenever a product is added, and
become unavailable when the product is removed from the catalog.

## Services

All inventory services target a specific Pool Manager config entry by
its `entry_id`. Use the **Configuration entry** selector in the UI to
pick one.

### `poolman.inventory_add_product`

Register a new product, optionally seeding it with stock and a
low-stock threshold.

```yaml
service: poolman.inventory_add_product
data:
  entry_id: <pool config entry id>
  product_id: brand_x_ph_minus_1_5kg
  name: Brand X pH Minus 1.5kg
  unit: g
  chemical: ph_minus       # optional tag, must be a ChemicalProduct value
  initial_quantity: 1500   # optional
  low_stock_threshold: 300 # optional
```

### `poolman.inventory_remove_product`

Remove a product and drop its stock entry.

```yaml
service: poolman.inventory_remove_product
data:
  entry_id: <pool config entry id>
  product_id: brand_x_ph_minus_1_5kg
```

### `poolman.inventory_add_stock`

Credit the current stock of a product.

```yaml
service: poolman.inventory_add_stock
data:
  entry_id: <pool config entry id>
  product_id: brand_x_ph_minus_1_5kg
  quantity: 500
```

### `poolman.inventory_set_stock`

Set the absolute current stock (e.g. after a manual inventory count).
Optionally also updates the low-stock threshold.

```yaml
service: poolman.inventory_set_stock
data:
  entry_id: <pool config entry id>
  product_id: brand_x_ph_minus_1_5kg
  quantity: 1200
  low_stock_threshold: 250   # optional
```

## Automatic decrement on action recording

When an [action](rules-and-recommendations.md) is recorded with a
`product_id`, Pool Manager automatically debits the matching product's
stock by `action.quantity`. The contract is intentionally lenient so an
inventory issue never prevents the action itself from being logged:

- **Unknown product** -- the action is recorded and a warning is logged
  (`Unknown product <id> -- action recorded but inventory not updated`).
  The inventory is left unchanged.
- **Unit mismatch** -- when the action unit differs from the product
  unit, the consumption is skipped and an error is logged
  (`Unit mismatch for product <id>: inventory=<u1> action=<u2> -- skipping
  inventory update`). No silent unit conversion is performed.
- **Negative stock** -- the consumption is still applied so the discrepancy
  remains visible; a warning is logged
  (`Negative stock for product <id> (<qty>)`).

Actions without a `product_id` (e.g. cleaning or maintenance) never
touch the inventory.

## Persistence

The inventory is persisted to Home Assistant's local storage as
`.storage/poolman.inventory.<entry_id>`. The payload is JSON and looks
like:

```json
{
  "products": [
    {
      "id": "brand_x_ph_minus_1_5kg",
      "name": "Brand X pH Minus 1.5kg",
      "unit": "g",
      "chemical": "ph_minus"
    }
  ],
  "items": [
    {
      "product_id": "brand_x_ph_minus_1_5kg",
      "quantity": 1200.0,
      "low_stock_threshold": 250.0
    }
  ]
}
```

A corrupted or partial payload is logged and replaced with an empty
inventory at startup; it never blocks integration setup.

## Roadmap

- **Config-flow editor** for products (currently services-only).
- **External inventory integration** with Vesta (issue #93).
