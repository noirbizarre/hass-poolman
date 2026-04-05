---
icon: lucide/shield-check
---

# Rules & Recommendations

Pool Manager includes an extensible rule engine that evaluates your pool's
state and produces actionable recommendations. Rules are evaluated every
5 minutes and results are exposed through the
[recommendations sensor](entities.md#recommendations-sensor-attributes)
and [binary sensors](entities.md#binary-sensors).

## Priority System

Each recommendation has a priority level that determines its urgency and affects the binary sensor states:

| Priority | Description | Triggers `action_required` | Triggers `water_ok` OFF |
| --- | --- | --- | --- |
| Critical | Immediate action needed | Yes | Yes |
| High | Act soon | Yes | Yes |
| Medium | Attention recommended | Yes | No |
| Low | Informational | Yes | No |

Recommendations are sorted by priority (critical first) when displayed.

## Action Kind

Each recommendation is classified as either a **suggestion** or a **requirement**:

| Kind | Description |
| --- | --- |
| Requirement | The pool needs attention to remain safe or functional |
| Suggestion | An optional improvement that would bring parameters closer to ideal |

The kind is exposed through the
[chemistry actions sensor](entities.md#chemistry-actions-sensor-attributes)
and can be used to filter or prioritize actions in automations
and dashboards.

## Recommendation Types

| Type | Description |
| --- | --- |
| Chemical | Add a specific chemical product (includes product name and dosage) |
| Filtration | Run the filtration system for a specified duration |
| Alert | Warning about a risky condition (e.g., algae risk) |
| Maintenance | General maintenance action (reserved for future use) |

## Built-in Rules

### pH Rule

Monitors the pH level and recommends adjustments when it deviates from the
target (7.2).

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| pH outside acceptable range (< 6.8 or > 7.8) | High | Requirement | Add pH+ or pH- with calculated dosage |
| pH deviation > 0.3 from target | Medium | Suggestion | Add pH+ or pH- with calculated dosage |
| pH deviation > 0.1 from target | Low | Suggestion | Add pH+ or pH- with calculated dosage |

The dosage is calculated based on pool volume.
See [pH Dosage Calculation](water-chemistry.md#ph-dosage-calculation)
for details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Sanitizer Rule (ORP)

Evaluates sanitizer effectiveness through ORP (Oxidation-Reduction Potential)
readings. The recommended products depend on the configured
[treatment type](getting-started.md#step-2-chemistry).

| ORP Level | Severity | Priority | Kind | Action |
| --- | --- | --- | --- | --- |
| < 650 mV | Critical | Critical | Requirement | Shock treatment required |
| 650--720 mV | Medium | Medium | Suggestion | Add regular sanitizer product |
| 720--900 mV | -- | -- | -- | No action (acceptable range) |
| > 900 mV | Medium | Medium | Requirement | Reduce sanitizer dosage (add neutralizer) |

#### Products by treatment type

| Treatment | Regular | Shock | Excess |
| --- | --- | --- | --- |
| Chlorine | Chlorine tablet | Shock chlorine | Neutralizer |
| Salt electrolysis | Salt | Salt (increased dose) | Neutralizer |
| Bromine | Bromine tablet | Bromine shock | Neutralizer |
| Active oxygen | Active oxygen tablet | Active oxygen activator | Neutralizer |

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Free Chlorine Rule

Supplements the ORP-based Sanitizer Rule with a direct free chlorine reading.
Unlike ORP, free chlorine provides a direct measurement of available
sanitizer. When free chlorine is configured, this rule operates alongside
(not instead of) the sanitizer rule.

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| Free chlorine < 1.0 ppm | High | Requirement | Add chlorine (shock chlorine product) |
| Free chlorine > 3.0 ppm | Low | Suggestion | Reduce chlorine dosage (neutralizer product) |

No specific dosage is calculated because the required amount depends on
multiple factors (CYA level, UV exposure, bather load).

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering)
    and [Active Wintering](pool-modes.md#active-wintering) modes.

### Filtration Rule

Recommends daily filtration duration based on the current [pool mode](pool-modes.md).

| Condition | Priority |
| --- | --- |
| Running mode, recommended duration >= 12h | Medium |
| Running mode, recommended duration < 12h | Low |
| Wintering modes | Low |

### TAC Rule (Total Alkalinity)

Monitors total alkalinity and recommends adjustments.

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| TAC < 80 ppm | Medium | Requirement | Add TAC+ with calculated dosage |
| TAC > 150 ppm | Low | Suggestion | pH- treatments will help lower it |

See [TAC Dosage Calculation](water-chemistry.md#tac-dosage-calculation) for dosage details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Algae Risk Rule

Detects conditions favorable to algae growth by combining temperature and ORP readings.

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| Water temperature > 28°C **and** ORP < 720 mV | High | Requirement | High algae risk alert |

Both conditions must be met simultaneously. This rule is disabled in
[Passive Wintering](pool-modes.md#passive-wintering) mode.

### CYA Rule (Cyanuric Acid)

Monitors cyanuric acid (stabilizer) levels and recommends adjustments.

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| CYA < 20 ppm | Medium | Requirement | Add stabilizer with calculated dosage |
| CYA > 75 ppm | Low | Requirement | Consider partial water drain (no chemical fix) |

See [CYA Dosage Calculation](water-chemistry.md#cya-dosage-calculation) for dosage details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Hardness Rule (Calcium Hardness)

Monitors calcium hardness levels and recommends adjustments.

| Condition | Priority | Kind | Recommendation |
| --- | --- | --- | --- |
| Hardness < 150 ppm | Medium | Requirement | Add calcium hardness increaser with calculated dosage |
| Hardness > 400 ppm | Low | Requirement | Consider partial water drain (no chemical fix) |

See [Hardness Dosage Calculation](water-chemistry.md#hardness-dosage-calculation) for dosage details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.
