---
icon: lucide/flask-conical
---

# Water Chemistry

Pool Manager monitors up to five water chemistry parameters. Each parameter
has a defined acceptable range and an ideal target value used for scoring
and dosage calculations.

## Parameter Ranges

| Parameter | Unit | Minimum | Target | Maximum |
| --- | --- | --- | --- | --- |
| pH | -- | 6.8 | 7.2 | 7.8 |
| ORP | mV | 650 | 750 | 900 |
| TAC (Total Alkalinity) | ppm | 80 | 120 | 150 |
| CYA (Cyanuric Acid) | ppm | 20 | 40 | 75 |
| Calcium Hardness | ppm | 150 | 250 | 400 |

Values within the minimum--maximum range are considered acceptable. The target
value represents the ideal level for each parameter.

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
the score is computed from those two. Adding TAC, CYA, or hardness sensors
increases the accuracy of the score.

If no parameter has a valid reading, the score is unavailable.

## Chemical Products

Pool Manager may recommend the following chemical products in its dosage calculations:

| Product | Usage |
| --- | --- |
| pH- (pH minus) | Lower pH when it is above target |
| pH+ (pH plus) | Raise pH when it is below target |
| Chlore choc (shock chlorine) | Emergency chlorination when ORP is critically low |
| Galet chlore (chlorine tablet) | Regular chlorine supplementation when ORP is below acceptable |
| Neutralizer | Reduce chlorine when ORP is excessively high |
| TAC+ (alkalinity increaser) | Raise total alkalinity when it is below minimum |

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
