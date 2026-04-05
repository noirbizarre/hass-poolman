---
icon: lucide/message-circle-question
---

# FAQ

## General

### Why does this project exist?

Most pool sensor integrations for Home Assistant (Flipr, iopool, Sutro, Blue
Connect, etc.) expose raw sensor readings but stop there. Pool Manager fills
the gap by adding an **intelligence layer** on top of those readings:
a water quality score, chemical dosage recommendations with specific products
and quantities, automated filtration control, seasonal mode management, and
treatment tracking -- all computed locally with no cloud dependency.

In short, the sensor integrations give you **data**; Pool Manager gives you
**actionable advice**.

### Does Pool Manager replace my pool probe integration?

No. Pool Manager **complements** your existing sensor integrations. It reads
sensor entities already available in Home Assistant -- regardless of their
source -- and produces computed analytics on top of them. You still need your
sensor integration (or manual input helpers) to provide the raw readings.

### What sensors do I need to get started?

At minimum, you need **pH**, **ORP**, and **water temperature** sensors.
These three are sufficient for water quality scoring, sanitizer evaluation,
and filtration duration calculation.

Additional sensors (free chlorine, TAC, CYA, hardness, salt, EC) improve
accuracy and unlock more rules and recommendations. See
[Getting Started](getting-started.md#sensor-requirements) for the full list.

### Does this work with my Flipr / iopool / Sutro / ESPHome sensors?

Yes. Pool Manager is **hardware agnostic**. It works with any Home Assistant
sensor entity: dedicated pool probes (Flipr, iopool, Sutro, Blue Connect),
ESPHome or Tasmota DIY sensors, MQTT sensors, or even manual
`input_number` helpers. If the value is available as a sensor entity in
Home Assistant, Pool Manager can use it.

### Can I manage multiple pools?

Yes. Add the integration multiple times -- once per pool. Each instance
operates independently with its own sensors, settings, and entities.

### Does this require an internet connection?

No. All computations happen locally on your Home Assistant instance. No cloud
API, no account, no internet connection required. The integration's IoT class
is `calculated`.

## Configuration

### Can I use this without connected sensors?

Yes. Create `input_number` helpers in Home Assistant for each parameter
(pH, ORP, temperature, etc.) and select them during configuration. You can
then update the values manually whenever you take a reading.

### Can I change settings after initial setup?

**Chemistry and filtration settings** can be updated at any time through
the integration's reconfigure option in
**Settings > Devices & Services > Pool Manager > Configure**.

However, **pool name**, **volume**, and **shape** are set during initial
configuration and cannot be changed afterwards. The pool name serves as
the unique identifier for the integration instance.

### How often does Pool Manager update?

Every **5 minutes**. This interval is fixed and not configurable. The
integration reads all configured sensor entities and recomputes scores,
recommendations, and filtration parameters on each update cycle.

## Chemistry & Water Quality

### How is the water quality score calculated?

Each configured parameter is scored individually based on how close its
reading is to the ideal target value. Readings at the target score 100%;
readings at the boundary score 50%; readings outside the acceptable range
score 0%. The overall water quality score is the **average** of all
individual parameter scores.

See [Water Chemistry -- Scoring](water-chemistry.md#scoring-algorithm) for
the full algorithm.

### Why doesn't free chlorine show a calculated dosage?

Unlike pH or alkalinity, the amount of chlorine needed depends on too many
variable factors: CYA (stabilizer) level, UV exposure, bather load, water
temperature, and more. Pool Manager recommends the appropriate **product**
(shock chlorine or neutralizer) but cannot reliably calculate a precise
quantity. See [Free Chlorine](water-chemistry.md#free-chlorine) for details.

### What does "partial water drain" mean?

When CYA (cyanuric acid) or calcium hardness exceeds the maximum threshold,
there is no chemical product that lowers these levels. The only solution is
to **dilute** the pool water by draining a portion and refilling with fresh
water. Pool Manager correctly recommends this when no chemical fix exists.

### What is EC used for?

Electrical conductivity (EC) is a **diagnostic-only** sensor. It has no
scoring, no status, and no rules. It is useful for tracking mineral buildup,
dissolved solids trends, or monitoring salt levels over time in your
dashboards. See [Electrical Conductivity](water-chemistry.md#electrical-conductivity-ec)
for more information.

## Filtration

### Does the recommended filtration duration control my pump?

No. The `sensor.{pool}_recommended_filtration_duration` entity is
**advisory only** -- it tells you how long filtration should run, but does
not act on it.

To enable automatic pump control, you must configure a **pump switch entity**
during setup and enable filtration control. This creates additional entities
(`switch.{pool}_filtration`, `time.{pool}_filtration_start`, etc.) that
manage the pump schedule. See
[Filtration Control](filtration-control.md) for the full setup.

### What happens if Home Assistant restarts during filtration?

Pool Manager includes **restart recovery**. On startup, it checks whether
the current time falls within the active filtration window. If it does, the
pump is turned back on and filtration resumes for the remaining duration.

## Troubleshooting

### Why are some entities missing?

Filtration control entities (`switch.{pool}_filtration`,
`time.{pool}_filtration_start`, `number.{pool}_filtration_duration`, etc.)
are **only created** when a pump switch entity is configured during setup.

Additionally, period 2 entities (for split filtration modes) are always
created but show as **unavailable** unless a split duration mode is active.

### Why are no events fired right after a restart?

By design, Pool Manager does **not** fire status change or threshold events
on the first data update after a Home Assistant restart. This prevents false
positives caused by sensors transitioning from "unknown" to their actual
values.

### Why does the `water_ok` binary sensor show unsafe when chemistry looks fine?

The `water_ok` binary sensor considers **both** water chemistry status
**and** active treatment safety. If a chemical treatment was recently
recorded and its swimming wait time has not elapsed, `water_ok` will report
unsafe even if all chemistry parameters are within range. See
[Chemistry Tracking](chemistry-tracking.md) for details on treatment safety
profiles.
