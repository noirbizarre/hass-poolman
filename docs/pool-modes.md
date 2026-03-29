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

Filtration duration is computed using the classic **temperature / 2** rule:

- A pool at 26°C gets a base recommendation of **13 hours**
- A pool at 18°C gets a base recommendation of **9 hours**

The duration is then adjusted to ensure at least one full water volume
turnover based on your pump flow rate:

$$
\text{turnover\_hours} = \frac{\text{volume\_m3}}{\text{pump\_flow\_m3h}}
$$

The final recommendation is the **greater** of the temperature-based
duration and the turnover time, clamped between **2 hours minimum** and
**24 hours maximum**.

!!! info "Filtration type"

    The filtration type (sand, cartridge, diatomaceous earth, glass)
    configured during setup is stored for informational purposes.
    It does not currently affect the filtration duration calculation.

??? example "Calculation example"

    For a 60 m³ pool with a 10 m³/h pump at 24°C:

    - Temperature rule: 24 / 2 = **12 hours**
    - Turnover time: 60 / 10 = **6 hours**
    - Result: **12 hours** (temperature rule wins)

    For a 80 m³ pool with a 8 m³/h pump at 14°C:

    - Temperature rule: 14 / 2 = **7 hours**
    - Turnover time: 80 / 8 = **10 hours**
    - Result: **10 hours** (turnover requirement wins)

### Rules

All chemistry rules are active: pH, chlorine/ORP, TAC, and algae risk.

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
| Filtration | temp / 2 (2--24h) | 4h fixed | 0h |
| pH rule | Active | Active | Disabled |
| Chlorine/ORP rule | Active | Active | Disabled |
| TAC rule | Active | Active | Disabled |
| Algae risk alert | Active | Active | Disabled |
| Typical season | Spring--Autumn | Cold months | Full winter shutdown |
