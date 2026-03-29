---
icon: lucide/sun-snow
---

# Pool Modes

Pool Manager supports three operational modes, selectable via the
`select.{pool}_mode` entity. Each mode adapts filtration duration and rule
behavior to the current season or pool status.

## Running

Normal season operation. This is the default mode.

### Filtration

Filtration duration is computed using a multi-factor algorithm that combines
water temperature, filter type efficiency, outdoor temperature, and pump
capacity.

#### Step 1: Base rule (temperature / 2)

The classic **temperature / 2** rule from the French pool industry:

- A pool at 26 °C gets a base of **13 hours**
- A pool at 18 °C gets a base of **9 hours**

This rule reflects the relationship between water temperature and biological
activity: warmer water promotes faster algae and bacteria growth, requiring
longer filtration to maintain clarity.

> **Sources**: [iopool](https://iopool.com), [hth](https://www.hth-pool.com),
> [Swim University](https://www.swimuniversity.com)

#### Step 2: Filter efficiency adjustment

The base duration is multiplied by a coefficient based on your filter type.
More efficient filters (finer micron rating) can achieve the same water
clarity in less time:

| Filter type | Micron rating | Coefficient | Effect |
| --- | --- | --- | --- |
| Sand | 20--40 μm | 1.00 | Baseline (no adjustment) |
| Cartridge | 10--20 μm | 0.95 | -5% filtration time |
| Glass media | 3--10 μm | 0.90 | -10% filtration time |
| Diatomaceous earth | 2--5 μm | 0.85 | -15% filtration time |

$$
\text{adjusted\_hours} = \text{base\_hours} \times \text{efficiency\_coefficient}
$$

> **Sources**: Micron ratings from
> [In The Swim](https://www.intheswim.com),
> [Crush Pools](https://crushpools.com),
> [Leslie's Pool](https://www.lesliespool.com)

#### Step 3: Outdoor temperature heat stress

When outdoor temperature exceeds **28 °C**, each additional degree increases
filtration duration by **5%** to compensate for:

- Accelerated algae growth due to ambient heat
- Faster UV-driven chlorine degradation
- Increased bather load (more swimming in hot weather)

$$
\text{heat\_factor} = 1 + (\text{outdoor\_temp} - 28) \times 0.05
$$

This adjustment is only applied when an outdoor temperature sensor or weather
entity is configured. If neither is available, this step is skipped.

> **Sources**:
> [Zodiac Pool Care](https://www.zodiac-poolcare.com),
> [Leslie's Pool](https://www.lesliespool.com),
> [In The Swim](https://www.intheswim.com)

#### Step 4: Turnover guarantee

The duration is adjusted to ensure at least one full water volume
turnover based on your pump flow rate:

$$
\text{turnover\_hours} = \frac{\text{volume\_m3}}{\text{pump\_flow\_m3h}}
$$

The final duration is the **greater** of the adjusted temperature-based
duration and the turnover time.

#### Step 5: Clamping

The result is bounded between **2 hours minimum** and **24 hours maximum**.

??? example "Calculation examples"

    **Example 1 --- Standard conditions**

    For a 60 m³ pool with a sand filter and 10 m³/h pump at 24 °C water,
    no outdoor temperature sensor:

    1. Base: 24 / 2 = **12 h**
    2. Sand efficiency: 12 × 1.0 = **12 h**
    3. No outdoor temp: skipped
    4. Turnover: 60 / 10 = 6 h → max(12, 6) = **12 h**
    5. Clamp: **12 hours**

    **Example 2 --- Efficient filter**

    Same pool with a DE filter:

    1. Base: 24 / 2 = **12 h**
    2. DE efficiency: 12 × 0.85 = **10.2 h**
    3. No outdoor temp: skipped
    4. Turnover: 6 h → max(10.2, 6) = **10.2 h**
    5. Clamp: **10.2 hours**

    **Example 3 --- Heat wave**

    60 m³ pool, glass filter, 10 m³/h pump, 28 °C water, 35 °C outdoors:

    1. Base: 28 / 2 = **14 h**
    2. Glass efficiency: 14 × 0.9 = **12.6 h**
    3. Heat stress: (35 − 28) × 0.05 = 0.35 → 12.6 × 1.35 = **17.01 h**
    4. Turnover: 6 h → max(17.01, 6) = **17.01 h**
    5. Clamp: **17.01 hours**

    **Example 4 --- Turnover-limited**

    80 m³ pool, sand filter, 8 m³/h pump, 14 °C water:

    1. Base: 14 / 2 = **7 h**
    2. Sand efficiency: 7 × 1.0 = **7 h**
    3. No outdoor temp: skipped
    4. Turnover: 80 / 8 = 10 h → max(7, 10) = **10 h**
    5. Clamp: **10 hours**

### Rules

All chemistry rules are active: pH, sanitizer/ORP, TAC, and algae risk.

## Active Wintering

Reduced operation during cold months when the pool is covered but the system
remains partially active.

### Active wintering filtration

Fixed at **4 hours** per day, regardless of water temperature.

### Active wintering rules

All chemistry rules remain active. The pool still needs chemical balance
monitoring even during winter to prevent damage.

## Passive Wintering

Pool is fully shut down and winterized.

### Passive wintering filtration

Set to **0 hours**. No filtration is recommended.

### Passive wintering rules

All chemistry rules are **disabled**. No recommendations are generated
in this mode.

!!! warning

    Ensure your pool is properly winterized before switching to passive wintering mode. Pool Manager will not generate any alerts in this mode.

## Mode Comparison

| Aspect | Running | Active Wintering | Passive Wintering |
| --- | --- | --- | --- |
| Filtration | Multi-factor (2--24h) | 4h fixed | 0h |
| pH rule | Active | Active | Disabled |
| Sanitizer/ORP rule | Active | Active | Disabled |
| TAC rule | Active | Active | Disabled |
| Algae risk alert | Active | Active | Disabled |
| Typical season | Spring--Autumn | Cold months | Full winter shutdown |
