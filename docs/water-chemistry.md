---
icon: lucide/flask-conical
---

# Water Chemistry

Pool Manager monitors up to eight water chemistry parameters. Each parameter
has a defined acceptable range and an ideal target value used for scoring
and dosage calculations.

## Parameter Ranges

| Parameter | Unit | Minimum | Target | Maximum |
| --- | --- | --- | --- | --- |
| pH | -- | 6.8 | 7.2 | 7.8 |
| ORP | mV | 650 | 750 | 900 |
| Free Chlorine | ppm | 1.0 | 2.0 | 3.0 |
| Salt | ppm | 2700 | 3200 | 3400 |
| TAC (Total Alkalinity) | ppm | 80 | 120 | 150 |
| CYA (Cyanuric Acid) | ppm | 20 | 40 | 75 |
| Calcium Hardness | ppm | 150 | 250 | 400 |
| TDS (Total Dissolved Solids) | ppm | 250 | 500 | 1500 |

Values within the minimum--maximum range are considered acceptable. The target
value represents the ideal level for each parameter.

## Chemistry Status

Each parameter is evaluated individually and assigned one of three statuses:
**good**, **warning**, or **bad**. These are exposed as
[enum sensors](entities.md#chemistry-status-sensors) for use in dashboards and
automations.

### How the status is determined

The status is derived from the parameter's individual quality score (the same
score used in the [water quality score](#water-quality-score) calculation):

| Status | Condition | Meaning |
| --- | --- | --- |
| **Good** | Score >= 50 (inner half of acceptable range) | Parameter is close to target, no attention needed |
| **Warning** | Score < 50 but value within min--max range | Parameter is drifting towards boundary, should be monitored |
| **Bad** | Value outside the acceptable min--max range | Parameter is out of range, action required |

??? example "pH status example"

    For pH with range 6.8--7.8 and target 7.2:

    | pH reading | Score | Status |
    | --- | --- | --- |
    | 7.2 | 100 | Good (at target) |
    | 7.0 | 50 | Good (midpoint, inner half) |
    | 6.9 | 25 | Warning (outer half, nearing boundary) |
    | 6.8 | 0 | Warning (at boundary, still in range) |
    | 6.5 | 0 | Bad (below range) |
    | 8.0 | 0 | Bad (above range) |

When a parameter's status changes between updates, a `poolman_event` is fired
on the Home Assistant event bus so you can trigger automations. See
[Events](entities.md#events) for the full event schema.

## Water Quality Score

The **water quality score** is a 0--100% value displayed by the
`sensor.{pool}_water_quality_score` entity. It provides a single-number
summary of your pool's overall water chemistry health.

### How it is calculated

Each available parameter is scored individually against its acceptable range:

- A reading **at the target** value scores **100**
- A reading at the **minimum or maximum** boundary scores **0**
- Values **between** the boundary and the target are scored **linearly**
- Values **outside** the acceptable range score **0**

The overall water quality score is the **average** of all individual parameter scores.

??? example "Scoring example"

    For pH with range 6.8--7.8 and target 7.2:

    | pH reading | Score |
    | --- | --- |
    | 7.2 | 100 (at target) |
    | 7.0 | 50 (halfway between min and target) |
    | 7.5 | 50 (halfway between target and max) |
    | 6.8 | 0 (at minimum boundary) |
    | 7.8 | 0 (at maximum boundary) |
    | 6.5 | 0 (below range) |
    | 8.0 | 0 (above range) |

### Which parameters are included

Only parameters for which a sensor is configured and currently reporting a
valid value are included in the score. If you only have pH and ORP sensors,
the score is computed from those two. Adding free chlorine, salt, TAC, CYA, or
hardness sensors increases the accuracy of the score.

If no parameter has a valid reading, the score is unavailable.

## Chemical Products

Pool Manager recommends chemical products based on your configured
[treatment type](getting-started.md#step-2-chemistry). The sanitizer-related
products adapt to your treatment method, while pH and TAC products are
universal.

### Universal products

| Product | Usage |
| --- | --- |
| pH- (pH minus) | Lower pH when it is above target |
| pH+ (pH plus) | Raise pH when it is below target |
| TAC+ (alkalinity increaser) | Raise total alkalinity when it is below minimum |
| Stabilizer (CYA) | Raise cyanuric acid when it is below minimum |
| Calcium hardness increaser | Raise calcium hardness when it is below minimum |
| Flocculant | Clarify cloudy water by clumping fine particles for filtration |
| Anti-algae | Preventive or curative algae treatment |
| Clarifier | Improve water clarity by binding micro-particles |
| Metal sequestrant | Bind dissolved metals to prevent staining and discoloration |
| Winterizing product | Protect pool water during winter shutdown |

### Sanitizer products by treatment type

| Treatment | Regular product | Shock product | Excess product |
| --- | --- | --- | --- |
| Chlorine | Chlorine tablet | Shock chlorine | Neutralizer |
| Salt electrolysis | Salt | Salt (increased dose) | Neutralizer |
| Bromine | Bromine tablet | Bromine shock | Neutralizer |
| Active oxygen | Active oxygen tablet | Active oxygen activator | Neutralizer |

## pH Dosage Calculation

When pH deviates from the target (7.2) by more than the tolerance (0.1),
Pool Manager calculates the required dosage:

$$
\text{quantity (g)} = \frac{|\text{pH} - 7.2|}{0.2} \times 150 \times \frac{\text{volume\_m3}}{10}
$$

Where:

- **150 g per 10 m³** is the base dosage for a 0.2 pH change
- The product is **pH-** if pH is above target, **pH+** if below

??? example "pH dosage example"

    For a 50 m³ pool with pH at 7.6:

    - Delta: |7.6 - 7.2| = 0.4
    - Quantity: (0.4 / 0.2) x 150 x (50 / 10) = 2 x 150 x 5 = **1500 g of pH-**

## TAC Dosage Calculation

When TAC falls below the minimum (80 ppm), the integration calculates the
sodium bicarbonate dosage needed to reach the target (120 ppm):

$$
\text{quantity (g)} = \frac{\text{target} - \text{TAC}}{10} \times 18 \times \text{volume\_m3}
$$

Where **18 g of sodium bicarbonate per m³** raises TAC by **10 ppm**.

When TAC is above the maximum (150 ppm), pH- treatments are recommended as they indirectly lower alkalinity.

## CYA Dosage Calculation

When CYA (cyanuric acid / stabilizer) falls below the minimum (20 ppm), the
integration calculates the stabilizer dosage needed to reach the target (40 ppm):

$$
\text{quantity (g)} = (\text{target} - \text{CYA}) \times 1 \times \text{volume\_m3}
$$

Where **1 g of cyanuric acid per m³** raises CYA by **1 ppm**.

When CYA is above the maximum (75 ppm), no chemical product can lower it.
The integration recommends a partial water drain instead.

??? example "CYA dosage example"

    For a 50 m³ pool with CYA at 10 ppm:

    - Delta: 40 - 10 = 30
    - Quantity: 30 x 1 x 50 = **1500 g of stabilizer**

## Hardness Dosage Calculation

When calcium hardness falls below the minimum (150 ppm), the integration
calculates the calcium chloride dosage needed to reach the target (250 ppm):

$$
\text{quantity (g)} = (\text{target} - \text{hardness}) \times 1.5 \times \text{volume\_m3}
$$

Where **1.5 g of CaCl₂ per m³** raises hardness by **1 ppm**.

When hardness is above the maximum (400 ppm), no chemical product can lower it.
The integration recommends a partial water drain instead.

??? example "Hardness dosage example"

    For a 50 m³ pool with hardness at 100 ppm:

    - Delta: 250 - 100 = 150
    - Quantity: 150 x 1.5 x 50 = **11250 g of calcium hardness increaser**

## Free Chlorine

Free chlorine measures the amount of active, available chlorine in the water.
Unlike ORP (which provides an indirect measure of sanitizer effectiveness),
free chlorine is a direct measurement that supplements the ORP-based
sanitizer evaluation.

When free chlorine is out of range, Pool Manager recommends the appropriate
product but does **not** calculate a specific dosage, because the required
amount depends on many factors (CYA level, UV exposure, bather load, etc.):

| Condition | Recommended product |
| --- | --- |
| Free chlorine < 1.0 ppm | Shock chlorine |
| Free chlorine > 3.0 ppm | Neutralizer |

## Electrical Conductivity (EC)

Electrical conductivity (EC) measures the water's ability to conduct an
electrical current, which correlates with total dissolved solids (TDS).
It is a useful diagnostic indicator for tracking mineral buildup, salt
levels, or general water freshness over time.

EC is exposed as a **read-only sensor** with no status, no scoring, and
no rules. There is no universal ideal range because acceptable EC values
vary widely depending on treatment type (salt electrolysis pools run at
3000--6000 µS/cm, while chlorine-treated pools are typically 500--1500
µS/cm), water source, and local conditions.

Use the `sensor.{pool}_ec` entity for trending and diagnostics in your
dashboards.

## Total Dissolved Solids (TDS)

Total Dissolved Solids (TDS) estimates the concentration of all dissolved
minerals, salts, and organic matter in the pool water. High TDS reduces
sanitizer effectiveness, can cause cloudy water, and may lead to scaling
on pool surfaces and equipment.

TDS is **computed from EC** (Electrical Conductivity) using a configurable
conversion factor:

$$
\text{TDS (ppm)} = \text{EC (µS/cm)} \times \text{factor}
$$

The default factor is **0.5**, which is standard for freshwater pools.
You can adjust it during setup or in the options flow (typical range:
0.4--0.8) to match your water composition.

When TDS is out of range, Pool Manager recommends the appropriate action:

| Condition | Recommended action |
| --- | --- |
| TDS > 1500 ppm | Partial water drain (no chemical fix) |
| TDS < 250 ppm | Verify EC sensor calibration |

!!! note

    The TDS rule is **skipped** for pools using **salt electrolysis**
    treatment, because dissolved salt naturally raises TDS well above
    freshwater thresholds. TDS scoring and status are still computed but
    the rule engine does not generate recommendations.

### Manual TDS measurement

You can record a manual TDS measurement using the `poolman.record_measure`
service with the `tds` parameter. Manual measurements override the
computed value until the next sensor update.

## Salt

Salt level monitoring is relevant for pools using **salt electrolysis**
treatment. The salt sensor tracks the concentration of dissolved salt
in the water, which is critical for the electrolysis cell to function
properly.

When salt level is out of range, Pool Manager recommends the appropriate
action:

| Condition | Recommended action |
| --- | --- |
| Salt < 2700 ppm | Add salt with calculated dosage |
| Salt > 3400 ppm | Partial water drain (no chemical fix) |

### Salt Dosage Calculation

When salt falls below the minimum (2700 ppm), the integration calculates
the salt dosage needed to reach the target (3200 ppm):

$$
\text{quantity (g)} = \frac{\text{target} - \text{salt}}{1000} \times 3000 \times \text{volume\_m3}
$$

Where **3 kg of salt per m³** raises salt level by **1000 ppm**.

??? example "Salt dosage example"

    For a 50 m³ pool with salt at 2000 ppm:

    - Delta: 3200 - 2000 = 1200
    - Quantity: (1200 / 1000) x 3000 x 50 = **180000 g (180 kg) of salt**

!!! note

    The salt rule only activates when the pool treatment type is set to
    **Salt electrolysis**. For other treatment types, salt level is still
    tracked if a sensor is configured, but no recommendations are generated.

## Spoon Equivalents

When [measuring spoon sizes](getting-started.md#step-3-measuring-spoons) are
configured, dosage recommendations include an approximate number of spoons
alongside the gram-based quantity. This makes it easier to measure products
in practice without a scale.

### How it works

Each chemical product has an approximate bulk density (g/mL) that is used to
convert grams to milliliters. The volume is then divided by the spoon size
to determine the number of spoons.

$$
\text{spoons} = \frac{\text{quantity\_g} / \text{density}}{\text{spoon\_size\_ml}}
$$

When multiple spoon sizes are configured, the integration selects the one
that minimizes rounding error when rounded to a whole number of spoons
(the **best-fit** strategy).

### Product density table

| Product | Density (g/mL) | Notes |
| --- | --- | --- |
| pH- (sodium bisulfate) | 1.1 | Dense granules |
| pH+ (sodium carbonate) | 0.55 | Light powder |
| Shock chlorine (dichlor) | 0.9 | Granules |
| Neutralizer (sodium thiosulfate) | 1.1 | Granules |
| TAC+ (sodium bicarbonate) | 0.9 | Powder |
| Salt (NaCl) | 1.2 | Crystals |
| Bromine shock | 0.8 | Granules |
| Stabilizer (cyanuric acid) | 0.75 | Low density granules |
| Calcium hardness increaser (CaCl₂) | 0.85 | Flakes / powder |
| Active oxygen activator | 1.0 | Liquid |
| Flocculant | 1.0 | Liquid |
| Anti-algae | 1.0 | Liquid |
| Clarifier | 1.0 | Liquid |
| Metal sequestrant | 1.1 | Liquid |
| Winterizing product | 1.0 | Liquid |

### Tablet products

Tablet products (chlorine tablets, bromine tablets, active oxygen tablets) are
excluded from spoon equivalents because they are not measured with spoons.

### Recommendation display

When spoon equivalents are available, the recommendation message format is:

```text
Add 300g of ph_minus (300g of ph_minus, 18 Large spoons)
```

The `spoon_count` and `spoon_name` values are also available as
[sensor attributes](entities.md#chemistry-actions-sensor-attributes)
for use in dashboards and automations.

### Service input

The `poolman.add_treatment` service accepts spoon-based input as an
alternative to grams:

| Field | Type | Description |
| --- | --- | --- |
| `spoons` | float | Number of spoons used |
| `spoon_name` | string | Name of the configured spoon size |

When `spoons` and `spoon_name` are provided (and `quantity_g` is omitted),
the service converts the spoon count to grams using the product's density
and the named spoon's volume.

??? example "Spoon equivalent example"

    With a "Large" spoon (15 mL) and pH- (density 1.1 g/mL):

    - Dosage: 300 g
    - Volume: 300 / 1.1 = 272.7 mL
    - Spoons: 272.7 / 15 = 18.2, rounded to **18 Large spoons**
