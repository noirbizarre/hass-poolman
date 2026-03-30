---
icon: lucide/sun-snow
---

# Pool Modes

Pool Manager supports five operational modes, selectable via the
`select.{pool}_mode` entity. Each mode adapts filtration duration and rule
behavior to the current season or pool status.

The modes follow a natural lifecycle:

**Active** → **Hibernating** → **Active Wintering** / **Passive Wintering**
→ **Activating** → **Active**

## Active

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

!!! info "Advisory vs Active Control"

    The recommended filtration duration computed here is an **advisory** value
    exposed as a sensor entity. It does not directly control your pump.
    If you have a pump switch configured, you can use
    [Filtration Control](filtration-control.md) for automatic daily pump
    scheduling, and optionally sync the duration via automation.

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

## Hibernating

Transition mode used when preparing the pool for winter. The pool is still
operational but the system is being shut down progressively. Typical tasks
during this phase include:

- Lowering the water level
- Cleaning the filter and skimmers
- Adding winterizing product
- Covering the pool

### Hibernating filtration

Fixed at **4 hours** per day, regardless of water temperature. This keeps
water circulating while the pool is being prepared.

### Hibernating rules

All chemistry rules remain active. The pool still needs monitoring during
the transition to catch any issues before full shutdown.

## Active Wintering

Reduced operation during cold months when the pool is covered but the system
remains partially active. **The pool is not usable for swimming** in this mode.

### Active wintering filtration

Filtration duration uses a **temperature / 3** formula adapted for winter
conditions:

1. **Base rule**: water temperature / 3 (industry standard for active
   wintering, roughly two-thirds less than summer operation)
2. **Filter efficiency**: same coefficient as active mode
3. **Turnover guarantee**: ensures at least one full volume cycle
4. **Clamping**: bounded between 2 h and 24 h

Outdoor temperature heat stress is **not applied** (not relevant in winter).

If no temperature reading is available, the duration falls back to a fixed
**4 hours** per day.

> **Source**: [Beatbot -- Active wintering guide](https://fr.beatbot.com/blogs/nettoyeur-de-piscine-automatique/hivernage-actif-piscine)

### Active wintering rules

Most chemistry rules are **disabled** -- only pH monitoring and sensor
calibration checks remain active:

| Rule | Status | Reason |
| --- | --- | --- |
| pH | Active | Equipment and liner protection |
| Sanitizer/ORP | Disabled | Low bather load, reduced biological activity |
| TAC | Disabled | Not actionable during winter |
| Algae risk | Disabled | Cold temperatures prevent algae growth |
| CYA | Disabled | Not actionable during winter |
| Hardness | Disabled | Not actionable during winter |
| Calibration | Active | Sensor drift detection always useful |
| Filtration | Active | Always produces recommendations |

## Passive Wintering

Pool is fully shut down and winterized.

### Passive wintering filtration

Set to **0 hours**. No filtration is recommended.

### Passive wintering rules

All chemistry rules are **disabled**. No recommendations are generated
in this mode.

!!! warning

    Ensure your pool is properly winterized before switching to passive wintering mode. Pool Manager will not generate any alerts in this mode.

## Activating

Transition mode used when bringing the pool out of hibernation. The pool is
not yet ready for swimming and typically requires:

- Removing the cover
- Raising the water level
- Cleaning the pool and filter
- Shock treatment
- Intensive filtration to restore water clarity

### Activation Wizard

When the pool mode is set to **Activating**, an activation wizard guides you
through the five steps needed to bring the pool back to full operation.
Progress is tracked via the `sensor.{pool}_activation_step` entity, which
shows the current (next pending) step.

#### Wizard steps

| # | Step | Confirmation |
| --- | --- | --- |
| 1 | **Remove cover** | Manual |
| 2 | **Raise water level** | Manual |
| 3 | **Clean pool and filter** | Manual |
| 4 | **Shock treatment** | Auto-detected when a shock product is recorded |
| 5 | **Intensive filtration** | Auto-detected when a filtration cycle completes |

Steps can be confirmed in any order. The three manual steps require
calling the `poolman.confirm_activation_step` service. The two
auto-detectable steps are confirmed automatically:

- **Shock treatment** is auto-confirmed when a shock product
  (`chlore_choc`, `bromine_shock`, or `active_oxygen_activator`) is
  recorded via the `poolman.add_treatment` service.
- **Intensive filtration** is auto-confirmed when a filtration cycle
  completes (the scheduler fires a `filtration_stopped` event).

When all five steps are confirmed, the pool mode automatically switches
to **Active** and the activation checklist is cleared.

#### Confirming steps manually

Use the `poolman.confirm_activation_step` service:

```yaml
service: poolman.confirm_activation_step
data:
  device_id: "<your_pool_device_id>"
  step: "remove_cover"
```

Valid step values: `remove_cover`, `raise_water_level`,
`clean_pool_and_filter`, `shock_treatment`, `intensive_filtration`.

#### Persistence

The activation checklist persists across Home Assistant restarts. When
HA restarts while the pool is in activating mode, already-confirmed
steps are restored from the `activation_step` sensor's persisted state
attributes.

### Activating filtration

Uses the full **dynamic multi-factor algorithm** (same as active mode).
The pool needs intensive filtration to restore water quality after the
winter period.

### Activating rules

All chemistry rules are active. Close monitoring is essential during this
phase to bring water parameters back to safe levels.

## Mode Comparison

| Aspect | Active | Hibernating | Active Wintering | Passive Wintering | Activating |
| --- | --- | --- | --- | --- | --- |
| Swimming | Safe | Unsafe | Unsafe | Unsafe | Unsafe |
| Filtration | Multi-factor (2--24h) | 4h fixed | temp/3 dynamic (2--24h) | 0h | Multi-factor (2--24h) |
| pH rule | Active | Active | Active | Disabled | Active |
| Sanitizer/ORP rule | Active | Active | Disabled | Disabled | Active |
| TAC rule | Active | Active | Disabled | Disabled | Active |
| Algae risk alert | Active | Active | Disabled | Disabled | Active |
| CYA rule | Active | Active | Disabled | Disabled | Active |
| Hardness rule | Active | Active | Disabled | Disabled | Active |
| Calibration rule | Active | Active | Active | Disabled | Active |
| Typical season | Spring--Autumn | Late autumn | Cold months | Full winter shutdown | Early spring |
