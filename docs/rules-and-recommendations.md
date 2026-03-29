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

| Condition | Priority | Recommendation |
| --- | --- | --- |
| pH outside acceptable range (< 6.8 or > 7.8) | High | Add pH+ or pH- with calculated dosage |
| pH deviation > 0.3 from target | Medium | Add pH+ or pH- with calculated dosage |
| pH deviation > 0.1 from target | Low | Add pH+ or pH- with calculated dosage |

The dosage is calculated based on pool volume.
See [pH Dosage Calculation](water-chemistry.md#ph-dosage-calculation)
for details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Chlorine Rule (ORP)

Evaluates chlorine effectiveness through ORP (Oxidation-Reduction Potential) readings.

| ORP Level | Severity | Priority | Recommendation |
| --- | --- | --- | --- |
| < 650 mV | Critical | Critical | Shock chlorination required |
| 650--720 mV | Medium | Medium | Add chlorine tablets |
| 720--900 mV | -- | -- | No action (acceptable range) |
| > 900 mV | Medium | Medium | Reduce chlorine dosage (add neutralizer) |

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Filtration Rule

Recommends daily filtration duration based on the current [pool mode](pool-modes.md).

| Condition | Priority |
| --- | --- |
| Running mode, recommended duration >= 12h | Medium |
| Running mode, recommended duration < 12h | Low |
| Wintering modes | Low |

### TAC Rule (Total Alkalinity)

Monitors total alkalinity and recommends adjustments.

| Condition | Priority | Recommendation |
| --- | --- | --- |
| TAC < 80 ppm | Medium | Add TAC+ with calculated dosage |
| TAC > 150 ppm | Low | pH- treatments will help lower it |

See [TAC Dosage Calculation](water-chemistry.md#tac-dosage-calculation) for dosage details.

!!! note

    This rule is disabled in [Passive Wintering](pool-modes.md#passive-wintering) mode.

### Algae Risk Rule

Detects conditions favorable to algae growth by combining temperature and ORP readings.

| Condition | Priority | Recommendation |
| --- | --- | --- |
| Water temperature > 28°C **and** ORP < 720 mV | High | High algae risk alert |

Both conditions must be met simultaneously. This rule is disabled in
[Passive Wintering](pool-modes.md#passive-wintering) mode.
